"""In-memory multiplayer room state and recipient snapshot serialization."""

import asyncio
from dataclasses import dataclass, field, asdict
import time
import secrets
from typing import Any, TYPE_CHECKING

from fastapi import WebSocket

from backend.practice_tiers import FREE_QUESTION_LIMIT
from backend.processing_policy import ProcessingPolicy
from backend.defense_session import DefenseSession, ResearchDefenseSession, PANELIST_ORDER
from backend.project_files import ProjectFile
from backend.question_generator import CoachingReport
from backend.openrouter_questions import SEPARATE_PLANNING
from backend.research_plan import ResearchPlan, ResearchPlanProgress, ResearchProfileDescription
from backend.resource_limits import AIBudget, limit
from backend.coaching_progress import CoachingProgress
from backend.room_operations import (
    RoomOperation, bind_operation, record_stage, record_total, release_operation,
    take_supplied_usage,
)
from backend.rooms.openings import OpeningCandidate
from backend.rooms.speech import SpeechState, draft_snapshot
from backend.timed_turn import TimedTurn
from backend.room_documents import RoomDocuments
from backend.turn_recovery import QuestionPlanRecovery

if TYPE_CHECKING:
    from backend.rooms.coordinator import RoomCoordinator


@dataclass
class Player:
    token: str
    name: str
    seat: int
    is_host: bool = False
    sockets: set[WebSocket] = field(default_factory=set)


@dataclass
class Room(TimedTurn):
    code: str
    files: list[ProjectFile]
    players: dict[str, Player]
    defense_type: str = "code"
    research_stage: str = "infer"
    defense: DefenseSession | None = None
    revision: int = 0
    published_revision: int = -1
    generation_id: int = 0
    speech: SpeechState = field(default_factory=SpeechState, repr=False)
    opening_candidate: OpeningCandidate | None = None
    question_retry_generation_id: int | None = None
    feedback_status: str = "none"   # none | generating | ready | failed
    feedback: CoachingReport | None = None
    coaching_progress: CoachingProgress | None = None
    closing_panelist: str | None = None
    closing_deadline_ms: int | None = None
    research_planning_status: str = "none"  # none | planning | ready | failed
    research_plan_progress: ResearchPlanProgress | None = None
    research_plan: ResearchPlan | None = None
    research_profile_correction: ResearchProfileDescription | None = None
    research_plan_error: str | None = None
    research_budget_preview: int | None = None
    research_plan_approved: bool = False
    research_plan_generation_id: int = 0
    feedback_generation_id: int = 0
    operation: RoomOperation | None = field(default=None, compare=False)
    question_recovery: QuestionPlanRecovery = field(default_factory=QuestionPlanRecovery, repr=False, compare=False)
    chat: list[dict[str, Any]] = field(default_factory=list)
    chat_seq: int = 0
    clock_task: asyncio.Task | None = field(default=None, repr=False)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    broadcast_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    owner_account_id: str | None = None
    run_id: str | None = None
    absent_since_ms: int | None = None
    absence_elapsed_ms: int = 0

    created_ms: int = field(default_factory=lambda: now_ms())
    activity_ms: int = field(default_factory=lambda: now_ms())
    terminal_ms: int | None = None
    settled: bool = True
    closed: bool = False
    ai_budget: AIBudget = field(default_factory=AIBudget)
    coordinator: "RoomCoordinator | None" = field(default=None, init=False, repr=False, compare=False)
    documents: RoomDocuments | None = field(default=None, repr=False, compare=False)
    defense_view_id: str = field(default_factory=lambda: secrets.token_hex(12))
    preparation_id: str = field(default_factory=lambda: secrets.token_hex(24))
    practice_tier: str = "standard"
    processing_policy: ProcessingPolicy = field(default_factory=ProcessingPolicy.legacy, compare=False)
    planning_contract: str = SEPARATE_PLANNING
    interaction_deadline_ms: int | None = field(default=None, compare=False)
    interaction_transient_retries: int = field(default=0, compare=False)

    @property
    def has_confirmed_research_profile(self) -> bool:
        return bool(self.research_plan and self.research_plan.profile and self.research_plan_approved)

    def online_players(self) -> dict[str, int]:
        return {player.token: player.seat for player in self.players.values() if player.sockets}

    def begin_interaction_window(self, now: int) -> None:
        self.interaction_deadline_ms = self.processing_policy.deadline_ms(now)
        self.interaction_transient_retries = 0

    def clear_interaction_window(self) -> None:
        self.interaction_deadline_ms = None
        self.interaction_transient_retries = 0

    def next_processing_deadline(self, now: int) -> int | None:
        if self.interaction_deadline_ms is not None:
            return self.interaction_deadline_ms
        return self.processing_policy.deadline_ms(now)

    def processing_expired(self, now: int) -> bool:
        operation = self.operation
        return bool(operation and self.processing_policy.expired(operation.window_deadline_ms, now))

    @property
    def active_deadline_ms(self) -> int | None:
        if self.phase == "complete" and self.closing_deadline_ms is not None:
            return self.closing_deadline_ms
        return super().active_deadline_ms

    def clear_clock(self) -> None:
        super().clear_clock()
        self.closing_panelist = None
        self.closing_deadline_ms = None

    def begin_operation(self, *, kind: str, operation_id: str, stage: str, now: int,
                        attempt: int = 1, retrying: bool = False,
                        window_deadline_ms: int | None = None) -> None:
        if self.operation is not None:
            release_operation(self.operation.usage_key)
        self.operation = RoomOperation(operation_id, kind, stage, now, now, attempt, retrying)
        self.operation.window_deadline_ms = window_deadline_ms
        bind_operation(self.operation.usage_key)

    def finish_operation_stage(self, now: int, outcome: str,
                               failure_class: str | None = None, usage: dict | None = None) -> None:
        operation = self.operation
        if operation is None or operation.stage_finished:
            return
        record_stage(operation, ended_at_ms=now, outcome=outcome,
                     failure_class=failure_class, usage=usage)
        operation.stage_finished = True

    def advance_operation(self, stage: str, now: int) -> None:
        operation = self.operation
        if operation is None or (operation.stage == stage and not operation.stage_finished):
            return
        self.finish_operation_stage(now, "succeeded")
        operation.stage = stage
        operation.stage_started_at_ms = now
        operation.stage_finished = False

    def retry_operation(self, now: int, *, retry_at_ms: int | None = None) -> None:
        operation = self.operation
        if operation is None:
            return
        record_stage(operation, ended_at_ms=now, outcome="retrying")
        operation.attempt += 1
        operation.retrying = True
        operation.stage = "retry_wait"
        operation.stage_started_at_ms = now
        operation.retry_at_ms = retry_at_ms

    def resume_operation(self, now: int, *, stage: str = "generating") -> None:
        operation = self.operation
        if operation is None:
            return
        if operation.stage == "retry_wait":
            record_stage(operation, ended_at_ms=now, outcome="retried")
            operation.stage = stage
            operation.stage_started_at_ms = now
        operation.retrying = True
        operation.retry_at_ms = None

    def finish_operation(self, now: int, outcome: str, usage: dict | None = None,
                         failure_class: str | None = None) -> None:
        operation = self.operation
        if operation is None:
            return
        usage = take_supplied_usage(operation.usage_key, usage)
        self.finish_operation_stage(now, outcome, failure_class=failure_class, usage=usage)
        record_total(operation, ended_at_ms=now, outcome=outcome, usage=usage,
                     failure_class=failure_class)
        self.operation = None

    def clear_operation(self) -> None:
        if self.operation is not None:
            release_operation(self.operation.usage_key)
        self.operation = None

    def visible_operation(self) -> RoomOperation | None:
        operation = self.operation
        if operation is None or self.closed:
            return None
        visible = {
            "question": self.phase == "generating",
            "interpretation": self.phase == "interpreting",
            "mapping": self.research_planning_status == "planning",
            "coaching": self.feedback_status == "generating",
        }
        return operation if visible.get(operation.kind, False) else None

    def panelist_activity(self, operation: RoomOperation | None) -> dict | None:
        """Expose current public discussion context, never prospective AI work."""
        if (self.defense_type == "code" or operation is None
                or operation.kind not in {"question", "interpretation", "mapping"}
                or operation.stage == "retry_wait"):
            return None
        if operation.kind == "mapping":
            # Accepted upload identity is already public to joined defenders.
            # Streamed topics remain provisional, including during validation.
            paper = next((file for file in self.files if file.kind.startswith("research")), None)
            context = " ".join(paper.name.split())[:160] or None if paper else None
            return {"operation_id": operation.id, "view_id": self.defense_view_id,
                    "reviewer": None, "context": context}
        session = self.defense
        previous = session.turns[-1] if session and session.turns else None
        reviewer = (previous.panelist if previous and operation.kind == "interpretation"
                    else session.pending_panelist if session else None)
        context = None
        if isinstance(session, ResearchDefenseSession) and session.plan and previous:
            # Only the already-published turn's topic is suitable. A validated
            # next-move plan is still private until its question is accepted.
            topic = next((topic for topic in session.plan.topics if topic.id == previous.topic_id), None)
            if topic and isinstance(topic.title, str):
                context = " ".join(topic.title.split())[:160] or None
        return {"operation_id": operation.id, "view_id": self.defense_view_id,
                "reviewer": reviewer, "context": context}

    def expire(self, now, online, session, expected_id=None, choose=None):
        if expected_id is not None and self.clock_id != expected_id:
            return None
        if self.phase == "complete" and self.closing_deadline_ms is not None and now >= self.closing_deadline_ms:
            self.closing_deadline_ms = None
            self.clock_id += 1
            self.clear_interaction_window()
            return "closing_finished"
        outcome = super().expire(now, online, session, expected_id, choose)
        if outcome in {"timed_out", "probe_expired"}:
            self.clear_interaction_window()
        return outcome

    def expires_at(self):
        if self.closed or not self.settled or self.phase not in {'lobby', 'retry', 'complete'} or self.research_planning_status == 'planning' or self.feedback_status in {'generating', 'failed'}:
            return None
        if self.phase == 'complete':
            return (self.terminal_ms or self.activity_ms) + limit('ROOM_RETENTION_SECONDS', 1800, 86400) * 1000
        if self.defense and self.defense.turns:
            return None
        return self.activity_ms + limit('ROOM_IDLE_SECONDS', 1800, 86400) * 1000

    def snapshot(self, recipient: Player | None = None, *, now: int | None = None) -> dict[str, Any]:
        now = now_ms() if now is None else now
        turns = []
        if self.defense:
            for index, turn in enumerate(self.defense.turns):
                turns.append(
                    {
                        **(self.documents.citation(turn.question.filename, turn.question.evidence_location) if self.documents else {}),
                        "panelist": turn.panelist,
                        "lead_in": turn.question.lead_in,
                        "question": turn.question.question,
                        "filename": turn.question.filename,
                        "evidence_line": turn.question.evidence_line,
                        "evidence_text": turn.question.evidence_text,
                        "evidence_location": turn.question.evidence_location or f"Line {turn.question.evidence_line}",
                        "evidence_kind": turn.question.evidence_kind,
                        "evidence_before": turn.question.evidence_before,
                        "evidence_after": turn.question.evidence_after,
                        "clarifications": [exchange.__dict__ for exchange in turn.clarifications],
                        "answer": turn.answer,
                        "input_provenance": turn.input_provenance,
                        "probe": {**asdict(turn.probe), "input_provenance": turn.probe_input_provenance} if turn.probe else None,
                        "resolved": turn.resolved,
                        "timed_out": turn.timed_out,
                        "ended_early": turn.ended_early,
                        "topic_id": turn.topic_id,
                        "is_follow_up": turn.is_follow_up,
                        "assigned_seat": turn.assigned_seat,
                        "answered_by": self.answered_by.get(index),
                        "answered_by_seat": self.answered_by_seat.get(index),
                    }
                )
        if self.defense and self.defense.awaiting_answer:
            active_panelist = self.defense.turns[-1].panelist
        elif self.defense and self.defense.needs_question:
            active_panelist = self.defense.pending_panelist
        elif self.phase == "generating":
            active_panelist = "Methodology Reviewer" if self.defense_type != "code" else PANELIST_ORDER[0]
        else:
            active_panelist = None
        feedback_dict = None
        if self.feedback is not None:
            feedback_dict = {
                "answer_cards": self.feedback.answer_cards,
                "summary": self.feedback.summary,
                "strengths": self.feedback.strengths,
                "improvements": self.feedback.improvements,
                "next_step": self.feedback.next_step,
                "closing": self.feedback.closing,
            }
        operation = self.visible_operation()
        return {
            "room_code": self.code,
            "question_recovery_stage": self.question_recovery.stage if self.phase == "retry" else None,
            "voice": self.speech.snapshot() if self.defense_type != "code" else None,
            "defense_view_id": self.defense_view_id,
            "documents": self.documents.snapshot() if self.documents else [],
            "expires_at_ms": self.expires_at(),
            "interpretation_attempts_left": max(0, limit('AI_INTERPRETATION_ATTEMPTS', 6, 20) - self.interpretation_attempts),
            "clock_paused": self.pause_deadline_ms is not None and now < self.pause_deadline_ms,
            "pause_deadline_ms": self.pause_deadline_ms,
            "question_attempts_left": self.ai_budget.remaining(f'question:{len(self.defense.turns) if self.defense else 0}', limit('AI_QUESTION_ATTEMPTS', 3, 10)),
            "opening_repeated": self.opening_candidate is not None,
            "opening_candidate": self.opening_candidate.preview() if self.opening_candidate and recipient and recipient.is_host else None,
            "question_retrying": self.phase == "generating" and self.question_retry_generation_id == self.generation_id,
            "operation": operation.snapshot() if operation else None,
            "panelist_activity": self.panelist_activity(operation) if recipient is not None
                and self.players.get(recipient.token) is recipient else None,
            "processing_policy": self.processing_policy.snapshot(),
            "coaching_attempts_left": (1 if self.coaching_progress.can_retry else 0) if self.coaching_progress else self.ai_budget.remaining('coaching', limit('AI_COACHING_ATTEMPTS', 3, 10)),
            "plan_attempts_left": self.ai_budget.remaining('plan', limit('AI_PLAN_ATTEMPTS', 3, 10)),
            "self_seat": recipient.seat if recipient is not None else None,
            "self_is_host": recipient.is_host if recipient is not None else False,
            "phase": self.phase,
            "probe_recovery_available": self.probe_recovery_available,
            "probe_deadline_ms": self.answer_deadline_ms if self.defense and self.defense.turns and self.defense.turns[-1].probe and self.defense.turns[-1].probe.status == "pending" else None,
            "players": [
                {
                    "seat": player.seat,
                    "name": player.name,
                    "online": bool(player.sockets),
                    "is_host": player.is_host,
                }
                for player in sorted(self.players.values(), key=lambda player: player.seat)
            ],
            "turns": turns,
            "active_panelist": active_panelist,
            "error": self.error,
            "revision": self.revision,
            "files": [file.name for file in self.files],
            "accepted_files": [{"name": file.name, "kind": file.kind, "detail": file.detail} for file in self.files],
            "defense_type": self.defense_type,
            "research_stage": self.research_stage,
            "practice_tier": self.practice_tier,
            "question_limit": FREE_QUESTION_LIMIT if self.practice_tier == "free" else 100,
            "research_planning_status": self.research_planning_status,
            "research_plan_progress": self.research_plan_progress.snapshot() if self.research_plan_progress else None,
            "research_plan": self.research_plan.snapshot() if self.research_plan else None,
            "research_plan_error": self.research_plan_error,
            "research_profile_correction": self.research_profile_correction.snapshot() if self.research_profile_correction else None,
            "research_budget_preview": self.research_budget_preview,
            "research_plan_approved": self.research_plan_approved,
            "question_budget": self.defense.question_budget if isinstance(self.defense, ResearchDefenseSession) else None,
            "coverage": self.defense.coverage if isinstance(self.defense, ResearchDefenseSession) else {},
            "current_topic": self.defense.turns[-1].topic_id if isinstance(self.defense, ResearchDefenseSession) and self.defense.turns else None,
            "completion_reason": self.defense.completion_reason if isinstance(self.defense, ResearchDefenseSession) else None,
            "coaching_progress": self.coaching_progress.snapshot() if self.coaching_progress else None,
            "feedback_status": self.feedback_status,
            "feedback": feedback_dict,
            "closing_panelist": self.closing_panelist,
            "closing_deadline_ms": self.closing_deadline_ms if self.closing_deadline_ms is not None and now < self.closing_deadline_ms else None,
            "server_now_ms": now,
            "vote_deadline_ms": self.vote_deadline_ms,
            "reaction_deadline_ms": self.reaction_deadline_ms,
            "answer_deadline_ms": self.answer_deadline_ms,
            "remaining_answer_ms": self.pending_submission.remaining_ms if self.pending_submission else None,
            "my_voice_draft": draft_snapshot(self, recipient, now),
            "my_pending_submission": (
                self.pending_submission.text if recipient is not None and self.pending_submission
                and recipient.token == self.pending_submission.token else None
            ),
            "selected_seat": self.selected_seat,
            "vote_counts": {
                str(seat): sum(1 for token, choice in self.votes.items()
                               if choice == seat and bool(self.players[token].sockets))
                for seat in sorted({player.seat for player in self.players.values() if player.sockets})
            },
            "my_vote": self.votes.get(recipient.token) if recipient is not None else None,
            "chat": list(self.chat),
        }


def now_ms() -> int:
    return int(time.time() * 1000)

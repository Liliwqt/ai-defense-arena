"""In-memory multiplayer room state and recipient snapshot serialization."""

import asyncio
from dataclasses import dataclass, field, asdict
import time
from typing import Any, TYPE_CHECKING

from fastapi import WebSocket

from backend.defense_session import DefenseSession, ResearchDefenseSession, PANELIST_ORDER
from backend.project_files import ProjectFile
from backend.question_generator import CoachingReport
from backend.research_plan import ResearchPlan
from backend.resource_limits import AIBudget, limit
from backend.timed_turn import TimedTurn

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
    question_retry_generation_id: int | None = None
    feedback_status: str = "none"   # none | generating | ready | failed
    feedback: CoachingReport | None = None
    research_planning_status: str = "none"  # none | planning | ready | failed
    research_plan: ResearchPlan | None = None
    research_plan_error: str | None = None
    research_budget_preview: int | None = None
    research_plan_approved: bool = False
    research_plan_generation_id: int = 0
    feedback_generation_id: int = 0
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

    def online_players(self) -> dict[str, int]:
        return {player.token: player.seat for player in self.players.values() if player.sockets}

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
                        "probe": asdict(turn.probe) if turn.probe else None,
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
                "summary": self.feedback.summary,
                "strengths": self.feedback.strengths,
                "improvements": self.feedback.improvements,
                "next_step": self.feedback.next_step,
            }
        return {
            "room_code": self.code,
            "expires_at_ms": self.expires_at(),
            "interpretation_attempts_left": max(0, limit('AI_INTERPRETATION_ATTEMPTS', 6, 20) - self.interpretation_attempts),
            "clock_paused": self.pause_deadline_ms is not None and now < self.pause_deadline_ms,
            "pause_deadline_ms": self.pause_deadline_ms,
            "question_attempts_left": self.ai_budget.remaining(f'question:{len(self.defense.turns) if self.defense else 0}', limit('AI_QUESTION_ATTEMPTS', 3, 10)),
            "question_retrying": self.phase == "generating" and self.question_retry_generation_id == self.generation_id,
            "coaching_attempts_left": self.ai_budget.remaining('coaching', limit('AI_COACHING_ATTEMPTS', 3, 10)),
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
            "research_planning_status": self.research_planning_status,
            "research_plan": self.research_plan.snapshot() if self.research_plan else None,
            "research_plan_error": self.research_plan_error,
            "research_budget_preview": self.research_budget_preview,
            "research_plan_approved": self.research_plan_approved,
            "question_budget": self.defense.question_budget if isinstance(self.defense, ResearchDefenseSession) else None,
            "coverage": self.defense.coverage if isinstance(self.defense, ResearchDefenseSession) else {},
            "current_topic": self.defense.turns[-1].topic_id if isinstance(self.defense, ResearchDefenseSession) and self.defense.turns else None,
            "completion_reason": self.defense.completion_reason if isinstance(self.defense, ResearchDefenseSession) else None,
            "feedback_status": self.feedback_status,
            "feedback": feedback_dict,
            "server_now_ms": now,
            "vote_deadline_ms": self.vote_deadline_ms,
            "reaction_deadline_ms": self.reaction_deadline_ms,
            "answer_deadline_ms": self.answer_deadline_ms,
            "remaining_answer_ms": self.pending_submission.remaining_ms if self.pending_submission else None,
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

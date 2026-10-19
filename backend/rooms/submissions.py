"""Submission rules and detached interpretation; the coordinator owns tasks."""

import asyncio
import copy
from dataclasses import dataclass, replace
import os
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING

from fastapi import HTTPException
from backend.project_files import ProjectFile
from backend.question_generator import (
    DEFAULT_MODEL, GroundedQuestion, AnsweredQuestion, ClarificationExchange,
    PanelistProbe, SubmissionDecision, interpret_submission,
)
from backend.openrouter_questions import RunQuestionClient, run_scope
from backend.resource_limits import limit
from backend.timed_turn import PendingSubmission, DeadlineExpired
from backend.defense_session import ResearchDefenseSession
from backend.rooms.commands import (
    CommandResult, VerifiedActor, SubmissionCommand, SubmitAnswer,
    SubmitDirectAnswer, SubmitProbeReply, DiscardVoiceDraft, FinishProbe, RetryInterpretation, UsePendingAnswer,
)
from backend.rooms.errors import safe_generation_error
from backend.rooms.speech import validate_submission

if TYPE_CHECKING:
    from backend.rooms.coordinator import RoomCoordinator
    from backend.rooms.model import Room


@dataclass(frozen=True)
class InterpretationWork:
    interpretation_id: int
    run_id: str | None
    pending: PendingSubmission | None


@dataclass(frozen=True)
class InterpretationInput:
    pending: PendingSubmission
    files: tuple[ProjectFile, ...]
    panelist: str
    question: GroundedQuestion
    clarifications: tuple[ClarificationExchange, ...]
    history: tuple[AnsweredQuestion, ...]
    defense_type: str
    research_stage: str
    probe: PanelistProbe | None
    original_answer: str | None
    original_speaker_name: str | None
    research_context: dict | None = None
    provider_scope: str | None = None
    provider_owner: str | None = None
    provider_stopped: Callable[[], bool] | None = None


def capture_interpretation(room: "Room", pending: PendingSubmission, *,
                           provider_stopped: Callable[[], bool] | None = None) -> InterpretationInput:
    """Capture under the room lock; mutable probe/history data is detached."""
    turn = room.defense.turns[pending.turn]
    context = room.defense.context() if isinstance(room.defense, ResearchDefenseSession) else None
    if context is not None:
        context = copy.deepcopy(context)
        context["current_topic"] = turn.topic_id
    funded = bool(room.run_id and room.owner_account_id
                  and isinstance(room.defense, ResearchDefenseSession))
    return InterpretationInput(pending, tuple(room.files), turn.panelist, turn.question,
        tuple(turn.clarifications), tuple(copy.deepcopy(room.defense.answered_history())),
        room.defense_type, room.research_stage, copy.deepcopy(turn.probe) if pending.probe_id else None,
        turn.answer, turn.speaker_name, context,
        provider_scope=run_scope(room.run_id) if funded else None,
        provider_owner=room.owner_account_id if funded else None,
        provider_stopped=provider_stopped if funded else None)


InterpretationRequest = Callable[[InterpretationInput], Awaitable[SubmissionDecision]]


async def request_interpretation(request: InterpretationInput) -> SubmissionDecision:
    client = None
    if request.provider_scope and request.provider_owner:
        client = RunQuestionClient(request.provider_scope, request.provider_owner, None,
                                   request.files,
                                   stopped=request.provider_stopped or (lambda: False)
                                   ).interaction(request.panelist)
    return await asyncio.to_thread(
        interpret_submission, list(request.files), os.getenv("OPENAI_API_KEY"),
        panelist=request.panelist, question=request.question, submission=request.pending.text,
        clarifications=request.clarifications, history=request.history,
        model=os.getenv("OPENAI_MODEL") or DEFAULT_MODEL, client=client,
        defense_type=request.defense_type, research_stage=request.research_stage,
        **({"research_context": request.research_context} if request.research_context else {}),
        **({"probe": request.probe, "original_answer": request.original_answer,
            "original_speaker_name": request.original_speaker_name,
            "speaker_name": request.pending.name} if request.probe else {}),
    )


async def run_interpretation(owner: "RoomCoordinator", work: InterpretationWork,
                             request: InterpretationInput) -> None:
    room = owner._room
    async with room.lock:
        if not owner._interpretation_current(work):
            return
    try:
        decision = await owner._workflows.interpretation_request(request)
        error = None
    except Exception as failure:
        decision, error = None, safe_generation_error(failure)
    # Obsolete provider completions cannot catch up or mutate a newer run.
    async with room.lock:
        if (room.closed or room.run_id != work.run_id
                or room.interpretation_id != work.interpretation_id
                or room.pending_submission is not work.pending):
            return
    await owner._expire_deadline()
    next_clock = generation_id = feedback_id = None
    async with room.lock:
        if not owner._interpretation_current(work):
            return
        now = owner._workflows.now()
        if error is not None:
            room.interpretation_failed(work.interpretation_id, work.pending, error, now)
            outcome = "failed"
        else:
            try:
                outcome = room.interpret(room.defense, decision, work.interpretation_id,
                                         work.pending, room.online_players(), now)
            except ValueError as failure:
                if not room.interpretation_failed(work.interpretation_id, work.pending, str(failure), now):
                    return
                outcome = "failed"
        if outcome is None:
            return
        if outcome in {"answered", "probed"}:
            attach_provenance(room, work.pending.turn, work.pending.probe_id, work.pending.input_provenance)
        if outcome in {"clarified", "probed", "failed"}:
            next_clock = (room.clock_id, room.answer_deadline_ms)
        elif outcome == "answered":
            generation_id, feedback_id = owner._resolve_turn_locked()
        room.revision += 1
    await owner._publish()
    if next_clock:
        owner._schedule_clock(*next_clock)
    if generation_id is not None:
        owner._schedule_question(generation_id, False)
    if feedback_id is not None:
        owner._schedule_coaching(feedback_id)


def attach_provenance(room, turn_index, probe_id, provenance):
    turn = room.defense.turns[turn_index]
    if probe_id is not None:
        if turn.probe and turn.probe.id == probe_id:
            turn.probe_input_provenance = provenance
    else:
        turn.input_provenance = provenance


async def handle_submission(owner: "RoomCoordinator", actor: VerifiedActor,
                            command: SubmissionCommand) -> CommandResult:
    room = owner._room
    generation_id = feedback_id = interpretation_id = None
    expired = False
    result = CommandResult(True)
    async with room.lock:
        if room.closed:
            return CommandResult(False, "Room not found. Create a fresh room.")
        try:
            player = owner._player(actor)
            now = owner._workflows.now()
            provenance = None
            if isinstance(command, (SubmitAnswer, SubmitDirectAnswer, SubmitProbeReply)) and command.voice_attempt is not None:
                provenance = validate_submission(owner, actor, command.turn, command.answer, command.voice_attempt, command.probe_id if isinstance(command, SubmitProbeReply) else None)
            if (isinstance(command, (RetryInterpretation, UsePendingAnswer))
                    and room.phase == "interpretation_retry"
                    and room.answer_deadline_ms is not None and now >= room.answer_deadline_ms):
                raise DeadlineExpired("Answer time is over.")
            cap = limit('AI_INTERPRETATION_ATTEMPTS', 6, 20)
            attempt_key = f'interpret:{len(room.defense.turns)-1}' if room.defense else ''
            if isinstance(command, DiscardVoiceDraft):
                draft = room.speech.draft
                if draft and draft.token == actor.token and draft.id == command.attempt_id:
                    room.speech.draft = None
                    if room.speech.current and room.speech.current.id == command.attempt_id:
                        room.speech.revoke()
            elif isinstance(command, RetryInterpretation):
                if room.phase != 'interpretation_retry' or room.pending_submission is None or not (player.is_host or room.selected_seat == player.seat):
                    raise ValueError('Only the host or chosen defender can retry a failed submission.')
                if room.interpretation_attempts >= cap:
                    raise ValueError('Interpretation allowance used. Use the saved submission as an answer.')
                room.ai_budget.admit(attempt_key, cap, room.owner_account_id or room.code)
                room.retry_interpretation(is_host=player.is_host, seat=player.seat, now=now)
                interpretation_id = room.interpretation_id
            elif isinstance(command, UsePendingAnswer):
                provenance = room.pending_submission.input_provenance if room.pending_submission else None
                turn_index = room.pending_submission.turn if room.pending_submission else None
                probe_id = room.pending_submission.probe_id if room.pending_submission else None
                room.accept_saved_answer(room.defense, player.token, player.seat)
                if turn_index is not None:
                    attach_provenance(room, turn_index, probe_id, provenance)
                generation_id, feedback_id = owner._resolve_turn_locked()
            elif isinstance(command, SubmitDirectAnswer):
                room.submit_direct(player.token, player.name, player.seat, command.turn,
                                   command.answer, room.defense, now)
                generation_id, feedback_id = owner._resolve_turn_locked()
            elif isinstance(command, FinishProbe):
                if room.phase != "interpretation_retry" and not room.probe_recovery_available and room.interpretation_attempts < cap and room.ai_budget.remaining(attempt_key, cap) > 0:
                    raise ValueError("Continue with the original answer is available during probe recovery.")
                room.finish_probe(player.seat, command.turn, command.probe_id, room.defense, now)
                generation_id, feedback_id = owner._resolve_turn_locked()
            elif isinstance(command, SubmitProbeReply):
                room.validate_submit(player.seat, command.turn, command.answer, room.defense,
                                     now, direct=command.direct, probe_id=command.probe_id)
                if not isinstance(command.probe_id, str) or not command.probe_id:
                    raise ValueError("A current panelist probe identifier is required.")
                if not command.direct:
                    room.ai_budget.admit(attempt_key, cap, room.owner_account_id or room.code)
                room.submit_probe_reply(player.token, player.name, player.seat, command.turn,
                    command.probe_id, command.answer, room.defense, now, direct=command.direct)
                if command.direct:
                    generation_id, feedback_id = owner._resolve_turn_locked()
                else:
                    interpretation_id = room.interpretation_id
            elif isinstance(command, SubmitAnswer):
                room.validate_submit(player.seat, command.turn, command.answer, room.defense, now)
                room.ai_budget.admit(attempt_key, cap, room.owner_account_id or room.code)
                room.submit(player.token, player.name, player.seat, command.turn,
                            command.answer, room.defense, now)
                interpretation_id = room.interpretation_id
        except HTTPException as failure:
            result = CommandResult(False, str(failure.detail), "ai_admission" if failure.status_code == 429 else None)
            if isinstance(command, SubmitProbeReply) and failure.status_code == 429:
                room.probe_recovery_available = True
        except ValueError as failure:
            result = CommandResult(False, str(failure))
            expired = isinstance(failure, DeadlineExpired)
        else:
            if isinstance(command, (SubmitAnswer, SubmitDirectAnswer, SubmitProbeReply)):
                if room.pending_submission:
                    room.pending_submission = replace(room.pending_submission, input_provenance=provenance)
                else:
                    attach_provenance(room, command.turn, command.probe_id if isinstance(command, SubmitProbeReply) else None, provenance)
            if interpretation_id is not None:
                owner._schedule_clock(room.clock_id, room.active_deadline_ms)
                # Claim task identity and capture inputs before publication awaits.
                owner._schedule_interpretation(interpretation_id)
            room.revision += 1
    if expired:
        await owner._expire_deadline()
    if not result.accepted:
        return result
    await owner._publish()
    if generation_id is not None:
        owner._schedule_question(generation_id, False)
    if feedback_id is not None:
        owner._schedule_coaching(feedback_id)
    return result

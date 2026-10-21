"""Submission rules and detached interpretation; the coordinator owns tasks."""

import asyncio
import copy
from dataclasses import dataclass, replace
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING

from fastapi import HTTPException
from backend.project_files import ProjectFile
from backend.question_generator import (
    DEFAULT_MODEL, GroundedQuestion, AnsweredQuestion, ClarificationExchange,
    CombinedSubmissionDraft, PanelistProbe, QuestionGenerationError, SubmissionDecision,
    interpret_submission,
)
from backend.openrouter_questions import (
    COMBINED_PLANNING, COMBINED_PLANNING_GUIDANCE, RunQuestionClient, run_scope,
)
from backend.processing_policy import ProcessingWindowExpired, decide_retry
from backend.resource_limits import limit
from backend.timed_turn import PendingSubmission, DeadlineExpired
from backend.defense_session import PlannedMove, ResearchDefenseSession
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
    planning_contract: str = ''
    planning_session: ResearchDefenseSession | None = None
    recovery_namespace: str | None = None


def capture_interpretation(room: "Room", pending: PendingSubmission, *,
                           provider_stopped: Callable[[], bool] | None = None) -> InterpretationInput:
    """Capture under the room lock; mutable probe/history data is detached."""
    turn = room.defense.turns[pending.turn]
    research = isinstance(room.defense, ResearchDefenseSession)
    context = room.defense.context() if research else None
    if context is not None:
        context = copy.deepcopy(context)
        context["current_topic"] = turn.topic_id
    funded = bool(room.run_id and room.owner_account_id and research)
    combined = (funded and pending.probe_id is None
                and room.planning_contract == COMBINED_PLANNING)
    planning_session = None
    if combined:
        planning_session = copy.deepcopy(room.defense)
        prospective = planning_session.turns[pending.turn]
        prospective.answer = pending.text
        prospective.speaker_name = pending.name
        prospective.input_provenance = pending.input_provenance
        context = planning_session.context()
        context["current_topic"] = prospective.topic_id
    return InterpretationInput(pending, tuple(room.files), turn.panelist, turn.question,
        tuple(turn.clarifications), tuple(copy.deepcopy(room.defense.answered_history())),
        room.defense_type, room.research_stage, copy.deepcopy(turn.probe) if pending.probe_id else None,
        turn.answer, turn.speaker_name, context,
        provider_scope=run_scope(room.run_id) if funded else None,
        provider_owner=room.owner_account_id if funded else None,
        provider_stopped=provider_stopped if funded else None,
        planning_contract=room.planning_contract,
        planning_session=planning_session,
        recovery_namespace=(f'{room.code}:{room.defense_view_id}:{room.preparation_id}'
                            if combined else None))


InterpretationRequest = Callable[[InterpretationInput], Awaitable[SubmissionDecision]]


async def request_interpretation(request: InterpretationInput) -> SubmissionDecision:
    funded = None
    combined = (request.planning_session is not None
                and request.planning_contract == COMBINED_PLANNING)
    if request.provider_scope and request.provider_owner:
        funded = RunQuestionClient(request.provider_scope, request.provider_owner,
                                   request.planning_session, request.files,
                                   stopped=request.provider_stopped or (lambda: False))
    client = funded.interaction(request.panelist, combined=combined) if funded else None
    extra = {}
    if combined:
        extra.update(text_format=CombinedSubmissionDraft,
                     planning_context=request.research_context,
                     planning_guidance=COMBINED_PLANNING_GUIDANCE)
    decision = await asyncio.to_thread(
        interpret_submission, list(request.files), None,
        panelist=request.panelist, question=request.question, submission=request.pending.text,
        clarifications=request.clarifications, history=request.history,
        model=DEFAULT_MODEL, client=client,
        defense_type=request.defense_type, research_stage=request.research_stage,
        **({"research_context": request.research_context} if request.research_context else {}),
        **({"probe": request.probe, "original_answer": request.original_answer,
            "original_speaker_name": request.original_speaker_name,
            "speaker_name": request.pending.name} if request.probe else {}),
        **extra,
    )
    if not combined or decision.action != 'answer':
        return decision
    if decision.plan is None:
        raise QuestionGenerationError('The AI returned an incomplete research plan. Please retry.')
    planned = PlannedMove(decision.plan.panelist, decision.plan.topic_id,
                          decision.plan.is_follow_up, decision.plan.assessment)
    request.planning_session.validate_plan(planned)
    identity = funded.plan_identity(
        history=request.planning_session.answered_history(),
        context=request.planning_session.context(),
        defense_type=request.defense_type, research_stage=request.research_stage)
    return replace(decision, plan_identity=identity)


async def run_interpretation(owner: "RoomCoordinator", work: InterpretationWork,
                             request: InterpretationInput) -> None:
    room = owner._room
    now = owner._workflows.now()
    async with room.lock:
        if not owner._interpretation_current(work):
            return
        room.begin_operation(kind="interpretation", operation_id=f"interpretation:{work.interpretation_id}",
                             stage="reviewing_reply" if work.pending.probe_id else "reviewing_answer",
                             now=now, window_deadline_ms=room.next_processing_deadline(now))
        room.revision += 1
    await owner._publish()
    failure_class = None
    decision = None
    error = None
    attempt = 0
    try:
        while True:
            async with room.lock:
                if not owner._interpretation_current(work):
                    break
                now = owner._workflows.now()
                if room.processing_expired(now):
                    raise ProcessingWindowExpired(room.processing_policy.expiry_message())
                if attempt:
                    room.resume_operation(now, stage=(
                        "reviewing_reply" if work.pending.probe_id else "reviewing_answer"))
                    room.revision += 1
            if attempt:
                await owner._publish()
            try:
                operation = room.operation
                assert operation is not None
                remaining = room.processing_policy.remaining_ms(operation.window_deadline_ms,
                                                                owner._workflows.now())
                if remaining is not None and remaining <= 0:
                    raise ProcessingWindowExpired(room.processing_policy.expiry_message())
                if remaining is None:
                    decision = await owner._workflows.interpretation_request(request)
                else:
                    try:
                        decision = await asyncio.wait_for(
                            owner._workflows.interpretation_request(request),
                            timeout=remaining / 1000)
                    except TimeoutError as failure:
                        raise ProcessingWindowExpired(room.processing_policy.expiry_message()) from failure
                error = None
            except Exception as failure:
                decision, error = None, safe_generation_error(failure)
                failure_class = type(failure).__name__
                async with room.lock:
                    if (room.closed or room.run_id != work.run_id
                            or room.interpretation_id != work.interpretation_id
                            or room.pending_submission is not work.pending):
                        return
                    now = owner._workflows.now()
                    if not owner._interpretation_current(work):
                        break
                    if room.processing_expired(now):
                        error = room.processing_policy.expiry_message()
                        failure_class = "ProcessingWindowExpired"
                        break
                    if (attempt >= room.processing_policy.automatic_retries
                            or room.processing_policy.version == 'legacy'
                            or room.interaction_transient_retries
                            >= room.processing_policy.automatic_retries):
                        break
                    operation = room.operation
                    deadline = operation.window_deadline_ms if operation else None
                    attempts_remaining = max(0, limit('AI_INTERPRETATION_ATTEMPTS', 6, 20)
                                             - room.interpretation_attempts)
                    retry = decide_retry(failure, room.processing_policy, now, deadline,
                                         attempts_remaining)
                    if not retry.allowed:
                        if retry.supplemental:
                            error = f"{error} {retry.supplemental}"
                        break
                    try:
                        attempt_key = f'interpret:{len(room.defense.turns)-1}' if room.defense else ''
                        room.ai_budget.admit(attempt_key, limit('AI_INTERPRETATION_ATTEMPTS', 6, 20),
                                             room.owner_account_id or room.code)
                    except HTTPException as denied:
                        error = safe_generation_error(denied)
                        failure_class = "HTTPException"
                        break
                    room.interpretation_attempts += 1
                    room.interaction_transient_retries += 1
                    room.retry_operation(now, retry_at_ms=now + retry.delay_ms)
                    room.revision += 1
                await owner._publish()
                await owner._workflows.sleep(retry.delay_ms / 1000)
                attempt += 1
                continue
            async with room.lock:
                if (room.closed or room.run_id != work.run_id
                        or room.interpretation_id != work.interpretation_id
                        or room.pending_submission is not work.pending):
                    return
                if room.processing_expired(owner._workflows.now()):
                    decision = None
                    error = room.processing_policy.expiry_message()
                    failure_class = "ProcessingWindowExpired"
            break
    except Exception as failure:
        decision, error = None, safe_generation_error(failure)
        failure_class = type(failure).__name__
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
            room.clear_interaction_window()
            outcome = "failed"
        else:
            try:
                outcome = room.interpret(room.defense, decision, work.interpretation_id,
                                         work.pending, room.online_players(), now)
            except ValueError as failure:
                failure_class = type(failure).__name__
                if not room.interpretation_failed(work.interpretation_id, work.pending, str(failure), now):
                    return
                outcome = "failed"
            if (outcome == "answered" and decision is not None and decision.plan is not None
                    and decision.plan_identity and request.recovery_namespace):
                room.question_recovery.seed(
                    request.recovery_namespace, decision.plan_identity,
                    PlannedMove(decision.plan.panelist, decision.plan.topic_id,
                                decision.plan.is_follow_up, decision.plan.assessment))
        if outcome is None:
            room.finish_operation(now, "failed")
            room.clear_interaction_window()
            return
        if outcome in {"answered", "probed"}:
            attach_provenance(room, work.pending.turn, work.pending.probe_id, work.pending.input_provenance)
        if outcome in {"clarified", "probed", "failed"}:
            next_clock = (room.clock_id, room.answer_deadline_ms)
        elif outcome == "answered":
            generation_id, feedback_id = owner._resolve_turn_locked()
        if outcome != "answered":
            room.clear_interaction_window()
        room.finish_operation(now, "failed" if outcome == "failed" else "succeeded",
                              failure_class=failure_class if outcome == "failed" else None)
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
                room.begin_interaction_window(now)
                interpretation_id = room.interpretation_id
            elif isinstance(command, UsePendingAnswer):
                provenance = room.pending_submission.input_provenance if room.pending_submission else None
                turn_index = room.pending_submission.turn if room.pending_submission else None
                probe_id = room.pending_submission.probe_id if room.pending_submission else None
                room.accept_saved_answer(room.defense, player.token, player.seat)
                room.clear_interaction_window()
                if turn_index is not None:
                    attach_provenance(room, turn_index, probe_id, provenance)
                generation_id, feedback_id = owner._resolve_turn_locked()
            elif isinstance(command, SubmitDirectAnswer):
                room.submit_direct(player.token, player.name, player.seat, command.turn,
                                   command.answer, room.defense, now)
                room.clear_interaction_window()
                generation_id, feedback_id = owner._resolve_turn_locked()
            elif isinstance(command, FinishProbe):
                if room.phase != "interpretation_retry" and not room.probe_recovery_available and room.interpretation_attempts < cap and room.ai_budget.remaining(attempt_key, cap) > 0:
                    raise ValueError("Continue with the original answer is available during probe recovery.")
                room.finish_probe(player.seat, command.turn, command.probe_id, room.defense, now)
                room.clear_interaction_window()
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
                    room.clear_interaction_window()
                    generation_id, feedback_id = owner._resolve_turn_locked()
                else:
                    room.begin_interaction_window(now)
                    interpretation_id = room.interpretation_id
            elif isinstance(command, SubmitAnswer):
                room.validate_submit(player.seat, command.turn, command.answer, room.defense, now)
                room.ai_budget.admit(attempt_key, cap, room.owner_account_id or room.code)
                room.submit(player.token, player.name, player.seat, command.turn,
                            command.answer, room.defense, now)
                room.begin_interaction_window(now)
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

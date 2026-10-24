"""Detached question generation and validation; the coordinator owns its tasks."""

import asyncio
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING
from collections.abc import Awaitable, Callable
from fastapi import HTTPException
from openai import APIConnectionError, APIStatusError
from pydantic import ValidationError
from backend.account_store import charge_run, release_run
from backend.defense_progression import PreparedProgression, prepare_progression, commit_progression
from backend.defense_session import ResearchDefenseSession
from backend.project_files import ProjectFile
from backend.financial_policy import live_mode
from backend.live_store import LiveStore
from backend.opening_history import OpeningQuestion, RepeatedOpening, paper_key, recent_openings
from backend.openrouter_questions import RunQuestionClient, run_scope
from backend.openrouter_stream import TransientProviderError
from backend.processing_policy import (
    ProcessingWindowExpired, decide_retry, transient_directive,
)
from backend.resource_limits import limit
from backend.question_generator import (
    DEFAULT_MODEL, InvalidQuestionResponse, QuestionGenerationError, generate_first_question,
    generate_next_move, generate_research_move,
    GroundedQuestion, PanelMove, ResearchMove,
)
from backend.rooms.openings import OpeningCandidate
from backend.rooms.errors import safe_generation_error

if TYPE_CHECKING:
    from backend.rooms.coordinator import RoomCoordinator


@dataclass(frozen=True)
class QuestionWork:
    generation_id: int
    first: bool
    run_id: str | None
    retrying: bool = False


QuestionResult = GroundedQuestion | PanelMove | ResearchMove
QuestionRequest = Callable[[PreparedProgression, tuple[ProjectFile, ...]], Awaitable[QuestionResult]]


async def request_question(request: PreparedProgression, files: tuple[ProjectFile, ...]) -> QuestionResult:
    client = None
    if request.provider_scope and request.provider_owner and isinstance(request.session, ResearchDefenseSession):
        client = RunQuestionClient(request.provider_scope, request.provider_owner, request.session, files,
                                   stopped=request.provider_stopped or (lambda: False),
                                   recovery=request.provider_recovery)
    return await asyncio.to_thread(request.generate, list(files), None,
        DEFAULT_MODEL, client=client,
        first_question=generate_first_question,
        next_move=generate_next_move, research_move=generate_research_move)


async def run_question(owner: "RoomCoordinator", work: QuestionWork) -> None:
    room, first = owner._room, work.first
    next_clock = None
    feedback_id = None
    repeated_candidate = None
    window_deadline = None
    try:
        # Each candidate is detached. History and access commit before publication;
        # rejected/racing duplicate candidates roll back without charging the run.
        for attempt in range(2):
            started = False
            if attempt:
                async with room.lock:
                    if not owner._question_current(work):
                        return
                    now = owner._workflows.now()
                    if room.processing_expired(now):
                        raise ProcessingWindowExpired(room.processing_policy.expiry_message())
                    room.resume_operation(now)
                    room.revision += 1
                await owner._publish()
            async with room.lock:
                if not owner._question_current(work):
                    return
                now = owner._workflows.now()
                if attempt == 0:
                    room.begin_operation(kind="question", operation_id=f"question:{work.generation_id}",
                                         stage="generating", now=now,
                                         retrying=work.retrying,
                                         window_deadline_ms=room.next_processing_deadline(now))
                    room.revision += 1
                    started = True
                if room.processing_expired(now):
                    raise ProcessingWindowExpired(room.processing_policy.expiry_message())
                cap = limit('AI_QUESTION_ATTEMPTS', 3, 10)
                attempt_key = f'question:{len(room.defense.turns) if room.defense else 0}'
                request = prepare_progression(room.defense, defense_type=room.defense_type,
                                              research_stage=room.research_stage)
                files = tuple(room.files)
                window_deadline = (room.operation.window_deadline_ms
                                   if room.operation else None)
                opening_key = None
                if room.owner_account_id and room.run_id and room.defense_type != "code" and (room.defense is None or not room.defense.turns):
                    opening_key = paper_key(files)
                account_id = room.owner_account_id
            if started:
                await owner._publish()
            if opening_key:
                remaining = room.processing_policy.remaining_ms(
                    window_deadline, owner._workflows.now())
                if remaining is not None and remaining <= 0:
                    raise ProcessingWindowExpired(room.processing_policy.expiry_message())
                try:
                    lookup = asyncio.to_thread(recent_openings, account_id, opening_key)
                    if remaining is None:
                        recent = await lookup
                    else:
                        try:
                            recent = await asyncio.wait_for(lookup, timeout=remaining / 1000)
                        except TimeoutError as failure:
                            raise ProcessingWindowExpired(
                                room.processing_policy.expiry_message()) from failure
                except ProcessingWindowExpired:
                    raise
                except Exception as failure:
                    raise QuestionGenerationError("Recent opening history could not be checked. No defense was charged; retry when storage recovers.") from failure
                request = replace(request, recent_openings=tuple(recent))
            async with room.lock:
                if not owner._question_current(work):
                    return
                if room.run_id and room.owner_account_id and isinstance(request.session, ResearchDefenseSession):
                    request = replace(request, provider_scope=run_scope(room.run_id),
                                      provider_owner=room.owner_account_id,
                                      provider_stopped=lambda: (
                                          not owner._question_current(work)
                                          or (window_deadline is not None
                                              and owner._workflows.now() >= window_deadline)),
                                      provider_recovery=room.question_recovery.claim(
                                          f'{room.code}:{room.defense_view_id}:{room.preparation_id}'))
                if room.processing_expired(owner._workflows.now()):
                    raise ProcessingWindowExpired(room.processing_policy.expiry_message())
                room.ai_budget.admit(attempt_key, cap, room.owner_account_id or room.code)
            try:
                now = owner._workflows.now()
                operation = room.operation
                assert operation is not None
                remaining = room.processing_policy.remaining_ms(operation.window_deadline_ms, now)
                if remaining is not None and remaining <= 0:
                    raise ProcessingWindowExpired(room.processing_policy.expiry_message())
                if remaining is None:
                    result = await owner._workflows.question_request(request, files)
                else:
                    try:
                        result = await asyncio.wait_for(
                            owner._workflows.question_request(request, files),
                            timeout=remaining / 1000)
                    except TimeoutError as error:
                        raise ProcessingWindowExpired(room.processing_policy.expiry_message()) from error
                try:
                    session = request.apply(result)
                except ValueError as error:
                    raise InvalidQuestionResponse(str(error)) from error
                async with room.lock:
                    if not owner._question_current(work):
                        return
                    if room.processing_expired(owner._workflows.now()):
                        raise ProcessingWindowExpired(room.processing_policy.expiry_message())
                    room.question_retry_generation_id = None
                    opening = room.defense is None or not room.defense.turns
                    if room.run_id and opening and session.turns:
                        if opening_key:
                            turn = session.turns[0]
                            candidate = OpeningQuestion(opening_key, turn.question.question, turn.panelist, turn.topic_id)
                            try:
                                charge_run(room.owner_account_id, room.run_id, opening=candidate)
                            except RepeatedOpening:
                                repeated_candidate = OpeningCandidate(room.run_id, work.generation_id,
                                    room.research_plan.id, opening_key, result)
                                raise
                            except Exception as failure:
                                raise QuestionGenerationError("Opening history and access could not be saved. No new opening was charged; retry when storage recovers.") from failure
                        else:
                            charge_run(room.owner_account_id, room.run_id)
                    elif live_mode() and room.run_id:
                        LiveStore().service_state(room.run_id, "coaching" if session.completed else "active")
                    room.defense = commit_progression(room.defense, session)
                    if room.defense.completed:
                        room.phase = "complete"
                        room.feedback_status = "generating"
                        room.feedback_generation_id += 1
                        feedback_id = room.feedback_generation_id
                    else:
                        room.present_question(room.defense, owner._workflows.now())
                        next_clock = (room.clock_id, room.reaction_deadline_ms or room.vote_deadline_ms)
                    room.error = None
                    room.finish_operation(owner._workflows.now(), "succeeded")
                    room.clear_interaction_window()
                    room.revision += 1
            except (RepeatedOpening, InvalidQuestionResponse, ValidationError, APIConnectionError, APIStatusError,
                    TransientProviderError) as error:
                transient = transient_directive(error) is not None
                recoverable = transient or isinstance(
                    error, (RepeatedOpening, InvalidQuestionResponse, ValidationError))
                async with room.lock:
                    if not owner._question_current(work):
                        return
                    resolved = room.defense is not None and bool(room.defense.turns) and (
                        room.defense.turns[-1].answer is not None or room.defense.turns[-1].timed_out)
                    duplicate = isinstance(error, RepeatedOpening)
                    if (attempt or not recoverable
                            or (not transient and not duplicate and (first or not resolved))
                            or (transient and room.processing_policy.version == 'legacy'
                                and (first or not resolved))
                            or (transient and room.interaction_transient_retries
                                >= room.processing_policy.automatic_retries)
                            or not room.ai_budget.remaining(attempt_key, cap)):
                        raise
                    now = owner._workflows.now()
                    operation = room.operation
                    deadline = operation.window_deadline_ms if operation else None
                    if transient:
                        decision = decide_retry(error, room.processing_policy, now, deadline, 1)
                        if not decision.allowed:
                            if decision.supplemental:
                                raise QuestionGenerationError(
                                    f'{safe_generation_error(error)} {decision.supplemental}') from error
                            raise
                        delay_ms = decision.delay_ms
                    else:
                        if room.processing_expired(now):
                            raise ProcessingWindowExpired(room.processing_policy.expiry_message())
                        delay_ms = 0 if duplicate else 1000
                        if deadline is not None and now + delay_ms >= deadline:
                            raise QuestionGenerationError(
                                f'{safe_generation_error(error)} The automatic retry would exceed '
                                'the remaining processing window. Use recovery to retry manually.') from error
                    room.question_retry_generation_id = work.generation_id
                    if transient:
                        room.interaction_transient_retries += 1
                    room.retry_operation(now, retry_at_ms=(
                        None if duplicate or room.processing_policy.version == 'legacy'
                        else now + delay_ms))
                    room.revision += 1
                await owner._publish()
                if not duplicate:
                    await owner._workflows.sleep(delay_ms / 1000)
                continue
            break
    except Exception as error:
        async with room.lock:
            if not owner._question_current(work):
                return
            now = owner._workflows.now()
            if room.processing_expired(now) or (
                    window_deadline is not None and now >= window_deadline):
                error = ProcessingWindowExpired(room.processing_policy.expiry_message())
            room.question_retry_generation_id = None
            room.phase = "retry"
            room.opening_candidate = repeated_candidate if isinstance(error, RepeatedOpening) else None
            room.error = str(error) if isinstance(error, RepeatedOpening) else safe_generation_error(error)
            room.finish_operation(now, "failed", failure_class=type(error).__name__)
            room.clear_interaction_window()
            try:
                if room.defense is None or not room.defense.turns:
                    release_run(room.run_id)
                    room.settled = True
                elif live_mode() and room.run_id and not isinstance(error, HTTPException):
                    LiveStore().service_state(room.run_id,"unavailable","question")
            except Exception:
                room.error="The defense state could not be saved. Your answers are retained; retry when the service recovers."
            room.revision += 1
        await owner._publish()
        return
    await owner._publish()
    if next_clock:
        owner._schedule_clock(*next_clock)
    if feedback_id is not None:
        owner._schedule_coaching(feedback_id)

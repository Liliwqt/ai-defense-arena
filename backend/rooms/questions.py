"""Detached question generation and validation; the coordinator owns its tasks."""

import asyncio
from dataclasses import dataclass, replace
import os
from typing import TYPE_CHECKING
from collections.abc import Awaitable, Callable
from fastapi import HTTPException
from openai import APIConnectionError, APIStatusError
from pydantic import ValidationError
from backend.account_store import charge_run, release_run
from backend.defense_progression import PreparedProgression, prepare_progression, commit_progression
from backend.project_files import ProjectFile
from backend.financial_policy import live_mode
from backend.live_store import LiveStore
from backend.opening_history import OpeningQuestion, RepeatedOpening, paper_key, recent_openings
from backend.resource_limits import limit
from backend.question_generator import (
    DEFAULT_MODEL, InvalidQuestionResponse, QuestionGenerationError, generate_first_question,
    generate_next_move, generate_research_move,
    GroundedQuestion, PanelMove, ResearchMove,
)
from backend.rooms.errors import safe_generation_error

if TYPE_CHECKING:
    from backend.rooms.coordinator import RoomCoordinator


@dataclass(frozen=True)
class QuestionWork:
    generation_id: int
    first: bool
    run_id: str | None


QuestionResult = GroundedQuestion | PanelMove | ResearchMove
QuestionRequest = Callable[[PreparedProgression, tuple[ProjectFile, ...]], Awaitable[QuestionResult]]


async def request_question(request: PreparedProgression, files: tuple[ProjectFile, ...]) -> QuestionResult:
    return await asyncio.to_thread(request.generate, list(files), os.getenv("OPENAI_API_KEY"),
        os.getenv("OPENAI_MODEL") or DEFAULT_MODEL, first_question=generate_first_question,
        next_move=generate_next_move, research_move=generate_research_move)


async def run_question(owner: "RoomCoordinator", work: QuestionWork) -> None:
    room, first = owner._room, work.first
    next_clock = None
    feedback_id = None
    try:
        # Each candidate is detached. History and access commit before publication;
        # rejected/racing duplicate candidates roll back without charging the run.
        for attempt in range(2):
            async with room.lock:
                if not owner._question_current(work):
                    return
                cap = limit('AI_QUESTION_ATTEMPTS', 3, 10)
                attempt_key = f'question:{len(room.defense.turns) if room.defense else 0}'
                request = prepare_progression(room.defense, defense_type=room.defense_type,
                                              research_stage=room.research_stage)
                files = tuple(room.files)
                opening_key = None
                if room.owner_account_id and room.run_id and room.defense_type != "code" and (room.defense is None or not room.defense.turns):
                    opening_key = paper_key(files)
                    try:
                        recent = recent_openings(room.owner_account_id, opening_key)
                    except Exception as failure:
                        raise QuestionGenerationError("Recent opening history could not be checked. No defense was charged; retry when storage recovers.") from failure
                    request = replace(request, recent_openings=tuple(recent))
                room.ai_budget.admit(attempt_key, cap, room.owner_account_id or room.code)
            try:
                result = await owner._workflows.question_request(request, files)
                try:
                    session = request.apply(result)
                except ValueError as error:
                    raise InvalidQuestionResponse(str(error)) from error
                async with room.lock:
                    if not owner._question_current(work):
                        return
                    room.question_retry_generation_id = None
                    opening = room.defense is None or not room.defense.turns
                    if room.run_id and opening and session.turns:
                        if opening_key:
                            turn = session.turns[0]
                            candidate = OpeningQuestion(opening_key, turn.question.question, turn.panelist, turn.topic_id)
                            try:
                                charge_run(room.owner_account_id, room.run_id, opening=candidate)
                            except RepeatedOpening:
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
                    room.revision += 1
            except (RepeatedOpening, InvalidQuestionResponse, ValidationError, APIConnectionError, APIStatusError) as error:
                recoverable = not isinstance(error, APIStatusError) or error.status_code >= 500
                async with room.lock:
                    if not owner._question_current(work):
                        return
                    resolved = room.defense is not None and bool(room.defense.turns) and (
                        room.defense.turns[-1].answer is not None or room.defense.turns[-1].timed_out)
                    duplicate = isinstance(error, RepeatedOpening)
                    if attempt or not recoverable or (not duplicate and (first or not resolved)) or not room.ai_budget.remaining(attempt_key, cap):
                        raise
                    room.question_retry_generation_id = work.generation_id
                    room.revision += 1
                await owner._publish()
                if not duplicate:
                    await owner._workflows.sleep(1)
                continue
            break
    except Exception as error:
        async with room.lock:
            if not owner._question_current(work):
                return
            room.question_retry_generation_id = None
            room.phase = "retry"
            room.error = str(error) if isinstance(error, RepeatedOpening) else safe_generation_error(error)
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

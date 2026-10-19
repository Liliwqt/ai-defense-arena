"""Detached final coaching and settlement; the coordinator owns task identity."""

import asyncio
import copy
from dataclasses import dataclass, replace
import os
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING

from fastapi import HTTPException
from backend.defense_session import ResearchDefenseSession
from backend.financial_policy import live_mode
from backend.live_store import LiveStore
from backend.project_files import ProjectFile
from backend.question_generator import DEFAULT_MODEL, AnsweredQuestion, CoachingReport, generate_coaching_report
from backend.research_coaching import validate_complete, has_discussion, factual_cards
from backend.openrouter_questions import RunQuestionClient, run_scope
from backend.coaching_progress import CoachingInput
from backend.resource_limits import limit
from backend.timed_turn import reaction_reading_ms
from backend.rooms.commands import CommandResult, VerifiedActor
from backend.rooms.errors import safe_generation_error

if TYPE_CHECKING:
    from backend.rooms.coordinator import RoomCoordinator
    from backend.rooms.model import Room


@dataclass(frozen=True)
class CoachingWork:
    generation_id: int
    run_id: str | None




def capture_coaching(room: "Room") -> CoachingInput:
    """Capture under the room lock so later room mutations cannot change input."""
    context = room.defense.context() if isinstance(room.defense, ResearchDefenseSession) else None
    history = room.defense.coaching_history() if room.defense_type != "code" else room.defense.answered_history()
    funded = bool(context is not None and room.run_id and room.owner_account_id)
    return CoachingInput(tuple(room.files), tuple(copy.deepcopy(history)),
                         copy.deepcopy(context), room.defense_type, room.research_stage,
                         provider_scope=run_scope(room.run_id) if funded else None,
                         provider_owner=room.owner_account_id if funded else None)


CoachingRequest = Callable[[CoachingInput], Awaitable[CoachingReport]]


async def request_coaching(request: CoachingInput) -> CoachingReport:
    client = None
    if request.provider_scope and request.provider_owner:
        client = RunQuestionClient(request.provider_scope, request.provider_owner, None,
                                   request.files, stopped=request.provider_stopped or (lambda: False)).coaching()
    return await asyncio.to_thread(generate_coaching_report, list(request.files), list(request.history),
        os.getenv("OPENAI_API_KEY"), os.getenv("OPENAI_MODEL") or DEFAULT_MODEL,
        defense_type=request.defense_type, research_stage=request.research_stage,
        **({"client": client} if client is not None else {}),
        **({"overview_only": True} if request.overview_only else {}),
        **({"section_turns": request.section_turns} if request.section_turns is not None else {}),
        **({"research_context": request.research_context} if request.research_context else {}))


async def run_coaching(owner: "RoomCoordinator", work: CoachingWork, request: CoachingInput) -> None:
    room = owner._room
    if request.defense_type != "code":
        return await run_progressive_coaching(owner, work)
    next_clock = None
    try:
        async with room.lock:
            if not owner._coaching_current(work):
                return
            if has_discussion(request.history):
                room.ai_budget.admit('coaching', limit('AI_COACHING_ATTEMPTS', 3, 10), room.owner_account_id or room.code)
        if not has_discussion(request.history):
            report = CoachingReport("The host ended the defense before any answer or timeout was recorded. No discussion coverage was confirmed.", [], [], "Review the paper map and start a new defense when the team is ready.",
                answer_cards=factual_cards(request.history) if request.defense_type != "code" else None)
        else:
            report = await owner._workflows.coaching_request(request)
        validate_complete(report, request.history, request.defense_type)
        async with room.lock:
            if not owner._coaching_current(work):
                return
            if live_mode() and work.run_id:
                LiveStore().finish_run(work.run_id, "completed")
            room.settled = True
            room.terminal_ms = owner._workflows.now()
            room.feedback = report
            room.feedback_status = "ready"
            owner._clear_clock()
            closing_history = [item for item in request.history if not item.ended_early]
            if report.closing and closing_history:
                room.closing_panelist = closing_history[-1].panelist
                room.closing_deadline_ms = room.terminal_ms + reaction_reading_ms(report.closing)
                next_clock = (room.clock_id, room.closing_deadline_ms)
            room.error = None
            room.revision += 1
    except Exception as error:
        async with room.lock:
            if not owner._coaching_current(work):
                return
            room.feedback_status = "failed"
            room.error = safe_generation_error(error)
            if live_mode() and work.run_id and not isinstance(error, HTTPException):
                try:
                    LiveStore().service_state(work.run_id, "unavailable", "coaching")
                except Exception:
                    room.error = "The coaching state could not be saved. Your answers are retained; retry when the service recovers."
            room.revision += 1
        await owner._publish()
        return
    await owner._publish()
    if next_clock:
        owner._schedule_clock(*next_clock)


async def retry_coaching(owner: "RoomCoordinator", actor: VerifiedActor) -> CommandResult:
    room = owner._room
    async with room.lock:
        if room.closed:
            return CommandResult(False, "Room not found. Create a fresh room.")
        try:
            player = owner._player(actor)
        except ValueError as error:
            return CommandResult(False, str(error))
        if not player.is_host:
            return CommandResult(False, "Only the host can control the defense.")
        if room.phase != "complete" or room.feedback_status != "failed":
            return CommandResult(False, "There is no failed coaching report to retry.")
        if room.coaching_progress:
            try:room.coaching_progress.retry()
            except ValueError as error:return CommandResult(False,str(error))
        room.feedback_status = "generating"
        room.error = None
        room.feedback_generation_id += 1
        owner._schedule_coaching(room.feedback_generation_id)
        room.revision += 1
    await owner._publish()
    return CommandResult(True)


async def run_progressive_coaching(owner, work):
    room=owner._room
    job=room.coaching_progress
    def current():
        return owner._coaching_current(work) and room.coaching_progress is job and not job.cancelled
    if job is None:return
    request=job.request
    for section in job.sections:
        async with room.lock:
            if not current():return
            if section.status!='pending':continue
            job.begin(section)
            room.revision+=1
        await owner._publish()
        try:
            async with room.lock:
                if not current():return
                if has_discussion(request.history):
                    room.ai_budget.admit(f'coaching:{job.id}:{section.id}',job.attempt_limit,room.owner_account_id or room.code)
            section_request=replace(request,overview_only=section.turns is None,section_turns=section.turns,
                provider_stopped=(lambda: not current()) if request.provider_scope else None)
            if not has_discussion(request.history):
                report=CoachingReport('The host ended before any answer or timeout was recorded. No discussion coverage was confirmed.',[],[],
                    'Review the paper map and practice a direct answer when ready.',
                    answer_cards=None if section.turns is None else factual_cards(request.history,section.turns))
            else:
                report=await owner._workflows.coaching_request(section_request)
            next_clock=None
            async with room.lock:
                if not current():return
                job.accept(section,report)
                room.feedback=job.assembled()
                if section.turns is None and not job.closing_started:
                    owner._clear_clock();job.closing_started=True
                    resolved=[item for item in request.history if not item.ended_early]
                    if report.closing and resolved:
                        room.closing_panelist=resolved[-1].panelist
                        room.closing_deadline_ms=owner._workflows.now()+reaction_reading_ms(report.closing)
                        next_clock=(room.clock_id,room.closing_deadline_ms)
                room.revision+=1
            await owner._publish()
            if next_clock:owner._schedule_clock(*next_clock)
        except asyncio.CancelledError:
            raise
        except Exception as error:
            async with room.lock:
                if not current():return
                section.status='failed';section.error=safe_generation_error(error)
                room.error=section.error
                if live_mode() and work.run_id and not isinstance(error,HTTPException):
                    try:LiveStore().service_state(work.run_id,'unavailable','coaching')
                    except Exception:room.error='The coaching error could not be saved. Ready cards are retained; retry when service recovers.'
                room.revision+=1
            await owner._publish()
            if section.turns is None:break
    async with room.lock:
        if not current():return
        if not job.complete_sections:
            room.feedback_status='failed'
            room.error=room.error or 'Required coaching sections are unfinished. Ready cards are retained.'
        else:
            try:
                validate_complete(job.assembled(),request.history,request.defense_type,batched=True)
                job.completion_attempts+=1
                if live_mode() and work.run_id:
                    if LiveStore().finish_run(work.run_id,'completed')!='completed':
                        raise ValueError('This run is already terminal. Its outcome cannot be replaced.')
                job.completion_status='ready';job.completion_error=None
                room.feedback=job.assembled();room.feedback_status='ready';room.settled=True
                room.terminal_ms=owner._workflows.now();room.error=None
            except Exception as error:
                job.completion_status='failed';job.completion_error=safe_generation_error(error)
                room.feedback_status='failed';room.error=job.completion_error
                if live_mode() and work.run_id:
                    try:LiveStore().service_state(work.run_id,'unavailable','coaching')
                    except Exception:room.error='Completion could not be saved. Ready cards are retained; retry when service recovers.'
        room.revision+=1
    await owner._publish()

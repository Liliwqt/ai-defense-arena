"""Detached final coaching and settlement; the coordinator owns task identity."""

import asyncio
import copy
from dataclasses import dataclass
import os
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING

from fastapi import HTTPException
from backend.defense_session import ResearchDefenseSession
from backend.financial_policy import live_mode
from backend.live_store import LiveStore
from backend.project_files import ProjectFile
from backend.question_generator import DEFAULT_MODEL, AnsweredQuestion, CoachingReport, generate_coaching_report
from backend.resource_limits import limit
from backend.rooms.commands import CommandResult, VerifiedActor
from backend.rooms.errors import safe_generation_error

if TYPE_CHECKING:
    from backend.rooms.coordinator import RoomCoordinator
    from backend.rooms.model import Room


@dataclass(frozen=True)
class CoachingWork:
    generation_id: int
    run_id: str | None


@dataclass(frozen=True)
class CoachingInput:
    files: tuple[ProjectFile, ...]
    history: tuple[AnsweredQuestion, ...]
    research_context: dict | None
    defense_type: str
    research_stage: str


def capture_coaching(room: "Room") -> CoachingInput:
    """Capture under the room lock so later room mutations cannot change input."""
    context = room.defense.context() if isinstance(room.defense, ResearchDefenseSession) else None
    return CoachingInput(tuple(room.files), tuple(copy.deepcopy(room.defense.answered_history())),
                         copy.deepcopy(context), room.defense_type, room.research_stage)


CoachingRequest = Callable[[CoachingInput], Awaitable[CoachingReport]]


async def request_coaching(request: CoachingInput) -> CoachingReport:
    return await asyncio.to_thread(generate_coaching_report, list(request.files), list(request.history),
        os.getenv("OPENAI_API_KEY"), os.getenv("OPENAI_MODEL") or DEFAULT_MODEL,
        defense_type=request.defense_type, research_stage=request.research_stage,
        **({"research_context": request.research_context} if request.research_context else {}))


async def run_coaching(owner: "RoomCoordinator", work: CoachingWork, request: CoachingInput) -> None:
    room = owner._room
    try:
        async with room.lock:
            if not owner._coaching_current(work):
                return
            if request.history:
                room.ai_budget.admit('coaching', limit('AI_COACHING_ATTEMPTS', 3, 10), room.owner_account_id or room.code)
        if not request.history:
            report = CoachingReport("The host ended the defense before any answer or timeout was recorded. No discussion coverage was confirmed.", [], [], "Review the paper map and start a new defense when the team is ready.")
        else:
            report = await owner._workflows.coaching_request(request)
        async with room.lock:
            if not owner._coaching_current(work):
                return
            if live_mode() and work.run_id:
                LiveStore().finish_run(work.run_id, "completed")
            room.settled = True
            room.terminal_ms = owner._workflows.now()
            room.feedback = report
            room.feedback_status = "ready"
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
        room.feedback_status = "generating"
        room.error = None
        room.feedback_generation_id += 1
        owner._schedule_coaching(room.feedback_generation_id)
        room.revision += 1
    await owner._publish()
    return CommandResult(True)

"""Research preparation and approval; the coordinator owns retained tasks."""

import asyncio
from dataclasses import dataclass
import os
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING

from backend.account_store import AccessError, require_run_access
from backend.project_files import ProjectFile
from backend.question_generator import DEFAULT_MODEL
from backend.research_plan import ResearchPlan, generate_research_plan, validate_question_budget
from backend.resource_limits import limit
from backend.rooms.commands import CommandResult, VerifiedActor, PlanCommand, PrepareResearchPlan
from backend.rooms.errors import safe_generation_error

if TYPE_CHECKING:
    from backend.rooms.coordinator import RoomCoordinator


@dataclass(frozen=True)
class PlanWork:
    generation_id: int
    run_id: str | None


@dataclass(frozen=True)
class PlanInput:
    files: tuple[ProjectFile, ...]
    defense_type: str
    research_stage: str


PlanRequest = Callable[[PlanInput], Awaitable[ResearchPlan]]


async def request_plan(request: PlanInput) -> ResearchPlan:
    return await asyncio.to_thread(generate_research_plan, list(request.files), os.getenv("OPENAI_API_KEY"),
        os.getenv("OPENAI_MODEL") or DEFAULT_MODEL,
        defense_type=request.defense_type, research_stage=request.research_stage)


async def run_plan(owner: "RoomCoordinator", work: PlanWork, request: PlanInput) -> None:
    room = owner._room
    try:
        async with room.lock:
            if not owner._plan_current(work):
                return
            room.ai_budget.admit('plan', limit('AI_PLAN_ATTEMPTS', 3, 10), room.owner_account_id or room.code)
        plan = await owner._workflows.plan_request(request)
    except Exception as error:
        async with room.lock:
            if not owner._plan_current(work):
                return
            room.research_planning_status = "failed"
            room.research_plan_error = safe_generation_error(error)
            room.revision += 1
        await owner._workflows.publish(room)
        return
    async with room.lock:
        if not owner._plan_current(work):
            return
        room.research_plan = plan
        room.research_planning_status = "ready"
        room.research_plan_error = None
        room.research_budget_preview = plan.suggested_budget
        room.research_plan_approved = False
        room.revision += 1
    await owner._workflows.publish(room)


async def handle_plan_command(owner: "RoomCoordinator", actor: VerifiedActor, command: PlanCommand) -> CommandResult:
    room = owner._room
    async with room.lock:
        if room.closed:
            return CommandResult(False, "Room not found. Create a fresh room.")
        try:
            player = owner._player(actor)
            if not player.is_host:
                return CommandResult(False, "Only the host can control the defense.")
            if isinstance(command, PrepareResearchPlan):
                require_run_access(actor.account_id)
                if room.defense_type == "code":
                    return CommandResult(False, "Paper mapping is available for research and mixed defenses only.")
                if room.phase != "lobby" or room.defense is not None:
                    return CommandResult(False, "Prepare the research map before starting a defense.")
                if room.research_planning_status == "planning":
                    return CommandResult(False, "The research map is already being prepared.")
                if command.retry and room.research_planning_status != "failed":
                    return CommandResult(False, "There is no failed research map to retry.")
                room.activity_ms = owner._workflows.now()
                room.research_planning_status = "planning"
                room.research_plan_error = None
                room.research_plan = None
                room.research_budget_preview = None
                room.research_plan_approved = False
                room.research_plan_generation_id += 1
                owner._schedule_research_plan(room.research_plan_generation_id)
            else:
                if room.phase != "lobby" or room.research_planning_status != "ready" or room.research_plan is None:
                    return CommandResult(False, "Prepare a research map before confirming its question budget.")
                if command.plan_id != room.research_plan.id:
                    return CommandResult(False, "The research map changed. Review the current map before confirming.")
                room.research_budget_preview = validate_question_budget(command.question_budget)
                room.activity_ms = owner._workflows.now()
                room.research_plan_approved = True
        except (ValueError, AccessError) as error:
            return CommandResult(False, str(error))
        room.revision += 1
    await owner._workflows.publish(room)
    return CommandResult(True)

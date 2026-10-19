"""Research preparation and approval; the coordinator owns retained tasks."""

import asyncio
from dataclasses import dataclass, field, replace
from threading import Event
from concurrent.futures import TimeoutError as FutureTimeoutError
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING

from backend.account_store import AccessError, require_run_access
from backend.project_files import ProjectFile
from backend.practice_tiers import FREE_QUESTION_LIMIT, validate_tier_budget
from backend.question_generator import QuestionGenerationError
from backend.research_plan import ResearchPlan, ResearchPlanProgress, generate_research_plan, validate_question_budget, ResearchProfileDescription, validate_profile_description
from backend.resource_limits import limit
from backend.rooms.commands import CommandResult, VerifiedActor, PlanCommand, PrepareResearchPlan
from backend.rooms.errors import safe_generation_error
from backend.openrouter_mapping import MappingClient, MODEL as MAPPING_MODEL

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
    on_progress: Callable[[ResearchPlanProgress], Awaitable[bool]] | None = field(default=None, compare=False, repr=False)
    profile_correction: ResearchProfileDescription | None = None
    preparation_id: str = ""
    owner_account_id: str = ""
    practice_tier: str = "standard"


PlanRequest = Callable[[PlanInput], Awaitable[ResearchPlan]]


async def request_plan(request: PlanInput) -> ResearchPlan:
    loop = asyncio.get_running_loop()
    stopped = Event()

    def report(progress: ResearchPlanProgress) -> None:
        if stopped.is_set():
            raise QuestionGenerationError("Research mapping was cancelled.")
        future = asyncio.run_coroutine_threadsafe(request.on_progress(progress), loop)
        try:
            while not stopped.is_set():
                try:
                    if not future.result(timeout=.25):
                        raise QuestionGenerationError("Research mapping was cancelled.")
                    return
                except FutureTimeoutError:
                    if future.done():
                        raise
                    continue
            raise QuestionGenerationError("Research mapping was cancelled.")
        finally:
            if not future.done():
                future.cancel()

    try:
        def generate():
            client = MappingClient(request.preparation_id, request.owner_account_id, stopped=stopped.is_set, tier=request.practice_tier)
            return generate_research_plan(list(request.files), client.api_key, MAPPING_MODEL,
                client=client, defense_type=request.defense_type, research_stage=request.research_stage,
                on_progress=report if request.on_progress else None, profile_correction=request.profile_correction)
        return await asyncio.to_thread(generate)
    finally:
        stopped.set()


async def run_plan(owner: "RoomCoordinator", work: PlanWork, request: PlanInput) -> None:
    room = owner._room

    async def progress(update: ResearchPlanProgress) -> bool:
        async with room.lock:
            if not owner._plan_current(work):
                return False
            room.research_plan_progress = update
            room.revision += 1
        await owner._publish()
        return True

    try:
        async with room.lock:
            if not owner._plan_current(work):
                return
            room.ai_budget.admit('plan', limit('AI_PLAN_ATTEMPTS', 3, 10), room.owner_account_id or room.code)
        plan = await owner._workflows.plan_request(replace(request, on_progress=progress))
    except Exception as error:
        async with room.lock:
            if not owner._plan_current(work):
                return
            room.research_planning_status = "failed"
            room.research_plan_progress = None
            room.research_plan_error = safe_generation_error(error)
            room.revision += 1
        await owner._publish()
        return
    async with room.lock:
        if not owner._plan_current(work):
            return
        room.research_plan = plan
        room.research_planning_status = "ready"
        room.research_plan_progress = None
        room.research_plan_error = None
        room.research_budget_preview = min(plan.suggested_budget, FREE_QUESTION_LIMIT) if room.practice_tier == "free" else plan.suggested_budget
        room.research_plan_approved = False
        room.revision += 1
    await owner._publish()


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
                if room.practice_tier != "free":
                    require_run_access(actor.account_id)
                if room.defense_type == "code":
                    return CommandResult(False, "Paper mapping is available for research and mixed defenses only.")
                if room.phase != "lobby" or room.defense is not None:
                    return CommandResult(False, "Prepare the research map before starting a defense.")
                if room.research_planning_status == "planning":
                    return CommandResult(False, "The research map is already being prepared.")
                if command.retry and room.research_planning_status != "failed":
                    return CommandResult(False, "There is no failed research map to retry.")
                correction = room.research_profile_correction
                if command.profile_correction is not None:
                    if command.retry:
                        return CommandResult(False, "Retry uses the saved profile. Prepare a new map to change it.")
                    correction = validate_profile_description(command.profile_correction)
                profile_changed = correction != room.research_profile_correction
                room.research_profile_correction = correction
                room.activity_ms = owner._workflows.now()
                room.research_planning_status = "planning"
                room.research_plan_progress = ResearchPlanProgress("preparing")
                room.research_plan_error = None
                # Retain a previously valid map for reference through failure;
                # status and revoked approval prevent it from starting a run.
                if profile_changed:
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
                profile = room.research_plan.profile
                if profile is None:
                    return CommandResult(False, "Prepare a new research map with a research profile before confirming.")
                if not command.confirm_profile:
                    return CommandResult(False, "Review and explicitly confirm the research profile before starting.")
                if profile.needs_uncertainty_acknowledgment and not command.acknowledge_uncertainty:
                    return CommandResult(False, "Acknowledge the unclear research profile before confirming.")
                room.research_budget_preview = validate_tier_budget(room.practice_tier, validate_question_budget(command.question_budget))
                room.activity_ms = owner._workflows.now()
                room.research_plan_approved = True
        except (ValueError, AccessError) as error:
            return CommandResult(False, str(error))
        room.revision += 1
    await owner._publish()
    return CommandResult(True)

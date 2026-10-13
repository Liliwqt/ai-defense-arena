"""Run lifecycle and invalidation; existing financial transactions stay intact."""

import asyncio
import secrets
from typing import TYPE_CHECKING
from fastapi import HTTPException
from backend.account_store import AccessError, require_run_access, reserve_run, release_run
from backend.financial_policy import live_mode
from backend.live_store import LiveStore
from backend.defense_session import ResearchDefenseSession
from backend.rooms.commands import (CommandResult, VerifiedActor, LifecycleCommand,
    StartDefense, RestartDefense, RetryQuestion, EndDefense, EndUnavailable)
from backend.rooms.publication import DELIVERY_ERRORS

if TYPE_CHECKING:
    from backend.rooms.coordinator import RoomCoordinator


def reserve_room_run(owner: "RoomCoordinator", account_id: str, confirmed: bool, retry: bool = False) -> None:
    room = owner._room
    if not retry:
        if live_mode():
            from backend.account_store import account_access
            access=account_access(account_id)
        else:
            access = require_run_access(account_id)
        if not access["free_access"] and not confirmed:
            raise AccessError("Confirm the 10-credit cost before starting or restarting this run.")
    run_id = room.run_id if retry and room.run_id else secrets.token_hex(24)
    if live_mode():
        from backend.account_store import account_access
        if not account_access(account_id)['free_access']:
            from backend.payments_live import settings
            try:settings()
            except HTTPException:
                raise AccessError('Paid defenses are temporarily unavailable. Your credits are retained.') from None
        LiveStore().reserve_run(account_id,run_id,owner._workflows.service_id,room.code,
                                replace_id=room.run_id if run_id!=room.run_id else None)
    else:
        reserve_run(account_id, run_id)
    if not live_mode() and run_id != room.run_id:
        release_run(room.run_id)
    room.run_id = run_id
    room.settled = False
    room.terminal_ms = None
    if not retry:
        room.ai_budget.reset_run(room.research_budget_preview or 8)
    room.absent_since_ms = None
    room.absence_elapsed_ms = 0


async def handle_lifecycle(owner: "RoomCoordinator", actor: VerifiedActor, command: LifecycleCommand) -> CommandResult:
    room = owner._room
    error = None
    generate_first = None
    generation_id = None
    feedback_generation_id = None
    async with room.lock:
        if room.closed:
            return CommandResult(False, "Room not found. Create a fresh room.")
        player = room.players.get(actor.token)
        if player is None:
            return CommandResult(False, "This room link is no longer valid. Join again.")
        # Authorize before mutation or scheduling any paid AI work.
        try:
            if player.is_host and isinstance(command, StartDefense) and room.phase == "lobby" and room.defense is None:
                # Budget/map validation below must precede a reservation.
                if room.defense_type == "code" or (room.research_plan and room.research_plan_approved
                        and command.plan_id == room.research_plan.id
                        and type(command.question_budget) is int
                        and command.question_budget == room.research_budget_preview):
                    reserve_room_run(owner, actor.account_id, command.confirm_cost)
            if player.is_host and isinstance(command, RestartDefense) and (room.defense_type == "code" or (room.research_plan and room.research_plan_approved)):
                reserve_room_run(owner, actor.account_id, command.confirm_cost)
            if player.is_host and isinstance(command, RetryQuestion) and room.phase == "retry" and (room.defense is None or not room.defense.turns):
                reserve_room_run(owner, actor.account_id, True, retry=True)
        except AccessError as failure:
            return CommandResult(False, str(failure))
        if not player.is_host:
            error = "Only the host can control the defense."
        elif isinstance(command, StartDefense):
            if room.phase != "lobby" or room.defense is not None:
                error = "The defense has already started."
            elif room.research_planning_status == "planning":
                error = "Wait for the research map to finish before starting."
            elif room.defense_type != "code" and (
                    room.research_plan is None or not room.research_plan_approved
                    or command.plan_id != room.research_plan.id
                    or type(command.question_budget) is not int
                    or command.question_budget != room.research_budget_preview):
                error = "Prepare and confirm the current research map and question budget before starting."
            else:
                owner._retire_work()
                if room.defense_type != "code":
                    room.defense = ResearchDefenseSession.create(room.research_plan, room.research_budget_preview,
                                                                 room.defense_type, room.research_stage)
                room.phase = "generating"
                room.error = None
                generation_id = room.generation_id
                room.revision += 1
                generate_first = True
        elif isinstance(command, EndUnavailable):
            if not live_mode() or not room.run_id:
                error = "There is no unavailable live defense to end."
            else:
                try:
                    LiveStore().end_unavailable(actor.account_id,room.run_id)
                except AccessError as failure:
                    error = str(failure)
                else:
                    owner._retire_work()
                    if isinstance(room.defense,ResearchDefenseSession) and not room.defense.completed:
                        room.defense.end()
                    room.phase = "complete"
                    room.settled = True
                    room.terminal_ms = owner._workflows.now()
                    room.feedback_status = "none"
                    room.error = "The unavailable defense was ended. Check Account for any returned credits."
                    room.revision += 1
        elif isinstance(command, EndDefense):
            if room.defense_type == "code" or not isinstance(room.defense, ResearchDefenseSession):
                error = "Ending early is available for an active research defense."
            elif room.defense.completed:
                error = "The defense is already complete."
            else:
                owner._retire_work()
                room.defense.end()
                release_run(room.run_id)
                if live_mode() and room.run_id:
                    LiveStore().finish_run(room.run_id,"ended")
                room.phase = "complete"
                room.error = None
                room.feedback_status = "generating"
                feedback_generation_id = room.feedback_generation_id
                room.revision += 1
        elif isinstance(command, RestartDefense):
            # Cancel an in-flight map without letting it mutate an active defense.
            owner._retire_work()
            if room.research_planning_status == "planning":
                room.research_planning_status = "none"
                room.research_plan_progress = None
                room.research_plan_error = None
            room.defense = None
            room.defense_view_id = secrets.token_hex(12)
            room.answered_by.clear()
            room.answered_by_seat.clear()
            room.chat.clear()
            room.chat_seq = 0
            room.phase = "generating"
            room.error = None
            generation_id = room.generation_id
            room.feedback_status = "none"
            room.feedback = None
            room.revision += 1
            generate_first = True
            if room.defense_type != "code":
                if room.research_plan is not None and room.research_plan_approved:
                    room.defense = ResearchDefenseSession.create(room.research_plan, room.research_budget_preview,
                                                                 room.defense_type, room.research_stage)
                else:
                    room.phase = "lobby"
                    generate_first = None
        elif isinstance(command, RetryQuestion):
            if room.phase != "retry":
                error = "There is no failed question to retry."
            else:
                owner._retire_work()
                generate_first = room.defense is None or not room.defense.turns
                room.phase = "generating"
                room.error = None
                generation_id = room.generation_id
                room.revision += 1
        else:
            error = "Unknown room action."
    if error:
        return CommandResult(False, error)
    await owner._publish()
    if generate_first is not None and generation_id is not None:
        owner._schedule_question(generation_id, generate_first)
    if feedback_generation_id is not None:
        owner._schedule_coaching(feedback_generation_id)

    return CommandResult(True)



async def reclaim_room(owner: "RoomCoordinator", expired_only: bool) -> CommandResult:
    """Called with registry ownership; only eligible rooms lose their uploads."""
    room = owner._room
    async with room.lock:
        expiry = room.expires_at()
        if room.closed or not room.settled or expiry is None:
            return CommandResult(False)
        if expired_only and owner._workflows.now() < expiry:
            return CommandResult(False)
        room.closed = True
        sockets = [socket for player in room.players.values() for socket in player.sockets]
    await owner.shutdown()

    async def close(socket):
        try:
            await asyncio.wait_for(owner._workflows.deliver(socket, {
                "type": "error", "message": "Room not found. This room was closed or expired; create a fresh room."
            }), 1)
        except DELIVERY_ERRORS:
            pass
        try:
            await asyncio.wait_for(owner._workflows.close(socket, 1000), 1)
        except DELIVERY_ERRORS:
            pass
    await asyncio.gather(*(close(socket) for socket in sockets))
    async with room.lock:
        room.files.clear()
        room.chat.clear()
        room.players.clear()
        room.defense = None
    return CommandResult(True)

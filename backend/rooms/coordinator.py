"""Room command boundary; unmigrated workflows stay in the transport entry."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from collections.abc import Awaitable, Callable
from types import MappingProxyType
from typing import Literal, Mapping, get_args

from backend.rooms.model import Room, now_ms
from backend.timed_turn import DeadlineExpired
from fastapi import HTTPException

MAX_CHAT_MESSAGES = 100
MAX_CHAT_CHARS = 500


@dataclass(frozen=True)
class SendChat:
    text: object


@dataclass(frozen=True)
class CastVote:
    seat: object


LegacyAction = Literal[
    "start", "restart", "retry", "retry_coaching", "prepare_research_plan",
    "retry_research_plan", "approve_research_plan", "end_defense", "end_unavailable",
    "retry_interpretation", "use_pending_as_answer", "submit_direct_answer",
    "finish_probe", "submit_probe_reply", "submit_answer",
]


@dataclass(frozen=True)
class LegacyCommand:
    """Temporary bridge for the existing workflows, removed as each migrates."""

    action: LegacyAction
    payload: Mapping[str, object]


Command = CastVote | SendChat | LegacyCommand


def decode_command(message: dict) -> Command:
    action = message.get("type")
    if action == "cast_vote":
        return CastVote(message.get("seat"))
    if action == "send_chat":
        return SendChat(message.get("text"))
    if action in get_args(LegacyAction):
        return LegacyCommand(action, MappingProxyType(dict(message)))
    raise ValueError("Unknown room action.")


@dataclass(frozen=True)
class CommandResult:
    accepted: bool
    error: str | None = None
    reason: str | None = None


@dataclass(frozen=True)
class RoomWorkflows:
    """Real transport/clock adapters; remaining workflows migrate in later tickets."""

    publish: Callable[[Room], Awaitable[None]]
    expire_deadline: Callable[[Room], Awaitable[None]]
    now: Callable[[], int] = now_ms
    legacy_action: Callable[[Room, VerifiedActor, LegacyCommand], Awaitable[CommandResult]] | None = None


@dataclass(frozen=True)
class VerifiedActor:
    """Identity established by server token/session checks for this invocation."""

    token: str
    account_id: str | None = None


class RoomCoordinator:
    def __init__(self, room: Room, workflows: RoomWorkflows | None = None):
        if room.coordinator is not None:
            raise ValueError("This room already has a coordinator.")
        self._room = room
        self._workflows = workflows
        self._shutdown_started = False
        room.coordinator = self

    def _player(self, actor: VerifiedActor):
        player = self._room.players.get(actor.token)
        if player is None:
            raise ValueError("This room link is no longer valid. Join again.")
        if player.is_host and actor.account_id != self._room.owner_account_id:
            raise ValueError("Sign in with the account that created this room to use host controls.")
        return player

    def view(self, actor: VerifiedActor) -> dict:
        """Capture under the caller's room lock; no socket or account data escapes."""
        now = self._workflows.now() if self._workflows else None
        return self._room.snapshot(self._player(actor), now=now)

    async def execute(self, command: Command, actor: VerifiedActor) -> CommandResult:
        if self._workflows is None:
            raise RuntimeError("Room workflows must be configured before executing commands.")
        room = self._room
        # Authentication precedes catching up a deadline, which can schedule AI work.
        async with room.lock:
            if room.closed:
                return CommandResult(False, "Room not found. Create a fresh room.")
            try:
                self._player(actor)
            except ValueError as failure:
                return CommandResult(False, str(failure))
        await self._workflows.expire_deadline(room)
        if isinstance(command, LegacyCommand):
            if self._workflows.legacy_action is None:
                raise RuntimeError("Unmigrated room workflows are not configured.")
            return await self._workflows.legacy_action(room, actor, command)
        expired = False
        result = CommandResult(True)
        async with room.lock:
            if room.closed:
                return CommandResult(False, "Room not found. Create a fresh room.")
            try:
                player = self._player(actor)
            except ValueError as failure:
                return CommandResult(False, str(failure))
            if isinstance(command, CastVote):
                previous_vote = room.votes.get(player.token)
                try:
                    room.cast_vote(player.token, command.seat, room.online_players(), self._workflows.now())
                except HTTPException as failure:
                    result = CommandResult(False, str(failure.detail))
                except ValueError as failure:
                    result = CommandResult(False, str(failure))
                    expired = isinstance(failure, DeadlineExpired)
                else:
                    if previous_vote == room.votes.get(player.token):
                        return result
                    room.revision += 1
            else:
                content = command.text
                if not isinstance(content, str) or not content.strip():
                    return CommandResult(False, "Write a team message before sending.")
                if len(content) > MAX_CHAT_CHARS:
                    return CommandResult(False, f"Keep team messages under {MAX_CHAT_CHARS} characters.")
                room.chat_seq += 1
                room.chat.append({"id": room.chat_seq, "seat": player.seat, "name": player.name,
                                  "text": content.strip(), "sent_at_ms": self._workflows.now()})
                room.chat = room.chat[-MAX_CHAT_MESSAGES:]
                room.revision += 1
        if expired:
            await self._workflows.expire_deadline(room)
        if result.accepted:
            await self._workflows.publish(room)
        return result

    async def shutdown(self) -> None:
        """Fence room work before cancellation; service lifecycle wiring comes later."""
        room = self._room
        async with room.lock:
            if self._shutdown_started:
                return
            self._shutdown_started = True
            room.closed = True
            room.generation_id += 1
            room.research_plan_generation_id += 1
            room.feedback_generation_id += 1
            room.discard_pending()
            room.clear_clock()
            clock_task, room.clock_task = room.clock_task, None
        if clock_task is not None and clock_task is not asyncio.current_task():
            clock_task.cancel()
            await asyncio.wait({clock_task}, timeout=.25)

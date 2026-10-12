"""Room command boundary; unmigrated workflows stay in the transport entry."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from collections.abc import Awaitable, Callable
from types import MappingProxyType
from typing import Literal, Mapping, get_args

from backend.rooms.model import Room, now_ms
from backend.timed_turn import DeadlineExpired
from backend.financial_policy import live_mode
from backend.live_store import LiveStore
from backend.rooms.questions import QuestionRequest, QuestionWork, request_question, run_question
from fastapi import HTTPException

MAX_CHAT_MESSAGES = 100
MAX_CHAT_CHARS = 500


@dataclass(frozen=True)
class SendChat:
    text: object


@dataclass(frozen=True)
class CastVote:
    seat: object


@dataclass(frozen=True)
class GenerateQuestion:
    generation_id: int
    first: bool


@dataclass(frozen=True)
class CatchUpDeadline:
    clock_id: int | None = None
    run_id: str | None = None


@dataclass(frozen=True)
class ClockWork:
    clock_id: int
    deadline_ms: int
    run_id: str | None


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


Command = CastVote | SendChat | LegacyCommand | GenerateQuestion | CatchUpDeadline


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
    now: Callable[[], int] = now_ms
    legacy_action: Callable[[Room, VerifiedActor, LegacyCommand], Awaitable[CommandResult]] | None = None
    question_request: QuestionRequest = request_question
    sleep: Callable[[float], Awaitable[None]] = lambda seconds: asyncio.sleep(seconds)
    coaching: Callable[[Room, int], None] | None = None


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
        self._question_tasks: dict[tuple[str | None, int], asyncio.Task] = {}
        self._tasks: set[asyncio.Task] = set()
        self._clock_work: ClockWork | None = None
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

    async def execute(self, command: Command, actor: VerifiedActor | None = None) -> CommandResult:
        if self._workflows is None:
            raise RuntimeError("Room workflows must be configured before executing commands.")
        room = self._room
        if isinstance(command, GenerateQuestion):
            async with room.lock:
                task = self._schedule_question(command.generation_id, command.first)
            return CommandResult(task is not None)
        if isinstance(command, CatchUpDeadline):
            await self._expire_deadline(command.clock_id, command.run_id)
            return CommandResult(True)
        # Authentication precedes catching up a deadline, which can schedule AI work.
        async with room.lock:
            if room.closed:
                return CommandResult(False, "Room not found. Create a fresh room.")
            try:
                if actor is None:
                    return CommandResult(False, "This room link is no longer valid. Join again.")
                self._player(actor)
            except ValueError as failure:
                return CommandResult(False, str(failure))
        await self._expire_deadline()
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
            await self._expire_deadline()
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
            self._cancel_clock()
            tasks = {task for task in self._tasks if task is not asyncio.current_task()}
            for task in tasks:
                task.cancel()
        if tasks:
            await asyncio.wait(tasks, timeout=.25)

    def _retain(self, task: asyncio.Task) -> asyncio.Task:
        self._tasks.add(task)
        def finished(done):
            self._tasks.discard(done)
            if not done.cancelled():
                done.exception()
        task.add_done_callback(finished)
        return task

    def _question_current(self, work: QuestionWork) -> bool:
        room = self._room
        return not room.closed and room.run_id == work.run_id and room.generation_id == work.generation_id and room.phase == "generating"

    def _schedule_question(self, generation_id: int, first: bool) -> asyncio.Task | None:
        work = QuestionWork(generation_id, first, self._room.run_id)
        if not self._question_current(work):
            return None
        key = (work.run_id, work.generation_id)
        if key in self._question_tasks:
            return self._question_tasks[key]
        task = self._retain(asyncio.create_task(run_question(self, work)))
        self._question_tasks[key] = task
        def finished(done):
            if self._question_tasks.get(key) is done:
                self._question_tasks.pop(key)
        task.add_done_callback(finished)
        return task

    def _cancel_clock(self) -> None:
        room = self._room
        if room.clock_task and room.clock_task is not asyncio.current_task():
            room.clock_task.cancel()
        room.clock_task = None
        self._clock_work = None

    def _schedule_clock(self, clock_id: int, deadline_ms: int) -> None:
        room = self._room
        if room.closed or room.clock_id != clock_id or room.active_deadline_ms != deadline_ms:
            return
        work = ClockWork(clock_id, deadline_ms, room.run_id)
        if self._clock_work == work and room.clock_task and not room.clock_task.done():
            return
        self._cancel_clock()
        self._clock_work = work
        async def wait_then_advance():
            try:
                await self._workflows.sleep(max(0, (deadline_ms - self._workflows.now()) / 1000))
                await self._expire_deadline(clock_id, work.run_id)
            except asyncio.CancelledError:
                pass
        room.clock_task = self._retain(asyncio.create_task(wait_then_advance()))

    def _resolve_turn_locked(self) -> tuple[int | None, int | None]:
        room = self._room
        self._cancel_clock()
        assert room.defense is not None
        if room.phase == "complete":
            if live_mode() and room.run_id:
                LiveStore().service_state(room.run_id, "coaching")
            room.feedback_status = "generating"
            room.feedback_generation_id += 1
            return None, room.feedback_generation_id
        room.generation_id += 1
        return room.generation_id, None

    def _schedule_coaching(self, version: int) -> None:
        if self._workflows.coaching is not None:
            self._workflows.coaching(self._room, version)

    async def _expire_deadline(self, expected_id: int | None = None, expected_run: str | None = None) -> None:
        room = self._room
        next_clock = generation_id = feedback_id = None
        async with room.lock:
            if room.closed or (expected_id is not None and room.run_id != expected_run):
                return
            outcome = room.expire(self._workflows.now(), room.online_players(), room.defense, expected_id)
            if outcome == "reaction_finished":
                next_clock = (room.clock_id, room.vote_deadline_ms)
            elif outcome in {"voting_closed", "pause_ended"}:
                next_clock = (room.clock_id, room.answer_deadline_ms)
            elif outcome in {"timed_out", "probe_expired"}:
                generation_id, feedback_id = self._resolve_turn_locked()
            if not outcome:
                return
            room.revision += 1
        await self._workflows.publish(room)
        if next_clock:
            self._schedule_clock(*next_clock)
        if generation_id is not None:
            self._schedule_question(generation_id, False)
        if feedback_id is not None:
            self._schedule_coaching(feedback_id)

"""Single-process multiplayer room server for AI Defense Arena."""

import asyncio
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
import json
import logging
import os
from pathlib import Path
import secrets
import time
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from openai import OpenAIError
from pydantic import BaseModel, ValidationError

from defense_session import DefenseSession, ResearchDefenseSession, MAX_ANSWER_CHARS, PANELIST_ORDER
from defense_progression import prepare_progression, commit_progression
from accounts import configure_auth, require_account, check_csrf, auth_settings
from account_store import (AccessError, require_run_access, reserve_run, charge_run,
                           release_run, release_orphaned_reservations)
from financial_policy import live_mode
from live_store import LiveStore, ServiceAlreadyActive
from resource_limits import limit, creation_rate, ai_rate, AIBudget
from timed_turn import TimedTurn, PendingSubmission, DeadlineExpired, VOTE_MS, ANSWER_MS
from payments import router as test_payment_router
from payments_live import router as live_payment_router
from project_files import MAX_ARCHIVE_BYTES, MAX_FILE_BYTES, ProjectFile, read_project_files
from research_files import MAX_RESEARCH_BYTES, read_research_files, combine_sources
from research_plan import ResearchPlan, generate_research_plan, validate_question_budget
from question_generator import (
    DEFAULT_MODEL,
    CoachingReport,
    interpret_submission,
    QuestionGenerationError,
    describe_openai_error,
    generate_coaching_report,
    generate_first_question,
    generate_next_move,
    generate_research_move,
)


SERVICE_ID = secrets.token_hex(24)
SERVICE_POLL_SECONDS = 2
SERVICE_HEARTBEAT_SECONDS = 10
SERVICE_STARTING_MESSAGE = "The room service is restarting. Please retry shortly."
MAX_PLAYERS = 4
MAX_CHAT_MESSAGES = 100
MAX_CHAT_CHARS = 500
MAX_ROOMS = 20
MAX_REQUEST_BYTES = 110_000_000
ROOM_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
GAME_DIR = Path(__file__).resolve().parent / "game" / "dist"


@dataclass(frozen=True)
class UploadedBytes:
    name: str
    data: bytes

    def getvalue(self) -> bytes:
        return self.data


@dataclass
class Player:
    token: str
    name: str
    seat: int
    is_host: bool = False
    sockets: set[WebSocket] = field(default_factory=set)


@dataclass
class Room(TimedTurn):
    code: str
    files: list[ProjectFile]
    players: dict[str, Player]
    defense_type: str = "code"
    research_stage: str = "infer"
    defense: DefenseSession | None = None
    revision: int = 0
    generation_id: int = 0
    feedback_status: str = "none"   # none | generating | ready | failed
    feedback: CoachingReport | None = None
    research_planning_status: str = "none"  # none | planning | ready | failed
    research_plan: ResearchPlan | None = None
    research_plan_error: str | None = None
    research_budget_preview: int | None = None
    research_plan_approved: bool = False
    research_plan_generation_id: int = 0
    feedback_generation_id: int = 0
    chat: list[dict[str, Any]] = field(default_factory=list)
    chat_seq: int = 0
    clock_task: asyncio.Task | None = field(default=None, repr=False)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    broadcast_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    owner_account_id: str | None = None
    run_id: str | None = None
    absent_since_ms: int | None = None
    absence_elapsed_ms: int = 0

    created_ms: int = field(default_factory=lambda: _now_ms())
    activity_ms: int = field(default_factory=lambda: _now_ms())
    terminal_ms: int | None = None
    settled: bool = True
    closed: bool = False
    ai_budget: AIBudget = field(default_factory=AIBudget)

    def expires_at(self):
        if self.closed or not self.settled or self.phase not in {'lobby', 'retry', 'complete'} or self.research_planning_status == 'planning' or self.feedback_status in {'generating', 'failed'}:
            return None
        if self.phase == 'complete':
            return (self.terminal_ms or self.activity_ms) + limit('ROOM_RETENTION_SECONDS', 1800, 86400) * 1000
        if self.defense and self.defense.turns:
            return None
        return self.activity_ms + limit('ROOM_IDLE_SECONDS', 1800, 86400) * 1000

    def snapshot(self, recipient: Player | None = None) -> dict[str, Any]:
        turns = []
        if self.defense:
            for index, turn in enumerate(self.defense.turns):
                turns.append(
                    {
                        "panelist": turn.panelist,
                        "lead_in": turn.question.lead_in,
                        "question": turn.question.question,
                        "filename": turn.question.filename,
                        "evidence_line": turn.question.evidence_line,
                        "evidence_text": turn.question.evidence_text,
                        "evidence_location": turn.question.evidence_location or f"Line {turn.question.evidence_line}",
                        "evidence_kind": turn.question.evidence_kind,
                        "evidence_before": turn.question.evidence_before,
                        "evidence_after": turn.question.evidence_after,
                        "clarifications": [exchange.__dict__ for exchange in turn.clarifications],
                        "answer": turn.answer,
                        "timed_out": turn.timed_out,
                        "ended_early": turn.ended_early,
                        "topic_id": turn.topic_id,
                        "is_follow_up": turn.is_follow_up,
                        "assigned_seat": turn.assigned_seat,
                        "answered_by": self.answered_by.get(index),
                        "answered_by_seat": self.answered_by_seat.get(index),
                    }
                )
        if self.defense and self.defense.awaiting_answer:
            active_panelist = self.defense.turns[-1].panelist
        elif self.defense and self.defense.needs_question:
            active_panelist = self.defense.pending_panelist
        elif self.phase == "generating":
            active_panelist = "Methodology Reviewer" if self.defense_type != "code" else PANELIST_ORDER[0]
        else:
            active_panelist = None
        feedback_dict = None
        if self.feedback is not None:
            feedback_dict = {
                "summary": self.feedback.summary,
                "strengths": self.feedback.strengths,
                "improvements": self.feedback.improvements,
                "next_step": self.feedback.next_step,
            }
        return {
            "room_code": self.code,
            "expires_at_ms": self.expires_at(),
            "interpretation_attempts_left": max(0, limit('AI_INTERPRETATION_ATTEMPTS', 6, 20) - self.interpretation_attempts),
            "clock_paused": self.pause_deadline_ms is not None and _now_ms() < self.pause_deadline_ms,
            "pause_deadline_ms": self.pause_deadline_ms,
            "question_attempts_left": self.ai_budget.remaining(f'question:{len(self.defense.turns) if self.defense else 0}', limit('AI_QUESTION_ATTEMPTS', 3, 10)),
            "coaching_attempts_left": self.ai_budget.remaining('coaching', limit('AI_COACHING_ATTEMPTS', 3, 10)),
            "plan_attempts_left": self.ai_budget.remaining('plan', limit('AI_PLAN_ATTEMPTS', 3, 10)),
            "self_seat": recipient.seat if recipient is not None else None,
            "self_is_host": recipient.is_host if recipient is not None else False,
            "phase": self.phase,
            "players": [
                {
                    "seat": player.seat,
                    "name": player.name,
                    "online": bool(player.sockets),
                    "is_host": player.is_host,
                }
                for player in sorted(self.players.values(), key=lambda player: player.seat)
            ],
            "turns": turns,
            "active_panelist": active_panelist,
            "error": self.error,
            "revision": self.revision,
            "files": [file.name for file in self.files],
            "accepted_files": [{"name": file.name, "kind": file.kind, "detail": file.detail} for file in self.files],
            "defense_type": self.defense_type,
            "research_stage": self.research_stage,
            "research_planning_status": self.research_planning_status,
            "research_plan": self.research_plan.snapshot() if self.research_plan else None,
            "research_plan_error": self.research_plan_error,
            "research_budget_preview": self.research_budget_preview,
            "research_plan_approved": self.research_plan_approved,
            "question_budget": self.defense.question_budget if isinstance(self.defense, ResearchDefenseSession) else None,
            "coverage": self.defense.coverage if isinstance(self.defense, ResearchDefenseSession) else {},
            "current_topic": self.defense.turns[-1].topic_id if isinstance(self.defense, ResearchDefenseSession) and self.defense.turns else None,
            "completion_reason": self.defense.completion_reason if isinstance(self.defense, ResearchDefenseSession) else None,
            "feedback_status": self.feedback_status,
            "feedback": feedback_dict,
            "server_now_ms": _now_ms(),
            "vote_deadline_ms": self.vote_deadline_ms,
            "answer_deadline_ms": self.answer_deadline_ms,
            "remaining_answer_ms": self.pending_submission.remaining_ms if self.pending_submission else None,
            "my_pending_submission": (
                self.pending_submission.text if recipient is not None and self.pending_submission
                and recipient.token == self.pending_submission.token else None
            ),
            "selected_seat": self.selected_seat,
            "vote_counts": {
                str(seat): sum(1 for token, choice in self.votes.items()
                               if choice == seat and bool(self.players[token].sockets))
                for seat in sorted({player.seat for player in self.players.values() if player.sockets})
            },
            "my_vote": self.votes.get(recipient.token) if recipient is not None else None,
            "chat": list(self.chat),
        }


def _now_ms() -> int:
    return int(time.time() * 1000)


rooms: dict[str, Room] = {}
registry_lock = asyncio.Lock()
creation_pending = {}
parser_pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix='room-parser')
parser_slots = asyncio.Semaphore(2)

async def _remove_room(room, expired_only=False):
    # Registry then room is the only nested lock order used for reclamation.
    async with registry_lock:
        async with room.lock:
            if rooms.get(room.code) is not room or not room.settled or room.expires_at() is None:
                return False
            if expired_only and _now_ms() < room.expires_at():
                return False
            room.closed = True
            room.generation_id += 1
            room.feedback_generation_id += 1
            room.research_plan_generation_id += 1
            room.discard_pending()
            _clear_clock_locked(room)
            del rooms[room.code]
            sockets = [socket for player in room.players.values() for socket in player.sockets]
    for socket in sockets:
        await _send_error(socket, 'Room not found. This room was closed or expired; create a fresh room.')
        try:
            await socket.close(code=1000)
        except (RuntimeError, OSError, WebSocketDisconnect):
            pass
    room.files.clear()
    room.chat.clear()
    room.players.clear()
    room.defense = None
    return True

async def _cleanup_rooms():
    for room in list(rooms.values()):
        async with room.lock:
            expiry = room.expires_at()
            due = expiry is not None and _now_ms() >= expiry
        if due:
            await _remove_room(room, expired_only=True)

async def _room_maintenance():
    while True:
        if not live_mode():
            for room in list(rooms.values()):
                await _observe_absence(room)
        await _cleanup_rooms()
        await asyncio.sleep(5)

async def _observe_absence(room):
    if not room.run_id:
        return
    changed=False
    async with room.lock:
        if room.phase == "complete" and room.feedback_status not in {"generating","failed"}:
            return
        if any(player.sockets for player in room.players.values()):
            room.absent_since_ms=None
            room.absence_elapsed_ms=0
            return
        now=_now_ms()
        if room.absent_since_ms is None:
            room.absent_since_ms=now
        else:
            elapsed=now-room.absent_since_ms
            # Unobserved process stalls/suspension are not defender abandonment.
            if 0<=elapsed<=30_000:
                room.absence_elapsed_ms+=elapsed
            room.absent_since_ms=now
        if room.absence_elapsed_ms>=600_000:
            if live_mode():
                LiveStore().finish_run(room.run_id,"abandoned")
            else:
                release_run(room.run_id)
            room.generation_id+=1
            room.feedback_generation_id+=1
            room.discard_pending()
            _clear_clock_locked(room)
            if isinstance(room.defense,ResearchDefenseSession) and not room.defense.completed:
                room.defense.end()
            room.phase="complete"
            room.settled=True
            room.terminal_ms=now
            room.feedback_status="none"
            room.error="This defense was abandoned after everyone disconnected for ten minutes."
            room.revision+=1
            changed=True
    if changed:
        await publish(room)


@asynccontextmanager
async def lifespan(app):
    global SERVICE_ID, parser_slots
    parser_slots = asyncio.Semaphore(2)
    for name, default, maximum in [('ROOM_HOST_LIMIT',2,20), ('ROOM_CREATE_PER_MINUTE',3,10000),
            ('ROOM_PROCESS_SECONDS',120,600), ('ROOM_IDLE_SECONDS',1800,86400), ('ROOM_RETENTION_SECONDS',1800,86400),
            ('MOBILE_START_PER_MINUTE',60,10000), ('MOBILE_NEW_PER_MINUTE',12,10000), ('MOBILE_PENDING_PER_NETWORK',16,128),
            ('AI_INTERPRETATION_ATTEMPTS',6,20), ('AI_OWNER_PER_MINUTE',12,10000), ('AI_QUESTION_ATTEMPTS',3,10),
            ('AI_COACHING_ATTEMPTS',3,10), ('AI_PLAN_ATTEMPTS',3,10), ('AI_PAUSE_SECONDS',240,600)]:
        limit(name, default, maximum)
    from ipaddress import ip_network
    for network in os.getenv('TRUSTED_PROXY_NETWORKS','').split(','):
        if network.strip():
            ip_network(network.strip())
    creation_pending.clear()
    creation_rate.__init__()
    ai_rate.__init__()
    if not live_mode():
        app.state.room_service_status = "ready"
        release_orphaned_reservations()
        maintenance = asyncio.create_task(_room_maintenance())
        try:
            yield
        finally:
            maintenance.cancel()
            await asyncio.gather(maintenance, return_exceptions=True)
        return
    SERVICE_ID=secrets.token_hex(24)
    service=SERVICE_ID
    app.state.room_service_status = "starting"
    owns_lease = False
    try:
        LiveStore().start_service(service)
    except ServiceAlreadyActive:
        if os.environ.get("RENDER") != "true":
            raise
        # Render waits for this instance's health before stopping its predecessor.
        # Bind HTTP now, but do not run rooms or recovery until the lease is free.
        logging.getLogger(__name__).info("Waiting for previous room service to stop.")
    else:
        owns_lease = True
        app.state.room_service_status = "ready"

    async def maintain():
        nonlocal owns_lease
        try:
            while True:
                if not owns_lease:
                    try:
                        LiveStore().start_service(service)
                    except ServiceAlreadyActive:
                        await asyncio.sleep(SERVICE_POLL_SECONDS)
                        continue
                    owns_lease = True
                    app.state.room_service_status = "ready"
                    logging.getLogger(__name__).info("Room service lease acquired.")
                LiveStore().heartbeat(service)
                for room in list(rooms.values()):
                    await _observe_absence(room)
                await asyncio.sleep(SERVICE_HEARTBEAT_SECONDS)
        except Exception:
            # Never reacquire after losing ownership or advertise a dead heartbeat.
            app.state.room_service_status = "failed"
            logging.getLogger(__name__).error("Room service maintenance failed; room access paused.")

    async def recover():
        from payments_live import recover_payments
        while True:
            if app.state.room_service_status == "ready":
                await recover_payments()
            await asyncio.sleep(SERVICE_POLL_SECONDS if not owns_lease else SERVICE_HEARTBEAT_SECONDS)
    # Provider latency cannot starve the service heartbeat or abandonment observations.
    tasks=[asyncio.create_task(maintain()),asyncio.create_task(recover()),asyncio.create_task(_room_maintenance())]
    try:
        yield
    finally:
        for task in tasks:task.cancel()
        await asyncio.gather(*tasks,return_exceptions=True)
        app.state.room_service_status = "stopped"
        if owns_lease:
            LiveStore().stop_service(service)


app = FastAPI(title="AI Defense Arena", lifespan=lifespan)
app.state.room_service_status = "ready"
configure_auth(app)


@app.middleware("http")
async def reject_large_uploads(request, call_next):
    if (live_mode() and app.state.room_service_status != "ready"
            and (request.url.path == "/api/rooms" or request.url.path.startswith("/api/rooms/"))):
        return JSONResponse({"detail": SERVICE_STARTING_MESSAGE}, status_code=503,
                            headers={"Retry-After": str(SERVICE_POLL_SECONDS)})
    if request.url.path == "/api/rooms":
        length = request.headers.get("content-length")
        if length and length.isdigit() and int(length) > MAX_REQUEST_BYTES:
            return JSONResponse({"detail": "Upload request is too large."}, status_code=413)
    return await call_next(request)


class RoomAdmissionMiddleware:
    """Own the downstream ASGI task so timeout cancels parsing and its waiters."""
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http' or scope['path'] != '/api/rooms' or scope['method'] != 'POST':
            await self.app(scope, receive, send)
            return
        request = Request(scope)
        admission = None
        response_started = False
        try:
            account = require_account(request)
            check_csrf(request, account)
            await _cleanup_rooms()
            async with registry_lock:
                owner = account['id']
                retained = sum(room.owner_account_id == owner for room in rooms.values())
                pending = sum(value == owner for value in creation_pending.values())
                if retained + pending >= limit('ROOM_HOST_LIMIT', 2, 20):
                    raise HTTPException(429, 'Your room allowance is full. Close an unused room in Controls.', headers={'Retry-After': '60'})
                if len(rooms) + len(creation_pending) >= MAX_ROOMS:
                    raise HTTPException(503, 'Room capacity reached. Try again later.')
                creation_rate.admit(owner, limit('ROOM_CREATE_PER_MINUTE', 3))
                admission = secrets.token_hex(16)
                creation_pending[admission] = owner
                request.state.room_admission = admission
                request.state.room_deadline = asyncio.get_running_loop().time() + limit('ROOM_PROCESS_SECONDS', 120, 600)
            received = 0

            async def bounded_receive():
                nonlocal received
                message = await receive()
                received += len(message.get('body', b''))
                if received > MAX_REQUEST_BYTES:
                    raise HTTPException(413, 'Upload request is too large.')
                return message

            async def tracked_send(message):
                nonlocal response_started
                if message['type'] == 'http.response.start':
                    response_started = True
                await send(message)

            await asyncio.wait_for(self.app(scope, bounded_receive, tracked_send), limit('ROOM_PROCESS_SECONDS', 120, 600))
        except asyncio.TimeoutError:
            if not response_started:
                await JSONResponse({'detail': 'Room processing took too long. Retry shortly.'}, status_code=408)(scope, receive, send)
        except HTTPException as error:
            if response_started:
                raise
            await JSONResponse({'detail': error.detail}, status_code=error.status_code, headers=error.headers)(scope, receive, send)
        finally:
            if admission is not None:
                async with registry_lock:
                    creation_pending.pop(admission, None)


app.add_middleware(RoomAdmissionMiddleware)


def _player_name(value: str) -> str:
    name = value.strip()
    if not name or len(name) > 24:
        raise HTTPException(422, "Choose a name of 1 to 24 characters.")
    return name


def _room_code() -> str:
    return "".join(secrets.choice(ROOM_ALPHABET) for _ in range(10))


def _new_token() -> str:
    return secrets.token_urlsafe(32)


def _safe_generation_error(error: Exception) -> str:
    if isinstance(error, HTTPException):
        return str(error.detail)
    if isinstance(error, QuestionGenerationError):
        return str(error)
    if isinstance(error, OpenAIError):
        return describe_openai_error(error, os.getenv("OPENAI_MODEL") or DEFAULT_MODEL, os.getenv("OPENAI_API_KEY"))
    if isinstance(error, ValidationError):
        return "The AI returned an unexpected response. Please try again."
    return "The AI request failed. Please try again."


async def publish(room: Room) -> None:
    """Send the latest state to every connected player in message order."""
    async with room.broadcast_lock:
        async with room.lock:
            deliveries = [
                (socket, {"type": "snapshot", "state": room.snapshot(player)})
                for player in room.players.values()
                for socket in player.sockets
            ]
        for socket, payload in deliveries:
            try:
                await socket.send_json(payload)
            except (RuntimeError, OSError, WebSocketDisconnect):
                async with room.lock:
                    for player in room.players.values():
                        player.sockets.discard(socket)


def _online_players(room: Room) -> dict[str, int]:
    return {player.token: player.seat for player in room.players.values() if player.sockets}


def _set_selected_locked(room: Room, seat: int | None) -> None:
    room.set_selected(seat, room.defense)


def _reassign_if_offline_locked(room: Room) -> bool:
    changed = room.reassign(_online_players(room), room.defense)
    if changed:
        room.revision += 1
    return changed


def _clear_clock_locked(room: Room) -> None:
    room.clear_clock()
    _cancel_clock_task(room)


def _cancel_clock_task(room: Room) -> None:
    if room.clock_task and room.clock_task is not asyncio.current_task():
        room.clock_task.cancel()
    room.clock_task = None


def _resolve_turn_locked(room: Room) -> tuple[int | None, int | None]:
    """Finish a resolved turn and return the next question/coaching generation id."""
    _cancel_clock_task(room)
    assert room.defense is not None
    if room.phase == "complete":
        if live_mode() and room.run_id:
            LiveStore().service_state(room.run_id,"coaching")
        room.feedback_status = "generating"
        room.feedback_generation_id += 1
        return None, room.feedback_generation_id
    room.generation_id += 1
    return room.generation_id, None


def _schedule_clock(room: Room, clock_id: int, deadline_ms: int) -> None:
    _cancel_clock_task(room)
    async def wait_then_advance() -> None:
        try:
            await asyncio.sleep(max(0, (deadline_ms - _now_ms()) / 1000))
            await _expire_deadline(room, clock_id)
        except asyncio.CancelledError:
            pass
    room.clock_task = asyncio.create_task(wait_then_advance())


async def _expire_deadline(room: Room, expected_id: int | None = None) -> None:
    """Apply a deadline under the room lock; action handlers also call this before validation."""
    changed = False
    next_clock = None
    generation_id = None
    feedback_id = None
    async with room.lock:
        outcome = room.expire(_now_ms(), _online_players(room), room.defense, expected_id)
        if outcome == "voting_closed":
            room.revision += 1
            changed = True
            next_clock = (room.clock_id, room.answer_deadline_ms)
        elif outcome == "pause_ended":
            next_clock = (room.clock_id, room.answer_deadline_ms)
            room.revision += 1
            changed = True
        elif outcome == "timed_out":
            generation_id, feedback_id = _resolve_turn_locked(room)
            room.revision += 1
            changed = True
    if not changed:
        return
    await publish(room)
    if next_clock:
        _schedule_clock(room, *next_clock)
    if generation_id is not None:
        _schedule_generation(room, generation_id, False)
    if feedback_id is not None:
        _schedule_coaching(room, feedback_id)


async def _generate_question(room: Room, generation_id: int, first: bool) -> None:
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL") or DEFAULT_MODEL
    next_clock = None
    feedback_id = None
    try:
        async with room.lock:
            if room.closed or room.generation_id != generation_id:
                return
            room.ai_budget.admit(f'question:{len(room.defense.turns) if room.defense else 0}', limit('AI_QUESTION_ATTEMPTS', 3, 10), room.owner_account_id or room.code)
            request = prepare_progression(room.defense, defense_type=room.defense_type,
                                          research_stage=room.research_stage)
        result = await asyncio.to_thread(request.generate, room.files, api_key, model,
            first_question=generate_first_question, next_move=generate_next_move,
            research_move=generate_research_move)
        async with room.lock:
            if room.generation_id != generation_id:
                return
            session = request.apply(result)
            opening=room.defense is None or not room.defense.turns
            if room.run_id and opening and session.turns:
                charge_run(room.owner_account_id, room.run_id)
            elif live_mode() and room.run_id:
                LiveStore().service_state(room.run_id,"coaching" if session.completed else "active")
            room.defense = commit_progression(room.defense, session)
            if room.defense.completed:
                room.phase = "complete"
                room.feedback_status = "generating"
                room.feedback_generation_id += 1
                feedback_id = room.feedback_generation_id
            else:
                room.begin_vote(_now_ms())
                next_clock = (room.clock_id, room.vote_deadline_ms)
            room.error = None
            room.revision += 1
    except Exception as error:
        async with room.lock:
            if room.generation_id != generation_id:
                return
            room.phase = "retry"
            room.error = _safe_generation_error(error)
            try:
                if room.defense is None or not room.defense.turns:
                    release_run(room.run_id)
                    room.settled = True
                elif live_mode() and room.run_id and not isinstance(error, HTTPException):
                    LiveStore().service_state(room.run_id,"unavailable","question")
            except Exception:
                room.error="The defense state could not be saved. Your answers are retained; retry when the service recovers."
            room.revision += 1
        await publish(room)
        return
    await publish(room)
    if next_clock:
        _schedule_clock(room, *next_clock)
    if feedback_id is not None:
        _schedule_coaching(room, feedback_id)


async def _interpret_pending(room: Room, interpretation_id: int) -> None:
    async with room.lock:
        pending = room.pending_submission
        if room.interpretation_id != interpretation_id or pending is None or room.defense is None:
            return
        turn = room.defense.turns[pending.turn]
        question = turn.question
        panelist = turn.panelist
        clarifications = tuple(turn.clarifications)
        history = room.defense.answered_history()
    try:
        decision = await asyncio.to_thread(
            interpret_submission, room.files, os.getenv("OPENAI_API_KEY"),
            panelist=panelist, question=question, submission=pending.text,
            clarifications=clarifications, history=history, model=os.getenv("OPENAI_MODEL") or DEFAULT_MODEL,
            defense_type=room.defense_type, research_stage=room.research_stage,
        )
    except Exception as error:
        async with room.lock:
            if not room.interpretation_failed(interpretation_id, pending, _safe_generation_error(error)):
                return
            room.revision += 1
        await publish(room)
        return
    next_clock = None
    generation_id = None
    feedback_id = None
    await _expire_deadline(room)
    async with room.lock:
        if room.defense is None:
            return
        outcome = room.interpret(room.defense, decision, interpretation_id, pending, _online_players(room), _now_ms())
        if outcome is None:
            return
        if outcome == "clarified":
            next_clock = (room.clock_id, room.answer_deadline_ms)
        elif outcome == "answered":
            generation_id, feedback_id = _resolve_turn_locked(room)
        room.revision += 1
    await publish(room)
    if next_clock:
        _schedule_clock(room, *next_clock)
    if generation_id is not None:
        _schedule_generation(room, generation_id, False)
    if feedback_id is not None:
        _schedule_coaching(room, feedback_id)


def _schedule_interpretation(room: Room, interpretation_id: int) -> None:
    task = asyncio.create_task(_interpret_pending(room, interpretation_id))
    task.add_done_callback(lambda finished: finished.exception() if not finished.cancelled() else None)


def _schedule_generation(room: Room, generation_id: int, first: bool) -> None:
    task = asyncio.create_task(_generate_question(room, generation_id, first))
    task.add_done_callback(lambda finished: finished.exception() if not finished.cancelled() else None)


async def _prepare_research_plan(room: Room, plan_generation_id: int) -> None:
    async with room.lock:
        if room.closed or room.research_plan_generation_id != plan_generation_id or room.phase != "lobby":
            return
        files, mode, stage = list(room.files), room.defense_type, room.research_stage
    try:
        async with room.lock:
            room.ai_budget.admit('plan', limit('AI_PLAN_ATTEMPTS', 3, 10), room.owner_account_id or room.code)
        plan = await asyncio.to_thread(generate_research_plan, files, os.getenv("OPENAI_API_KEY"),
                                       os.getenv("OPENAI_MODEL") or DEFAULT_MODEL,
                                       defense_type=mode, research_stage=stage)
    except Exception as error:
        async with room.lock:
            if room.research_plan_generation_id != plan_generation_id or room.phase != "lobby":
                return
            room.research_planning_status = "failed"
            room.research_plan_error = _safe_generation_error(error)
            room.revision += 1
        await publish(room)
        return
    async with room.lock:
        if room.research_plan_generation_id != plan_generation_id or room.phase != "lobby":
            return
        room.research_plan = plan
        room.research_planning_status = "ready"
        room.research_plan_error = None
        room.research_budget_preview = plan.suggested_budget
        room.research_plan_approved = False
        room.revision += 1
    await publish(room)


def _schedule_research_plan(room: Room, plan_generation_id: int) -> None:
    task = asyncio.create_task(_prepare_research_plan(room, plan_generation_id))
    task.add_done_callback(lambda finished: finished.exception() if not finished.cancelled() else None)


async def _generate_coaching(room: Room, feedback_generation_id: int) -> None:
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL") or DEFAULT_MODEL
    async with room.lock:
        if room.feedback_generation_id != feedback_generation_id or room.defense is None:
            return
        history = room.defense.answered_history()
        research_context = room.defense.context() if isinstance(room.defense, ResearchDefenseSession) else None
    try:
        if not history:
            report = CoachingReport("The host ended the defense before any answer or timeout was recorded. No discussion coverage was confirmed.", [], [], "Review the paper map and start a new defense when the team is ready.")
        else:
            async with room.lock:
                if room.closed or room.feedback_generation_id != feedback_generation_id:
                    return
                room.ai_budget.admit('coaching', limit('AI_COACHING_ATTEMPTS', 3, 10), room.owner_account_id or room.code)
            report = await asyncio.to_thread(
                generate_coaching_report, room.files, history, api_key, model,
                defense_type=room.defense_type, research_stage=room.research_stage,
                **({"research_context": research_context} if research_context else {}),
            )
        async with room.lock:
            if room.feedback_generation_id != feedback_generation_id:
                return
            if live_mode() and room.run_id:
                LiveStore().finish_run(room.run_id,"completed")
            room.settled = True
            room.terminal_ms = _now_ms()
            room.feedback = report
            room.feedback_status = "ready"
            room.error = None
            room.revision += 1
    except Exception as error:
        async with room.lock:
            if room.feedback_generation_id != feedback_generation_id:
                return
            room.feedback_status = "failed"
            room.error = _safe_generation_error(error)
            if live_mode() and room.run_id and not isinstance(error, HTTPException):
                try:LiveStore().service_state(room.run_id,"unavailable","coaching")
                except Exception:
                    room.error="The coaching state could not be saved. Your answers are retained; retry when the service recovers."
            room.revision += 1
        await publish(room)
        return

    await publish(room)


def _schedule_coaching(room: Room, feedback_generation_id: int) -> None:
    task = asyncio.create_task(_generate_coaching(room, feedback_generation_id))
    task.add_done_callback(lambda finished: finished.exception() if not finished.cancelled() else None)


@app.get("/health")
async def health() -> dict[str, str]:
    if live_mode() and app.state.room_service_status != "ready":
        status = app.state.room_service_status
        return JSONResponse({"status": "ok" if status == "starting" else "unavailable",
                             "room_service": status}, status_code=200 if status == "starting" else 503)
    return {"status": "ok"}


@app.post("/api/rooms", status_code=201)
async def create_room(
    request: Request,
    host_name: str = Form(...),
    files: list[UploadFile] | None = File(None),
    research_files: list[UploadFile] | None = File(None),
    defense_type: str = Form("code"),
    research_stage: str = Form("infer"),
) -> dict[str, str]:
    account = require_account(request)
    check_csrf(request, account)
    name = _player_name(host_name)
    if defense_type not in {"code", "research", "mixed"} or research_stage not in {"infer", "proposal", "completed"}:
        raise HTTPException(422, "Choose a valid defense type and research stage.")
    source_uploads = files or []
    paper_uploads = research_files or []
    if defense_type == "code" and (not source_uploads or paper_uploads):
        raise HTTPException(422, "Code defense requires project source files only.")
    if defense_type == "research" and (not paper_uploads or source_uploads):
        raise HTTPException(422, "Research defense requires research documents only.")
    if defense_type == "mixed" and (not source_uploads or not paper_uploads):
        raise HTTPException(422, "Research + code requires both research documents and project files.")
    uploads = []
    for upload in source_uploads:
        filename = upload.filename or ""
        limit = MAX_ARCHIVE_BYTES if filename.lower().endswith(".zip") else MAX_FILE_BYTES
        data = await upload.read(limit + 1)
        if len(data) > limit:
            raise HTTPException(413, f"{filename or 'File'} exceeds the upload size limit.")
        uploads.append(UploadedBytes(filename, data))

    research_uploads = []
    for upload in paper_uploads:
        filename = upload.filename or ""
        data = await upload.read(MAX_RESEARCH_BYTES + 1)
        if len(data) > MAX_RESEARCH_BYTES:
            raise HTTPException(413, f"{filename or 'Research document'} exceeds the 10 MB limit.")
        research_uploads.append(UploadedBytes(filename, data))
    def extract():
        project_files, errors = read_project_files(uploads) if uploads else ([], [])
        if errors:
            return [], errors
        papers, errors = read_research_files(research_uploads) if research_uploads else ([], [])
        return ([], errors) if errors else combine_sources(project_files, papers)
    await parser_slots.acquire()
    if (creation_pending.get(getattr(request.state, 'room_admission', None)) != account['id']
            or asyncio.get_running_loop().time() >= request.state.room_deadline):
        parser_slots.release()
        raise HTTPException(408, 'Room creation expired. Please retry.')
    future = asyncio.get_running_loop().run_in_executor(parser_pool, extract)
    slots = parser_slots
    future.add_done_callback(lambda _: slots.release())
    project_files, errors = await asyncio.shield(future)
    if errors:
        raise HTTPException(422, errors[0])
    async with registry_lock:
        if (creation_pending.get(getattr(request.state, 'room_admission', None)) != account['id']
                or asyncio.get_running_loop().time() >= request.state.room_deadline):
            raise HTTPException(408, 'Room creation expired. Please retry.')
        code = _room_code()
        while code in rooms:
            code = _room_code()
        token = _new_token()
        rooms[code] = Room(code, project_files, {token: Player(token, name, 0, True)}, defense_type, research_stage,
                           owner_account_id=account["id"])
    return {"room_code": code, "player_token": token}


@app.get('/api/rooms')
async def list_owned_rooms(request: Request):
    account = require_account(request)
    await _cleanup_rooms()
    return {'limit': limit('ROOM_HOST_LIMIT', 2, 20), 'rooms': [
        {'room_code': room.code, 'phase': room.phase, 'expires_at_ms': room.expires_at(),
         'can_close': room.expires_at() is not None}
        for room in rooms.values() if room.owner_account_id == account['id']]}


@app.post('/api/rooms/{code}/resume')
async def resume_owned_room(code: str, request: Request):
    account = require_account(request)
    check_csrf(request, account)
    await _cleanup_rooms()
    room = rooms.get(code.upper())
    if room is None:
        raise HTTPException(404, 'Room not found. Create a fresh room.')
    async with room.lock:
        if room.closed or room.owner_account_id != account['id']:
            raise HTTPException(403, 'Only the room owner can resume host access.')
        host = next(player for player in room.players.values() if player.is_host)
        return {'room_code': room.code, 'player_token': host.token}


@app.delete('/api/rooms/{code}')
async def close_owned_room(code: str, request: Request):
    account = require_account(request)
    check_csrf(request, account)
    room = rooms.get(code.upper())
    if room is None:
        raise HTTPException(404, 'Room not found. Create a fresh room.')
    if room.owner_account_id != account['id']:
        raise HTTPException(403, 'Only the room owner can close it.')
    if not await _remove_room(room):
        raise HTTPException(409, 'End or recover the active defense before closing this room.')
    return {'closed': True}


class JoinRequest(BaseModel):
    name: str


@app.post("/api/rooms/{code}/join")
async def join_room(code: str, request: JoinRequest) -> dict[str, str]:
    name = _player_name(request.name)
    room = rooms.get(code.upper())
    if room is None:
        raise HTTPException(404, "Room not found. Check the invite code.")
    async with room.lock:
        if room.closed:
            raise HTTPException(404, "Room not found. Create a fresh room.")
        if len(room.players) >= MAX_PLAYERS:
            raise HTTPException(409, "This room already has four defenders.")
        occupied = {player.seat for player in room.players.values()}
        seat = next(index for index in range(MAX_PLAYERS) if index not in occupied)
        token = _new_token()
        room.activity_ms = _now_ms()
        room.players[token] = Player(token, name, seat)
        room.revision += 1
    await publish(room)
    return {"room_code": room.code, "player_token": token}


async def _send_error(socket: WebSocket, message: str) -> None:
    try:
        await socket.send_json({"type": "error", "message": message})
    except (RuntimeError, OSError, WebSocketDisconnect):
        # The peer may close while the server is preparing its reply.
        pass


def _host_account(room: Room, socket: WebSocket):
    account = require_account(socket)
    if account["id"] != room.owner_account_id or socket.headers.get("origin") != auth_settings()[2]:
        raise HTTPException(403, "Sign in with the account that created this room to use host controls.")
    return account


def _reserve_room_run(room: Room, account_id: str, confirmed: bool, retry: bool = False) -> None:
    if not retry:
        if live_mode():
            from account_store import account_access
            access=account_access(account_id)
        else:
            access = require_run_access(account_id)
        if not access["free_access"] and not confirmed:
            raise AccessError("Confirm the 10-credit cost before starting or restarting this run.")
    run_id = room.run_id if retry and room.run_id else secrets.token_hex(24)
    if live_mode():
        from account_store import account_access
        if not account_access(account_id)['free_access']:
            from payments_live import settings
            try:settings()
            except HTTPException:
                raise AccessError('Paid defenses are temporarily unavailable. Your credits are retained.') from None
        LiveStore().reserve_run(account_id,run_id,SERVICE_ID,room.code,
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


async def _handle_action(room: Room, player: Player, socket: WebSocket, message: dict) -> None:
    if live_mode() and app.state.room_service_status != "ready":
        await _send_error(socket, SERVICE_STARTING_MESSAGE)
        return
    account = None
    if player.is_host:
        try:
            account = _host_account(room, socket)
        except HTTPException as failure:
            await _send_error(socket, failure.detail)
            return
    if room.closed:
        await _send_error(socket, "Room not found. Create a fresh room.")
        return
    await _expire_deadline(room)
    action = message.get("type")
    error = None
    expired_action = False
    generate_first = None
    generation_id = None
    feedback_generation_id = None
    interpretation_id = None
    plan_generation_id = None
    async with room.lock:
        if room.closed:
            await _send_error(socket, "Room not found. Create a fresh room.")
            return
        # Authorize before mutation or scheduling any paid AI work.
        try:
            if player.is_host and action in {"prepare_research_plan", "retry_research_plan"}:
                require_run_access(account["id"])
            if player.is_host and action == "start" and room.phase == "lobby" and room.defense is None:
                # Budget/map validation below must precede a reservation.
                if room.defense_type == "code" or (room.research_plan and room.research_plan_approved
                        and message.get("plan_id") == room.research_plan.id
                        and type(message.get("question_budget")) is int
                        and message["question_budget"] == room.research_budget_preview):
                    _reserve_room_run(room, account["id"], message.get("confirm_cost") is True)
            if player.is_host and action == "restart" and (room.defense_type == "code" or (room.research_plan and room.research_plan_approved)):
                _reserve_room_run(room, account["id"], message.get("confirm_cost") is True)
            if player.is_host and action == "retry" and room.phase == "retry" and (room.defense is None or not room.defense.turns):
                _reserve_room_run(room, account["id"], True, retry=True)
        except AccessError as failure:
            await _send_error(socket, str(failure))
            return
        if action in {"start", "restart", "retry", "retry_coaching", "prepare_research_plan", "retry_research_plan", "approve_research_plan", "end_defense", "end_unavailable"} and not player.is_host:
            error = "Only the host can control the defense."
        elif action in {"prepare_research_plan", "retry_research_plan"}:
            if room.defense_type == "code":
                error = "Paper mapping is available for research and mixed defenses only."
            elif room.phase != "lobby" or room.defense is not None:
                error = "Prepare the research map before starting a defense."
            elif room.research_planning_status == "planning":
                error = "The research map is already being prepared."
            elif action == "retry_research_plan" and room.research_planning_status != "failed":
                error = "There is no failed research map to retry."
            else:
                room.activity_ms = _now_ms()
                room.research_planning_status = "planning"
                room.research_plan_error = None
                room.research_plan = None
                room.research_budget_preview = None
                room.research_plan_approved = False
                room.research_plan_generation_id += 1
                plan_generation_id = room.research_plan_generation_id
                room.revision += 1
        elif action == "approve_research_plan":
            if room.phase != "lobby" or room.research_planning_status != "ready" or room.research_plan is None:
                error = "Prepare a research map before confirming its question budget."
            elif message.get("plan_id") != room.research_plan.id:
                error = "The research map changed. Review the current map before confirming."
            else:
                try:
                    room.research_budget_preview = validate_question_budget(message.get("question_budget"))
                except ValueError as exc:
                    error = str(exc)
                else:
                    room.activity_ms = _now_ms()
                    room.research_plan_approved = True
                    room.revision += 1
        elif action == "start":
            if room.phase != "lobby" or room.defense is not None:
                error = "The defense has already started."
            elif room.research_planning_status == "planning":
                error = "Wait for the research map to finish before starting."
            elif room.defense_type != "code" and (
                    room.research_plan is None or not room.research_plan_approved
                    or message.get("plan_id") != room.research_plan.id
                    or type(message.get("question_budget")) is not int
                    or message.get("question_budget") != room.research_budget_preview):
                error = "Prepare and confirm the current research map and question budget before starting."
            else:
                if room.defense_type != "code":
                    room.defense = ResearchDefenseSession.create(room.research_plan, room.research_budget_preview,
                                                                 room.defense_type, room.research_stage)
                room.phase = "generating"
                room.error = None
                room.generation_id += 1
                generation_id = room.generation_id
                room.revision += 1
                generate_first = True
        elif action == "end_unavailable":
            if not live_mode() or not room.run_id:
                error = "There is no unavailable live defense to end."
            else:
                try:
                    LiveStore().end_unavailable(account["id"],room.run_id)
                except AccessError as failure:
                    error = str(failure)
                else:
                    room.generation_id += 1
                    room.feedback_generation_id += 1
                    room.discard_pending()
                    _clear_clock_locked(room)
                    if isinstance(room.defense,ResearchDefenseSession) and not room.defense.completed:
                        room.defense.end()
                    room.phase = "complete"
                    room.settled = True
                    room.terminal_ms = _now_ms()
                    room.feedback_status = "none"
                    room.error = "The unavailable defense was ended. Check Account for any returned credits."
                    room.revision += 1
        elif action == "end_defense":
            if room.defense_type == "code" or not isinstance(room.defense, ResearchDefenseSession):
                error = "Ending early is available for an active research defense."
            elif room.defense.completed:
                error = "The defense is already complete."
            else:
                room.generation_id += 1
                room.discard_pending()
                _clear_clock_locked(room)
                room.defense.end()
                release_run(room.run_id)
                if live_mode() and room.run_id:
                    LiveStore().finish_run(room.run_id,"ended")
                room.phase = "complete"
                room.error = None
                room.feedback_status = "generating"
                room.feedback_generation_id += 1
                feedback_generation_id = room.feedback_generation_id
                room.revision += 1
        elif action == "restart":
            # Cancel an in-flight map without letting it mutate an active defense.
            room.research_plan_generation_id += 1
            if room.research_planning_status == "planning":
                room.research_planning_status = "none"
                room.research_plan_error = None
            room.discard_pending()
            _clear_clock_locked(room)
            room.defense = None
            room.answered_by.clear()
            room.answered_by_seat.clear()
            room.chat.clear()
            room.chat_seq = 0
            room.phase = "generating"
            room.error = None
            room.generation_id += 1
            generation_id = room.generation_id
            room.feedback_status = "none"
            room.feedback = None
            room.feedback_generation_id += 1
            room.revision += 1
            generate_first = True
            if room.defense_type != "code":
                if room.research_plan is not None and room.research_plan_approved:
                    room.defense = ResearchDefenseSession.create(room.research_plan, room.research_budget_preview,
                                                                 room.defense_type, room.research_stage)
                else:
                    room.phase = "lobby"
                    generate_first = None
        elif action == "retry":
            if room.phase != "retry":
                error = "There is no failed question to retry."
            else:
                generate_first = room.defense is None
                room.phase = "generating"
                room.error = None
                room.generation_id += 1
                generation_id = room.generation_id
                room.revision += 1
        elif action == "retry_coaching":
            if room.phase != "complete" or room.feedback_status != "failed":
                error = "There is no failed coaching report to retry."
            else:
                room.feedback_status = "generating"
                room.error = None
                room.feedback_generation_id += 1
                feedback_generation_id = room.feedback_generation_id
                room.revision += 1
        elif action == "cast_vote":
            try:
                room.cast_vote(player.token, message.get("seat"), _online_players(room), _now_ms())
            except HTTPException as failure:
                error = str(failure.detail)
            except ValueError as failure:
                error = str(failure)
                expired_action = isinstance(failure, DeadlineExpired)
            else:
                room.revision += 1
        elif action == "send_chat":
            content = message.get("text")
            if not isinstance(content, str) or not content.strip():
                error = "Write a team message before sending."
            elif len(content) > MAX_CHAT_CHARS:
                error = f"Keep team messages under {MAX_CHAT_CHARS} characters."
            else:
                room.chat_seq += 1
                room.chat.append({"id": room.chat_seq, "seat": player.seat, "name": player.name,
                                  "text": content.strip(), "sent_at_ms": _now_ms()})
                room.chat = room.chat[-MAX_CHAT_MESSAGES:]
                room.revision += 1
        elif action == "retry_interpretation":
            try:
                if room.phase != 'interpretation_retry' or room.pending_submission is None or not (player.is_host or room.selected_seat == player.seat):
                    raise ValueError('Only the host or chosen defender can retry a failed submission.')
                if room.interpretation_attempts >= limit('AI_INTERPRETATION_ATTEMPTS', 6, 20):
                    raise ValueError('Interpretation allowance used. Use the saved submission as an answer.')
                room.ai_budget.admit(f'interpret:{len(room.defense.turns)-1}', limit('AI_INTERPRETATION_ATTEMPTS', 6, 20), room.owner_account_id or room.code)
                room.retry_interpretation(is_host=player.is_host, seat=player.seat)
            except HTTPException as failure:
                error = str(failure.detail)
            except ValueError as failure:
                error = str(failure)
            else:
                interpretation_id = room.interpretation_id
                room.revision += 1
        elif action == "use_pending_as_answer":
            try:
                room.accept_saved_answer(room.defense, player.token, player.seat)
            except HTTPException as failure:
                error = str(failure.detail)
            except ValueError as failure:
                error = str(failure)
            else:
                generation_id, feedback_generation_id = _resolve_turn_locked(room)
                if generation_id is not None:
                    generate_first = False
                room.revision += 1
        elif action == 'submit_direct_answer':
            try:
                room.submit_direct(player.token, player.name, player.seat, message.get('turn'), message.get('answer'), room.defense, _now_ms())
            except HTTPException as failure:
                error = str(failure.detail)
            except ValueError as failure:
                error = str(failure)
                expired_action = isinstance(failure, DeadlineExpired)
            else:
                generation_id, feedback_generation_id = _resolve_turn_locked(room)
                if generation_id is not None:
                    generate_first = False
                room.revision += 1
        elif action == "submit_answer":
            try:
                room.validate_submit(player.seat, message.get('turn'), message.get('answer'), room.defense, _now_ms())
                room.ai_budget.admit(f'interpret:{len(room.defense.turns)-1}', limit('AI_INTERPRETATION_ATTEMPTS', 6, 20), room.owner_account_id or room.code)
                room.submit(player.token, player.name, player.seat, message.get("turn"), message.get("answer"),
                            room.defense, _now_ms())
            except HTTPException as failure:
                error = str(failure.detail)
            except ValueError as failure:
                error = str(failure)
                expired_action = isinstance(failure, DeadlineExpired)
            else:
                _cancel_clock_task(room)
                _schedule_clock(room, room.clock_id, room.pause_deadline_ms or room.answer_deadline_ms)
                interpretation_id = room.interpretation_id
                room.revision += 1
        else:
            error = "Unknown room action."
    if expired_action:
        await _expire_deadline(room)
    if error:
        await _send_error(socket, error)
        return
    await publish(room)
    if plan_generation_id is not None:
        _schedule_research_plan(room, plan_generation_id)
    if generate_first is not None and generation_id is not None:
        _schedule_generation(room, generation_id, generate_first)
    if feedback_generation_id is not None:
        _schedule_coaching(room, feedback_generation_id)
    if interpretation_id is not None:
        _schedule_interpretation(room, interpretation_id)


@app.websocket("/ws/{code}")
async def room_socket(socket: WebSocket, code: str) -> None:
    await socket.accept()
    if live_mode() and app.state.room_service_status != "ready":
        await _send_error(socket, SERVICE_STARTING_MESSAGE)
        await socket.close(code=1013)
        return
    room = rooms.get(code.upper())
    if room is None:
        await _send_error(socket, "Room not found. Check the invite code.")
        try:
            await socket.close(code=1008)
        except (RuntimeError, OSError, WebSocketDisconnect):
            pass
        return
    try:
        raw = await asyncio.wait_for(socket.receive_text(), timeout=10)
        hello = json.loads(raw) if len(raw) <= 500 else None
        token = hello.get("token") if isinstance(hello, dict) and hello.get("type") == "hello" else None
    except WebSocketDisconnect:
        return
    except (asyncio.TimeoutError, json.JSONDecodeError):
        token = None
    await _observe_absence(room)
    async with room.lock:
        player = room.players.get(token) if isinstance(token, str) else None
        if player is not None and player.is_host:
            try:
                _host_account(room, socket)
            except HTTPException as failure:
                await _send_error(socket, failure.detail)
                await socket.close(code=1008)
                return
        if player is not None:
            player.sockets.add(socket)
            room.absent_since_ms = None
            room.absence_elapsed_ms = 0
            _reassign_if_offline_locked(room)
            room.revision += 1
    if player is None:
        await _send_error(socket, "This room link is no longer valid. Join again.")
        try:
            await socket.close(code=1008)
        except (RuntimeError, OSError, WebSocketDisconnect):
            pass
        return
    await _expire_deadline(room)
    await publish(room)
    try:
        while True:
            raw = await socket.receive_text()
            if len(raw) > MAX_ANSWER_CHARS + 500:
                await _send_error(socket, "Message is too long.")
                continue
            try:
                message = json.loads(raw)
            except json.JSONDecodeError:
                await _send_error(socket, "Invalid room message.")
                continue
            if not isinstance(message, dict):
                await _send_error(socket, "Invalid room message.")
                continue
            await _handle_action(room, player, socket, message)
    except WebSocketDisconnect:
        pass
    finally:
        async with room.lock:
            player.sockets.discard(socket)
            _reassign_if_offline_locked(room)
            room.revision += 1
        await _observe_absence(room)
        await publish(room)


app.include_router(test_payment_router)
app.include_router(live_payment_router)
app.mount("/", StaticFiles(directory=GAME_DIR, html=True), name="game")

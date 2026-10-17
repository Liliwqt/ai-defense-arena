"""Single-process multiplayer room server for AI Defense Arena."""

import asyncio
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import json
import logging
import os
from pathlib import Path
import secrets
import threading

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend.rooms.model import Player, Room, now_ms as _now_ms
from backend.rooms.coordinator import (
    RoomCoordinator, RoomWorkflows,
)
from backend.rooms.commands import (
    VerifiedActor, decode_command,
    ObserveAbsence, JoinDefender, DefenderConnected, DefenderDisconnected, ReclaimRoom,
)

from backend.defense_session import MAX_ANSWER_CHARS
from backend.accounts import configure_auth, require_account, check_csrf, auth_settings
from backend.account_store import release_orphaned_reservations
from backend.financial_policy import live_mode
from backend.live_store import LiveStore, ServiceAlreadyActive
from backend.resource_limits import (limit, creation_rate, ai_rate, client_network,
    JoinAdmissionMiddleware, join_rate, join_capacity, socket_capacity,
    socket_connect_rate, socket_player_rate, socket_message_rate, socket_room_rate)
from backend.payments import router as test_payment_router
from backend.payments_live import router as live_payment_router
from backend.project_files import MAX_ARCHIVE_BYTES, MAX_FILE_BYTES, ProjectFile, read_project_files
from backend.research_files import MAX_RESEARCH_BYTES, read_research_files, combine_sources
from backend.room_documents import DocumentStore


SERVICE_ID = secrets.token_hex(24)
SERVICE_POLL_SECONDS = 2
SERVICE_HEARTBEAT_SECONDS = 10
SERVICE_STARTING_MESSAGE = "The room service is restarting. Please retry shortly."
MAX_ROOMS = 20
MAX_REQUEST_BYTES = 110_000_000
ROOM_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
GAME_DIR = Path(__file__).resolve().parents[1] / "game" / "dist"


@dataclass(frozen=True)
class UploadedBytes:
    name: str
    data: bytes

    def getvalue(self) -> bytes:
        return self.data



rooms: dict[str, Room] = {}
registry_lock = asyncio.Lock()
registry_removals: set[asyncio.Task] = set()
creation_pending = {}
parser_pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix='room-parser')
parser_slots = asyncio.Semaphore(2)

async def _remove_room(room, expired_only=False):
    # Own the full registry operation even if its HTTP/maintenance caller exits.
    # Cleanup and deletion must finish together so a closed room cannot retain
    # uploads and permanently consume the host's room allowance.
    task = asyncio.create_task(_reclaim_registered_room(room, expired_only))
    registry_removals.add(task)

    def finished(done):
        registry_removals.discard(done)
        if not done.cancelled():
            done.exception()

    task.add_done_callback(finished)
    return await asyncio.shield(task)


async def _reclaim_registered_room(room, expired_only):
    # Registry ownership precedes the coordinator's eligibility recheck/fence.
    async with registry_lock:
        if rooms.get(room.code) is not room:
            return False
        result = await _coordinator(room).execute(ReclaimRoom(expired_only))
        if result.accepted:
            del rooms[room.code]
        return result.accepted


async def _shutdown_rooms():
    await asyncio.gather(
        *(_coordinator(room).shutdown() for room in list(rooms.values())),
        *(asyncio.shield(task) for task in tuple(registry_removals)),
    )


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
                await _coordinator(room).execute(ObserveAbsence())
        await _cleanup_rooms()
        try:
            from backend.opening_history import prune_openings
            await asyncio.to_thread(prune_openings)
        except Exception:
            logging.getLogger(__name__).warning("Opening-history retention cleanup unavailable.")
        await asyncio.sleep(5)

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
    app.state.documents = DocumentStore()
    creation_rate.__init__()
    ai_rate.__init__()
    for admission in (join_rate, join_capacity, socket_capacity, socket_connect_rate,
                      socket_player_rate, socket_message_rate, socket_room_rate):
        admission.__init__()
    if not live_mode():
        app.state.documents.start()
        app.state.room_service_status = "ready"
        release_orphaned_reservations()
        maintenance = asyncio.create_task(_room_maintenance())
        try:
            yield
        finally:
            maintenance.cancel()
            await asyncio.gather(maintenance, return_exceptions=True)
            app.state.room_service_status = "stopped"
            await _shutdown_rooms()
            app.state.documents.close()
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
        try:
            app.state.documents.start()
        except BaseException:
            LiveStore().stop_service(service)
            raise
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
                    app.state.documents.start()
                    app.state.room_service_status = "ready"
                    logging.getLogger(__name__).info("Room service lease acquired.")
                LiveStore().heartbeat(service)
                for room in list(rooms.values()):
                    await _coordinator(room).execute(ObserveAbsence())
                await asyncio.sleep(SERVICE_HEARTBEAT_SECONDS)
        except Exception:
            # Never reacquire after losing ownership or advertise a dead heartbeat.
            app.state.room_service_status = "failed"
            logging.getLogger(__name__).error("Room service maintenance failed; room access paused.")
            await _shutdown_rooms()

    async def recover():
        from backend.payments_live import recover_payments
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
        await _shutdown_rooms()
        app.state.documents.close()
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
app.add_middleware(JoinAdmissionMiddleware)


def _player_name(value: str) -> str:
    name = value.strip()
    if not name or len(name) > 24:
        raise HTTPException(422, "Choose a name of 1 to 24 characters.")
    return name


def _room_code() -> str:
    return "".join(secrets.choice(ROOM_ALPHABET) for _ in range(10))


def _new_token() -> str:
    return secrets.token_urlsafe(32)


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
    documents = request.app.state.documents.reserve(research_uploads)
    published = False
    try:
        stop_parsing = threading.Event()
        def extract():
            project_files, errors = read_project_files(uploads) if uploads else ([], [])
            if errors:
                return [], errors
            papers, errors = read_research_files(research_uploads, cancel=stop_parsing) if research_uploads else ([], [])
            if errors:
                return [], errors
            accepted, errors = combine_sources(project_files, papers)
            if not errors:
                documents.stage(accepted, research_uploads)
            return accepted, errors
        await parser_slots.acquire()
        if (creation_pending.get(getattr(request.state, 'room_admission', None)) != account['id']
                or asyncio.get_running_loop().time() >= request.state.room_deadline):
            parser_slots.release()
            raise HTTPException(408, 'Room creation expired. Please retry.')
        future = asyncio.get_running_loop().run_in_executor(parser_pool, extract)
        slots = parser_slots
        def parser_finished(done):
            slots.release()
            if not done.cancelled():
                done.exception()  # Observe a parser that outlives HTTP cancellation.
        future.add_done_callback(parser_finished)
        try:
            project_files, errors = await asyncio.shield(future)
        finally:
            stop_parsing.set()
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
            room = Room(code, project_files, {token: Player(token, name, 0, True)}, defense_type, research_stage,
                        owner_account_id=account["id"], created_ms=_now_ms(), activity_ms=_now_ms(), documents=documents)
            _coordinator(room)
            rooms[code] = room
        published = True
        return {"room_code": code, "player_token": token}
    finally:
        if not published:
            documents.release()



@app.get('/api/rooms')
async def list_owned_rooms(request: Request):
    account = require_account(request)
    await _cleanup_rooms()
    return {'limit': limit('ROOM_HOST_LIMIT', 2, 20), 'rooms': [
        {'room_code': room.code, 'phase': room.phase, 'expires_at_ms': room.expires_at(),
         'can_close': room.expires_at() is not None}
        for room in rooms.values() if room.owner_account_id == account['id']]}


@app.get('/api/rooms/{code}/documents/{document_id}')
async def room_document(code: str, document_id: str, request: Request):
    if live_mode() and app.state.room_service_status != 'ready':
        raise HTTPException(503, SERVICE_STARTING_MESSAGE)
    room = rooms.get(code.upper())
    if room is None:
        raise HTTPException(404, 'Paper unavailable. Create a fresh room.')
    async with room.lock:
        player = room.players.get(request.headers.get('X-Player-Token', ''))
        if player is None:
            raise HTTPException(403, 'Join this room to view its papers.')
        if player.is_host and require_account(request)['id'] != room.owner_account_id:
            raise HTTPException(403, 'Sign in as the room owner to view its papers.')
        expiry = room.expires_at()
        if room.closed or (expiry is not None and _now_ms() >= expiry) or room.documents is None:
            raise HTTPException(404, 'Paper unavailable. Create a fresh room.')
        stream = room.documents.open(document_id)
    async def chunks():
        try:
            while data := await asyncio.to_thread(stream.read, 65536):
                yield data
        finally:
            stream.close()
    return StreamingResponse(chunks(), media_type='application/pdf',
                             headers={'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff'})


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
    token = _new_token()
    result = await _coordinator(room).execute(JoinDefender(token, name))
    if not result.accepted:
        raise HTTPException(409 if result.reason == "room_full" else 404, result.error)
    return {"room_code": room.code, "player_token": token}


async def _send_error(socket: WebSocket, message: str, reason: str | None = None) -> None:
    try:
        await asyncio.wait_for(socket.send_json({"type": "error", "message": message, **({"reason": reason} if reason else {})}), 1)
    except (RuntimeError, OSError, WebSocketDisconnect):
        # The peer may close while the server is preparing its reply.
        pass


def _host_account(room: Room, socket: WebSocket):
    account = require_account(socket)
    if account["id"] != room.owner_account_id or socket.headers.get("origin") != auth_settings()[2]:
        raise HTTPException(403, "Sign in with the account that created this room to use host controls.")
    return account


def _coordinator(room: Room) -> RoomCoordinator:
    """Compose one coordinator with real clock and service identity."""
    if room.coordinator is None:
        RoomCoordinator(room, RoomWorkflows(
            now=lambda: _now_ms(),
            service_id=SERVICE_ID,
        ))
    return room.coordinator


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
    actor = VerifiedActor(player.token, account["id"] if account else None)
    try:
        command = decode_command(message)
    except ValueError as failure:
        await _send_error(socket, str(failure))
        return
    result = await _coordinator(room).execute(command, actor)
    if not result.accepted:
        await _send_error(socket, result.error, result.reason)


@app.websocket("/ws/{code}")
async def room_socket(socket: WebSocket, code: str) -> None:
    network = client_network(socket)
    try:
        socket_connect_rate.admit(network, 60)
        socket_capacity.acquire(network, 256, 32)
    except HTTPException:
        await asyncio.wait_for(socket.close(code=1013), 1)
        return
    try:
        await _serve_room_socket(socket, code)
    except (asyncio.TimeoutError, RuntimeError, OSError, WebSocketDisconnect):
        try:
            await asyncio.wait_for(socket.close(code=1013), 1)
        except (asyncio.TimeoutError, RuntimeError, OSError, WebSocketDisconnect):
            pass
    finally:
        socket_capacity.release(network)


async def _serve_room_socket(socket: WebSocket, code: str) -> None:
    await asyncio.wait_for(socket.accept(), 1)
    if live_mode() and app.state.room_service_status != "ready":
        await _send_error(socket, SERVICE_STARTING_MESSAGE)
        await asyncio.wait_for(socket.close(code=1013), 1)
        return
    room = rooms.get(code.upper())
    if room is None:
        await _send_error(socket, "Room not found. Check the invite code.")
        try:
            await asyncio.wait_for(socket.close(code=1008), 1)
        except (RuntimeError, OSError, WebSocketDisconnect):
            pass
        return
    try:
        raw = await asyncio.wait_for(socket.receive_text(), timeout=10)
        hello = json.loads(raw) if len(raw) <= 500 else None
        token = hello.get("token") if isinstance(hello, dict) and hello.get("type") == "hello" else None
    except WebSocketDisconnect:
        return
    except (asyncio.TimeoutError, json.JSONDecodeError, KeyError):
        token = None
    async with room.lock:
        player = room.players.get(token) if isinstance(token, str) else None
    if player is None:
        await _send_error(socket, "This room link is no longer valid. Join again.")
        try:
            await asyncio.wait_for(socket.close(code=1008), 1)
        except (RuntimeError, OSError, WebSocketDisconnect):
            pass
        return
    account = None
    if player.is_host:
        try:
            account = _host_account(room, socket)
        except HTTPException as failure:
            await _send_error(socket, failure.detail)
            await asyncio.wait_for(socket.close(code=1008), 1)
            return
    try:
        result = await _coordinator(room).execute(
            DefenderConnected(socket), VerifiedActor(player.token, account["id"] if account else None))
        if not result.accepted:
            await _send_error(socket, result.error, result.reason)
            await asyncio.wait_for(socket.close(code=1013 if result.reason == "socket_admission" else 1008), 1)
            return
        while True:
            event = await socket.receive()
            if event['type'] == 'websocket.disconnect':
                break
            try:
                # Shared across all sockets for this token; reconnect cannot reset it.
                socket_message_rate.admit(player.token, 10, seconds=2)
                socket_room_rate.admit(room.code, 24, seconds=2)
            except HTTPException:
                await asyncio.wait_for(_send_error(socket, 'Too many room messages. Retry shortly.', 'socket_admission'), 1)
                await asyncio.wait_for(socket.close(code=1013), 1)
                break
            raw = event.get('text')
            if not isinstance(raw, str):
                await asyncio.wait_for(socket.close(code=1003), 1)
                break
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
    except (WebSocketDisconnect, asyncio.TimeoutError, RuntimeError, OSError):
        pass
    finally:
        await _coordinator(room).execute(DefenderDisconnected(player.token, socket))


app.include_router(test_payment_router)
app.include_router(live_payment_router)
app.mount("/", StaticFiles(directory=GAME_DIR, html=True), name="game")

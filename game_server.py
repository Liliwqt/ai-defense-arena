"""Single-process multiplayer room server for AI Defense Arena."""

import asyncio
from dataclasses import dataclass, field
import json
import os
from pathlib import Path
import secrets
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from openai import OpenAIError
from pydantic import BaseModel, ValidationError

from defense_session import DefenseSession, MAX_ANSWER_CHARS, PANELIST_ORDER
from project_files import MAX_ARCHIVE_BYTES, MAX_FILE_BYTES, ProjectFile, read_project_files
from question_generator import (
    DEFAULT_MODEL,
    CoachingReport,
    QuestionGenerationError,
    describe_openai_error,
    generate_coaching_report,
    generate_first_question,
    generate_next_move,
)


MAX_PLAYERS = 4
MAX_ROOMS = 20
MAX_REQUEST_BYTES = MAX_ARCHIVE_BYTES + 2_000_000
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
class Room:
    code: str
    files: list[ProjectFile]
    players: dict[str, Player]
    defense: DefenseSession | None = None
    answered_by: dict[int, str] = field(default_factory=dict)
    answered_by_seat: dict[int, int] = field(default_factory=dict)
    phase: str = "lobby"
    error: str | None = None
    revision: int = 0
    generation_id: int = 0
    feedback_status: str = "none"   # none | generating | ready | failed
    feedback: CoachingReport | None = None
    feedback_generation_id: int = 0
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    broadcast_lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    def snapshot(self, recipient: Player | None = None) -> dict[str, Any]:
        turns = []
        if self.defense:
            for index, turn in enumerate(self.defense.turns):
                turns.append(
                    {
                        "panelist": turn.panelist,
                        "question": turn.question.question,
                        "filename": turn.question.filename,
                        "evidence_line": turn.question.evidence_line,
                        "evidence_text": turn.question.evidence_text,
                        "answer": turn.answer,
                        "answered_by": self.answered_by.get(index),
                        "answered_by_seat": self.answered_by_seat.get(index),
                    }
                )
        if self.defense and self.defense.awaiting_answer:
            active_panelist = self.defense.turns[-1].panelist
        elif self.defense and self.defense.needs_question:
            active_panelist = self.defense.pending_panelist
        elif self.phase == "generating":
            active_panelist = PANELIST_ORDER[0]
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
            "feedback_status": self.feedback_status,
            "feedback": feedback_dict,
        }


rooms: dict[str, Room] = {}
registry_lock = asyncio.Lock()
app = FastAPI(title="AI Defense Arena")


@app.middleware("http")
async def reject_large_uploads(request, call_next):
    if request.url.path == "/api/rooms":
        length = request.headers.get("content-length")
        if length and length.isdigit() and int(length) > MAX_REQUEST_BYTES:
            return JSONResponse({"detail": "Upload request is too large."}, status_code=413)
    return await call_next(request)


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
    if isinstance(error, QuestionGenerationError):
        return str(error)
    if isinstance(error, OpenAIError):
        return describe_openai_error(error, os.getenv("OPENAI_MODEL") or DEFAULT_MODEL, os.getenv("OPENAI_API_KEY"))
    if isinstance(error, ValidationError):
        return "The AI returned an unexpected response. Please try again."
    return "Could not generate a question. Please try again."


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


async def _generate_question(room: Room, generation_id: int, first: bool) -> None:
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL") or DEFAULT_MODEL
    try:
        if first:
            question = await asyncio.to_thread(
                generate_first_question, room.files, api_key, model
            )
        else:
            async with room.lock:
                if room.generation_id != generation_id or room.defense is None:
                    return
                allowed = room.defense.allowed_next_panelists
                may_complete = room.defense.may_complete
                history = room.defense.answered_history()
            move = await asyncio.to_thread(
                generate_next_move,
                room.files,
                api_key,
                history=history,
                allowed_panelists=allowed,
                may_complete=may_complete,
                model=model,
            )
    except Exception as error:
        async with room.lock:
            if room.generation_id != generation_id:
                return
            room.phase = "retry"
            room.error = _safe_generation_error(error)
            room.revision += 1
        await publish(room)
        return

    start_coaching = False
    feedback_generation_id = None
    async with room.lock:
        if room.generation_id != generation_id:
            return
        if first:
            room.defense = DefenseSession.start(question)
            room.phase = "question"
        elif room.defense is not None and room.defense.needs_question:
            room.defense.apply_move(move)
            if room.defense.completed:
                room.phase = "complete"
                room.feedback_status = "generating"
                room.feedback_generation_id += 1
                feedback_generation_id = room.feedback_generation_id
                start_coaching = True
            else:
                room.phase = "question"
        else:
            return
        room.error = None
        room.revision += 1
    await publish(room)
    if start_coaching and feedback_generation_id is not None:
        _schedule_coaching(room, feedback_generation_id)


def _schedule_generation(room: Room, generation_id: int, first: bool) -> None:
    task = asyncio.create_task(_generate_question(room, generation_id, first))
    task.add_done_callback(lambda finished: finished.exception() if not finished.cancelled() else None)


async def _generate_coaching(room: Room, feedback_generation_id: int) -> None:
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL") or DEFAULT_MODEL
    async with room.lock:
        if room.feedback_generation_id != feedback_generation_id or room.defense is None:
            return
        history = room.defense.answered_history()
    try:
        report = await asyncio.to_thread(
            generate_coaching_report, room.files, history, api_key, model
        )
    except Exception as error:
        async with room.lock:
            if room.feedback_generation_id != feedback_generation_id:
                return
            room.feedback_status = "failed"
            room.error = _safe_generation_error(error)
            room.revision += 1
        await publish(room)
        return

    async with room.lock:
        if room.feedback_generation_id != feedback_generation_id:
            return
        room.feedback = report
        room.feedback_status = "ready"
        room.error = None
        room.revision += 1
    await publish(room)


def _schedule_coaching(room: Room, feedback_generation_id: int) -> None:
    task = asyncio.create_task(_generate_coaching(room, feedback_generation_id))
    task.add_done_callback(lambda finished: finished.exception() if not finished.cancelled() else None)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/rooms", status_code=201)
async def create_room(
    host_name: str = Form(...),
    host_passcode: str = Form(...),
    files: list[UploadFile] = File(...),
) -> dict[str, str]:
    expected = os.getenv("GAME_HOST_PASSCODE") or ""
    if not expected:
        raise HTTPException(503, "Room creation is not configured on this server.")
    if not secrets.compare_digest(host_passcode, expected):
        raise HTTPException(403, "Invalid host passcode.")
    name = _player_name(host_name)
    uploads = []
    for upload in files:
        filename = upload.filename or ""
        limit = MAX_ARCHIVE_BYTES if filename.lower().endswith(".zip") else MAX_FILE_BYTES
        data = await upload.read(limit + 1)
        if len(data) > limit:
            raise HTTPException(413, f"{filename or 'File'} exceeds the upload size limit.")
        uploads.append(UploadedBytes(filename, data))
    project_files, errors = read_project_files(uploads)
    if errors:
        raise HTTPException(422, errors[0])
    async with registry_lock:
        if len(rooms) >= MAX_ROOMS:
            raise HTTPException(503, "Room capacity reached. Try again later.")
        code = _room_code()
        while code in rooms:
            code = _room_code()
        token = _new_token()
        rooms[code] = Room(code, project_files, {token: Player(token, name, 0, True)})
    return {"room_code": code, "player_token": token}


class JoinRequest(BaseModel):
    name: str


@app.post("/api/rooms/{code}/join")
async def join_room(code: str, request: JoinRequest) -> dict[str, str]:
    name = _player_name(request.name)
    room = rooms.get(code.upper())
    if room is None:
        raise HTTPException(404, "Room not found. Check the invite code.")
    async with room.lock:
        if len(room.players) >= MAX_PLAYERS:
            raise HTTPException(409, "This room already has four defenders.")
        occupied = {player.seat for player in room.players.values()}
        seat = next(index for index in range(MAX_PLAYERS) if index not in occupied)
        token = _new_token()
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


async def _handle_action(room: Room, player: Player, socket: WebSocket, message: dict) -> None:
    action = message.get("type")
    error = None
    generate_first = None
    generation_id = None
    start_coaching = False
    feedback_generation_id = None
    async with room.lock:
        if action in {"start", "restart", "retry", "retry_coaching"} and not player.is_host:
            error = "Only the host can control the defense."
        elif action == "start":
            if room.phase != "lobby" or room.defense is not None:
                error = "The defense has already started."
            else:
                room.phase = "generating"
                room.error = None
                room.generation_id += 1
                generation_id = room.generation_id
                room.revision += 1
                generate_first = True
        elif action == "restart":
            room.defense = None
            room.answered_by.clear()
            room.answered_by_seat.clear()
            room.phase = "generating"
            room.error = None
            room.generation_id += 1
            generation_id = room.generation_id
            room.feedback_status = "none"
            room.feedback = None
            room.feedback_generation_id += 1
            room.revision += 1
            generate_first = True
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
                start_coaching = True
                room.revision += 1
        elif action == "submit_answer":
            turn = message.get("turn")
            answer = message.get("answer")
            if room.phase != "question" or room.defense is None:
                error = "There is no question awaiting an answer."
            elif isinstance(turn, bool) or not isinstance(turn, int) or turn != len(room.defense.turns) - 1:
                error = "That question has already been answered."
            elif not isinstance(answer, str):
                error = "Write an answer before continuing."
            elif len(answer) > MAX_ANSWER_CHARS:
                error = f"Keep your answer under {MAX_ANSWER_CHARS:,} characters."
            else:
                try:
                    room.defense.submit_answer(answer)
                except ValueError as validation_error:
                    error = str(validation_error)
                else:
                    room.answered_by[turn] = player.name
                    room.answered_by_seat[turn] = player.seat
                    if room.defense.completed:
                        room.phase = "complete"
                        room.feedback_status = "generating"
                        room.feedback_generation_id += 1
                        feedback_generation_id = room.feedback_generation_id
                        start_coaching = True
                    else:
                        room.phase = "generating"
                        generate_first = False
                        room.generation_id += 1
                        generation_id = room.generation_id
                    room.revision += 1
        else:
            error = "Unknown room action."
    if error:
        await _send_error(socket, error)
        return
    await publish(room)
    if generate_first is not None and generation_id is not None:
        _schedule_generation(room, generation_id, generate_first)
    if start_coaching and feedback_generation_id is not None:
        _schedule_coaching(room, feedback_generation_id)


@app.websocket("/ws/{code}")
async def room_socket(socket: WebSocket, code: str) -> None:
    await socket.accept()
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
    async with room.lock:
        player = room.players.get(token) if isinstance(token, str) else None
        if player is not None:
            player.sockets.add(socket)
            room.revision += 1
    if player is None:
        await _send_error(socket, "This room link is no longer valid. Join again.")
        try:
            await socket.close(code=1008)
        except (RuntimeError, OSError, WebSocketDisconnect):
            pass
        return
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
            room.revision += 1
        await publish(room)


app.mount("/", StaticFiles(directory=GAME_DIR, html=True), name="game")

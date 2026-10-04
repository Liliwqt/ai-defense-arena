"""Single-process multiplayer room server for AI Defense Arena."""

import asyncio
from dataclasses import dataclass, field
import json
import os
from pathlib import Path
import secrets
import time
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from openai import OpenAIError
from pydantic import BaseModel, ValidationError

from defense_session import DefenseSession, ResearchDefenseSession, MAX_ANSWER_CHARS, PANELIST_ORDER
from project_files import MAX_ARCHIVE_BYTES, MAX_FILE_BYTES, ProjectFile, read_project_files
from research_files import MAX_RESEARCH_BYTES, read_research_files, combine_sources
from research_plan import ResearchPlan, generate_research_plan, validate_question_budget
from question_generator import (
    DEFAULT_MODEL,
    CoachingReport,
    ClarificationExchange,
    interpret_submission,
    QuestionGenerationError,
    describe_openai_error,
    generate_coaching_report,
    generate_first_question,
    generate_next_move,
    generate_research_move,
)


MAX_PLAYERS = 4
VOTE_MS = 15_000
ANSWER_MS = 120_000
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
class PendingSubmission:
    turn: int
    token: str
    name: str
    seat: int
    text: str
    remaining_ms: int


@dataclass
class Room:
    code: str
    files: list[ProjectFile]
    players: dict[str, Player]
    defense_type: str = "code"
    research_stage: str = "infer"
    defense: DefenseSession | None = None
    answered_by: dict[int, str] = field(default_factory=dict)
    answered_by_seat: dict[int, int] = field(default_factory=dict)
    phase: str = "lobby"
    error: str | None = None
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
    vote_deadline_ms: int | None = None
    answer_deadline_ms: int | None = None
    selected_seat: int | None = None
    votes: dict[str, int] = field(default_factory=dict)
    chat: list[dict[str, Any]] = field(default_factory=list)
    chat_seq: int = 0
    pending_submission: PendingSubmission | None = None
    interpretation_id: int = 0
    clock_id: int = 0
    clock_task: asyncio.Task | None = field(default=None, repr=False)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    broadcast_lock: asyncio.Lock = field(default_factory=asyncio.Lock)

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


def _online_seats(room: Room) -> list[int]:
    return sorted(player.seat for player in room.players.values() if player.sockets)


def _set_selected_locked(room: Room, seat: int | None) -> None:
    room.selected_seat = seat
    if room.defense and room.defense.awaiting_answer:
        room.defense.turns[-1].assigned_seat = seat


def _reassign_if_offline_locked(room: Room) -> bool:
    if room.phase != "question":
        return False
    online = _online_seats(room)
    if room.selected_seat in online:
        return False
    replacement = secrets.choice(online) if online else None
    if replacement == room.selected_seat:
        return False
    _set_selected_locked(room, replacement)
    room.revision += 1
    return True


def _clear_clock_locked(room: Room) -> None:
    room.clock_id += 1
    room.vote_deadline_ms = None
    room.answer_deadline_ms = None
    room.selected_seat = None
    room.votes.clear()
    if room.clock_task and room.clock_task is not asyncio.current_task():
        room.clock_task.cancel()
    room.clock_task = None


def _pause_answer_clock_locked(room: Room) -> None:
    room.clock_id += 1
    if room.clock_task and room.clock_task is not asyncio.current_task():
        room.clock_task.cancel()
    room.clock_task = None
    room.answer_deadline_ms = None


def _resume_answer_clock_locked(room: Room, remaining_ms: int) -> tuple[int, int]:
    room.phase = "question"
    room.answer_deadline_ms = _now_ms() + remaining_ms
    room.clock_id += 1
    _reassign_if_offline_locked(room)
    return room.clock_id, room.answer_deadline_ms


def _resolve_turn_locked(room: Room) -> tuple[int | None, int | None]:
    """Finish a resolved turn and return the next question/coaching generation id."""
    _clear_clock_locked(room)
    assert room.defense is not None
    if room.defense.completed:
        room.phase = "complete"
        room.feedback_status = "generating"
        room.feedback_generation_id += 1
        return None, room.feedback_generation_id
    room.phase = "generating"
    room.generation_id += 1
    return room.generation_id, None


def _choose_vote_winner_locked(room: Room) -> int | None:
    online = _online_seats(room)
    if not online:
        return None
    counts = {seat: 0 for seat in online}
    for token, seat in room.votes.items():
        if seat in counts and room.players[token].sockets:
            counts[seat] += 1
    highest = max(counts.values())
    return secrets.choice([seat for seat, count in counts.items() if count == highest])


def _schedule_clock(room: Room, clock_id: int, deadline_ms: int) -> None:
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
        if expected_id is not None and room.clock_id != expected_id:
            return
        now = _now_ms()
        if room.phase == "voting" and room.vote_deadline_ms is not None and now >= room.vote_deadline_ms:
            winner = _choose_vote_winner_locked(room)
            _set_selected_locked(room, winner)
            room.votes.clear()
            room.vote_deadline_ms = None
            room.phase = "question"
            room.answer_deadline_ms = now + ANSWER_MS
            room.clock_id += 1
            room.revision += 1
            changed = True
            next_clock = (room.clock_id, room.answer_deadline_ms)
        elif room.phase == "question" and room.answer_deadline_ms is not None and now >= room.answer_deadline_ms:
            assert room.defense is not None
            room.defense.time_out_current()
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
            if room.generation_id != generation_id:
                return
            session = room.defense
            research = isinstance(session, ResearchDefenseSession)
            history = session.answered_history() if session else []
            context = session.context() if research else None
            allowed = session.allowed_next_panelists if session and not research else ()
            may_complete = session.may_complete if session and not research else False
        if research:
            move = await asyncio.to_thread(generate_research_move, room.files, api_key,
                history=history, context=context, model=model,
                defense_type=room.defense_type, research_stage=room.research_stage)
        elif first:
            question = await asyncio.to_thread(generate_first_question, room.files, api_key, model,
                defense_type=room.defense_type, research_stage=room.research_stage)
        else:
            move = await asyncio.to_thread(generate_next_move, room.files, api_key,
                history=history, allowed_panelists=allowed, may_complete=may_complete, model=model,
                defense_type=room.defense_type, research_stage=room.research_stage)
        async with room.lock:
            if room.generation_id != generation_id:
                return
            if research:
                session.apply_move(move)
            elif first:
                room.defense = DefenseSession.start(question, room.defense_type, room.research_stage)
            elif session and session.needs_question:
                session.apply_move(move)
            else:
                return
            if room.defense.completed:
                room.phase = "complete"
                room.feedback_status = "generating"
                room.feedback_generation_id += 1
                feedback_id = room.feedback_generation_id
            else:
                room.phase = "voting"
                room.votes.clear()
                room.selected_seat = None
                room.answer_deadline_ms = None
                room.vote_deadline_ms = _now_ms() + VOTE_MS
                room.clock_id += 1
                next_clock = (room.clock_id, room.vote_deadline_ms)
            room.error = None
            room.revision += 1
    except Exception as error:
        async with room.lock:
            if room.generation_id != generation_id:
                return
            room.phase = "retry"
            room.error = _safe_generation_error(error)
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
            if room.interpretation_id != interpretation_id or room.pending_submission is not pending:
                return
            room.phase = "interpretation_retry"
            room.error = _safe_generation_error(error)
            room.revision += 1
        await publish(room)
        return
    next_clock = None
    generation_id = None
    feedback_id = None
    async with room.lock:
        if room.interpretation_id != interpretation_id or room.pending_submission is not pending or room.defense is None:
            return
        if decision.action == "clarify":
            if len(room.defense.turns[pending.turn].clarifications) >= 2:
                room.error = "This question has used both clarifications. Please submit an answer."
            else:
                room.defense.turns[pending.turn].clarifications.append(
                    ClarificationExchange(pending.text, decision.clarification)
                )
                room.error = None
            room.pending_submission = None
            next_clock = _resume_answer_clock_locked(room, pending.remaining_ms)
        else:
            room.defense.submit_answer(pending.text, speaker_name=pending.name)
            room.answered_by[pending.turn] = pending.name
            room.answered_by_seat[pending.turn] = pending.seat
            room.pending_submission = None
            room.error = None
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
        if room.research_plan_generation_id != plan_generation_id or room.phase != "lobby":
            return
        files, mode, stage = list(room.files), room.defense_type, room.research_stage
    try:
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
            report = await asyncio.to_thread(
                generate_coaching_report, room.files, history, api_key, model,
                defense_type=room.defense_type, research_stage=room.research_stage,
                **({"research_context": research_context} if research_context else {}),
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
    host_passcode: str = Form(""),
    files: list[UploadFile] | None = File(None),
    research_files: list[UploadFile] | None = File(None),
    defense_type: str = Form("code"),
    research_stage: str = Form("infer"),
) -> dict[str, str]:
    expected_passcode = os.getenv("GAME_HOST_PASSCODE") or ""
    if not expected_passcode:
        raise HTTPException(503, "Room access is not configured on this server.")
    if not secrets.compare_digest(host_passcode, expected_passcode):
        raise HTTPException(403, "Invalid host passcode.")
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
    project_files, errors = read_project_files(uploads) if uploads else ([], [])
    if errors:
        raise HTTPException(422, errors[0])
    research_uploads = []
    for upload in paper_uploads:
        filename = upload.filename or ""
        data = await upload.read(MAX_RESEARCH_BYTES + 1)
        if len(data) > MAX_RESEARCH_BYTES:
            raise HTTPException(413, f"{filename or 'Research document'} exceeds the 10 MB limit.")
        research_uploads.append(UploadedBytes(filename, data))
    papers, errors = await asyncio.to_thread(read_research_files, research_uploads) if research_uploads else ([], [])
    if errors:
        raise HTTPException(422, errors[0])
    project_files, errors = combine_sources(project_files, papers)
    if errors:
        raise HTTPException(422, errors[0])
    async with registry_lock:
        if len(rooms) >= MAX_ROOMS:
            raise HTTPException(503, "Room capacity reached. Try again later.")
        code = _room_code()
        while code in rooms:
            code = _room_code()
        token = _new_token()
        rooms[code] = Room(code, project_files, {token: Player(token, name, 0, True)}, defense_type, research_stage)
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
        if action in {"start", "restart", "retry", "retry_coaching", "prepare_research_plan", "retry_research_plan", "approve_research_plan", "end_defense"} and not player.is_host:
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
        elif action == "end_defense":
            if room.defense_type == "code" or not isinstance(room.defense, ResearchDefenseSession):
                error = "Ending early is available for an active research defense."
            elif room.defense.completed:
                error = "The defense is already complete."
            else:
                room.generation_id += 1
                room.interpretation_id += 1
                room.pending_submission = None
                _clear_clock_locked(room)
                room.defense.end()
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
            room.interpretation_id += 1
            room.pending_submission = None
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
            seat = message.get("seat")
            if room.phase != "voting" or room.vote_deadline_ms is None:
                error = "Voting is not open."
            elif _now_ms() >= room.vote_deadline_ms:
                error = "Voting time is over."
                expired_action = True
            elif isinstance(seat, bool) or not isinstance(seat, int) or seat not in _online_seats(room):
                error = "Choose an online defender."
            else:
                room.votes[player.token] = seat
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
            if room.phase != "interpretation_retry" or room.pending_submission is None:
                error = "There is no failed submission to retry."
            elif not (player.is_host or room.selected_seat == player.seat):
                error = "Only the host or chosen defender can retry."
            else:
                room.phase = "interpreting"
                room.error = None
                room.interpretation_id += 1
                interpretation_id = room.interpretation_id
                room.revision += 1
        elif action == "use_pending_as_answer":
            pending = room.pending_submission
            if room.phase != "interpretation_retry" or pending is None or room.defense is None:
                error = "There is no failed submission to use as an answer."
            elif room.selected_seat != player.seat or player.token != pending.token:
                error = "Only the chosen defender can use their submission as an answer."
            else:
                room.interpretation_id += 1
                room.defense.submit_answer(pending.text, speaker_name=pending.name)
                room.answered_by[pending.turn] = pending.name
                room.answered_by_seat[pending.turn] = pending.seat
                room.pending_submission = None
                room.error = None
                generation_id, feedback_generation_id = _resolve_turn_locked(room)
                if generation_id is not None:
                    generate_first = False
                room.revision += 1
        elif action == "submit_answer":
            turn = message.get("turn")
            answer = message.get("answer")
            if room.phase != "question" or room.defense is None:
                error = "There is no question awaiting an answer."
            elif room.answer_deadline_ms is None or _now_ms() >= room.answer_deadline_ms:
                error = "Answer time is over."
                expired_action = True
            elif room.selected_seat != player.seat:
                error = "Only the chosen defender can answer this question."
            elif isinstance(turn, bool) or not isinstance(turn, int) or turn != len(room.defense.turns) - 1:
                error = "That question has already been answered."
            elif not isinstance(answer, str):
                error = "Write an answer before continuing."
            elif len(answer) > MAX_ANSWER_CHARS:
                error = f"Keep your answer under {MAX_ANSWER_CHARS:,} characters."
            else:
                if not answer.strip():
                    error = "Write an answer or clarification request before continuing."
                else:
                    remaining_ms = max(0, room.answer_deadline_ms - _now_ms())
                    room.pending_submission = PendingSubmission(turn, player.token, player.name, player.seat,
                                                                answer.strip(), remaining_ms)
                    _pause_answer_clock_locked(room)
                    room.phase = "interpreting"
                    room.error = None
                    room.interpretation_id += 1
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
        await publish(room)


app.mount("/", StaticFiles(directory=GAME_DIR, html=True), name="game")

"""Defender presence, reassignment and observed absence without delivery locks."""

from typing import TYPE_CHECKING

from fastapi import HTTPException
from backend.account_store import release_run
from backend.defense_session import ResearchDefenseSession
from backend.financial_policy import live_mode
from backend.live_store import LiveStore
from backend.resource_limits import socket_player_rate
from backend.rooms.commands import CommandResult, VerifiedActor, JoinDefender, DefenderConnected, DefenderDisconnected
from backend.rooms.model import Player

if TYPE_CHECKING:
    from backend.rooms.coordinator import RoomCoordinator

MAX_PLAYERS = 4


async def join(owner: "RoomCoordinator", command: JoinDefender) -> CommandResult:
    """Allocate a guest seat atomically after transport admission/validation."""
    room = owner._room
    async with room.lock:
        if room.closed:
            return CommandResult(False, "Room not found. Create a fresh room.", "room_closed")
        if len(room.players) >= MAX_PLAYERS:
            return CommandResult(False, "This room already has four defenders.", "room_full")
        occupied = {player.seat for player in room.players.values()}
        seat = next(index for index in range(MAX_PLAYERS) if index not in occupied)
        room.activity_ms = owner._workflows.now()
        room.players[command.token] = Player(command.token, command.name, seat)
        room.revision += 1
    await owner._publish()
    return CommandResult(True)


def reassign_if_offline(owner: "RoomCoordinator") -> bool:
    room = owner._room
    changed = room.reassign(room.online_players(), room.defense)
    if changed:
        room.revision += 1
    return changed


def remove_socket(owner: "RoomCoordinator", socket, token: str | None = None) -> bool:
    """Under the room lock; another tab keeps the same defender online."""
    room = owner._room
    changed = False
    for player in room.players.values():
        if (token is None or player.token == token) and socket in player.sockets:
            if room.speech.current and room.speech.current.token == player.token:
                room.speech.revoke(preserve_draft=True)
            player.sockets.discard(socket)
            room.revision += 1
            changed = True
    if changed:
        reassign_if_offline(owner)
    return changed


async def observe_absence(owner: "RoomCoordinator") -> bool:
    """Return whether state changed; caller owns any subsequent publication."""
    room = owner._room
    async with room.lock:
        if room.closed or not room.run_id:
            return False
        if room.phase == "complete" and room.feedback_status not in {"generating", "failed"}:
            return False
        if any(player.sockets for player in room.players.values()):
            room.absent_since_ms = None
            room.absence_elapsed_ms = 0
            return False
        now = owner._workflows.now()
        if room.absent_since_ms is None:
            room.absent_since_ms = now
        else:
            elapsed = now - room.absent_since_ms
            # Unobserved process stalls/suspension are not defender abandonment.
            if 0 <= elapsed <= 30_000:
                room.absence_elapsed_ms += elapsed
            room.absent_since_ms = now
        if room.absence_elapsed_ms < 600_000:
            return False
        if live_mode():
            LiveStore().finish_run(room.run_id, "abandoned")
        else:
            release_run(room.run_id)
        owner._retire_work()
        if isinstance(room.defense, ResearchDefenseSession) and not room.defense.completed:
            room.defense.end()
        room.phase = "complete"
        room.settled = True
        room.terminal_ms = now
        room.feedback_status = "none"
        if room.coaching_progress:room.coaching_progress.invalidate("abandoned")
        room.error = "This defense was abandoned after everyone disconnected for ten minutes."
        room.revision += 1
        return True


async def connect(owner: "RoomCoordinator", actor: VerifiedActor, command: DefenderConnected) -> CommandResult:
    room = owner._room
    # Preserve observed abandonment before a reconnect clears the absence count.
    await observe_absence(owner)
    async with room.lock:
        if room.closed:
            return CommandResult(False, "Room not found. Create a fresh room.")
        try:
            player = owner._player(actor)
            if command.socket in player.sockets:
                return CommandResult(True)
            socket_player_rate.admit(player.token, 12)
            if len(player.sockets) >= 2 or sum(len(item.sockets) for item in room.players.values()) >= 8:
                raise HTTPException(429, 'Room connection limit reached. Close an extra tab and retry.')
        except ValueError as error:
            return CommandResult(False, str(error))
        except HTTPException as error:
            return CommandResult(False, str(error.detail), "socket_admission")
        player.sockets.add(command.socket)
        room.absent_since_ms = None
        room.absence_elapsed_ms = 0
        reassign_if_offline(owner)
        room.revision += 1
    await owner._expire_deadline()
    await owner._publish()
    return CommandResult(True)


async def disconnect(owner: "RoomCoordinator", command: DefenderDisconnected) -> CommandResult:
    room = owner._room
    async with room.lock:
        if room.closed:
            return CommandResult(True)
        remove_socket(owner, command.socket, command.token)
    await observe_absence(owner)
    # A failed send may already have removed this socket before cancellation
    # interrupted its corrective publication. Coalescing makes duplicate cleanup
    # harmless while ensuring that any unpublished revision reaches survivors.
    await owner._publish()
    return CommandResult(True)

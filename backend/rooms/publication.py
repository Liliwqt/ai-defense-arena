"""Ordered private snapshots with bounded delivery outside the room lock."""

import asyncio
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING

from starlette.websockets import WebSocketDisconnect
from backend.rooms.commands import VerifiedActor
from backend.rooms.presence import remove_socket, observe_absence

if TYPE_CHECKING:
    from backend.rooms.coordinator import RoomCoordinator

SocketDelivery = Callable[[object, dict], Awaitable[None]]
SocketClose = Callable[[object, int], Awaitable[None]]
DELIVERY_ERRORS = (asyncio.TimeoutError, RuntimeError, OSError, WebSocketDisconnect)


async def deliver_socket(socket, payload: dict) -> None:
    await socket.send_json(payload)


async def close_socket(socket, code: int) -> None:
    await socket.close(code=code)


async def publish(owner: "RoomCoordinator") -> None:
    room = owner._room
    # Follow-up publication enters only after releasing the delivery lock. A
    # queued caller may already have published that revision, so coalesce again.
    while True:
        async with room.broadcast_lock:
            async with room.lock:
                if room.closed or room.published_revision == room.revision:
                    return
                room.published_revision = room.revision
                deliveries = []
                for player in room.players.values():
                    if player.sockets:
                        actor = VerifiedActor(player.token, room.owner_account_id if player.is_host else None)
                        payload = {"type": "snapshot", "state": owner.view(actor)}
                        deliveries.extend((socket, payload) for socket in player.sockets)

            async def deliver(socket, payload):
                try:
                    await asyncio.wait_for(owner._workflows.deliver(socket, payload), 1)
                except DELIVERY_ERRORS:
                    return socket
                return None

            failed = [socket for socket in await asyncio.gather(
                *(deliver(socket, payload) for socket, payload in deliveries)) if socket is not None]
            changed = False
            if failed:
                async with room.lock:
                    if not room.closed:
                        for socket in failed:
                            changed = remove_socket(owner, socket) or changed
        # Failed-delivery feedback and abandonment cannot recursively publish
        # under broadcast_lock; bounded close also holds neither room lock.
        async def close_failed(socket):
            try:
                await asyncio.wait_for(owner._workflows.close(socket, 1013), .25)
            except DELIVERY_ERRORS:
                pass
        await asyncio.gather(*(close_failed(socket) for socket in failed))
        if failed:
            changed = await observe_absence(owner) or changed
        if not changed:
            return

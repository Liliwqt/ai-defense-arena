"""Captured socket delivery at the coordinator command/view boundary."""

import asyncio
import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from backend import game_server as server
from backend.rooms.commands import PublishRoom, DefenderConnected, DefenderDisconnected, SendChat, VerifiedActor, decode_command
from backend.rooms.coordinator import RoomCoordinator, RoomWorkflows
from backend.rooms.model import Player, Room
from backend.defense_session import DefenseSession
from backend.project_files import ProjectFile
from backend.question_generator import GroundedQuestion
from backend.timed_turn import PendingSubmission


class CapturedSocket:
    def __init__(self, *, fails=False):
        self.messages = []
        self.closed = []
        self.fails = fails

    async def send_json(self, payload):
        if self.fails:
            raise OSError("Offline delivery failure")
        self.messages.append(payload)

    async def close(self, *, code):
        self.closed.append(code)


class PresenceCoordinationTests(unittest.IsolatedAsyncioTestCase):
    async def test_cancelled_initial_snapshot_removes_socket_and_reassigns(self):
        for moment in ["sending", "closing"]:
            with self.subTest(moment=moment):
                sending, never = asyncio.Event(), asyncio.Event()

                class ConnectingSocket(CapturedSocket):
                    headers = {}
                    client = SimpleNamespace(host="192.0.2.105")

                    async def accept(self):
                        pass

                    async def receive_text(self):
                        return json.dumps({"type": "hello", "token": "guest-cancel"})

                    async def send_json(self, payload):
                        if moment == "sending":
                            sending.set()
                            await never.wait()
                        raise OSError("Offline delivery failure")

                    async def close(self, *, code):
                        sending.set()
                        await never.wait()

                socket, healthy = ConnectingSocket(), CapturedSocket()
                guest = Player("guest-cancel", "Sam", 0)
                host = Player("host-cancel", "Alex", 1, True, {healthy})
                room = Room("CANCELCONNECT", [], {guest.token: guest, host.token: host}, owner_account_id="owner",
                            phase="question", selected_seat=0, answer_deadline_ms=121000)
                room.defense = DefenseSession.start(GroundedQuestion("Why?", "queue.py", 1, "queue = []"))
                coordinator = RoomCoordinator(room, RoomWorkflows(now=lambda: 1000))
                self.addAsyncCleanup(coordinator.shutdown)
                with patch.dict(server.rooms, {room.code: room}):
                    connection = asyncio.create_task(server.room_socket(socket, room.code))
                    await asyncio.wait_for(sending.wait(), 1)
                    connection.cancel()
                    with self.assertRaises(asyncio.CancelledError):
                        await connection
                state = coordinator.view(VerifiedActor(guest.token))
                self.assertFalse(next(player for player in state["players"] if player["seat"] == 0)["online"])
                self.assertEqual(state["selected_seat"], 1)
                self.assertEqual(state["answer_deadline_ms"], 121000)
                self.assertEqual(healthy.messages[-1]["state"]["revision"], state["revision"])

    async def test_concurrent_updates_are_ordered_coalesced_and_recipient_private(self):
        host_socket, guest_socket = CapturedSocket(), CapturedSocket()
        host = Player("host", "Alex", 0, True, {host_socket})
        guest = Player("guest", "Sam", 1, sockets={guest_socket})
        room = Room("ROOM", [], {host.token: host, guest.token: guest}, owner_account_id="private-owner")
        room.votes = {host.token: 1, guest.token: 0}
        room.pending_submission = PendingSubmission(0, guest.token, guest.name, 1, "private draft", 30000)
        started, release = asyncio.Event(), asyncio.Event()

        async def deliver(socket, payload):
            if payload["state"]["revision"] == 0:
                started.set()
                await release.wait()
            await socket.send_json(payload)

        coordinator = RoomCoordinator(room, RoomWorkflows(deliver=deliver, now=lambda: 1000))
        self.addAsyncCleanup(coordinator.shutdown)
        first = asyncio.create_task(coordinator.execute(PublishRoom()))
        await asyncio.wait_for(started.wait(), 1)
        chat_one = asyncio.create_task(coordinator.execute(SendChat("First"), VerifiedActor(guest.token)))
        await asyncio.sleep(0)
        chat_two = asyncio.create_task(coordinator.execute(SendChat("Second"), VerifiedActor(guest.token)))
        await asyncio.sleep(0)
        self.assertEqual(len(coordinator.view(VerifiedActor(guest.token))["chat"]), 2)
        release.set()
        await asyncio.wait_for(asyncio.gather(first, chat_one, chat_two), 2)
        for socket, expected_vote, draft in [(host_socket, 1, None), (guest_socket, 0, "private draft")]:
            states = [payload["state"] for payload in socket.messages]
            self.assertEqual([state["revision"] for state in states], [0, 2])
            self.assertEqual(len(states[-1]["chat"]), 2)
            self.assertTrue(all(state["my_vote"] == expected_vote for state in states))
            self.assertTrue(all(state["my_pending_submission"] == draft for state in states))
            self.assertNotIn("private-owner", repr(states))
            self.assertNotIn("owner_account_id", repr(states))

    async def test_partial_tab_disconnect_and_reconnect_preserve_selection_and_deadline(self):
        tab_one, tab_two, guest_socket = CapturedSocket(), CapturedSocket(), CapturedSocket()
        host = Player("host-tabs", "Alex", 0, True, {tab_one, tab_two})
        guest = Player("guest-tabs", "Sam", 1, sockets={guest_socket})
        room = Room("ROOM", [], {host.token: host, guest.token: guest}, owner_account_id="owner",
                    phase="question", selected_seat=0, answer_deadline_ms=121000)
        room.defense = DefenseSession.start(GroundedQuestion("Why?", "queue.py", 1, "queue = []"))
        coordinator = RoomCoordinator(room, RoomWorkflows(now=lambda: 1000))
        self.addAsyncCleanup(coordinator.shutdown)
        actor = VerifiedActor(host.token, "owner")
        await coordinator.execute(DefenderDisconnected(host.token, tab_one))
        self.assertEqual(coordinator.view(actor)["selected_seat"], 0)
        revision = coordinator.view(actor)["revision"]
        await coordinator.execute(DefenderDisconnected(host.token, tab_one))
        self.assertEqual(coordinator.view(actor)["revision"], revision)
        await coordinator.execute(DefenderDisconnected(host.token, tab_two))
        self.assertEqual(coordinator.view(actor)["selected_seat"], 1)
        await coordinator.execute(DefenderDisconnected(guest.token, guest_socket))
        self.assertIsNone(coordinator.view(actor)["selected_seat"])
        new_tab = CapturedSocket()
        wrong = await coordinator.execute(DefenderConnected(new_tab), VerifiedActor(host.token, "other"))
        self.assertFalse(wrong.accepted)
        self.assertEqual(new_tab.messages, [])
        missing = await coordinator.execute(DefenderConnected(new_tab), VerifiedActor("missing"))
        self.assertFalse(missing.accepted)
        self.assertTrue((await coordinator.execute(DefenderConnected(new_tab), actor)).accepted)
        state = new_tab.messages[-1]["state"]
        self.assertEqual(state["selected_seat"], 0)
        self.assertEqual(state["answer_deadline_ms"], 121000)
        self.assertEqual(state["answer_deadline_ms"] - state["server_now_ms"], 120000)

    async def test_slow_recipient_cannot_block_healthy_delivery_or_hold_room_lock(self):
        healthy, slow = CapturedSocket(), CapturedSocket()
        guest = Player("guest-slow", "Sam", 1, sockets={healthy})
        host = Player("host-slow", "Alex", 0, True, {slow})
        room = Room("ROOM", [], {host.token: host, guest.token: guest}, owner_account_id="owner")
        delivered, never = asyncio.Event(), asyncio.Event()

        async def deliver(socket, payload):
            if socket is slow:
                await never.wait()
            else:
                await socket.send_json(payload)
                delivered.set()

        coordinator = RoomCoordinator(room, RoomWorkflows(deliver=deliver, now=lambda: 1000))
        self.addAsyncCleanup(coordinator.shutdown)
        publication = asyncio.create_task(coordinator.execute(PublishRoom()))
        await asyncio.wait_for(delivered.wait(), .5)
        async with asyncio.timeout(.5):
            async with room.lock:
                self.assertTrue(host.sockets)
        await asyncio.wait_for(publication, 2)
        self.assertEqual(slow.closed, [1013])
        self.assertEqual(len(healthy.messages), 2)
        self.assertFalse(healthy.messages[-1]["state"]["players"][0]["online"])

    async def test_failed_delivery_starts_observed_absence_and_internal_commands_are_not_wire_actions(self):
        failed = CapturedSocket(fails=True)
        host = Player("host-absent", "Alex", 0, True, {failed})
        room = Room("ROOM", [], {host.token: host}, owner_account_id="owner", run_id="run",
                    phase="question", selected_seat=0, answer_deadline_ms=121000)
        room.defense = DefenseSession.start(GroundedQuestion("Why?", "queue.py", 1, "queue = []"))
        coordinator = RoomCoordinator(room, RoomWorkflows(now=lambda: 1000))
        self.addAsyncCleanup(coordinator.shutdown)
        await asyncio.wait_for(coordinator.execute(PublishRoom()), 2)
        self.assertEqual(room.absent_since_ms, 1000)
        self.assertIsNone(coordinator.view(VerifiedActor(host.token, "owner"))["selected_seat"])
        for action in ["publish_room", "observe_absence", "defender_connected", "defender_disconnected"]:
            with self.assertRaises(ValueError):
                decode_command({"type": action})

    async def test_failed_delivery_reassigns_and_republishes_without_resetting_clock(self):
        failed, healthy = CapturedSocket(fails=True), CapturedSocket()
        host, guest = Player("host", "Alex", 0, True, {failed}), Player("guest", "Sam", 1, sockets={healthy})
        room = Room("ROOM", [ProjectFile("queue.py", "queue = []")], {host.token: host, guest.token: guest},
                    owner_account_id="owner", phase="question", selected_seat=0, answer_deadline_ms=121000)
        room.defense = DefenseSession.start(GroundedQuestion("Why?", "queue.py", 1, "queue = []"))
        coordinator = RoomCoordinator(room, RoomWorkflows(now=lambda: 1000))
        self.addAsyncCleanup(coordinator.shutdown)
        await asyncio.wait_for(coordinator.execute(PublishRoom()), 2)
        self.assertEqual(failed.closed, [1013])
        self.assertEqual(len(healthy.messages), 2)
        states = [payload["state"] for payload in healthy.messages]
        self.assertEqual([state["selected_seat"] for state in states], [0, 1])
        self.assertEqual([state["answer_deadline_ms"] for state in states], [121000, 121000])
        self.assertFalse(next(player for player in states[-1]["players"] if player["seat"] == 0)["online"])
        self.assertLess(states[0]["revision"], states[1]["revision"])

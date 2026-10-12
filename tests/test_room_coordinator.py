"""Observable room command/view checks; no providers are contacted."""

import unittest

from backend.rooms.coordinator import CastVote, RoomCoordinator, RoomWorkflows, SendChat, VerifiedActor
from backend.rooms.model import Player, Room
from backend.defense_session import DefenseSession
from backend.question_generator import GroundedQuestion
from backend.timed_turn import PendingSubmission


class RoomCoordinatorTests(unittest.IsolatedAsyncioTestCase):
    async def test_wrong_owner_unknown_actor_and_shutdown_cannot_change_chat(self):
        host = Player("host", "Alex", 0, True, {object()})
        room = Room("ROOMA", [], {host.token: host}, owner_account_id="owner")
        published = []

        async def deliver(socket, payload):
            state = payload["state"]
            published.append(state)

        coordinator = RoomCoordinator(room, RoomWorkflows(deliver))
        wrong_owner = await coordinator.execute(SendChat("secret"), VerifiedActor(host.token, "other"))
        self.assertIn("account that created", wrong_owner.error)
        missing = await coordinator.execute(SendChat("secret"), VerifiedActor("missing"))
        self.assertIn("Join again", missing.error)
        with self.assertRaises(ValueError):
            coordinator.view(VerifiedActor(host.token, "other"))
        await coordinator.shutdown()
        await coordinator.shutdown()
        closed = await coordinator.execute(SendChat("secret"), VerifiedActor(host.token, "owner"))
        self.assertEqual(closed.error, "Room not found. Create a fresh room.")
        self.assertEqual(published, [])
        self.assertEqual(room.chat, [])

    async def test_votes_change_without_duplicate_publication_and_reject_late_votes(self):
        host = Player("host", "Alex", 0, True, {object()})
        guest = Player("guest", "Sam", 1, sockets={object()})
        room = Room("ROOMA", [], {host.token: host, guest.token: guest}, owner_account_id="owner")
        room.defense = DefenseSession.start(GroundedQuestion("Why?", "queue.py", 1, "value = 1"))
        room.begin_vote(1000)
        now = 1000
        published = []

        async def deliver(socket, payload):
            state = payload["state"]
            if socket in guest.sockets:
                published.append(state)

        coordinator = RoomCoordinator(room, RoomWorkflows(deliver, now=lambda: now))
        actor = VerifiedActor(guest.token)
        await coordinator.execute(CastVote(0), actor)
        await coordinator.execute(CastVote(1), actor)
        duplicate = await coordinator.execute(CastVote(1), actor)
        self.assertTrue(duplicate.accepted)
        self.assertEqual(len(published), 2)
        self.assertEqual(coordinator.view(actor)["vote_counts"], {"0": 0, "1": 1})
        now = 16_000
        late = await coordinator.execute(CastVote(0), actor)
        self.assertEqual(late.error, "Voting is not open.")
        self.assertEqual(coordinator.view(actor)["selected_seat"], 1)
        self.assertEqual(coordinator.view(actor)["answer_deadline_ms"], 136_000)

    async def test_chat_uses_server_name_and_publishes_bounded_room_history(self):
        guest = Player("guest", "Sam", 1, sockets={object()})
        room = Room("ROOMA", [], {guest.token: guest})
        published = []

        async def deliver(socket, payload):
            state = payload["state"]
            published.append(state)

        coordinator = RoomCoordinator(room, RoomWorkflows(deliver, now=lambda: 1000))
        actor = VerifiedActor(guest.token)
        rejected = await coordinator.execute(SendChat(" "), actor)
        self.assertEqual(rejected.error, "Write a team message before sending.")
        self.assertEqual(published, [])
        for number in range(101):
            result = await coordinator.execute(SendChat(f"  message {number}  "), actor)
            self.assertTrue(result.accepted)
        history = coordinator.view(actor)["chat"]
        self.assertEqual(len(history), 100)
        self.assertEqual(history[0]["id"], 2)
        self.assertEqual(history[-1], {"id": 101, "seat": 1, "name": "Sam",
                                      "text": "message 100", "sent_at_ms": 1000})
        self.assertEqual(published[-1]["chat"], history)

    async def test_views_keep_identity_and_pending_text_private(self):
        host = Player("host-token", "Alex", 0, True)
        guest = Player("guest-token", "Sam", 1)
        room = Room("ROOMA", [], {host.token: host, guest.token: guest},
                    owner_account_id="private-account")
        coordinator = RoomCoordinator(room)
        room.pending_submission = PendingSubmission(0, guest.token, guest.name, 1,
                                                    "private draft", 30_000)
        room.votes = {host.token: 1, guest.token: 0}
        host_view = coordinator.view(VerifiedActor(host.token, "private-account"))
        guest_view = coordinator.view(VerifiedActor(guest.token))
        self.assertEqual(host_view["self_seat"], 0)
        self.assertEqual(host_view["my_vote"], 1)
        self.assertIsNone(host_view["my_pending_submission"])
        self.assertEqual(guest_view["my_pending_submission"], "private draft")
        self.assertEqual(guest_view["my_vote"], 0)
        self.assertNotIn("private-account", str(host_view))
        self.assertNotIn("guest-token", str(host_view))

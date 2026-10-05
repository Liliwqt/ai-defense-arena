from offline_accounts import authenticate
"""Fake-clock checks for room-owned voting, answer deadlines, and private chat."""

import asyncio
import unittest
from unittest.mock import patch

import game_server as server
from defense_session import DefenseSession
from question_generator import GroundedQuestion, PanelMove


class FakeSocket:
    def __init__(self):
        self.messages = []

    async def send_json(self, payload):
        self.messages.append(payload)


class TimedRoomTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        authenticate(self, unit_server=server)
        self.now = 1_000_000
        self.clock_patch = patch.object(server, "_now_ms", side_effect=lambda: self.now)
        self.clock_patch.start()
        self.addCleanup(self.clock_patch.stop)
        self.host_socket = FakeSocket()
        self.guest_socket = FakeSocket()
        self.host = server.Player("host", "Alex", 0, True, {self.host_socket})
        self.guest = server.Player("guest", "Sam", 1, False, {self.guest_socket})
        self.room = server.Room("ROOMA", [], {"host": self.host, "guest": self.guest})
        self.room.defense = DefenseSession.start(GroundedQuestion("Why?", "queue.py", 1, "value = 1"))
        self.room.phase = "voting"
        self.room.vote_deadline_ms = self.now + server.VOTE_MS
        self.generated = []
        self.generation_patch = patch.object(server, "_schedule_generation", side_effect=lambda *args: self.generated.append(args))
        self.generation_patch.start()
        self.addCleanup(self.generation_patch.stop)

    async def asyncTearDown(self):
        if self.room.clock_task:
            self.room.clock_task.cancel()
            await asyncio.gather(self.room.clock_task, return_exceptions=True)

    async def action(self, player, socket, **message):
        await server._handle_action(self.room, player, socket, message)

    def last_error(self, socket):
        return next((event["message"] for event in reversed(socket.messages)
                     if event["type"] == "error"), None)

    async def test_changed_votes_and_reconnect_snapshot(self):
        await self.action(self.host, self.host_socket, type="cast_vote", seat=0)
        await self.action(self.guest, self.guest_socket, type="cast_vote", seat=1)
        await self.action(self.host, self.host_socket, type="cast_vote", seat=1)
        self.assertEqual(self.room.snapshot(self.host)["vote_counts"], {"0": 0, "1": 2})
        self.assertEqual(self.room.snapshot(self.host)["my_vote"], 1)
        self.assertEqual(self.room.snapshot(self.guest)["my_vote"], 1)
        self.assertGreater(self.room.snapshot(self.guest)["vote_deadline_ms"] - self.now, 0)
        self.now += server.VOTE_MS
        await server._expire_deadline(self.room)
        self.assertEqual(self.room.phase, "question")
        self.assertEqual(self.room.selected_seat, 1)
        self.assertEqual(self.room.answer_deadline_ms, self.now + server.ANSWER_MS)
        self.assertEqual(self.room.snapshot(self.guest)["selected_seat"], 1)
        self.assertEqual(self.room.snapshot(self.guest)["vote_counts"], {"0": 0, "1": 0})
        await self.action(self.host, self.host_socket, type="cast_vote", seat=0)
        self.assertIn("Voting is not open", self.last_error(self.host_socket))

    async def test_random_tie_and_no_vote_choose_online_defender(self):
        with patch.object(server.secrets, "choice", return_value=1) as choose:
            await self.action(self.host, self.host_socket, type="cast_vote", seat=0)
            await self.action(self.guest, self.guest_socket, type="cast_vote", seat=1)
            self.now += server.VOTE_MS
            await server._expire_deadline(self.room)
            self.assertEqual(choose.call_args.args[0], [0, 1])
            self.assertEqual(self.room.selected_seat, 1)
        server._clear_clock_locked(self.room)
        self.room.phase = "voting"
        self.room.vote_deadline_ms = self.now + server.VOTE_MS
        with patch.object(server.secrets, "choice", return_value=0) as choose:
            self.now += server.VOTE_MS
            await server._expire_deadline(self.room)
            self.assertEqual(choose.call_args.args[0], [0, 1])
            self.assertEqual(self.room.selected_seat, 0)

    async def test_answer_authority_late_rejection_and_timeout_progression(self):
        self.room.phase = "question"
        self.room.vote_deadline_ms = None
        self.room.answer_deadline_ms = self.now + server.ANSWER_MS
        server._set_selected_locked(self.room, 1)
        await self.action(self.host, self.host_socket, type="submit_answer", turn=0, answer="wrong seat")
        self.assertIn("chosen defender", self.last_error(self.host_socket))
        self.assertIsNone(self.room.defense.turns[0].answer)
        self.now += server.ANSWER_MS
        await self.action(self.guest, self.guest_socket, type="submit_answer", turn=0, answer="too late")
        self.assertTrue(self.room.defense.turns[0].timed_out)
        self.assertIsNone(self.room.defense.turns[0].answer)
        self.assertEqual(self.room.phase, "generating")
        self.assertEqual(len(self.generated), 1)
        history = self.room.defense.answered_history()
        self.assertEqual(len(history), 1)
        self.assertTrue(history[0].timed_out)
        self.assertIsNone(history[0].answer)
        self.assertIn("There is no question", self.last_error(self.guest_socket))

    async def test_disconnect_reassigns_without_resetting_answer_clock(self):
        self.room.phase = "question"
        self.room.vote_deadline_ms = None
        self.room.answer_deadline_ms = self.now + server.ANSWER_MS
        server._set_selected_locked(self.room, 1)
        self.guest.sockets.clear()
        self.assertTrue(server._reassign_if_offline_locked(self.room))
        self.assertEqual(self.room.selected_seat, 0)
        self.assertEqual(self.room.answer_deadline_ms, self.now + server.ANSWER_MS)
        self.host.sockets.clear()
        self.assertTrue(server._reassign_if_offline_locked(self.room))
        self.assertIsNone(self.room.selected_seat)
        self.guest.sockets.add(self.guest_socket)
        self.assertTrue(server._reassign_if_offline_locked(self.room))
        self.assertEqual(self.room.selected_seat, 1)
        self.assertEqual(self.room.answer_deadline_ms, self.now + server.ANSWER_MS)

    async def test_retry_after_timed_out_turn_preserves_it_and_excludes_chat(self):
        self.room.phase = "question"
        self.room.vote_deadline_ms = None
        self.room.answer_deadline_ms = self.now + server.ANSWER_MS
        server._set_selected_locked(self.room, 0)
        await self.action(self.host, self.host_socket, type="send_chat", text="private strategy")
        self.now += server.ANSWER_MS
        await server._expire_deadline(self.room)
        self.assertTrue(self.room.defense.turns[0].timed_out)
        generation_id = self.room.generation_id
        with patch.object(server, "generate_next_move", side_effect=RuntimeError("mock AI failure")):
            await server._generate_question(self.room, generation_id, False)
        self.assertEqual(self.room.phase, "retry")
        self.assertTrue(self.room.defense.turns[0].timed_out)
        await self.action(self.guest, self.guest_socket, type="retry")
        self.assertIn("Only the host", self.last_error(self.guest_socket))
        await self.action(self.host, self.host_socket, type="retry")
        self.assertEqual(self.room.phase, "generating")
        self.assertEqual(len(self.generated), 2)
        followup = GroundedQuestion("Why is this still open?", "queue.py", 1, "value = 1")
        def next_move(*args, **kwargs):
            self.assertEqual(len(kwargs["history"]), 1)
            self.assertTrue(kwargs["history"][0].timed_out)
            self.assertIsNone(kwargs["history"][0].answer)
            self.assertNotIn("private strategy", repr(kwargs["history"]))
            return PanelMove(server.PANELIST_ORDER[0], followup)
        with patch.object(server, "generate_next_move", side_effect=next_move):
            await server._generate_question(self.room, self.room.generation_id, False)
        self.assertEqual(self.room.phase, "voting", self.room.error)
        self.assertEqual(len(self.room.defense.turns), 2)
        self.assertTrue(self.room.defense.turns[0].timed_out)
        self.assertEqual(self.room.chat[0]["text"], "private strategy")

    async def test_vote_rejects_offline_candidate_and_late_action(self):
        self.guest.sockets.clear()
        await self.action(self.host, self.host_socket, type="cast_vote", seat=1)
        self.assertIn("online defender", self.last_error(self.host_socket))
        self.now = self.room.vote_deadline_ms
        await self.action(self.host, self.host_socket, type="cast_vote", seat=0)
        self.assertEqual(self.room.phase, "question")
        self.assertIn("Voting is not open", self.last_error(self.host_socket))

    async def test_chat_validation_room_isolation_history_and_restart(self):
        other_socket = FakeSocket()
        other_room = server.Room("ROOMB", [], {"other": server.Player("other", "Lee", 0, True, {other_socket})})
        await self.action(self.host, self.host_socket, type="send_chat", text="  private note  ")
        self.assertEqual(self.room.snapshot(self.guest)["chat"][0]["text"], "private note")
        self.assertEqual(other_room.snapshot()["chat"], [])
        self.assertEqual(other_socket.messages, [])
        await self.action(self.guest, self.guest_socket, type="send_chat", text=" ")
        self.assertIn("Write a team message", self.last_error(self.guest_socket))
        await self.action(self.guest, self.guest_socket, type="send_chat", text="x" * 501)
        self.assertIn("500 characters", self.last_error(self.guest_socket))
        for index in range(105):
            await self.action(self.host, self.host_socket, type="send_chat", text=f"note {index}")
        self.assertEqual(len(self.room.chat), 100)
        self.assertEqual(self.room.chat[-1]["text"], "note 104")
        with patch.object(server, "_schedule_generation"):
            await self.action(self.host, self.host_socket, type="restart")
        self.assertEqual(self.room.chat, [])
        self.assertEqual(self.room.votes, {})
        self.assertIsNone(self.room.vote_deadline_ms)
        self.assertIsNone(self.room.answer_deadline_ms)


if __name__ == "__main__":
    unittest.main()

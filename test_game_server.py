"""Offline multiplayer room checks; all AI calls are mocked."""

import os
from pathlib import Path
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from openai import OpenAIError

import game_server
from question_generator import CoachingReport, GroundedQuestion, PanelMove


class GameServerTests(unittest.TestCase):
    def setUp(self):
        game_server.rooms.clear()
        self.client = TestClient(game_server.app)
        self.client.__enter__()
        self.addCleanup(lambda: self.client.__exit__(None, None, None))
        self.files = [
            ("files", ("README.md", Path("sample_project/README.md").read_bytes(), "text/markdown")),
            ("files", ("queue.py", Path("sample_project/queue.py").read_bytes(), "text/x-python")),
        ]
        code_lines = Path("sample_project/queue.py").read_text().splitlines()
        self.questions = [
            GroundedQuestion(text, "queue.py", line, code_lines[line - 1])
            for text, line in [
                ("Why use SQLite?", 5),
                ("How would you protect reservation names?", 8),
                ("How would concurrent requests affect that choice?", 9),
                ("How would you restrict access to this result?", 33),
            ]
        ]
        self.short_moves = [
            PanelMove(role, question)
            for role, question in zip(game_server.PANELIST_ORDER[1:], self.questions[1:])
        ] + [PanelMove(None, None)]

    def create_room(self):
        response = self.client.post(
            "/api/rooms",
            data={"host_name": "Alex", "host_passcode": "offline-passcode"},
            files=self.files,
        )
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def join_room(self, code, name="Sam"):
        response = self.client.post(f"/api/rooms/{code}/join", json={"name": name})
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def receive_phase(self, socket, phase):
        for _ in range(8):
            event = socket.receive_json()
            if event["type"] == "snapshot" and event["state"]["phase"] == phase:
                return event["state"]
        self.fail(f"Never received phase {phase}")

    def connect(self, code, token):
        socket = self.client.websocket_connect(f"/ws/{code}")
        socket.__enter__()
        socket.send_json({"type": "hello", "token": token})
        first = socket.receive_json()
        self.assertEqual(first["type"], "snapshot")
        return socket, first["state"]

    def test_creation_requires_host_passcode_and_upload_validation(self):
        with patch.dict(os.environ, {"GAME_HOST_PASSCODE": "offline-passcode"}):
            denied = self.client.post(
                "/api/rooms",
                data={"host_name": "Alex", "host_passcode": "wrong"},
                files=self.files,
            )
            self.assertEqual(denied.status_code, 403)
            self.assertFalse(game_server.rooms)
            invalid = self.client.post(
                "/api/rooms",
                data={"host_name": "Alex", "host_passcode": "offline-passcode"},
                files=[("files", ("secret.env", b"PRIVATE=1", "text/plain"))],
            )
            self.assertEqual(invalid.status_code, 422)
            self.assertFalse(game_server.rooms)
            host = self.create_room()
            self.assertEqual(len(game_server.rooms[host["room_code"]].files), 2)
            for name in ("Sam", "Lee", "Kai"):
                self.join_room(host["room_code"], name)
            full = self.client.post(f"/api/rooms/{host['room_code']}/join", json={"name": "Fifth"})
            self.assertEqual(full.status_code, 409)

    def test_websocket_requires_a_valid_room_token(self):
        with self.client.websocket_connect("/ws/UNKNOWN") as socket:
            socket.send_json({"type": "hello", "token": "invalid"})
            self.assertIn("Room not found", socket.receive_json()["message"])
        with patch.dict(os.environ, {"GAME_HOST_PASSCODE": "offline-passcode"}):
            host = self.create_room()
        with self.client.websocket_connect(f"/ws/{host['room_code']}") as socket:
            socket.send_json({"type": "hello", "token": "invalid"})
            self.assertIn("no longer valid", socket.receive_json()["message"])

    def test_two_clients_share_four_turns_and_first_answer_wins(self):
        with (
            patch.dict(os.environ, {"GAME_HOST_PASSCODE": "offline-passcode", "OPENAI_API_KEY": "test-key"}),
            patch("game_server.generate_first_question", return_value=self.questions[0]) as first_call,
            patch("game_server.generate_next_move", side_effect=self.short_moves) as later_calls,
        ):
            host = self.create_room()
            guest = self.join_room(host["room_code"])
            host_socket, host_initial = self.connect(host["room_code"], host["player_token"])
            try:
                self.assertTrue(host_initial["self_is_host"])
                self.assertEqual(host_initial["self_seat"], 0)
                guest_socket, guest_initial = self.connect(guest["room_code"], guest["player_token"])
                try:
                    self.assertFalse(guest_initial["self_is_host"])
                    self.assertEqual(guest_initial["self_seat"], 1)
                    guest_socket.send_json({"type": "start"})
                    self.assertIn("Only the host", guest_socket.receive_json()["message"])
                    host_socket.send_json({"type": "start"})
                    for socket in (host_socket, guest_socket):
                        state = self.receive_phase(socket, "question")
                        self.assertEqual(state["turns"][0]["evidence_text"], self.questions[0].evidence_text)
                    self.assertEqual(first_call.call_count, 1)

                    guest_socket.send_json({"type": "submit_answer", "turn": 0, "answer": "A simple prototype."})
                    for socket in (host_socket, guest_socket):
                        state = self.receive_phase(socket, "question")
                        self.assertEqual(len(state["turns"]), 2)
                        self.assertEqual(state["turns"][0]["answer"], "A simple prototype.")
                        self.assertEqual(state["turns"][0]["answered_by"], "Sam")
                    host_socket.send_json({"type": "submit_answer", "turn": 0, "answer": "Too late."})
                    self.assertIn("already been answered", host_socket.receive_json()["message"])

                    for turn, socket, answer in (
                        (1, host_socket, "Add sign-in."),
                        (2, guest_socket, "Queue database writes."),
                        (3, host_socket, "Check access before returning names."),
                    ):
                        socket.send_json({"type": "submit_answer", "turn": turn, "answer": answer})
                        phase = "complete" if turn == 3 else "question"
                        for observer in (host_socket, guest_socket):
                            state = self.receive_phase(observer, phase)
                            self.assertEqual(state["turns"][turn]["answer"], answer)
                    self.assertEqual(len(state["turns"]), 4)
                    self.assertEqual(later_calls.call_count, 4)
                    self.assertEqual([turn["panelist"] for turn in state["turns"]], list(game_server.PANELIST_ORDER))
                finally:
                    guest_socket.__exit__(None, None, None)
            finally:
                host_socket.__exit__(None, None, None)

    def test_eight_turn_defense_allows_one_followup_per_role_then_coaches(self):
        lines = Path("sample_project/queue.py").read_text().splitlines()
        role_sequence = [role for role in game_server.PANELIST_ORDER for _ in range(2)]
        questions = [GroundedQuestion(f"Question {i + 1}?", "queue.py", line, lines[line - 1])
                     for i, line in enumerate((5, 8, 9, 33, 5, 8, 9, 33))]
        moves = [PanelMove(role, question) for role, question in zip(role_sequence[1:], questions[1:])]
        report = CoachingReport("Eight answers reviewed.",
                                [{"turn": 7, "text": "Strong final answer."}],
                                [{"turn": 0, "text": "Clarify the first answer."}],
                                "Review both tradeoffs.")
        with (
            patch.dict(os.environ, {"GAME_HOST_PASSCODE": "offline-passcode", "OPENAI_API_KEY": "test-key"}),
            patch("game_server.generate_first_question", return_value=questions[0]),
            patch("game_server.generate_next_move", side_effect=moves) as next_call,
            patch("game_server.generate_coaching_report", return_value=report) as coaching_call,
        ):
            host = self.create_room()
            guest = self.join_room(host["room_code"])
            host_socket, _ = self.connect(host["room_code"], host["player_token"])
            try:
                guest_socket, _ = self.connect(guest["room_code"], guest["player_token"])
                try:
                    host_socket.send_json({"type": "start"})
                    for socket in (host_socket, guest_socket):
                        self.receive_phase(socket, "question")
                    for index in range(8):
                        sender = guest_socket if index % 2 == 0 else host_socket
                        sender.send_json({"type": "submit_answer", "turn": index,
                                          "answer": f"Answer {index + 1}"})
                        for socket in (host_socket, guest_socket):
                            state = self.receive_phase(socket, "complete" if index == 7 else "question")
                            self.assertEqual(state["turns"][index]["answer"], f"Answer {index + 1}")
                    self.assertEqual([turn["panelist"] for turn in state["turns"]], role_sequence)
                    self.assertEqual(len(state["turns"]), 8)
                    self.assertEqual(next_call.call_count, 7)
                    self.assertEqual(coaching_call.call_count, 1)
                finally:
                    guest_socket.__exit__(None, None, None)
            finally:
                host_socket.__exit__(None, None, None)

    def test_failure_retains_answer_then_host_retries_and_guest_reconnects(self):
        with (
            patch.dict(os.environ, {"GAME_HOST_PASSCODE": "offline-passcode", "OPENAI_API_KEY": "test-key"}),
            patch("game_server.generate_first_question", return_value=self.questions[0]),
            patch("game_server.generate_next_move", side_effect=[OpenAIError("temporary outage"), self.short_moves[0]]),
        ):
            host = self.create_room()
            guest = self.join_room(host["room_code"])
            host_socket, _ = self.connect(host["room_code"], host["player_token"])
            try:
                guest_socket, _ = self.connect(guest["room_code"], guest["player_token"])
                host_socket.send_json({"type": "start"})
                self.receive_phase(host_socket, "question")
                self.receive_phase(guest_socket, "question")
                guest_socket.send_json({"type": "submit_answer", "turn": 0, "answer": "Keep the answer."})
                for socket in (host_socket, guest_socket):
                    state = self.receive_phase(socket, "retry")
                    self.assertEqual(state["turns"][0]["answer"], "Keep the answer.")
                    self.assertEqual(len(state["turns"]), 1)
                guest_socket.__exit__(None, None, None)
                self.receive_phase(host_socket, "retry")  # Guest is now offline.
                guest_socket, joined_state = self.connect(guest["room_code"], guest["player_token"])
                try:
                    self.assertEqual(joined_state["turns"][0]["answer"], "Keep the answer.")
                    guest_socket.send_json({"type": "retry"})
                    self.assertIn("Only the host", guest_socket.receive_json()["message"])
                    host_socket.send_json({"type": "retry"})
                    for socket in (host_socket, guest_socket):
                        state = self.receive_phase(socket, "question")
                        self.assertEqual(len(state["turns"]), 2)
                        self.assertEqual(state["turns"][0]["answer"], "Keep the answer.")
                finally:
                    guest_socket.__exit__(None, None, None)
            finally:
                host_socket.__exit__(None, None, None)


    def _complete_four_turns(self, host_socket, guest_socket, mock_coaching):
        """Drive four question/answer turns and return the complete state for both sockets."""
        host_socket.send_json({"type": "start"})
        for socket in (host_socket, guest_socket):
            self.receive_phase(socket, "question")
        for turn, socket, answer in (
            (0, guest_socket, "SQLite keeps it simple."),
            (1, host_socket, "Parameterised queries."),
            (2, guest_socket, "Single writer is fine."),
            (3, host_socket, "Check access before returning."),
        ):
            socket.send_json({"type": "submit_answer", "turn": turn, "answer": answer})
            expected = "complete" if turn == 3 else "question"
            for observer in (host_socket, guest_socket):
                self.receive_phase(observer, expected)
        # Coaching arrives asynchronously; wait for it.
        states = {}
        for socket, label in ((host_socket, "host"), (guest_socket, "guest")):
            state = self.receive_phase(socket, "complete")
            while state.get("feedback_status") == "generating":
                state = self.receive_phase(socket, "complete")
            states[label] = state
        return states

    def test_coaching_report_is_sent_after_fourth_answer(self):
        mock_report = CoachingReport(
            summary="Solid defense.",
            strengths=[{"turn": 0, "text": "Good SQLite rationale."}],
            improvements=[{"turn": 1, "text": "Elaborate on validation."}],
            next_step="Practice edge cases.",
        )
        with (
            patch.dict(os.environ, {"GAME_HOST_PASSCODE": "offline-passcode", "OPENAI_API_KEY": "test-key"}),
            patch("game_server.generate_first_question", return_value=self.questions[0]),
            patch("game_server.generate_next_move", side_effect=self.short_moves),
            patch("game_server.generate_coaching_report", return_value=mock_report) as coaching_call,
        ):
            host = self.create_room()
            guest = self.join_room(host["room_code"])
            host_socket, _ = self.connect(host["room_code"], host["player_token"])
            try:
                guest_socket, _ = self.connect(guest["room_code"], guest["player_token"])
                try:
                    states = self._complete_four_turns(host_socket, guest_socket, mock_report)
                    for label, state in states.items():
                        self.assertEqual(state["feedback_status"], "ready", f"{label} should have ready feedback")
                        fb = state["feedback"]
                        self.assertEqual(fb["summary"], "Solid defense.")
                        self.assertEqual(fb["strengths"], [{"turn": 0, "text": "Good SQLite rationale."}])
                        self.assertEqual(fb["improvements"], [{"turn": 1, "text": "Elaborate on validation."}])
                        self.assertEqual(fb["next_step"], "Practice edge cases.")
                    self.assertEqual(coaching_call.call_count, 1)
                finally:
                    guest_socket.__exit__(None, None, None)
            finally:
                host_socket.__exit__(None, None, None)

    def test_coaching_failure_host_can_retry_once(self):
        mock_report = CoachingReport(
            summary="Good session.",
            strengths=[{"turn": 2, "text": "Addressed concurrency."}],
            improvements=[{"turn": 3, "text": "Be more specific about access control."}],
            next_step="Run load tests.",
        )
        with (
            patch.dict(os.environ, {"GAME_HOST_PASSCODE": "offline-passcode", "OPENAI_API_KEY": "test-key"}),
            patch("game_server.generate_first_question", return_value=self.questions[0]),
            patch("game_server.generate_next_move", side_effect=self.short_moves),
            patch("game_server.generate_coaching_report",
                  side_effect=[OpenAIError("coaching timeout"), mock_report]) as coaching_call,
        ):
            host = self.create_room()
            guest = self.join_room(host["room_code"])
            host_socket, _ = self.connect(host["room_code"], host["player_token"])
            try:
                guest_socket, _ = self.connect(guest["room_code"], guest["player_token"])
                try:
                    host_socket.send_json({"type": "start"})
                    for socket in (host_socket, guest_socket):
                        self.receive_phase(socket, "question")
                    for turn, socket, answer in (
                        (0, guest_socket, "SQLite keeps it simple."),
                        (1, host_socket, "Parameterised queries."),
                        (2, guest_socket, "Single writer is fine."),
                        (3, host_socket, "Check access before returning."),
                    ):
                        socket.send_json({"type": "submit_answer", "turn": turn, "answer": answer})
                        expected = "complete" if turn == 3 else "question"
                        for observer in (host_socket, guest_socket):
                            self.receive_phase(observer, expected)
                    # Wait for coaching failure.
                    for socket in (host_socket, guest_socket):
                        state = self.receive_phase(socket, "complete")
                        while state.get("feedback_status") == "generating":
                            state = self.receive_phase(socket, "complete")
                        self.assertEqual(state["feedback_status"], "failed")
                        self.assertIsNone(state["feedback"])
                        self.assertIsNotNone(state["error"])
                        # All four answers preserved.
                        self.assertEqual(len([t for t in state["turns"] if t["answer"]]), 4)
                    # Guest cannot retry coaching.
                    guest_socket.send_json({"type": "retry_coaching"})
                    self.assertIn("Only the host", guest_socket.receive_json()["message"])
                    # Host retries.
                    host_socket.send_json({"type": "retry_coaching"})
                    for socket in (host_socket, guest_socket):
                        state = self.receive_phase(socket, "complete")
                        while state.get("feedback_status") == "generating":
                            state = self.receive_phase(socket, "complete")
                        self.assertEqual(state["feedback_status"], "ready")
                        self.assertEqual(state["feedback"]["summary"], "Good session.")
                    self.assertEqual(coaching_call.call_count, 2)
                finally:
                    guest_socket.__exit__(None, None, None)
            finally:
                host_socket.__exit__(None, None, None)

    def test_restart_clears_coaching_and_only_one_coaching_call_per_defense(self):
        mock_report = CoachingReport(
            summary="Good first run.",
            strengths=[{"turn": 0, "text": "Clear."}],
            improvements=[{"turn": 1, "text": "Go deeper."}],
            next_step="Rehearse once more.",
        )
        with (
            patch.dict(os.environ, {"GAME_HOST_PASSCODE": "offline-passcode", "OPENAI_API_KEY": "test-key"}),
            patch("game_server.generate_first_question", return_value=self.questions[0]),
            patch("game_server.generate_next_move", side_effect=self.short_moves * 2),
            patch("game_server.generate_coaching_report", return_value=mock_report) as coaching_call,
        ):
            host = self.create_room()
            host_socket, _ = self.connect(host["room_code"], host["player_token"])
            try:
                guest = self.join_room(host["room_code"])
                guest_socket, _ = self.connect(guest["room_code"], guest["player_token"])
                try:
                    states = self._complete_four_turns(host_socket, guest_socket, mock_report)
                    self.assertEqual(states["host"]["feedback_status"], "ready")
                    self.assertEqual(coaching_call.call_count, 1)
                    # Host restarts — coaching must be cleared.
                    host_socket.send_json({"type": "restart"})
                    for socket in (host_socket, guest_socket):
                        state = self.receive_phase(socket, "generating")
                        self.assertEqual(state["feedback_status"], "none")
                        self.assertIsNone(state["feedback"])
                    # Stale coaching result must not arrive after restart.
                    # Complete a second defense.
                    states2 = self._complete_four_turns(host_socket, guest_socket, mock_report)
                    self.assertEqual(states2["host"]["feedback_status"], "ready")
                    # Exactly one coaching call per completed defense (2 total).
                    self.assertEqual(coaching_call.call_count, 2)
                finally:
                    guest_socket.__exit__(None, None, None)
            finally:
                host_socket.__exit__(None, None, None)

    def test_reconnecting_client_receives_coaching_report(self):
        mock_report = CoachingReport(
            summary="Reconnect check.",
            strengths=[{"turn": 3, "text": "Strong finish."}],
            improvements=[{"turn": 0, "text": "Start with more context."}],
            next_step="Review sources.",
        )
        with (
            patch.dict(os.environ, {"GAME_HOST_PASSCODE": "offline-passcode", "OPENAI_API_KEY": "test-key"}),
            patch("game_server.generate_first_question", return_value=self.questions[0]),
            patch("game_server.generate_next_move", side_effect=self.short_moves),
            patch("game_server.generate_coaching_report", return_value=mock_report),
        ):
            host = self.create_room()
            guest = self.join_room(host["room_code"])
            host_socket, _ = self.connect(host["room_code"], host["player_token"])
            try:
                guest_socket, _ = self.connect(guest["room_code"], guest["player_token"])
                try:
                    states = self._complete_four_turns(host_socket, guest_socket, mock_report)
                    self.assertEqual(states["guest"]["feedback_status"], "ready")
                finally:
                    guest_socket.__exit__(None, None, None)
                # Guest reconnects and must immediately receive the coaching report.
                guest_socket2, rejoined_state = self.connect(guest["room_code"], guest["player_token"])
                try:
                    self.assertEqual(rejoined_state["feedback_status"], "ready")
                    self.assertEqual(rejoined_state["feedback"]["summary"], "Reconnect check.")
                finally:
                    guest_socket2.__exit__(None, None, None)
            finally:
                host_socket.__exit__(None, None, None)


if __name__ == "__main__":
    unittest.main()

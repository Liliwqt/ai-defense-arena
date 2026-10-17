"""Authenticated room openings with AI mocked and a controlled room clock."""

from dataclasses import replace
import threading
import unittest
from unittest.mock import patch

from backend import game_server
from backend.opening_history import paper_key, recent_openings
from backend.question_generator import ResearchMove, GroundedQuestion, RESEARCH_PANELISTS
from backend.rooms import planning, questions
from backend.research_plan import ResearchPlan
from tests import test_research_coverage as coverage
from tests.research_profile_fixtures import research_profile


class OpeningHistoryProtocolTests(unittest.TestCase):
    setUp = coverage.CoverageProtocolTests.setUp
    def until(self, socket, phase=None, *, allow_retry=False, **conditions):
        for _ in range(40):
            event = socket.receive_json()
            self.assertNotEqual(event["type"], "error", event)
            state = event["state"]
            if phase != "retry" and not allow_retry:
                self.assertNotEqual(state["phase"], "retry", state.get("error"))
            if (phase is None or state["phase"] == phase) and all(state.get(k) == v for k, v in conditions.items()):
                return state
        self.fail("Expected room snapshot was not published.")

    def start_opening(self, generate, *, filename="paper.md", expected="voting", during_history=None, on_state=None, paper=coverage.PAPER):
        response = self.client.post("/api/rooms", data={"host_name": "Host", "defense_type": "research"},
                                    files=[("research_files", (filename, paper.encode(), "text/markdown"))])
        self.assertEqual(response.status_code, 201, response.text)
        host = response.json()
        self.latest_host = host
        topics = tuple(replace(topic, references=tuple(replace(ref, filename=filename) for ref in topic.references))
                       for topic in coverage.plan(4).topics)
        plan = ResearchPlan(topics, profile=research_profile(topics[0].references[0]))
        with patch.object(planning, "generate_research_plan", return_value=plan), \
             patch.object(questions, "generate_research_move", side_effect=generate), \
             self.client.websocket_connect(f"/ws/{host['room_code']}") as socket:
            socket.send_json({"type": "hello", "token": host["player_token"]})
            self.until(socket, "lobby")
            socket.send_json({"type": "prepare_research_plan"})
            self.until(socket, research_planning_status="ready")
            socket.send_json({"type": "approve_research_plan", "plan_id": plan.id,
                              "question_budget": 4, "confirm_profile": True})
            self.until(socket, research_plan_approved=True)
            socket.send_json({"type": "start", "plan_id": plan.id, "question_budget": 4})
            if during_history:
                during_history(socket)
            state = self.until(socket, expected)
            if on_state:
                on_state(socket, state)
            return state

    @staticmethod
    def move(files, question):
        return ResearchMove(RESEARCH_PANELISTS[0], GroundedQuestion(question, files[0].name, 1,
            files[0].content.splitlines()[0], evidence_kind="research_text"), "topic-1", False, None)

    def test_fresh_rooms_and_renamed_paper_receive_private_committed_opening_context(self):
        seen = []
        def generate(files, key, *, context, **kwargs):
            seen.append(context)
            return self.move(files, "Why this campus?" if len(seen) == 1 else "How will the pilot be evaluated?")
        first = self.start_opening(generate)
        self.assertEqual(first["turns"][0]["question"], "Why this campus?")
        history = recent_openings(self._offline_credentials[2]["id"], paper_key(coverage.FILES))
        self.assertEqual([entry["question"] for entry in history], ["Why this campus?"])
        second = self.start_opening(generate, filename="renamed.md")
        self.assertEqual(second["turns"][0]["question"], "How will the pilot be evaluated?")
        self.assertEqual(seen[0]["recent_openings"], [])
        self.assertEqual([entry["question"] for entry in seen[1]["recent_openings"]], ["Why this campus?"])
        self.assertNotIn("recent_openings", second)

    def test_repeated_candidate_regenerates_once_and_never_becomes_active(self):
        self.start_opening(lambda files, *args, **kwargs: self.move(files, "Why this campus?"))
        attempts = []
        def repeated(files, *args, **kwargs):
            attempts.append(kwargs["context"])
            return self.move(files, "WHY this campus!!!")
        state = self.start_opening(repeated, expected="retry")
        self.assertEqual(len(attempts), 2)
        self.assertEqual(state["turns"], [])
        self.assertIn("recent opening", state["error"])
        self.assertEqual(len(recent_openings(self._offline_credentials[2]["id"], paper_key(coverage.FILES))), 1)

    def test_duplicate_can_recover_to_a_fresh_cited_angle(self):
        self.start_opening(lambda files, *args, **kwargs: self.move(files, "Why this campus?"))
        choices = iter(("Why this campus?", "How will the pilot be evaluated?"))
        state = self.start_opening(lambda files, *args, **kwargs: self.move(files, next(choices)))
        self.assertEqual(state["turns"][0]["question"], "How will the pilot be evaluated?")
        self.assertEqual(len(recent_openings(self._offline_credentials[2]["id"], paper_key(coverage.FILES))), 2)

    def test_unavailable_history_stops_before_ai_or_commit_without_disclosing_details(self):
        with patch.object(questions, "recent_openings", side_effect=RuntimeError("private-database-details")):
            state = self.start_opening(lambda *args, **kwargs: self.fail("AI must not run without required history"), expected="retry")
        self.assertEqual(state["turns"], [])
        self.assertIn("history could not be checked", state["error"])
        self.assertNotIn("private-database-details", state["error"])

    def test_slow_history_storage_does_not_block_room_chat(self):
        entered, release, timed_out = threading.Event(), threading.Event(), threading.Event()
        def slow_history(*args, **kwargs):
            entered.set()
            if not release.wait(5):
                timed_out.set()
            return []
        def use_room(socket):
            try:
                self.assertTrue(entered.wait(2))
                socket.send_json({"type": "send_chat", "text": "We can still coordinate."})
                for _ in range(10):
                    event = socket.receive_json()
                    if any(item["text"] == "We can still coordinate." for item in event.get("state", {}).get("chat", [])):
                        break
                else:
                    self.fail("Room chat did not progress while history was loading.")
                self.assertFalse(timed_out.is_set(), "The history read blocked the room event loop.")
            finally:
                release.set()
        with patch.object(questions, "recent_openings", side_effect=slow_history):
            state = self.start_opening(lambda files, *args, **kwargs: self.move(files, "Why this campus?"), during_history=use_room)
        self.assertEqual(state["turns"][0]["question"], "Why this campus?")

    def test_host_can_accept_current_repeat_while_guest_waits_and_replay_is_rejected(self):
        self.start_opening(lambda files, *args, **kwargs: self.move(files, "Why this campus?"))
        def choose(socket, state):
            self.assertTrue(state.get("opening_repeated"))
            socket.send_json({"type": "approve_research_plan", "plan_id": "obsolete-map", "question_budget": 4, "confirm_profile": True})
            self.assertEqual(socket.receive_json()["type"], "error")
            socket.send_json({"type": "prepare_research_plan"})
            self.assertEqual(socket.receive_json()["type"], "error")
            choice = state["opening_candidate"]
            self.assertEqual(choice["question"], "Why this campus?")
            self.assertEqual(state["turns"], [])
            self.assertIsNone(state["vote_deadline_ms"])
            guest = self.client.post(f"/api/rooms/{state['room_code']}/join", json={"name": "Guest"}).json()
            with self.client.websocket_connect(f"/ws/{state['room_code']}") as second:
                second.send_json({"type": "hello", "token": guest["player_token"]})
                waiting = self.until(second, "retry")
                self.assertTrue(waiting["opening_repeated"])
                self.assertIsNone(waiting.get("opening_candidate"))
                payload = {"type": "accept_repeated_opening", "candidate_id": choice["id"]}
                second.send_json(payload)
                event = second.receive_json()
                self.assertEqual(event["type"], "error")
                socket.send_json(payload)
                active = self.until(socket, "voting", allow_retry=True)
                self.assertEqual(len(active["turns"]), 1)
                self.assertIsNotNone(active["vote_deadline_ms"])
                self.assertFalse(active["opening_repeated"])
                self.assertEqual(self.until(second, "voting")["turns"], active["turns"])
                socket.send_json(payload)
                self.assertEqual(socket.receive_json()["type"], "error")
            self.assertEqual(len(recent_openings(self._offline_credentials[2]["id"], paper_key(coverage.FILES))), 2)
        self.start_opening(lambda files, *args, **kwargs: self.move(files, "Why this campus?"), expected="retry", on_state=choose)

    def test_retry_replaces_candidate_within_cap_and_old_choices_expire_after_restart(self):
        self.start_opening(lambda files, *args, **kwargs: self.move(files, "Why this campus?"))
        def choose(socket, state):
            old = state["opening_candidate"]["id"]
            socket.send_json({"type": "retry_opening", "candidate_id": old})
            refreshed = self.until(socket, "retry")
            current = refreshed["opening_candidate"]["id"]
            self.assertNotEqual(old, current)
            self.assertEqual(refreshed["question_attempts_left"], 0)
            socket.send_json({"type": "accept_repeated_opening", "candidate_id": old})
            self.assertEqual(socket.receive_json()["type"], "error")
            socket.send_json({"type": "retry_opening", "candidate_id": current})
            self.assertEqual(socket.receive_json()["type"], "error")
            with self.client.websocket_connect(f"/ws/{state['room_code']}") as reconnect:
                reconnect.send_json({"type": "hello", "token": self.latest_host["player_token"]})
                restored = self.until(reconnect, "retry")
                self.assertEqual(restored["opening_candidate"]["id"], current)
            # Drain the disconnect snapshot before inspecting the restart.
            self.until(socket, "retry")
            socket.send_json({"type": "restart"})
            self.until(socket, "generating", allow_retry=True)
            new_run = self.until(socket, "retry")
            self.assertNotEqual(new_run["opening_candidate"]["id"], current)
            socket.send_json({"type": "accept_repeated_opening", "candidate_id": current})
            self.assertEqual(socket.receive_json()["type"], "error")
            self.assertEqual(len(recent_openings(self._offline_credentials[2]["id"], paper_key(coverage.FILES))), 1)
        self.start_opening(lambda files, *args, **kwargs: self.move(files, "Why this campus?"), expected="retry", on_state=choose)

    def test_failed_acceptance_keeps_candidate_and_no_vote_until_storage_recovers(self):
        from backend.account_store import connect_store, database_path
        self.start_opening(lambda files, *args, **kwargs: self.move(files, "Why this campus?"))
        def choose(socket, state):
            payload = {"type": "accept_repeated_opening", "candidate_id": state["opening_candidate"]["id"]}
            with connect_store(database_path()) as db:
                db.execute("CREATE TRIGGER reject_accept BEFORE INSERT ON research_openings BEGIN SELECT RAISE(ABORT,'private fixture'); END")
            socket.send_json(payload)
            error = socket.receive_json()
            self.assertEqual(error["type"], "error")
            self.assertIn("Nothing new was charged", error["message"])
            self.assertNotIn("private fixture", error["message"])
            with connect_store(database_path()) as db:
                db.execute("DROP TRIGGER reject_accept")
            socket.send_json(payload)
            active = self.until(socket, "voting", allow_retry=True)
            self.assertEqual(active["turns"][0]["question"], "Why this campus?")
            self.assertEqual(len(recent_openings(self._offline_credentials[2]["id"], paper_key(coverage.FILES))), 2)
        self.start_opening(lambda files, *args, **kwargs: self.move(files, "Why this campus?"), expected="retry", on_state=choose)

    def test_repeated_opening_with_unicode_line_separator_keeps_authoritative_citation(self):
        from backend.question_generator import numbered_source_lines
        paper = coverage.PAPER.replace("Section 1:", "Section 1:\u2028continued:")
        def generate(files, *args, **kwargs):
            return ResearchMove(RESEARCH_PANELISTS[0], GroundedQuestion("Why this campus?", files[0].name, 1,
                numbered_source_lines(files[0].content)[0][1], evidence_kind="research_text"), "topic-1", False, None)
        self.start_opening(generate, paper=paper)
        def choose(socket, state):
            socket.send_json({"type": "accept_repeated_opening", "candidate_id": state["opening_candidate"]["id"]})
            active = self.until(socket, "voting", allow_retry=True)
            self.assertEqual(active["turns"][0]["evidence_text"], "Section 1:\u2028")
        self.start_opening(generate, paper=paper, expected="retry", on_state=choose)

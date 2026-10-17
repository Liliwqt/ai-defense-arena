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
    def until(self, socket, phase=None, **conditions):
        for _ in range(40):
            event = socket.receive_json()
            self.assertNotEqual(event["type"], "error", event)
            state = event["state"]
            if phase != "retry":
                self.assertNotEqual(state["phase"], "retry", state.get("error"))
            if (phase is None or state["phase"] == phase) and all(state.get(k) == v for k, v in conditions.items()):
                return state
        self.fail("Expected room snapshot was not published.")

    def start_opening(self, generate, *, filename="paper.md", expected="voting", during_history=None):
        response = self.client.post("/api/rooms", data={"host_name": "Host", "defense_type": "research"},
                                    files=[("research_files", (filename, coverage.PAPER.encode(), "text/markdown"))])
        self.assertEqual(response.status_code, 201, response.text)
        host = response.json()
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
            return self.until(socket, expected)

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

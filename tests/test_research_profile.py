"""Profile review contracts; AI responses are synthetic and offline."""

import unittest
import os
from pathlib import Path
from unittest.mock import patch

from backend import game_server
from backend.question_generator import QuestionGenerationError
from pydantic import ValidationError
from streamlit.testing.v1 import AppTest

from backend.project_files import ProjectFile
from backend.research_plan import generate_research_plan
from tests.test_research_plan import FakeClient, PAPER, draft
from tests import test_research_plan as fixtures


def profile_draft():
    return {
        "fields": ["Education", "Software engineering"],
        "approaches": ["quantitative", "computational/design"],
        "setting": "University campus",
        "explanation": "The paper proposes a campus queue pilot and compares waiting times.",
        "references": [{"source_file": 1, "evidence_line": 4}],
        "uncertainties": [],
    }


class ResearchProfileGenerationTests(unittest.TestCase):
    def test_mapping_returns_grounded_multifield_profile_in_its_existing_request(self):
        output = {**draft(), "profile": profile_draft()}
        output["profile"]["references"][0]["evidence_text"] = "AI invented quotation"
        client = FakeClient(output)
        plan = generate_research_plan([ProjectFile("study.md", PAPER, "research_text")],
                                     "offline-key", client=client)
        profile = plan.snapshot()["profile"]
        self.assertEqual(profile["fields"], ["Education", "Software engineering"])
        self.assertEqual(profile["approaches"], ["quantitative", "computational/design"])
        self.assertEqual(profile["references"][0]["evidence_text"], "Recruit volunteers for a two-week pilot.")
        self.assertEqual(profile["references"][0]["evidence_location"], "Line 4")
        self.assertNotIn("AI invented quotation", str(profile))
        self.assertEqual(len(client.calls), 1)

    def test_invalid_profile_cannot_become_a_ready_map(self):
        invalid = [
            {"fields": []}, {"fields": ["Education", "education"]},
            {"fields": ["x" * 121]}, {"approaches": []},
            {"approaches": ["qualitative", "qualitative"]}, {"approaches": ["invented-method"]},
            {"setting": "x" * 301}, {"explanation": ""},
            {"references": []}, {"references": [{"source_file": 1, "evidence_line": 900}]},
            {"references": [{"source_file": True, "evidence_line": 1}]},
            {"uncertainties": ["x" * 301]},
        ]
        for change in invalid:
            with self.subTest(change=change):
                output = {**draft(), "profile": {**profile_draft(), **change}}
                with self.assertRaises((QuestionGenerationError, ValidationError)):
                    generate_research_plan([ProjectFile("study.md", PAPER, "research_text")],
                                          "offline-key", client=FakeClient(output))

    def test_profile_requires_paper_evidence_even_when_code_is_accepted(self):
        output = {**draft(), "profile": profile_draft()}
        output["profile"]["references"] = [{"source_file": 2, "evidence_line": 1}]
        files = [ProjectFile("study.md", PAPER, "research_text"), ProjectFile("queue.py", "save()")]
        with self.assertRaises(QuestionGenerationError):
            generate_research_plan(files, "offline-key", defense_type="mixed", client=FakeClient(output))
        output.pop("profile")
        with self.assertRaises(ValidationError):
            generate_research_plan(files, "offline-key", defense_type="mixed", client=FakeClient(output))


class ResearchProfileRoomTests(unittest.TestCase):
    setUp = fixtures.ResearchPlanRoomTests.setUp
    create = fixtures.ResearchPlanRoomTests.create
    hello = fixtures.ResearchPlanRoomTests.hello
    until = fixtures.ResearchPlanRoomTests.until

    def test_host_must_explicitly_confirm_profile_before_budget_approval(self):
        host = self.create()
        with patch("backend.rooms.planning.generate_research_plan", return_value=self.plan) as ai, \
                self.client.websocket_connect(f"/ws/{host['room_code']}") as socket:
            self.hello(socket, host["player_token"])
            socket.send_json({"type": "prepare_research_plan"})
            ready = self.until(socket, research_planning_status="ready")
            self.assertEqual(ready["research_plan"]["profile"]["fields"], ["Education"])
            socket.send_json({"type": "approve_research_plan", "plan_id": self.plan.id,
                              "question_budget": 8})
            rejected = socket.receive_json()
            self.assertEqual(rejected["type"], "error")
            self.assertIn("profile", rejected["message"])
            socket.send_json({"type": "approve_research_plan", "plan_id": self.plan.id,
                              "question_budget": 8, "confirm_profile": True})
            approved = self.until(socket, research_plan_approved=True)
            self.assertEqual(approved["research_plan"]["profile"], ready["research_plan"]["profile"])
            self.assertEqual(ai.call_count, 1)
            with patch("backend.rooms.questions.generate_research_move", side_effect=QuestionGenerationError("offline opening")):
                socket.send_json({"type": "start", "plan_id": self.plan.id, "question_budget": 8})
                self.until(socket, phase="retry")
            self.assertIs(game_server.rooms[host["room_code"]].defense.plan.profile, self.plan.profile)
            self.assertEqual(game_server.rooms[host["room_code"]].defense.context()["plan"]["profile"],
                             ready["research_plan"]["profile"])

    def test_unclear_profile_needs_acknowledgment_and_restores_for_guests(self):
        output = {**draft(), "profile": {**profile_draft(), "fields": ["Unclear"],
                  "approaches": ["unclear"], "uncertainties": ["The analysis approach is not specified."]}}
        self.plan = generate_research_plan([ProjectFile("study.md", PAPER, "research_text")],
                                          "offline-key", client=FakeClient(output))
        host = self.create()
        guest = self.client.post(f"/api/rooms/{host['room_code']}/join", json={"name": "Guest"}).json()
        with patch("backend.rooms.planning.generate_research_plan", return_value=self.plan) as ai:
            with self.client.websocket_connect(f"/ws/{host['room_code']}") as h, \
                    self.client.websocket_connect(f"/ws/{host['room_code']}") as g:
                self.hello(h, host["player_token"])
                self.hello(g, guest["player_token"])
                h.send_json({"type": "prepare_research_plan"})
                for socket in (h, g):
                    ready = self.until(socket, research_planning_status="ready")
                    self.assertTrue(ready["research_plan"]["profile"]["needs_uncertainty_acknowledgment"])
                approval = {"type": "approve_research_plan", "plan_id": self.plan.id,
                            "question_budget": 8, "confirm_profile": True}
                g.send_json({**approval, "acknowledge_uncertainty": True})
                self.assertIn("Only the host", g.receive_json()["message"])
                for ack in (None, False, "true"):
                    h.send_json({**approval, "acknowledge_uncertainty": ack})
                    self.assertIn("Acknowledge", h.receive_json()["message"])
                h.send_json({**approval, "acknowledge_uncertainty": True})
                for socket in (h, g):
                    approved = self.until(socket, research_plan_approved=True)
                    self.assertEqual(approved["turns"], [])
            with self.client.websocket_connect(f"/ws/{host['room_code']}") as restored:
                state = self.hello(restored, guest["player_token"])
                self.assertTrue(state["research_plan_approved"])
                self.assertEqual(state["research_plan"]["profile"]["fields"], ["Unclear"])
            self.assertEqual(ai.call_count, 1)

    def test_older_approved_map_cannot_start_or_reserve_a_run(self):
        from dataclasses import replace
        host = self.create()
        room = game_server.rooms[host["room_code"]]
        room.research_plan = replace(self.plan, profile=None)
        room.research_plan_approved = True
        room.research_budget_preview = 8
        with patch("backend.rooms.lifecycle.reserve_room_run") as reserve, \
                self.client.websocket_connect(f"/ws/{host['room_code']}") as socket:
            self.hello(socket, host["player_token"])
            socket.send_json({"type": "start", "plan_id": self.plan.id, "question_budget": 8})
            error = socket.receive_json()
            self.assertEqual(error["type"], "error")
            self.assertIn("profile", error["message"])
            reserve.assert_not_called()


class ResearchProfileStreamlitTests(unittest.TestCase):
    def setUp(self):
        from tests.offline_accounts import fallback
        fallback(self)

    def test_fallback_requires_profile_review_before_confirmation(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "offline-key"}), \
                patch("backend.research_plan.generate_research_plan", return_value=fixtures.fixture_plan()) as ai:
            app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "backend/app.py")).run()
            app.selectbox[0].select("Research paper").run()
            app.file_uploader[0].set_value([("study.md", PAPER.encode(), "text/markdown")]).run()
            next(button for button in app.button if button.label == "Prepare defense").click().run()
            self.assertFalse(app.exception)
            self.assertTrue(any("Education" in str(item.value) for item in app.markdown))
            confirm = next(button for button in app.button if button.label == "Confirm profile and budget")
            self.assertTrue(confirm.disabled)
            next(box for box in app.checkbox if box.label == "I reviewed the research profile").check().run()
            next(button for button in app.button if button.label == "Confirm profile and budget").click().run()
            self.assertTrue(app.session_state["research_plan_approved"])
            self.assertEqual(ai.call_count, 1)


    def test_fallback_unclear_profile_requires_separate_acknowledgment(self):
        from dataclasses import replace
        from backend.research_plan import ResearchProfile
        plan = fixtures.fixture_plan()
        plan = replace(plan, profile=ResearchProfile(("Unclear",), ("unclear",), None,
                       "The proposal does not describe the analysis.", plan.profile.references,
                       ("Analysis is not specified.",)))
        with patch.dict(os.environ, {"OPENAI_API_KEY": "offline-key"}), \
                patch("backend.research_plan.generate_research_plan", return_value=plan):
            app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "backend/app.py")).run()
            app.selectbox[0].select("Research paper").run()
            app.file_uploader[0].set_value([("study.md", PAPER.encode(), "text/markdown")]).run()
            next(b for b in app.button if b.label == "Prepare defense").click().run()
            next(box for box in app.checkbox if box.label == "I reviewed the research profile").check().run()
            self.assertTrue(next(b for b in app.button if b.label == "Confirm profile and budget").disabled)
            next(box for box in app.checkbox if box.label == "I understand the profile has unclear information").check().run()
            next(b for b in app.button if b.label == "Confirm profile and budget").click().run()
            self.assertTrue(app.session_state["research_plan_approved"])
            self.assertFalse(app.exception)

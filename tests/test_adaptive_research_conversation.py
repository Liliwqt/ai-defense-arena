"""Offline contracts for a confirmed research lens throughout dialogue."""

import json
from tests.research_coaching_fixtures import with_cards, scope_options
import unittest
from types import SimpleNamespace

from backend.project_files import ProjectFile
from backend.question_generator import GroundedQuestion, interpret_submission
from backend.research_plan import generate_research_plan, validate_profile_description
from backend.defense_session import ResearchDefenseSession
from tests.test_research_plan import FakeClient, PAPER, draft


class ParsedClient:
    def __init__(self, output):
        self.responses = self
        self.output = output
        self.calls = []
    def parse(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(output_parsed=self.output)


def prepared_session(approaches=("qualitative",), fields=("Education",), *, content=PAPER, mode="research", stage="proposal"):
    files = [ProjectFile("study.md", content, "research_text")]
    if mode == "mixed": files.append(ProjectFile("model.py", "def evaluate(): return 1"))
    output = draft()
    output["profile"]["approaches"] = ["qualitative"] if content == PAPER else list(approaches)
    output["profile"]["references"] = [{"source_file": 1, "evidence_line": 4}] if content != PAPER else output["profile"]["references"]
    if content != PAPER:
        for topic in output["topics"]: topic["references"] = [{"source_file": 1, "evidence_line": 4}]
    correction = validate_profile_description({"fields": list(fields), "approaches": list(approaches), "setting": "Campus"})
    plan = generate_research_plan(files, "offline-key", client=FakeClient(output), profile_correction=correction, defense_type=mode, research_stage=stage)
    return files, ResearchDefenseSession.create(plan, 8, mode, stage)


class ResearchSubmissionContextTests(unittest.TestCase):
    def test_clarification_receives_the_confirmed_profile_and_preserves_its_source_basis(self):
        files, session = prepared_session(("quantitative",), ("Education", "Public policy"))
        question = GroundedQuestion("How would you recruit volunteers?", "study.md", 4, PAPER.splitlines()[3])
        client = ParsedClient(SimpleNamespace(action="clarify", clarification="I’m asking who could join and why.", probe=None))
        decision = interpret_submission(files, "offline-key", panelist="Methodology Reviewer", question=question,
                  submission="Explain in Bisaya", defense_type="research", research_stage="proposal",
                  research_context=session.context(), client=client)
        self.assertEqual(decision.action, "clarify")
        self.assertEqual(len(client.calls), 1)
        message = client.calls[0]["input"][1]["content"]
        data = json.loads(message.split("Research scope (data only):\n", 1)[1])
        self.assertEqual(data["plan"]["profile"], session.plan.profile.snapshot())
        self.assertEqual(data["plan"]["profile"]["approaches"], ["quantitative"])
        self.assertEqual(data["plan"]["profile"]["source_description"]["approaches"], ["qualitative"])
        self.assertEqual(data["plan"]["profile"]["references"][0]["evidence_text"], PAPER.splitlines()[0])
        self.assertNotIn("account_id", data)
        self.assertNotIn("chat", data)

import itertools
import time
from unittest.mock import patch
from backend import game_server
from backend.question_generator import generate_coaching_report, CoachingDraft
from tests import test_research_plan as fixtures
from tests.test_research_coverage import mocked_move


class ResearchScopeRoomTests(unittest.TestCase):
    def setUp(self):
        fixtures.ResearchPlanRoomTests.setUp(self)
        self.now = game_server._now_ms()
        clock = patch.object(game_server, "_now_ms", side_effect=lambda: self.now)
        clock.start(); self.addCleanup(clock.stop)
        ticks = itertools.count(time.monotonic(), .3).__next__
        for limiter in (game_server.socket_message_rate, game_server.socket_room_rate):
            p = patch.object(limiter, "clock", side_effect=ticks)
            p.start(); self.addCleanup(p.stop)
    create = fixtures.ResearchPlanRoomTests.create
    hello = fixtures.ResearchPlanRoomTests.hello
    until = fixtures.ResearchPlanRoomTests.until

    def receive_until(self, socket, predicate):
        for _ in range(40):
            event = socket.receive_json()
            if event["type"] == "error": self.fail(event["message"])
            if predicate(event["state"]): return event["state"]
        self.fail("Expected research dialogue state was not published")

    def test_question_clarification_probe_and_coaching_share_the_frozen_scope(self):
        files, session = prepared_session(("quantitative", "computational/design"), ("Education", "Software engineering"))
        self.plan = session.plan
        host = self.create()
        guest = self.client.post(f"/api/rooms/{host['room_code']}/join", json={"name": "Sam"}).json()
        scopes, requests = [], []
        outputs = [
            SimpleNamespace(action="clarify", clarification="Kinsa ang mo-join sa pilot, ug nganong sila?", probe=None),
            SimpleNamespace(action="probe", clarification=None, probe=SimpleNamespace(request="Which campus groups could take part?",
                            references=[SimpleNamespace(source_file=1, evidence_line=4)])),
            SimpleNamespace(action="answer", clarification=None, probe=None),
        ]
        def ask(files, key, *, history, context, **kwargs):
            scopes.append(context["plan"]["profile"])
            return mocked_move(files, key, history=history, context=context, **kwargs)
        def interpret(files, key, **kwargs):
            kwargs.pop("client", None)
            requests.append(kwargs.get("research_context"))
            return interpret_submission(files, key, client=ParsedClient(outputs.pop(0)), **kwargs)
        def coach(files, history, key, model, **kwargs):
            kwargs.pop("client", None)
            scopes.append(kwargs["research_context"]["plan"]["profile"])
            output = CoachingDraft(summary="The team discussed recruitment. Remaining topics need practice.",
                strengths=[{"turn": 0, "text": "Explained who could join."}],
                improvements=[{"turn": 0, "text": "Justify recruitment coverage."}], next_step="Practice the unresolved topics.")
            return generate_coaching_report(files, history, key, model, client=ParsedClient(with_cards(output,history, **scope_options(kwargs))), **kwargs)
        with patch("backend.rooms.planning.generate_research_plan", return_value=self.plan) as mapper, \
                patch("backend.rooms.questions.generate_research_move", side_effect=ask), \
                patch("backend.rooms.submissions.interpret_submission", side_effect=interpret), \
                patch("backend.rooms.coaching.generate_coaching_report", side_effect=coach), \
                self.client.websocket_connect(f"/ws/{host['room_code']}") as h, \
                self.client.websocket_connect(f"/ws/{host['room_code']}") as g:
            self.hello(h, host["player_token"]); self.hello(g, guest["player_token"])
            h.send_json({"type": "prepare_research_plan"})
            self.until(h, research_planning_status="ready")
            h.send_json({"type": "approve_research_plan", "plan_id": self.plan.id, "question_budget": 8, "confirm_profile": True})
            self.until(h, research_plan_approved=True)
            h.send_json({"type": "start", "plan_id": self.plan.id, "question_budget": 8})
            voting = self.until(h, phase="voting")
            h.send_json({"type": "cast_vote", "seat": 0})
            self.until(h, my_vote=0)
            self.now = voting["vote_deadline_ms"]
            h.send_json({"type": "send_chat", "text": "private team planning detail"})
            self.receive_until(h, lambda s: s["phase"] == "question" and bool(s["chat"]))
            h.send_json({"type": "submit_answer", "turn": 0, "answer": "Explain in Bisaya"})
            clarified = self.receive_until(h, lambda s: bool(s["turns"][0]["clarifications"]))
            self.assertEqual(len(clarified["turns"]), 1)
            h.send_json({"type": "submit_answer", "turn": 0, "answer": "Volunteers from our campus could join."})
            probed = self.until(h, phase="probe")
            probe_id = probed["turns"][0]["probe"]["id"]
            h.send_json({"type": "submit_probe_reply", "turn": 0, "probe_id": probe_id, "answer": "Students from different departments."})
            self.receive_until(h, lambda s: len(s["turns"]) == 2)
            h.send_json({"type": "end_defense"})
            complete = self.until(h, feedback_status="ready")
            shared = self.until(g, feedback_status="ready")
            self.assertEqual(complete["turns"], shared["turns"])
            self.assertEqual(complete["turns"][0]["answer"], "Volunteers from our campus could join.")
            self.assertEqual(complete["turns"][0]["probe"]["reply"], "Students from different departments.")
            self.assertEqual(mapper.call_count, 1)
        self.assertEqual(len(requests), 3)
        for request in requests:
            self.assertIsNotNone(request)
            self.assertEqual(request["plan"]["profile"], self.plan.profile.snapshot())
            self.assertEqual(request["current_topic"], "topic-1")
            self.assertNotIn("private team planning detail", str(request))
            self.assertNotIn("owner_account_id", request)
        self.assertEqual(scopes, [self.plan.profile.snapshot()]*4)


class ResearchApproachRequestTests(unittest.TestCase):
    def test_supported_study_context_is_shared_in_questions_probe_clarification_and_coaching(self):
        from backend.question_generator import generate_research_move, PanelistProbe
        from tests.test_research_coverage import proposal
        cases = [
            (("qualitative",), ("Education",), "Use interviews and thematic interpretation.", "proposal", "research"),
            (("quantitative",), ("Psychology",), "Compare measured response times between conditions.", "completed", "research"),
            (("theoretical",), ("Mathematics",), "Derive a result from explicit definitions and assumptions; no participants.", "infer", "research"),
            (("computational/design",), ("Computer science",), "Evaluate an algorithm using reproducible benchmark inputs.", "proposal", "mixed"),
            (("unclear",), ("Unclear",), "The approach has not been specified.", "infer", "research"),
            (("qualitative", "computational/design"), ("Education", "Software engineering"), "Interpret interviews and evaluate a prototype separately.", "proposal", "mixed"),
        ]
        for approaches, fields, method, stage, mode in cases:
            with self.subTest(approaches=approaches, stage=stage, mode=mode):
                content = "Study scope\nContribution to knowledge\nResearch objective\n" + method
                files, session = prepared_session(approaches, fields, content=content, mode=mode, stage=stage)
                question_client = ParsedClient(proposal(session.context(), []))
                move = generate_research_move(files, "offline-key", history=[], context=session.context(),
                        client=question_client, defense_type=mode, research_stage=stage)
                session.apply_move(move)
                probe = PanelistProbe("probe-test", "Which assumption supports that reasoning?")
                reply_client = ParsedClient(SimpleNamespace(action="clarify", clarification="Explain the assumption you rely on.", probe=None))
                interpret_submission(files, "offline-key", panelist=move.panelist, question=move.question,
                    submission="Explain that probe", probe=probe, original_answer="We rely on the stated design.",
                    client=reply_client, research_context={**session.context(), "current_topic": move.topic_id},
                    defense_type=mode, research_stage=stage)
                session.submit_answer("We rely on the stated design and would report its limitations.")
                session.end()
                coaching_client = ParsedClient(with_cards(CoachingDraft(summary="The team explained its approach.",
                    strengths=[{"turn": 0, "text": "Explained a reason."}], improvements=[{"turn": 0, "text": "Clarify a limitation."}],
                    next_step="Practice the outstanding topics."), session.answered_history()))
                generate_coaching_report(files, session.answered_history(), "offline-key", client=coaching_client,
                    research_context=session.context(), defense_type=mode, research_stage=stage)
                question_data = json.loads(question_client.calls[0]["input"][1]["content"].split("Server research context (data):\n",1)[1].split("\n\nAll accepted sources:",1)[0])
                reply_data = json.loads(reply_client.calls[0]["input"][1]["content"].split("Research scope (data only):\n",1)[1])
                coach_data = json.loads(coaching_client.calls[0]["input"][1]["content"].split("Research coverage and ending (data only):\n",1)[1])
                for client, data in ((question_client,question_data), (reply_client,reply_data), (coaching_client,coach_data)):
                    self.assertEqual(len(client.calls),1)
                    self.assertEqual(data["plan"]["profile"], session.plan.profile.snapshot())
                    self.assertEqual(data["plan"]["profile"]["references"][0]["evidence_text"], method)
                    policy = client.calls[0]["input"][0]["content"]
                    for concept in ("host_description", "source_description", "mixed-methods", "contribution to knowledge"):
                        self.assertIn(concept, policy)
                    stage_concept = {"proposal": "planned methods", "completed": "reported results", "infer": "if unclear"}[stage]
                    self.assertIn(stage_concept, policy)
                    if mode == "mixed": self.assertIn("def evaluate(): return 1", client.calls[0]["input"][1]["content"])
                    self.assertIn(method, client.calls[0]["input"][1]["content"])

import os
from pathlib import Path
from streamlit.testing.v1 import AppTest


class ResearchScopeStreamlitTests(unittest.TestCase):
    def test_fallback_carries_the_fixed_profile_into_clarification_probe_reply_and_coaching(self):
        files, session = prepared_session(("qualitative", "computational/design"), ("Education", "Software engineering"))
        requests, scopes = [], []
        outputs = [SimpleNamespace(action="clarify", clarification="Kinsa ang mo-join, ug nganong sila?", probe=None),
            SimpleNamespace(action="probe", clarification=None, probe=SimpleNamespace(request="Which groups would you recruit?", references=[])),
            SimpleNamespace(action="answer", clarification=None, probe=None)]
        def interpret(files, key, **kwargs):
            kwargs.pop("client", None)
            requests.append(kwargs.get("research_context"))
            return interpret_submission(files, key, client=ParsedClient(outputs.pop(0)), **kwargs)
        def ask(files, key, *, context, history, **kwargs):
            scopes.append(context["plan"]["profile"])
            return mocked_move(files, key, context=context, history=history, **kwargs)
        def coach(files, history, key, model, **kwargs):
            kwargs.pop("client", None)
            scopes.append(kwargs["research_context"]["plan"]["profile"])
            return generate_coaching_report(files, history, key, model, client=ParsedClient(with_cards(CoachingDraft(
                summary="The team explained a recruitment choice.", strengths=[{"turn":0,"text":"Identified possible volunteers."}],
                improvements=[{"turn":0,"text":"Explain coverage limitations."}],next_step="Practice the unresolved topics.",
                closing="That explains the recruitment choice. Review the remaining topics below."),history, **scope_options(kwargs))), **kwargs)
        with patch.dict(os.environ, {"OPENAI_API_KEY":"offline-key"}), \
                patch("backend.research_plan.generate_research_plan", return_value=session.plan) as mapper, \
                patch("backend.defense_session.generate_research_move", side_effect=ask), \
                patch("backend.question_generator.interpret_submission", side_effect=interpret), \
                patch("backend.question_generator.generate_coaching_report", side_effect=coach):
            app = AppTest.from_file(str(Path(__file__).resolve().parents[1]/"backend/app.py")).run()
            app.selectbox[0].select("Research paper").run()
            app.file_uploader[0].set_value([("study.md", PAPER.encode(), "text/markdown")]).run()
            next(b for b in app.button if b.label=="Prepare defense").click().run()
            next(box for box in app.checkbox if box.label=="I reviewed the research profile").check().run()
            next(b for b in app.button if b.label=="Confirm profile and budget").click().run()
            next(b for b in app.button if b.label=="Start defense").click().run()
            for text in ("in Bisaya", "Volunteers would join.", "Students across departments."):
                next(area for area in app.text_area if area.label.startswith("Your ")).set_value(text).run()
                next(b for b in app.button if b.label=="Send to panelist").click().run()
                self.assertFalse(app.exception)
            self.assertEqual(len(app.session_state["defense_session"].turns),2)
            next(b for b in app.button if b.label=="End defense").click().run()
            next(b for b in app.button if b.label=="Generate coaching").click().run()
            self.assertFalse(app.exception)
            self.assertEqual(mapper.call_count,1)
            self.assertEqual(len(requests),3)
            for scope in requests:
                self.assertEqual(scope["plan"]["profile"], session.plan.profile.snapshot())
                self.assertEqual(scope["current_topic"],"topic-1")
            self.assertEqual(scopes,[session.plan.profile.snapshot()]*4)
            self.assertIn("That explains the recruitment choice. Review the remaining topics below.",
                          [item.value for item in app.markdown])

"""Optional closing contracts; provider output and room clocks are mocked."""

import asyncio
import unittest
from types import SimpleNamespace
from pathlib import Path
from unittest.mock import patch

from backend.project_files import ProjectFile
from backend.question_generator import (
    AnsweredQuestion, CoachingDraft, ResearchCoachingDraft, CoachingReport, QuestionGenerationError,
    SubmissionDecision, generate_coaching_report,
)
from backend.rooms.commands import CatchUpDeadline, GenerateCoaching, VerifiedActor, decode_command
from backend.rooms.coordinator import RoomCoordinator, RoomWorkflows
from tests.research_coaching_fixtures import with_cards, cards_for
from tests.offline_accounts import authenticate
from tests.test_planning_coaching_coordination import completed_room
from streamlit.testing.v1 import AppTest
from tests import test_research_coverage as coverage
from tests.test_research_coverage import Client
from backend.timed_turn import VOTE_MS


class CoachingClosingContractTests(unittest.TestCase):
    def test_legacy_reviewer_and_missing_closing_remain_compatible_but_bad_core_fails(self):
        files = [ProjectFile("paper.md", "Limited scope", "research_text")]
        history = [AnsweredQuestion("Legacy reviewer", "Why?", "A limited claim.")]
        old = SimpleNamespace(summary="Scope discussed.", strengths=[], improvements=[], next_step="Review.")
        report = generate_coaching_report(files, history, "offline-key", client=Client(with_cards(old,history)), defense_type="research")
        self.assertEqual(report.closing, "")
        invalid = CoachingDraft(summary=" ", strengths=[], improvements=[], next_step="Review.", closing=42)
        with self.assertRaises(QuestionGenerationError):
            generate_coaching_report(files, history, "offline-key", client=Client(invalid), defense_type="research")

    def test_coaching_returns_a_bounded_closing_from_the_same_request(self):
        history = [AnsweredQuestion("Methodology Reviewer", "Why this scope?",
                                    "We will limit the claim to the campus participants.")]
        closing = "That explains the scope you can defend. Review the remaining limits in coaching."
        client = Client(with_cards(SimpleNamespace(summary="The team explained scope.", strengths=[],
            improvements=[], next_step="Document scope limits.", closing=closing),history))
        report = generate_coaching_report([ProjectFile("study.md", "Campus participants", "research_text")],
            history, "offline-key", client=client, defense_type="research")

        self.assertEqual(report.closing, closing)
        self.assertEqual(len(client.calls), 1)
        self.assertIn("optional closing", client.calls[0]["input"][0]["content"])

    def test_bad_optional_closing_never_discards_a_valid_report(self):
        history = [AnsweredQuestion("Methodology Reviewer", "Why?", "We will limit the claim.")]
        for closing in (None, 42, {}, ["not text"], " ", "x" * 301, "One. Two. Three."):
            with self.subTest(closing=closing):
                draft = CoachingDraft(summary="Scope was discussed.", strengths=[],
                    improvements=[], next_step="Review limits.", closing=closing)
                client = Client(with_cards(draft,history))
                report = generate_coaching_report([ProjectFile("paper.md", "Limited scope", "research_text")],
                    history, "offline-key", client=client, defense_type="research")
                self.assertEqual(report.summary, "Scope was discussed.")
                self.assertEqual(report.closing, "")
                self.assertEqual(len(client.calls), 1)


class CoachingClosingRoomTests(unittest.IsolatedAsyncioTestCase):
    async def test_success_is_settled_once_and_restart_discards_the_old_closing(self):
        account = authenticate(self)
        room = completed_room(account, run_id="old-run")
        ready = asyncio.Event()
        requests = []

        async def coach(request):
            requests.append(request)
            return CoachingReport("Discussion ended.", [], [], "Practice.", closing="That explains the final decision.")

        async def deliver(socket, payload):
            if payload["state"]["feedback_status"] == "ready":
                ready.set()

        async def blocked(*args):
            await asyncio.Event().wait()

        coordinator = RoomCoordinator(room, RoomWorkflows(coaching_request=coach,
            question_request=blocked, sleep=blocked, now=lambda: 10_000, deliver=deliver))
        self.addAsyncCleanup(coordinator.shutdown)
        with patch("backend.rooms.coaching.live_mode", return_value=True), \
             patch("backend.rooms.coaching.LiveStore") as store:
            await coordinator.execute(GenerateCoaching(1))
            await asyncio.wait_for(ready.wait(), 1)
            self.assertTrue(room.settled)
            self.assertGreater(coordinator.view(VerifiedActor("guest"))["closing_deadline_ms"], 10_000)
            store.return_value.finish_run.assert_called_once_with("old-run", "completed")
            await coordinator.execute(GenerateCoaching(1))
            store.return_value.finish_run.assert_called_once()
            self.assertEqual(len(requests), 1)
        result = await coordinator.execute(decode_command({"type": "restart"}),
            VerifiedActor("host", account["id"]))
        self.assertTrue(result.accepted, result)
        reset = coordinator.view(VerifiedActor("guest"))
        self.assertIsNone(reset["closing_deadline_ms"])
        self.assertIsNone(reset["closing_panelist"])
        self.assertIsNone(reset["feedback"])
        self.assertEqual(reset["phase"], "generating")

    async def test_closing_is_terminal_and_reconnect_keeps_the_same_deadline(self):
        account = authenticate(self)
        room = completed_room(account)
        now = 10_000
        text = "That explains the final decision. Review the remaining limits in coaching."
        ready = asyncio.Event()

        async def coach(request):
            return CoachingReport("Discussion ended.", [], [], "Practice the gaps.", closing=text)

        async def deliver(socket, payload):
            if payload["state"]["feedback_status"] == "ready":
                ready.set()

        async def sleep(delay):
            await asyncio.Event().wait()

        coordinator = RoomCoordinator(room, RoomWorkflows(coaching_request=coach,
            now=lambda: now, deliver=deliver, sleep=sleep))
        self.addAsyncCleanup(coordinator.shutdown)
        await coordinator.execute(GenerateCoaching(1))
        await asyncio.wait_for(ready.wait(), 1)
        first = coordinator.view(VerifiedActor("host", account["id"]))
        deadline = first["closing_deadline_ms"]
        self.assertTrue(room.settled)
        self.assertEqual(first["phase"], "complete")
        self.assertEqual(first["closing_panelist"], "Critical Judge")
        self.assertEqual(first["feedback"]["closing"], text)
        self.assertIsNone(first["vote_deadline_ms"])
        self.assertIsNone(first["answer_deadline_ms"])
        self.assertGreaterEqual(deadline - now, 4_000)
        self.assertLessEqual(deadline - now, 12_000)
        expiry = room.expires_at()
        now += 1_000
        returned = coordinator.view(VerifiedActor("guest"))
        self.assertEqual(returned["closing_deadline_ms"], deadline)
        self.assertEqual(returned["turns"], first["turns"])
        now = deadline
        await coordinator.execute(CatchUpDeadline())
        final = coordinator.view(VerifiedActor("guest"))
        self.assertIsNone(final["closing_deadline_ms"])
        self.assertEqual(final["feedback"], first["feedback"])
        self.assertEqual(room.expires_at(), expiry)
        self.assertEqual(final["phase"], "complete")


class CoachingClosingStreamlitTests(unittest.TestCase):
    def test_code_fallback_displays_saved_closing_inline_without_a_new_request(self):
        text = "That explains your final decision. Review the limits below."
        report = CoachingReport("Discussion complete.",
            [{"turn": 0, "text": "You explained the constraint."}],
            [{"turn": 0, "text": "Support the claim with a measurement."}], "Practice.", closing=text)
        with patch("backend.question_generator.generate_coaching_report") as coach:
            app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "backend/app.py")).run()
            app.session_state["defense_session"] = completed_room({"id": "unused"}).defense
            app.session_state["research_coaching"] = report
            app.selectbox[0].select("Code project").run()
            self.assertFalse(app.exception)
            self.assertIn(text, [item.value for item in app.markdown])
            self.assertIn("Critical Judge · Closing remarks", [item.value for item in app.caption])
            self.assertIn("Question 1: You explained the constraint.", [item.value for item in app.markdown])
            self.assertIn("Question 1: Support the claim with a measurement.", [item.value for item in app.markdown])
            coach.assert_not_called()

    def test_unavailable_code_preserves_saved_exchanges_citations_and_missed_turns(self):
        from backend.defense_session import DefenseSession, DefenseTurn
        from backend.question_generator import GroundedQuestion, ClarificationExchange, PanelistProbe
        question = GroundedQuestion("Why use this queue?", "queue.py", 2, "queue = []",
            evidence_location="Line 2", lead_in="That explains the requested operation.")
        saved = DefenseSession([
            DefenseTurn("Technical Architect", question, answer="It preserves arrival order.",
                clarifications=[ClarificationExchange("What order?", "The order in which requests arrive.")],
                probe=PanelistProbe("saved-probe", "How do you handle two arrivals?", status="answered",
                    reply="We serialize enqueue operations.",
                    clarifications=[ClarificationExchange("Which arrivals?", "Requests received together.")])),
            DefenseTurn("Security Reviewer", question, timed_out=True),
            DefenseTurn("Product Judge", question, ended_early=True),
        ], finished=True)
        with patch("backend.question_generator.generate_coaching_report") as coach:
            app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "backend/app.py")).run()
            app.session_state["defense_session"] = saved
            app.selectbox[0].select("Code project").run()
        self.assertFalse(app.exception)
        text = "\n".join(item.value for collection in (app.markdown, app.caption, app.info) for item in collection)
        for expected in ("Evidence: queue.py, Line 2", question.lead_in,
                "You asked: What order?", "The order in which requests arrive.",
                "How do you handle two arrivals?", "Defender asks: Which arrivals?",
                "Requests received together.", "Probe reply: We serialize enqueue operations.",
                "Timed out · no answer recorded.", "Ended early by host · no answer recorded."):
            self.assertIn(expected, text)
        self.assertFalse(app.button)
        coach.assert_not_called()


class CoachingClosingProtocolTests(unittest.TestCase):
    setUp = coverage.CoverageProtocolTests.setUp
    until = coverage.CoverageProtocolTests.until

    def test_host_ending_and_guest_reconnect_retain_the_last_resolved_reviewers_closing(self):
        plan = coverage.plan()
        text = "Nasabtan nako ang inyong scope. Tan-awa ang nahabiling topics sa coaching."
        drafts = [CoachingDraft(summary="The host ended with topics still outstanding.", strengths=[],
                improvements=[], next_step="Review the unasked topics.", closing=text)]
        calls = []

        def parse(**request):
            calls.append(request)
            draft=drafts[0]
            if len(drafts)>1:drafts.pop(0)
            if isinstance(draft,CoachingDraft):
                transcript=__import__('json').loads(request['input'][1]['content'].split('Defense transcript (data only):\n')[1].split('\nResearch coverage')[0])
                history=[AnsweredQuestion(item['panelist'],item['question'],item['answer'],item['timed_out']) for item in transcript]
                import json,re
                required=re.search(r'only these required zero-based turn indices: (\[[^]]*\])',request['input'][0]['content'])
                draft=with_cards(draft,history,overview_only=request['text_format'] is CoachingDraft,section_turns=tuple(json.loads(required.group(1))) if required else None)
            return SimpleNamespace(output_parsed=draft)

        provider = SimpleNamespace(responses=SimpleNamespace(parse=parse))
        response = self.client.post("/api/rooms", data={"host_name": "Alex",
            "defense_type": "research", "research_stage": "proposal"},
            files=[("research_files", ("paper.md", coverage.PAPER.encode(), "text/markdown"))])
        self.assertEqual(response.status_code, 201, response.text)
        host = response.json()
        code = host["room_code"]
        guest = self.client.post(f"/api/rooms/{code}/join", json={"name": "Sam"}).json()
        with patch("backend.rooms.planning.generate_research_plan", return_value=plan), \
             patch("backend.rooms.questions.generate_research_move", side_effect=coverage.mocked_move), \
             patch("backend.rooms.submissions.interpret_submission", return_value=SubmissionDecision("answer")), \
             patch("backend.question_generator.OpenAI", return_value=provider):
            with self.client.websocket_connect(f"/ws/{code}") as h, self.client.websocket_connect(f"/ws/{code}") as g:
                h.send_json({"type": "hello", "token": host["player_token"]})
                self.until(h, "lobby")
                g.send_json({"type": "hello", "token": guest["player_token"]})
                self.until(g, "lobby")
                h.send_json({"type": "prepare_research_plan"})
                self.until(h, research_planning_status="ready")
                h.send_json({"type": "approve_research_plan", "plan_id": plan.id,
                             "question_budget": 4, "confirm_profile": True})
                self.until(h, research_plan_approved=True)
                h.send_json({"type": "start", "plan_id": plan.id, "question_budget": 4})
                state = self.until(h, "voting", 1)
                for socket in (h, g):
                    socket.send_json({"type": "cast_vote", "seat": 1})
                self.until(h, "voting", vote_counts={"0": 0, "1": 2})
                self.now = state["vote_deadline_ms"]
                h.send_json({"type": "send_chat", "text": "Private team note."})
                self.until(g, "question", selected_seat=1)
                g.send_json({"type": "submit_answer", "turn": 0,
                             "answer": "We will report the limits of this campus pilot."})
                self.until(h, "voting", 2)
                h.send_json({"type": "end_defense"})
                states = [self.until(socket, "complete", feedback_status="ready") for socket in (h, g)]
                self.assertEqual(states[0]["turns"], states[1]["turns"])
                for state in states:
                    self.assertEqual(state["closing_panelist"], "Methodology Reviewer")
                    self.assertEqual(state["feedback"]["closing"], text)
                    self.assertEqual(state["turns"][0]["answered_by"], "Sam")
                    self.assertTrue(state["turns"][1]["ended_early"])
                    self.assertFalse(state["turns"][1]["timed_out"])
                    self.assertEqual(state["question_budget"], 4)
                deadline = states[0]["closing_deadline_ms"]
                self.now += 500
                with self.client.websocket_connect(f"/ws/{code}") as returned:
                    returned.send_json({"type": "hello", "token": guest["player_token"]})
                    state = self.until(returned, "complete", feedback_status="ready")
                    self.assertEqual(state["closing_deadline_ms"], deadline)
                    self.assertEqual(state["feedback"], states[0]["feedback"])
                self.now = deadline
                h.send_json({"type": "send_chat", "text": "Reviewing coaching."})
                state = self.until(h, "complete", closing_deadline_ms=None)
                self.assertEqual(state["feedback"]["closing"], text)
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[0]["text_format"], CoachingDraft)
        self.assertEqual(calls[1]["text_format"], ResearchCoachingDraft)
        self.assertNotIn("Private team note.", calls[0]["input"][1]["content"])

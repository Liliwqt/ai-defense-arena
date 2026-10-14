"""Clarity request contracts and room progression; AI output is mocked.

Request assertions establish the guidance sent to the provider, not whether a
live model obeys it. Room assertions exercise the existing authenticated seam.
"""

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from backend.project_files import ProjectFile
from backend.defense_session import ResearchDefenseSession
from backend.question_generator import (
    AnsweredQuestion, NextMoveDraft, QuestionDraft, SubmissionDraft,
    generate_next_move, generate_research_move,
)
from backend.timed_turn import VOTE_MS
from tests.test_question_generator import FakeClient
from tests import test_research_coverage as coverage


class ConversationClarityTests(unittest.TestCase):
    def test_brevity_guidance_keeps_a_valid_question_with_necessary_qualifications(self):
        files = [ProjectFile("queue.py", "STAFF_ONLY = True\n")]
        history = [AnsweredQuestion("Technical Architect", "Who can read the queue?",
                                    "Staff can read it after authentication.")]
        question = (
            "When a staff member loses their role while their existing browser session "
            "is still open, how does the next request prevent access to the queue, given "
            "that the team says authentication is checked before returning names and "
            "that the uploaded code describes a staff-only boundary?"
        )
        client = FakeClient(NextMoveDraft(action="ask", panelist="Security Reviewer",
            lead_in="", question=question, source_file=1, evidence_line=1))
        move = generate_next_move(files, "offline-key", history=history,
            allowed_panelists=("Security Reviewer",), may_complete=False, client=client)

        self.assertEqual(move.question.question, question)
        self.assertEqual(move.question.evidence_text, "STAFF_ONLY = True")
        self.assertEqual(move.question.lead_in, "")
        policy = client.request["input"][0]["content"]
        self.assertIn("usually one spoken sentence", policy)
        self.assertIn("Keep qualifications needed for accuracy", policy)

    def test_research_and_mixed_reactions_identify_what_the_answer_explains(self):
        answer = "We will restrict our claim to this campus because recruitment is limited to its students."
        for mode in ("research", "mixed"):
            with self.subTest(mode=mode):
                session = ResearchDefenseSession.create(coverage.plan(), 12, mode, "proposal")
                session.apply_move(coverage.mocked_move(coverage.FILES, "offline-key",
                    history=[], context=session.context()))
                session.submit_answer(answer, speaker_name="Sam")
                output = coverage.proposal(session.context(), session.answered_history())
                output["lead_in"] = "That explains the campus scope; it does not establish results for other schools."
                client = coverage.Client(output)
                move = generate_research_move(coverage.FILES, "offline-key",
                    history=session.answered_history(), context=session.context(),
                    defense_type=mode, client=client)

                self.assertEqual(len(client.calls), 1)
                self.assertEqual(move.question.lead_in, output["lead_in"])
                self.assertEqual(session.turns[0].answer, answer)
                self.assertEqual(move.question.evidence_text,
                                 coverage.PAPER.splitlines()[move.question.evidence_line - 1])
                policy = client.calls[0]["input"][0]["content"]
                self.assertIn("Say what that reason or correction explains", policy)
                self.assertIn("Do not force a resolved-point-plus-gap template", policy)


class ConversationClarityRoomTests(unittest.TestCase):
    setUp = coverage.CoverageProtocolTests.setUp
    until = coverage.CoverageProtocolTests.until

    def test_two_clients_retain_the_answer_during_a_specific_next_reviewer_reaction(self):
        drafts = [
            QuestionDraft(lead_in="", question="Who can read the queue?", source_file=1, evidence_line=1),
            SubmissionDraft(action="answer", clarification=None),
            NextMoveDraft(action="ask", panelist="Security Reviewer",
                lead_in="That explains who needs access; the uploaded flag alone does not show how it is enforced.",
                question="How does the next request check staff access?", source_file=1, evidence_line=1),
        ]
        calls = []

        def parse(**request):
            calls.append(request)
            return SimpleNamespace(output_parsed=drafts.pop(0))

        provider = SimpleNamespace(responses=SimpleNamespace(parse=parse))
        response = self.client.post("/api/rooms", data={"host_name": "Alex", "defense_type": "code"},
            files=[("files", ("queue.py", b"STAFF_ONLY = True\n", "text/x-python"))])
        self.assertEqual(response.status_code, 201, response.text)
        host = response.json()
        code = host["room_code"]
        guest = self.client.post(f"/api/rooms/{code}/join", json={"name": "Sam"}).json()

        with patch("backend.question_generator.OpenAI", return_value=provider):
            with self.client.websocket_connect(f"/ws/{code}") as h, self.client.websocket_connect(f"/ws/{code}") as g:
                h.send_json({"type": "hello", "token": host["player_token"]})
                self.until(h, "lobby")
                g.send_json({"type": "hello", "token": guest["player_token"]})
                self.until(g, "lobby")
                h.send_json({"type": "start"})
                for socket in (h, g):
                    self.until(socket, "voting", 1)
                for socket in (h, g):
                    socket.send_json({"type": "cast_vote", "seat": 1})
                self.until(h, "voting", vote_counts={"0": 0, "1": 2})
                self.now += VOTE_MS
                g.send_json({"type": "send_chat", "text": "Private team note."})
                for socket in (h, g):
                    self.until(socket, "question", selected_seat=1)
                answer = "Only staff need access; we plan to check their role on each request."
                g.send_json({"type": "submit_answer", "turn": 0, "answer": answer})
                states = [self.until(socket, "reacting", 2) for socket in (h, g)]
                self.assertEqual(states[0]["turns"], states[1]["turns"])
                for state in states:
                    self.assertEqual(state["turns"][0]["answer"], answer)
                    self.assertEqual(state["turns"][0]["answered_by"], "Sam")
                    self.assertEqual(state["active_panelist"], "Security Reviewer")
                    self.assertEqual(state["turns"][1]["evidence_text"], "STAFF_ONLY = True")
                    self.assertIsNone(state["vote_deadline_ms"])
                    self.assertIsNone(state["answer_deadline_ms"])
                    self.assertGreaterEqual(state["reaction_deadline_ms"] - self.now, 4_000)
                    self.assertLessEqual(state["reaction_deadline_ms"] - self.now, 12_000)
                self.now = states[0]["reaction_deadline_ms"]
                h.send_json({"type": "send_chat", "text": "Ready for the next vote."})
                for socket in (h, g):
                    state = self.until(socket, "voting", 2)
                    self.assertEqual(state["vote_deadline_ms"], self.now + VOTE_MS)

        self.assertEqual(len(calls), 3)
        self.assertEqual([request["text_format"] for request in calls],
                         [QuestionDraft, SubmissionDraft, NextMoveDraft])
        for request in calls:
            self.assertIn("usually one spoken sentence", request["input"][0]["content"])
            self.assertIn("Say what that reason or correction explains", request["input"][0]["content"])
            self.assertNotIn("Private team note.", request["input"][1]["content"])

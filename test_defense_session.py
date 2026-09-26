"""Offline checks for the guided defense and retryable question generation."""

import unittest
from types import SimpleNamespace

from openai import OpenAIError

from defense_session import (
    MAX_ANSWER_CHARS,
    PANELIST_ORDER,
    DefenseSession,
    advance_defense,
    sync_project_session,
)
from project_files import ProjectFile
from question_generator import (
    GroundedQuestion,
    QuestionDraft,
    QuestionGenerationError,
    generate_panel_question,
)


class FakeClient:
    def __init__(self, outcomes):
        self.responses = self
        self.outcomes = iter(outcomes)
        self.requests = []

    def parse(self, **kwargs):
        self.requests.append(kwargs)
        outcome = next(self.outcomes)
        if isinstance(outcome, Exception):
            raise outcome
        return SimpleNamespace(output_parsed=outcome)


class DefenseSessionTests(unittest.TestCase):
    def setUp(self):
        self.files = [
            ProjectFile("README.md", "# Demo\nQueue requests safely.\n"),
            ProjectFile("queue.py", "def enqueue(item):\n    return str(item)\n"),
        ]
        self.first = GroundedQuestion(
            "Why convert queue items to strings?", "queue.py", 2, "    return str(item)"
        )

    def test_four_alternating_turns_use_answers_and_exact_evidence(self):
        session = DefenseSession.start(self.first)
        client = FakeClient(
            [
                QuestionDraft(question="How is input checked?", source_file=2, evidence_line=1),
                QuestionDraft(question="What about non-string items?", source_file=2, evidence_line=2),
                QuestionDraft(question="What if item is untrusted?", source_file=2, evidence_line=1),
            ]
        )
        answers = [
            "We normalize for display.",
            "Input is currently trusted by the caller.",
            "We would add a type check.",
            "We would validate at the boundary.",
        ]
        for index, answer in enumerate(answers):
            self.assertTrue(session.awaiting_answer)
            session.submit_answer(answer)
            if index < 3:
                advance_defense(session, self.files, "test-key", client=client)
        self.assertTrue(session.completed)
        self.assertFalse(session.needs_question)
        self.assertEqual([turn.panelist for turn in session.turns], list(PANELIST_ORDER))
        self.assertEqual([turn.answer for turn in session.turns], answers)
        self.assertEqual(session.turns[1].question.evidence_text, "def enqueue(item):")
        self.assertEqual(session.turns[2].question.evidence_text, "    return str(item)")
        self.assertEqual(len(client.requests), 3)
        self.assertIn("Security Reviewer", client.requests[0]["input"][0]["content"])
        self.assertIn("security implication", client.requests[0]["input"][0]["content"])
        self.assertIn("follow-up turn", client.requests[1]["input"][0]["content"])
        self.assertIn("We normalize for display.", client.requests[1]["input"][1]["content"])
        self.assertIn("Input is currently trusted", client.requests[2]["input"][1]["content"])
        self.assertIn("follow-up turn", client.requests[2]["input"][0]["content"])

    def test_failed_request_keeps_answer_and_retry_adds_one_question(self):
        session = DefenseSession.start(self.first)
        session.submit_answer("We normalize for display.")
        client = FakeClient(
            [
                OpenAIError("temporary failure"),
                QuestionDraft(question="How is input checked?", source_file=2, evidence_line=1),
            ]
        )
        with self.assertRaises(OpenAIError):
            advance_defense(session, self.files, "test-key", client=client)
        self.assertTrue(session.needs_question)
        self.assertEqual(len(session.turns), 1)
        self.assertEqual(session.turns[0].answer, "We normalize for display.")
        advance_defense(session, self.files, "test-key", client=client)
        self.assertEqual(len(session.turns), 2)
        self.assertEqual(session.turns[0].answer, "We normalize for display.")
        self.assertEqual(session.turns[1].panelist, "Security Reviewer")
        self.assertEqual(client.requests[0]["input"], client.requests[1]["input"])

    def test_invalid_citation_keeps_pending_turn_retryable(self):
        session = DefenseSession.start(self.first)
        session.submit_answer("We normalize for display.")
        client = FakeClient([QuestionDraft(question="Risk?", source_file=1, evidence_line=2)])
        with self.assertRaisesRegex(QuestionGenerationError, "invalid project file"):
            advance_defense(session, self.files, "test-key", client=client)
        self.assertTrue(session.needs_question)
        self.assertEqual(len(session.turns), 1)

    def test_follow_up_requires_earlier_answer_from_same_panelist(self):
        with self.assertRaisesRegex(ValueError, "earlier answer"):
            generate_panel_question(
                self.files,
                "test-key",
                panelist="Technical Architect",
                history=(),
                follow_up=True,
                client=FakeClient([]),
            )

    def test_answers_are_bounded_and_cannot_be_submitted_twice(self):
        session = DefenseSession.start(self.first)
        with self.assertRaisesRegex(ValueError, "Write an answer"):
            session.submit_answer("  ")
        with self.assertRaisesRegex(ValueError, "under"):
            session.submit_answer("a" * (MAX_ANSWER_CHARS + 1))
        session.submit_answer("valid")
        with self.assertRaisesRegex(ValueError, "no question"):
            session.submit_answer("duplicate")

    def test_project_change_resets_session_and_same_project_keeps_it(self):
        session = DefenseSession.start(self.first)
        state = {"defense_project_fingerprint": "original", "defense_session": session}
        sync_project_session(state, "original")
        self.assertIs(state["defense_session"], session)
        sync_project_session(state, "changed")
        self.assertNotIn("defense_session", state)
        self.assertEqual(state["defense_project_fingerprint"], "changed")
        state["defense_session"] = DefenseSession.start(self.first)
        sync_project_session(state, None)
        self.assertNotIn("defense_session", state)


if __name__ == "__main__":
    unittest.main()

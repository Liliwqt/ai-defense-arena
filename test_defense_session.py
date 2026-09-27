"""Offline checks for adaptive panelist order, completion, and retry."""

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
from question_generator import GroundedQuestion, NextMoveDraft, QuestionGenerationError


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


def ask(role, line=2):
    return NextMoveDraft(action="ask", panelist=role, lead_in="I heard your answer.", question=f"Why this choice, {role}?",
                         source_file=2, evidence_line=line)


def complete():
    return NextMoveDraft(action="complete", panelist=None, lead_in=None, question=None,
                         source_file=None, evidence_line=None)


class DefenseSessionTests(unittest.TestCase):
    def setUp(self):
        self.files = [
            ProjectFile("README.md", "# Demo\nQueue requests safely.\n"),
            ProjectFile("queue.py", "def enqueue(item):\n    return str(item)\n"),
        ]
        self.first = GroundedQuestion(
            "Why convert queue items to strings?", "queue.py", 2, "    return str(item)",
            "Let's begin with the queue representation."
        )

    def test_four_distinct_panelists_can_finish_without_followups(self):
        session = DefenseSession.start(self.first)
        client = FakeClient([ask(role) for role in PANELIST_ORDER[1:]] + [complete()])
        for index in range(4):
            session.submit_answer(f"Answer {index}")
            if session.needs_question:
                advance_defense(session, self.files, "test-key", client=client)
        self.assertTrue(session.completed)
        self.assertEqual([turn.panelist for turn in session.turns], list(PANELIST_ORDER))
        self.assertEqual(len(client.requests), 4)
        self.assertIn("Product Judge", client.requests[1]["input"][0]["content"])
        self.assertIn("Completion allowed: True", client.requests[-1]["input"][0]["content"])

    def test_each_role_can_follow_up_once_for_eight_answers(self):
        session = DefenseSession.start(self.first)
        moves = []
        for role in PANELIST_ORDER:
            moves.append(ask(role))
            if role != PANELIST_ORDER[-1]:
                moves.append(ask(PANELIST_ORDER[PANELIST_ORDER.index(role) + 1]))
        client = FakeClient(moves)
        for index in range(8):
            session.submit_answer(f"Answer {index}")
            if session.needs_question:
                advance_defense(session, self.files, "test-key", client=client)
        self.assertTrue(session.completed)
        self.assertEqual([turn.panelist for turn in session.turns],
                         [role for role in PANELIST_ORDER for _ in range(2)])
        self.assertEqual(len(client.requests), 7)
        with self.assertRaisesRegex(ValueError, "no question"):
            session.submit_answer("ninth")

    def test_premature_complete_and_skipped_role_are_retryable(self):
        session = DefenseSession.start(self.first)
        session.submit_answer("We normalize for display.")
        client = FakeClient([complete(), ask("Critical Judge"), ask("Security Reviewer")])
        with self.assertRaisesRegex(QuestionGenerationError, "too early"):
            advance_defense(session, self.files, "test-key", client=client)
        with self.assertRaisesRegex(QuestionGenerationError, "invalid panelist"):
            advance_defense(session, self.files, "test-key", client=client)
        self.assertEqual(len(session.turns), 1)
        self.assertEqual(session.turns[0].answer, "We normalize for display.")
        advance_defense(session, self.files, "test-key", client=client)
        self.assertEqual(session.turns[1].panelist, "Security Reviewer")

    def test_failed_request_and_invalid_citation_preserve_answer(self):
        session = DefenseSession.start(self.first)
        session.submit_answer("Keep the answer.")
        bad = NextMoveDraft(action="ask", panelist="Security Reviewer", lead_in="I heard your answer.", question="Risk?",
                            source_file=99, evidence_line=1)
        client = FakeClient([OpenAIError("temporary"), bad, ask("Security Reviewer")])
        with self.assertRaises(OpenAIError):
            advance_defense(session, self.files, "test-key", client=client)
        with self.assertRaisesRegex(QuestionGenerationError, "invalid project file"):
            advance_defense(session, self.files, "test-key", client=client)
        self.assertTrue(session.needs_question)
        self.assertEqual(session.turns[0].answer, "Keep the answer.")
        advance_defense(session, self.files, "test-key", client=client)
        self.assertEqual(len(session.turns), 2)

    def test_followup_prompt_includes_earlier_answer(self):
        session = DefenseSession.start(self.first)
        session.submit_answer("We normalize for display.")
        history = session.answered_history()
        self.assertEqual(history[0].lead_in, "Let's begin with the queue representation.")
        client = FakeClient([ask("Technical Architect")])
        advance_defense(session, self.files, "test-key", client=client)
        self.assertEqual(session.turns[1].panelist, "Technical Architect")
        self.assertEqual(session.turns[1].question.lead_in, "I heard your answer.")
        self.assertIn("We normalize for display.", client.requests[0]["input"][1]["content"])
        self.assertIn("follow-up", client.requests[0]["input"][0]["content"])

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
        state["defense_session"] = DefenseSession.start(self.first)
        sync_project_session(state, None)
        self.assertNotIn("defense_session", state)


if __name__ == "__main__":
    unittest.main()

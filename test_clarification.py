"""Offline same-turn clarification and answer-clock checks."""

import asyncio
import unittest
from unittest.mock import patch

import game_server as server
from defense_session import DefenseSession
from project_files import ProjectFile
from question_generator import (
    ClarificationExchange, GroundedQuestion, QuestionGenerationError,
    SubmissionDecision, SubmissionDraft, interpret_submission,
)


class FakeClient:
    def __init__(self, draft):
        self.draft = draft
        self.calls = []
        self.responses = self

    def parse(self, **kwargs):
        self.calls.append(kwargs)
        return type("Response", (), {"output_parsed": self.draft})()


class FakeSocket:
    def __init__(self):
        self.messages = []

    async def send_json(self, payload):
        self.messages.append(payload)


class InterpretationTests(unittest.TestCase):
    def setUp(self):
        self.files = [ProjectFile("study.md", "We plan to interview students.", "research_text")]
        self.question = GroundedQuestion("How will you recruit students?", "study.md", 1,
                                         "We plan to interview students.", evidence_kind="research_text")

    def test_single_structured_request_classifies_and_explains_same_question(self):
        client = FakeClient(SubmissionDraft(action="clarify", clarification="I mean how you will invite students to join the interviews."))
        result = interpret_submission(self.files, "test-key", panelist="Methodology Reviewer",
            question=self.question, submission="Can you say it in simple English?",
            clarifications=[ClarificationExchange("What does recruit mean?", "Invite people to join.")],
            defense_type="research", research_stage="proposal", client=client)
        self.assertEqual(result.action, "clarify")
        self.assertIn("invite students", result.clarification)
        self.assertEqual(len(client.calls), 1)
        self.assertIs(client.calls[0]["text_format"], SubmissionDraft)
        data = client.calls[0]["input"][1]["content"]
        self.assertIn("How will you recruit students?", data)
        self.assertIn("What does recruit mean?", data)
        self.assertIn("We plan to interview students.", data)
        self.assertNotIn("private chat", data)

    def test_invalid_interpretations_are_retriable(self):
        for draft in (
            SubmissionDraft(action="clarify", clarification=""),
            SubmissionDraft(action="clarify", clarification="x" * 801),
            SubmissionDraft(action="answer", clarification="unexpected"),
        ):
            with self.subTest(draft=draft):
                with self.assertRaises(QuestionGenerationError):
                    interpret_submission(self.files, "test-key", panelist="Methodology Reviewer",
                        question=self.question, submission="Please explain", client=FakeClient(draft))


class ClarificationRoomTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.now = 1_000_000
        self.clock = patch.object(server, "_now_ms", side_effect=lambda: self.now)
        self.clock.start()
        self.addCleanup(self.clock.stop)
        self.scheduled = patch.object(server, "_schedule_interpretation")
        self.scheduled.start()
        self.addCleanup(self.scheduled.stop)
        self.host_socket = FakeSocket()
        self.guest_socket = FakeSocket()
        self.host = server.Player("host", "Alex", 0, True, {self.host_socket})
        self.guest = server.Player("guest", "Sam", 1, False, {self.guest_socket})
        self.room = server.Room("ROOM", [ProjectFile("paper.md", "Planned pilot", "research_text")],
                                {"host": self.host, "guest": self.guest}, "research", "proposal")
        question = GroundedQuestion("How will you run the pilot?", "paper.md", 1, "Planned pilot")
        self.room.defense = DefenseSession.start(question, "research", "proposal")
        self.room.phase = "question"
        self.room.answer_deadline_ms = self.now + 60_000
        server._set_selected_locked(self.room, 1)

    async def asyncTearDown(self):
        if self.room.clock_task:
            self.room.clock_task.cancel()
            await asyncio.gather(self.room.clock_task, return_exceptions=True)

    async def send(self, player, socket, **message):
        await server._handle_action(self.room, player, socket, message)

    async def resolve(self, result):
        with patch.object(server, "interpret_submission", side_effect=result if isinstance(result, Exception) else None,
                          return_value=None if isinstance(result, Exception) else result):
            await server._interpret_pending(self.room, self.room.interpretation_id)

    async def test_clarification_keeps_turn_speaker_and_remaining_time(self):
        self.now += 20_000
        await self.send(self.guest, self.guest_socket, type="submit_answer", turn=0,
                        answer="Can you repeat that in simple English?")
        self.assertEqual(self.room.phase, "interpreting")
        self.assertEqual(self.room.snapshot(self.guest)["remaining_answer_ms"], 40_000)
        self.assertEqual(self.room.snapshot(self.host)["my_pending_submission"], None)
        self.assertEqual(self.room.snapshot(self.guest)["my_pending_submission"], "Can you repeat that in simple English?")
        self.now += 30_000  # AI processing does not consume answer time.
        await self.resolve(SubmissionDecision("clarify", "How will you test the planned pilot?"))
        self.assertEqual(self.room.phase, "question")
        self.assertEqual(self.room.answer_deadline_ms, self.now + 40_000)
        self.assertEqual(self.room.selected_seat, 1)
        self.assertEqual(len(self.room.defense.turns), 1)
        self.assertIsNone(self.room.defense.turns[0].answer)
        self.assertEqual(self.room.snapshot(self.host)["turns"][0]["clarifications"][0]["reply"],
                         "How will you test the planned pilot?")
        self.assertEqual(self.room.defense.answered_history(), [])
        self.assertIsNone(self.room.snapshot(self.guest)["my_pending_submission"])

    async def test_two_clarifications_then_answer_and_history(self):
        for index in range(2):
            await self.send(self.guest, self.guest_socket, type="submit_answer", turn=0,
                            answer=f"Can you give example {index}?")
            await self.resolve(SubmissionDecision("clarify", f"Example {index}: run a small trial."))
        await self.send(self.guest, self.guest_socket, type="submit_answer", turn=0,
                        answer="Can you explain more?")
        await self.resolve(SubmissionDecision("clarify", "Another explanation."))
        self.assertEqual(len(self.room.defense.turns[0].clarifications), 2)
        self.assertIn("both clarifications", self.room.error)
        await self.send(self.guest, self.guest_socket, type="submit_answer", turn=0,
                        answer="We will recruit ten volunteers and observe use.")
        await self.resolve(SubmissionDecision("answer"))
        self.assertEqual(self.room.phase, "generating")
        history = self.room.defense.answered_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].answer, "We will recruit ten volunteers and observe use.")
        self.assertEqual(len(history[0].clarifications), 2)
        self.assertEqual(self.room.answered_by[0], "Sam")

    async def test_old_deadline_cannot_expire_while_interpreting_or_after_resume(self):
        old_clock_id = self.room.clock_id
        self.now += 10_000
        await self.send(self.guest, self.guest_socket, type="submit_answer", turn=0,
                        answer="Can you give an example?")
        self.now += 100_000
        await server._expire_deadline(self.room, old_clock_id)
        self.assertEqual(self.room.phase, "interpreting")
        self.assertFalse(self.room.defense.turns[0].timed_out)
        await self.resolve(SubmissionDecision("clarify", "For example, test a pilot with volunteers."))
        self.assertEqual(self.room.answer_deadline_ms, self.now + 50_000)
        await self.send(self.guest, self.guest_socket, type="submit_answer", turn=0,
                        answer="Another example?")
        await self.resolve(SubmissionDecision("clarify", "Observe whether the pilot works."))
        self.now = self.room.answer_deadline_ms
        await server._expire_deadline(self.room)
        self.assertTrue(self.room.defense.turns[0].timed_out)
        self.assertEqual(len(self.room.defense.answered_history()), 1)
        self.assertIsNone(self.room.defense.answered_history()[0].answer)
        self.assertEqual(len(self.room.defense.answered_history()[0].clarifications), 2)

    async def test_failure_retry_and_explicit_use_as_answer(self):
        await self.send(self.guest, self.guest_socket, type="submit_answer", turn=0,
                        answer="We will test with volunteers.")
        await self.resolve(QuestionGenerationError("Temporary interpretation failure."))
        self.assertEqual(self.room.phase, "interpretation_retry")
        self.assertIsNone(self.room.answer_deadline_ms)
        self.assertEqual(self.room.snapshot(self.guest)["my_pending_submission"], "We will test with volunteers.")
        await self.send(self.host, self.host_socket, type="use_pending_as_answer")
        self.assertIn("Only the chosen defender", self.host_socket.messages[-1]["message"])
        await self.send(self.host, self.host_socket, type="retry_interpretation")
        self.assertEqual(self.room.phase, "interpreting")
        await self.resolve(QuestionGenerationError("Still unavailable."))
        await self.send(self.guest, self.guest_socket, type="use_pending_as_answer")
        self.assertEqual(self.room.defense.turns[0].answer, "We will test with volunteers.")
        self.assertEqual(self.room.phase, "generating")

    async def test_restart_invalidates_pending_ai_result(self):
        await self.send(self.guest, self.guest_socket, type="submit_answer", turn=0,
                        answer="Please simplify.")
        old_id = self.room.interpretation_id
        await self.send(self.host, self.host_socket, type="restart")
        self.assertIsNone(self.room.pending_submission)
        self.assertEqual(self.room.phase, "generating")
        with patch.object(server, "interpret_submission") as ai:
            await server._interpret_pending(self.room, old_id)
            ai.assert_not_called()

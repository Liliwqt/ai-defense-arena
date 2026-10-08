"""Timed-turn behavior without sockets, identity setup, or AI calls."""

import unittest

from defense_session import DefenseSession
from question_generator import GroundedQuestion, SubmissionDecision
from timed_turn import TimedTurn


class TimedTurnTests(unittest.TestCase):
    def test_exhausted_clarification_requires_explicit_direct_answer(self):
        session = DefenseSession.start(GroundedQuestion('Why?', 'queue.py', 1, 'queue = []'))
        turn = TimedTurn()
        turn.begin_vote(0)
        turn.expire(15000, {'alex':0}, session)
        for now in [16000, 17000]:
            turn.submit('alex', 'Alex', 0, 0, 'Explain?', session, now)
            turn.interpret(session, SubmissionDecision('clarify', 'Explain the queue.'), turn.interpretation_id, turn.pending_submission, {'alex':0}, now+100)
        with self.assertRaisesRegex(ValueError, 'clarification'):
            turn.submit('alex', 'Alex', 0, 0, 'Explain again?', session, 18000)
        turn.submit_direct('alex', 'Alex', 0, 0, 'We store arrivals.', session, 18000)
        self.assertEqual(session.turns[0].answer, 'We store arrivals.')
        self.assertEqual(turn.phase, 'generating')

    def test_total_pause_is_bounded_even_while_waiting_for_retry(self):
        session = DefenseSession.start(GroundedQuestion('Why?', 'queue.py', 1, 'queue = []'))
        turn = TimedTurn()
        turn.begin_vote(0)
        turn.expire(15000, {'alex':0}, session)
        turn.submit('alex', 'Alex', 0, 0, 'Explain?', session, 16000)
        turn.interpretation_failed(turn.interpretation_id, turn.pending_submission, 'Offline failure')
        self.assertEqual(turn.expire(375000, {'alex':0}, session), 'timed_out')
        self.assertTrue(session.turns[0].timed_out)
        self.assertIsNone(turn.pending_submission)

    def test_expiry_is_idempotent_and_disconnect_never_resets_deadline(self):
        session = DefenseSession.start(GroundedQuestion("Why?", "queue.py", 1, "queue = []"))
        turn = TimedTurn()
        turn.begin_vote(0)
        turn.expire(15000, {"alex": 0, "sam": 1}, session, choose=lambda seats: seats[-1])
        self.assertEqual(turn.selected_seat, 1)
        deadline = turn.answer_deadline_ms
        self.assertTrue(turn.reassign({"alex": 0}, session))
        self.assertEqual(turn.selected_seat, 0)
        self.assertEqual(session.turns[0].assigned_seat, 0)
        self.assertTrue(turn.reassign({}, session))
        self.assertIsNone(turn.selected_seat)
        self.assertTrue(turn.reassign({"sam": 1}, session))
        self.assertEqual(turn.answer_deadline_ms, deadline)
        with self.assertRaisesRegex(ValueError, "Answer time is over"):
            turn.submit("sam", "Sam", 1, 0, "Late answer", session, deadline)
        self.assertEqual(turn.expire(deadline, {"sam": 1}, session), "timed_out")
        self.assertIsNone(turn.expire(deadline, {"sam": 1}, session))
        self.assertEqual(turn.phase, "generating")
        self.assertTrue(session.turns[0].timed_out)
        self.assertIsNone(session.turns[0].answer)

    def test_retry_accepts_saved_answer_once_and_restart_rejects_stale_result(self):
        session = DefenseSession.start(GroundedQuestion("Why?", "queue.py", 1, "queue = []"))
        turn = TimedTurn()
        online = {"alex": 0}
        turn.begin_vote(0)
        turn.expire(15000, online, session)
        turn.submit("alex", "Alex", 0, 0, "We use a queue.", session, 16000)
        pending = turn.pending_submission
        old_id = turn.interpretation_id
        self.assertTrue(turn.interpretation_failed(old_id, pending, "AI unavailable."))
        self.assertEqual(turn.phase, "interpretation_retry")
        with self.assertRaisesRegex(ValueError, "Only the chosen defender"):
            turn.accept_saved_answer(session, "other", 1)
        turn.retry_interpretation(is_host=True, seat=1)
        self.assertTrue(turn.interpretation_failed(turn.interpretation_id, pending, "Still unavailable."))
        turn.accept_saved_answer(session, "alex", 0)
        self.assertEqual(session.turns[0].answer, "We use a queue.")
        self.assertEqual(session.turns[0].speaker_name, "Alex")
        self.assertEqual(turn.answered_by, {0: "Alex"})
        with self.assertRaisesRegex(ValueError, "There is no failed submission"):
            turn.accept_saved_answer(session, "alex", 0)
        turn.discard_pending()
        self.assertIsNone(turn.interpret(session, SubmissionDecision("answer"), old_id, pending, online, 17000))

    def test_vote_then_clarification_preserves_speaker_and_answer_time(self):
        session = DefenseSession.start(GroundedQuestion("Why?", "queue.py", 1, "queue = []"))
        turn = TimedTurn()
        online = {"alex": 0, "sam": 1}
        turn.begin_vote(1000)
        turn.cast_vote("alex", 1, online, 2000)
        turn.cast_vote("sam", 1, online, 3000)
        self.assertEqual(turn.expire(16000, online, session, choose=lambda seats: seats[0]), "voting_closed")
        self.assertEqual(turn.selected_seat, 1)
        self.assertEqual(turn.answer_deadline_ms, 136000)
        old_clock = turn.clock_id
        turn.submit("sam", "Sam", 1, 0, "Please simplify", session, 36000)
        pending = turn.pending_submission
        self.assertEqual(pending.remaining_ms, 100000)
        self.assertEqual(turn.pause_deadline_ms, 276000)
        self.assertIsNone(turn.expire(200000, online, session, expected_id=old_clock))
        self.assertEqual(turn.interpret(session, SubmissionDecision("clarify", "Explain the design."),
                                        turn.interpretation_id, pending, online, 200000), "clarified")
        self.assertEqual(turn.answer_deadline_ms, 300000)
        self.assertEqual(turn.selected_seat, 1)
        self.assertEqual(len(session.turns), 1)
        self.assertEqual(session.turns[0].clarifications[0].request, "Please simplify")
        self.assertIsNone(session.turns[0].answer)


if __name__ == "__main__":
    unittest.main()

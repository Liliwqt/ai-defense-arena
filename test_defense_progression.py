"""Generation preparation and application, with AI mocked."""

import unittest
from unittest.mock import Mock

from defense_session import DefenseSession
from defense_progression import prepare_progression
from question_generator import GroundedQuestion, PanelMove, SECURITY_REVIEWER


class DefenseProgressionTests(unittest.TestCase):
    def test_prepared_history_is_isolated_until_validated_move_is_applied(self):
        first = GroundedQuestion("Why?", "queue.py", 1, "queue = []")
        session = DefenseSession.start(first)
        session.submit_answer("We serialize work.", speaker_name="Alex")
        request = prepare_progression(session)
        session.turns[0].speaker_name = "Changed after preparation"
        generator = Mock(return_value=PanelMove(SECURITY_REVIEWER, GroundedQuestion("Who may add work?", "queue.py", 1, "queue = []")))
        move = request.generate([], "mock-key", next_move=generator)
        self.assertEqual(generator.call_args.kwargs["history"][0].speaker_name, "Alex")
        candidate = request.apply(move)
        self.assertEqual(len(session.turns), 1)
        self.assertEqual(len(candidate.turns), 2)
        self.assertEqual(candidate.turns[0].speaker_name, "Alex")
        self.assertEqual(candidate.turns[0].question, first)

    def test_invalid_move_preserves_prepared_and_original_answers(self):
        session = DefenseSession.start(GroundedQuestion("Why?", "queue.py", 1, "queue = []"))
        session.submit_answer("A complete answer.")
        request = prepare_progression(session)
        with self.assertRaises(ValueError):
            request.apply(PanelMove(None, None))
        self.assertEqual(len(session.turns), 1)
        self.assertEqual(session.turns[0].answer, "A complete answer.")
        self.assertEqual(len(request.session.turns), 1)
        self.assertFalse(request.session.finished)


if __name__ == "__main__":
    unittest.main()

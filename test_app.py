"""Offline Streamlit walkthrough using deterministic panel questions."""

import os
from pathlib import Path
import unittest
from unittest.mock import patch

from openai import OpenAIError
from streamlit.testing.v1 import AppTest

from question_generator import GroundedQuestion, PanelMove, SubmissionDecision


class DefenseAppTests(unittest.TestCase):
    def test_four_answer_screen_retry_and_project_reset(self):
        readme = Path("sample_project/README.md").read_bytes()
        code = Path("sample_project/queue.py").read_bytes()
        lines = code.decode().splitlines()

        def question(text, line):
            return GroundedQuestion(text, "queue.py", line, lines[line - 1])

        questions = [
            question("Why use a local SQLite database?", 5),
            question("How are reservations protected?", 8),
            question("How does this help students?", 9),
            question("What assumption needs proof?", 33),
        ]
        with (
            patch.dict(os.environ, {"OPENAI_API_KEY": "offline-test-key"}),
            patch("question_generator.generate_first_question", return_value=questions[0]),
            patch("question_generator.interpret_submission", return_value=SubmissionDecision("answer")),
            patch(
                "defense_session.generate_next_move",
                side_effect=[OpenAIError("temporary failure"),
                             PanelMove("Security Reviewer", questions[1]),
                             PanelMove("Product Judge", questions[2]),
                             PanelMove("Critical Judge", questions[3]),
                             PanelMove(None, None)],
            ),
        ):
            app = AppTest.from_file("app.py").run()
            app.file_uploader[0].set_value(
                [
                    ("README.md", readme, "text/markdown"),
                    ("queue.py", code, "text/x-python"),
                ]
            ).run()
            next(button for button in app.button if button.label == "Start defense").click().run()
            self.assertFalse(app.exception)
            self.assertIn("Why use a local SQLite database?", [item.value for item in app.markdown])

            app.text_area[0].set_value("We chose a simple local prototype.")
            next(button for button in app.button if button.label == "Send to panelist").click().run()
            self.assertTrue(any(button.label == "Retry next question" for button in app.button))
            self.assertEqual(len(app.session_state["defense_session"].turns), 1)
            self.assertEqual(
                app.session_state["defense_session"].turns[0].answer,
                "We chose a simple local prototype.",
            )
            next(button for button in app.button if button.label == "Retry next question").click().run()
            self.assertEqual(len(app.session_state["defense_session"].turns), 2)
            self.assertFalse(app.exception)

            for answer in ("We need sign-in.", "We would serialize writes.", "Add access checks."):
                app.text_area[0].set_value(answer)
                next(button for button in app.button if button.label == "Send to panelist").click().run()
                self.assertFalse(app.exception)
            self.assertTrue(app.session_state["defense_session"].completed)
            self.assertEqual(
                [item.value for item in app.code[-4:]],
                [question.evidence_text for question in questions],
            )
            self.assertTrue(any("Defense complete" in item.value for item in app.success))
            self.assertTrue(any("Product Judge" in item.value for item in app.markdown))
            self.assertTrue(any("Critical Judge" in item.value for item in app.markdown))

            next(button for button in app.button if button.label == "Start new defense").click().run()
            self.assertEqual(len(app.session_state["defense_session"].turns), 1)
            self.assertIsNone(app.session_state["defense_session"].turns[0].answer)
            self.assertTrue(any("Progress: 0 answered" in item.value for item in app.caption))

            app.file_uploader[0].set_value(
                [("queue.py", b"def changed():\n    pass\n", "text/x-python")]
            ).run()
            self.assertNotIn("defense_session", app.session_state)
            self.assertTrue(any(button.label == "Start defense" for button in app.button))
            self.assertFalse(app.exception)


    def test_clarification_keeps_streamlit_on_same_question(self):
        from question_generator import SubmissionDecision
        readme = Path("sample_project/README.md").read_bytes()
        first = GroundedQuestion("Why use a reservation queue?", "README.md", 1,
                                 readme.decode().splitlines()[0])
        second = GroundedQuestion("Who may see reservations?", "README.md", 1,
                                  readme.decode().splitlines()[0])
        with (
            patch.dict(os.environ, {"OPENAI_API_KEY": "offline-test-key"}),
            patch("question_generator.generate_first_question", return_value=first),
            patch("question_generator.interpret_submission", side_effect=[
                SubmissionDecision("clarify", "I mean what benefit a queue gives students."),
                SubmissionDecision("answer"),
            ]) as interpreter,
            patch("defense_session.generate_next_move", return_value=PanelMove("Security Reviewer", second)),
        ):
            app = AppTest.from_file("app.py").run()
            app.file_uploader[0].set_value([("README.md", readme, "text/markdown")]).run()
            next(button for button in app.button if button.label == "Start defense").click().run()
            app.text_area[0].set_value("Can you explain that simply?")
            next(button for button in app.button if button.label == "Send to panelist").click().run()
            session = app.session_state["defense_session"]
            self.assertEqual(len(session.turns), 1)
            self.assertIsNone(session.turns[0].answer)
            self.assertEqual(session.turns[0].clarifications[0].reply,
                             "I mean what benefit a queue gives students.")
            self.assertTrue(any("I mean what benefit" in item.value for item in app.info))
            app.text_area[0].set_value("It reduces waiting time.")
            next(button for button in app.button if button.label == "Send to panelist").click().run()
            self.assertEqual(app.session_state["defense_session"].turns[0].answer,
                             "It reduces waiting time.")
            self.assertEqual(len(app.session_state["defense_session"].turns), 2)
            self.assertEqual(interpreter.call_count, 2)


if __name__ == "__main__":
    unittest.main()

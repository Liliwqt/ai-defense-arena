"""Offline Streamlit walkthrough using deterministic panel questions."""

import os
from pathlib import Path
import unittest
from unittest.mock import patch

from openai import OpenAIError
from streamlit.testing.v1 import AppTest

from question_generator import GroundedQuestion


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
            question("What happens with concurrent requests?", 9),
            question("How would you protect the student name returned here?", 33),
        ]
        with (
            patch.dict(os.environ, {"OPENAI_API_KEY": "offline-test-key"}),
            patch("question_generator.generate_first_question", return_value=questions[0]),
            patch(
                "defense_session.generate_panel_question",
                side_effect=[OpenAIError("temporary failure"), *questions[1:]],
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
            next(button for button in app.button if button.label == "Submit answer").click().run()
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
                next(button for button in app.button if button.label == "Submit answer").click().run()
                self.assertFalse(app.exception)
            self.assertTrue(app.session_state["defense_session"].completed)
            self.assertEqual(
                [item.value for item in app.code[-4:]],
                [question.evidence_text for question in questions],
            )
            self.assertTrue(any("Defense complete" in item.value for item in app.success))
            self.assertTrue(any("follow-up" in item.value for item in app.markdown))

            next(button for button in app.button if button.label == "Start new defense").click().run()
            self.assertEqual(len(app.session_state["defense_session"].turns), 1)
            self.assertIsNone(app.session_state["defense_session"].turns[0].answer)
            self.assertTrue(any("Progress: 0 of 4" in item.value for item in app.caption))

            app.file_uploader[0].set_value(
                [("queue.py", b"def changed():\n    pass\n", "text/x-python")]
            ).run()
            self.assertNotIn("defense_session", app.session_state)
            self.assertTrue(any(button.label == "Start defense" for button in app.button))
            self.assertFalse(app.exception)


if __name__ == "__main__":
    unittest.main()

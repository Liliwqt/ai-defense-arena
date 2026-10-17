"""Research-first preparation through the typed Streamlit application."""

from pathlib import Path
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest


class PracticePreparationTests(unittest.TestCase):
    def test_research_default_guide_and_explicit_code_selection_survive_rerun(self):
        with patch.dict("os.environ", {"OPENAI_API_KEY": "offline-key"}):
            app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "backend" / "app.py")).run()
            self.assertFalse(app.exception)
            self.assertEqual(app.selectbox[0].value, "Research paper")
            self.assertIn("Answer directly", " ".join(item.value for item in app.markdown))
            self.assertIn("Code project · Experimental", app.selectbox[0].options)
            app.selectbox[0].select("Code project").run()
            app.run()
            self.assertFalse(app.exception)
            self.assertEqual(app.selectbox[0].value, "Code project")

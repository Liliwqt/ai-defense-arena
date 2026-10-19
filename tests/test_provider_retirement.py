"""Public generation seams fail closed without their funded text client."""

import unittest
from unittest.mock import patch

from backend.project_files import ProjectFile
from backend.defense_session import ResearchDefenseSession
from backend.question_generator import (
    AnsweredQuestion, GroundedQuestion, QuestionGenerationError,
    generate_first_question, generate_next_move, generate_research_move,
    generate_coaching_report, interpret_submission,
)
from backend.research_plan import generate_research_plan
from tests.test_research_plan import fixture_plan, PAPER


class RetiredDirectProviderTests(unittest.TestCase):
    def test_text_entry_points_require_a_funded_client_instead_of_an_old_key(self):
        files = [ProjectFile('study.md', PAPER, 'research_text')]
        question = GroundedQuestion('Why this pilot?', 'study.md', 4, PAPER.splitlines()[3])
        history = [AnsweredQuestion('Methodology Reviewer', question.question, 'We limit the scope.')] * 4
        session = ResearchDefenseSession.create(fixture_plan(), 4, 'research', 'proposal')
        operations = [
            lambda key: generate_first_question(files, key),
            lambda key: generate_next_move(files, key, history=history, allowed_panelists=('Critical Judge',), may_complete=True),
            lambda key: generate_research_move(files, key, history=[], context=session.context()),
            lambda key: generate_research_plan(files, key),
            lambda key: interpret_submission(files, key, panelist='Methodology Reviewer', question=question, submission='A limited pilot.'),
            lambda key: generate_coaching_report(files, history, key),
        ]
        with patch('httpx.Client', side_effect=AssertionError('No implicit provider dispatch')):
            for key in (None, 'retired-key', 'retired\nkey'):
                for operation in operations:
                    with self.subTest(key=bool(key), operation=operation), self.assertRaisesRegex(QuestionGenerationError, 'funded OpenRouter client'):
                        operation(key)

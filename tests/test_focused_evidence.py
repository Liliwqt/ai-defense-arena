"""Focused evidence view and bounded broader lookup; AI and network mocked."""

import unittest

from backend.focused_evidence import FocusedEvidence, MAX_EXPANSION_BYTES, MAX_EXPANSION_WINDOWS
from backend.project_files import ProjectFile
from backend.question_generator import QuestionDraft, QuestionGenerationError, _ground_question
from tests import test_research_plan as maps

LINES = [f"Section line {index}." for index in range(1, 41)]
LINES[3] = "Recruit volunteers for a two-week pilot."
LINES[5] = "Obtain consent and anonymize responses."
LINES[7] = "Compare students' wait times."
LINES[9] = "A single campus may not represent other campuses."
LINES[29] = "Retention remained stable twelve weeks after rollout."
TEXT = "\n".join(LINES) + "\n"


def build_plan():
    return maps.generate_research_plan([ProjectFile('study.md', TEXT, 'research_text')],
                                       'offline-key', research_stage='proposal',
                                       client=maps.FakeClient(maps.draft()))


def evidence_for(context):
    return FocusedEvidence.build([ProjectFile('study.md', TEXT, 'research_text')], context=context)


class FocusedEvidenceViewTests(unittest.TestCase):
    def setUp(self):
        self.files = [ProjectFile('study.md', TEXT, 'research_text')]
        self.plan = build_plan()

    def test_view_has_openings_guide_and_only_confirmed_passages(self):
        evidence = evidence_for({'plan': self.plan.snapshot(), 'question_options': [], 'coverage': {}})
        text = evidence.render()
        self.assertIn('STUDY-WIDE CONTEXT', text)
        self.assertIn('CONFIRMED PREPARATION', text)
        self.assertIn('Study design', text)
        self.assertIn('Discuss study design', text)
        self.assertIn('Recruit volunteers for a two-week pilot.', text)
        self.assertIn('EXACT RELEVANT PASSAGES', text)
        self.assertNotIn('Retention remained stable', text)
        self.assertNotIn('No focused passage was resolved', text)

    def test_numbered_sources_and_selected_topic_survive_the_excerpt_cap(self):
        lines = [f'Unique accepted passage {n}.' for n in range(1, 211)]
        files = [ProjectFile('code.py', 'def pilot(): return 1'),
                 ProjectFile('study.md', '\n'.join(lines), 'research_text')]
        topics = [{'id': f'topic-{n}', 'references': [{'filename': 'study.md',
                   'evidence_line': n*10, 'evidence_text': lines[n*10-1]}]} for n in range(1, 17)]
        context = {'plan': {'topics': topics}, 'previous_topic': 'topic-1',
                   'question_options': [{'topic_id': 'topic-16'}]}
        text = FocusedEvidence.build(files, context=context, defense_type='mixed').render()
        self.assertIn('FILE 1: code.py', text)
        self.assertIn('FILE 2: study.md', text)
        self.assertIn(lines[159], text)

    def test_representative_bounds_keep_required_cross_document_evidence(self):
        from tests.evidence_context_harness import measure
        records = measure()
        selected = [row for row in records if row['excerpt_limit'] == 14]
        self.assertEqual(len(selected), 4)
        for row in selected:
            self.assertEqual(row['retained_passages'], 9)
            self.assertLess(row['focused_bytes'], row['accepted_source_bytes']//2)
            self.assertGreater(row['lookup_windows'], 0)
            self.assertLessEqual(row['lookup_windows'], 6)
            self.assertLessEqual(row['lookup_bytes'], 24000)
        self.assertTrue(all(row['retained_passages'] < 9 for row in records if row['excerpt_limit'] < 14))

    def test_citation_outside_the_view_still_validates_against_full_source(self):
        lookup = evidence_for({}).lookup
        review = QuestionDraft(lead_in='', question='What does retention show?', source_file=1, evidence_line=30)
        question = _ground_question(review, lookup, {1})
        self.assertEqual(question.evidence_line, 30)
        self.assertIn('Retention remained stable', question.evidence_text)

    def test_missing_excerpt_is_flagged_as_not_absence_not_evidence(self):
        evidence = evidence_for({'plan': {'topics': []}})
        self.assertIn('not evidence that the paper or source omits them', evidence.render())

    def test_expansion_is_finite_reported_and_reused(self):
        evidence = evidence_for({'plan': self.plan.snapshot()})
        report = evidence.expand('retention twelve weeks after rollout')
        self.assertEqual(report['windows'], 1)
        self.assertGreater(report['bytes'], 0)
        self.assertLessEqual(report['bytes'], MAX_EXPANSION_BYTES)
        self.assertLessEqual(report['windows'], MAX_EXPANSION_WINDOWS)
        self.assertIn('Retention remained stable', evidence.expansion.text)
        self.assertIn('BROADER LOOKUP', evidence.render())
        again = evidence.expand('something unrelated entirely')
        self.assertEqual(again, report)
        self.assertIn('Retention remained stable', evidence.expansion.text)

    def test_passages_already_in_the_view_are_not_expanded_again(self):
        evidence = evidence_for({'plan': self.plan.snapshot()})
        report = evidence.expand('pilot volunteers')
        self.assertEqual(report['windows'], 0)
        self.assertEqual(report['bytes'], 0)

    def test_mixed_eligibility_still_accepts_implementation_evidence(self):
        files = [ProjectFile('study.md', TEXT, 'research_text'),
                 ProjectFile('code.py', 'def pilot():\n    return 1\n', 'implementation')]
        lookup = FocusedEvidence.build(files, context={}).lookup
        review = QuestionDraft(lead_in='', question='What does the pilot return?', source_file=2, evidence_line=1)
        question = _ground_question(review, lookup, {2})
        self.assertEqual(question.filename, 'code.py')
        with self.assertRaises(QuestionGenerationError):
            _ground_question(review, lookup, {1})


if __name__ == '__main__':
    unittest.main()

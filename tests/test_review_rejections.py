"""Rejected synthetic review responses remain identifiable without storing content."""
import json
from copy import deepcopy
from unittest.mock import patch

import httpx

from tests.test_openrouter_questions import HTTPClient, IsolatedAllowanceTests, stream_response


class ReviewRejectionTests(IsolatedAllowanceTests):
    def interpret_response(self, response):
        from backend.openrouter_questions import RunQuestionClient, establish_run_allowance
        from backend.question_generator import CombinedSubmissionDraft, GroundedQuestion, interpret_submission
        from backend.question_generator import CRITICAL_JUDGE
        establish_run_allowance('diagnostic-test', 'owner', self.files, 4)
        client = RunQuestionClient('diagnostic-test', 'owner', None, self.files, api_key='offline-fixture')
        with patch('httpx.Client', side_effect=lambda **kw: HTTPClient(
                transport=httpx.MockTransport(lambda request: stream_response(response)), **kw)):
            return interpret_submission(self.files, None, panelist=CRITICAL_JUDGE,
                question=GroundedQuestion('How will you justify the comparison?', 'study.md', 4,
                                         self.files[0].content.splitlines()[3]),
                submission='Synthetic submitted wording.', defense_type='research', research_stage='proposal',
                text_format=CombinedSubmissionDraft, research_context=self.session.context(),
                planning_context=self.session.context(), client=client.interaction(CRITICAL_JUDGE, combined=True))

    def test_critical_contradictory_response_is_classified_and_keeps_submission_pending(self):
        from tests.benchmark_transport import CampaignObserver
        from tests.operation_timing_harness import SyntheticDefenseCase, SyntheticClock, _SyntheticProvider
        from tests.reviewer_benchmark import run_case
        from tests.reviewer_cases import CASES, policies
        case = CASES[0]
        policy = policies()['current']
        scripted = _SyntheticProvider(SyntheticDefenseCase(case.id, 'synthetic-study.md',
            case.files[0].content, case.answers[0]), SyntheticClock(1000), 1)
        def respond(request):
            body = json.loads(request.content)
            if (body['model'] == 'z-ai/glm-5.3-flash' and
                    body['response_format']['json_schema']['name'] == 'CombinedSubmissionDraft'):
                return stream_response({'result': {'action': 'answer',
                    'clarification': 'synthetic-private-marker', 'probe': None,
                    'assessment': None, 'panelist': None, 'topic_id': None, 'is_follow_up': False},
                    'lookup': None})
            return scripted(request)
        observer = CampaignObserver('critical-rejection', 5_000_000_000, policy,
            transport_factory=lambda: httpx.MockTransport(respond))
        records, quality = run_case(case, 'current', policy, observer, evidence='mocked', complete=True)
        self.assertEqual(records[-1]['failure_class'], 'InvalidQuestionResponse')
        self.assertEqual(records[-1]['failure_code'], 'response_schema_invalid')
        self.assertEqual(records[-1]['failure_stage'], 'CombinedSubmissionDraft')
        self.assertEqual(quality[-1]['interpretation_results'], [])
        self.assertEqual(quality[-1]['run_result']['accepted_answers'], 3)
        self.assertTrue(quality[-1]['run_result']['pending_submission_retained'])
        self.assertFalse(quality[-1]['run_result']['defense_complete'])
        self.assertNotIn('synthetic-private-marker', json.dumps(records + quality))

    def test_each_interpretation_guard_has_a_content_free_code_and_valid_replies_stay_valid(self):
        from backend.question_generator import QuestionGenerationError
        from tests.reviewer_benchmark import failure_code
        from tests.test_openrouter_interactions import combined_answer
        base = combined_answer()
        variants = [
            ({'action': 'probe'}, 'submission_probe_conflict'),
            ({'action': 'probe', 'assessment': None, 'panelist': None, 'topic_id': None,
              'probe': {'request': '', 'references': []}}, 'submission_probe_payload_invalid'),
            ({'probe': {'request': 'Synthetic probe.', 'references': []}}, 'submission_unexpected_probe'),
            ({'clarification': ''}, 'submission_answer_has_clarification'),
            ({'assessment': None}, 'submission_missing_assessment'),
            ({'topic_id': None}, 'submission_incomplete_selection'),
            ({'action': 'clarify', 'clarification': 'Synthetic explanation.'}, 'submission_clarification_has_plan'),
            ({'action': 'clarify', 'clarification': ' ', 'assessment': None,
              'panelist': None, 'topic_id': None}, 'submission_invalid_clarification'),
        ]
        for changes, expected in variants:
            with self.subTest(code=expected), self.assertRaises(QuestionGenerationError) as raised:
                self.interpret_response({'result': {**base, **changes}, 'lookup': None})
            self.assertIs(type(raised.exception), QuestionGenerationError)
            self.assertEqual(failure_code(raised.exception), expected)
        self.assertEqual(self.interpret_response({'result': base, 'lookup': None}).action, 'answer')
        self.assertEqual(self.interpret_response({'result': {'action': 'clarify', 'clarification': 'Explain the comparison.',
            'probe': None}, 'lookup': None}).action, 'clarify')

    def test_plan_rejections_are_distinct_without_mutating_accepted_state(self):
        from backend.defense_session import PlannedMove
        from backend.question_generator import GroundedQuestion, QuestionGenerationError, RESEARCH_PANELISTS, ResearchMove
        from tests.reviewer_benchmark import failure_code
        from tests.test_combined_planning import assessment
        methodology, ethics = RESEARCH_PANELISTS[:2]
        self.session.apply_move(ResearchMove(methodology, GroundedQuestion('Why this design?', 'study.md', 4,
            self.files[0].content.splitlines()[3]), 'topic-1', False, None))
        self.session.submit_answer('Synthetic saved answer.')
        before = deepcopy(self.session)
        variants = [
            (PlannedMove(ethics, 'topic-2', False, assessment('topic-2', 0)), 'plan_invalid_assessment'),
            (PlannedMove('synthetic-private-marker', 'topic-2', False, assessment('topic-1', 0)), 'plan_invalid_selection'),
            (PlannedMove(None, None, False, assessment('topic-1', 0)), 'plan_premature_completion'),
        ]
        for planned, expected in variants:
            with self.subTest(code=expected), self.assertRaises(QuestionGenerationError) as raised:
                self.session.validate_plan(planned)
            self.assertIs(type(raised.exception), QuestionGenerationError)
            self.assertEqual(failure_code(raised.exception), expected)
            self.assertEqual(self.session, before)
            self.assertNotIn('synthetic-private-marker', failure_code(raised.exception))

    def test_empty_lookup_has_its_own_code_and_arbitrary_codes_are_not_exported(self):
        from backend.question_generator import QuestionGenerationError
        from tests.reviewer_benchmark import failure_code
        with self.assertRaises(QuestionGenerationError) as raised:
            self.interpret_response({'result': None, 'lookup': {'query': 'unmatchablexyz890', 'source_files': [1]}})
        self.assertEqual(failure_code(raised.exception), 'evidence_lookup_empty')
        for code in ('synthetic-private-marker', {'unsafe': 'synthetic-private-marker'}):
            error = QuestionGenerationError('synthetic-private-marker')
            error.reason_code = code
            self.assertEqual(failure_code(error), 'unclassified')

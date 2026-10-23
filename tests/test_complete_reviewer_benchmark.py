"""Full typed benchmark attempts stay bounded and cannot imply provider readiness."""
import json
import re
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

import httpx

from tests.test_openrouter_questions import IsolatedAllowanceTests


def scripted_responder(case, received, *, fail_section=None):
    from tests.operation_timing_harness import SyntheticDefenseCase, SyntheticClock, _SyntheticProvider
    from tests.research_coaching_fixtures import feedback
    from tests.test_openrouter_questions import stream_response
    scripted = _SyntheticProvider(SyntheticDefenseCase(case.id, 'synthetic-study.md',
        case.files[0].content, case.answers[0]), SyntheticClock(1000), 1)
    def respond(request):
        body = json.loads(request.content)
        received.append(body)
        name = body['response_format']['json_schema']['name']
        if name not in {'CoachingDraft', 'ResearchCoachingDraft'}:
            return scripted(request)
        result = {'summary': 'A bounded proposal was discussed.', 'strengths': [], 'improvements': [],
                  'next_step': 'Practice explaining the limits.', 'closing': ''}
        if name == 'ResearchCoachingDraft':
            turns = json.loads(re.search(r'only these required zero-based turn indices: (\[[0-9, ]+\])',
                                         body['messages'][0]['content'])[1])
            if fail_section in turns:
                return httpx.Response(429, json={'error': {'code': 429}})
            result['answer_cards'] = [{'turn': turn, 'feedback': feedback(), 'probe_id': None,
                                      'probe_feedback': None} for turn in turns]
        return stream_response(result)
    return respond


class CompleteReviewerBenchmarkTests(IsolatedAllowanceTests):
    def test_plan_includes_final_answer_and_coaching_without_changing_runtime_policy(self):
        from tests.reviewer_benchmark import main
        from tests.reviewer_cases import policies
        original = policies()['current']
        with redirect_stdout(StringIO()) as output, patch('httpx.Client', side_effect=AssertionError('No inference')):
            self.assertEqual(main(['--plan', '--complete-candidate']), 0)
        plan = json.loads(output.getvalue())
        self.assertEqual(len(plan['runs']), 4)
        self.assertEqual(plan['protocol']['question_budget'], 8)
        self.assertEqual(plan['protocol']['answered_turns'], 8)
        self.assertEqual(plan['protocol']['coaching'], 'funded overview and all bounded answer sections')
        self.assertEqual(plan['provider_gate'], 'not-run')
        for row in plan['runs']:
            self.assertIsNone(row['admission_problem'])
            policy = row['policy']
            self.assertEqual(policy['reviewer_reasoning']['Impact Reviewer'], {'enabled': False})
            self.assertEqual(policy['interaction_reasoning'], original.interaction_reasoning)
            self.assertGreater(row['coaching_bound_nano'], 0)
        self.assertEqual(policies()['current'], original)

    def test_complete_attempt_coaches_every_answer_and_records_all_roles_without_claiming_acceptance(self):
        from tests.reviewer_benchmark import complete_candidate, run_campaign, summarize_campaign
        from tests.reviewer_cases import CASES
        from tests.benchmark_transport import CampaignObserver
        case = CASES[0]
        configured, routes = complete_candidate()
        received = []
        respond = scripted_responder(case, received)
        observer = CampaignObserver('complete-attempt', 5_000_000_000, configured['complete-candidate'],
            provider_routes=routes, transport_factory=lambda: httpx.MockTransport(respond))
        records, quality, active = run_campaign(observer, evidence='mocked', cases=(case,),
            configured=configured, complete=True)
        self.assertEqual(active, 0)
        outcome = quality[-1]['run_result']
        self.assertTrue(outcome['defense_complete'])
        self.assertTrue(outcome['coaching_complete'])
        self.assertEqual(outcome['questions'], 8)
        self.assertEqual(outcome['cards_ready'], 8)
        self.assertEqual(len(outcome['roles_observed']), 4)
        self.assertEqual(outcome['roles_missing'], [])
        self.assertEqual(sum(r['phase'] == 'coaching' for r in records if r['event'] == 'total'), 4)
        report = summarize_campaign(records)
        self.assertEqual(report['provider_gate'], 'unreviewed')
        # The final answer is completion, not another question-writing latency sample.
        self.assertEqual(report['conditions']['complete-candidate']['target']['attempted'], 7)
        impact = [b for b in received if b['model'] == 'qwen/qwen3.8-flash']
        self.assertTrue(impact)
        for body in impact:
            self.assertEqual(body['provider']['ignore'], ['alibaba/us-east-1'])
            self.assertEqual(body['reasoning'], {'enabled': False} if
                body['response_format']['json_schema']['name'] == 'QuestionDraft' else {'max_tokens': 1024})
        self.assertNotIn(case.answers[0], json.dumps(records))
        self.assertNotIn('original_answer', json.dumps(quality))

    def test_failed_opening_stays_incomplete_and_does_not_generate_coaching(self):
        from tests.reviewer_benchmark import complete_candidate, run_campaign
        from tests.reviewer_cases import CASES
        from tests.benchmark_transport import CampaignObserver
        configured, routes = complete_candidate()
        observer = CampaignObserver('incomplete-opening', 5_000_000_000, configured['complete-candidate'],
            provider_routes=routes, transport_factory=lambda: httpx.MockTransport(lambda request:
                httpx.Response(429, json={'error': {'code': 429}})))
        records, quality, active = run_campaign(observer, evidence='mocked', cases=(CASES[0],),
            configured=configured, complete=True)
        self.assertEqual(active, 0)
        self.assertEqual(len([r for r in records if r['event'] == 'stage']), 1)
        outcome = quality[-1]['run_result']
        self.assertFalse(outcome['defense_complete'])
        self.assertFalse(outcome['coaching_complete'])
        self.assertEqual(len(outcome['roles_missing']), 4)
        self.assertEqual(outcome['coaching_reports'], [])

    def test_failed_coaching_keeps_ready_sections_and_never_claims_full_completion(self):
        from tests.reviewer_benchmark import complete_candidate, run_campaign
        from tests.reviewer_cases import CASES
        from tests.benchmark_transport import CampaignObserver
        configured, routes = complete_candidate()
        received = []
        observer = CampaignObserver('partial-coaching', 5_000_000_000, configured['complete-candidate'],
            provider_routes=routes, transport_factory=lambda: httpx.MockTransport(
                scripted_responder(CASES[0], received, fail_section=3)))
        records, quality, active = run_campaign(observer, evidence='mocked', cases=(CASES[0],),
            configured=configured, complete=True)
        self.assertEqual(active, 0)
        outcome = quality[-1]['run_result']
        self.assertTrue(outcome['defense_complete'])
        self.assertFalse(outcome['coaching_complete'])
        self.assertEqual(outcome['cards_ready'], 3)
        self.assertEqual([s['status'] for s in outcome['coaching_sections']],
                         ['ready', 'ready', 'failed', 'pending'])
        self.assertEqual([s['section'] for s in outcome['coaching_reports']], ['overview', 'answers-0'])
        self.assertEqual(len([b for b in received if b['response_format']['json_schema']['name'] ==
                              'ResearchCoachingDraft']), 2)

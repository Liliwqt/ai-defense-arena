"""Provider comparisons change only the selected model's endpoint, offline."""
import json
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

import httpx

from backend.openrouter_questions import RunQuestionPolicy
from backend.openrouter_stream import payload
from backend.question_generator import QuestionDraft
from tests.test_openrouter_questions import IsolatedAllowanceTests

DEEPSEEK = 'deepseek/deepseek-v4.1-flash-1017'


class ProviderRoutingBenchmarkTests(IsolatedAllowanceTests):
    def test_model_route_can_exclude_failed_endpoint_without_relaxing_saved_controls(self):
        from tests.benchmark_transport import CampaignObserver
        policy = RunQuestionPolicy.configured()
        model = policy.reviewer_models['Impact Reviewer']
        received = []
        selector = {'only': ['alibaba'], 'ignore': ['alibaba/us-east-1']}
        observer = CampaignObserver('excluded-endpoint', 100_000_000, policy,
            provider_routes={'candidate': {model: selector}},
            transport_factory=lambda: httpx.MockTransport(lambda request:
                received.append(json.loads(request.content)) or httpx.Response(200, text='data: [DONE]\n\n')))
        observer.context = {'condition': 'candidate'}
        body = payload(model, [], QuestionDraft, reasoning={'enabled': False}, max_tokens=100)
        with observer.client() as client:
            client.post('https://openrouter.ai/api/v1/chat/completions', json=body)
        self.assertEqual(received[0]['provider'], {**body['provider'], **selector})
        self.assertEqual(observer.records[0]['requested_provider'], selector)
        body['provider']['ignore'] = ['alibaba/other']
        with observer.client() as client, self.assertRaises(ValueError):
            client.post('https://openrouter.ai/api/v1/chat/completions', json=body)
        self.assertEqual(len(received), 1)

    def test_prepared_matrix_keeps_models_reasoning_and_other_routes_fixed(self):
        from tests.reviewer_benchmark import main
        with redirect_stdout(StringIO()) as output, patch('httpx.Client', side_effect=AssertionError('No inference in plan')):
            self.assertEqual(main(['--plan', '--provider-comparison', '--cases',
                                   'quantitative-en', 'qualitative-bisaya']), 0)
        plan = json.loads(output.getvalue())
        self.assertEqual(len(plan['runs']), 4)
        self.assertEqual(plan['provider_routes'], {
            'provider-auto': {}, 'provider-deepinfra': {DEEPSEEK: 'deepinfra'}})
        for case in ('quantitative-en', 'qualitative-bisaya'):
            rows = [r for r in plan['runs'] if r['case_id'] == case]
            self.assertEqual(len({r['case_fingerprint'] for r in rows}), 1)
            self.assertTrue(all(r['policy'] == rows[0]['policy'] for r in rows))
        self.assertEqual(plan['provider_gate'], 'not-run')

    def test_model_scoped_route_changes_only_provider_selector_and_is_recorded(self):
        from tests.benchmark_transport import CampaignObserver
        policy = RunQuestionPolicy.configured()
        captured = []
        def respond(request):
            body = json.loads(request.content)
            captured.append(body)
            self.assertEqual(int(request.headers['content-length']), len(request.content))
            return httpx.Response(200, text='data: [DONE]\n\n')
        routes = {'provider-deepinfra': {DEEPSEEK: 'deepinfra'}}
        observer = CampaignObserver('model-route', 100_000_000, policy, provider_routes=routes,
                                    transport_factory=lambda: httpx.MockTransport(respond))
        # Caller mutation cannot change an established campaign route.
        routes['provider-deepinfra'][DEEPSEEK] = 'other'
        observer.context = {'condition': 'provider-deepinfra'}
        bodies = [payload(model, [], QuestionDraft, reasoning={'effort': 'high'}, max_tokens=100)
                  for model in (DEEPSEEK, policy.planner_model)]
        with observer.client() as client:
            for body in bodies:
                with client.stream('POST', 'https://openrouter.ai/api/v1/chat/completions', json=body) as response:
                    response.read()
        self.assertEqual(captured[0], {**bodies[0], 'provider': {**bodies[0]['provider'], 'only': ['deepinfra']}})
        self.assertEqual(captured[1], bodies[1])
        records, active = observer.snapshot()
        self.assertEqual(active, 0)
        self.assertEqual(records[0]['requested_provider'], 'deepinfra')
        self.assertNotIn('requested_provider', records[1])
        self.assertNotIn('provider', records[0])  # A requested route is not an observed provider.
        self.assertEqual(observer.allowance.snapshot()['used'], sum(r['reserved_nano'] for r in records))
        with self.assertRaises(ValueError):
            CampaignObserver('model-route', 100_000_000, policy, provider_routes=routes)

    def test_routing_cannot_override_a_saved_route_or_relax_privacy(self):
        from tests.benchmark_transport import CampaignObserver
        policy = RunQuestionPolicy.configured()
        observer = CampaignObserver('conflicting-route', 100_000_000, policy,
            provider_routes={'pin': {DEEPSEEK: 'deepinfra'}},
            transport_factory=lambda: httpx.MockTransport(lambda request: self.fail('Must not dispatch')))
        observer.context = {'condition': 'pin'}
        for change in ({'only': ['deepseek']}, {'data_collection': 'allow'}):
            body = payload(DEEPSEEK, [], QuestionDraft, reasoning={'effort': 'high'}, max_tokens=100)
            body['provider'].update(change)
            with observer.client() as client, self.assertRaises(ValueError):
                client.post('https://openrouter.ai/api/v1/chat/completions', json=body)
        self.assertEqual(observer.allowance.snapshot()['used'], 0)

    def test_complete_mocked_comparison_routes_only_deepseek(self):
        from tests.benchmark_transport import CampaignObserver
        from tests.operation_timing_harness import SyntheticDefenseCase, SyntheticClock, _SyntheticProvider
        from tests.reviewer_benchmark import provider_comparison, run_campaign
        from tests.reviewer_cases import CASES
        configured, routes = provider_comparison()
        case = CASES[0]
        scripted = _SyntheticProvider(SyntheticDefenseCase(case.id, 'synthetic-study.md',
            case.files[0].content, case.answers[0]), SyntheticClock(1000), 1)
        received = []
        def respond(request):
            body = json.loads(request.content)
            received.append((observer.context['condition'], body))
            return scripted(request)
        observer = CampaignObserver('full-provider-comparison', 2_000_000_000,
            configured['provider-auto'], provider_routes=routes,
            transport_factory=lambda: httpx.MockTransport(respond))
        records, quality, active = run_campaign(observer, evidence='mocked', cases=(case,), configured=configured)
        self.assertEqual(active, 0)
        self.assertEqual(len(quality), 10)
        self.assertTrue(all(r['outcome'] == 'succeeded' for r in records if r['event'] == 'total'))
        for condition, body in received:
            expected = ['deepinfra'] if condition == 'provider-deepinfra' and body['model'] == DEEPSEEK else None
            self.assertEqual(body['provider'].get('only'), expected)
        routed = [r for r in records if r.get('requested_provider')]
        self.assertTrue(routed)
        self.assertTrue(all(r['model'] == DEEPSEEK for r in routed))

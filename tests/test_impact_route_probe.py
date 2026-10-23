"""Offline checks for narrowly scoped paid Impact-route diagnostics."""
import json
from unittest.mock import patch

import httpx

from backend.openrouter_questions import RunQuestionPolicy
from backend.openrouter_stream import payload
from backend.question_generator import QuestionDraft
from tests.test_openrouter_questions import IsolatedAllowanceTests


class ImpactDiagnosticTests(IsolatedAllowanceTests):
    def test_429_retains_only_allowlisted_metadata_and_bounded_retry_after(self):
        from tests.benchmark_transport import CampaignObserver
        secret = 'DO-NOT-PERSIST-private-message'
        response = {'error': {'code': 429, 'message': secret, 'metadata': {
            'error_type': 'rate_limit_exceeded', 'limit_source': 'upstream_provider_shared_pool',
            'provider_name': 'Alibaba', 'raw': secret, 'remedy_hint': secret}}}
        observer = CampaignObserver('safe-impact-error', 100_000_000, RunQuestionPolicy.configured(),
            transport_factory=lambda: httpx.MockTransport(lambda request: httpx.Response(
                429, json=response, headers={'Retry-After': '60', 'X-Secret': secret})))
        body = payload('qwen/qwen3.8-flash', [], QuestionDraft, reasoning={'max_tokens': 2048}, max_tokens=100)
        with observer.client() as client:
            with client.stream('POST', 'https://openrouter.ai/api/v1/chat/completions', json=body) as r:
                r.read()
        records, _ = observer.snapshot()
        record = records[0]
        self.assertEqual(record['http_status'], 429)
        self.assertEqual(record['error_code'], 429)
        self.assertEqual(record['retry_after_seconds'], 60)
        self.assertEqual(record['error_type'], 'rate_limit_exceeded')
        self.assertEqual(record['limit_source'], 'upstream_provider_shared_pool')
        self.assertEqual(record['error_provider'], 'Alibaba')
        self.assertNotIn('provider', record)  # Error attribution is not serving evidence.
        self.assertNotIn(secret, json.dumps(records))
        self.assertNotIn('cost_nano', record)
        self.assertEqual(observer.allowance.snapshot()['used'], record['reserved_nano'])

    def test_unknown_error_metadata_and_oversized_body_stay_unknown(self):
        from tests.benchmark_transport import CampaignObserver
        for i, response in enumerate((httpx.Response(429, json={'error': {'code': 'private-code',
                'metadata': {'provider_name': 'private-name', 'error_type': 'private-type',
                             'limit_source': 'private-source'}}}, headers={'Retry-After': '-1'}),
                httpx.Response(429, content=b'x'*20000))):
            observer = CampaignObserver('unknown-impact-error'+str(i), 100_000_000, RunQuestionPolicy.configured(),
                transport_factory=lambda response=response: httpx.MockTransport(lambda request: response))
            with observer.client() as client:
                with client.stream('POST', 'https://openrouter.ai/api/v1/chat/completions', json=payload(
                        'qwen/qwen3.8-flash', [], QuestionDraft, reasoning={'max_tokens': 2048}, max_tokens=100)) as r:
                    r.read()
            record = observer.snapshot()[0][0]
            self.assertEqual(record['http_status'], 429)
            for field in ('error_code','error_provider','error_type','limit_source','retry_after_seconds'):
                self.assertNotIn(field, record)
            self.assertNotIn('private-', json.dumps(record))

    def test_probe_builds_identical_payloads_with_only_route_changes_without_ai(self):
        from tests.impact_route_probe import prepare_probes
        with patch('httpx.HTTPTransport', side_effect=AssertionError('No real transport during preparation')):
            probes = prepare_probes()
        self.assertEqual(len(probes), 4)
        for case in ('quantitative-en','qualitative-bisaya'):
            selected = [p for p in probes if p['case_id']==case]
            self.assertEqual(len(selected), 2)
            first, second = selected
            self.assertEqual({k:v for k,v in first['body'].items() if k!='provider'},
                             {k:v for k,v in second['body'].items() if k!='provider'})
            self.assertEqual(first['body']['model'], 'qwen/qwen3.8-flash')
            self.assertEqual(first['body']['reasoning'], {'max_tokens':2048})
            self.assertEqual(first['body']['max_tokens'],8192)
            self.assertEqual(first['body']['provider']['only'],['alibaba'])
            self.assertEqual(first['body']['provider']['ignore'],['alibaba/us-east-1'])
            self.assertEqual(second['body']['provider']['only'],['alibaba/us-east-1'])
            self.assertNotIn('ignore',second['body']['provider'])

    def test_single_impact_probe_uses_guarded_stream_and_validates_real_source(self):
        from tests.benchmark_transport import CampaignObserver
        from tests.impact_route_probe import prepare_probes, run_probe
        from tests.test_openrouter_questions import stream_response
        probe = prepare_probes()[0]
        received = []
        def respond(request):
            body = json.loads(request.content); received.append(body)
            return stream_response({'result': {'question': 'How will you evaluate the contribution in its stated setting?',
                'lead_in': '', 'source_file': 1, 'evidence_line': 6}, 'lookup': None})
        observer = CampaignObserver('single-impact-stream', 100_000_000, probe['policy'],
            transport_factory=lambda: httpx.MockTransport(respond))
        result = run_probe(probe, observer, 'offline-key')
        self.assertEqual(result['outcome'], 'succeeded')
        self.assertEqual(result['citation_line'], 6)
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0]['provider']['ignore'], ['alibaba/us-east-1'])
        self.assertEqual(observer.snapshot()[1], 0)

    def test_single_impact_failure_never_retries_or_spends_on_other_models(self):
        from tests.benchmark_transport import CampaignObserver
        from tests.impact_route_probe import prepare_probes, run_probe
        probe = prepare_probes()[1]
        observer = CampaignObserver('single-impact-failure', 100_000_000, probe['policy'],
            transport_factory=lambda: httpx.MockTransport(lambda request: httpx.Response(
                429, json={'error': {'code':429, 'metadata': {'provider_name':'Alibaba',
                                       'error_type':'rate_limit_exceeded'}}}, headers={'Retry-After':'1'})))
        result = run_probe(probe, observer, 'offline-key')
        self.assertEqual(result['outcome'], 'failed')
        self.assertEqual(result['failure_code'], 'http_429')
        requests, _ = observer.snapshot()
        self.assertEqual(len(requests), 1)
        self.assertEqual(requests[0]['model'], 'qwen/qwen3.8-flash')
        self.assertEqual(requests[0]['error_provider'], 'Alibaba')
        self.assertEqual(requests[0]['retry_after_seconds'], 1)

    def test_streamed_error_metadata_has_same_privacy_filter(self):
        from tests.benchmark_transport import CampaignObserver
        secret = 'NEVER-RETAIN-THIS'
        event = {'error': {'code':429, 'message':secret, 'metadata': {'error_type':'rate_limit_exceeded',
                       'provider_name':'Alibaba', 'raw':secret, 'retry_after':2}}}
        observer = CampaignObserver('streamed-impact-error', 100_000_000, RunQuestionPolicy.configured(),
            transport_factory=lambda: httpx.MockTransport(lambda request: httpx.Response(
                200, text='data: '+json.dumps(event)+'\n\n')))
        body = payload('qwen/qwen3.8-flash', [], QuestionDraft, reasoning={'max_tokens':2048}, max_tokens=100)
        with observer.client() as client:
            with client.stream('POST','https://openrouter.ai/api/v1/chat/completions',json=body) as response:
                response.read()
        record = observer.snapshot()[0][0]
        self.assertEqual(record['http_status'], 200)
        self.assertEqual(record['error_code'], 429)
        self.assertEqual(record['retry_after_seconds'], 2)
        self.assertEqual(record['outcome'], 'failed')
        self.assertNotIn(secret, json.dumps(record))

    def test_prepared_probe_plan_is_reproducible_across_fresh_fixture_maps(self):
        from tests.impact_route_probe import measurement_plan, prepare_probes
        self.assertEqual(measurement_plan(prepare_probes()), measurement_plan(prepare_probes()))

"""Comparable reviewer measurements; external provider HTTP is synthetic."""
import unittest
import json
from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
from pathlib import Path
import tempfile
from unittest.mock import patch

import httpx

from tests.test_openrouter_questions import IsolatedAllowanceTests


class BenchmarkReportTests(unittest.TestCase):
    def test_late_request_records_reconcile_usage_and_do_not_make_failed_legacy_totals_complete(self):
        from tests.reviewer_benchmark import reconcile_records
        common={'condition':'current','case_id':'case-a','operation_id':'op','case_fingerprint':'same'}
        rows=[{**common,'event':'total','kind':'transition','phase':'answer','outcome':'failed',
               'duration_ms':45000,'request_count':1,'cost_nano':20},
              {**common,'event':'stage','kind':'provider_request','outcome':'received','duration_ms':100,
               'model':'model-a','cost_nano':20},
              {**common,'event':'stage','kind':'provider_request','outcome':'received','duration_ms':200,
               'model':'model-b'}]
        result=reconcile_records(rows)
        self.assertEqual(result[0]['request_count'],2)
        self.assertNotIn('cost_nano',result[0])
        self.assertTrue(result[0]['request_count_is_lower_bound'])
        rows[0]['capture_version']=2
        rows[-1]['cost_nano']=30
        self.assertEqual(reconcile_records(rows)[0]['cost_nano'],50)
        self.assertEqual(rows[0]['request_count'],1)

    def test_failed_transitions_and_unknown_cost_are_not_hidden(self):
        from tests.reviewer_benchmark import summarize_campaign
        records = [
            {'event': 'total', 'kind': 'transition', 'phase': 'answer', 'duration_ms': 9000,
             'outcome': 'succeeded', 'condition': 'current', 'case_id': 'case-a',
             'case_fingerprint': 'same', 'cost_nano': 20},
            {'event': 'total', 'kind': 'transition', 'phase': 'answer', 'duration_ms': 45000,
             'outcome': 'failed', 'condition': 'current', 'case_id': 'case-a',
             'case_fingerprint': 'same', 'failure_class': 'ProcessingWindowExpired'},
        ]
        result = summarize_campaign(records)
        current = result['conditions']['current']
        self.assertEqual(current['target']['attempted'], 2)
        self.assertEqual(current['target']['within_15_seconds'], 1)
        self.assertEqual(current['target']['fraction_within_15_seconds'], 0.5)
        self.assertEqual(current['transition_timing']['total:transition']['usage']['cost_nano'],
                         {'sum': 20, 'known_records': 1, 'unknown_records': 1})
        self.assertEqual(result['provider_gate'], 'unreviewed')
        self.assertIsNone(current['broader_lookup']['lookup_requests']['sum'])

    def test_plan_is_credential_free_and_execute_requires_explicit_local_configuration(self):
        from tests.reviewer_benchmark import main
        with patch('httpx.Client',side_effect=AssertionError('No plan requests')), redirect_stdout(StringIO()) as stdout:
            self.assertEqual(main(['--plan']),0)
        plan=json.loads(stdout.getvalue())
        self.assertEqual(plan['evidence'],'plan-only')
        self.assertEqual(len(plan['runs']),12)
        self.assertEqual(len({r['case_fingerprint'] for r in plan['runs']}),4)
        self.assertEqual(plan['provider_gate'],'not-run')
        with tempfile.TemporaryDirectory() as folder, redirect_stderr(StringIO()), patch.dict('os.environ',{'OPENROUTER_API_KEY':''}):
            output=Path(folder)/'not-created'
            with self.assertRaises(SystemExit):
                main(['--execute','--max-usd','5','--output',str(output)])
            self.assertFalse(output.exists())
            with self.assertRaises(SystemExit):
                main(['--plan','--execute'])


class BenchmarkFundingTests(IsolatedAllowanceTests):
    def test_unfinished_request_is_visible_and_cannot_supply_complete_transition_usage(self):
        from tests.benchmark_transport import CampaignObserver
        from backend.openrouter_questions import RunQuestionPolicy,PlanDraft
        from backend.openrouter_stream import payload
        from tests.reviewer_benchmark import reconcile_records,summarize_campaign
        policy=RunQuestionPolicy.configured()
        observer=CampaignObserver('active-request',100_000_000,policy,
            transport_factory=lambda:httpx.MockTransport(lambda r:httpx.Response(200,text='data: [DONE]\n\n')))
        observer.context={'condition':'current','case_id':'case-a','case_fingerprint':'same','operation_id':'active'}
        body=payload(policy.planner_model,[],PlanDraft,reasoning={'effort':'low'},max_tokens=100)
        with observer.client() as client:
            request=client.build_request('POST','https://openrouter.ai/api/v1/chat/completions',json=body)
            response=client.send(request,stream=True)
            stages,active=observer.snapshot()
            self.assertEqual(active,1)
            self.assertEqual(stages[0]['outcome'],'in_flight')
            total={**observer.context,'event':'total','kind':'transition','phase':'answer','outcome':'failed',
                   'duration_ms':45000,'capture_version':2,'cost_nano':99}
            records=reconcile_records([total]+stages)
            self.assertNotIn('cost_nano',records[0])
            self.assertEqual(records[0]['request_count'],1)
            summary=summarize_campaign(records)['conditions']['current']
            self.assertEqual(summary['stages'],{})
            self.assertEqual(summary['in_flight_requests'],1)
            response.close()
        stages,active=observer.snapshot()
        self.assertEqual(active,0)
        self.assertEqual(len(stages),1)

    def test_conflicting_cost_stays_unknown_even_when_the_stream_then_fails(self):
        from tests.benchmark_transport import CampaignObserver
        from backend.openrouter_questions import RunQuestionPolicy,PlanDraft
        from backend.openrouter_stream import payload
        class Interrupted(httpx.SyncByteStream):
            def __iter__(self):
                for cost in (0.0005,0.0007):
                    yield ('data: '+json.dumps({'usage':{'cost':cost}})+'\n\n').encode()
                raise httpx.ReadError('Synthetic interrupted stream')
        policy=RunQuestionPolicy.configured()
        observer=CampaignObserver('conflict-interrupted',100_000_000,policy,
            transport_factory=lambda:httpx.MockTransport(lambda r:httpx.Response(200,stream=Interrupted())))
        body=payload(policy.planner_model,[],PlanDraft,reasoning={'effort':'low'},max_tokens=100)
        with observer.client() as client,self.assertRaises(httpx.ReadError):
            client.post('https://openrouter.ai/api/v1/chat/completions',json=body)
        self.assertNotIn('cost_nano',observer.records[0])
        self.assertEqual(observer.allowance.snapshot()['used'],observer.records[0]['reserved_nano'])

    def test_writer_failure_preserves_the_validated_decision_for_review(self):
        from tests.reviewer_benchmark import run_case
        from tests.reviewer_cases import CASES,policies
        from tests.benchmark_transport import CampaignObserver
        from tests.operation_timing_harness import SyntheticDefenseCase,SyntheticClock,_SyntheticProvider
        case=CASES[0]
        provider=_SyntheticProvider(SyntheticDefenseCase(case.id,'synthetic-study.md',case.files[0].content,
            case.answers[0]),SyntheticClock(1000),1)
        writers=0
        def respond(request):
            nonlocal writers
            name=json.loads(request.content)['response_format']['json_schema']['name']
            if name=='QuestionDraft':
                writers+=1
                if writers==2:
                    return httpx.Response(400,json={'error':'Synthetic writer rejection'})
            return provider(request)
        observer=CampaignObserver('writer-failure',1_000_000_000,policies()['current'],
            transport_factory=lambda:httpx.MockTransport(respond))
        records,quality=run_case(case,'current',policies()['current'],observer,evidence='mocked')
        self.assertEqual(records[-1]['outcome'],'failed')
        plan=quality[-1]['validated_next_plans'][0]
        self.assertEqual(plan['assessment']['turn'],0)
        self.assertTrue(plan['assessment']['reason'])
        self.assertIsNotNone(plan['panelist'])
        self.assertIsNotNone(plan['topic_id'])
        self.assertEqual(quality[-1]['interpretation_results'][0]['plan']['panelist'],plan['panelist'])
        self.assertIn('topic_id',quality[-1]['displayed'][0])
        self.assertIn('is_follow_up',quality[-1]['displayed'][0])
        self.assertNotIn(case.answers[0],json.dumps(quality))

    def test_concurrent_campaign_admission_and_reopening_keep_the_same_cap(self):
        from concurrent.futures import ThreadPoolExecutor
        from tests.benchmark_transport import CampaignObserver
        from backend.openrouter_questions import RunQuestionPolicy, PlanDraft
        from backend.provider_allowance import AllowanceExhausted
        from backend.openrouter_stream import payload
        policy = RunQuestionPolicy.configured()
        calls = []
        factory = lambda: httpx.MockTransport(lambda r: calls.append(r) or httpx.Response(200,text='data: [DONE]\n\n'))
        observer = CampaignObserver('concurrent',100_000_000,policy,transport_factory=factory)
        body = payload(policy.planner_model,[],PlanDraft,reasoning={'effort':'low'},max_tokens=100)
        with observer.client() as client:
            client.post('https://openrouter.ai/api/v1/chat/completions',json=body)
        bound = observer.records[0]['reserved_nano']
        observer.allowance.reserve(int(observer.allowance.snapshot()['remaining'])-bound)
        def send(_):
            try:
                with observer.client() as client:
                    client.post('https://openrouter.ai/api/v1/chat/completions',json=body)
                return True
            except AllowanceExhausted:
                return False
        with ThreadPoolExecutor(max_workers=4) as workers:
            self.assertEqual(sum(workers.map(send,range(4))),1)
        self.assertEqual(len(calls),2)
        reopened=CampaignObserver('concurrent',100_000_000,policy,transport_factory=factory)
        self.assertEqual(int(reopened.allowance.snapshot()['remaining']),0)
        with self.assertRaises(ValueError):
            CampaignObserver('concurrent',200_000_000,policy)

    def test_real_flow_retry_and_lookup_are_measured_not_inferred(self):
        from tests.reviewer_benchmark import run_case,summarize_campaign
        from tests.reviewer_cases import CASES,policies
        from tests.benchmark_transport import CampaignObserver
        from tests.operation_timing_harness import SyntheticDefenseCase,SyntheticClock,_SyntheticProvider
        from tests.test_openrouter_questions import stream_response
        case=CASES[2]
        provider=_SyntheticProvider(SyntheticDefenseCase(case.id,'synthetic-study.md',case.files[0].content,
            case.answers[0]),SyntheticClock(1000),1)
        counts={}
        def respond(request):
            name=json.loads(request.content)['response_format']['json_schema']['name']
            counts[name]=counts.get(name,0)+1
            if name=='CombinedSubmissionDraft' and counts[name]==1:
                return httpx.Response(503,json={'error':'Synthetic temporary failure'})
            if name=='CombinedSubmissionDraft' and counts[name]==2:
                return stream_response({'lookup':{'query':'Eligibility protocol preserve excluded cases','source_files':[1]}})
            return provider(request)
        observer=CampaignObserver('retry-lookup',1_000_000_000,policies()['current'],
            transport_factory=lambda:httpx.MockTransport(respond))
        records,quality=run_case(case,'current',policies()['current'],observer,evidence='mocked')
        self.assertTrue(all(r['outcome']=='succeeded' for r in records))
        answer=records[1]
        self.assertEqual(answer['automatic_retries'],1)
        self.assertGreater(answer['retry_wait_ms'],0)
        self.assertEqual(answer['lookup_requests'],1)
        self.assertGreater(answer['lookup_bytes'],0)
        stages,active=observer.snapshot()
        summary=summarize_campaign(records+stages)['conditions']['current']
        self.assertEqual(summary['automatic_retries'],1)
        self.assertEqual(summary['broader_lookup']['lookup_requests']['sum'],1)
        self.assertEqual(active,0)

    def test_campaign_cap_retains_unknown_hold_and_stops_before_dispatch(self):
        from tests.benchmark_transport import CampaignObserver
        from backend.openrouter_questions import RunQuestionPolicy
        from backend.provider_allowance import AllowanceExhausted
        policy = RunQuestionPolicy.configured()
        calls = []
        observer = CampaignObserver('campaign', 100_000_000, policy,
            transport_factory=lambda: httpx.MockTransport(lambda r: calls.append(r) or httpx.Response(200, text='data: [DONE]\n\n')))
        body = {'model': policy.planner_model, 'messages': [], 'reasoning': {'effort': 'low'},
            'max_tokens': 100, 'response_format': {'json_schema': {'name': 'PlanDraft'}},
            'provider': {'allow_fallbacks': False, 'require_parameters': True, 'data_collection': 'deny',
                         'max_price': {'prompt': .30, 'completion': 1.20, 'request': 0}}}
        observer.context = {'case_id': 'case-a', 'condition': 'current'}
        with observer.client() as client:
            client.post('https://openrouter.ai/api/v1/chat/completions', json=body)
        before = observer.allowance.snapshot()
        self.assertGreater(before['used'], 0)
        self.assertNotIn('cost_nano', observer.records[0])
        observer.allowance.reserve(int(before['remaining']))
        with observer.client() as client, self.assertRaises(AllowanceExhausted):
            client.post('https://openrouter.ai/api/v1/chat/completions', json=body)
        self.assertEqual(len(calls), 1)
        self.assertNotIn('messages', json.dumps(observer.records))

    def test_current_and_candidate_use_real_contracts_without_selecting_defaults(self):
        from tests.reviewer_benchmark import run_case, summarize_campaign
        from tests.reviewer_cases import CASES, policies
        from tests.benchmark_transport import CampaignObserver
        from tests.operation_timing_harness import SyntheticDefenseCase, SyntheticClock, _SyntheticProvider
        original = policies()['current']
        all_records = []
        for condition in ('baseline', 'current', 'candidate-light'):
            case = CASES[0]
            scripted = _SyntheticProvider(SyntheticDefenseCase(case.id, 'synthetic-study.md',
                case.files[0].content, case.answers[0]), SyntheticClock(1000), 1)
            observer = CampaignObserver('contracts-'+condition, 1_000_000_000, original,
                transport_factory=lambda: httpx.MockTransport(scripted))
            records, quality = run_case(case, condition, policies()[condition], observer, evidence='mocked')
            self.assertEqual(len(records), 5)
            self.assertTrue(all(r['outcome'] == 'succeeded' for r in records))
            requests, active = observer.snapshot()
            names = [r['stage'] for r in requests]
            self.assertEqual(names.count('PlanDraft'), 5 if condition == 'baseline' else 1)
            self.assertEqual(names.count('CombinedSubmissionDraft'), 0 if condition == 'baseline' else 4)
            self.assertEqual(names.count('QuestionDraft'), 5)
            self.assertEqual(active, 0)
            self.assertEqual(len(quality), 5)
            self.assertTrue(all(item['manual_review']['grounding'] is None for item in quality))
            all_records.extend(records+requests)
        self.assertEqual(summarize_campaign(all_records)['provider_gate'], 'unreviewed')
        self.assertEqual(policies()['current'], original)

    def test_observer_reconciles_supplied_cost_without_logging_content(self):
        from tests.benchmark_transport import CampaignObserver
        from backend.openrouter_questions import RunQuestionPolicy
        from tests.test_openrouter_questions import stream_response
        from backend.openrouter_stream import payload
        from backend.openrouter_questions import PlanDraft
        policy = RunQuestionPolicy.configured()
        observer = CampaignObserver('receipt', 100_000_000, policy,
            transport_factory=lambda: httpx.MockTransport(lambda r: stream_response({}, usage={'cost': 0.0005})))
        body = payload(policy.planner_model,[{'role': 'user', 'content': 'synthetic-private-marker'}],PlanDraft,
                       reasoning={'effort':'low'}, max_tokens=100)
        with observer.client() as client:
            client.post('https://openrouter.ai/api/v1/chat/completions',json=body)
        self.assertEqual(observer.allowance.snapshot()['used'], 500_000)
        self.assertEqual(observer.records[0]['cost_nano'],500_000)
        self.assertNotIn('synthetic-private-marker',json.dumps(observer.records))

    def test_privacy_guard_stops_dispatch_and_conflicting_receipts_keep_the_hold(self):
        from tests.benchmark_transport import CampaignObserver
        from backend.openrouter_questions import RunQuestionPolicy, PlanDraft
        from backend.openrouter_stream import payload
        policy = RunQuestionPolicy.configured()
        events = ''.join('data: '+json.dumps({'usage': {'cost': cost}})+'\n\n'
                         for cost in (0.0005,0.0007,0.0007))
        calls = []
        observer = CampaignObserver('conflict', 100_000_000, policy,
            transport_factory=lambda: httpx.MockTransport(lambda r: calls.append(r) or httpx.Response(200,text=events)))
        body = payload(policy.planner_model,[],PlanDraft,reasoning={'effort':'low'},max_tokens=100)
        body['provider']['data_collection'] = 'allow'
        with observer.client() as client, self.assertRaisesRegex(ValueError,'cannot relax'):
            client.post('https://openrouter.ai/api/v1/chat/completions',json=body)
        self.assertEqual(calls,[])
        self.assertEqual(observer.allowance.snapshot()['used'],0)
        body['provider']['data_collection'] = 'deny'
        with observer.client() as client:
            client.post('https://openrouter.ai/api/v1/chat/completions',json=body)
        self.assertEqual(observer.records[0]['failure_class'],'ConflictingUsage')
        self.assertNotIn('cost_nano',observer.records[0])
        self.assertEqual(observer.allowance.snapshot()['used'],observer.records[0]['reserved_nano'])

    def test_complete_matrix_is_reproducible_and_keeps_every_role_unreviewed(self):
        from tests.benchmark_transport import CampaignObserver
        from tests.reviewer_cases import CASES,policies
        from tests.reviewer_benchmark import run_campaign,summarize_campaign
        from tests.operation_timing_harness import SyntheticDefenseCase,SyntheticClock,_SyntheticProvider
        providers={case.id:_SyntheticProvider(SyntheticDefenseCase(case.id,'synthetic-study.md',case.files[0].content,
            case.answers[0],defense_type='mixed' if case.mixed else 'research'),SyntheticClock(1000),1) for case in CASES}
        observer=CampaignObserver('matrix',5_000_000_000,policies()['current'],
            transport_factory=lambda:httpx.MockTransport(lambda request:providers[observer.context['case_id']](request)))
        records,quality,active=run_campaign(observer,evidence='mocked')
        self.assertEqual(active,0)
        report=summarize_campaign(records)
        self.assertEqual(report['provider_gate'],'unreviewed')
        for condition in policies():
            self.assertEqual(report['conditions'][condition]['target']['attempted'],16)
            self.assertEqual(report['conditions'][condition]['case_ids'],[case.id for case in sorted(CASES,key=lambda c:c.id)])
        self.assertEqual(len(quality),60)
        self.assertEqual({r['evidence'] for r in records},{'mocked'})
        self.assertNotIn(CASES[0].answers[0],json.dumps(records+quality))


if __name__ == '__main__':
    unittest.main()

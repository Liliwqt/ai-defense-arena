"""Same-route Qwen reasoning comparison; external providers stay mocked."""
import json
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

import httpx

from tests.test_openrouter_questions import IsolatedAllowanceTests, stream_response


class ImpactReasoningProbeTests(IsolatedAllowanceTests):
    def test_same_prompts_route_and_output_with_only_reasoning_changed(self):
        from tests.impact_route_probe import prepare_reasoning_probes, reasoning_measurement_plan
        probes = prepare_reasoning_probes()
        self.assertEqual(len(probes), 4)
        for case in ('quantitative-en', 'qualitative-bisaya'):
            current, disabled = [p for p in probes if p['case_id']==case]
            self.assertEqual(current['condition'],'reasoning-current')
            self.assertEqual(disabled['condition'],'reasoning-disabled')
            self.assertEqual(current['body']['reasoning'], {'max_tokens':2048})
            self.assertEqual(disabled['body']['reasoning'], {'enabled':False})
            self.assertEqual({k:v for k,v in current['body'].items() if k!='reasoning'},
                             {k:v for k,v in disabled['body'].items() if k!='reasoning'})
            self.assertEqual(current['body']['provider'], disabled['body']['provider'])
            self.assertEqual(current['body']['provider']['ignore'],['alibaba/us-east-1'])
            self.assertEqual(current['body']['max_tokens'],8192)
            self.assertEqual(current['policy'], disabled['policy'])
        plan = reasoning_measurement_plan(probes)
        self.assertEqual(plan['protocol']['reasoning_conditions'],{
            'reasoning-current':{'max_tokens':2048}, 'reasoning-disabled':{'enabled':False}})
        self.assertEqual(plan['runs'][1]['request_reasoning'],{'enabled':False})
        self.assertEqual(plan,reasoning_measurement_plan(prepare_reasoning_probes()))

    def test_plan_mode_never_constructs_real_transport_or_spends(self):
        from tests.impact_route_probe import main
        with redirect_stdout(StringIO()) as output, patch('httpx.HTTPTransport', side_effect=AssertionError('Offline plan')):
            self.assertEqual(main(['--plan','--reasoning-comparison']),0)
        plan=json.loads(output.getvalue())
        self.assertEqual(plan['maximum_requests'],4)
        self.assertEqual(plan['provider_gate'],'not-run')
        self.assertEqual(plan['ordinary_bound_nano'],89341200)

    def test_actual_request_seam_sends_disabled_reasoning_and_keeps_condition(self):
        from tests.benchmark_transport import CampaignObserver
        from tests.impact_route_probe import prepare_reasoning_probes,run_probe
        probe=prepare_reasoning_probes()[1]
        captured=[]
        def respond(request):
            captured.append(json.loads(request.content))
            return stream_response({'result':{'question':'How will you evaluate the bounded contribution?',
                'lead_in':'','source_file':1,'evidence_line':6},'lookup':None})
        observer=CampaignObserver('disabled-reasoning',100_000_000,probe['policy'],
            transport_factory=lambda:httpx.MockTransport(respond))
        outcome=run_probe(probe,observer,'offline-key')
        self.assertEqual(outcome['condition'],'reasoning-disabled')
        self.assertEqual(outcome['outcome'],'succeeded')
        records,active=observer.snapshot()
        self.assertEqual(active,0)
        self.assertEqual(len(captured),1)
        self.assertEqual(captured[0]['reasoning'],{'enabled':False})
        self.assertEqual(records[0]['condition'],'reasoning-disabled')
        self.assertNotIn('reasoning_tokens',records[0])  # Missing metric is not zero.

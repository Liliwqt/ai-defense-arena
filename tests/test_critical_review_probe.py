"""Targeted Critical replay uses synthetic retained state, never a new defense."""
import json
from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
from pathlib import Path
import tempfile
from unittest.mock import patch

import httpx

from tests.test_openrouter_questions import IsolatedAllowanceTests, stream_response


class CriticalReviewProbeTests(IsolatedAllowanceTests):
    def test_reconstruction_retains_research_citation_context_from_original_sources(self):
        from tests.critical_review_probe import replay_inputs
        _, _, session, _, _ = replay_inputs()
        citation = session.turns[-1].question
        self.assertEqual(citation.evidence_kind, 'research_text')
        self.assertIn('Impact:', citation.evidence_before)
        self.assertIn('Setting:', citation.evidence_after)
        self.assertIn('no effectiveness is proven', citation.evidence_text)

    def test_execute_rejects_unpinned_database_before_dispatch_or_output_creation(self):
        from tests.critical_review_probe import main
        with tempfile.TemporaryDirectory() as folder, redirect_stderr(StringIO()) as error, \
                patch('httpx.HTTPTransport', side_effect=AssertionError('No inference')):
            output = Path(folder)/'uncreated'
            with self.assertRaises(SystemExit):
                main(['--execute', '--max-usd', '0.05', '--output', str(output)])
            self.assertFalse(output.exists())
            self.assertIn('prepared isolated launcher', error.getvalue())

    def test_plan_is_reproducible_and_does_not_use_real_transport(self):
        from tests.critical_review_probe import main
        outputs = []
        with patch('httpx.HTTPTransport', side_effect=AssertionError('No paid plan call')):
            for _ in range(2):
                with redirect_stdout(StringIO()) as output:
                    self.assertEqual(main(['--plan']), 0)
                outputs.append(json.loads(output.getvalue()))
        self.assertEqual(outputs[0], outputs[1])
        self.assertEqual(outputs[0]['maximum_requests'], 2)
        self.assertEqual(outputs[0]['model'], 'z-ai/glm-5.3-flash')
        self.assertEqual(outputs[0]['reasoning'], {'effort': 'low'})
        self.assertEqual(outputs[0]['provider_gate'], 'not-run')

    def test_rejected_review_reports_only_safe_code_without_replaying_earlier_stages(self):
        from tests.critical_review_probe import prepare_probe, run_probe
        from tests.benchmark_transport import CampaignObserver
        probe = prepare_probe()
        received = []
        def respond(request):
            received.append(json.loads(request.content))
            return stream_response({'result': {'action': 'answer', 'clarification': 'synthetic-private-marker',
                'probe': None, 'assessment': None, 'panelist': None, 'topic_id': None, 'is_follow_up': False},
                'lookup': None})
        observer = CampaignObserver('critical-probe', 100_000_000, probe['policy'],
            transport_factory=lambda: httpx.MockTransport(respond))
        result = run_probe(probe, observer, 'offline-fixture', 0)
        self.assertEqual(result['failure_code'], 'response_schema_invalid')
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0], probe['body'])
        self.assertEqual(result['outcome'], 'failed')
        self.assertNotIn('synthetic-private-marker', json.dumps(result))
        self.assertEqual(observer.snapshot()[1], 0)

    def test_valid_decision_and_lookup_never_dispatch_a_next_question(self):
        from tests.critical_review_probe import prepare_probe, run_probe
        from tests.benchmark_transport import CampaignObserver
        probe = prepare_probe()
        normal = {'action': 'answer', 'clarification': None, 'probe': None,
            'assessment': {'turn': 6, 'topic_id': 'topic-4', 'status': 'needs clarification',
                           'reason': 'The explanation does not name the selection assumptions.'},
            'panelist': 'Critical Judge', 'topic_id': 'topic-4', 'is_follow_up': True}
        for name, body, expected in (
                ('valid', {'result': normal, 'lookup': None}, 'succeeded'),
                ('lookup', {'result': None, 'lookup': {'query': 'selection assumptions', 'source_files': [1]}},
                 'lookup_requested')):
            with self.subTest(name=name):
                received = []
                def respond(request):
                    received.append(request)
                    return stream_response(body)
                observer = CampaignObserver('critical-'+name, 100_000_000, probe['policy'],
                    transport_factory=lambda: httpx.MockTransport(respond))
                result = run_probe(probe, observer, 'offline-fixture', 0)
                self.assertEqual(result['outcome'], expected)
                self.assertEqual(len(received), 1)
                if name == 'valid':
                    self.assertEqual(result['validated_action'], 'answer')

    def test_replay_parses_the_same_bound_assessment_schema_it_sends(self):
        from tests.critical_review_probe import prepare_probe, run_probe
        from tests.benchmark_transport import CampaignObserver
        probe = prepare_probe()
        normal = {'action': 'answer', 'clarification': None, 'probe': None,
            'assessment': {'turn': 7, 'topic_id': 'topic-4', 'status': 'needs clarification',
                           'reason': 'The assumptions need explanation.'},
            'panelist': 'Critical Judge', 'topic_id': 'topic-4', 'is_follow_up': True}
        observer = CampaignObserver('critical-bound-schema', 100_000_000, probe['policy'],
            transport_factory=lambda: httpx.MockTransport(lambda request:
                stream_response({'result': normal, 'lookup': None})))
        result = run_probe(probe, observer, 'offline-fixture', 0)
        self.assertEqual(result['failure_code'], 'response_schema_invalid')
        self.assertEqual(result['outcome'], 'failed')
        self.assertEqual(len(observer.records), 1)

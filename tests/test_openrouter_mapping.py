"""Room-to-provider mapping contract; HTTP, Google and payments are offline."""

import json
import os
from pathlib import Path
import tempfile
from threading import Event
import unittest
from unittest.mock import patch

import httpx

from tests import test_research_plan as maps

HTTPClient = httpx.Client


def stream_response(output, *, usage=None):
    events = [
        {"choices": [{"index": 0, "delta": {"content": json.dumps(output)}, "finish_reason": None}]},
        {"choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]},
        {"choices": [], "usage": usage if usage is not None else {"prompt_tokens": 500, "completion_tokens": 300, "cost": 0.0005}},
    ]
    return httpx.Response(200, text=''.join('data: ' + json.dumps(event) + '\n\n' for event in events) + 'data: [DONE]\n\n')


class OpenRouterMappingContractTests(unittest.TestCase):
    """Generation-to-mocked-HTTP seam; no ASGI server or network sockets."""

    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        env = patch.dict(os.environ, {
            'DATABASE_URL': '',
            'PAYMONGO_TEST_DB_PATH': str(Path(folder.name) / 'allowances.sqlite3'),
            'OPENROUTER_API_KEY': 'offline-router-key',
            'OPENROUTER_PREPARATION_USD': '.75',
            'OPENROUTER_MAPPING_MAX_OUTPUT_TOKENS': '65536',
        })
        env.start()
        self.addCleanup(env.stop)

    def test_new_mapping_reduces_reasoning_while_retaining_grounded_material_and_policy(self):
        from backend.openrouter_mapping import MappingClient, MODEL
        calls = []
        def provider(request):
            calls.append(json.loads(request.content))
            return stream_response(maps.draft())
        def client(*args, **kwargs):
            return HTTPClient(transport=httpx.MockTransport(provider))
        mapping = MappingClient('fast-preparation', 'owner')
        files = [maps.ProjectFile('study.md', maps.PAPER, 'research_text')]
        with patch('httpx.Client', side_effect=client):
            plan = maps.generate_research_plan(files, mapping.api_key, MODEL, client=mapping)
        self.assertEqual(calls[0]['reasoning'], {'effort': 'low', 'exclude': True})
        self.assertEqual(calls[0]['model'], 'z-ai/glm-5.3-flash')
        self.assertEqual(calls[0]['provider']['only'], ['deepinfra'])
        self.assertIn(maps.PAPER.splitlines()[3], calls[0]['messages'][1]['content'])
        self.assertEqual(plan.topics[0].references[0].evidence_text, maps.PAPER.splitlines()[3])
        with patch.dict(os.environ, {'OPENROUTER_MAPPING_REASONING_EFFORT': 'high',
                                     'OPENROUTER_MAPPING_MODEL': 'deepseek/deepseek-v4.1-flash-1017',
                                     'OPENROUTER_MAPPING_PROVIDER': 'wafer'}):
            reopened = MappingClient('fast-preparation', 'owner')
        with patch('httpx.Client', side_effect=client):
            maps.generate_research_plan(files, reopened.api_key, MODEL, client=reopened)
        self.assertEqual(calls[1]['reasoning'], calls[0]['reasoning'])
        self.assertEqual(calls[1]['model'], 'z-ai/glm-5.3-flash')
        self.assertEqual(calls[1]['provider']['only'], ['deepinfra'])

    def test_mapping_provider_override_applies_only_to_new_standard_preparations(self):
        from backend.openrouter_mapping import MappingClient, MappingPolicy
        for provider in ('deepinfra', 'wafer', 'z-ai', 'auto'):
            with self.subTest(provider=provider), patch.dict(os.environ, {'OPENROUTER_MAPPING_PROVIDER': provider}):
                policy = MappingClient('route-' + provider, 'owner').policy
                self.assertEqual(policy.provider_only, None if provider == 'auto' else [provider])
                self.assertEqual(MappingPolicy.configured('free').provider_only, ['atlas-cloud'])
        for provider in ('', 'private-invalid-setting', 'deepinfra,wafer'):
            with self.subTest(provider=provider), patch.dict(os.environ, {'OPENROUTER_MAPPING_PROVIDER': provider}), \
                 patch('httpx.Client') as upstream:
                with self.assertRaisesRegex(maps.QuestionGenerationError, 'OPENROUTER_MAPPING_PROVIDER') as raised:
                    MappingClient('invalid-provider', 'owner')
                self.assertNotIn('private-invalid-setting', str(raised.exception))
                upstream.assert_not_called()

    def test_retained_legacy_mapping_keeps_high_reasoning_and_explicit_high_is_supported(self):
        from dataclasses import asdict
        from backend.openrouter_mapping import MappingClient, MappingPolicy, MODEL
        from backend.provider_allowance import ProviderAllowance
        legacy = asdict(MappingPolicy())
        legacy.pop('reasoning_effort')
        ProviderAllowance('old-preparation', 'owner').establish(legacy['allowance_nano'], legacy)
        calls = []
        def provider(request):
            calls.append(json.loads(request.content))
            return stream_response(maps.draft())
        def client(*args, **kwargs):
            return HTTPClient(transport=httpx.MockTransport(provider))
        mapping = MappingClient('old-preparation', 'owner')
        with patch('httpx.Client', side_effect=client):
            maps.generate_research_plan([maps.ProjectFile('study.md', maps.PAPER, 'research_text')],
                mapping.api_key, MODEL, client=mapping)
        self.assertEqual(calls[0]['reasoning'], {'effort': 'high', 'exclude': True})
        self.assertEqual(calls[0]['model'], 'deepseek/deepseek-v4.1-flash-1017')
        legacy.pop('model')
        ProviderAllowance('old-preparation-without-model', 'owner').establish(legacy['allowance_nano'], legacy)
        self.assertEqual(MappingClient('old-preparation-without-model', 'owner').policy.model,
                         'deepseek/deepseek-v4.1-flash-1017')
        with patch.dict(os.environ, {'OPENROUTER_MAPPING_REASONING_EFFORT': 'high'}):
            self.assertEqual(MappingClient('new-high-preparation', 'owner').mapping_reasoning, {'effort': 'high'})
        for invalid in ('medium', 'none', '', '2000'):
            with self.subTest(invalid=invalid), patch.dict(os.environ, {'OPENROUTER_MAPPING_REASONING_EFFORT': invalid}):
                with self.assertRaisesRegex(maps.QuestionGenerationError, 'OPENROUTER_MAPPING_REASONING_EFFORT'):
                    MappingClient('invalid-preparation', 'owner')
        self.assertIsNone(ProviderAllowance('invalid-preparation', 'owner').policy())

    def test_explicit_model_rollback_changes_only_new_preparations(self):
        from backend.openrouter_mapping import MappingClient, MODEL
        from backend.provider_allowance import ProviderAllowance
        calls = []
        def provider(request):
            calls.append(json.loads(request.content))
            return stream_response(maps.draft())
        def client(*args, **kwargs):
            return HTTPClient(transport=httpx.MockTransport(provider))
        with patch.dict(os.environ, {'OPENROUTER_MAPPING_MODEL': 'deepseek/deepseek-v4.1-flash-1017'}):
            mapping = MappingClient('rollback-preparation', 'owner')
        with patch('httpx.Client', side_effect=client):
            maps.generate_research_plan([maps.ProjectFile('study.md', maps.PAPER, 'research_text')],
                mapping.api_key, MODEL, client=mapping)
        self.assertEqual(calls[0]['model'], 'deepseek/deepseek-v4.1-flash-1017')
        for invalid in ('openrouter/auto', 'z-ai/glm-5.3-flash:free', ''):
            with self.subTest(invalid=invalid), patch.dict(os.environ, {'OPENROUTER_MAPPING_MODEL': invalid}), \
                 patch('httpx.Client') as upstream:
                with self.assertRaisesRegex(maps.QuestionGenerationError, 'OPENROUTER_MAPPING_MODEL'):
                    MappingClient('unsupported-preparation', 'owner')
                upstream.assert_not_called()
        self.assertIsNone(ProviderAllowance('unsupported-preparation', 'owner').policy())

    def test_mapping_can_finish_after_the_previous_ninety_second_cutoff(self):
        from backend.openrouter_mapping import MappingClient, MODEL
        elapsed = [0]
        response = stream_response(maps.draft())
        class SlowStream(httpx.SyncByteStream):
            def __iter__(self):
                elapsed[0] = 100
                yield response.content
        def client(*args, **kwargs):
            return HTTPClient(transport=httpx.MockTransport(
                lambda request: httpx.Response(200, stream=SlowStream())))
        mapping = MappingClient('slow-preparation', 'owner')
        with patch('backend.openrouter_mapping.monotonic', side_effect=lambda: elapsed[0]), \
             patch('httpx.Client', side_effect=client):
            plan = maps.generate_research_plan(
                [maps.ProjectFile('study.md', maps.PAPER, 'research_text')],
                mapping.api_key, MODEL, client=mapping)
        self.assertEqual(len(plan.topics), 4)

    def test_mapping_deadline_remains_bounded_and_preserves_unsettled_cost(self):
        from backend.openrouter_mapping import MappingClient, MODEL
        elapsed = [0]
        calls = []
        class SlowStream(httpx.SyncByteStream):
            def __iter__(self):
                elapsed[0] = 300
                yield b'data: [DONE]\n\n'
        def provider(request):
            calls.append(request)
            return httpx.Response(200, stream=SlowStream())
        def client(*args, **kwargs):
            return HTTPClient(transport=httpx.MockTransport(provider))
        mapping = MappingClient('expired-preparation', 'owner')
        with patch('backend.openrouter_mapping.monotonic', side_effect=lambda: elapsed[0]), \
             patch('httpx.Client', side_effect=client):
            with self.assertRaisesRegex(maps.QuestionGenerationError, '300-second time limit'):
                maps.generate_research_plan(
                    [maps.ProjectFile('study.md', maps.PAPER, 'research_text')],
                    mapping.api_key, MODEL, client=mapping)
        self.assertEqual(len(calls), 1)
        self.assertGreater(mapping.allowance.snapshot()['used'], 0)

    def test_cancelled_mapping_does_not_dispatch(self):
        from backend.openrouter_mapping import MappingClient, MODEL
        mapping = MappingClient('cancelled-preparation', 'owner', stopped=lambda: True)
        with patch('httpx.Client') as client:
            with self.assertRaisesRegex(maps.QuestionGenerationError, '^OpenRouter mapping was cancelled\\.$'):
                maps.generate_research_plan(
                    [maps.ProjectFile('study.md', maps.PAPER, 'research_text')],
                    mapping.api_key, MODEL, client=mapping)
        client.assert_not_called()

    def test_operator_timeout_is_bounded_and_independent_of_saved_model_policy(self):
        from backend.openrouter_mapping import MappingClient, mapping_timeout_seconds
        first = MappingClient('retained-preparation', 'owner')
        for value in ('30', '180', '600'):
            with self.subTest(value=value), patch.dict(os.environ, {'OPENROUTER_MAPPING_TIMEOUT_SECONDS': value}):
                self.assertEqual(mapping_timeout_seconds(), int(value))
                self.assertEqual(MappingClient('retained-preparation', 'owner').policy, first.policy)
        for value in ('29', '601', 'nan', ''):
            with self.subTest(value=value), patch.dict(os.environ, {'OPENROUTER_MAPPING_TIMEOUT_SECONDS': value}):
                with self.assertRaisesRegex(maps.QuestionGenerationError, 'OPENROUTER_MAPPING_TIMEOUT_SECONDS'):
                    mapping_timeout_seconds()

    def test_conflicting_stream_cost_receipts_freeze_further_dispatch(self):
        from backend.openrouter_mapping import MappingClient, MODEL
        calls = []
        def provider(request):
            calls.append(request)
            response = stream_response(maps.draft())
            content = response.text.replace('data: [DONE]',
                'data: {"choices":[],"usage":{"cost":0}}\n\ndata: [DONE]')
            return httpx.Response(200, text=content)
        def client(*args, **kwargs):
            return HTTPClient(transport=httpx.MockTransport(provider))
        mapping = MappingClient('preparation', 'owner')
        with patch('httpx.Client', side_effect=client):
            for _ in range(2):
                with self.assertRaisesRegex(maps.QuestionGenerationError, 'cost evidence|operator review'):
                    maps.generate_research_plan([maps.ProjectFile('study.md', maps.PAPER, 'research_text')],
                        mapping.api_key, MODEL, client=mapping)
        self.assertEqual(len(calls), 1)

    def test_multilingual_source_reaches_provider_without_escape_expansion_rejection(self):
        from backend.openrouter_mapping import MappingClient, MODEL
        source = maps.PAPER + ('é' * 180000)
        calls = []
        def provider(request):
            calls.append(json.loads(request.content))
            return stream_response(maps.draft())
        def client(*args, **kwargs):
            return HTTPClient(transport=httpx.MockTransport(provider))
        mapping = MappingClient('preparation', 'owner')
        with patch('httpx.Client', side_effect=client):
            plan = maps.generate_research_plan([maps.ProjectFile('study.md', source, 'research_text')],
                mapping.api_key, MODEL, client=mapping)
        self.assertEqual(len(plan.topics), 4)
        self.assertIn('é' * 180000, calls[0]['messages'][1]['content'])


class OpenRouterMappingProtocolTests(unittest.TestCase):
    def setUp(self):
        maps.ResearchPlanRoomTests.setUp(self)
        gates = patch.multiple('backend.defense_availability', CODE_ONLY_AVAILABLE=False, VOICE_AVAILABLE=False)
        gates.start()
        self.addCleanup(gates.stop)
    create = maps.ResearchPlanRoomTests.create
    hello = maps.ResearchPlanRoomTests.hello
    until = maps.ResearchPlanRoomTests.until

    def map_state(self, socket, action='prepare_research_plan'):
        socket.send_json({'type': action})
        for _ in range(25):
            state = socket.receive_json()['state']
            if state['research_planning_status'] in {'ready', 'failed'}:
                return state
        self.fail('No terminal mapping state')

    def test_uncertain_cost_and_reconnect_cannot_reset_preparation_allowance(self):
        calls = []
        def provider(request):
            calls.append(json.loads(request.content))
            return stream_response(maps.draft(), usage={})
        def client(*args, **kwargs):
            return HTTPClient(transport=httpx.MockTransport(provider))
        host = self.create()
        with patch.dict(os.environ, {'OPENROUTER_PREPARATION_USD': '0.1'}), \
             patch('httpx.Client', side_effect=client):
            with self.client.websocket_connect(f"/ws/{host['room_code']}") as socket:
                self.hello(socket, host['player_token'])
                self.assertEqual(self.map_state(socket)['research_planning_status'], 'ready')
            with patch.dict(os.environ, {'OPENROUTER_PREPARATION_USD': '10', 'OPENROUTER_MAPPING_MAX_OUTPUT_TOKENS':'1024'}), \
                 self.client.websocket_connect(f"/ws/{host['room_code']}") as socket:
                previous = self.hello(socket, host['player_token'])
                state = self.map_state(socket)
                self.assertEqual(state['research_planning_status'], 'failed')
                self.assertIn('allowance', state['research_plan_error'])
                self.assertEqual(len(calls), 1)
                self.assertEqual(state['research_plan'], previous['research_plan'])
                self.assertFalse(state['research_plan_approved'])

    def test_known_usage_allows_remap_with_the_original_settings(self):
        calls = []
        def provider(request):
            calls.append(json.loads(request.content))
            return stream_response(maps.draft())
        def client(*args, **kwargs):
            return HTTPClient(transport=httpx.MockTransport(provider))
        host = self.create()
        with patch.dict(os.environ, {'OPENROUTER_PREPARATION_USD': '.02', 'OPENROUTER_MAPPING_MAX_OUTPUT_TOKENS':'2048'}), \
             patch('httpx.Client', side_effect=client), \
             self.client.websocket_connect(f"/ws/{host['room_code']}") as socket:
            self.hello(socket, host['player_token'])
            self.assertEqual(self.map_state(socket)['research_planning_status'], 'ready')
            with patch.dict(os.environ, {'OPENROUTER_PREPARATION_USD':'invalid', 'OPENROUTER_MAPPING_MAX_OUTPUT_TOKENS':'invalid',
                                         'AI_MAPPING_REASONING_EFFORT':'broken-legacy-setting'}):
                self.assertEqual(self.map_state(socket)['research_planning_status'], 'ready')
        self.assertEqual([call['max_tokens'] for call in calls], [2048,2048])

    def test_old_code_room_cannot_start_restart_or_retry_and_keeps_its_transcript(self):
        from backend import game_server
        host = self.create()
        room = game_server.rooms[host['room_code']]
        room.defense_type = 'code'  # Existing retained room fixture, not new creation.
        with self.client.websocket_connect(f"/ws/{host['room_code']}") as socket:
            before = self.hello(socket, host['player_token'])
            for action in ('start','restart','retry'):
                socket.send_json({'type':action, 'confirm_cost':True})
                event = socket.receive_json()
                self.assertEqual(event['type'], 'error')
                self.assertIn('temporarily unavailable', event['message'])
            self.assertEqual(room.run_id, None)
            self.assertEqual(before['turns'], [])

    def test_two_clients_see_grounded_streaming_progress_before_final_confirmation(self):
        release = Event()
        self.addCleanup(release.set)
        complete = json.dumps(maps.draft())
        split = complete.index('}, {') + 1
        def event(text):
            return ('data: ' + json.dumps({'choices':[{'index':0,'delta':{'content':text},'finish_reason':None}]}) + '\n\n').encode()
        class Bytes(httpx.SyncByteStream):
            def __iter__(self):
                yield event(complete[:split])
                if not release.wait(5):
                    raise RuntimeError('Fixture did not release')
                yield event(complete[split:])
                yield b'data: {"choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}\n\ndata: [DONE]\n\n'
        def client(*args, **kwargs):
            return HTTPClient(transport=httpx.MockTransport(lambda request:httpx.Response(200,stream=Bytes())))
        host = self.create()
        guest = self.client.post(f"/api/rooms/{host['room_code']}/join",json={'name':'Guest'}).json()
        with patch('httpx.Client', side_effect=client), \
             self.client.websocket_connect(f"/ws/{host['room_code']}") as h, \
             self.client.websocket_connect(f"/ws/{host['room_code']}") as g:
            self.hello(h,host['player_token']); self.hello(g,guest['player_token'])
            h.send_json({'type':'prepare_research_plan'})
            for socket in (h,g):
                for _ in range(12):
                    state = socket.receive_json()['state']
                    if (state.get('research_plan_progress') or {}).get('topics'):
                        break
                self.assertEqual(len(state['research_plan_progress']['topics']),1)
                self.assertFalse(state['research_plan_approved'])
            release.set()
            ready = [self.until(socket,research_planning_status='ready') for socket in (h,g)]
            self.assertEqual(ready[0]['research_plan'],ready[1]['research_plan'])

    def test_new_code_only_creation_is_temporarily_disabled(self):
        result = self.client.post('/api/rooms', data={'host_name': 'Host', 'defense_type': 'code'},
            files=[('files', ('app.py', b'print(1)', 'text/x-python'))])
        self.assertEqual(result.status_code, 503)
        self.assertIn('temporarily unavailable', result.json()['detail'])

    def test_standard_capacity_failure_keeps_paid_route_and_uploads_on_retry(self):
        from backend import game_server
        calls = []
        def provider(request):
            calls.append(json.loads(request.content))
            return httpx.Response(429, json={'error': {'code': 429,
                'message': 'PRIVATE-PROVIDER-PAYLOAD',
                'metadata': {'limit_source': 'upstream_provider_shared_pool'}}})
        def client(*args, **kwargs):
            return HTTPClient(transport=httpx.MockTransport(provider))
        host = self.create()
        room = game_server.rooms[host['room_code']]
        uploads = list(room.files)
        with patch.dict(os.environ, {'OPENROUTER_MAPPING_MODEL': 'z-ai/glm-5.3-flash'}), \
             patch('httpx.Client', side_effect=client), \
             self.client.websocket_connect(f"/ws/{host['room_code']}") as socket:
            self.hello(socket, host['player_token'])
            for action in ('prepare_research_plan', 'retry_research_plan'):
                state = self.map_state(socket, action)
                self.assertEqual(state['research_planning_status'], 'failed')
                self.assertEqual(state['practice_tier'], 'standard')
                self.assertIn('upstream provider', state['research_plan_error'])
                self.assertNotIn('free-model', state['research_plan_error'])
                self.assertNotIn('PRIVATE-PROVIDER-PAYLOAD', state['research_plan_error'])
                self.assertIsNone(state['panelist_activity'])
                self.assertEqual(room.files, uploads)
        self.assertEqual(len(calls), 2)
        self.assertTrue(all(body['model'] == 'z-ai/glm-5.3-flash' for body in calls))
        self.assertTrue(all(body['provider']['only'] == ['deepinfra'] for body in calls))
        self.assertTrue(all(body['provider']['max_price']['prompt'] > 0 for body in calls))

    def test_provider_error_is_redacted_and_never_falls_back(self):
        calls=[]
        def provider(request):
            calls.append(str(request.url))
            return httpx.Response(401,json={'error':{'message':'PRIVATE-PROVIDER-PAYLOAD'}})
        def client(*args,**kwargs):
            return HTTPClient(transport=httpx.MockTransport(provider))
        host=self.create()
        with patch('httpx.Client',side_effect=client), self.client.websocket_connect(f"/ws/{host['room_code']}") as socket:
            self.hello(socket,host['player_token'])
            state=self.map_state(socket)
        self.assertEqual(state['research_planning_status'],'failed')
        self.assertIn('OpenRouter',state['research_plan_error'])
        self.assertNotIn('PRIVATE-PROVIDER-PAYLOAD',state['research_plan_error'])
        self.assertEqual(calls,['https://openrouter.ai/api/v1/chat/completions'])

    def test_accepted_multilingual_paper_is_not_rejected_for_json_escape_expansion(self):
        text = maps.PAPER + ('é' * 180000)
        response = self.client.post('/api/rooms',data={'host_name':'Host','defense_type':'research'},
            files=[('research_files',('study.md',text.encode(),'text/markdown'))])
        self.assertEqual(response.status_code,201,response.text)
        host=response.json()
        calls=[]
        def provider(request):
            calls.append(json.loads(request.content))
            return stream_response(maps.draft())
        def client(*args,**kwargs):
            return HTTPClient(transport=httpx.MockTransport(provider))
        with patch('httpx.Client',side_effect=client),self.client.websocket_connect(f"/ws/{host['room_code']}") as socket:
            self.hello(socket,host['player_token'])
            state=self.map_state(socket)
            self.assertEqual(state['research_planning_status'],'ready',state.get('research_plan_error'))
        self.assertIn('é'*180000,calls[0]['messages'][1]['content'])

    def test_truncated_stream_keeps_full_cost_bound_and_cannot_approve_or_dispatch_again(self):
        calls=[]
        def provider(request):
            calls.append(request)
            event={'choices':[{'index':0,'delta':{'content':json.dumps(maps.draft())},'finish_reason':'length'}]}
            return httpx.Response(200,text='data: '+json.dumps(event)+'\n\ndata: [DONE]\n\n')
        def client(*args,**kwargs):
            return HTTPClient(transport=httpx.MockTransport(provider))
        host=self.create()
        with patch.dict(os.environ,{'OPENROUTER_PREPARATION_USD':'.1'}),patch('httpx.Client',side_effect=client), \
             self.client.websocket_connect(f"/ws/{host['room_code']}") as socket:
            self.hello(socket,host['player_token'])
            state=self.map_state(socket)
            self.assertEqual(state['research_planning_status'],'failed')
            self.assertIsNone(state['research_plan'])
            self.assertFalse(state['research_plan_approved'])
            state=self.map_state(socket,'retry_research_plan')
            self.assertIn('allowance',state['research_plan_error'])
        self.assertEqual(len(calls),1)

    def test_old_speech_configuration_cannot_enable_the_direct_provider(self):
        host = self.create()
        with patch.dict(os.environ, {'VOICE_PILOT_ENABLED':'1', 'OPENAI_SPEECH_API_KEY':'offline-speech-key'}), \
             self.client.websocket_connect(f"/ws/{host['room_code']}") as socket:
            state = self.hello(socket, host['player_token'])
            self.assertFalse(state['voice']['enabled'])

    def test_insufficient_preparation_allowance_does_not_dispatch_or_lose_material(self):
        calls = []
        upstream = httpx.Client(transport=httpx.MockTransport(lambda request: (
            calls.append(request) or stream_response(maps.draft()))))
        self.addCleanup(upstream.close)
        host = self.create()
        with patch.dict(os.environ, {'OPENROUTER_API_KEY': 'offline-router-key', 'OPENROUTER_PREPARATION_USD': '0.000001'}), \
             patch('httpx.Client', return_value=upstream), \
             self.client.websocket_connect(f"/ws/{host['room_code']}") as socket:
            self.hello(socket, host['player_token'])
            socket.send_json({'type': 'prepare_research_plan'})
            for _ in range(20):
                state = socket.receive_json()['state']
                if state['research_planning_status'] in {'ready', 'failed'}:
                    break
            self.assertEqual(state['research_planning_status'], 'failed')
            self.assertIn('allowance', state['research_plan_error'])
            self.assertEqual(state['files'], ['study.md'])
            self.assertEqual(calls, [])

    def test_explicit_mapping_uses_assigned_openrouter_route_and_retains_grounded_review(self):
        calls = []

        def provider(request):
            calls.append(request)
            return stream_response(maps.draft())

        upstream = httpx.Client(transport=httpx.MockTransport(provider))
        self.addCleanup(upstream.close)
        host = self.create()
        with patch.dict(os.environ, {'OPENROUTER_API_KEY': 'offline-router-key'}), \
             patch('httpx.Client', return_value=upstream), \
             self.client.websocket_connect(f"/ws/{host['room_code']}") as socket:
            state = self.hello(socket, host['player_token'])
            self.assertEqual(calls, [])
            socket.send_json({'type': 'prepare_research_plan'})
            for _ in range(20):
                state = socket.receive_json()['state']
                if state['research_planning_status'] in {'ready', 'failed'}:
                    break
            self.assertEqual(state['research_planning_status'], 'ready', state.get('research_plan_error'))
            self.assertEqual(len(calls), 1)
            request = calls[0]
            self.assertEqual(str(request.url), 'https://openrouter.ai/api/v1/chat/completions')
            self.assertEqual(request.headers['authorization'], 'Bearer offline-router-key')
            body = json.loads(request.content)
            self.assertEqual(body['model'], 'z-ai/glm-5.3-flash')
            self.assertEqual(body['reasoning']['effort'], 'low')
            self.assertFalse(body['provider']['allow_fallbacks'])
            self.assertTrue(body['provider']['require_parameters'])
            self.assertGreater(body['max_tokens'], 0)
            self.assertEqual(body['response_format']['type'], 'json_schema')
            self.assertEqual(state['research_plan']['topics'][0]['references'][0]['evidence_text'], maps.PAPER.splitlines()[3])
            self.assertFalse(state['research_plan_approved'])
            self.assertEqual(state['turns'], [])
            self.assertFalse(state['voice']['enabled'])

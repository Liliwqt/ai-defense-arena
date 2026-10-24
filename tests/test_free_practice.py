"""Free practice: real disposable ledgers/room protocol, provider HTTP mocked."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
import json
import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import httpx

from backend import account_store, game_server
from backend.live_store import LiveStore
from backend.openrouter_mapping import MappingClient, MappingPolicy
from backend.openrouter_questions import RunQuestionPolicy, establish_run_allowance
from backend.openrouter_stream import payload
from backend.practice_tiers import FREE_MODEL, FREE_CONTEXT_TOKENS, RETIRED_FREE_MODEL
from backend.provider_allowance import ProviderAllowance, AllowanceError
from backend.question_generator import QuestionGenerationError, QuestionDraft
from backend.research_plan import ResearchPlanDraft
from backend.rooms.commands import CatchUpDeadline
from backend.timed_turn import VOTE_MS
from tests.test_openrouter_questions import IsolatedAllowanceTests, HTTPClient, stream_response
from tests.test_openrouter_streamlit import SyntheticRouter, APP, button
from tests import test_openrouter_checkpoint as checkpoint
from tests import test_research_plan as maps


class FreePolicyTests(IsolatedAllowanceTests):
    def test_mapping_selects_a_free_route_compatible_with_no_collection(self):
        calls = []
        def provider(request):
            body = json.loads(request.content)
            calls.append(body)
            if body['model'] == 'nvidia/nemotron-3.5-super-vl:free' and body['provider']['data_collection'] == 'deny':
                return httpx.Response(404, json={'error': {'code': 404,
                    'message': 'No endpoints found matching your data policy.'}})
            self.assertEqual(body['model'], 'dots-studio/dots-3-note-preview:free')
            self.assertEqual(body['provider']['only'], ['atlas-cloud'])
            self.assertEqual(body['provider']['data_collection'], 'deny')
            self.assertEqual(body['provider']['max_price'], {'prompt': 0, 'completion': 0, 'request': 0})
            return stream_response(maps.draft(), usage={'cost': 0})
        with patch('httpx.Client', side_effect=lambda **kw: HTTPClient(transport=httpx.MockTransport(provider))):
            client = MappingClient('compatible-free-map', 'owner', tier='free')
            result = client.parse(input=[], text_format=ResearchPlanDraft)
        self.assertEqual(len(result.output_parsed.topics), 4)
        self.assertEqual(len(calls), 1)

    def test_free_policy_routes_every_task_to_free_model_and_rejects_large_budget(self):
        policy = establish_run_allowance('free-run', 'owner', self.files, 8, tier='free')
        self.assertEqual(set(policy.reviewer_models.values()), {FREE_MODEL})
        self.assertEqual(policy.planner_model, FREE_MODEL)
        self.assertEqual(policy.coaching_model, FREE_MODEL)
        self.assertEqual(policy.provider_only, ['atlas-cloud'])
        self.assertEqual(policy.context_tokens, FREE_CONTEXT_TOKENS)
        with self.assertRaisesRegex(ValueError, 'up to 8'):
            establish_run_allowance('too-long', 'owner', self.files, 9, tier='free')
        with self.assertRaisesRegex(QuestionGenerationError, 'tier is fixed'):
            establish_run_allowance('free-run', 'owner', self.files, 8)

    def test_retained_xing_mapping_and_run_keep_their_original_route(self):
        from dataclasses import replace
        old_model = 'xingchen-agi/xing4.0-29b-a4b:free'
        saved = asdict(MappingPolicy.configured('free'))
        saved.update(model=old_model, provider_only=['phala'], context_tokens=262144)
        ProviderAllowance('xing-map', 'owner').establish(saved['allowance_nano'], saved)
        bodies = []
        def provider(request):
            bodies.append(json.loads(request.content))
            return stream_response(maps.draft(), usage={'cost': 0})
        with patch('httpx.Client', side_effect=lambda **kw: HTTPClient(transport=httpx.MockTransport(provider))):
            MappingClient('xing-map', 'owner', tier='free').parse(input=[], text_format=ResearchPlanDraft)
        self.assertEqual(bodies[0]['model'], old_model)
        self.assertEqual(bodies[0]['provider']['only'], ['phala'])
        self.assertEqual(ProviderAllowance('xing-map', 'owner').policy(), saved)
        old_run = replace(RunQuestionPolicy.configured('free'), planner_model=old_model,
            coaching_model=old_model, reviewer_models={role: old_model for role in RunQuestionPolicy.configured('free').reviewer_models},
            provider_only=['phala'], context_tokens=262144).snapshotted(self.files, 4)
        ProviderAllowance('xing-run', 'owner').establish(old_run.ceiling_nano, asdict(old_run))
        reopened = establish_run_allowance('xing-run', 'owner', self.files, 4, tier='free')
        self.assertEqual(asdict(reopened), asdict(old_run))

    def test_legacy_preparation_stays_fixed_and_requires_new_room_without_dispatch(self):
        saved = asdict(MappingPolicy.configured('free'))
        saved.update(model=RETIRED_FREE_MODEL, provider_only=None, context_tokens=1000000)
        allowance = ProviderAllowance('legacy-map', 'owner')
        allowance.establish(saved['allowance_nano'], saved)
        with patch('httpx.Client') as http:
            with self.assertRaisesRegex(QuestionGenerationError, 'Create another room'):
                MappingClient('legacy-map', 'owner', tier='free').parse(input=[], text_format=ResearchPlanDraft)
        http.assert_not_called()
        self.assertEqual(allowance.policy(), saved)
        self.assertEqual(allowance.snapshot()['used'], 0)

    def test_free_context_refuses_oversized_mapping_and_coaching_before_dispatch(self):
        from backend.openrouter_questions import RunQuestionClient
        from backend.question_generator import CoachingDraft
        large = [{'role': 'user', 'content': 'x' * FREE_CONTEXT_TOKENS}]
        establish_run_allowance('context-run', 'owner', self.files, 4, tier='free')
        with patch('httpx.Client') as http:
            with self.assertRaisesRegex(QuestionGenerationError, 'context'):
                MappingClient('context-map', 'owner', tier='free').parse(input=large, text_format=ResearchPlanDraft)
            with self.assertRaisesRegex(QuestionGenerationError, 'context'):
                RunQuestionClient('context-run', 'owner', self.session, self.files).coaching().parse(
                    input=large, text_format=CoachingDraft)
        http.assert_not_called()

    def test_free_payload_requires_free_suffix_and_zero_price_fence(self):
        body = payload(FREE_MODEL, [], QuestionDraft, reasoning={'max_tokens': 512}, max_tokens=4096, free=True)
        self.assertEqual(body['provider']['max_price'], {'prompt': 0, 'completion': 0, 'request': 0})
        self.assertEqual(body['provider']['data_collection'], 'deny')
        self.assertFalse(body['provider']['allow_fallbacks'])
        self.assertTrue(body['provider']['require_parameters'])
        with self.assertRaises(QuestionGenerationError):
            payload('paid/model', [], QuestionDraft, reasoning={}, max_tokens=1, free=True)

    def test_mapping_retry_keeps_tier_and_counts_zero_cost_receipts(self):
        bodies = []
        def provider(request):
            bodies.append(json.loads(request.content))
            return stream_response(maps.draft(), usage={'cost': 0})
        with patch('httpx.Client', side_effect=lambda **kw: HTTPClient(transport=httpx.MockTransport(provider))):
            for _ in range(3):
                client = MappingClient('free-map', 'owner', tier='free')
                client.parse(input=[], text_format=ResearchPlanDraft)
            with self.assertRaisesRegex(QuestionGenerationError, 'request limit'):
                MappingClient('free-map', 'owner', tier='free').parse(input=[], text_format=ResearchPlanDraft)
        self.assertEqual(len(bodies), 3)
        self.assertTrue(all(body['model'] == FREE_MODEL for body in bodies))
        self.assertTrue(all(body['reasoning'] == {'max_tokens': 512, 'exclude': True} for body in bodies))
        self.assertTrue(all(body['provider']['max_price']['completion'] == 0 for body in bodies))
        self.assertEqual(client.allowance.snapshot()['used'], 0)
        with self.assertRaisesRegex(QuestionGenerationError, 'tier is fixed'):
            MappingClient('free-map', 'owner')

    def test_concurrent_request_limit_preserves_coaching_slots_and_survives_reopen(self):
        policy = asdict(RunQuestionPolicy.configured('free'))
        policy.update(request_limit=5, coaching_request_reserve=2)
        allowance = ProviderAllowance('limited', 'owner')
        allowance.establish(1000, policy)
        def reserve(_):
            try:
                return allowance.reserve(1)
            except AllowanceError:
                return None
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(reserve, range(8)))
        self.assertEqual(sum(value is not None for value in results), 3)
        for identity in filter(None, results):
            allowance.settle(identity, 0)
        reopened = ProviderAllowance('limited', 'owner')
        with self.assertRaisesRegex(AllowanceError, 'request limit'):
            reopened.reserve(1)
        reopened.reserve(1, coaching=True)
        reopened.reserve(1, coaching=True)
        with self.assertRaises(AllowanceError):
            reopened.reserve(1, coaching=True)

    def test_daily_quota_is_shared_across_new_scopes_and_not_paid(self):
        with patch.dict(os.environ, {'OPENROUTER_FREE_DAILY_REQUESTS': '1'}):
            for scope in ('one', 'two'):
                ProviderAllowance(scope, scope).establish(1000, asdict(MappingPolicy.configured('free')))
            identity = ProviderAllowance('one', 'one').reserve(1)
            ProviderAllowance('one', 'one').settle(identity, 0)
            with self.assertRaisesRegex(AllowanceError, 'daily request limit'):
                ProviderAllowance('two', 'two').reserve(1)
            paid = ProviderAllowance('paid', 'owner')
            paid.establish(1000, {'tier': 'standard'})
            paid.reserve(1)

    def test_quota_expiry_and_unknown_receipts_are_not_free_retries(self):
        allowance = ProviderAllowance('window', 'owner')
        allowance.establish(1000, asdict(MappingPolicy.configured('free')))
        with patch.dict(os.environ, {'OPENROUTER_FREE_PER_MINUTE': '1'}):
            with patch('backend.provider_allowance.time.time', return_value=86401):
                allowance.reserve(1)
                with self.assertRaisesRegex(AllowanceError, 'busy'):
                    allowance.reserve(1)
            with patch('backend.provider_allowance.time.time', return_value=86462):
                allowance.reserve(1)
            with patch('backend.provider_allowance.time.time', return_value=172801):
                allowance.reserve(1)
                with self.assertRaisesRegex(AllowanceError, 'request limit'):
                    allowance.reserve(1)

    def test_upstream_429_has_no_paid_fallback(self):
        calls = []
        def provider(request):
            calls.append(json.loads(request.content))
            return httpx.Response(429, json={'error': {'code': 429, 'message': 'Quota'}})
        with patch('httpx.Client', side_effect=lambda **kw: HTTPClient(transport=httpx.MockTransport(provider))):
            with self.assertRaises(QuestionGenerationError):
                MappingClient('quota', 'owner', tier='free').parse(input=[], text_format=ResearchPlanDraft)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]['model'], FREE_MODEL)

    def test_fallback_tier_survives_reruns_and_does_not_upgrade(self):
        from streamlit.testing.v1 import AppTest
        calls = []
        def provider(request):
            calls.append(json.loads(request.content))
            return stream_response(maps.draft(), usage={'cost': 0})
        with patch('httpx.Client', side_effect=lambda **kw: HTTPClient(transport=httpx.MockTransport(provider))):
            app = AppTest.from_file(APP).run()
            next(item for item in app.selectbox if item.label == 'Practice tier').select('Free practice').run()
            app.file_uploader[0].set_value([('study.md', maps.PAPER.encode(), 'text/markdown')]).run()
            button(app, 'Prepare defense').click().run()
            self.assertFalse(app.exception)
            preparation = app.session_state['research_provider'].preparation_scope
            app.run()
            self.assertEqual(app.session_state['research_provider'].preparation_scope, preparation)
            self.assertEqual(app.session_state['research_provider'].practice_tier, 'free')
            self.assertEqual(calls[0]['model'], FREE_MODEL)
            self.assertLessEqual(app.number_input[0].value, 8)

    def test_nonzero_free_receipt_blocks_future_dispatch(self):
        allowance = ProviderAllowance('free', 'owner')
        allowance.establish(1000, asdict(MappingPolicy.configured('free')))
        identity = allowance.reserve(100)
        with self.assertRaisesRegex(AllowanceError, 'nonzero cost'):
            allowance.settle(identity, 1)
        with self.assertRaisesRegex(AllowanceError, 'operator review'):
            allowance.reserve(1)

    def test_free_access_neither_debits_nor_creates_refund_and_keeps_one_live_run(self):
        token, _ = account_store.create_google_session('free-host', 'free@example.test', 'Free host')
        owner = account_store.session_account(token)['id']
        self.assertFalse(account_store.account_access(owner)['free_access'])
        with self.assertRaises(account_store.AccessError):
            account_store.reserve_run(owner, 'paid')
        self.assertEqual(account_store.reserve_run(owner, 'test-free', free_tier=True)['cost'], 0)
        store = LiveStore()
        store.start_service('free-service')
        with patch.dict(os.environ, {'LIVE_PAID_STARTS_ENABLED': '0'}):
            row = store.reserve_run(owner, 'live-free', 'free-service', 'ROOM', free_tier=True)
        self.assertEqual((row['mode'], row['cost']), ('free', 0))
        with self.assertRaises(account_store.AccessError):
            store.reserve_run(owner, 'other-free', 'free-service', 'OTHER', free_tier=True)
        store.charge_run(owner, 'live-free')
        store.service_state('live-free', 'unavailable', 'coaching')
        store.end_unavailable(owner, 'live-free')
        view = store.overview(owner)
        self.assertEqual(view['live_credits'], 0)
        self.assertEqual(view['credit_returns'], [])


class FreeRoomTests(unittest.TestCase):
    setUp = checkpoint.OpenRouterTextCheckpointTests.setUp
    until = checkpoint.OpenRouterTextCheckpointTests.until

    def test_two_clients_complete_free_defense_without_voucher_or_credits(self):
        with account_store.connect_store(account_store.database_path()) as db:
            db.execute('DELETE FROM voucher_grants')
        response = self.client.post('/api/rooms', data={'host_name': 'Host', 'defense_type': 'research',
            'research_stage': 'proposal', 'practice_tier': 'free'},
            files=[('research_files', ('study.md', maps.PAPER.encode(), 'text/markdown'))])
        self.assertEqual(response.status_code, 201, response.text)
        host = response.json()
        code = host['room_code']
        guest = self.client.post(f'/api/rooms/{code}/join', json={'name': 'Sam'}).json()
        room = game_server.rooms[code]
        router = SyntheticRouter()
        router.app = SimpleNamespace(session_state=checkpoint.RoomAnswers(code))
        def provider(request):
            response = router(request)
            # The synthetic upstream supplies an explicit zero-dollar receipt.
            return httpx.Response(response.status_code, content=response.content.replace(b'0.0005', b'0.0'))
        with patch.dict(os.environ, {'OPENROUTER_FREE_PER_MINUTE': '1000'}), \
             patch('httpx.Client', side_effect=lambda **kw: HTTPClient(transport=httpx.MockTransport(provider))):
            with self.client.websocket_connect(f'/ws/{code}') as host_socket, self.client.websocket_connect(f'/ws/{code}') as guest_socket:
                for socket, identity in ((host_socket, host), (guest_socket, guest)):
                    socket.send_json({'type': 'hello', 'token': identity['player_token']})
                    state = self.until(socket, 'lobby')
                    self.assertEqual(state['practice_tier'], 'free')
                    self.assertEqual(state['question_limit'], 8)
                host_socket.send_json({'type': 'prepare_research_plan'})
                state = self.until(host_socket, research_planning_status='ready')
                host_socket.send_json({'type': 'approve_research_plan', 'plan_id': state['research_plan']['id'],
                    'question_budget': 9, 'confirm_profile': True})
                while True:
                    event = host_socket.receive_json()
                    if event['type'] == 'error':
                        self.assertIn('up to 8', event['message'])
                        break
                self.assertFalse(room.research_plan_approved)
                host_socket.send_json({'type': 'approve_research_plan', 'plan_id': state['research_plan']['id'],
                    'question_budget': 4, 'confirm_profile': True})
                self.until(host_socket, research_plan_approved=True)
                host_socket.send_json({'type': 'start', 'plan_id': state['research_plan']['id'], 'question_budget': 4})
                for index in range(4):
                    for socket in (host_socket, guest_socket):
                        self.until(socket, 'voting', index + 1)
                        socket.send_json({'type': 'cast_vote', 'seat': 0})
                    self.until(host_socket, 'voting', index + 1, vote_counts={'0': 2, '1': 0})
                    self.now += VOTE_MS
                    self.client.portal.call(game_server._coordinator(room).execute, CatchUpDeadline())
                    self.until(host_socket, 'question', index + 1)
                    host_socket.send_json({'type': 'submit_answer', 'turn': index, 'answer': 'We will limit the claim to our campus pilot.'})
                states = [self.until(socket, 'complete', 4, feedback_status='ready') for socket in (host_socket, guest_socket)]
                self.assertEqual(states[0]['feedback'], states[1]['feedback'])
                self.assertEqual(len(states[0]['feedback']['answer_cards']), 4)
        self.assertTrue(all(body['model'] == FREE_MODEL for body in router.calls))
        self.assertTrue(all(body['provider']['only'] == ['atlas-cloud'] for body in router.calls))
        self.assertTrue(all(body['provider']['max_price'] == {'prompt': 0, 'completion': 0, 'request': 0} for body in router.calls))
        with account_store.connect_store(account_store.database_path()) as db:
            row = db.execute('SELECT cost FROM defense_runs WHERE id=?', (room.run_id,)).fetchone()
            self.assertEqual(row['cost'], 0)

    def test_unknown_tier_is_rejected_before_file_processing(self):
        response = self.client.post('/api/rooms', data={'host_name': 'Host', 'defense_type': 'research', 'practice_tier': 'free-paid-fallback'})
        self.assertEqual(response.status_code, 422)

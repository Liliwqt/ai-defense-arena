"""Resource admission through authenticated HTTP; providers remain mocked."""
import unittest
import asyncio
import os
from unittest.mock import patch
import test_room_access as room_fixture
import game_server as server
import accounts
import mobile_auth
import test_accounts as account_fixture


class RoomAdmissionTests(unittest.TestCase):
    setUp = room_fixture.RoomAccessTests.setUp
    signin = room_fixture.RoomAccessTests.signin
    capture = room_fixture.RoomAccessTests.capture
    create = room_fixture.RoomAccessTests.create

    def test_room_limit_rejects_before_source_extraction_and_close_recovers(self):
        first, _, _ = self.create()
        self.create()
        with patch.object(server, 'read_project_files') as extract:
            response = self.client.post('/api/rooms', data={'host_name': 'Owner'}, files=self.files)
        self.assertEqual(response.status_code, 429)
        extract.assert_not_called()
        listing = self.client.get('/api/rooms').json()
        self.assertEqual(len(listing['rooms']), 2)
        self.assertNotIn('owner_account_id', str(listing))
        self.assertEqual(self.client.delete('/api/rooms/'+first.code).status_code, 200)
        self.create()

    def test_other_account_cannot_list_or_close_owners_room(self):
        room, _, _ = self.create()
        self.signin('other')
        self.assertEqual(self.client.get('/api/rooms').json()['rooms'], [])
        self.assertEqual(self.client.delete('/api/rooms/'+room.code).status_code, 403)
        self.assertEqual(self.client.post('/api/rooms/'+room.code+'/resume').status_code, 403)

    def test_owner_resume_restores_original_host_token_with_csrf(self):
        room, _, credentials = self.create()
        self.assertEqual(self.client.post('/api/rooms/'+room.code+'/resume').json(), credentials)
        self.assertEqual(self.client.post('/api/rooms/'+room.code+'/resume', headers={'X-CSRF-Token':'bad'}).status_code, 403)

    def test_terminal_expiry_warns_and_invalidates_connected_tokens(self):
        with patch.object(server, '_now_ms', return_value=1000):
            room, _, credentials = self.create()
            room.phase = 'complete'
            room.terminal_ms = 1000
            with self.client.websocket_connect('/ws/'+room.code) as socket:
                socket.send_json({'type': 'hello', 'token': credentials['player_token']})
                snapshot = socket.receive_json()['state']
                self.assertEqual(snapshot['expires_at_ms'], 1_801_000)
                with patch.object(server, '_now_ms', return_value=1_801_000):
                    self.assertEqual(self.client.get('/api/rooms').json()['rooms'], [])
                notice = socket.receive_json()
                self.assertEqual(notice['type'], 'error')
                self.assertIn('expired', notice['message'])
        self.assertIsNone(room.defense)
        self.assertEqual(room.players, {})
        self.assertEqual(room.files, [])

    def test_invalid_upload_releases_capacity(self):
        response = self.client.post('/api/rooms', data={'host_name':'Owner'}, files=[('files', ('bad.exe', b'bad'))])
        self.assertEqual(response.status_code, 422)
        self.create()
        self.create()

    def test_processing_timeout_returns_promptly_and_drops_late_result(self):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Event
        entered, release = Event(), Event()
        original = server.read_project_files

        def blocked(uploads):
            entered.set()
            release.wait(5)
            return original(uploads)

        with patch.dict('os.environ', {'ROOM_PROCESS_SECONDS': '1'}), patch.object(server, 'read_project_files', side_effect=blocked), ThreadPoolExecutor(max_workers=1) as pool:
            request = pool.submit(self.client.post, '/api/rooms', data={'host_name': 'Owner'}, files=self.files)
            try:
                self.assertTrue(entered.wait(3))
                self.assertEqual(request.result(timeout=2).status_code, 408)
                self.assertEqual(self.client.get('/api/rooms').json()['rooms'], [])
            finally:
                release.set()
        self.assertEqual(self.client.get('/api/rooms').json()['rooms'], [])

    def test_waiting_parser_is_cancelled_without_dispatch(self):
        async def occupy():
            await server.parser_slots.acquire()
            await server.parser_slots.acquire()
        async def free():
            server.parser_slots.release()
            server.parser_slots.release()
        with patch.dict('os.environ', {'ROOM_PROCESS_SECONDS': '1'}), patch.object(server, 'read_project_files') as extract:
            self.client.portal.call(occupy)
            try:
                response = self.client.post('/api/rooms', data={'host_name': 'Owner'}, files=self.files)
                self.assertEqual(response.status_code, 408)
            finally:
                self.client.portal.call(free)
            self.client.portal.call(asyncio.sleep, .05)
            extract.assert_not_called()
            self.assertEqual(self.client.get('/api/rooms').json()['rooms'], [])

    def test_cancelled_upload_releases_admission_before_body_finishes(self):
        async def cancel():
            entered = asyncio.Event()
            async def receive():
                entered.set()
                await asyncio.Event().wait()
            async def send(message):
                pass
            scope = {'type': 'http', 'asgi': {'version': '3.0'}, 'http_version': '1.1',
                'scheme': 'http', 'method': 'POST', 'path': '/api/rooms', 'raw_path': b'/api/rooms',
                'query_string': b'', 'root_path': '', 'state': {}, 'client': ('127.0.0.1', 123),
                'server': ('127.0.0.1', 8000), 'headers': [
                    (b'cookie', (accounts.ACCOUNT_COOKIE+'='+self.token).encode()),
                    (b'origin', self.origin.encode()), (b'x-csrf-token', self.csrf.encode()),
                    (b'content-type', b'multipart/form-data; boundary=offline')]}
            task = asyncio.create_task(server.app(scope, receive, send))
            await asyncio.wait_for(entered.wait(), 2)
            task.cancel()
            result = await asyncio.gather(task, return_exceptions=True)
            self.assertIsInstance(result[0], asyncio.CancelledError)
        self.client.portal.call(cancel)
        self.create()
        self.create()

    def test_concurrent_accounts_cannot_exceed_global_capacity(self):
        from concurrent.futures import ThreadPoolExecutor
        import account_store
        for index in range(server.MAX_ROOMS-2):
            code = f'EXISTING{index}'
            server.rooms[code] = server.Room(code, [], {}, owner_account_id=f'other-{index}')
        identities = [account_store.create_google_session(f'parallel-{index}', f'parallel-{index}@example.test', 'Host') for index in range(6)]
        def create(identity):
            token, csrf = identity
            return self.client.post('/api/rooms', data={'host_name': 'Owner'}, files=self.files,
                headers={'Cookie': accounts.ACCOUNT_COOKIE+'='+token, 'X-CSRF-Token': csrf}).status_code
        with ThreadPoolExecutor(max_workers=6) as pool:
            statuses = list(pool.map(create, identities))
        self.assertEqual(statuses.count(201), 2)
        self.assertEqual(statuses.count(503), 4)
        self.assertEqual(len(server.rooms), server.MAX_ROOMS)

    def cleanup_race(self, action):
        with patch.object(server, '_now_ms', return_value=1000):
            room, host, _ = self.create()
        if action == 'restart':
            room.phase = 'complete'
            room.terminal_ms = 1000
        self.client.post('/api/auth/voucher', json={'voucher': os.environ['FREE_ACCESS_VOUCHER']})
        original = server._remove_room
        async def scenario():
            removing, proceed = asyncio.Event(), asyncio.Event()
            async def paused_remove(candidate, **kwargs):
                removing.set()
                await proceed.wait()
                return await original(candidate, **kwargs)
            with patch.object(server, '_remove_room', side_effect=paused_remove):
                task = asyncio.create_task(server._cleanup_rooms())
                await asyncio.wait_for(removing.wait(), 2)
                await server._handle_action(room, host, self.socket, {'type': action})
                proceed.set()
                await task
            self.assertIs(server.rooms.get(room.code), room)
            self.assertEqual(room.phase, 'generating')
            self.assertFalse(room.closed)
        with patch.object(server, '_now_ms', return_value=1_801_000):
            self.client.portal.call(scenario)

    def test_start_wins_cleanup_recheck_without_losing_room(self):
        self.cleanup_race('start')

    def test_restart_wins_cleanup_recheck_without_losing_room(self):
        self.cleanup_race('restart')

    def test_concurrent_creation_cannot_exceed_account_capacity(self):
        from concurrent.futures import ThreadPoolExecutor
        def create(_):
            return self.client.post('/api/rooms', data={'host_name':'Owner'}, files=self.files).status_code
        with ThreadPoolExecutor(max_workers=6) as pool:
            statuses = list(pool.map(create, range(6)))
        self.assertEqual(statuses.count(201), 2)
        self.assertEqual(statuses.count(429), 4)

    def test_opening_generation_attempts_are_bounded_before_provider(self):
        room, _, _ = self.create()
        room.phase = 'generating'
        with patch.object(server, 'generate_first_question', side_effect=server.QuestionGenerationError('Offline failure')) as provider:
            for _ in range(4):
                self.client.portal.call(server._generate_question, room, room.generation_id, True)
        self.assertEqual(provider.call_count, 3)
        self.assertEqual(room.phase, 'retry')
        self.assertIn('allowance', room.error)

    def test_idle_expiry_frees_slots_but_active_run_is_protected(self):
        with patch.object(server, '_now_ms', return_value=1000):
            room, _, credentials = self.create()
        with patch.object(server, '_now_ms', return_value=1_801_000):
            self.assertEqual(self.client.get('/api/rooms').json()['rooms'], [])
        self.assertEqual(self.client.post('/api/rooms/'+room.code+'/join', json={'name':'Guest'}).status_code, 404)
        active, _, _ = self.create()
        active.settled = False
        active.phase = 'question'
        with patch.object(server, '_now_ms', return_value=10_000_000_000_000):
            self.assertEqual(len(self.client.get('/api/rooms').json()['rooms']), 1)
            self.assertEqual(self.client.delete('/api/rooms/'+active.code).status_code, 409)


class MobileAdmissionTests(unittest.TestCase):
    google_response = account_fixture.AccountCreditTests.google_response

    def setUp(self):
        account_fixture.AccountCreditTests.setUp(self)
        self.handoffs = mobile_auth.MobileHandoffs()
        replacement = patch.object(accounts, 'handoffs', self.handoffs)
        replacement.start()
        self.addCleanup(replacement.stop)

    def start(self, index=0, **kwargs):
        return self.client.post('/api/auth/mobile/start', json={'challenge':str(index).zfill(43)}, **kwargs)

    def test_retry_reuses_flow_without_consuming_new_capacity(self):
        first = self.start().json()
        for _ in range(15):
            self.assertEqual(self.start().json()['flow'], first['flow'])
        for index in range(1, 12):
            self.assertEqual(self.start(index).status_code, 200)
        blocked = self.start(12)
        self.assertEqual(blocked.status_code, 429)
        self.assertIn('retry-after', blocked.headers)

    def test_forwarded_header_does_not_bypass_untrusted_peer_limit(self):
        for index in range(12):
            self.assertEqual(self.start(index).status_code, 200)
        self.assertEqual(self.start(13, headers={'X-Forwarded-For':'192.0.2.15'}).status_code, 429)

    def test_reused_flow_keeps_original_expiry(self):
        with patch.object(mobile_auth.time, 'monotonic', return_value=1):
            first = self.start().json()['flow']
        with patch.object(mobile_auth.time, 'monotonic', return_value=290):
            self.assertEqual(self.start().json()['flow'], first)
        with patch.object(mobile_auth.time, 'monotonic', return_value=302):
            self.assertNotEqual(self.start().json()['flow'], first)

    def test_opened_retry_does_not_reopen_oauth(self):
        flow = self.start().json()['flow']
        self.handoffs.open(flow)
        response = self.start()
        self.assertEqual(response.status_code, 409)
        self.assertIn('existing browser', response.json()['detail'])

    def test_existing_signin_can_complete_while_new_starts_are_throttled(self):
        import base64
        import hashlib
        from urllib.parse import parse_qs, urlsplit
        verifier = 'A' * 64
        challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip('=')
        first = self.client.post('/api/auth/mobile/start', json={'challenge': challenge}).json()
        for index in range(1, 12):
            self.assertEqual(self.start(index).status_code, 200)
        self.assertEqual(self.start(12).status_code, 429)
        login = self.client.get(first['login_url'], follow_redirects=False)
        params = parse_qs(urlsplit(login.headers['location']).query)
        self.nonce = params['nonce'][0]
        returned = self.client.get('/api/auth/google/callback', params={'code': 'offline-code', 'state': params['state'][0]}, follow_redirects=False)
        code = parse_qs(urlsplit(returned.headers['location']).query)['code'][0]
        exchanged = self.client.post('/api/auth/mobile/complete', json={'flow': first['flow'], 'code': code, 'verifier': verifier})
        self.assertEqual(exchanged.status_code, 200)
        self.assertTrue(self.client.get('/api/auth/me').json()['authenticated'])

    def test_independent_network_can_sign_in_after_first_is_full(self):
        from resource_limits import client_network
        with patch.dict('os.environ', {'TRUSTED_PROXY_NETWORKS':'127.0.0.1/32'}):
            from types import SimpleNamespace
            self.assertEqual(client_network(SimpleNamespace(client=SimpleNamespace(host='127.0.0.1'), headers={'x-forwarded-for':'192.0.2.3'})), '192.0.2.3')
        for index in range(12):
            self.start(index)
        with patch.object(accounts, 'handoffs', self.handoffs), patch('resource_limits.client_network', return_value='second-network'):
            self.assertEqual(self.start(20).status_code, 200)


class AIBudgetTests(unittest.TestCase):
    def test_long_research_budget_and_per_turn_retry_cap(self):
        from resource_limits import AIBudget
        from fastapi import HTTPException
        budget = AIBudget()
        budget.reset_run(100)
        with patch.dict('os.environ', {'AI_OWNER_PER_MINUTE':'1000'}):
            for index in range(100):
                budget.admit(f'question:{index}', 3, 'long-research-fixture')
                for _ in range(6):
                    budget.admit(f'interpret:{index}', 6, 'long-research-fixture')
            with self.assertRaises(HTTPException):
                budget.admit('interpret:99', 6, 'long-research-fixture')
            self.assertEqual(budget.total, 700)

    def test_owner_burst_counts_different_guest_operations(self):
        from resource_limits import AIBudget, ai_rate
        from fastapi import HTTPException
        ai_rate.__init__()
        budget = AIBudget()
        for index in range(12):
            budget.admit(f'guest-operation:{index}', 6, 'one-host-fixture')
        with self.assertRaises(HTTPException):
            budget.admit('another-guest', 6, 'one-host-fixture')
        self.assertEqual(budget.total, 12)
        budget.admit('another-host', 6, 'independent-host-fixture')

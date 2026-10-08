"""Render deployment overlap using a real disposable store; providers mocked."""
import asyncio
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

import game_server
from account_store import AccessError, create_google_session, session_account
from management_store import ManagementStore
from live_store import LiveStore, ServiceAlreadyActive
from starlette.websockets import WebSocketDisconnect


class ServiceHandoffTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        env = patch.dict(os.environ, {
            'DATABASE_URL': os.environ.get('DATABASE_URL', '') if getattr(self, 'pg_url', None) else '',
            'PAYMENTS_MODE': 'live', 'RENDER': 'true',
            'LIVE_PAID_STARTS_ENABLED': '1', 'FREE_ACCESS_VOUCHER': '',
            'PAYMONGO_TEST_DB_PATH': str(Path(folder.name) / 'handoff.sqlite3'),
        })
        env.start()
        self.addCleanup(env.stop)
        recovery = patch('payments_live.recover_payments', new_callable=AsyncMock)
        self.recover = recovery.start()
        self.addCleanup(recovery.stop)
        for name in ('SERVICE_POLL_SECONDS', 'SERVICE_HEARTBEAT_SECONDS'):
            timing = patch.object(game_server, name, 0.01)
            timing.start()
            self.addCleanup(timing.stop)
        self.store = LiveStore()
        self.store.start_service('previous-process')

    def wait_for_status(self, client, expected):
        async def wait():
            async def poll():
                while game_server.app.state.room_service_status != expected:
                    await asyncio.sleep(0.005)
            await asyncio.wait_for(poll(), timeout=2)
        client.portal.call(wait)

    def test_render_replacement_starts_without_stealing_previous_lease(self):
        with TestClient(game_server.app) as client:
            result = client.get('/health')
            self.assertEqual(result.status_code, 200)
            self.assertEqual(result.json()['room_service'], 'starting')
            self.assertEqual(client.post('/api/rooms').status_code, 503)
            with self.store.transaction() as db:
                rows = db.execute("SELECT id FROM live_services WHERE status='running'").fetchall()
                self.assertEqual([row['id'] for row in rows], ['previous-process'])
            self.recover.assert_not_awaited()
            self.assertEqual(client.post('/api/rooms/TEST/join').status_code, 503)
            with client.websocket_connect('/ws/TEST') as socket:
                self.assertEqual(socket.receive_json()['message'], game_server.SERVICE_STARTING_MESSAGE)
                with self.assertRaises(WebSocketDisconnect) as closed:
                    socket.receive_json()
                self.assertEqual(closed.exception.code, 1013)
            self.assertEqual(client.get('/api/auth/me').status_code, 200)

    def test_replacement_acquires_only_after_previous_process_stops(self):
        with TestClient(game_server.app) as client:
            self.store.stop_service('previous-process')
            self.wait_for_status(client, 'ready')
            self.assertEqual(client.get('/health').json(), {'status': 'ok'})
            service = game_server.SERVICE_ID
            with self.store.transaction() as db:
                rows = db.execute("SELECT id FROM live_services WHERE status='running'").fetchall()
                self.assertEqual([row['id'] for row in rows], [service])
            # A further candidate cannot steal an active lease.
            with self.assertRaises(ServiceAlreadyActive):
                self.store.start_service('third-process')
            # Let the independently scheduled recovery task run after takeover.
            async def recovered():
                async def poll():
                    while not self.recover.await_count:
                        await asyncio.sleep(0.005)
                await asyncio.wait_for(poll(), timeout=2)
            client.portal.call(recovered)
        with self.store.transaction() as db:
            self.assertEqual(db.execute('SELECT status FROM live_services WHERE id=?', (service,)).fetchone()[0], 'stopped')

    def test_crashed_previous_process_expires_and_is_fenced(self):
        with TestClient(game_server.app) as client:
            with self.store.transaction() as db:
                db.execute('UPDATE live_services SET heartbeat=0 WHERE id=?', ('previous-process',))
            self.wait_for_status(client, 'ready')
            with self.assertRaises(AccessError) as fenced:
                self.store.heartbeat('previous-process')
            self.assertIn('no longer owns', str(fenced.exception))

    def test_cancelled_waiter_leaves_previous_process_running(self):
        with TestClient(game_server.app) as client:
            self.assertEqual(client.get('/health').json()['room_service'], 'starting')
        self.store.heartbeat('previous-process')
        with self.store.transaction() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM live_services').fetchone()[0], 1)

    def test_handoff_returns_unfinished_charge_once_and_never_before_lease_release(self):
        token, _ = create_google_session('offline-handoff-owner', 'owner@example.test', 'Owner')
        account = session_account(token)['id']
        ManagementStore().adjust(account, account, 10, 'Offline handoff fixture', 'handoff-fixture')
        self.store.reserve_run(account, 'unfinished-run', 'previous-process', 'ROOM')
        self.store.charge_run(account, 'unfinished-run')
        with TestClient(game_server.app) as client:
            self.assertEqual(self.store.overview(account)['live_credits'], 0)
            self.assertEqual(self.store.overview(account)['credit_returns'], [])
            self.store.stop_service('previous-process')
            self.wait_for_status(client, 'ready')
            self.store.start_service(game_server.SERVICE_ID)
            view = self.store.overview(account)
            self.assertEqual(view['live_credits'], 10)
            self.assertEqual(len(view['credit_returns']), 1)
            self.assertEqual(view['live_runs'][0]['outcome'], 'interrupted')
            with self.assertRaises(AccessError):
                self.store.charge_run(account, 'unfinished-run')

    def test_non_render_duplicate_still_fails_startup(self):
        with patch.dict(os.environ, {'RENDER': ''}), self.assertRaises(ServiceAlreadyActive):
            with TestClient(game_server.app):
                self.fail('Duplicate local service must not start.')

    def test_unrelated_database_failure_is_not_treated_as_deploy_overlap(self):
        with patch.object(LiveStore, 'start_service', side_effect=RuntimeError('offline database failure')):
            with self.assertRaisesRegex(RuntimeError, 'offline database failure'):
                with TestClient(game_server.app):
                    self.fail('Database failure must not advertise a healthy startup.')

    def test_lost_heartbeat_blocks_room_access_and_health_without_reacquiring(self):
        self.store.stop_service('previous-process')
        with patch.object(LiveStore, 'heartbeat', side_effect=ServiceAlreadyActive('offline ownership loss')):
            with TestClient(game_server.app) as client:
                self.wait_for_status(client, 'failed')
                self.assertEqual(client.get('/health').status_code, 503)
                self.assertEqual(client.post('/api/rooms').status_code, 503)
                self.recover.assert_not_awaited()


if __name__ == '__main__':
    unittest.main()

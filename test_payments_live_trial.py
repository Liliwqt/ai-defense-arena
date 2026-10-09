"""Offline live-trial checks; Google, PayMongo and signatures use fixtures."""

from concurrent.futures import ThreadPoolExecutor
import hashlib
import hmac
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import AsyncMock, Mock, patch

from fastapi.testclient import TestClient

import account_store
import accounts
import payments
import payments_live_trial as trial
from purchase_store import PurchaseError, PurchaseStore


class LiveTrialTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.database = Path(folder.name) / 'qr-one-peso-live.sqlite3'
        environment = patch.dict(os.environ, {
            'DATABASE_URL': '', 'PAYMONGO_LIVE_TRIAL_ENABLED': '1',
            'PAYMONGO_LIVE_SECRET_KEY': 'sk_live_offline_fixture',
            'PAYMONGO_LIVE_WEBHOOK_SECRET': 'offline-live-webhook',
            'PAYMONGO_LIVE_TRIAL_OWNER_SUB': 'offline-owner',
            'PAYMONGO_PUBLIC_BASE_URL': 'https://trial.example.test',
            'PAYMONGO_TEST_DB_PATH': str(self.database),
            'GOOGLE_CLIENT_ID': 'offline', 'GOOGLE_CLIENT_SECRET': 'offline',
            'AUTH_SESSION_SECRET': 'offline-session-secret-with-more-than32chars',
            'AUTH_PUBLIC_BASE_URL': 'https://trial.example.test',
        })
        environment.start()
        self.addCleanup(environment.stop)
        clock = patch.object(payments.time, 'time', return_value=1_800_000_000)
        clock.start()
        self.addCleanup(clock.stop)
        self.client = TestClient(trial.create_app(), base_url='https://trial.example.test')
        self.client.__enter__()
        self.addCleanup(lambda: self.client.__exit__(None, None, None))
        self.token, self.csrf = account_store.create_google_session('offline-owner', 'owner@example.test', 'Owner')
        self.owner_id = account_store.session_account(self.token)['id']
        self.client.cookies.set(accounts.ACCOUNT_COOKIE, self.token)
        self.client.headers.update({'Origin': 'https://trial.example.test', 'X-CSRF-Token': self.csrf})
        self.provider = AsyncMock()
        provider = patch.object(payments.httpx, 'AsyncClient')
        provider.start().return_value.__aenter__.return_value = self.provider
        self.addCleanup(provider.stop)

    def resources(self, *, mode=True, amount=100):
        image = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a1uoAAAAASUVORK5CYII='
        attrs = {'livemode': mode, 'amount': amount, 'currency': 'PHP'}
        data = [
            {'id': 'pi_live_fixture', 'type': 'payment_intent', 'attributes': {**attrs, 'client_key': 'offline', 'status': 'awaiting_payment_method'}},
            {'id': 'pm_live_fixture', 'type': 'payment_method', 'attributes': {'livemode': mode, 'type': 'qrph'}},
            {'id': 'pi_live_fixture', 'type': 'payment_intent', 'attributes': {**attrs, 'status': 'awaiting_next_action', 'next_action': {'code': {'image_url': image}}}},
        ]
        results = []
        for item in data:
            result = Mock()
            result.json.return_value = {'data': item}
            results.append(result)
        self.provider.post.side_effect = results

    def create(self, key='offline-request-id-1234', **body):
        return self.client.post('/api/payments/live-trial/topups', json={'confirm_real_payment': True, **body}, headers={'Idempotency-Key': key})

    def event(self, receipt, *, mode=True, amount=100, kind='payment.paid'):
        return {'data': {'type': 'event', 'attributes': {'livemode': mode, 'type': kind, 'data': {
            'id': 'pay_live_fixture', 'type': 'payment', 'attributes': {
                'livemode': mode, 'amount': amount, 'currency': 'PHP', 'status': kind.split('.')[1],
                'payment_intent_id': 'pi_live_fixture', 'metadata': {'topup_id': receipt['id']},
            }}}}}

    def deliver(self, event, *, signature_mode='li', stamp='1800000000'):
        raw = json.dumps(event).encode()
        digest = hmac.new(b'offline-live-webhook', stamp.encode()+b'.'+raw, hashlib.sha256).hexdigest()
        return self.client.post('/api/payments/live-trial/webhook', content=raw, headers={'Paymongo-Signature': f't={stamp},{signature_mode}={digest}'})

    def test_fixed_price_real_mode_and_no_simulation_route(self):
        self.resources()
        result = self.create()
        self.assertEqual(result.status_code, 201)
        row = result.json()['topup']
        self.assertEqual((row['amount'], row['credits'], row['mode'], row['simulated']), (100, 100, 'live', False))
        payload = self.provider.post.call_args_list[0].kwargs['json']['data']['attributes']
        self.assertEqual(payload['amount'], 100)
        self.assertIn('live trial', payload['description'])
        self.assertEqual(self.provider.post.call_args_list[0].kwargs['auth'][0], 'sk_live_offline_fixture')
        for path in ['/api/payments/live-trial/topups/'+row['id']+'/simulate', '/api/payments/test/topups', '/api/rooms']:
            self.assertEqual(self.client.post(path, json={}).status_code, 404)

    def test_signed_live_payment_awards_once_replay_preserves_paid(self):
        self.resources()
        row = self.create().json()['topup']
        self.assertEqual(self.deliver(self.event(row)).status_code, 200)
        self.assertEqual(self.deliver(self.event(row)).status_code, 200)
        self.assertEqual(self.create().json()['topup']['status'], 'paid')
        self.assertEqual(self.provider.post.call_count, 3)
        with account_store.connect_store(self.database) as db:
            self.assertEqual(db.execute('SELECT COUNT(*), SUM(credits) FROM test_credit_ledger').fetchone()[:], (1, 100))

    def test_test_mode_wrong_amount_and_wrong_signature_cannot_award(self):
        self.resources()
        row = self.create().json()['topup']
        self.assertEqual(self.deliver(self.event(row), signature_mode='te').status_code, 401)
        self.assertEqual(self.deliver(self.event(row), stamp='1799990000').status_code, 401)
        for event in [self.event(row, mode=False), self.event(row, amount=10000)]:
            self.assertEqual(self.deliver(event).status_code, 400)
        self.assertEqual(account_store.account_overview(self.owner_id)['test_credits'], 0)

    def test_receipt_reference_mismatch_rejected(self):
        self.resources()
        row = self.create().json()['topup']
        event = self.event(row)
        event['data']['attributes']['data']['attributes']['metadata']['topup_id'] = 'other'
        self.assertEqual(self.deliver(event).status_code, 400)
        self.assertEqual(account_store.account_overview(self.owner_id)['test_credits'], 0)

    def test_no_provider_call_without_owner_csrf_and_confirmation(self):
        self.assertEqual(self.create(confirm_real_payment=False).status_code, 400)
        self.assertEqual(self.create(amount=1).status_code, 422)
        self.client.headers['X-CSRF-Token'] = 'wrong'
        self.assertEqual(self.create().status_code, 403)
        token, csrf = account_store.create_google_session('another-person', 'other@example.test', 'Other')
        self.client.cookies.set(accounts.ACCOUNT_COOKIE, token)
        self.client.headers['X-CSRF-Token'] = csrf
        self.assertEqual(self.create().status_code, 403)
        self.assertEqual(self.client.get('/api/payments/live-trial/config').status_code, 403)
        self.client.cookies.clear()
        self.assertEqual(self.create().status_code, 401)
        self.provider.post.assert_not_called()

    def test_one_trial_even_after_failed_creation_or_expiry(self):
        self.resources(mode=False)
        self.assertEqual(self.create().status_code, 502)
        self.assertEqual(self.create().status_code, 409)
        self.assertEqual(self.create(key='different-request-id-1234').status_code, 409)
        self.assertEqual(self.provider.post.call_count, 1)

    def test_server_rejects_wrong_provider_price(self):
        self.resources(amount=10000)
        self.assertEqual(self.create().status_code, 502)
        self.assertEqual(self.provider.post.call_count, 1)

    def test_concurrent_trial_requests_only_one_receipt(self):
        def begin(index):
            try:
                return PurchaseStore(self.database).begin_live_trial(self.owner_id, f'offline-request-{index}')['status']
            except PurchaseError as error:
                return error.kind
        with ThreadPoolExecutor(max_workers=2) as executor:
            self.assertCountEqual(list(executor.map(begin, [1, 2])), ['creating', 'trial_exists'])
        with account_store.connect_store(self.database) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM test_orders').fetchone()[0], 1)

    def test_config_fail_closed(self):
        for key, value in [('PAYMONGO_LIVE_TRIAL_ENABLED','0'), ('PAYMONGO_LIVE_SECRET_KEY','sk_test_fixture'),
                           ('PAYMONGO_LIVE_WEBHOOK_SECRET',''), ('PAYMONGO_LIVE_TRIAL_OWNER_SUB',''),
                           ('PAYMONGO_TEST_DB_PATH','/tmp/payments-test.sqlite3'), ('DATABASE_URL','postgresql://not-used'),
                           ('PAYMONGO_PUBLIC_BASE_URL','http://trial.example.test'), ('AUTH_PUBLIC_BASE_URL','https://different.example.test')]:
            with self.subTest(setting=key), patch.dict(os.environ, {key:value}):
                self.assertEqual(self.client.get('/api/payments/live-trial/config').status_code, 503)
                self.assertEqual(self.create().status_code, 503)
        self.provider.post.assert_not_called()

    def test_existing_unmarked_database_cannot_be_reused(self):
        with account_store.connect_store(self.database) as db:
            db.execute('DELETE FROM payment_environment')
        with self.assertRaises(Exception) as error:
            trial.initialize_trial_store(trial.trial_settings())
        self.assertEqual(error.exception.status_code, 503)

    def test_receipt_restores_and_status_read_does_not_award(self):
        self.resources()
        row = self.create().json()['topup']
        self.assertEqual(self.client.get('/api/payments/live-trial/config').json()['receipt_id'], row['id'])
        self.assertEqual(self.client.get('/api/payments/live-trial/topups/'+row['id']).json()['topup']['status'], 'pending')
        self.assertEqual(account_store.account_overview(self.owner_id)['test_credits'], 0)
        self.assertEqual(self.provider.post.call_count, 3)

    def test_live_page_is_truthful_and_has_no_simulator(self):
        page = self.client.get('/')
        self.assertEqual(page.status_code, 200)
        self.assertIn('REAL PAYMENT', page.text)
        self.assertIn('₱1.00', page.text)
        self.assertNotIn('Simulate paid top-up', page.text)
        self.assertIn("row.mode!=='live'||row.amount!==100", page.text)


if __name__ == '__main__':
    unittest.main()

"""Owner dashboard checks with synthetic Google sessions; no provider calls."""
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
import accounts
import account_store
from live_store import LiveStore


class ManagementTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        env = patch.dict(os.environ, {
            'DATABASE_URL': os.environ.get('DATABASE_URL','') if getattr(self,'pg_url',None) else '', 'PAYMONGO_TEST_DB_PATH': str(Path(folder.name)/'manager.sqlite3'),
            'PAYMENTS_MODE': 'live', 'LIVE_PAID_STARTS_ENABLED': '1',
            'GOOGLE_CLIENT_ID': 'offline', 'GOOGLE_CLIENT_SECRET': 'offline',
            'AUTH_SESSION_SECRET': 'offline-secret-longer-than-thirty-two-characters',
            'AUTH_PUBLIC_BASE_URL': 'http://127.0.0.1:8000',
            'PAYMENT_OPERATOR_GOOGLE_SUB': 'owner-sub', 'LIVE_TOPUP_INVITED_EMAILS': 'legacy@example.test'})
        env.start(); self.addCleanup(env.stop)
        app = FastAPI(); accounts.configure_auth(app)
        self.client = TestClient(app)
        self.addCleanup(self.client.close)
        self.token, self.csrf = account_store.create_google_session('owner-sub', 'owner@example.test', 'Owner')
        self.owner = account_store.session_account(self.token)['id']
        self.other_token, self.other_csrf = account_store.create_google_session('other-sub', 'other@example.test', 'Other')
        self.other = account_store.session_account(self.other_token)['id']
        self.client.cookies.set(accounts.ACCOUNT_COOKIE, self.token)
        self.client.headers.update({'Origin': 'http://127.0.0.1:8000', 'X-CSRF-Token': self.csrf})

    def adjust(self, delta, key='manager-request-12345', **extra):
        return self.client.post('/api/manager/users/'+self.other+'/credits',
            json={'delta': delta, 'reason': 'Tester credit correction', **extra}, headers={'Idempotency-Key': key})

    def test_only_verified_owner_can_list_and_mutate(self):
        self.assertTrue(self.client.get('/api/auth/me').json()['manager_enabled'])
        self.assertEqual(self.client.get('/api/manager/users').status_code, 200)
        self.client.cookies.set(accounts.ACCOUNT_COOKIE, self.other_token)
        self.client.headers['X-CSRF-Token'] = self.other_csrf
        self.assertFalse(self.client.get('/api/auth/me').json()['manager_enabled'])
        for path in ['/api/manager/users', '/api/manager/testers', '/api/manager/audit']:
            self.assertEqual(self.client.get(path).status_code, 403)
        self.assertEqual(self.adjust(10).status_code, 403)
        self.assertEqual(self.client.put('/api/manager/testers', json={'email':'new@example.test','enabled':True}).status_code, 403)
        self.client.cookies.clear()
        self.assertEqual(self.client.get('/api/manager/users').status_code, 401)

    def test_csrf_owner_configuration_and_expiry(self):
        self.client.headers['X-CSRF-Token'] = 'wrong'
        self.assertEqual(self.adjust(10).status_code, 403)
        with patch.dict(os.environ, {'PAYMENT_OPERATOR_GOOGLE_SUB': ''}):
            self.assertEqual(self.client.get('/api/manager/users').status_code, 403)
        account_store.remove_session(self.token)
        self.assertEqual(self.client.get('/api/manager/users').status_code, 401)

    def test_invite_before_signin_revoke_legacy_and_persist(self):
        from financial_policy import invited
        self.assertFalse(invited('new@example.test'))
        result = self.client.put('/api/manager/testers', json={'email': ' NEW@example.test ', 'enabled': True})
        self.assertEqual(result.status_code, 200, result.text)
        self.assertTrue(invited('new@example.test'))
        self.assertEqual(self.client.put('/api/manager/testers', json={'email': 'legacy@example.test', 'enabled': False}).status_code, 200)
        self.assertFalse(invited('legacy@example.test'))
        rows = self.client.get('/api/manager/testers').json()['testers']
        self.assertIn({'email': 'new@example.test', 'enabled': True}, rows)
        self.assertEqual(self.client.put('/api/manager/testers', json={'email': 'bad email', 'enabled': True}).status_code, 422)
        token, _ = account_store.create_google_session('new-sub', 'new@example.test', 'New')
        self.client.cookies.set(accounts.ACCOUNT_COOKIE, token)
        self.assertTrue(self.client.get('/api/auth/me').json()['topup_invited'])
        self.assertNotIn('testers', self.client.get('/api/auth/me').json())

    def test_grants_are_audited_once_without_fake_purchases(self):
        response = self.adjust(25)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(self.adjust(25).json(), response.json())
        self.assertEqual(self.adjust(30).status_code, 409)
        view = LiveStore().overview(self.other)
        self.assertEqual(view['live_credits'], 25)
        self.assertEqual(view['live_orders'], [])
        self.assertEqual(view['credit_returns'], [])
        self.assertEqual(self.adjust(-5, 'manager-negative-12345').status_code, 200)
        self.assertEqual(LiveStore().overview(self.other)['live_credits'], 20)
        audit = self.client.get('/api/manager/audit').json()['entries']
        changes = [entry for entry in audit if entry['action'] == 'credits']
        self.assertEqual(sorted(entry['delta'] for entry in changes), [-5, 25])
        self.assertTrue(all(entry['actor_id'] == self.owner for entry in changes))

    def test_validation_and_underflow_rollback(self):
        for delta in [0, True, '10', 100001]:
            self.assertEqual(self.adjust(delta).status_code, 422)
        self.assertEqual(self.adjust(10, reason=' ').status_code, 422)
        self.assertEqual(self.adjust(-1).status_code, 409)
        self.assertEqual(self.client.post('/api/manager/users/'+self.other+'/credits',json={'delta':10,'reason':'Missing request key'}).status_code, 422)
        self.assertEqual(self.client.post('/api/manager/users/missing/credits', json={'delta':10,'reason':'Tester grant'}, headers={'Idempotency-Key':'manager-missing-12345'}).status_code, 404)
        self.assertEqual(LiveStore().overview(self.other)['live_credits'], 0)

    def test_grant_funds_defense_reservation_retry_and_credit_return(self):
        self.assertEqual(self.adjust(20).status_code, 200)
        store = LiveStore(); store.start_service('manager-service')
        store.reserve_run(self.other, 'grant-run', 'manager-service', 'ROOM')
        view = store.overview(self.other)
        self.assertEqual((view['live_credits'], view['live_reserved_credits']), (10, 10))
        self.assertEqual(self.adjust(-11, 'reserved-debit-12345').status_code, 409)
        self.assertEqual(self.adjust(-10, 'available-debit-12345').status_code, 200)
        store.release_run('grant-run')
        self.assertEqual(store.overview(self.other)['live_credits'], 10)
        store.reserve_run(self.other, 'grant-run', 'manager-service', 'ROOM')
        store.charge_run(self.other, 'grant-run'); store.charge_run(self.other, 'grant-run')
        store.service_state('grant-run', 'unavailable', 'question')
        store.end_unavailable(self.other, 'grant-run'); store.end_unavailable(self.other, 'grant-run')
        self.assertEqual(store.overview(self.other)['live_credits'], 10)

    def test_concurrent_same_adjustment_grants_once_and_user_pagination(self):
        from management_store import ManagementStore
        store = ManagementStore()
        with ThreadPoolExecutor(max_workers=2) as pool:
            list(pool.map(lambda _: store.adjust(self.owner, self.other, 10, 'Concurrent test grant', 'shared-request-12345'), range(2)))
        self.assertEqual(LiveStore().overview(self.other)['live_credits'], 10)
        result = self.client.get('/api/manager/users?limit=1&offset=0').json()
        self.assertEqual((result['total'], len(result['users'])), (2, 1))
        filtered = self.client.get('/api/manager/users?q=other').json()['users']
        self.assertEqual(filtered[0]['id'], self.other)
        self.assertNotIn('google_sub', filtered[0])
        self.assertNotIn('csrf_token', filtered[0])

    def test_owner_is_google_subject_not_email(self):
        token, _ = account_store.create_google_session('imposter-sub', 'owner@example.test', 'Owner')
        self.client.cookies.set(accounts.ACCOUNT_COOKIE, token)
        self.assertEqual(self.client.get('/api/manager/users').status_code, 403)
        self.assertFalse(self.client.get('/api/auth/me').json()['manager_enabled'])

    def test_mixed_grant_purchase_allocations_and_restart_recovery(self):
        store = LiveStore()
        self.client.put('/api/manager/testers',json={'email':'other@example.test','enabled':True})
        receipt, _ = store.begin_topup(self.other,'credits-10','purchase-fixture-12345')
        store.bind_topup_intent(receipt['id'],'pi_fixture')
        store.register_topup(receipt['id'],'pi_fixture','offline-image',1800000000)
        store.record_topup_paid(receipt['id'],'pi_fixture',['pay_fixture'],100,'PHP')
        self.assertEqual(self.adjust(5).status_code,200)
        store.start_service('old-service',now=100)
        store.reserve_run(self.other,'mixed-run','old-service','ROOM')
        self.assertEqual(store.overview(self.other)['live_reserved_credits'],10)
        store.charge_run(self.other,'mixed-run')
        self.assertEqual(store.overview(self.other)['live_credits'],5)
        store.start_service('new-service',now=200)
        store.start_service('new-service',now=200)
        self.assertEqual(store.overview(self.other)['live_credits'],15)
        self.assertEqual(self.adjust(-12,'remove-purchased-12345').status_code,200)
        view=store.overview(self.other)
        self.assertEqual(view['live_credits'],3)
        self.assertEqual(view['live_orders'][0]['status'],'paid')
        with self.assertRaises(account_store.AccessError):
            store.hold_refund(receipt['id'],self.owner,'Credits no longer unused')

    def test_concurrent_negative_adjustments_cannot_overdraw(self):
        from management_store import ManagementStore
        self.adjust(10)
        def subtract(key):
            try:
                ManagementStore().adjust(self.owner,self.other,-10,'Concurrent removal',key)
                return True
            except account_store.AccessError:
                return False
        with ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(subtract,['negative-attempt-1111','negative-attempt-2222']))
        self.assertEqual(sorted(results),[False,True])
        self.assertEqual(LiveStore().overview(self.other)['live_credits'],0)

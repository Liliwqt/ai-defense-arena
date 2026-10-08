"""Live access contracts through existing account HTTP seams; providers mocked."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
import accounts
import account_store


class LiveAccessTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory(); self.addCleanup(folder.cleanup)
        self.env = patch.dict(os.environ, {'DATABASE_URL': os.environ.get('DATABASE_URL','') if getattr(self,'pg_url',None) else '', 'PAYMENTS_MODE':'live',
            'PAYMONGO_TEST_DB_PATH': str(Path(folder.name)/'accounts.sqlite3'),
            'GOOGLE_CLIENT_ID':'offline', 'GOOGLE_CLIENT_SECRET':'offline',
            'AUTH_SESSION_SECRET':'offline-session-secret-with-more-than32chars',
            'AUTH_PUBLIC_BASE_URL':'http://127.0.0.1:8000',
            'LIVE_TOPUP_INVITED_EMAILS':'owner@example.test', 'FREE_ACCESS_VOUCHER':'offline-voucher'})
        self.env.start(); self.addCleanup(self.env.stop)
        app = FastAPI(); accounts.configure_auth(app)
        self.client = TestClient(app); self.client.__enter__(); self.addCleanup(lambda:self.client.__exit__(None,None,None))
        self.token, self.csrf = account_store.create_google_session('owner-sub','owner@example.test','Owner')
        self.account = account_store.session_account(self.token)
        self.client.cookies.set(accounts.ACCOUNT_COOKIE,self.token)
        self.client.headers.update({'Origin':'http://127.0.0.1:8000','X-CSRF-Token':self.csrf})

    def test_live_wallet_starts_empty_and_invitation_does_not_gate_voucher(self):
        view = self.client.get('/api/auth/me').json()
        self.assertEqual(view['payment_mode'],'live')
        self.assertEqual(view['live_credits'],0)
        self.assertTrue(view['topup_invited'])
        with patch.dict(os.environ,{'LIVE_TOPUP_INVITED_EMAILS':''}):
            redeemed = self.client.post('/api/auth/voucher',json={'voucher':'offline-voucher'})
            self.assertEqual(redeemed.status_code,200)
            view = self.client.get('/api/auth/me').json()
            self.assertTrue(view['free_access'])
            self.assertFalse(view['topup_invited'])
            self.assertEqual(view['live_credits'],0)

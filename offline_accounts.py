"""Test-only account fixtures. Never imported by the application."""
import os
from pathlib import Path
import tempfile
from unittest.mock import patch

import account_store
import accounts


def authenticate(test, client=None, *, unit_server=None):
    if hasattr(test, "_offline_credentials"):
        token, csrf, account = test._offline_credentials
        if client:
            client.cookies.set(accounts.ACCOUNT_COOKIE, token)
            client.headers.update({"Origin":"http://127.0.0.1:8000", "X-CSRF-Token":csrf})
        return account
    folder = tempfile.TemporaryDirectory()
    test.addCleanup(folder.cleanup)
    env = patch.dict(os.environ, {
        'GOOGLE_CLIENT_ID': 'offline-client', 'GOOGLE_CLIENT_SECRET': 'offline-secret',
        'AUTH_SESSION_SECRET': 'offline-session-secret-longer-than-32-characters',
        'AUTH_PUBLIC_BASE_URL': 'http://127.0.0.1:8000',
        'PAYMONGO_TEST_DB_PATH': str(Path(folder.name) / 'accounts.sqlite3'),
        'FREE_ACCESS_VOUCHER': 'offline-shareable-voucher',
    })
    env.start(); test.addCleanup(env.stop)
    token, csrf = account_store.create_google_session('offline-host', 'host@example.test', 'Host')
    account = account_store.session_account(token)
    account_store.redeem_voucher(account['id'], 'offline-shareable-voucher')
    test._offline_credentials = (token, csrf, account)
    if client:
        client.cookies.set(accounts.ACCOUNT_COOKIE, token)
        client.headers.update({'Origin': 'http://127.0.0.1:8000', 'X-CSRF-Token': csrf})
    if unit_server:
        # Isolated state-machine tests use fake sockets; protocol tests exercise real auth.
        def verified(room, socket):
            room.owner_account_id = account['id']
            return account
        mock = patch.object(unit_server, '_host_account', side_effect=verified)
        mock.start(); test.addCleanup(mock.stop)
    return account

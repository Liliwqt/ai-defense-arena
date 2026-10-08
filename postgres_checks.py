"""Explicit real-PostgreSQL gate with mocked Google, PayMongo and AI.

TEST_POSTGRES_URL must point to a local disposable PostgreSQL server whose user
can create databases. Each case creates/drops its own database. Never use a
hosted account database here. Run: .venv/bin/python postgres_checks.py
"""

from concurrent.futures import ThreadPoolExecutor
import os
from pathlib import Path
import secrets
import sqlite3
import unittest
from unittest.mock import patch
from urllib.parse import urlsplit, urlunsplit

import psycopg
from psycopg import sql

import account_store as store
import postgres_store
import test_accounts
import test_room_access
import test_payment_sandbox
import test_purchase_store
import test_live_access
import test_live_payments
import test_live_runs
import test_live_refunds


class LocalDatabase:
    def setUp(self):
        url = os.environ.get('TEST_POSTGRES_URL', '')
        parsed = urlsplit(url)
        if parsed.hostname not in {'localhost', '127.0.0.1', '::1'}:
            raise RuntimeError('TEST_POSTGRES_URL must point to a disposable local database server.')
        name = 'defense_test_' + secrets.token_hex(8)
        with psycopg.connect(url, autocommit=True) as admin:
            admin.execute(sql.SQL("CREATE DATABASE {} TEMPLATE template0 ENCODING 'UTF8'").format(sql.Identifier(name)))
        def drop():
            with psycopg.connect(url, autocommit=True) as admin:
                admin.execute(sql.SQL('DROP DATABASE {} WITH (FORCE)').format(sql.Identifier(name)))
            postgres_store._initialized.clear()
        self.addCleanup(drop)
        self.pg_url = urlunsplit(parsed._replace(path='/' + name))
        env = patch.dict(os.environ, {'DATABASE_URL': self.pg_url})
        env.start()
        self.addCleanup(env.stop)
        super().setUp()


class PostgresAccounts(LocalDatabase, test_accounts.AccountCreditTests):
    def test_credit_failure_rolls_back_payment_until_retry(self):
        self.sign_in_fixture()
        order = self.topup().json()['topup']
        # PostgreSQL equivalent of the SQLite fault-injection trigger.
        with store.connect_store(self.db_path) as db:
            db.execute("ALTER TABLE test_credit_ledger ADD CONSTRAINT reject_credit CHECK(credits < 0)")
        self.assertEqual(self.webhook(order).status_code, 400)
        with store.connect_store(self.db_path) as db:
            self.assertEqual(db.execute('SELECT status FROM test_orders WHERE id=?', (order['id'],)).fetchone()[0], 'pending')
            db.execute('ALTER TABLE test_credit_ledger DROP CONSTRAINT reject_credit')
        self.assertEqual(self.webhook(order).status_code, 200)
        self.assertEqual(self.client.get('/api/auth/me').json()['test_credits'], 100)

    def test_existing_receipt_migration_preserves_anonymous_paid_record(self):
        with psycopg.connect(self.pg_url, autocommit=True) as db:
            db.execute('''CREATE TABLE test_orders (id TEXT PRIMARY KEY, token_hash TEXT NOT NULL, checkout_id TEXT UNIQUE,
                checkout_url TEXT, amount INTEGER NOT NULL, currency TEXT NOT NULL, status TEXT NOT NULL,
                payment_id TEXT UNIQUE, created_at INTEGER NOT NULL, paid_at INTEGER)''')
            db.execute("INSERT INTO test_orders VALUES ('legacy', %s, 'cs_legacy', 'https://checkout.paymongo.com/legacy', 10000, 'PHP', 'paid', 'pay_legacy', 1, 1)", (store.token_hash('legacy-token'),))
        self.sign_in_fixture()
        result = self.client.get('/api/payments/test/orders/legacy', headers={'Authorization': 'Bearer legacy-token'})
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json()['order']['credits'], 0)
        self.assertEqual(self.client.get('/api/auth/me').json()['test_credits'], 0)

    def test_concurrent_signed_webhooks_award_once(self):
        self.sign_in_fixture()
        order = self.topup().json()['topup']
        with ThreadPoolExecutor(max_workers=4) as workers:
            statuses = list(workers.map(lambda _: self.webhook(order).status_code, range(8)))
        self.assertEqual(statuses, [200] * 8)
        self.assertEqual(self.client.get('/api/auth/me').json()['test_credits'], 100)

    def test_new_connections_preserve_identity_voucher_and_credit_charge(self):
        token, _ = self.sign_in_fixture()
        account = store.session_account(token)
        order = self.topup().json()['topup']
        self.webhook(order)
        store.reserve_run(account['id'], 'persisted-run')
        store.charge_run(account['id'], 'persisted-run')
        with patch.dict(os.environ, {'FREE_ACCESS_VOUCHER': 'local-test-voucher'}):
            store.redeem_voucher(account['id'], 'local-test-voucher')
            # Simulate a fresh application process/schema cache, not a new DB.
            postgres_store._initialized.clear()
            store.release_orphaned_reservations()
            access = store.account_access(store.session_account(token)['id'])
            self.assertEqual(access['test_credits'], 90)
            self.assertEqual(access['reserved_credits'], 0)
            self.assertTrue(access['free_access'])
        self.assertFalse(self.db_path.exists())


class PostgresRoomAccess(LocalDatabase, test_room_access.RoomAccessTests):
    pass


class PostgresPayments(LocalDatabase, test_payment_sandbox.PaymentSandboxTests):
    pass


class PostgresPurchases(LocalDatabase, test_purchase_store.PurchaseStoreTests):
    pass


class PostgresLiveAccess(LocalDatabase,test_live_access.LiveAccessTests):
    pass


class PostgresLivePayments(LocalDatabase,test_live_payments.LivePaymentTests):
    pass


class PostgresLiveRuns(LocalDatabase,test_live_runs.LiveRunTests):
    pass


class PostgresLiveRefunds(LocalDatabase,test_live_refunds.LiveRefundTests):
    pass


if __name__ == '__main__':
    if not os.environ.get('TEST_POSTGRES_URL'):
        raise SystemExit('Set TEST_POSTGRES_URL to a disposable local PostgreSQL server first.')
    unittest.main(verbosity=2)

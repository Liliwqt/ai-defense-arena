"""Offline adapter checks; real PostgreSQL gates live in postgres_checks.py."""

import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import psycopg
import account_store
import postgres_store as backend


class PostgresAdapterTests(unittest.TestCase):
    def test_named_indexed_and_mapping_rows_preserve_store_contract(self):
        row = backend.StoreRow(['status', 'total'], ['reserved', 10])
        self.assertEqual(row[0], row['status'])
        self.assertEqual(dict(row), {'status': 'reserved', 'total': 10})
        self.assertEqual(dict([row]), {'reserved': 10})

    def test_query_translation_preserves_literals_comments_and_parameters(self):
        query = "SELECT '?', \"?\", ? -- ?\n/* ? */ WHERE value=?"
        self.assertEqual(backend.postgres_sql(query), "SELECT '?', \"?\", %s -- ?\n/* ? */ WHERE value=%s")
        connection = MagicMock()
        store = backend.PostgresStore(connection)
        value = "?'; DROP TABLE accounts; --"
        store.execute('SELECT name FROM accounts WHERE id=?', (value,))
        connection.execute.assert_called_once_with('SELECT name FROM accounts WHERE id=%s', (value,))

    def test_remote_database_requires_tls_and_errors_hide_url(self):
        for url in ('https://db.example/test', 'postgresql://user:private@db.example/test', 'postgresql://user:private@db.example/test?sslmode=disable', 'postgresql://user:private@db.example:bad/test', 'postgresql://user:private@db.example/?sslmode=require'):
            with self.subTest(url=url):
                with self.assertRaises(ValueError) as error:
                    backend.validate_database_url(url)
                self.assertNotIn('private', str(error.exception))
        backend.validate_database_url('postgresql://user:private@db.example/test?sslmode=require')
        backend.validate_database_url('postgresql://user@127.0.0.1/test')

    def test_configured_postgres_never_creates_sqlite_on_failure(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'never-created.sqlite3'
            with patch.dict(os.environ, {'DATABASE_URL': 'postgresql://user:private@db.example/test?sslmode=require'}), patch.object(backend.psycopg, 'connect', side_effect=psycopg.OperationalError('private')):
                with self.assertRaisesRegex(RuntimeError, 'Could not connect') as error:
                    with account_store.connect_store(path):
                        self.fail('must not yield a fallback store')
                self.assertNotIn('private', str(error.exception))
            self.assertFalse(path.exists())

    def test_lock_and_transaction_cover_migration_and_operation(self):
        backend._initialized.clear()
        connection = MagicMock()
        initialize = MagicMock()
        with patch.object(backend.psycopg, 'connect', return_value=connection):
            with backend.connect_postgres('postgresql://user@localhost/test', initialize) as db:
                db.execute('BEGIN IMMEDIATE')
                db.execute('UPDATE accounts SET name=?', ('Alex',))
        connection.transaction.assert_called_once()
        connection.execute.assert_any_call('SELECT pg_advisory_xact_lock(%s)', (backend.STORE_LOCK,))
        initialize.assert_called_once_with(db, postgres=True)
        connection.execute.assert_any_call('UPDATE accounts SET name=%s', ('Alex',))
        self.assertFalse(any(call.args == ('BEGIN IMMEDIATE', ()) for call in connection.execute.call_args_list))
        backend._initialized.clear()

    def test_failed_operation_does_not_cache_migration(self):
        backend._initialized.clear()
        with patch.object(backend.psycopg, 'connect', return_value=MagicMock()):
            with self.assertRaises(ValueError):
                with backend.connect_postgres('postgresql://user@localhost/test', MagicMock()):
                    raise ValueError('retry')
        self.assertEqual(backend._initialized, set())


if __name__ == '__main__':
    unittest.main()

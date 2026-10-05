"""PostgreSQL backend for the small account store; no SQLite fallback on failure.

Keep the store's SQLite-style bound queries and row interface. A transaction
advisory lock serializes store operations across connections, like SQLite's
BEGIN IMMEDIATE, including migrations and webhook deliveries. This deliberately
favors correctness over throughput for the single-instance sandbox.
"""

from contextlib import contextmanager
import hashlib
import re
import sqlite3
from urllib.parse import parse_qs, urlsplit

import psycopg


STORE_LOCK = 0x4149444546454E53
_initialized = set()
_sql_tokens = re.compile(r"' (?: '' | [^'] )* ' | \" (?: \"\" | [^\"] )* \" | --[^\n]* | /\*.*?\*/ | \?", re.X | re.S)


class StoreRow:
    """sqlite3.Row-compatible name/position access and dict conversion."""

    def __init__(self, names, values):
        self._names = names
        self._values = values

    def keys(self):
        return self._names

    def __getitem__(self, key):
        return self._values[self._names.index(key)] if isinstance(key, str) else self._values[key]

    def __iter__(self):
        return iter(self._values)

    def __len__(self):
        return len(self._values)


def store_row(cursor):
    names = [column.name for column in cursor.description] if cursor.description else []
    return lambda values: StoreRow(names, values)


def postgres_sql(query):
    # Only placeholders become %s; quoted identifiers/text and comments survive.
    return _sql_tokens.sub(lambda match: "%s" if match.group() == "?" else match.group(), query)


def validate_database_url(url):
    try:
        parsed = urlsplit(url)
        parsed.port
        if parsed.scheme not in {"postgres", "postgresql"} or not parsed.hostname or not parsed.username or not parsed.path.strip("/") or parsed.fragment:
            raise ValueError
        if parsed.hostname not in {"localhost", "127.0.0.1", "::1"} and parse_qs(parsed.query).get("sslmode") not in (["require"], ["verify-ca"], ["verify-full"]):
            raise ValueError
    except ValueError:
        raise ValueError("DATABASE_URL must be a PostgreSQL connection URL; remote databases require sslmode=require or certificate verification.") from None


class PostgresStore:
    def __init__(self, connection):
        self.connection = connection

    def execute(self, query, parameters=()):
        if query.strip().upper() == "BEGIN IMMEDIATE":
            # connect_postgres already owns the transaction and store lock.
            return None
        try:
            return self.connection.execute(postgres_sql(query), parameters)
        except psycopg.IntegrityError:
            # Preserve the existing safe webhook error and transaction rollback.
            raise sqlite3.IntegrityError("Account store constraint violation.") from None

    def columns(self, table):
        return {row[0] for row in self.connection.execute(
            "SELECT column_name FROM information_schema.columns WHERE table_schema=current_schema() AND table_name=%s", (table,))}


@contextmanager
def connect_postgres(url, initialize):
    validate_database_url(url)
    key = hashlib.sha256(url.encode()).digest()
    # Never print the DSN or forward a provider exception containing credentials.
    try:
        connection = psycopg.connect(url, autocommit=True, row_factory=store_row, connect_timeout=10)
    except psycopg.OperationalError:
        raise RuntimeError("Could not connect to the account database. Check DATABASE_URL and database availability.") from None
    with connection:
        with connection.transaction():
            connection.execute("SET LOCAL lock_timeout = '10s'")
            connection.execute("SET LOCAL statement_timeout = '20s'")
            connection.execute("SELECT pg_advisory_xact_lock(%s)", (STORE_LOCK,))
            db = PostgresStore(connection)
            if key not in _initialized:
                initialize(db, postgres=True)
            yield db
        # Cache only committed schema initialization, never a failed migration.
        _initialized.add(key)

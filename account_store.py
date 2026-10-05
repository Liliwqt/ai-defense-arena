"""Sandbox identities, opaque sessions and transactional SQLite/PostgreSQL credits."""

from contextlib import contextmanager
import hashlib
import os
from pathlib import Path
import secrets
import sqlite3
import time

DEFAULT_DB = Path(__file__).resolve().parent / ".local" / "payments-test.sqlite3"
SESSION_SECONDS = 8 * 60 * 60
RUN_COST = 10


def database_path() -> Path:
    return Path(os.environ.get("PAYMONGO_TEST_DB_PATH", str(DEFAULT_DB)))


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _initialize_store(db, *, postgres=False):
    db.execute("""CREATE TABLE IF NOT EXISTS accounts (
        id TEXT PRIMARY KEY, google_sub TEXT UNIQUE NOT NULL,
        email TEXT NOT NULL, name TEXT NOT NULL, created_at INTEGER NOT NULL
    )""")
    db.execute("""CREATE TABLE IF NOT EXISTS account_sessions (
        token_hash TEXT PRIMARY KEY, account_id TEXT NOT NULL REFERENCES accounts(id),
        csrf_token TEXT NOT NULL, expires_at INTEGER NOT NULL
    )""")
    db.execute("""CREATE TABLE IF NOT EXISTS test_orders (
        id TEXT PRIMARY KEY, token_hash TEXT NOT NULL,
        checkout_id TEXT UNIQUE, checkout_url TEXT,
        amount INTEGER NOT NULL, currency TEXT NOT NULL,
        status TEXT NOT NULL, payment_id TEXT UNIQUE,
        created_at INTEGER NOT NULL, paid_at INTEGER
    )""")
    columns = db.columns("test_orders") if postgres else {row["name"] for row in db.execute("PRAGMA table_info(test_orders)")}
    if "account_id" not in columns:
        db.execute("ALTER TABLE test_orders ADD COLUMN account_id TEXT REFERENCES accounts(id)")
    if "credits" not in columns:
        db.execute("ALTER TABLE test_orders ADD COLUMN credits INTEGER NOT NULL DEFAULT 0")
    if "request_hash" not in columns:
        db.execute("ALTER TABLE test_orders ADD COLUMN request_hash TEXT")
    db.execute("CREATE UNIQUE INDEX IF NOT EXISTS orders_by_request ON test_orders(request_hash)")
    db.execute("""CREATE TABLE IF NOT EXISTS test_credit_ledger (
        order_id TEXT PRIMARY KEY REFERENCES test_orders(id),
        account_id TEXT NOT NULL REFERENCES accounts(id),
        credits INTEGER NOT NULL CHECK(credits > 0), created_at INTEGER NOT NULL
    )""")
    db.execute("CREATE INDEX IF NOT EXISTS orders_by_account ON test_orders(account_id)")
    db.execute("CREATE INDEX IF NOT EXISTS credits_by_account ON test_credit_ledger(account_id)")
    db.execute("""CREATE TABLE IF NOT EXISTS voucher_grants (
        account_id TEXT PRIMARY KEY REFERENCES accounts(id), fingerprint TEXT NOT NULL,
        redeemed_at INTEGER NOT NULL
    )""")
    db.execute("""CREATE TABLE IF NOT EXISTS voucher_attempts (
        account_id TEXT PRIMARY KEY REFERENCES accounts(id), window_start INTEGER NOT NULL,
        failures INTEGER NOT NULL
    )""")
    db.execute("""CREATE TABLE IF NOT EXISTS defense_runs (
        id TEXT PRIMARY KEY, account_id TEXT NOT NULL REFERENCES accounts(id),
        mode TEXT NOT NULL CHECK(mode IN ('voucher', 'credits')),
        cost INTEGER NOT NULL CHECK(cost IN (0, 10)),
        status TEXT NOT NULL CHECK(status IN ('reserved', 'charged', 'released')),
        created_at INTEGER NOT NULL, charged_at INTEGER
    )""")
    db.execute("CREATE INDEX IF NOT EXISTS runs_by_account ON defense_runs(account_id)")


@contextmanager
def connect_store(path: Path):
    """DATABASE_URL selects PostgreSQL; otherwise preserve local SQLite data."""
    url = os.environ.get("DATABASE_URL", "").strip()
    if url:
        from postgres_store import connect_postgres
        with connect_postgres(url, _initialize_store) as db:
            yield db
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, timeout=5)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    try:
        with db:
            db.execute("BEGIN IMMEDIATE")
            _initialize_store(db)
        with db:
            yield db
    finally:
        db.close()


def create_google_session(sub: str, email: str, name: str) -> tuple[str, str]:
    now = int(time.time())
    token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    with connect_store(database_path()) as db:
        # Google subject, never display name or email, is the identity key.
        db.execute("INSERT INTO accounts VALUES (?, ?, ?, ?, ?) ON CONFLICT(google_sub) DO UPDATE SET email=excluded.email, name=excluded.name",
                   (secrets.token_hex(16), sub, email, name, now))
        account_id = db.execute("SELECT id FROM accounts WHERE google_sub=?", (sub,)).fetchone()["id"]
        db.execute("DELETE FROM account_sessions WHERE expires_at<=?", (now,))
        db.execute("INSERT INTO account_sessions VALUES (?, ?, ?, ?)", (token_hash(token), account_id, csrf, now + SESSION_SECONDS))
    return token, csrf


def session_account(token: str):
    if not token or len(token) > 200:
        return None
    with connect_store(database_path()) as db:
        return db.execute("""SELECT accounts.id, accounts.email, accounts.name, account_sessions.csrf_token
            FROM account_sessions JOIN accounts ON accounts.id=account_sessions.account_id
            WHERE token_hash=? AND expires_at>?""", (token_hash(token), int(time.time()))).fetchone()


def remove_session(token: str):
    with connect_store(database_path()) as db:
        db.execute("DELETE FROM account_sessions WHERE token_hash=?", (token_hash(token),))


class AccessError(ValueError):
    pass


def voucher_fingerprint() -> str | None:
    value = os.environ.get("FREE_ACCESS_VOUCHER", "")
    return token_hash(value) if value else None


def _access(db, account_id: str) -> dict:
    fingerprint = voucher_fingerprint()
    grant = db.execute("SELECT fingerprint FROM voucher_grants WHERE account_id=?", (account_id,)).fetchone()
    free = bool(fingerprint and grant and secrets.compare_digest(fingerprint, grant[0]))
    awarded = db.execute("SELECT COALESCE(SUM(credits),0) FROM test_credit_ledger WHERE account_id=?", (account_id,)).fetchone()[0]
    totals = dict(db.execute("SELECT status, SUM(cost) FROM defense_runs WHERE account_id=? GROUP BY status", (account_id,)).fetchall())
    reserved, charged = totals.get("reserved", 0), totals.get("charged", 0)
    return {"free_access": free, "voucher_enabled": fingerprint is not None,
            "test_credits": awarded - reserved - charged, "reserved_credits": reserved,
            "spent_credits": charged, "run_cost": RUN_COST}


def account_access(account_id: str) -> dict:
    with connect_store(database_path()) as db:
        return _access(db, account_id)


def account_overview(account_id: str) -> dict:
    """Read balance, receipts and run records in one serialized snapshot."""
    with connect_store(database_path()) as db:
        db.execute("BEGIN IMMEDIATE")
        access = _access(db, account_id)
        orders = db.execute("""SELECT o.id, o.amount, o.currency, o.credits, o.status,
            o.created_at, o.paid_at, COALESCE(l.credits,0) AS awarded_credits
            FROM test_orders o LEFT JOIN test_credit_ledger l ON l.order_id=o.id
            WHERE o.account_id=? ORDER BY o.created_at DESC, o.id DESC LIMIT 20""", (account_id,)).fetchall()
        runs = db.execute("""SELECT id, mode, cost, status, created_at, charged_at
            FROM defense_runs WHERE account_id=? ORDER BY created_at DESC, id DESC LIMIT 20""", (account_id,)).fetchall()
    return {**access, "orders": [dict(row) for row in orders], "runs": [dict(row) for row in runs]}


def require_run_access(account_id: str) -> dict:
    access = account_access(account_id)
    if not access["free_access"] and access["test_credits"] < RUN_COST:
        raise AccessError("Redeem a free-access voucher or obtain at least 10 available test credits before preparing or starting a defense.")
    return access


def redeem_voucher(account_id: str, value: str) -> None:
    now = int(time.time())
    error = None
    with connect_store(database_path()) as db:
        expected = voucher_fingerprint()
        if expected is None:
            error = "Voucher access is not configured on this server."
        else:
            attempt = db.execute("SELECT window_start, failures FROM voucher_attempts WHERE account_id=?", (account_id,)).fetchone()
            window, failures = (attempt[0], attempt[1]) if attempt and now - attempt[0] < 300 else (now, 0)
            if failures >= 5:
                error = "Too many voucher attempts. Wait five minutes before trying again."
            elif not secrets.compare_digest(token_hash(value), expected):
                db.execute("INSERT INTO voucher_attempts VALUES (?,?,?) ON CONFLICT(account_id) DO UPDATE SET window_start=excluded.window_start, failures=excluded.failures",
                           (account_id, window, failures + 1))
                error = "The voucher could not be redeemed. Check it and try again."
            else:
                db.execute("INSERT INTO voucher_grants VALUES (?,?,?) ON CONFLICT(account_id) DO UPDATE SET fingerprint=excluded.fingerprint, redeemed_at=excluded.redeemed_at",
                           (account_id, expected, now))
                db.execute("DELETE FROM voucher_attempts WHERE account_id=?", (account_id,))
    # Commit failed-attempt counters before reporting a safe error.
    if error:
        raise AccessError(error)


def reserve_run(account_id: str, run_id: str) -> dict:
    with connect_store(database_path()) as db:
        db.execute("BEGIN IMMEDIATE")
        previous = db.execute("SELECT * FROM defense_runs WHERE id=?", (run_id,)).fetchone()
        if previous and previous["account_id"] != account_id:
            raise AccessError("This defense belongs to another account.")
        if previous and previous["status"] != "released":
            return dict(previous)
        access = _access(db, account_id)
        if not access["free_access"] and access["test_credits"] < RUN_COST:
            raise AccessError("Not enough available test credits. This run needs 10, or a free-access voucher.")
        mode, cost = ("voucher", 0) if access["free_access"] else ("credits", RUN_COST)
        # A voucher authorizes this whole run even if it is later rotated.
        status = "charged" if cost == 0 else "reserved"
        db.execute("""INSERT INTO defense_runs VALUES (?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET
            mode=excluded.mode, cost=excluded.cost, status=excluded.status, charged_at=excluded.charged_at""",
                   (run_id, account_id, mode, cost, status, int(time.time()), None))
        return dict(db.execute("SELECT * FROM defense_runs WHERE id=?", (run_id,)).fetchone())


def charge_run(account_id: str, run_id: str) -> None:
    with connect_store(database_path()) as db:
        db.execute("BEGIN IMMEDIATE")
        row = db.execute("SELECT * FROM defense_runs WHERE id=? AND account_id=?", (run_id, account_id)).fetchone()
        if row is None or row["status"] == "released":
            raise AccessError("Run access has expired. Retry the opening question to reserve access again.")
        db.execute("UPDATE defense_runs SET status='charged', charged_at=? WHERE id=? AND status='reserved'", (int(time.time()), run_id))


def release_run(run_id: str | None) -> None:
    if run_id:
        with connect_store(database_path()) as db:
            db.execute("UPDATE defense_runs SET status='released' WHERE id=? AND status='reserved'", (run_id,))


def release_orphaned_reservations() -> None:
    with connect_store(database_path()) as db:
        db.execute("UPDATE defense_runs SET status='released' WHERE status='reserved'")

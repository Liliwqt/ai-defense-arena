"""Transactional provider expenditure, separate from defense access credits.

Amounts are integer nano-USD. Dispatched requests retain their full reservation
unless the provider supplies valid cost evidence; process death is not a refund.
"""

from contextlib import contextmanager
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_CEILING
import json
import secrets
import time

from backend.account_store import connect_store, database_path
from backend.resource_limits import limit as resource_limit


class AllowanceError(ValueError):
    pass


class AllowanceExhausted(AllowanceError):
    """The next bounded request cannot fit in the remaining allowance."""


def reported_nano(usage) -> int | None:
    """Convert one provider cost receipt to nano-USD; absent/unsafe evidence is None."""
    cost = usage.get('cost') if isinstance(usage, dict) else None
    try:
        value = Decimal(str(cost))
        if value.is_finite() and 0 <= value <= 1_000_000:
            return int((value * 1_000_000_000).to_integral_value(rounding=ROUND_CEILING))
    except InvalidOperation:
        pass
    return None


@contextmanager
def transaction():
    with connect_store(database_path()) as db:
        db.execute('BEGIN IMMEDIATE')
        db.execute('''CREATE TABLE IF NOT EXISTS provider_allowances (
            id TEXT PRIMARY KEY, owner TEXT NOT NULL, ceiling BIGINT NOT NULL CHECK(ceiling>0),
            policy TEXT NOT NULL, created_at BIGINT NOT NULL,
            blocked INTEGER NOT NULL DEFAULT 0)''')
        db.execute('''CREATE TABLE IF NOT EXISTS provider_requests (
            id TEXT PRIMARY KEY, allowance_id TEXT NOT NULL REFERENCES provider_allowances(id),
            reserved BIGINT NOT NULL CHECK(reserved>0), billed BIGINT CHECK(billed>=0),
            created_at BIGINT NOT NULL)''')
        db.execute('CREATE INDEX IF NOT EXISTS provider_requests_by_allowance ON provider_requests(allowance_id)')
        db.execute('''CREATE TABLE IF NOT EXISTS free_provider_requests (
            id TEXT PRIMARY KEY REFERENCES provider_requests(id), owner TEXT NOT NULL,
            created_at BIGINT NOT NULL)''')
        db.execute('CREATE INDEX IF NOT EXISTS free_provider_requests_by_time ON free_provider_requests(created_at)')
        yield db


@dataclass(frozen=True)
class ProviderAllowance:
    id: str
    owner: str

    def policy(self) -> dict | None:
        with transaction() as db:
            row = db.execute('SELECT * FROM provider_allowances WHERE id=?', (self.id,)).fetchone()
            if row is None:
                return None
            if row['owner'] != self.owner:
                raise AllowanceError('This preparation allowance is unavailable.')
            return json.loads(row['policy'])

    def establish(self, ceiling: int, policy: dict) -> dict:
        """Create once; remapping and configuration edits retain the first policy."""
        with transaction() as db:
            db.execute('INSERT INTO provider_allowances (id,owner,ceiling,policy,created_at) VALUES (?,?,?,?,?) ON CONFLICT(id) DO NOTHING',
                (self.id, self.owner, ceiling, json.dumps(policy, sort_keys=True), int(time.time())))
            row = self._owned(db)
            return json.loads(row['policy'])

    def _owned(self, db):
        row = db.execute('SELECT * FROM provider_allowances WHERE id=?', (self.id,)).fetchone()
        if row is None or row['owner'] != self.owner:
            raise AllowanceError('This provider allowance is unavailable. Contact the operator.')
        return row

    def snapshot(self) -> dict:
        with transaction() as db:
            row = self._owned(db)
            if row['blocked']:
                raise AllowanceError('This allowance needs operator review before another request.')
            used = db.execute('SELECT COALESCE(SUM(COALESCE(billed,reserved)),0) FROM provider_requests WHERE allowance_id=?', (self.id,)).fetchone()[0]
            return {'ceiling': row['ceiling'], 'used': used, 'remaining': max(0, row['ceiling'] - used)}

    def reserve(self, cost: int, limit: int | None = None, *, coaching=False) -> str:
        """Admit one request; an optional protected limit is the most it may use."""
        if type(cost) is not int or cost <= 0:
            raise AllowanceError('Invalid preparation cost bound. Check server configuration.')
        if limit is not None and (type(limit) is not int or limit <= 0):
            raise AllowanceError('Invalid defense spending limit. Check server configuration.')
        with transaction() as db:
            row = self._owned(db)
            if row['blocked']:
                raise AllowanceError('This allowance needs operator review before another request.')
            policy = json.loads(row['policy'])
            free = policy.get('tier') == 'free'
            if free:
                self._admit_free(db, policy, coaching)
            used = db.execute('SELECT COALESCE(SUM(COALESCE(billed,reserved)),0) FROM provider_requests WHERE allowance_id=?', (self.id,)).fetchone()[0]
            ceiling = row['ceiling'] if limit is None else min(row['ceiling'], limit)
            if used + cost > ceiling:
                if limit is None:
                    raise AllowanceExhausted('Preparation allowance cannot fund another mapping request. Your material is retained; contact the operator. Retrying will not reset the allowance.')
                raise AllowanceExhausted('The defense allowance cannot fund another question. Your discussion is retained; contact the operator. Retrying will not reset the allowance.')
            identity = secrets.token_hex(24)
            db.execute('INSERT INTO provider_requests VALUES (?,?,?,?,?)',
                       (identity, self.id, cost, None, int(time.time())))
            if free:
                db.execute('INSERT INTO free_provider_requests VALUES (?,?,?)',
                           (identity, self.owner, int(time.time())))
            return identity

    def _admit_free(self, db, policy, coaching):
        """Count dispatched attempts, including failures, across restarts/scopes.

        This transaction is serialized by the shared SQLite/PostgreSQL store.
        Zero-dollar receipts never replenish request quotas. Non-coaching work
        cannot consume the run's protected coaching request slots.
        """
        maximum = policy.get('request_limit')
        if type(maximum) is not int or maximum <= 0:
            raise AllowanceError('The free practice request policy is unavailable.')
        reserve = 0 if coaching else policy.get('coaching_request_reserve', 0)
        count = db.execute('SELECT COUNT(*) FROM provider_requests WHERE allowance_id=?', (self.id,)).fetchone()[0]
        if count >= maximum - reserve:
            raise AllowanceExhausted('Free practice request limit reached. Your work is retained; retrying does not reset this limit.')
        now = int(time.time())
        day = now - now % 86400
        minute = db.execute('SELECT COUNT(*) FROM free_provider_requests WHERE created_at>?', (now - 60,)).fetchone()[0]
        daily = db.execute('SELECT COUNT(*) FROM free_provider_requests WHERE created_at>=?', (day,)).fetchone()[0]
        own = db.execute('SELECT COUNT(*) FROM free_provider_requests WHERE owner=? AND created_at>=?', (self.owner, day)).fetchone()[0]
        if minute >= resource_limit('OPENROUTER_FREE_PER_MINUTE', 15, 1000):
            raise AllowanceExhausted('Free practice is busy. Wait a minute, then retry. Your work is retained.')
        if (daily >= resource_limit('OPENROUTER_FREE_DAILY_REQUESTS', 50, 100000)
                or own >= resource_limit('OPENROUTER_FREE_OWNER_DAILY_REQUESTS', 40, 100000)):
            raise AllowanceExhausted('Free practice daily request limit reached. Try again after 00:00 UTC. Your work is retained.')

    def settle(self, request_id: str, billed: int) -> None:
        if type(billed) is not int or billed < 0:
            raise AllowanceError('Invalid provider cost evidence.')
        error = None
        with transaction() as db:
            row = self._owned(db)
            request = db.execute('SELECT * FROM provider_requests WHERE id=? AND allowance_id=?', (request_id, self.id)).fetchone()
            if request is None:
                raise AllowanceError('Provider request accounting is unavailable.')
            if json.loads(row['policy']).get('tier') == 'free' and billed != 0:
                error = 'A free provider reported a nonzero cost. Free practice is blocked for operator review.'
            elif request['billed'] is not None and request['billed'] != billed:
                billed = max(billed, request['billed'], request['reserved'])
                error = 'Conflicting provider cost evidence. Contact the operator.'
            elif billed > request['reserved']:
                error = 'Provider cost exceeded its reserved bound. Contact the operator.'
            if error:
                db.execute('UPDATE provider_allowances SET blocked=1 WHERE id=?', (self.id,))
            db.execute('UPDATE provider_requests SET billed=? WHERE id=?', (billed, request_id))
        if error:
            raise AllowanceError(error)

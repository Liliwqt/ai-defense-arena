"""Transactional provider expenditure, separate from defense access credits.

Amounts are integer nano-USD. Dispatched requests retain their full reservation
unless the provider supplies valid cost evidence; process death is not a refund.
"""

from contextlib import contextmanager
from dataclasses import dataclass
import json
import secrets
import time

from backend.account_store import connect_store, database_path


class AllowanceError(ValueError):
    pass


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
            raise AllowanceError('This preparation allowance is unavailable.')
        return row

    def snapshot(self) -> dict:
        with transaction() as db:
            row = self._owned(db)
            if row['blocked']:
                raise AllowanceError('Preparation allowance needs operator review before another request.')
            used = db.execute('SELECT COALESCE(SUM(COALESCE(billed,reserved)),0) FROM provider_requests WHERE allowance_id=?', (self.id,)).fetchone()[0]
            return {'ceiling': row['ceiling'], 'used': used, 'remaining': max(0, row['ceiling'] - used)}

    def reserve(self, cost: int) -> str:
        if type(cost) is not int or cost <= 0:
            raise AllowanceError('Invalid preparation cost bound. Check server configuration.')
        with transaction() as db:
            row = self._owned(db)
            if row['blocked']:
                raise AllowanceError('Preparation allowance needs operator review before another request.')
            used = db.execute('SELECT COALESCE(SUM(COALESCE(billed,reserved)),0) FROM provider_requests WHERE allowance_id=?', (self.id,)).fetchone()[0]
            if used + cost > row['ceiling']:
                raise AllowanceError('Preparation allowance cannot fund another mapping request. Your material is retained; contact the operator. Retrying will not reset the allowance.')
            identity = secrets.token_hex(24)
            db.execute('INSERT INTO provider_requests VALUES (?,?,?,?,?)',
                       (identity, self.id, cost, None, int(time.time())))
            return identity

    def settle(self, request_id: str, billed: int) -> None:
        if type(billed) is not int or billed < 0:
            raise AllowanceError('Invalid provider cost evidence.')
        error = None
        with transaction() as db:
            self._owned(db)
            request = db.execute('SELECT * FROM provider_requests WHERE id=? AND allowance_id=?', (request_id, self.id)).fetchone()
            if request is None:
                raise AllowanceError('Provider request accounting is unavailable.')
            if request['billed'] is not None and request['billed'] != billed:
                billed = max(billed, request['billed'], request['reserved'])
                error = 'Conflicting provider cost evidence. Contact the operator.'
            elif billed > request['reserved']:
                error = 'Provider cost exceeded its reserved bound. Contact the operator.'
            if error:
                db.execute('UPDATE provider_allowances SET blocked=1 WHERE id=?', (self.id,))
            db.execute('UPDATE provider_requests SET billed=? WHERE id=?', (billed, request_id))
        if error:
            raise AllowanceError(error)

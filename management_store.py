"""Owner-managed invitations and audited live-credit grants, never payment receipts."""
import json
import os
import secrets
import time

from account_store import AccessError, connect_store, database_path, token_hash


def initialize(db):
    db.execute('''CREATE TABLE IF NOT EXISTS managed_testers (
        email TEXT PRIMARY KEY, enabled INTEGER NOT NULL CHECK(enabled IN (0,1)),
        actor_id TEXT NOT NULL REFERENCES accounts(id), updated_at INTEGER NOT NULL)''')
    db.execute('''CREATE TABLE IF NOT EXISTS manager_audit (
        id TEXT PRIMARY KEY, actor_id TEXT NOT NULL REFERENCES accounts(id),
        account_id TEXT REFERENCES accounts(id), email TEXT, action TEXT NOT NULL,
        delta INTEGER, reason TEXT NOT NULL, request_hash TEXT UNIQUE,
        balance_after INTEGER, created_at INTEGER NOT NULL)''')
    db.execute('''CREATE TABLE IF NOT EXISTS live_grants (
        id TEXT PRIMARY KEY REFERENCES manager_audit(id), account_id TEXT NOT NULL REFERENCES accounts(id),
        credits INTEGER NOT NULL CHECK(credits>0), available INTEGER NOT NULL CHECK(available>=0),
        created_at INTEGER NOT NULL)''')
    db.execute('''CREATE TABLE IF NOT EXISTS live_grant_allocations (
        run_id TEXT NOT NULL REFERENCES live_runs(id), grant_id TEXT NOT NULL REFERENCES live_grants(id),
        credits INTEGER NOT NULL CHECK(credits>0), status TEXT NOT NULL, PRIMARY KEY(run_id,grant_id))''')
    db.execute('CREATE INDEX IF NOT EXISTS grants_by_account ON live_grants(account_id)')
    db.execute('CREATE INDEX IF NOT EXISTS manager_audit_by_account ON manager_audit(account_id)')


def invitation(db, email):
    email = email.strip().casefold()
    override = db.execute('SELECT enabled FROM managed_testers WHERE email=?', (email,)).fetchone()
    if override is not None:
        return bool(override['enabled'])
    return email in {value.strip().casefold() for value in os.environ.get('LIVE_TOPUP_INVITED_EMAILS', '').split(',') if value.strip()}


class ManagementStore:
    def testers(self):
        with connect_store(database_path()) as db:
            values = {email.strip().casefold(): True for email in os.environ.get('LIVE_TOPUP_INVITED_EMAILS', '').split(',') if email.strip()}
            values.update({row['email']: bool(row['enabled']) for row in db.execute('SELECT email,enabled FROM managed_testers')})
            return [{'email': email, 'enabled': values[email]} for email in sorted(values)]

    def set_tester(self, actor, email, enabled):
        with connect_store(database_path()) as db:
            db.execute('BEGIN IMMEDIATE')
            existing = db.execute('SELECT enabled FROM managed_testers WHERE email=?', (email,)).fetchone()
            if existing is not None and bool(existing['enabled']) == enabled:
                return
            now = int(time.time())
            db.execute('''INSERT INTO managed_testers VALUES(?,?,?,?) ON CONFLICT(email)
                DO UPDATE SET enabled=excluded.enabled,actor_id=excluded.actor_id,updated_at=excluded.updated_at''', (email, int(enabled), actor, now))
            db.execute('''INSERT INTO manager_audit(id,actor_id,email,action,reason,created_at)
                VALUES(?,?,?,'tester',?,?)''', ('admin_'+secrets.token_hex(16), actor, email, 'Top-up invitation enabled' if enabled else 'Top-up invitation disabled', now))

    def users(self, query='', limit=50, offset=0):
        with connect_store(database_path()) as db:
            db.execute('BEGIN IMMEDIATE')
            # Escape wildcards: searches are literal substrings, including % and _.
            pattern = '%'+query.casefold().replace('!', '!!').replace('%', '!%').replace('_', '!_')+'%'
            where = "WHERE lower(name) LIKE ? ESCAPE '!' OR lower(email) LIKE ? ESCAPE '!'"
            total = db.execute('SELECT COUNT(*) FROM accounts '+where, (pattern, pattern)).fetchone()[0]
            rows = db.execute('SELECT id,name,email,created_at FROM accounts '+where+' ORDER BY created_at DESC,id LIMIT ? OFFSET ?', (pattern, pattern, limit, offset)).fetchall()
            from live_store import LiveStore
            from account_store import _access
            users = []
            for row in rows:
                balances = LiveStore().snapshot(db, row['id'])
                access = _access(db, row['id'])
                users.append(dict(row) | {key: balances[key] for key in ('live_credits','live_reserved_credits','live_held_credits','topup_invited')} | {'test_credits': access['test_credits'], 'free_access': access['free_access']})
            return {'users': users, 'total': total, 'limit': limit, 'offset': offset}

    def audit(self, limit=50, offset=0):
        with connect_store(database_path()) as db:
            rows = db.execute('''SELECT a.id,a.actor_id,a.account_id,a.email,a.action,a.delta,a.reason,a.balance_after,a.created_at,
                u.name AS account_name,u.email AS account_email FROM manager_audit a LEFT JOIN accounts u ON u.id=a.account_id
                ORDER BY a.created_at DESC,a.id DESC LIMIT ? OFFSET ?''', (limit, offset)).fetchall()
            return [dict(row) for row in rows]

    def adjust(self, actor, account_id, delta, reason, request_id):
        fingerprint = token_hash(json.dumps([actor, request_id]))
        with connect_store(database_path()) as db:
            db.execute('BEGIN IMMEDIATE')
            previous = db.execute('SELECT * FROM manager_audit WHERE request_hash=?', (fingerprint,)).fetchone()
            if previous:
                if (previous['account_id'], previous['delta'], previous['reason']) != (account_id, delta, reason):
                    raise AccessError('This adjustment request was already used. Refresh before changing its details.')
                return {'id': previous['id'], 'balance_after': previous['balance_after']}
            if not db.execute('SELECT id FROM accounts WHERE id=?', (account_id,)).fetchone():
                raise LookupError('Account not found.')
            grants = db.execute('SELECT * FROM live_grants WHERE account_id=? AND available>0 ORDER BY created_at,id', (account_id,)).fetchall()
            lots = db.execute('SELECT * FROM live_lots WHERE account_id=? AND available>0 ORDER BY created_at,topup_id', (account_id,)).fetchall()
            balance = sum(row['available'] for row in grants)+sum(row['available'] for row in lots)
            if balance+delta < 0:
                raise AccessError('Only available credits can be removed. Reserved or held credits are protected.')
            ident = 'admin_'+secrets.token_hex(16); now = int(time.time())
            db.execute('''INSERT INTO manager_audit(id,actor_id,account_id,action,delta,reason,request_hash,balance_after,created_at)
                VALUES(?,?,?,'credits',?,?,?,?,?)''', (ident, actor, account_id, delta, reason, fingerprint, balance+delta, now))
            if delta > 0:
                db.execute('INSERT INTO live_grants VALUES(?,?,?,?,?)', (ident, account_id, delta, delta, now))
            else:
                remaining = -delta
                for row in grants:
                    take = min(remaining, row['available'])
                    db.execute('UPDATE live_grants SET available=available-? WHERE id=?', (take, row['id'])); remaining -= take
                for row in lots:
                    take = min(remaining, row['available'])
                    db.execute('UPDATE live_lots SET available=available-? WHERE topup_id=?', (take, row['topup_id'])); remaining -= take
            return {'id': ident, 'balance_after': balance+delta}

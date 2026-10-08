"""Transactional live wallet, receipts and defense lifecycle, separate from demo history."""
from contextlib import contextmanager
import json
import secrets
import time

from account_store import AccessError, connect_store, database_path, token_hash
from financial_policy import LIVE_PACKAGES, invited


def initialize(db):
    db.execute("""CREATE TABLE IF NOT EXISTS live_topups (
        id TEXT PRIMARY KEY, account_id TEXT NOT NULL REFERENCES accounts(id),
        package_id TEXT NOT NULL, package_version TEXT NOT NULL,
        amount INTEGER NOT NULL CHECK(amount>0), currency TEXT NOT NULL CHECK(currency='PHP'),
        credits INTEGER NOT NULL CHECK(credits>0), status TEXT NOT NULL,
        request_hash TEXT UNIQUE NOT NULL, intent_id TEXT UNIQUE, payment_id TEXT UNIQUE,
        qr_image_url TEXT, expires_at INTEGER, created_at INTEGER NOT NULL, paid_at INTEGER,
        recovery_after INTEGER NOT NULL DEFAULT 0, recovery_attempts INTEGER NOT NULL DEFAULT 0)""")
    db.execute("""CREATE TABLE IF NOT EXISTS live_lots (
        topup_id TEXT PRIMARY KEY REFERENCES live_topups(id), account_id TEXT NOT NULL REFERENCES accounts(id),
        credits INTEGER NOT NULL CHECK(credits>0), available INTEGER NOT NULL CHECK(available>=0),
        ever_spent INTEGER NOT NULL DEFAULT 0, held INTEGER NOT NULL DEFAULT 0 CHECK(held>=0),
        refunded INTEGER NOT NULL DEFAULT 0 CHECK(refunded>=0), created_at INTEGER NOT NULL)""")
    db.execute("""CREATE TABLE IF NOT EXISTS live_services (
        id TEXT PRIMARY KEY, heartbeat INTEGER NOT NULL, status TEXT NOT NULL)""")
    db.execute("""CREATE TABLE IF NOT EXISTS live_runs (
        id TEXT PRIMARY KEY, account_id TEXT NOT NULL REFERENCES accounts(id),
        mode TEXT NOT NULL, cost INTEGER NOT NULL CHECK(cost IN (0,10)),
        status TEXT NOT NULL, outcome TEXT NOT NULL, service_id TEXT NOT NULL,
        room_code TEXT NOT NULL, epoch INTEGER NOT NULL DEFAULT 0, error_kind TEXT,
        created_at INTEGER NOT NULL, charged_at INTEGER, updated_at INTEGER NOT NULL)""")
    db.execute("""CREATE UNIQUE INDEX IF NOT EXISTS live_active_host ON live_runs(account_id)
        WHERE outcome IN ('opening','active','coaching','unavailable')""")
    db.execute("""CREATE TABLE IF NOT EXISTS live_allocations (
        run_id TEXT NOT NULL REFERENCES live_runs(id), topup_id TEXT NOT NULL REFERENCES live_lots(topup_id),
        credits INTEGER NOT NULL CHECK(credits>0), status TEXT NOT NULL, PRIMARY KEY(run_id,topup_id))""")
    db.execute("""CREATE TABLE IF NOT EXISTS live_adjustments (
        id TEXT PRIMARY KEY, account_id TEXT NOT NULL REFERENCES accounts(id),
        run_id TEXT UNIQUE REFERENCES live_runs(id), topup_id TEXT REFERENCES live_topups(id),
        credits INTEGER NOT NULL, reason TEXT NOT NULL, actor TEXT NOT NULL, created_at INTEGER NOT NULL)""")
    db.execute("""CREATE TABLE IF NOT EXISTS live_refunds (
        id TEXT PRIMARY KEY, topup_id TEXT UNIQUE NOT NULL REFERENCES live_topups(id),
        provider_id TEXT UNIQUE, status TEXT NOT NULL, amount INTEGER NOT NULL,
        reason TEXT NOT NULL, actor TEXT NOT NULL, created_at INTEGER NOT NULL)""")
    db.execute('CREATE TABLE IF NOT EXISTS live_ai_requests (account_id TEXT NOT NULL REFERENCES accounts(id), created_at INTEGER NOT NULL)')


class LiveStore:
    @contextmanager
    def transaction(self):
        with connect_store(database_path()) as db:
            db.execute('BEGIN IMMEDIATE')
            yield db

    def overview(self, account_id):
        with self.transaction() as db:
            return self.snapshot(db,account_id)

    def snapshot(self,db,account_id):
        lots = db.execute('SELECT COALESCE(SUM(available),0), COALESCE(SUM(held),0) FROM live_lots WHERE account_id=?', (account_id,)).fetchone()
        reserved = db.execute("SELECT COALESCE(SUM(a.credits),0) FROM live_allocations a JOIN live_runs r ON r.id=a.run_id WHERE r.account_id=? AND a.status='reserved'",(account_id,)).fetchone()[0]
        rows = db.execute('SELECT * FROM live_topups WHERE account_id=? ORDER BY created_at DESC,id DESC LIMIT 20',(account_id,)).fetchall()
        orders = [self.public(row) for row in rows]
        refunds = db.execute('SELECT f.* FROM live_refunds f JOIN live_topups t ON t.id=f.topup_id WHERE t.account_id=?',(account_id,)).fetchall()
        for order in orders:
            refund = next((r for r in refunds if r['topup_id']==order['id']),None)
            order['refund_status'] = refund['status'] if refund else None
        runs = [dict(row) for row in db.execute('SELECT id,mode,cost,status,outcome,error_kind,created_at,charged_at FROM live_runs WHERE account_id=? ORDER BY created_at DESC,id DESC LIMIT 20',(account_id,))]
        changes = [dict(row) for row in db.execute('SELECT id,credits,reason,created_at FROM live_adjustments WHERE account_id=? AND credits>0 ORDER BY created_at DESC,id DESC LIMIT 20',(account_id,))]
        active = db.execute("SELECT id FROM live_runs WHERE account_id=? AND outcome IN ('opening','active','coaching','unavailable')",(account_id,)).fetchone()
        account = db.execute('SELECT email FROM accounts WHERE id=?',(account_id,)).fetchone()
        return dict(live_credits=lots[0],live_reserved_credits=reserved,live_held_credits=lots[1],
                    live_orders=orders,live_runs=runs,credit_returns=changes,
                    active_run=active['id'] if active else None,topup_invited=bool(account and invited(account['email'])))

    @staticmethod
    def public(row):
        fields = ('id','package_id','package_version','amount','currency','credits','status','qr_image_url','expires_at','created_at','paid_at')
        extra=dict(row)
        return {key:row[key] for key in fields} | {'mode':'live','simulated':False,'awarded_credits':row['credits'] if row['status']=='paid' else 0,
            'refund_status':extra.get('refund_status'),'refund_eligibility':extra.get('refund_eligibility')}

    def get(self, topup_id):
        with self.transaction() as db:
            row=db.execute('SELECT * FROM live_topups WHERE id=?',(topup_id,)).fetchone()
            if not row:return None
            refund=db.execute('SELECT status FROM live_refunds WHERE topup_id=?',(topup_id,)).fetchone()
            lot=db.execute('SELECT * FROM live_lots WHERE topup_id=?',(topup_id,)).fetchone()
            return dict(row)|{'refund_status':refund['status'] if refund else None,
                'refund_eligibility':'held' if refund and refund['status'] in {'held','pending','processing'} else
                    'used_review' if lot and lot['ever_spent'] else 'unused_review' if lot and lot['available']==lot['credits'] else 'unavailable'}

    def get_topup_by_intent(self, intent_id):
        with self.transaction() as db:
            row=db.execute('SELECT * FROM live_topups WHERE intent_id=?',(intent_id,)).fetchone()
            return dict(row) if row else None

    def begin_topup(self, account_id, package_id, request_id):
        package=LIVE_PACKAGES.get(package_id)
        if not package:
            raise AccessError('Choose an available credit package.')
        fingerprint=token_hash(json.dumps(['live','payment_intent',account_id,request_id]))
        now=int(time.time())
        with self.transaction() as db:
            previous=db.execute('SELECT * FROM live_topups WHERE request_hash=?',(fingerprint,)).fetchone()
            if previous:
                if previous['status']=='creating':
                    raise AccessError('This QR is being created. Keep this request and retry shortly.')
                return dict(previous),False
            account=db.execute('SELECT email FROM accounts WHERE id=?',(account_id,)).fetchone()
            if not account or not invited(account['email']):
                raise PermissionError('Top-ups are temporarily unavailable for your account.')
            attempts=db.execute('SELECT COUNT(*) FROM live_topups WHERE account_id=? AND created_at>?',(account_id,now-600)).fetchone()[0]
            if attempts>=5:
                raise AccessError('Too many top-up attempts. Wait ten minutes before trying again.')
            ident='live_'+secrets.token_hex(16)
            db.execute("""INSERT INTO live_topups(id,account_id,package_id,package_version,amount,currency,credits,status,request_hash,created_at)
                VALUES (?,?,?,?,?,?,?,'creating',?,?)""",(ident,account_id,package.id,package.version,package.amount,package.currency,package.credits,fingerprint,now))
            return dict(db.execute('SELECT * FROM live_topups WHERE id=?',(ident,)).fetchone()),True

    def bind_topup_intent(self,topup_id,intent_id):
        with self.transaction() as db:
            db.execute("UPDATE live_topups SET intent_id=? WHERE id=? AND status='creating' AND intent_id IS NULL",(intent_id,topup_id))

    def register_topup(self,topup_id,intent_id,image,expires_at):
        with self.transaction() as db:
            db.execute("UPDATE live_topups SET qr_image_url=?,expires_at=?,status='pending' WHERE id=? AND intent_id=? AND status='creating'",(image,expires_at,topup_id,intent_id))
            return dict(db.execute('SELECT * FROM live_topups WHERE id=?',(topup_id,)).fetchone())

    def creation_failed(self,topup_id):
        with self.transaction() as db:
            db.execute("UPDATE live_topups SET status='creation_failed' WHERE id=? AND status='creating'",(topup_id,))

    def record_topup_paid(self,topup_id,intent_id,payment_ids,amount,currency):
        from purchase_store import PurchaseError
        now=int(time.time())
        with self.transaction() as db:
            row=db.execute('SELECT * FROM live_topups WHERE id=?',(topup_id,)).fetchone()
            if not row or not payment_ids or row['intent_id']!=intent_id or row['amount']!=amount or row['currency']!=currency:
                raise PurchaseError('payment_mismatch')
            if row['status']=='creating':
                raise PurchaseError('registration_pending')
            if row['payment_id'] and row['payment_id'] not in payment_ids:
                raise PurchaseError('payment_mismatch')
            duplicate=db.execute('SELECT id FROM live_topups WHERE payment_id=? AND id<>?',(payment_ids[0],topup_id)).fetchone()
            if duplicate:
                raise PurchaseError('duplicate_payment')
            db.execute("UPDATE live_topups SET status='paid',payment_id=?,paid_at=COALESCE(paid_at,?) WHERE id=?",(payment_ids[0],now,topup_id))
            db.execute('''INSERT INTO live_lots(topup_id,account_id,credits,available,created_at)
                VALUES (?,?,?,?,?) ON CONFLICT(topup_id) DO NOTHING''',(topup_id,row['account_id'],row['credits'],row['credits'],now))

    def mark_topup_failed(self,topup_id):
        self._mark(topup_id,'failed')

    def mark_topup_expired(self,topup_id):
        self._mark(topup_id,'expired')

    def _mark(self,topup_id,status):
        with self.transaction() as db:
            db.execute("UPDATE live_topups SET status=? WHERE id=? AND status IN ('creating','pending','creation_failed')",(status,topup_id))

    def reserve_run(self,account_id,run_id,service_id,room_code,*,replace_id=None):
        from account_store import _access
        import os
        now=int(time.time())
        with self.transaction() as db:
            self._check_service(db,service_id)
            previous=db.execute('SELECT * FROM live_runs WHERE id=?',(run_id,)).fetchone()
            if previous and (previous['account_id']!=account_id or previous['room_code']!=room_code or previous['service_id']!=service_id):
                raise AccessError('This defense belongs to another room or service.')
            if previous and previous['outcome'] in {'completed','ended','abandoned','interrupted','ended_unavailable'}:
                raise AccessError('This defense has ended. Start a new run.')
            if previous and previous['status'] in {'reserved','charged'} and previous['outcome']!='opening_failed':
                return dict(previous)
            active=db.execute("SELECT id FROM live_runs WHERE account_id=? AND outcome IN ('opening','active','coaching','unavailable')",(account_id,)).fetchone()
            if active and active['id'] not in {run_id,replace_id}:
                raise AccessError('You already have an active defense. Finish or end it first.')
            if replace_id:
                old=db.execute('SELECT * FROM live_runs WHERE id=?',(replace_id,)).fetchone()
                if not old or old['account_id']!=account_id or old['room_code']!=room_code or old['service_id']!=service_id:
                    raise AccessError('The previous defense could not be replaced safely.')
            free=_access(db,account_id)['free_access']
            if not free and os.environ.get('LIVE_PAID_STARTS_ENABLED')!='1':
                raise AccessError('Paid defenses are temporarily unavailable. Voucher access remains available.')
            lots=db.execute('SELECT * FROM live_lots WHERE account_id=? AND available>0 ORDER BY created_at,topup_id',(account_id,)).fetchall()
            releasable=db.execute("SELECT COALESCE(SUM(credits),0) FROM live_allocations WHERE run_id=? AND status='reserved'",(replace_id,)).fetchone()[0] if replace_id else 0
            if not free and sum(row['available'] for row in lots)+releasable<10:
                raise AccessError('This defense needs 10 available credits or a free-access voucher.')
            # Release an old opening's reservation only after all preconditions pass.
            if replace_id:
                self._release(db,replace_id)
                db.execute("UPDATE live_runs SET outcome='ended',error_kind=NULL,updated_at=? WHERE id=? AND outcome IN ('opening','opening_failed','active','coaching','unavailable')",(now,replace_id))
                lots=db.execute('SELECT * FROM live_lots WHERE account_id=? AND available>0 ORDER BY created_at,topup_id',(account_id,)).fetchall()
            mode,cost,status=('voucher',0,'charged') if free else ('credits',10,'reserved')
            if previous:
                db.execute('DELETE FROM live_allocations WHERE run_id=?',(run_id,))
                db.execute("UPDATE live_runs SET mode=?,cost=?,status=?,outcome='opening',error_kind=NULL,updated_at=? WHERE id=?",(mode,cost,status,now,run_id))
            else:
                db.execute("INSERT INTO live_runs(id,account_id,mode,cost,status,outcome,service_id,room_code,created_at,updated_at) VALUES(?,?,?,?,?,'opening',?,?,?,?)",(run_id,account_id,mode,cost,status,service_id,room_code,now,now))
            remaining=cost
            for lot in lots:
                if not remaining:break
                take=min(remaining,lot['available'])
                db.execute('UPDATE live_lots SET available=available-? WHERE topup_id=?',(take,lot['topup_id']))
                db.execute("INSERT INTO live_allocations VALUES(?,?,?,'reserved')",(run_id,lot['topup_id'],take));remaining-=take
            return dict(db.execute('SELECT * FROM live_runs WHERE id=?',(run_id,)).fetchone())

    @staticmethod
    def _check_service(db,service_id):
        row=db.execute('SELECT status FROM live_services WHERE id=?',(service_id,)).fetchone()
        if not row or row['status']!='running':
            raise AccessError('This service no longer owns its defense runs.')

    @staticmethod
    def _check_run_service(db,run_id):
        row=db.execute('SELECT service_id FROM live_runs WHERE id=?',(run_id,)).fetchone()
        if row:LiveStore._check_service(db,row['service_id'])

    @staticmethod
    def _release(db,run_id):
        allocations=db.execute("SELECT * FROM live_allocations WHERE run_id=? AND status='reserved'",(run_id,)).fetchall()
        for item in allocations:
            db.execute('UPDATE live_lots SET available=available+? WHERE topup_id=?',(item['credits'],item['topup_id']))
        db.execute("UPDATE live_allocations SET status='released' WHERE run_id=? AND status='reserved'",(run_id,))
        db.execute("UPDATE live_runs SET status='released' WHERE id=? AND status='reserved'",(run_id,))

    def release_run(self,run_id):
        with self.transaction() as db:
            self._check_run_service(db,run_id)
            self._release(db,run_id)
            db.execute("UPDATE live_runs SET outcome='opening_failed',error_kind='question',updated_at=? WHERE id=? AND outcome='opening'",(int(time.time()),run_id))

    def charge_run(self,account_id,run_id):
        with self.transaction() as db:
            self._check_run_service(db,run_id)
            row=db.execute('SELECT * FROM live_runs WHERE id=? AND account_id=?',(run_id,account_id)).fetchone()
            if not row or row['outcome'] not in {'opening','active'} or row['status'] not in {'reserved','charged'}:
                raise AccessError('Run access has expired. Retry the opening question to reserve access again.')
            for item in db.execute("SELECT * FROM live_allocations WHERE run_id=? AND status='reserved'",(run_id,)).fetchall():
                db.execute('UPDATE live_lots SET ever_spent=ever_spent+? WHERE topup_id=?',(item['credits'],item['topup_id']))
            db.execute("UPDATE live_allocations SET status='charged' WHERE run_id=? AND status='reserved'",(run_id,))
            db.execute("UPDATE live_runs SET status='charged',outcome='active',charged_at=COALESCE(charged_at,?),updated_at=? WHERE id=?",(int(time.time()),int(time.time()),run_id))

    def finish_run(self,run_id,outcome):
        if outcome not in {'completed','ended','abandoned'}:
            raise ValueError('Invalid terminal defense outcome')
        with self.transaction() as db:
            self._check_run_service(db,run_id)
            row=db.execute('SELECT outcome FROM live_runs WHERE id=?',(run_id,)).fetchone()
            if row and row['outcome'] not in {'completed','ended','abandoned','interrupted','ended_unavailable'}:
                self._release(db,run_id)
                db.execute('UPDATE live_runs SET outcome=?,error_kind=NULL,updated_at=? WHERE id=?',(outcome,int(time.time()),run_id))

    def service_state(self,run_id,outcome,error_kind=None):
        if outcome not in {'active','coaching','unavailable'} or error_kind not in {None,'question','coaching'}:
            raise ValueError('Invalid service state')
        with self.transaction() as db:
            self._check_run_service(db,run_id)
            db.execute("UPDATE live_runs SET outcome=?,error_kind=?,updated_at=? WHERE id=? AND outcome IN ('active','coaching','unavailable')",(outcome,error_kind,int(time.time()),run_id))

    def recovery_batch(self,now):
        with self.transaction() as db:
            db.execute("UPDATE live_topups SET status='creation_failed' WHERE status='creating' AND created_at<?",(now-90,))
            rows=db.execute("SELECT * FROM live_topups WHERE intent_id IS NOT NULL AND status IN ('pending','creation_failed','failed','expired') AND recovery_after<=? ORDER BY created_at LIMIT 10",(now,)).fetchall()
            for row in rows:
                delay=min(3600,30*2**min(row['recovery_attempts'],7))
                db.execute('UPDATE live_topups SET recovery_after=?,recovery_attempts=recovery_attempts+1 WHERE id=?',(now+delay,row['id']))
            return [dict(row) for row in rows]

    @staticmethod
    def _return_run(db,row,reason):
        now=int(time.time())
        if row['status']=='charged' and row['cost']==10:
            for item in db.execute("SELECT * FROM live_allocations WHERE run_id=? AND status='charged'",(row['id'],)).fetchall():
                db.execute('UPDATE live_lots SET available=available+? WHERE topup_id=?',(item['credits'],item['topup_id']))
            db.execute("UPDATE live_allocations SET status='returned' WHERE run_id=? AND status='charged'",(row['id'],))
            db.execute('INSERT INTO live_adjustments(id,account_id,run_id,credits,reason,actor,created_at) VALUES(?,?,?,?,?,?,?) ON CONFLICT(run_id) DO NOTHING',('return_'+row['id'],row['account_id'],row['id'],10,reason,'system',now))
            db.execute("UPDATE live_runs SET status='returned' WHERE id=?",(row['id'],))
        else:
            LiveStore._release(db,row['id'])

    def end_unavailable(self,account_id,run_id):
        with self.transaction() as db:
            self._check_run_service(db,run_id)
            row=db.execute('SELECT * FROM live_runs WHERE id=? AND account_id=?',(run_id,account_id)).fetchone()
            if row and row['outcome']=='ended_unavailable':return
            if not row or row['outcome'] not in {'unavailable','opening_failed'} or row['error_kind'] not in {'question','coaching'}:
                raise AccessError('Credit recovery is available only during an unresolved service error.')
            self._return_run(db,row,'ai_unavailable')
            db.execute("UPDATE live_runs SET outcome='ended_unavailable',error_kind=NULL,updated_at=? WHERE id=?",(int(time.time()),run_id))

    def start_service(self,service_id,*,now=None):
        now=int(time.time()) if now is None else now
        with self.transaction() as db:
            alive=db.execute("SELECT id FROM live_services WHERE status='running' AND heartbeat>? AND id<>?",(now-60,service_id)).fetchone()
            if alive:
                raise AccessError('Another room service is active. Use one worker and one instance.')
            old=db.execute("SELECT r.* FROM live_runs r JOIN live_services s ON s.id=r.service_id WHERE r.service_id<>? AND r.outcome IN ('opening','opening_failed','active','coaching','unavailable') AND (s.status IN ('stopped','lost') OR s.heartbeat<=?)",(service_id,now-60)).fetchall()
            for row in old:
                self._return_run(db,row,'server_interruption')
                db.execute("UPDATE live_runs SET outcome='interrupted',error_kind=NULL,updated_at=? WHERE id=?",(now,row['id']))
            db.execute("UPDATE live_services SET status='lost' WHERE id<>? AND status='running'",(service_id,))
            db.execute("INSERT INTO live_services VALUES(?,?,'running') ON CONFLICT(id) DO UPDATE SET heartbeat=excluded.heartbeat,status='running'",(service_id,now))

    def heartbeat(self,service_id):
        with self.transaction() as db:
            row=db.execute('SELECT status FROM live_services WHERE id=?',(service_id,)).fetchone()
            if not row or row['status']!='running':
                raise AccessError('This service no longer owns its defense runs.')
            db.execute('UPDATE live_services SET heartbeat=? WHERE id=?',(int(time.time()),service_id))

    def stop_service(self,service_id):
        with self.transaction() as db:
            db.execute("UPDATE live_services SET status='stopped' WHERE id=?",(service_id,))

    def allow_ai_request(self,account_id):
        now=int(time.time())
        with self.transaction() as db:
            db.execute('DELETE FROM live_ai_requests WHERE created_at<?',(now-60,))
            count=db.execute('SELECT COUNT(*) FROM live_ai_requests WHERE account_id=?',(account_id,)).fetchone()[0]
            if count>=12:raise AccessError('Too many defense requests. Wait a minute before trying again.')
            db.execute('INSERT INTO live_ai_requests VALUES(?,?)',(account_id,now))

    def hold_refund(self,topup_id,actor,reason):
        """Review and hold a fully unused lot atomically; never request money movement."""
        with self.transaction() as db:
            receipt=db.execute('SELECT * FROM live_topups WHERE id=?',(topup_id,)).fetchone()
            lot=db.execute('SELECT * FROM live_lots WHERE topup_id=?',(topup_id,)).fetchone()
            existing=db.execute('SELECT * FROM live_refunds WHERE topup_id=?',(topup_id,)).fetchone()
            if existing:return dict(existing),False
            if not receipt or receipt['status']!='paid' or not lot:
                raise AccessError('A verified paid purchase is required for refund review.')
            if lot['ever_spent'] or lot['refunded']:
                raise AccessError('Previously used credits require separate complaint review.')
            if lot['available']!=lot['credits'] or lot['held']:
                raise AccessError('This purchase has reserved or held credits. Resolve that run first.')
            ident='refund_'+secrets.token_hex(16)
            db.execute('INSERT INTO live_refunds(id,topup_id,status,amount,reason,actor,created_at) VALUES(?,?,\'held\',?,?,?,?)',
                       (ident,topup_id,receipt['amount'],reason,actor,int(time.time())))
            db.execute('UPDATE live_lots SET held=available,available=0 WHERE topup_id=?',(topup_id,))
            return dict(db.execute('SELECT * FROM live_refunds WHERE id=?',(ident,)).fetchone()),True

    def refund(self,ident):
        with self.transaction() as db:
            row=db.execute('SELECT f.*,t.payment_id,t.currency FROM live_refunds f JOIN live_topups t ON t.id=f.topup_id WHERE f.id=?',(ident,)).fetchone()
            return dict(row) if row else None

    def reconcile_refund(self,ident,resource,actor):
        """Only independently retrieved, exactly bound full-refund evidence is accepted."""
        with self.transaction() as db:
            row=db.execute('SELECT f.*,t.payment_id,t.currency FROM live_refunds f JOIN live_topups t ON t.id=f.topup_id WHERE f.id=?',(ident,)).fetchone()
            attrs=resource.get('attributes',{})
            provider=resource.get('id')
            if (not row or resource.get('type')!='refund' or not isinstance(provider,str) or not provider.startswith('ref_')
                    or attrs.get('livemode') is not True or type(attrs.get('amount')) is not int
                    or attrs['amount']!=row['amount'] or attrs.get('currency')!=row['currency']
                    or attrs.get('payment_id')!=row['payment_id'] or (row['provider_id'] and row['provider_id']!=provider)):
                raise AccessError('Refund evidence does not match this purchase; the hold is retained.')
            if row['status'] in {'succeeded','failed'}:return dict(row)
            duplicate=db.execute('SELECT id FROM live_refunds WHERE provider_id=? AND id<>?',(provider,ident)).fetchone()
            if duplicate:raise AccessError('This refund is already associated with another review.')
            status=attrs.get('status')
            if status not in {'pending','processing','succeeded','failed'}:
                raise AccessError('Refund outcome is unverified; the hold is retained.')
            if status=='succeeded':
                db.execute('UPDATE live_lots SET refunded=refunded+held,held=0 WHERE topup_id=?',(row['topup_id'],))
            elif status=='failed':
                db.execute('UPDATE live_lots SET available=available+held,held=0 WHERE topup_id=?',(row['topup_id'],))
            db.execute('UPDATE live_refunds SET provider_id=?,status=? WHERE id=?',(provider,status,ident))
            db.execute('INSERT INTO live_adjustments(id,account_id,topup_id,credits,reason,actor,created_at) SELECT ?,account_id,?,0,?,?,? FROM live_topups WHERE id=? ON CONFLICT(id) DO NOTHING',
                       ('audit_'+ident+'_'+status,row['topup_id'],'refund_'+status,actor,int(time.time()),row['topup_id']))
            return dict(db.execute('SELECT * FROM live_refunds WHERE id=?',(ident,)).fetchone())

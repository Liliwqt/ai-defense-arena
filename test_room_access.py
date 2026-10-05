"""Offline room-account/voucher/credit tests; Google, payment and AI calls mocked."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
import account_store as store
import accounts
import game_server as server
from question_generator import GroundedQuestion, QuestionGenerationError


class RoomAccessTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory(); self.addCleanup(folder.cleanup)
        self.db = Path(folder.name) / 'accounts.sqlite3'
        self.origin = 'http://127.0.0.1:8000'
        self.env = patch.dict(os.environ, {
            'GOOGLE_CLIENT_ID':'offline-client', 'GOOGLE_CLIENT_SECRET':'offline-secret',
            'AUTH_SESSION_SECRET':'offline-cookie-secret-longer-than-32-characters',
            'AUTH_PUBLIC_BASE_URL':self.origin, 'PAYMONGO_TEST_DB_PATH':str(self.db),
            'FREE_ACCESS_VOUCHER':'offline-shareable-high-entropy-voucher',
        }); self.env.start(); self.addCleanup(self.env.stop)
        server.rooms.clear()
        self.client = TestClient(server.app, base_url=self.origin).__enter__()
        self.addCleanup(lambda:self.client.__exit__(None,None,None))
        self.token, self.csrf = self.signin('owner')
        self.account = store.session_account(self.token)
        self.socket = SimpleNamespace(cookies={accounts.ACCOUNT_COOKIE:self.token}, headers={'origin':self.origin}, send_json=self.capture)
        self.events = []
        self.files = [('files', ('queue.py', b'    queue = []\n', 'text/x-python'))]
        self.question = GroundedQuestion('How is the queue stored?', 'queue.py', 1, '    queue = []')
        self.schedule = patch.object(server, '_schedule_generation'); self.schedule.start(); self.addCleanup(self.schedule.stop)
        clock = patch.object(server, '_schedule_clock'); clock.start(); self.addCleanup(clock.stop)

    async def capture(self, event): self.events.append(event)

    def signin(self, sub, client=None):
        client = client or self.client
        token, csrf = store.create_google_session(sub,sub+'@example.test',sub)
        client.cookies.set(accounts.ACCOUNT_COOKIE,token)
        client.headers.update({'Origin':self.origin,'X-CSRF-Token':csrf})
        return token,csrf

    def seed(self, amount=100, account_id=None):
        account_id = account_id or self.account['id']
        oid = 'offline-order-'+os.urandom(4).hex()
        with store.connect_store(self.db) as db:
            db.execute("INSERT INTO test_orders (id,token_hash,amount,currency,status,created_at,account_id,credits) VALUES (?,? ,10000,'PHP','paid',1,?,?)", (oid,'hash',account_id,amount))
            db.execute('INSERT INTO test_credit_ledger VALUES (?,?,?,1)', (oid,account_id,amount))

    def create(self):
        response=self.client.post('/api/rooms',data={'host_name':'Display name'},files=self.files)
        self.assertEqual(response.status_code,201,response.text)
        credentials=response.json();room=server.rooms[credentials['room_code']]
        return room,room.players[credentials['player_token']],credentials

    def act(self, room, host, action, **extra):
        self.client.portal.call(server._handle_action,room,host,self.socket,{'type':action,**extra})

    def generate(self, room, question=None, error=None):
        with patch.object(server,'generate_first_question',side_effect=error,return_value=question or self.question):
            self.client.portal.call(server._generate_question,room,room.generation_id,True)

    def test_upload_is_free_but_owner_and_csrf_are_required(self):
        room,host,credentials=self.create()
        self.assertEqual(room.owner_account_id,self.account['id'])
        self.assertIsNone(room.run_id)
        self.act(room,host,'start',confirm_cost=True)
        self.assertEqual(room.phase,'lobby')
        self.assertIn('10',self.events[-1]['message'])
        self.assertEqual(self.client.post('/api/rooms',data={'host_name':'X'},files=self.files,headers={'X-CSRF-Token':'bad'}).status_code,403)
        self.client.cookies.clear()
        self.assertEqual(self.client.post('/api/rooms',data={'host_name':'X'},files=self.files).status_code,401)
        self.assertEqual(self.client.post(f"/api/rooms/{room.code}/join",json={'name':'Guest'}).status_code,200)

    def test_unconfigured_google_cannot_create_room(self):
        with patch.dict(os.environ,{'GOOGLE_CLIENT_ID':''}):
            self.assertEqual(self.client.post('/api/rooms',data={'host_name':'X'},files=self.files).status_code,503)

    def test_voucher_is_shareable_idempotent_private_and_revocable(self):
        code=os.environ['FREE_ACCESS_VOUCHER']
        for sub in ['owner','other']:
            token,csrf=self.signin(sub)
            for _ in range(2):self.assertEqual(self.client.post('/api/auth/voucher',json={'voucher':code}).status_code,200)
            self.assertTrue(self.client.get('/api/auth/me').json()['free_access'])
        with store.connect_store(self.db) as db:
            records=json.dumps([dict(row) for row in db.execute('SELECT * FROM voucher_grants')]);self.assertNotIn(code,records)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM voucher_grants').fetchone()[0],2)
        with patch.dict(os.environ,{'FREE_ACCESS_VOUCHER':'rotated-voucher'}):self.assertFalse(self.client.get('/api/auth/me').json()['free_access'])
        with patch.dict(os.environ,{'FREE_ACCESS_VOUCHER':''}):self.assertFalse(self.client.get('/api/auth/me').json()['free_access'])

    def test_failed_voucher_attempts_are_throttled_and_csrf_protected(self):
        self.assertEqual(self.client.post('/api/auth/voucher',json={'voucher':'bad'},headers={'Origin':'https://attacker.test'}).status_code,403)
        for _ in range(5):self.assertEqual(self.client.post('/api/auth/voucher',json={'voucher':'bad'}).status_code,403)
        self.assertEqual(self.client.post('/api/auth/voucher',json={'voucher':os.environ['FREE_ACCESS_VOUCHER']}).status_code,429)
        with store.connect_store(self.db) as db:db.execute('UPDATE voucher_attempts SET window_start=0')
        self.assertEqual(self.client.post('/api/auth/voucher',json={'voucher':os.environ['FREE_ACCESS_VOUCHER']}).status_code,200)

    def test_host_token_alone_does_not_reconnect_or_control(self):
        room,host,credentials=self.create()
        self.client.cookies.clear()
        with self.client.websocket_connect(f'/ws/{room.code}') as ws:
            ws.send_json({'type':'hello','token':credentials['player_token']})
            self.assertIn('Sign in',ws.receive_json()['message'])
        store.remove_session(self.token)
        self.act(room,host,'restart',confirm_cost=True)
        self.assertEqual(room.phase,'lobby');self.assertIsNone(room.run_id)
        self.assertIn('Sign in',self.events[-1]['message'])

    def test_different_account_and_wrong_origin_cannot_use_owner_token(self):
        room,host,credentials=self.create()
        other,_=self.signin('other')
        self.socket.cookies[accounts.ACCOUNT_COOKIE]=other
        self.act(room,host,'restart',confirm_cost=True)
        self.assertIn('created',self.events[-1]['message'])
        self.socket.cookies[accounts.ACCOUNT_COOKIE]=self.token;self.socket.headers['origin']='https://attacker.test'
        self.act(room,host,'start',confirm_cost=True)
        self.assertIsNone(room.run_id)

    def test_paid_start_reserves_then_charges_once_at_first_question(self):
        self.seed();room,host,_=self.create()
        self.act(room,host,'start')
        self.assertEqual(room.phase,'lobby');self.assertIn('Confirm',self.events[-1]['message'])
        self.act(room,host,'start',confirm_cost=True);rid=room.run_id
        access=store.account_access(self.account['id']);self.assertEqual((access['test_credits'],access['reserved_credits'],access['spent_credits']),(90,10,0))
        self.act(room,host,'start',confirm_cost=True);self.assertEqual(room.run_id,rid)
        self.generate(room);store.charge_run(self.account['id'],rid)
        access=store.account_access(self.account['id']);self.assertEqual((access['test_credits'],access['reserved_credits'],access['spent_credits']),(90,0,10))
        self.assertEqual(room.phase,'voting');self.assertEqual(len(room.defense.turns),1)
        snapshot=json.dumps(room.snapshot(host));self.assertNotIn(self.account['id'],snapshot);self.assertNotIn('test_credits',snapshot);self.assertNotIn('example.test',snapshot)

    def test_opening_failure_releases_retry_reserves_same_run(self):
        self.seed(10);room,host,_=self.create();self.act(room,host,'start',confirm_cost=True);rid=room.run_id
        self.generate(room,error=QuestionGenerationError('offline failure'))
        self.assertEqual(room.phase,'retry');self.assertIsNone(room.defense)
        self.assertEqual(store.account_access(self.account['id'])['test_credits'],10)
        self.act(room,host,'retry');self.assertEqual(room.run_id,rid)
        self.generate(room);self.assertEqual(store.account_access(self.account['id'])['spent_credits'],10)

    def test_concurrent_reservations_cannot_overspend(self):
        self.seed(10)
        def reserve(i):
            try:store.reserve_run(self.account['id'],str(i));return True
            except store.AccessError:return False
        with ThreadPoolExecutor(max_workers=8) as pool:self.assertEqual(sum(pool.map(reserve,range(8))),1)
        self.assertEqual(store.account_access(self.account['id'])['test_credits'],0)

    def test_voucher_run_survives_rotation_but_next_run_requires_credits(self):
        store.redeem_voucher(self.account['id'],os.environ['FREE_ACCESS_VOUCHER'])
        room,host,_=self.create();self.act(room,host,'start');rid=room.run_id
        with patch.dict(os.environ,{'FREE_ACCESS_VOUCHER':'rotated'}):
            self.generate(room);self.assertEqual(room.phase,'voting')
            self.act(room,host,'restart',confirm_cost=True)
            self.assertEqual(room.run_id,rid);self.assertEqual(room.phase,'voting')
        self.assertEqual(store.account_access(self.account['id'])['spent_credits'],0)

    def test_restart_requires_confirmation_and_new_run_charge(self):
        self.seed(20);room,host,_=self.create();self.act(room,host,'start',confirm_cost=True);self.generate(room);rid=room.run_id
        self.act(room,host,'restart');self.assertEqual(room.run_id,rid);self.assertEqual(room.phase,'voting')
        self.act(room,host,'restart',confirm_cost=True);self.assertNotEqual(room.run_id,rid);self.generate(room)
        self.assertEqual(store.account_access(self.account['id'])['spent_credits'],20)

    def test_stale_opening_result_cannot_publish_or_charge(self):
        self.seed(20);room,host,_=self.create();self.act(room,host,'start',confirm_cost=True)
        generation=room.generation_id;rid=room.run_id
        self.act(room,host,'restart',confirm_cost=True)
        with patch.object(server,'generate_first_question',return_value=self.question):self.client.portal.call(server._generate_question,room,generation,True)
        self.assertIsNone(room.defense);self.assertEqual(store.account_access(self.account['id'])['spent_credits'],0)
        with store.connect_store(self.db) as db:self.assertEqual(db.execute('SELECT status FROM defense_runs WHERE id=?',(rid,)).fetchone()[0],'released')

    def test_startup_releases_only_orphaned_reservations(self):
        self.seed(30);store.reserve_run(self.account['id'],'pending');store.reserve_run(self.account['id'],'charged');store.charge_run(self.account['id'],'charged')
        self.client.portal.call(server.app.router.lifespan_context(server.app).__aenter__)
        access=store.account_access(self.account['id']);self.assertEqual((access['test_credits'],access['reserved_credits'],access['spent_credits']),(20,0,10))

    def test_run_id_cannot_be_reused_by_another_account(self):
        self.seed(10);store.reserve_run(self.account['id'],'unique')
        token,_=self.signin('other')
        with self.assertRaises(store.AccessError):store.reserve_run(store.session_account(token)['id'],'unique')

    def test_room_preparation_requires_access_without_deduction(self):
        room,host,_=self.create();room.defense_type='research'
        self.act(room,host,'prepare_research_plan');self.assertEqual(room.research_planning_status,'none')
        self.seed(10)
        with patch.object(server,'_schedule_research_plan') as scheduled:self.act(room,host,'prepare_research_plan');scheduled.assert_called_once()
        self.assertEqual(store.account_access(self.account['id'])['test_credits'],10)

    def test_failed_charge_does_not_publish_opening_question(self):
        self.seed(10);room,host,_=self.create();self.act(room,host,'start',confirm_cost=True)
        with patch.object(server,'charge_run',side_effect=store.AccessError('offline storage failure')):self.generate(room)
        self.assertEqual(room.phase,'retry');self.assertIsNone(room.defense)
        self.assertEqual(store.account_access(self.account['id'])['test_credits'],10)

    def test_early_ending_releases_only_unpublished_opening_reservation(self):
        from test_research_plan import PAPER, fixture_plan
        from defense_session import ResearchDefenseSession
        from question_generator import ResearchMove
        from project_files import ProjectFile
        for publish in (False, True):
            with self.subTest(published=publish):
                self.seed(10)
                room,host,_=self.create()
                room.defense_type='research';room.files=[ProjectFile('study.md',PAPER,'research_text')]
                room.research_plan=fixture_plan();room.research_plan_approved=True;room.research_budget_preview=4
                self.act(room,host,'start',confirm_cost=True,plan_id=room.research_plan.id,question_budget=4)
                before=store.account_access(self.account['id'])['spent_credits']
                if publish:
                    q=GroundedQuestion('How will the pilot work?','study.md',4,PAPER.splitlines()[3],evidence_kind='research_text')
                    with patch.object(server,'generate_research_move',return_value=ResearchMove('Methodology Reviewer',q,'topic-1',False,None)):
                        self.client.portal.call(server._generate_question,room,room.generation_id,True)
                with patch.object(server,'_schedule_coaching'):self.act(room,host,'end_defense')
                access=store.account_access(self.account['id'])
                self.assertEqual(access['reserved_credits'],0)
                self.assertEqual(access['spent_credits'],before+(10 if publish else 0))
                self.assertEqual(room.phase,'complete')



if __name__=='__main__':unittest.main()

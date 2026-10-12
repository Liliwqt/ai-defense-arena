"""Original PDF access through authenticated room HTTP/WebSocket boundaries."""

import os
from pathlib import Path
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from threading import Event
from unittest.mock import patch

from tests import test_room_access as fixture
from tests.test_research_defense import pdf_bytes
from backend import game_server as server
from backend.room_documents import DocumentStore
from backend import account_store
from backend.defense_session import ResearchDefenseSession
from backend.question_generator import GroundedCitation, RESEARCH_PANELISTS
from backend.research_plan import ResearchPlan, ResearchTopic
from backend.rooms.commands import RestartDefense, VerifiedActor


class RoomDocumentTests(unittest.TestCase):
    signin = fixture.RoomAccessTests.signin
    capture = fixture.RoomAccessTests.capture

    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.documents_path = Path(folder.name)
        settings = {'ROOM_DOCUMENT_DIR': str(self.documents_path), 'ROOM_CREATE_PER_MINUTE': '1000'}
        if self._testMethodName.startswith('test_quota'):
            settings['ROOM_DOCUMENT_TOTAL_BYTES'] = str(len(pdf_bytes('Planned interviews', 'Consent and anonymity')))
        env = patch.dict(os.environ, settings)
        env.start()
        self.addCleanup(env.stop)
        fixture.RoomAccessTests.setUp(self)

    def paper_room(self, data=None):
        self.paper = data or pdf_bytes('Planned interviews', 'Consent and anonymity')
        response = self.client.post('/api/rooms', data={'host_name': 'Alex', 'defense_type': 'research'},
            files=[('research_files', ('paper.pdf', self.paper, 'application/pdf'))])
        self.assertEqual(response.status_code, 201, response.text)
        credentials = response.json()
        with self.client.websocket_connect('/ws/' + credentials['room_code']) as socket:
            socket.send_json({'type': 'hello', 'token': credentials['player_token']})
            state = socket.receive_json()['state']
        return credentials, state

    def test_original_is_private_and_reconnect_metadata_is_safe(self):
        host, state = self.paper_room()
        self.assertEqual(len(state['documents']), 1)
        document = state['documents'][0]
        self.assertEqual(document['filename'], 'paper.pdf')
        self.assertEqual(document['page_count'], 2)
        self.assertEqual(set(document), {'id', 'filename', 'page_count'})
        url = f"/api/rooms/{host['room_code']}/documents/{document['id']}"
        response = self.client.get(url, headers={'X-Player-Token': host['player_token']})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, self.paper)
        self.assertEqual(response.headers['content-type'], 'application/pdf')
        self.assertEqual(response.headers['cache-control'], 'no-store')
        self.assertEqual(self.client.get(url).status_code, 403)
        guest = self.client.post('/api/rooms/' + host['room_code'] + '/join', json={'name': 'Sam'}).json()
        self.client.cookies.clear()
        self.assertEqual(self.client.get(url, headers={'X-Player-Token': host['player_token']}).status_code, 401)
        self.assertEqual(self.client.get(url, headers={'X-Player-Token': guest['player_token']}).content, self.paper)
        with self.client.websocket_connect('/ws/' + host['room_code']) as socket:
            socket.send_json({'type': 'hello', 'token': guest['player_token']})
            reconnected = socket.receive_json()['state']
        self.assertEqual(reconnected['documents'], state['documents'])

    def test_quota_close_releases_bytes_and_wrong_room_access_is_rejected(self):
        host, state = self.paper_room()
        document = state['documents'][0]
        response = self.client.post('/api/rooms', data={'host_name': 'Alex', 'defense_type': 'research'},
            files=[('research_files', ('paper.pdf', self.paper, 'application/pdf'))])
        self.assertEqual(response.status_code, 503)
        self.assertIn('storage is full', response.json()['detail'])
        self.assertEqual(self.client.delete('/api/rooms/' + host['room_code']).status_code, 200)
        second, _ = self.paper_room()
        url = f"/api/rooms/{second['room_code']}/documents/{document['id']}"
        self.assertEqual(self.client.get(url, headers={'X-Player-Token': second['player_token']}).status_code, 404)

    def test_quota_invalid_pdf_releases_reservations(self):
        response = self.client.post('/api/rooms', data={'host_name': 'Alex', 'defense_type': 'research'},
            files=[('research_files', ('invalid.pdf', b'invalid', 'application/pdf'))])
        self.assertEqual(response.status_code, 422)
        self.paper_room()

    def test_owner_account_expiry_and_shutdown_reject_access_and_remove_files(self):
        host, state = self.paper_room()
        url = f"/api/rooms/{host['room_code']}/documents/{state['documents'][0]['id']}"
        self.signin('other')
        self.assertEqual(self.client.get(url, headers={'X-Player-Token':host['player_token']}).status_code, 403)
        self.signin('owner')
        room = server.rooms[host['room_code']]
        room.phase = 'complete'; room.terminal_ms = 1000
        with patch.object(server, '_now_ms', return_value=1_801_000):
            self.assertEqual(self.client.get(url, headers={'X-Player-Token':host['player_token']}).status_code, 404)
            self.assertEqual(self.client.get('/api/rooms').json()['rooms'], [])
        self.assertFalse(any(path.is_dir() for path in self.documents_path.iterdir()))

    def test_quota_concurrent_creation_cannot_overbook_and_timeout_cannot_recreate_files(self):
        data = pdf_bytes('Planned interviews', 'Consent and anonymity')
        entered, release = Event(), Event()
        original = server.read_research_files
        def blocked(*args, **kwargs):
            entered.set(); release.wait(4)
            # Intentionally ignore cancellation: exercise late ownership fencing.
            kwargs.pop('cancel', None)
            return original(*args, **kwargs)
        with patch.dict(os.environ, {'ROOM_PROCESS_SECONDS':'1'}), patch.object(server, 'read_research_files', side_effect=blocked), ThreadPoolExecutor(max_workers=1) as pool:
            first = pool.submit(self.client.post, '/api/rooms', data={'host_name':'Alex','defense_type':'research'}, files=[('research_files',('paper.pdf',data,'application/pdf'))])
            try:
                self.assertTrue(entered.wait(2))
                second = self.client.post('/api/rooms', data={'host_name':'Alex','defense_type':'research'}, files=[('research_files',('paper.pdf',data,'application/pdf'))])
                self.assertEqual(second.status_code, 503)
                self.assertEqual(first.result(timeout=2).status_code, 408)
            finally:
                release.set()
        self.paper_room()
        self.assertEqual(len(self.client.get('/api/rooms').json()['rooms']), 1)
        self.assertEqual(len([path for path in self.documents_path.iterdir() if path.is_dir()]), 1)

    def test_per_room_limit_and_publication_failure_release_capacity(self):
        data = pdf_bytes('Planned interviews', 'Consent and anonymity')
        store = server.app.state.documents
        store.per_room = len(data) - 1
        response = self.client.post('/api/rooms', data={'host_name':'Alex','defense_type':'research'}, files=[('research_files',('paper.pdf',data,'application/pdf'))])
        self.assertEqual(response.status_code, 413)
        store.per_room = 110_000_000
        with patch.object(server, '_room_code', side_effect=RuntimeError('synthetic publication failure')):
            with self.assertRaises(RuntimeError):
                self.paper_room(data)
        self.assertEqual(store.used, 0)
        self.assertFalse(any(path.is_dir() for path in self.documents_path.iterdir()))
        self.paper_room(data)

    def test_storage_startup_cannot_purge_a_live_owner_and_cleans_orphans(self):
        self.paper_room()
        replacement = DocumentStore()
        with self.assertRaisesRegex(RuntimeError, 'Another service'):
            replacement.start()
        self.assertTrue(any(path.is_dir() for path in self.documents_path.iterdir()))
        server.app.state.documents.close()
        orphan = self.documents_path / ('a' * 48)
        orphan.mkdir(); (orphan / 'private').write_bytes(b'synthetic orphan')
        replacement.start()
        self.addCleanup(replacement.close)
        self.assertFalse(orphan.exists())

    def test_same_room_defense_restart_retains_originals_but_changes_reading_turn_identity(self):
        host, state = self.paper_room()
        room = server.rooms[host['room_code']]
        account_store.redeem_voucher(self.account['id'], os.environ['FREE_ACCESS_VOUCHER'])
        reference = GroundedCitation('paper.pdf',1,'Planned interviews','Page 1 · extracted line 1','research_pdf')
        plan = ResearchPlan(tuple(ResearchTopic(f'topic-{i}', 'Pilot method', 'Discuss the method.', role, (reference,)) for i,role in enumerate(RESEARCH_PANELISTS)))
        room.research_plan = plan; room.research_plan_approved = True; room.research_budget_preview = 8
        room.defense = ResearchDefenseSession.create(plan,8,'research','proposal'); room.phase = 'complete'
        old_view = room.defense_view_id
        result = self.client.portal.call(server._coordinator(room).execute, RestartDefense(True), VerifiedActor(host['player_token'],self.account['id']))
        self.assertTrue(result.accepted)
        self.assertNotEqual(room.defense_view_id, old_view)
        self.assertEqual(room.documents.snapshot(), state['documents'])
        url = f"/api/rooms/{host['room_code']}/documents/{state['documents'][0]['id']}"
        self.assertEqual(self.client.get(url,headers={'X-Player-Token':host['player_token']}).content,self.paper)

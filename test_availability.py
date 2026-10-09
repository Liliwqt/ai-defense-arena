"""Bounded hostile inputs through real admission; providers stay offline."""
import asyncio
from contextlib import ExitStack
from io import BytesIO
import json
import os
import unittest
from unittest.mock import patch
from zipfile import ZIP_DEFLATED, ZipFile

from fastapi.testclient import TestClient

import game_server as server
import research_files
from offline_accounts import authenticate
from test_research_defense import docx_bytes, upload


class AvailabilityTests(unittest.TestCase):
    def setUp(self):
        isolated = patch.dict(os.environ, {'DATABASE_URL': '', 'PAYMENTS_MODE': 'test'})
        isolated.start()
        self.addCleanup(isolated.stop)
        authenticate(self)
        server.rooms.clear()
        self.client = TestClient(server.app).__enter__()
        self.addCleanup(lambda: self.client.__exit__(None, None, None))
        authenticate(self, self.client)

    def room(self):
        response = self.client.post('/api/rooms', data={'host_name': 'Host'},
                                    files=[('files', ('main.py', b'queue = []'))])
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()['room_code']

    def test_unknown_room_rejects_oversized_json_before_endpoint(self):
        with patch.object(server, '_player_name') as endpoint:
            response = self.client.post('/api/rooms/UNKNOWN/join',
                                        json={'name': 'Guest', 'extra': 'x' * 5000})
        self.assertEqual(response.status_code, 413)
        endpoint.assert_not_called()

    def test_guest_token_has_bounded_connections(self):
        code = self.room()
        token = self.client.post(f'/api/rooms/{code}/join', json={'name': 'Guest'}).json()['player_token']
        with ExitStack() as stack:
            for _ in range(2):
                socket = stack.enter_context(self.client.websocket_connect('/ws/' + code))
                socket.send_json({'type': 'hello', 'token': token})
                self.assertEqual(socket.receive_json()['type'], 'snapshot')
            revision = server.rooms[code].revision
            extra = stack.enter_context(self.client.websocket_connect('/ws/' + code))
            extra.send_json({'type': 'hello', 'token': token})
            event = extra.receive_json()
            self.assertEqual(event['type'], 'error')
            self.assertIn('connection', event['message'].lower())
            self.assertEqual(len(server.rooms[code].players[token].sockets), 2)
            self.assertEqual(server.rooms[code].revision, revision)


    def test_guest_message_budget_survives_reconnect_and_binary_cleanup(self):
        from resource_limits import socket_message_rate
        code = self.room()
        token = self.client.post(f'/api/rooms/{code}/join', json={'name': 'Guest'}).json()['player_token']
        with self.client.websocket_connect('/ws/' + code) as socket:
            socket.send_json({'type': 'hello', 'token': token})
            socket.receive_json()
            for _ in range(10):
                socket.send_json({'type': 'unknown'})
                self.assertEqual(socket.receive_json()['type'], 'error')
            socket.send_json({'type': 'unknown'})
            self.assertEqual(socket.receive_json()['reason'], 'socket_admission')
        with self.client.websocket_connect('/ws/' + code) as socket:
            socket.send_json({'type': 'hello', 'token': token})
            socket.receive_json()
            socket.send_json({'type': 'send_chat', 'text': 'bypass attempt'})
            self.assertEqual(socket.receive_json()['reason'], 'socket_admission')
        self.assertFalse(server.rooms[code].chat)
        socket_message_rate.__init__()
        with self.client.websocket_connect('/ws/' + code) as socket:
            socket.send_json({'type': 'hello', 'token': token})
            socket.receive_json()
            socket.send_bytes(b'invalid')
            with self.assertRaises(server.WebSocketDisconnect):
                socket.receive_json()
        self.assertFalse(server.rooms[code].players[token].sockets)

    def test_utf8_name_and_two_tabs_keep_seat_online_until_last_disconnect(self):
        code = self.room()
        name = '友' * 24
        joined = self.client.post(f'/api/rooms/{code.lower()}/join', json={'name': name})
        self.assertEqual(joined.status_code, 200, joined.text)
        token = joined.json()['player_token']
        with self.client.websocket_connect('/ws/' + code) as first:
            first.send_json({'type': 'hello', 'token': token})
            first.receive_json()
            with self.client.websocket_connect('/ws/' + code) as second:
                second.send_json({'type': 'hello', 'token': token})
                second.receive_json()
            # Consume connect then disconnect broadcasts; the remaining tab is online.
            while True:
                snapshot = first.receive_json()
                if len(server.rooms[code].players[token].sockets) == 1:
                    self.assertTrue(next(p for p in snapshot['state']['players'] if p['name'] == name)['online'])
                    break
        self.assertFalse(server.rooms[code].players[token].sockets)


class DocumentExpansionTests(unittest.TestCase):
    def test_oversized_related_part_is_rejected_before_document_load(self):
        # Small harmless fixture models expansion with a lowered member limit.
        buffer = BytesIO()
        with ZipFile(BytesIO(docx_bytes())) as original, ZipFile(buffer, 'w', ZIP_DEFLATED) as out:
            for item in original.infolist():
                data = original.read(item)
                if item.filename == 'word/_rels/document.xml.rels':
                    data = data.replace(b'</Relationships>', b'<Relationship Id="extra" Type="http://example.test/attachment" Target="media/large.bin"/></Relationships>')
                if item.filename == '[Content_Types].xml':
                    data = data.replace(b'</Types>', b'<Default Extension="bin" ContentType="application/octet-stream"/></Types>')
                out.writestr(item.filename, data)
            out.writestr('word/media/large.bin', b'x' * 500_000)
        with patch.object(research_files, 'MAX_DOCX_MEMBER_BYTES', 400_000, create=True), patch.object(research_files, 'Document', wraps=research_files.Document) as parser:
            with self.assertRaisesRegex(research_files.ProjectInputError, 'expanded'):
                research_files._docx_in_process('study.docx', buffer.getvalue())
        parser.assert_not_called()

class TransportBoundaryTests(unittest.IsolatedAsyncioTestCase):
    async def test_selected_uvicorn_backend_bounds_completed_message_queue(self):
        from pathlib import Path
        from uvicorn import Config
        from uvicorn.server import ServerState
        from uvicorn.protocols.websockets.websockets_impl import WebSocketProtocol
        root = Path(__file__).resolve().parent
        for filename in ('render.yaml', 'run_local.sh'):
            command = (root / filename).read_text()
            self.assertIn('--ws websockets --ws-max-size 20000 --ws-max-queue 4', command)
        config = Config(server.app, ws='websockets', ws_max_size=20000, ws_max_queue=4)
        protocol = WebSocketProtocol(config, ServerState(), {})
        self.assertIs(config.ws_protocol_class, WebSocketProtocol)
        self.assertEqual(protocol.max_size, 20000)
        read_fifth = asyncio.Event()
        count = 0
        async def read_message():
            nonlocal count
            count += 1
            if count == 5:
                read_fifth.set()
            return 'ordinary small message'
        with patch.object(protocol, 'read_message', side_effect=read_message):
            task = asyncio.create_task(protocol.transfer_data())
            try:
                await asyncio.wait_for(read_fifth.wait(), 1)
                self.assertEqual(len(protocol.messages), 4)
                self.assertFalse(task.done())
            finally:
                task.cancel()
                await asyncio.gather(task, return_exceptions=True)

    async def test_chunked_join_counts_actual_bytes_with_false_or_absent_length(self):
        from resource_limits import JoinAdmissionMiddleware, join_capacity, join_rate
        for headers in ([], [(b'content-length', b'1')]):
            join_capacity.__init__()
            join_rate.__init__()
            reached = []
            sent = []
            chunks = iter([{'type': 'http.request', 'body': b'x' * 3000, 'more_body': True},
                           {'type': 'http.request', 'body': b'y' * 2000, 'more_body': False}])
            async def receive():
                return next(chunks)
            async def send(message):
                sent.append(message)
            async def downstream(*args):
                reached.append(True)
            scope = {'type': 'http', 'method': 'POST', 'path': '/api/rooms/MISSING/join',
                     'headers': headers, 'client': ('192.0.2.10', 10)}
            await JoinAdmissionMiddleware(downstream)(scope, receive, send)
            self.assertFalse(reached)
            self.assertEqual(sent[0]['status'], 413)
            self.assertEqual(join_capacity.total, 0)

    async def test_join_disconnected_body_releases_capacity(self):
        from resource_limits import JoinAdmissionMiddleware, join_capacity, join_rate
        join_capacity.__init__()
        join_rate.__init__()
        async def receive():
            return {'type': 'http.disconnect'}
        async def unused(*args):
            self.fail('Disconnected request reached downstream')
        await JoinAdmissionMiddleware(unused)(
            {'type': 'http', 'method': 'POST', 'path': '/api/rooms/ANY/join',
             'headers': [], 'client': ('192.0.2.10', 10)}, receive, unused)
        self.assertEqual(join_capacity.total, 0)

    async def test_slow_recipient_does_not_block_healthy_peer(self):
        class Socket:
            def __init__(self, slow=False):
                self.slow = slow
                self.messages = []
                self.closed = False
            async def send_json(self, message):
                if self.slow:
                    await asyncio.Event().wait()
                self.messages.append(message)
            async def close(self, **kwargs):
                self.closed = True
        slow, fast = Socket(True), Socket()
        a = server.Player('a', 'Alex', 0, False, {slow})
        b = server.Player('b', 'Sam', 1, False, {fast})
        room = server.Room('BOUNDED', [], {'a': a, 'b': b})
        await asyncio.wait_for(server.publish(room), 2)
        self.assertTrue(slow.closed)
        self.assertFalse(a.sockets)
        self.assertEqual(len(fast.messages), 1)
        self.assertTrue(b.sockets)
        await server.publish(room)
        self.assertFalse(fast.messages[-1]['state']['players'][0]['online'])

    async def test_pending_hello_uses_and_releases_global_capacity(self):
        from resource_limits import socket_capacity, socket_connect_rate
        socket_capacity.__init__()
        socket_connect_rate.__init__()
        class Socket:
            headers = {}
            client = type('Peer', (), {'host': '192.0.2.1'})()
            async def accept(self):
                pass
            async def receive_text(self):
                raise server.WebSocketDisconnect()
        room = server.Room('HELLO', [], {})
        server.rooms['HELLO'] = room
        try:
            await server.room_socket(Socket(), 'HELLO')
            self.assertEqual(socket_capacity.total, 0)
            self.assertEqual(socket_capacity.networks, {})
        finally:
            server.rooms.pop('HELLO', None)

    async def test_room_removal_clears_data_despite_slow_error_and_close(self):
        class SlowSocket:
            async def send_json(self, payload):
                await asyncio.Event().wait()
            async def close(self, **kwargs):
                await asyncio.Event().wait()
        socket = SlowSocket()
        player = server.Player('remove', 'Alex', 0, False, {socket})
        room = server.Room('REMOVE', [], {'remove': player})
        server.rooms[room.code] = room
        self.assertTrue(await asyncio.wait_for(server._remove_room(room), 3))
        self.assertNotIn(room.code, server.rooms)
        self.assertFalse(room.players)
        self.assertFalse(room.chat)

    async def test_unauthenticated_socket_capacity_is_reserved_before_hello(self):
        from resource_limits import socket_capacity, socket_connect_rate
        socket_capacity.__init__()
        socket_connect_rate.__init__()
        waiting = asyncio.Event()
        class Socket:
            headers = {}
            client = type('Peer', (), {'host': '192.0.2.2'})()
            closed = False
            async def accept(self):
                pass
            async def receive_text(self):
                waiting.set()
                await asyncio.Event().wait()
            async def close(self, **kwargs):
                self.closed = True
        room = server.Room('PENDING', [], {})
        server.rooms['PENDING'] = room
        socket_capacity.acquire('192.0.2.2', 256, 32)
        # Model already-reserved clients without opening dozens of transports.
        for _ in range(30):
            socket_capacity.acquire('192.0.2.2', 256, 32)
        task = asyncio.create_task(server.room_socket(Socket(), 'PENDING'))
        try:
            await asyncio.wait_for(waiting.wait(), 1)
            self.assertEqual(socket_capacity.total, 32)
            extra = Socket()
            await server.room_socket(extra, 'PENDING')
            self.assertTrue(extra.closed)
            self.assertEqual(socket_capacity.total, 32)
        finally:
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
            self.assertEqual(socket_capacity.total, 31)
            socket_capacity.__init__()
            server.rooms.pop('PENDING', None)


class ParserLifecycleTests(unittest.TestCase):
    def test_public_docx_path_rejects_expansion_and_recovers_for_normal_upload(self):
        buffer = BytesIO()
        with ZipFile(buffer, 'w', ZIP_DEFLATED) as archive:
            archive.writestr('oversized.bin', b'x' * 8_000_001)
        files, errors = research_files.read_research_files([upload('attack.docx', buffer.getvalue())])
        self.assertFalse(files)
        self.assertIn('expanded', errors[0])
        files, errors = research_files.read_research_files([upload('valid.docx', docx_bytes())])
        self.assertFalse(errors)
        self.assertTrue(files[0].locations)

    def test_duplicate_members_and_entry_count_rejected(self):
        import warnings
        for many in (False, True):
            buffer = BytesIO()
            with warnings.catch_warnings():
                warnings.simplefilter('ignore')
                with ZipFile(buffer, 'w') as archive:
                    for i in range(513 if many else 2):
                        archive.writestr(str(i) if many else 'same', b'x')
            with self.assertRaises(research_files.ProjectInputError):
                research_files._validate_docx_package('attack.docx', buffer.getvalue())

    def test_worker_has_real_memory_ceiling(self):
        import subprocess
        import sys
        result = subprocess.run(
            [sys.executable, '-c',
             'from document_parser_worker import set_limits; set_limits(); '
             '\ntry: bytearray(256 * 1024 * 1024)\nexcept MemoryError: print("bounded")'],
            capture_output=True, timeout=5, env={'LANG': 'C.UTF-8'})
        self.assertEqual(result.returncode, 0, result.stderr.decode())
        self.assertEqual(result.stdout.strip(), b'bounded')

    def test_timeout_and_cancellation_kill_and_reap_worker_without_credentials(self):
        import subprocess
        import sys
        import threading
        real_popen = subprocess.Popen
        for cancel_requested in (False, True):
            processes = []
            cancelled = threading.Event()
            def sleeping_worker(*args, **kwargs):
                self.assertEqual(kwargs['env'], {'LANG': 'C.UTF-8'})
                proc = real_popen([sys.executable, '-c', 'import time; time.sleep(30)'], **kwargs)
                processes.append(proc)
                if cancel_requested:
                    cancelled.set()
                return proc
            with patch.object(research_files.subprocess, 'Popen', side_effect=sleeping_worker), patch.object(research_files, 'DOCX_PARSE_SECONDS', .05):
                with self.assertRaisesRegex(research_files.ProjectInputError, 'cancelled|too long'):
                    research_files._docx('test.docx', b'x', cancelled)
            self.assertIsNotNone(processes[0].poll())

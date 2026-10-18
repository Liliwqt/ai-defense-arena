"""Authenticated speech/room protocol, synthetic PCM and mocked speech/AI providers."""
import asyncio
import json
import os
import unittest
from unittest.mock import patch

from backend import game_server
from backend.rooms.commands import CatchUpDeadline
from backend.question_generator import SubmissionDecision
from tests import test_opening_history_protocol as opening_protocol
from tests import test_research_coverage as coverage


class FakeSpeechSocket:
    def __init__(self):
        self.events = asyncio.Queue()
        self.forwarded = []
        self.commits = 0
        self.closed = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        self.closed = True

    async def send(self, raw):
        event = json.loads(raw)
        if event['type'] == 'session.update':
            await self.events.put({'type': 'session.updated', 'session': event['session']})
        elif event['type'] == 'input_audio_buffer.append':
            self.forwarded.append(event['audio'])
        elif event['type'] == 'input_audio_buffer.commit':
            self.commits += 1
            item = f'item-{self.commits}'
            await self.events.put({'type': 'input_audio_buffer.committed', 'item_id': item,
                                   'previous_item_id': f'item-{self.commits-1}' if self.commits > 1 else None})
            await self.events.put({'type': 'conversation.item.input_audio_transcription.completed',
                                   'item_id': item, 'transcript': 'We will evaluate the campus pilot.', 'event_id': f'final-{item}'})

    async def recv(self):
        return json.dumps(await self.events.get())


class LiveVoiceProtocolTests(unittest.TestCase):
    setUp = coverage.CoverageProtocolTests.setUp
    until = opening_protocol.OpeningHistoryProtocolTests.until
    start_opening = opening_protocol.OpeningHistoryProtocolTests.start_opening
    move = staticmethod(opening_protocol.OpeningHistoryProtocolTests.move)

    def test_manual_voice_finalization_uses_one_verified_normal_answer(self):
        provider = FakeSpeechSocket()
        def use_room(socket, state):
            socket.send_json({'type': 'cast_vote', 'seat': 0})
            self.until(socket, 'voting')
            self.now = state['vote_deadline_ms']
            self.client.portal.call(game_server._coordinator(game_server.rooms[state['room_code']]).execute, CatchUpDeadline())
            answering = self.until(socket, 'question')
            with self.client.websocket_connect(f"/ws/{state['room_code']}/speech") as speech:
                speech.send_json({'type': 'start', 'token': self.latest_host['player_token'], 'turn': 0,
                                  'view_id': answering['defense_view_id']})
                started = speech.receive_json()
                self.assertEqual(started['type'], 'started', started)
                speech.send_bytes(bytes(4800))  # 100ms of actual PCM16 at24kHz.
                usage = speech.receive_json()
                self.assertEqual(usage['remaining_ms'], 599900)
                speech.send_json({'type': 'finalize'})
                ready = speech.receive_json()
                while ready['type'] != 'ready':
                    self.assertNotEqual(ready['type'], 'error', ready)
                    ready = speech.receive_json()
                self.assertEqual(ready['text'], 'We will evaluate the campus pilot.')
                self.assertEqual(len(provider.forwarded), 1)
                # A final speech event alone did not accept an answer.
                socket.send_json({'type': 'send_chat', 'text': 'Ready to send.'})
                unchanged = self.until(socket, 'question')
                self.assertIsNone(unchanged['turns'][0]['answer'])
                socket.send_json({'type': 'submit_answer', 'turn': 0, 'answer': ready['text'],
                                  'voice_attempt': started['attempt_id']})
                accepted = self.until(socket, allow_retry=True)
                while accepted['turns'][0]['answer'] is None:
                    accepted = self.until(socket, allow_retry=True)
                self.assertEqual(accepted['turns'][0]['input_provenance']['method'], 'voice')
                self.assertEqual(accepted['turns'][0]['input_provenance']['audio_ms'], 100)
        with patch.dict(os.environ, {'VOICE_PILOT_ENABLED': '1', 'OPENAI_SPEECH_API_KEY': 'offline-speech-key'}), \
             patch('websockets.asyncio.client.connect', return_value=provider), \
             patch('backend.rooms.submissions.interpret_submission', return_value=SubmissionDecision('answer')):
            self.start_opening(lambda files,*args,**kwargs:self.move(files,'Why this campus?'), on_state=use_room)

    def answering(self, callback, provider=None):
        provider = provider or FakeSpeechSocket()
        def use_room(socket, state):
            socket.send_json({'type':'cast_vote','seat':0})
            self.until(socket, 'voting')
            self.now = state['vote_deadline_ms']
            self.client.portal.call(game_server._coordinator(game_server.rooms[state['room_code']]).execute, CatchUpDeadline())
            callback(socket, self.until(socket, 'question'), provider)
        with patch.dict(os.environ, {'VOICE_PILOT_ENABLED':'1','OPENAI_SPEECH_API_KEY':'offline-speech-key'}), \
             patch('websockets.asyncio.client.connect', return_value=provider):
            self.start_opening(lambda files,*args,**kwargs:self.move(files,'Why this campus?'), on_state=use_room)

    def speech_until(self, socket, kind):
        for _ in range(40):
            event = socket.receive_json()
            if event['type'] == kind:
                return event
            self.assertNotEqual(event['type'], 'error', event)
        self.fail('Missing speech event.')

    def hello(self, state, token=None):
        return {'type':'start','token':token or self.latest_host['player_token'],
                'turn':len(state['turns'])-1,'view_id':state['defense_view_id']}

    def test_unselected_guest_stale_scope_and_forged_voice_text_are_rejected(self):
        def check(socket,state,provider):
            guest=self.client.post(f"/api/rooms/{state['room_code']}/join",json={'name':'Guest'}).json()
            with self.client.websocket_connect(f"/ws/{state['room_code']}") as second:
                second.send_json({'type':'hello','token':guest['player_token']})
                self.until(second,'question')
                for start in (self.hello(state,guest['player_token']),{**self.hello(state),'view_id':'old-run'}):
                    with self.client.websocket_connect(f"/ws/{state['room_code']}/speech") as speech:
                        speech.send_json(start)
                        self.assertEqual(speech.receive_json()['type'],'error')
                socket.send_json({'type':'submit_answer','turn':0,'answer':'Invented voice text','voice_attempt':'forged'})
                event=socket.receive_json()
                while event['type']!='error': event=socket.receive_json()
                self.assertIn('not a current finalized',event['message'])
                self.assertEqual(provider.forwarded,[])
        self.answering(check)

    def test_duplicate_out_of_order_segments_finalize_in_commit_order(self):
        provider=FakeSpeechSocket()
        original=provider.send
        async def delayed(raw):
            if json.loads(raw)['type']=='input_audio_buffer.commit':
                provider.commits+=1
            else: await original(raw)
        provider.send=delayed
        clock=[100.0]
        def check(socket,state,provider):
            with self.client.websocket_connect(f"/ws/{state['room_code']}/speech") as speech:
                speech.send_json(self.hello(state));speech.receive_json()
                for _ in range(21):
                    clock[0]+=.1; speech.send_bytes(bytes(4800));self.speech_until(speech,'allowance')
                speech.send_json({'type':'finalize'});self.speech_until(speech,'finalizing')
                events=[{'type':'conversation.item.input_audio_transcription.completed','item_id':'b','transcript':'Then support it.','event_id':'two'},
                    {'type':'input_audio_buffer.committed','item_id':'b','previous_item_id':'a'},
                    {'type':'conversation.item.input_audio_transcription.completed','item_id':'b','transcript':'Then support it.','event_id':'two'},
                    {'type':'conversation.item.input_audio_transcription.completed','item_id':'a','transcript':'Answer directly.','event_id':'one'},
                    {'type':'input_audio_buffer.committed','item_id':'a','previous_item_id':None}]
                for event in events:self.client.portal.call(provider.events.put,event)
                ready=self.speech_until(speech,'ready')
                self.assertEqual(ready['text'],'Answer directly. Then support it.')
                socket.send_json({'type':'send_chat','text':'Not sent yet'})
                self.assertIsNone(self.until(socket,'question')['turns'][0]['answer'])
        with patch('backend.rooms.speech.monotonic',side_effect=lambda:clock[0]):self.answering(check,provider)

    def test_cap_finalizes_without_submitting_and_reconnect_preserves_usage(self):
        clock=[100.0]
        def check(socket,state,provider):
            with self.client.websocket_connect(f"/ws/{state['room_code']}/speech") as speech:
                speech.send_json(self.hello(state));speech.receive_json()
                for _ in range(5):
                    clock[0]+=.2;speech.send_bytes(bytes(9600));event=self.speech_until(speech,'allowance')
                self.assertTrue(event['capped']);self.assertEqual(event['remaining_ms'],0)
                self.assertEqual(self.speech_until(speech,'ready')['text'],'We will evaluate the campus pilot.')
                self.assertEqual(len(provider.forwarded),5)
            with self.client.websocket_connect(f"/ws/{state['room_code']}") as reconnect:
                reconnect.send_json({'type':'hello','token':self.latest_host['player_token']})
                restored=self.until(reconnect,'question')
                self.assertEqual(restored['voice']['remaining_ms'],0)
                self.assertIsNone(restored['turns'][0]['answer'])
        with patch.dict(os.environ,{'VOICE_ALLOWANCE_SECONDS':'1'}), patch('backend.rooms.speech.monotonic',side_effect=lambda:clock[0]):
            self.answering(check)

    def test_deadline_during_finalization_revokes_without_an_answer(self):
        provider=FakeSpeechSocket()
        original=provider.send
        async def delayed(raw):
            if json.loads(raw)['type']!='input_audio_buffer.commit':await original(raw)
        provider.send=delayed
        def check(socket,state,provider):
            with self.client.websocket_connect(f"/ws/{state['room_code']}/speech") as speech:
                speech.send_json(self.hello(state));started=speech.receive_json()
                speech.send_bytes(bytes(4800));self.speech_until(speech,'allowance')
                speech.send_json({'type':'finalize'});self.speech_until(speech,'finalizing')
                self.now=state['answer_deadline_ms']+1
                event=speech.receive_json()
                self.assertIn(event['type'],{'stopped','error'})
                socket.send_json({'type':'submit_answer','turn':0,'answer':'Too late','voice_attempt':started['attempt_id']})
                event=socket.receive_json()
                while event['type']!='error':
                    if event['type']=='snapshot':self.assertIsNone(event['state']['turns'][0]['answer'])
                    event=socket.receive_json()
                self.assertEqual(len(provider.forwarded),1)
        self.answering(check,provider)

    def test_finalizing_after_last_segment_already_completed_is_ready_immediately(self):
        clock=[100.0]
        def check(socket,state,provider):
            with self.client.websocket_connect(f"/ws/{state['room_code']}/speech") as speech:
                speech.send_json(self.hello(state));speech.receive_json()
                for _ in range(20):
                    clock[0]+=.1;speech.send_bytes(bytes(4800));self.speech_until(speech,'allowance')
                event=self.speech_until(speech,'transcript')
                while not event.get('finalized_text'):event=self.speech_until(speech,'transcript')
                speech.send_json({'type':'finalize'})
                ready=speech.receive_json()
                if ready['type']=='finalizing':
                    clock[0]+=9
                    ready=self.speech_until(speech,'ready')
                self.assertEqual(ready['type'],'ready')
                self.assertEqual(ready['text'],'We will evaluate the campus pilot.')
        with patch('backend.rooms.speech.monotonic',side_effect=lambda:clock[0]):self.answering(check)

    def test_malformed_audio_and_main_disconnect_stop_forwarding(self):
        def check(socket,state,provider):
            with self.client.websocket_connect(f"/ws/{state['room_code']}/speech") as speech:
                speech.send_json(self.hello(state));speech.receive_json()
                speech.send_bytes(bytes(9601))
                self.assertEqual(speech.receive_json()['type'],'error')
                self.assertEqual(provider.forwarded,[])
            with self.client.websocket_connect(f"/ws/{state['room_code']}/speech") as speech:
                speech.send_json(self.hello(state));speech.receive_json()
                speech.send_bytes(bytes(4800));self.speech_until(speech,'allowance')
                socket.close()
                self.assertEqual(speech.receive_json()['type'],'stopped')
                self.assertEqual(len(provider.forwarded),1)
        self.answering(check)

    def test_provider_overflow_is_unsent_and_allows_a_fresh_typed_answer(self):
        def check(socket,state,provider):
            with self.client.websocket_connect(f"/ws/{state['room_code']}/speech") as speech:
                speech.send_json(self.hello(state));speech.receive_json()
                speech.send_bytes(bytes(4800));self.speech_until(speech,'allowance')
                self.client.portal.call(provider.events.put,{'type':'conversation.item.input_audio_transcription.completed',
                    'item_id':'overflow','transcript':'x'*4001})
                self.assertIn('4000',speech.receive_json()['message'])
                socket.send_json({'type':'submit_direct_answer','turn':0,'answer':'A fresh typed answer.',
                                  'input_provenance':{'method':'voice','audio_ms':9999}})
                accepted=self.until(socket,allow_retry=True)
                while accepted['turns'][0]['answer'] is None:accepted=self.until(socket,allow_retry=True)
                self.assertIsNone(accepted['turns'][0]['input_provenance'])
        self.answering(check)

    def test_restarting_invalidates_active_capture_and_prior_attempt_provenance(self):
        def check(socket,state,provider):
            with self.client.websocket_connect(f"/ws/{state['room_code']}/speech") as speech:
                speech.send_json(self.hello(state));started=speech.receive_json()
                speech.send_bytes(bytes(4800));self.speech_until(speech,'allowance')
                socket.send_json({'type':'restart'})
                self.assertEqual(speech.receive_json()['type'],'stopped')
                socket.send_json({'type':'submit_answer','turn':0,'answer':'Old words','voice_attempt':started['attempt_id']})
                event=socket.receive_json()
                while event['type']!='error':event=socket.receive_json()
                self.assertIn('not a current finalized',event['message'])
                self.assertEqual(len(provider.forwarded),1)
        self.answering(check)

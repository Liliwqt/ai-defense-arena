"""Authenticated speech/room protocol, synthetic PCM and mocked speech/AI providers."""
import asyncio
import json
import os
import unittest
from unittest.mock import patch

from backend import game_server
from backend.rooms.commands import CatchUpDeadline
from backend.question_generator import SubmissionDecision, ProbeRequest
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

    def test_short_final_tail_is_padded_and_accounted_without_losing_the_answer(self):
        clock=[100.0]
        def check(socket,state,provider):
            with self.client.websocket_connect(f"/ws/{state['room_code']}/speech") as speech:
                speech.send_json(self.hello(state));started=speech.receive_json()
                for _ in range(20):
                    clock[0]+=.1;speech.send_bytes(bytes(4800));self.speech_until(speech,'allowance')
                clock[0]+=.05;speech.send_bytes(bytes(2400));self.speech_until(speech,'allowance')
                speech.send_json({'type':'finalize'})
                ready=self.speech_until(speech,'ready')
                socket.send_json({'type':'submit_direct_answer','turn':0,'answer':ready['text'],'voice_attempt':started['attempt_id']})
                accepted=self.until(socket,allow_retry=True)
                while accepted['turns'][0]['answer'] is None:accepted=self.until(socket,allow_retry=True)
                provenance=accepted['turns'][0]['input_provenance']
                self.assertEqual(provenance['audio_ms'],2100)
                self.assertEqual(provenance['padding_ms'],50)
                self.assertEqual(accepted['voice']['remaining_ms'],597900)
        with patch('backend.rooms.speech.monotonic',side_effect=lambda:clock[0]):self.answering(check)

    def test_slow_provider_write_does_not_block_chat_or_restart_revocation(self):
        import threading,time
        provider=FakeSpeechSocket();entered=threading.Event();cancelled=threading.Event()
        original=provider.send
        async def slow(raw):
            if json.loads(raw)['type']=='input_audio_buffer.append':
                entered.set()
                try:await asyncio.sleep(5)
                finally:cancelled.set()
            else:await original(raw)
        provider.send=slow
        def check(socket,state,provider):
            with self.client.websocket_connect(f"/ws/{state['room_code']}/speech") as speech:
                speech.send_json(self.hello(state));speech.receive_json()
                speech.send_bytes(bytes(4800));self.assertTrue(entered.wait(1))
                start=time.monotonic()
                socket.send_json({'type':'send_chat','text':'Provider must not block this.'})
                fresh=self.until(socket,'question')
                while not any(item['text']=='Provider must not block this.' for item in fresh['chat']):fresh=self.until(socket,'question')
                self.assertLess(time.monotonic()-start,.4)
                socket.send_json({'type':'restart'})
                self.assertEqual(speech.receive_json()['type'],'stopped')
                self.assertTrue(cancelled.wait(1))
                self.assertEqual(provider.forwarded,[])
        self.answering(check,provider)

    def test_inflight_audio_after_cap_is_discarded_while_finalization_remains_usable(self):
        clock=[100.0];provider=FakeSpeechSocket();original=provider.send
        async def delayed(raw):
            if json.loads(raw)['type']=='input_audio_buffer.commit':provider.commits+=1
            else:await original(raw)
        provider.send=delayed
        def check(socket,state,provider):
            with self.client.websocket_connect(f"/ws/{state['room_code']}/speech") as speech:
                speech.send_json(self.hello(state));started=speech.receive_json()
                for _ in range(4):
                    clock[0]+=.2;speech.send_bytes(bytes(9600));self.speech_until(speech,'allowance')
                clock[0]+=.2;speech.send_bytes(bytes(9600));speech.send_bytes(bytes(4800))
                self.assertTrue(self.speech_until(speech,'allowance')['capped'])
                for event in ({'type':'input_audio_buffer.committed','item_id':'cap','previous_item_id':None},
                    {'type':'conversation.item.input_audio_transcription.completed','item_id':'cap','transcript':'Usable final words.'}):
                    self.client.portal.call(provider.events.put,event)
                ready=self.speech_until(speech,'ready')
                self.assertEqual(len(provider.forwarded),5)
                socket.send_json({'type':'submit_direct_answer','turn':0,'answer':ready['text'],'voice_attempt':started['attempt_id']})
                accepted=self.until(socket,allow_retry=True)
                while accepted['turns'][0]['answer'] is None:accepted=self.until(socket,allow_retry=True)
                self.assertEqual(accepted['turns'][0]['answer'],'Usable final words.')
        with patch.dict(os.environ,{'VOICE_ALLOWANCE_SECONDS':'1'}),patch('backend.rooms.speech.monotonic',side_effect=lambda:clock[0]):self.answering(check,provider)

    def test_chosen_guest_can_submit_voice_and_both_clients_share_the_accepted_record(self):
        def check(socket,state,provider):
            guest=self.client.post(f"/api/rooms/{state['room_code']}/join",json={'name':'Sam'}).json()
            with self.client.websocket_connect(f"/ws/{state['room_code']}") as teammate:
                teammate.send_json({'type':'hello','token':guest['player_token']});self.until(teammate,'question')
                socket.close()
                chosen=self.until(teammate,'question')
                while chosen['selected_seat']!=1:chosen=self.until(teammate,'question')
                with self.client.websocket_connect(f"/ws/{state['room_code']}") as host:
                    host.send_json({'type':'hello','token':self.latest_host['player_token']});self.until(host,'question')
                    with self.client.websocket_connect(f"/ws/{state['room_code']}/speech") as speech:
                        speech.send_json(self.hello(chosen,guest['player_token']));started=speech.receive_json()
                        speech.send_bytes(bytes(4800));self.speech_until(speech,'allowance')
                        speech.send_json({'type':'finalize'});ready=self.speech_until(speech,'ready')
                        host.send_json({'type':'submit_answer','turn':0,'answer':ready['text'],'voice_attempt':started['attempt_id']})
                        event=host.receive_json()
                        while event['type']!='error':event=host.receive_json()
                        self.assertIn('not a current finalized',event['message'])
                        teammate.send_json({'type':'submit_answer','turn':0,'answer':ready['text'],'voice_attempt':started['attempt_id']})
                        accepted=self.until(teammate,allow_retry=True)
                        while accepted['turns'][0]['answer'] is None:accepted=self.until(teammate,allow_retry=True)
                        observed=self.until(host,allow_retry=True)
                        while observed['turns'][0]['answer'] is None:observed=self.until(host,allow_retry=True)
                        self.assertEqual(observed['turns'],accepted['turns'])
                        self.assertEqual(accepted['turns'][0]['answered_by'],'Sam')
                        self.assertEqual(accepted['turns'][0]['input_provenance']['audio_ms'],100)
        with patch('backend.rooms.submissions.interpret_submission',return_value=SubmissionDecision('answer')):self.answering(check)

    def test_voice_probe_reply_keeps_original_and_reply_provenance_separate(self):
        def check(socket,state,provider):
            with self.client.websocket_connect(f"/ws/{state['room_code']}/speech") as speech:
                speech.send_json(self.hello(state));started=speech.receive_json()
                speech.send_bytes(bytes(4800));self.speech_until(speech,'allowance')
                speech.send_json({'type':'finalize'});ready=self.speech_until(speech,'ready')
                socket.send_json({'type':'submit_answer','turn':0,'answer':ready['text'],'voice_attempt':started['attempt_id']})
                probing=self.until(socket,'probe')
                original=probing['turns'][0]['input_provenance']
            probe_id=probing['turns'][0]['probe']['id']
            provider.commits=0  # A fresh provider connection starts a new segment chain.
            with self.client.websocket_connect(f"/ws/{state['room_code']}/speech") as reply:
                reply.send_json({**self.hello(probing),'probe_id':probe_id})
                started=reply.receive_json();self.assertEqual(started['type'],'started',started)
                reply.send_bytes(bytes(9600));self.speech_until(reply,'allowance')
                reply.send_json({'type':'finalize'});ready=self.speech_until(reply,'ready')
                socket.send_json({'type':'submit_probe_reply','turn':0,'probe_id':probe_id,'answer':ready['text'],'voice_attempt':started['attempt_id'],'direct':True})
                accepted=self.until(socket,allow_retry=True)
                while accepted['turns'][0]['probe']['reply'] is None:accepted=self.until(socket,allow_retry=True)
                self.assertEqual(len(accepted['turns']),1)
                self.assertEqual(accepted['turns'][0]['input_provenance'],original)
                self.assertEqual(original['audio_ms'],100)
                self.assertEqual(accepted['turns'][0]['probe']['input_provenance']['audio_ms'],200)
                self.assertEqual(accepted['turns'][0]['probe']['speaker_name'],'Host')
                self.assertEqual(accepted['voice']['remaining_ms'],599700)
        with patch('backend.rooms.submissions.interpret_submission',return_value=SubmissionDecision('probe',probe=ProbeRequest('What will you compare?'))):self.answering(check)

    def test_finalized_unsent_draft_survives_navigation_privately_and_requires_fresh_send(self):
        def check(socket,state,provider):
            with self.client.websocket_connect(f"/ws/{state['room_code']}/speech") as speech:
                speech.send_json(self.hello(state));started=speech.receive_json()
                speech.send_bytes(bytes(4800));self.speech_until(speech,'allowance')
                speech.send_json({'type':'finalize'});ready=self.speech_until(speech,'ready')
            socket.send_json({'type':'send_chat','text':'Back from Account'})
            restored=self.until(socket,'question')
            while not any(item['text']=='Back from Account' for item in restored['chat']):restored=self.until(socket,'question')
            self.assertIsNone(restored['turns'][0]['answer'])
            self.assertEqual(restored['my_voice_draft']['attempt_id'],started['attempt_id'])
            self.assertEqual(restored['my_voice_draft']['text'],ready['text'])
            self.assertEqual(restored['voice']['remaining_ms'],599900)
            guest=self.client.post(f"/api/rooms/{state['room_code']}/join",json={'name':'Guest'}).json()
            with self.client.websocket_connect(f"/ws/{state['room_code']}") as other:
                other.send_json({'type':'hello','token':guest['player_token']})
                self.assertIsNone(self.until(other,'question').get('my_voice_draft'))
                socket.send_json({'type':'submit_direct_answer','turn':0,'answer':ready['text'],'voice_attempt':started['attempt_id']})
                accepted=self.until(socket,allow_retry=True)
                while accepted['turns'][0]['answer'] is None:accepted=self.until(socket,allow_retry=True)
                self.assertEqual(accepted['turns'][0]['input_provenance']['audio_ms'],100)
                self.assertIsNone(accepted['my_voice_draft'])
        self.answering(check)

    def test_discard_finalized_draft_revokes_proof_without_restoring_allowance(self):
        def check(socket,state,provider):
            with self.client.websocket_connect(f"/ws/{state['room_code']}/speech") as speech:
                speech.send_json(self.hello(state));started=speech.receive_json()
                speech.send_bytes(bytes(4800));self.speech_until(speech,'allowance')
                speech.send_json({'type':'finalize'});ready=self.speech_until(speech,'ready')
            socket.send_json({'type':'discard_voice_draft','attempt_id':started['attempt_id']})
            socket.send_json({'type':'send_chat','text':'Discard acknowledged'})
            fresh=self.until(socket,'question')
            while not any(item['text']=='Discard acknowledged' for item in fresh['chat']):fresh=self.until(socket,'question')
            self.assertIsNone(fresh.get('my_voice_draft'))
            self.assertEqual(fresh['voice']['remaining_ms'],599900)
            socket.send_json({'type':'submit_direct_answer','turn':0,'answer':ready['text'],'voice_attempt':started['attempt_id']})
            event=socket.receive_json()
            while event['type']!='error':event=socket.receive_json()
            self.assertIn('not a current finalized',event['message'])
        self.answering(check)

    def final_draft(self, state, provider, *, token=None):
        provider.commits=0  # Independent upstream session per capture.
        with self.client.websocket_connect(f"/ws/{state['room_code']}/speech") as speech:
            speech.send_json({**self.hello(state,token), 'probe_id':(state['turns'][-1].get('probe') or {}).get('id')})
            started=speech.receive_json();self.assertEqual(started['type'],'started',started)
            speech.send_bytes(bytes(4800));self.speech_until(speech,'allowance')
            speech.send_json({'type':'finalize'});ready=self.speech_until(speech,'ready')
        return {'answer':ready['text'],'voice_attempt':started['attempt_id']}

    def test_failed_voice_probe_interpretation_retry_and_saved_acceptance_keep_attribution(self):
        def check(socket,state,provider):
            initial=self.final_draft(state,provider)
            socket.send_json({'type':'submit_answer','turn':0,**initial})
            probing=self.until(socket,'probe');probe_id=probing['turns'][0]['probe']['id']
            reply=self.final_draft(probing,provider)
            socket.send_json({'type':'submit_probe_reply','turn':0,'probe_id':probe_id,**reply})
            failed=self.until(socket,'interpretation_retry')
            self.assertEqual(failed['my_pending_submission'],reply['answer'])
            self.assertIsNone(failed['turns'][0]['probe']['reply'])
            self.assertIsNone(failed.get('my_voice_draft'))
            socket.send_json({'type':'retry_interpretation'})
            self.until(socket,'interpretation_retry')
            socket.send_json({'type':'use_pending_as_answer'})
            accepted=self.until(socket,allow_retry=True)
            while accepted['turns'][0]['probe']['reply'] is None:accepted=self.until(socket,allow_retry=True)
            self.assertEqual(accepted['turns'][0]['probe']['input_provenance']['audio_ms'],100)
            self.assertEqual(accepted['turns'][0]['input_provenance']['audio_ms'],100)
            socket.send_json({'type':'submit_probe_reply','turn':0,'probe_id':probe_id,'direct':True,**reply})
            event=socket.receive_json()
            while event['type']!='error':event=socket.receive_json()
            self.assertIn('not a current finalized',event['message'])
        decisions=[SubmissionDecision('probe',probe=ProbeRequest('What will you compare?')),RuntimeError('Offline failure'),RuntimeError('Offline failure')]
        with patch('backend.rooms.submissions.interpret_submission',side_effect=decisions):self.answering(check)

    def test_recognized_voice_clarification_is_not_an_answer_and_obsolete_proof_is_rejected(self):
        def check(socket,state,provider):
            words=self.final_draft(state,provider)
            socket.send_json({'type':'submit_answer','turn':0,**words})
            clarified=self.until(socket,'question')
            while not clarified['turns'][0]['clarifications']:clarified=self.until(socket,'question')
            self.assertIsNone(clarified['turns'][0]['answer'])
            self.assertIsNone(clarified['turns'][0]['input_provenance'])
            self.assertIsNone(clarified.get('my_voice_draft'))
            socket.send_json({'type':'submit_direct_answer','turn':0,**words})
            event=socket.receive_json()
            while event['type']!='error':event=socket.receive_json()
            self.assertIn('not a current finalized',event['message'])
            socket.send_json({'type':'submit_direct_answer','turn':0,'answer':'A fresh typed answer.'})
            accepted=self.until(socket,allow_retry=True)
            while accepted['turns'][0]['answer'] is None:accepted=self.until(socket,allow_retry=True)
            self.assertIsNone(accepted['turns'][0]['input_provenance'])
        with patch('backend.rooms.submissions.interpret_submission',return_value=SubmissionDecision('clarify','Explain the comparison you plan.')):self.answering(check)

    def test_new_direct_answer_during_failed_voice_interpretation_never_inherits_old_provenance(self):
        def check(socket,state,provider):
            words=self.final_draft(state,provider)
            socket.send_json({'type':'submit_answer','turn':0,**words})
            self.until(socket,'interpretation_retry')
            socket.send_json({'type':'submit_direct_answer','turn':0,'answer':'A different typed explanation.'})
            accepted=self.until(socket,allow_retry=True)
            while accepted['turns'][0]['answer'] is None:accepted=self.until(socket,allow_retry=True)
            self.assertEqual(accepted['turns'][0]['answer'],'A different typed explanation.')
            self.assertIsNone(accepted['turns'][0]['input_provenance'])
        with patch('backend.rooms.submissions.interpret_submission',side_effect=RuntimeError('Offline failure')):self.answering(check)

    def test_selection_change_after_disconnect_invalidates_private_finalized_draft(self):
        def check(socket,state,provider):
            guest=self.client.post(f"/api/rooms/{state['room_code']}/join",json={'name':'Sam'}).json()
            with self.client.websocket_connect(f"/ws/{state['room_code']}") as second:
                second.send_json({'type':'hello','token':guest['player_token']});self.until(second,'question')
                words=self.final_draft(state,provider)
                socket.close()
                chosen=self.until(second,'question')
                while chosen['selected_seat']!=1:chosen=self.until(second,'question')
                self.assertIsNone(chosen.get('my_voice_draft'))
                with self.client.websocket_connect(f"/ws/{state['room_code']}") as host:
                    host.send_json({'type':'hello','token':self.latest_host['player_token']})
                    restored=self.until(host,'question');self.assertIsNone(restored.get('my_voice_draft'))
                    host.send_json({'type':'submit_direct_answer','turn':0,**words})
                    event=host.receive_json()
                    while event['type']!='error':event=host.receive_json()
                    self.assertIn('not a current finalized',event['message'])
                    self.assertEqual(restored['voice']['remaining_ms'],599900)
        self.answering(check)

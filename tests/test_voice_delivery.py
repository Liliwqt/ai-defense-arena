"""Accepted voice evidence through authenticated room and report contracts; providers mocked."""
import unittest
from tests import test_live_voice as voice


class VoiceDeliveryProtocolTests(unittest.TestCase):
    setUp=voice.LiveVoiceProtocolTests.setUp
    until=voice.LiveVoiceProtocolTests.until
    start_opening=voice.LiveVoiceProtocolTests.start_opening
    answering=voice.LiveVoiceProtocolTests.answering
    move=staticmethod(voice.LiveVoiceProtocolTests.move)
    hello=voice.LiveVoiceProtocolTests.hello
    speech_until=voice.LiveVoiceProtocolTests.speech_until
    final_draft=voice.LiveVoiceProtocolTests.final_draft

    def test_accepted_capture_has_server_sample_evidence_and_ignores_client_delivery_claims(self):
        def check(socket,state,provider):
            words=self.final_draft(state,provider)
            socket.send_json({'type':'submit_direct_answer','turn':0,**words,
                'input_provenance':{'delivery_evidence':{'capture_ms':999999,'speaking_rate':180}},
                'delivery_evidence':{'pause_count':0}})
            accepted=self.until(socket,allow_retry=True)
            while accepted['turns'][0]['answer'] is None:accepted=self.until(socket,allow_retry=True)
            evidence=accepted['turns'][0]['input_provenance']['delivery_evidence']
            self.assertEqual(evidence['capture_ms'],100)
            self.assertEqual(evidence['source'],'server_pcm_samples')
            self.assertEqual(evidence['recognition_confidence'],'not_provided')
            self.assertNotIn('speaking_rate',evidence);self.assertNotIn('pause_count',evidence)
            self.assertEqual(accepted['turns'][0]['answered_by'],'Host')
        self.answering(check)


    def test_unconfirmed_english_configuration_never_forwards_audio(self):
        import json
        class WrongLanguage(voice.FakeSpeechSocket):
            async def send(self,raw):
                event=json.loads(raw)
                if event['type']=='session.update':
                    event['session']['audio']['input']['transcription']['languages']=['tl']
                    await self.events.put({'type':'session.updated','session':event['session']})
                else:await super().send(raw)
        provider=WrongLanguage()
        def check(socket,state,provider):
            with self.client.websocket_connect(f"/ws/{state['room_code']}/speech") as speech:
                speech.send_json(self.hello(state))
                event=speech.receive_json()
                self.assertEqual(event['type'],'error')
                self.assertEqual(provider.forwarded,[])
        self.answering(check,provider)


class VoiceDeliveryReportTests(unittest.TestCase):
    def test_report_distinguishes_verified_recording_from_transcript_examples_and_unavailable_speech_measures(self):
        from backend.question_generator import AnsweredQuestion, CoachingReport
        from tests.research_coaching_fixtures import with_cards
        evidence={'version':1,'source':'server_pcm_samples','capture_ms':12000,'recognition_confidence':'not_provided','configured_language':'en'}
        words='Uhm, I I will explain the campus pilot, ang among plan.'
        history=[AnsweredQuestion('Methodology Reviewer','Why?',words,speaker_name='Alex',input_provenance={
            'method':'voice','provider':'OpenAI','model':'gpt-live-transcribe','audio_ms':12000,'padding_ms':0,'delivery_evidence':evidence}),
            AnsweredQuestion('Ethics Reviewer','Why?',words,speaker_name='Sam')]
        report=with_cards(CoachingReport('The team explained scope.',[],[],'Practice the limits.'),history)
        voice,typed=report.answer_cards
        delivery=voice['delivery']
        self.assertEqual(delivery['recording']['capture_ms'],12000)
        self.assertEqual(delivery['observations']['filler_examples'],['Uhm'])
        self.assertEqual(delivery['observations']['repetition_examples'],['I I'])
        self.assertIsNone(delivery['speaking_rate']);self.assertIsNone(delivery['pauses'])
        self.assertEqual(delivery['measurement_reason'],'word_timing_and_confidence_unavailable')
        self.assertIsNone(typed['delivery']['recording'])
        self.assertEqual(typed['delivery']['measurement_reason'],'typed_input')
        self.assertEqual(typed['speaker_name'],'Sam')

    def test_probe_and_original_have_separate_capture_and_wording_evidence_and_no_bisaya_particle_counts(self):
        from backend.question_generator import AnsweredQuestion,PanelistProbe,CoachingReport
        from tests.research_coaching_fixtures import with_cards
        proof=lambda ms:{'method':'voice','provider':'OpenAI','model':'gpt-live-transcribe','audio_ms':ms,
            'delivery_evidence':{'version':1,'source':'server_pcm_samples','capture_ms':ms,'recognition_confidence':'not_provided','configured_language':'en'}}
        probe=PanelistProbe('probe-one','Why this setting?',status='answered',reply='Ang among plan, kuan, is a campus pilot.',speaker_name='Sam',speaker_seat=1)
        history=[AnsweredQuestion('Methodology Reviewer','Why?','Uhm, I I will explain the scope.',speaker_name='Alex',probe=probe,
            input_provenance=proof(12000),probe_input_provenance=proof(200))]
        card=with_cards(CoachingReport('The team explained scope.',[],[],'Practice the limits.'),history).answer_cards[0]
        self.assertEqual(card['speaker_name'],'Alex');self.assertEqual(card['probe']['speaker_name'],'Sam')
        self.assertEqual(card['delivery']['observations']['filler_examples'],['Uhm'])
        self.assertEqual(card['probe']['delivery']['observations']['filler_examples'],[])
        self.assertEqual(card['probe']['delivery']['measurement_reason'],'recording_too_short')
        self.assertEqual(card['probe']['delivery']['recording']['capture_ms'],200)
        self.assertIsNone(card['probe']['delivery']['speaking_rate'])
        self.assertEqual(card['probe']['reply'],probe.reply)

    def test_legacy_or_invalid_capture_evidence_is_unavailable_without_placeholder_measures(self):
        from backend.question_generator import AnsweredQuestion,CoachingReport
        from tests.research_coaching_fixtures import with_cards
        for raw in (None,{'version':1,'source':'client','capture_ms':12000},
                    {'version':1,'source':'server_pcm_samples','capture_ms':-1,'recognition_confidence':'not_provided','configured_language':'en'}):
            with self.subTest(raw=raw):
                history=[AnsweredQuestion('Methodology Reviewer','Why?','We will explain the scope.',input_provenance={
                    'method':'voice','audio_ms':12000,'delivery_evidence':raw})]
                delivery=with_cards(CoachingReport('The team explained scope.',[],[],'Practice.'),history).answer_cards[0]['delivery']
                self.assertIsNone(delivery['recording'])
                self.assertIsNone(delivery['speaking_rate']);self.assertIsNone(delivery['pauses'])
                self.assertEqual(delivery['measurement_reason'],'capture_evidence_unavailable')


    def test_overview_request_receives_voice_measurement_and_delivery_limits(self):
        from backend.question_generator import AnsweredQuestion,CoachingDraft,generate_coaching_report
        from backend.project_files import ProjectFile
        from tests.test_research_coverage import Client
        history=[AnsweredQuestion('Methodology Reviewer','Why?','Uhm, we limit the claim.',input_provenance={
            'method':'voice','audio_ms':12000,'delivery_evidence':{'version':1,'source':'server_pcm_samples',
            'capture_ms':12000,'recognition_confidence':'not_provided','configured_language':'en'}})]
        client=Client(CoachingDraft(summary='The team explained scope.',strengths=[],improvements=[],next_step='Practice the limits.'))
        generate_coaching_report([ProjectFile('paper.md','A campus pilot.','research_text')],history,'offline-key',client=client,
            defense_type='research',overview_only=True)
        prompt=client.calls[0]['input'][0]['content']
        for restriction in ('never invent pace, pause or filler totals','Do not treat transcription uncertainty as poor speaking',
                            'psychological confidence','pronunciation','natural language particles'):
            self.assertIn(restriction,prompt)
        self.assertIn('server_pcm_samples',client.calls[0]['input'][1]['content'])

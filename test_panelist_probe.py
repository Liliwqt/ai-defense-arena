"""Same-question panelist probes at the shared turn and generator boundaries."""
import unittest
from defense_session import DefenseSession
from timed_turn import TimedTurn
from question_generator import GroundedQuestion, SubmissionDecision, ProbeRequest


class ProbeTurnTests(unittest.TestCase):
    def setUp(self):
        self.session = DefenseSession.start(GroundedQuestion('How will you select students?', 'paper.md', 1, 'Interview 20 students.'))
        self.room = TimedTurn(phase='question', selected_seat=0, answer_deadline_ms=120000)

    def test_probe_retains_initial_answer_and_resolves_only_after_reply(self):
        self.room.submit('ana', 'Ana', 0, 0, 'Randomly.', self.session, 1000)
        pending = self.room.pending_submission
        result = self.room.interpret(self.session, SubmissionDecision('probe', probe=ProbeRequest('From a complete list, or whoever is available?')),
                                     self.room.interpretation_id, pending, {'ana': 0}, 2000)
        self.assertEqual(result, 'probed')
        self.assertEqual(self.room.phase, 'probe')
        self.assertEqual(self.session.turns[0].answer, 'Randomly.')
        self.assertFalse(self.session.turns[0].resolved)
        self.assertFalse(self.session.needs_question)
        self.assertEqual(self.room.probe_deadline_ms, 32000)
        probe = self.session.turns[0].probe
        self.room.submit_probe_reply('ana', 'Ana', 0, 0, probe.id, 'Whoever is available.', self.session, 3000, direct=True)
        self.assertTrue(self.session.turns[0].resolved)
        self.assertEqual(self.session.turns[0].probe.reply, 'Whoever is available.')
        self.assertEqual(len(self.session.turns), 1)

    def publish_probe(self):
        self.room.submit('ana', 'Ana', 0, 0, 'Randomly.', self.session, 1000)
        self.room.interpret(self.session, SubmissionDecision('probe', probe=ProbeRequest('From a complete list?')),
                            self.room.interpretation_id, self.room.pending_submission, {'ana': 0}, 2000)
        return self.session.turns[0].probe

    def test_probe_expiry_retains_answer_and_does_not_timeout_original_question(self):
        self.publish_probe()
        self.assertEqual(self.room.expire(32000, {'ana': 0}, self.session), 'probe_expired')
        self.assertEqual(self.session.turns[0].answer, 'Randomly.')
        self.assertFalse(self.session.turns[0].timed_out)
        self.assertEqual(self.session.turns[0].probe.status, 'expired')
        self.assertIsNone(self.room.expire(32001, {'ana': 0}, self.session))

    def test_wrong_speaker_stale_submit_and_late_reply_cannot_resolve_probe(self):
        probe = self.publish_probe()
        for seat, probe_id, now in ((1, probe.id, 3000), (0, 'old', 3000), (0, probe.id, 32000)):
            with self.assertRaises(ValueError):
                self.room.submit_probe_reply('other', 'Sam', seat, 0, probe_id, 'Yes', self.session, now, direct=True)
        with self.assertRaises(ValueError):
            self.room.submit_direct('ana', 'Ana', 0, 0, 'replayed initial submit', self.session, 3000)
        self.assertFalse(self.session.turns[0].resolved)

    def test_probe_clarification_retry_and_direct_reply_keep_original_and_clock(self):
        probe = self.publish_probe()
        self.room.submit_probe_reply('ana', 'Ana', 0, 0, probe.id, 'Simplify?', self.session, 3000)
        pending, ident = self.room.pending_submission, self.room.interpretation_id
        self.room.interpretation_failed(ident, pending, 'AI unavailable')
        self.room.retry_interpretation(is_host=False, seat=0)
        self.room.interpret(self.session, SubmissionDecision('clarify', 'Which list will you draw names from?'),
                            self.room.interpretation_id, pending, {'ana': 0}, 4000)
        self.assertEqual(self.room.phase, 'probe')
        self.assertEqual(self.room.answer_deadline_ms, 33000)
        self.assertEqual(probe.clarifications[0].request, 'Simplify?')
        self.room.submit_probe_reply('ana', 'Ana', 0, 0, probe.id, 'The school list.', self.session, 5000, direct=True)
        self.assertEqual(self.session.turns[0].answer, 'Randomly.')
        self.assertEqual(probe.reply, 'The school list.')
        with self.assertRaises(ValueError):
            self.room.submit_probe_reply('ana', 'Ana', 0, 0, probe.id, 'duplicate', self.session, 5001, direct=True)

    def test_reassignment_retains_probe_clock_and_original_author(self):
        probe = self.publish_probe()
        deadline = self.room.answer_deadline_ms
        self.room.reassign({'sam': 1}, self.session)
        self.assertEqual(self.room.selected_seat, 1)
        self.assertEqual(self.room.answer_deadline_ms, deadline)
        self.room.submit_probe_reply('sam', 'Sam', 1, 0, probe.id, 'No.', self.session, 3000, direct=True)
        history = self.session.answered_history()[0]
        self.assertEqual(history.speaker_name, 'Ana')
        self.assertEqual(history.probe.speaker_name, 'Sam')
        from question_generator import serialize_transcript
        self.assertIn('"reply": "No."', serialize_transcript([history]))

    def test_final_code_question_waits_for_probe_before_completion(self):
        from defense_session import DefenseTurn
        self.session.turns = [DefenseTurn('Critical Judge', self.session.turns[0].question, answer='Earlier answer'),
                              DefenseTurn('Critical Judge', self.session.turns[0].question)]
        self.room.submit('ana', 'Ana', 0, 1, 'It works.', self.session, 1000)
        self.room.interpret(self.session, SubmissionDecision('probe', probe=ProbeRequest('What supports that?')),
                            self.room.interpretation_id, self.room.pending_submission, {'ana': 0}, 2000)
        self.assertFalse(self.session.completed)
        probe = self.session.turns[-1].probe
        self.room.submit_probe_reply('ana', 'Ana', 0, 1, probe.id, 'I cannot support it.', self.session, 3000, direct=True)
        self.assertTrue(self.session.completed)
        self.assertEqual(self.room.phase, 'complete')

    def test_explicit_probe_recovery_invalidates_pending_ai_and_keeps_original(self):
        probe = self.publish_probe()
        self.room.submit_probe_reply('ana','Ana',0,0,probe.id,'Need help.',self.session,3000)
        pending, ident = self.room.pending_submission, self.room.interpretation_id
        self.room.interpretation_failed(ident,pending,'AI unavailable')
        self.room.finish_probe(0,0,probe.id,self.session,4000)
        self.assertEqual(probe.status,'ended_early')
        self.assertEqual(self.session.turns[0].answer,'Randomly.')
        self.assertIsNone(self.room.interpret(self.session,SubmissionDecision('answer'),ident,pending,{'ana':0},5000))
        self.assertIsNone(self.room.expire(33000,{'ana':0},self.session))
        self.assertEqual(len(self.session.answered_history()),1)

    def test_research_host_ending_keeps_answer_and_marks_only_probe_ended(self):
        from defense_session import ResearchDefenseSession
        from test_research_coverage import plan
        from question_generator import ResearchMove
        self.session = ResearchDefenseSession.create(plan(),12,"research","proposal")
        self.session.apply_move(ResearchMove('Methodology Reviewer',GroundedQuestion('How?', 'paper.md',1,'Interview 20 students.'),self.session.plan.topics[0].id,False,None))
        self.publish_probe()
        self.session.end()
        self.assertTrue(self.session.completed)
        turn = self.session.turns[0]
        self.assertFalse(turn.timed_out)
        self.assertFalse(turn.ended_early)
        self.assertEqual(turn.probe.status,'ended_early')
        self.assertEqual(turn.answer,'Randomly.')
        self.assertEqual(self.session.completion_reason,'ended by host')


class ProbeGeneratorTests(unittest.TestCase):
    def test_probe_language_request_persists_after_brief_reply_in_next_prompt(self):
        from question_generator import PanelistProbe, ClarificationExchange, AnsweredQuestion, PanelMove, NextMoveDraft, generate_next_move
        from project_files import ProjectFile
        from test_question_generator import FakeClient
        probe=PanelistProbe('p','Which students?',status='answered',reply='No.',clarifications=[ClarificationExchange('Explain in Taglish please.','Aling students?')])
        history=[AnsweredQuestion('Technical Architect','How?', 'We use the school list to select students for the interviews.',probe=probe)]
        draft=NextMoveDraft(action='ask',panelist='Security Reviewer',lead_in='',question='Who can read the list?',source_file=1,evidence_line=1)
        client=FakeClient(draft)
        generate_next_move([ProjectFile('main.py','value=1')],'offline',history=history,allowed_panelists=['Security Reviewer'],may_complete=False,client=client)
        prompt=client.request['input'][0]['content']
        self.assertIn('"language": "Taglish"',prompt)
        self.assertIn('probe admission is not proof',prompt)
        transcript=client.request['input'][1]['content']
        self.assertIn('"reply": "No."',transcript)

    def test_probe_reference_uses_server_owned_excerpt_and_rejects_invalid_reference(self):
        from project_files import ProjectFile
        from question_generator import SubmissionDraft, ProbeDraft, ProbeReferenceDraft, interpret_submission, QuestionGenerationError
        from test_question_generator import FakeClient
        files = [ProjectFile('paper.md', 'Interview 20 students.')]
        args = dict(panelist='Technical Architect', question=GroundedQuestion('How?', 'paper.md', 1, files[0].content), submission='Randomly.')
        valid = SubmissionDraft(action='probe', clarification=None, probe=ProbeDraft(request='From which list?', references=[ProbeReferenceDraft(source_file=1, evidence_line=1)]))
        decision = interpret_submission(files, 'offline-key', client=FakeClient(valid), **args)
        self.assertEqual(decision.probe.references[0].evidence_text, 'Interview 20 students.')
        invalid = valid.model_copy(update={'probe': ProbeDraft(request='From which list?', references=[ProbeReferenceDraft(source_file=1, evidence_line=99)])})
        with self.assertRaises(QuestionGenerationError):
            interpret_submission(files, 'offline-key', client=FakeClient(invalid), **args)

    def test_nested_probe_and_conflicting_fields_are_rejected(self):
        from question_generator import SubmissionDraft, ProbeDraft, PanelistProbe, interpret_submission, QuestionGenerationError
        from project_files import ProjectFile
        from test_question_generator import FakeClient
        args = dict(panelist='Technical Architect', question=GroundedQuestion('Why?', 'main.py', 1, 'value=1'), submission='Yes.')
        draft = SubmissionDraft(action='probe', clarification=None, probe=ProbeDraft(request='Why again?', references=[]))
        with self.assertRaises(QuestionGenerationError):
            interpret_submission([ProjectFile('main.py', 'value=1')], 'offline', client=FakeClient(draft),
                                 probe=PanelistProbe('p', 'What supports it?'), **args)
        conflicting = SubmissionDraft(action='answer', clarification=None, probe=draft.probe)
        with self.assertRaises(QuestionGenerationError):
            interpret_submission([ProjectFile('main.py', 'value=1')], 'offline', client=FakeClient(conflicting), **args)

class ProbeProtocolTests(unittest.TestCase):
    def setUp(self):
        from test_game_server import GameServerTests
        GameServerTests.setUp(self)
        for name in ('socket_message_rate', 'socket_room_rate'):
            limiter = getattr(__import__('game_server'), name, None)
            if limiter is None:
                continue
            from unittest.mock import patch
            clock = patch.object(limiter, 'clock', side_effect=lambda: self.clock_ms / 1000)
            clock.start()
            self.addCleanup(clock.stop)

    def create_room(self):
        from test_game_server import GameServerTests
        return GameServerTests.create_room(self)

    def join_room(self, code, name='Sam'):
        from test_game_server import GameServerTests
        return GameServerTests.join_room(self, code, name)

    def connect(self, code, token):
        from test_game_server import GameServerTests
        return GameServerTests.connect(self, code, token)

    def receive_phase(self, socket, phase):
        from test_game_server import GameServerTests
        return GameServerTests.receive_phase(self, socket, phase)

    def test_two_clients_complete_four_and_eight_turns_with_same_turn_probes(self):
        import os
        import game_server as server
        from unittest.mock import patch
        from question_generator import PanelMove, CoachingReport
        for eight in (False, True):
            with self.subTest(eight=eight):
                server.rooms.clear()
                roles = [role for role in server.PANELIST_ORDER for _ in range(2)] if eight else list(server.PANELIST_ORDER)
                moves = [PanelMove(role, GroundedQuestion(f'Question {i+1}?', 'queue.py', 5, self.questions[0].evidence_text))
                         for i, role in enumerate(roles)][1:] + [PanelMove(None, None)]
                # Probe first and final answers, with one defender clarification.
                decisions = []
                for i in range(len(roles)):
                    decisions.append(SubmissionDecision('probe', probe=ProbeRequest('Which specific decision do you mean?')) if i in (0, len(roles)-1) else SubmissionDecision('answer'))
                    if i == 0:
                        decisions.extend([SubmissionDecision('clarify', 'Name the decision in your answer.'), SubmissionDecision('answer')])
                    elif i == len(roles)-1:
                        decisions.append(SubmissionDecision('answer'))
                with patch.dict(os.environ, {'OPENAI_API_KEY':'offline'}), patch.object(server, 'generate_first_question', return_value=self.questions[0]), patch.object(server, 'generate_next_move', side_effect=moves), patch.object(server, 'interpret_submission', side_effect=decisions), patch.object(server, 'generate_coaching_report', return_value=CoachingReport('Review.', [], [], 'Practice.')):
                    host = self.create_room(); guest = self.join_room(host['room_code'])
                    hs,_ = self.connect(host['room_code'], host['player_token'])
                    gs,_ = self.connect(host['room_code'], guest['player_token'])
                    try:
                        hs.send_json({'type':'start'})
                        for i in range(len(roles)):
                            states = [self.receive_phase(ws, 'question') for ws in (hs,gs)]
                            speaker = gs if i % 2 == 0 else hs
                            speaker.send_json({'type':'submit_answer','turn':i,'answer':f'Original answer {i}.'})
                            if i in (0,len(roles)-1):
                                states = [self.receive_phase(ws,'probe') for ws in (hs,gs)]
                                self.assertEqual(states[0]['turns'][-1]['probe'], states[1]['turns'][-1]['probe'])
                                self.assertEqual(len(states[0]['turns']), i+1)
                                self.assertFalse(states[0]['turns'][-1]['resolved'])
                                probe = states[0]['turns'][-1]['probe']
                                if i == 0:
                                    speaker.send_json({'type':'submit_probe_reply','turn':i,'probe_id':probe['id'],'answer':'Simplify?'})
                                    states = [self.receive_phase(ws,'probe') for ws in (hs,gs)]
                                    self.assertEqual(states[0]['turns'][-1]['probe']['clarifications'][0]['request'], 'Simplify?')
                                    # Reconnect a spectator while the selected host/guest is replying.
                                    spectator = hs
                                    spectator.__exit__(None,None,None)
                                    hs,state = self.connect(host['room_code'], host['player_token'])
                                    self.assertEqual(state['turns'][-1]['probe']['id'],probe['id'])
                                speaker.send_json({'type':'submit_probe_reply','turn':i,'probe_id':probe['id'],'answer':'The storage choice.'})
                        states = [self.receive_phase(ws,'complete') for ws in (hs,gs)]
                        for state in states:
                            self.assertEqual(len(state['turns']),len(roles))
                            self.assertEqual(state['turns'][0]['answer'],'Original answer 0.')
                            self.assertEqual(state['turns'][-1]['probe']['reply'],'The storage choice.')
                            self.assertTrue(state['turns'][-1]['resolved'])
                    finally:
                        hs.__exit__(None,None,None);gs.__exit__(None,None,None)

    def test_research_and_mixed_stop_at_budget_after_probe_expiry_and_retry(self):
        import os
        import game_server as server
        from contextlib import ExitStack
        from unittest.mock import patch
        from test_research_coverage import PAPER, plan, proposal, Client
        from question_generator import generate_research_move, CoachingReport
        for mode in ('research', 'mixed'):
            with self.subTest(mode=mode), ExitStack() as stack:
                server.rooms.clear()
                stack.enter_context(patch.dict(os.environ, {'OPENAI_API_KEY':'offline'}))
                planned = plan(4)
                stack.enter_context(patch.object(server,'generate_research_plan',return_value=planned))
                def generate(files,key,*,history,context,**kwargs):
                    output = proposal(context, history)
                    if output['action']=='ask':
                        output['source_file'] = next(i for i,f in enumerate(files,1) if f.kind.startswith('research'))
                    return generate_research_move(files,key,history=history,context=context,client=Client(output),**kwargs)
                stack.enter_context(patch.object(server,'generate_research_move',side_effect=generate))
                decisions = [SubmissionDecision('probe',probe=ProbeRequest('Which group will you recruit?'))] + [SubmissionDecision('answer')] * 2 + [SubmissionDecision('probe',probe=ProbeRequest('What supports your conclusion?')), RuntimeError('offline failure'), SubmissionDecision('answer')]
                stack.enter_context(patch.object(server,'interpret_submission',side_effect=decisions))
                captured = []
                def coach(files,history,*args,**kwargs):
                    captured.extend(history)
                    return CoachingReport('Review retained answers.',[],[],'Practice.')
                stack.enter_context(patch.object(server,'generate_coaching_report',side_effect=coach))
                files = [('research_files',('paper.md',PAPER.encode(),'text/markdown'))]
                if mode == 'mixed': files += [('files',('main.py',b'value=1','text/x-python'))]
                response = self.client.post('/api/rooms',data={'host_name':'Alex','defense_type':mode},files=files)
                self.assertEqual(response.status_code,201,response.text)
                host=response.json();guest=self.join_room(host['room_code'])
                hs,_=self.connect(host['room_code'],host['player_token']);gs,_=self.connect(host['room_code'],guest['player_token'])
                try:
                    hs.send_json({'type':'prepare_research_plan'})
                    while True:
                        state=hs.receive_json()
                        if state['type']=='snapshot' and state['state']['research_planning_status']=='ready': break
                    hs.send_json({'type':'approve_research_plan','plan_id':planned.id,'question_budget':4})
                    hs.send_json({'type':'start','plan_id':planned.id,'question_budget':4})
                    for i in range(4):
                        for ws in (hs,gs): self.receive_phase(ws,'question')
                        speaker=gs if i%2==0 else hs
                        speaker.send_json({'type':'submit_answer','turn':i,'answer':f'Original answer {i}.'})
                        if i in (0,3):
                            states=[self.receive_phase(ws,'probe') for ws in (hs,gs)]
                            probe=states[0]['turns'][-1]['probe']
                            if i==0:
                                self.clock_ms = states[0]['probe_deadline_ms']
                                self.client.portal.call(server._expire_deadline,server.rooms[host['room_code']])
                            else:
                                speaker.send_json({'type':'submit_probe_reply','turn':i,'probe_id':probe['id'],'answer':'It is only a proposal.'})
                                for ws in (hs,gs): self.receive_phase(ws,'interpretation_retry')
                                hs.send_json({'type':'retry_interpretation'})
                    states=[self.receive_phase(ws,'complete') for ws in (hs,gs)]
                    while states[0]['feedback_status']!='ready': states[0]=self.receive_phase(hs,'complete')
                    self.assertEqual(len(states[0]['turns']),4)
                    self.assertEqual(states[0]['completion_reason'],'budget exhausted')
                    self.assertEqual(states[0]['turns'][0]['probe']['status'],'expired')
                    self.assertFalse(states[0]['turns'][0]['timed_out'])
                    self.assertEqual(states[0]['turns'][-1]['probe']['reply'],'It is only a proposal.')
                    self.assertEqual(len(captured),4)
                    self.assertEqual(captured[0].answer,'Original answer 0.')
                finally:
                    hs.__exit__(None,None,None);gs.__exit__(None,None,None)


class ProbeStreamlitTests(unittest.TestCase):
    def test_streamlit_keeps_same_question_until_probe_reply_without_fake_timer(self):
        import os
        from unittest.mock import patch
        from streamlit.testing.v1 import AppTest
        from test_research_coverage import PAPER, plan, mocked_move
        with patch.dict(os.environ, {'OPENAI_API_KEY':'offline'}), patch('research_plan.generate_research_plan',return_value=plan()), patch('defense_session.generate_research_move',side_effect=mocked_move), patch('question_generator.interpret_submission',side_effect=[SubmissionDecision('probe',probe=ProbeRequest('Which students?')),SubmissionDecision('answer')]):
            app=AppTest.from_file('app.py').run()
            app.selectbox[0].select('Research paper').run()
            app.file_uploader[0].set_value([('paper.md',PAPER.encode(),'text/markdown')]).run()
            next(b for b in app.button if b.label=='Prepare defense').click().run()
            app.number_input[0].set_value(12).run()
            next(b for b in app.button if b.label=='Confirm question budget').click().run()
            next(b for b in app.button if b.label=='Start defense').click().run()
            app.text_area[0].set_value('Randomly.').run()
            next(b for b in app.button if b.label=='Send to panelist').click().run()
            session=app.session_state['defense_session']
            self.assertFalse(app.exception)
            self.assertEqual(len(session.turns),1)
            self.assertEqual(session.turns[0].answer,'Randomly.')
            self.assertEqual(app.text_area[0].label,'Your probe reply or clarification request')
            app.text_area[0].set_value('Available students.').run()
            next(b for b in app.button if b.label=='Send to panelist').click().run()
            self.assertFalse(app.exception)
            self.assertEqual(len(session.turns),2)
            self.assertEqual(session.turns[0].probe.reply,'Available students.')

    def test_failed_streamlit_probe_can_end_with_original_answer(self):
        import os
        from unittest.mock import patch
        from streamlit.testing.v1 import AppTest
        from test_research_coverage import PAPER, plan, mocked_move
        from question_generator import QuestionGenerationError
        with patch.dict(os.environ, {'OPENAI_API_KEY':'offline'}), patch('research_plan.generate_research_plan',return_value=plan()), patch('defense_session.generate_research_move',side_effect=mocked_move), patch('question_generator.interpret_submission',side_effect=[SubmissionDecision('probe',probe=ProbeRequest('Which students?')),QuestionGenerationError('AI unavailable')]):
            app=AppTest.from_file('app.py').run()
            app.selectbox[0].select('Research paper').run()
            app.file_uploader[0].set_value([('paper.md',PAPER.encode(),'text/markdown')]).run()
            next(b for b in app.button if b.label=='Prepare defense').click().run()
            app.number_input[0].set_value(12).run()
            next(b for b in app.button if b.label=='Confirm question budget').click().run()
            next(b for b in app.button if b.label=='Start defense').click().run()
            app.text_area[0].set_value('Randomly.').run()
            next(b for b in app.button if b.label=='Send to panelist').click().run()
            app.text_area[0].set_value('Available students.').run()
            next(b for b in app.button if b.label=='Send to panelist').click().run()
            next(b for b in app.button if b.label=='Continue with original answer').click().run()
            session=app.session_state['defense_session']
            self.assertFalse(app.exception)
            self.assertEqual(session.turns[0].answer,'Randomly.')
            self.assertEqual(session.turns[0].probe.status,'ended_early')
            self.assertEqual(len(session.turns),2)

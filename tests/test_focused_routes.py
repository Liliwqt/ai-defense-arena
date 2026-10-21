"""Focused lookup through funded, authenticated rooms; AI/provider HTTP is mocked."""
from dataclasses import replace
import json
from unittest.mock import patch

import httpx

from backend import game_server
from backend.openrouter_questions import RunQuestionPolicy, run_scope
from backend.provider_allowance import ProviderAllowance
from backend.question_generator import RESEARCH_PANELISTS, CoachingReport
from backend.rooms import planning, coaching
from backend.rooms.commands import CatchUpDeadline
from backend.timed_turn import VOTE_MS
from tests.research_coaching_fixtures import with_cards, scope_options
from tests.test_openrouter_interactions import FundedInteractionRooms, clarification, probe, combined_answer
from tests.test_openrouter_questions import planner_move, reviewer_question, assessment
from tests.test_research_plan import PAPER


METHOD, ETHICS, IMPACT, CRITICAL = RESEARCH_PANELISTS
LATE = 'Deferred retention comparison uses the twelve-week follow-up interviews.'
LOOKUP = {'lookup': {'query': 'retention twelve week follow up interviews', 'source_files': []}}


class FocusedRouteTests(FundedInteractionRooms):
    def prepare(self, socket):
        socket.send_json({'type':'prepare_research_plan'})
        self.until(socket,research_planning_status='ready')
        socket.send_json({'type':'approve_research_plan','plan_id':self.plan.id,
                          'question_budget':4,'confirm_profile':True,'acknowledge_uncertainty':True})
        self.until(socket,research_plan_approved=True)
        socket.send_json({'type':'start','plan_id':self.plan.id,'question_budget':4})

    def create_case(self, mode='research', approach='qualitative'):
        self.plan = replace(self.plan, profile=replace(self.plan.profile, approaches=(approach,)))
        appendix = '\n'.join(['General appendix background.']*39 + [LATE])
        files = [('research_files', ('study.md', PAPER.encode(), 'text/markdown')),
                 ('research_files', ('appendix.md', appendix.encode(), 'text/markdown'))]
        if mode == 'mixed':
            files.insert(0, ('files', ('pilot.py', b'consent_required = True\n', 'text/x-python')))
        created = self.client.post('/api/rooms', data={'host_name': 'Host', 'defense_type': mode,
                                                     'research_stage': 'proposal'}, files=files)
        self.assertEqual(created.status_code, 201, created.text)
        host = created.json()
        guest = self.client.post(f"/api/rooms/{host['room_code']}/join", json={'name': 'Sam'}).json()
        return host, guest

    def open_outputs(self, source=1):
        return [planner_move(METHOD, 'topic-1'), reviewer_question('How will you justify the study design?', source_file=source)]

    def test_interpretation_lookup_is_focused_and_writer_recovery_keeps_original(self):
        host, guest = self.create_case()
        code = host['room_code']
        calls = self.funded(*self.open_outputs(), LOOKUP, combined_answer(),
                            httpx.Response(404, text='{}'),
                            reviewer_question('How will consent cover later interviews?', evidence_line=6))
        with patch.object(planning, 'generate_research_plan', return_value=self.plan):
            with self.client.websocket_connect(f'/ws/{code}') as h, self.client.websocket_connect(f'/ws/{code}') as g:
                before = self.open_question(((h, host['player_token']), (g, guest['player_token'])))
                h.send_json({'type': 'submit_answer', 'turn': 0, 'answer': 'We plan follow-up interviews.'})
                for socket in (h, g):
                    state = self.until(socket, phase='retry')
                    self.assertEqual(state['turns'][0]['answer'], 'We plan follow-up interviews.')
                self.assertNotIn(LATE, calls[2]['messages'][1]['content'])
                self.assertIn(LATE, calls[3]['messages'][1]['content'])
                self.assertIn('Focused accepted evidence', calls[2]['messages'][1]['content'])
                self.assertEqual(calls[2]['response_format']['json_schema']['name'], 'CombinedSubmissionDraft')
                h.send_json({'type': 'retry'})
                for socket in (h, g):
                    self.until(socket, 'voting', 2)
                self.assertEqual([c['response_format']['json_schema']['name'] for c in calls[4:]], ['QuestionDraft']*2)

    def test_expanded_writer_context_survives_opening_retry_without_another_lookup(self):
        host, guest = self.create_case(approach='theoretical')
        code = host['room_code']
        calls = self.funded(planner_move(METHOD, 'topic-1'), LOOKUP, httpx.Response(404, text='{}'),
                            reviewer_question('How does the retention comparison support the design?', source_file=2, evidence_line=40))
        with patch.object(planning, 'generate_research_plan', return_value=self.plan):
            with self.client.websocket_connect(f'/ws/{code}') as h, self.client.websocket_connect(f'/ws/{code}') as g:
                for socket, token in ((h, host['player_token']), (g, guest['player_token'])):
                    socket.send_json({'type': 'hello', 'token': token}); self.until(socket, phase='lobby')
                self.prepare(h)
                for socket in (h, g): self.until(socket, phase='retry')
                h.send_json({'type': 'retry'})
                for socket in (h, g):
                    state = self.until(socket, 'voting', 1)
                    self.assertEqual(state['turns'][0]['filename'], 'appendix.md')
                self.assertEqual(len(calls), 4)
                self.assertIn(LATE, calls[-1]['messages'][1]['content'])
                self.assertIn('FILE 2: appendix.md', calls[-1]['messages'][1]['content'])

    def test_repeated_or_empty_lookup_recovers_without_accepting_an_answer(self):
        for missing in (False, True):
            with self.subTest(missing=missing):
                host, guest = self.create_case()
                code = host['room_code']
                output = {'lookup': {'query': 'unfindablexyz', 'source_files': []}} if missing else LOOKUP
                opening = self.open_outputs()
                opening[1]['question'] += ' Missing case?' if missing else ' Repeated case?'
                calls = self.funded(*opening, output, LOOKUP)
                with patch.object(planning, 'generate_research_plan', return_value=self.plan):
                    with self.client.websocket_connect(f'/ws/{code}') as h, self.client.websocket_connect(f'/ws/{code}') as g:
                        before = self.open_question(((h, host['player_token']), (g, guest['player_token'])))
                        h.send_json({'type': 'submit_answer', 'turn': 0, 'answer': 'Retain this explanation.'})
                        for socket in (h, g):
                            failed = self.until(socket, phase='interpretation_retry')
                            self.assertEqual(failed['turns'], before['turns'])
                            self.assertEqual(failed['coverage'], before['coverage'])
                            self.assertEqual(failed['answer_deadline_ms'], before['answer_deadline_ms'])
                            self.assertFalse(failed['clock_paused'])
                        self.assertEqual(len(calls), 3 if missing else 4)

    def test_mixed_decision_and_unknown_source_lookup_cannot_advance_state(self):
        for invalid in ({**LOOKUP, **combined_answer()},
                        {'lookup': {'query':'retention interviews','source_files':[999]}}):
            with self.subTest(invalid=invalid):
                host, guest = self.create_case()
                code = host['room_code']
                opening = self.open_outputs()
                opening[1]['question'] += ' Mixed case?' if 'action' in invalid else ' Source case?'
                calls = self.funded(*opening, invalid)
                with patch.object(planning,'generate_research_plan',return_value=self.plan):
                    with self.client.websocket_connect(f'/ws/{code}') as h, self.client.websocket_connect(f'/ws/{code}') as g:
                        before = self.open_question(((h,host['player_token']),(g,guest['player_token'])))
                        h.send_json({'type':'submit_answer','turn':0,'answer':'Preserve this pending answer.'})
                        for socket in (h,g):
                            state = self.until(socket,phase='interpretation_retry')
                            self.assertEqual(state['coverage'],before['coverage'])
                            self.assertIsNone(state['turns'][0]['answer'])
                        self.assertEqual(len(calls),3)

    def test_lookup_must_fit_the_existing_processing_window(self):
        host, guest = self.create_case()
        code = host['room_code']
        def elapsed(index):
            if index == 3: self.now += 45000
        calls = self.funded(*self.open_outputs(), LOOKUP, combined_answer(), on_call=elapsed)
        with patch.object(planning, 'generate_research_plan', return_value=self.plan):
            with self.client.websocket_connect(f'/ws/{code}') as h, self.client.websocket_connect(f'/ws/{code}') as g:
                before = self.open_question(((h, host['player_token']), (g, guest['player_token'])))
                h.send_json({'type': 'submit_answer', 'turn': 0, 'answer': 'Keep my pending response.'})
                for socket in (h, g):
                    state = self.until(socket, phase='interpretation_retry')
                    self.assertIsNone(state['turns'][0]['answer'])
                    self.assertEqual(state['coverage'], before['coverage'])
                self.assertEqual(len(calls), 3)

    def test_lookup_cannot_spend_protected_coaching_or_release_unknown_usage(self):
        host, guest = self.create_case()
        code = host['room_code']
        def exhaust(index):
            if index == 3:
                allowance = ProviderAllowance(run_scope(game_server.rooms[code].run_id), self._offline_credentials[2]['id'])
                policy = RunQuestionPolicy(**allowance.policy())
                # PostgreSQL SUM(bigint) returns Decimal; reserve accepts only
                # integer nano-USD on both supported database adapters.
                allowance.reserve(policy.question_limit_nano-int(allowance.snapshot()['used']), limit=policy.question_limit_nano)
        calls = self.funded(*self.open_outputs(), LOOKUP, combined_answer(), on_call=exhaust, usage={})
        with patch.object(planning, 'generate_research_plan', return_value=self.plan):
            with self.client.websocket_connect(f'/ws/{code}') as h, self.client.websocket_connect(f'/ws/{code}') as g:
                self.open_question(((h, host['player_token']), (g, guest['player_token'])))
                h.send_json({'type': 'submit_answer', 'turn': 0, 'answer': 'Keep this explanation.'})
                for socket in (h, g):
                    state = self.until(socket, phase='interpretation_retry')
                    self.assertIsNone(state['turns'][0]['answer'])
                allowance = ProviderAllowance(run_scope(game_server.rooms[code].run_id), self._offline_credentials[2]['id'])
                policy = RunQuestionPolicy(**allowance.policy())
                self.assertEqual(allowance.snapshot()['remaining'], policy.coaching_reserve_nano)
                self.assertEqual(len(calls), 3)

    def _complete(self, mode, approach):
        host, guest = self.create_case(mode, approach)
        code = host['room_code']; source = 2 if mode == 'mixed' else 1
        outputs = [LOOKUP, *self.open_outputs(source), LOOKUP, clarification('Explain the comparison, not the outcome.'),
                   LOOKUP, probe(), LOOKUP, combined_answer(),
                   reviewer_question('How will consent be recorded?', source_file=source, evidence_line=6)]
        for i, role in ((1, IMPACT), (2, CRITICAL)):
            outputs += [{'action':'answer','clarification':None,'probe':None,
                         'assessment':assessment(f'topic-{i+1}',i),'panelist':role,
                         'topic_id':f'topic-{i+2}','is_follow_up':False},
                        reviewer_question(f'How will you justify decision {i+2}?',
                            source_file=1 if mode=='mixed' and i==2 else source,
                            evidence_line=1 if mode=='mixed' and i==2 else 8)]
        outputs += [{'action':'answer','clarification':None,'probe':None,
                     'assessment':assessment('topic-4',3),'panelist':None,'topic_id':None,'is_follow_up':False}]
        def coach(files, history, key, model, **kwargs):
            return with_cards(CoachingReport('Discussion complete.',[],[],'Practice the limits.'),history,**scope_options(kwargs))
        calls = self.funded(*outputs)
        with patch.object(planning,'generate_research_plan',return_value=self.plan), \
             patch.object(coaching,'generate_coaching_report',side_effect=coach):
            with self.client.websocket_connect(f'/ws/{code}') as h, self.client.websocket_connect(f'/ws/{code}') as g:
                self.open_question(((h,host['player_token']),(g,guest['player_token'])))
                h.send_json({'type':'submit_answer','turn':0,'answer':'Please explain in modern Bisaya.'})
                for socket in (h,g): self.until(socket,phase='question')
                h.send_json({'type':'submit_answer','turn':0,'answer':'Our comparison covers volunteers only.'})
                for socket in (h,g): state=self.until(socket,phase='probe')
                h.send_json({'type':'submit_probe_reply','turn':0,'probe_id':state['turns'][0]['probe']['id'],'answer':'The same campus recruitment criteria.'})
                for i in range(1,4):
                    for socket in (h,g): self.until(socket,'voting',i+1)
                    h.send_json({'type':'cast_vote','seat':0})
                    for socket in (h,g): self.until(socket,'voting',i+1)
                    self.now+=VOTE_MS+1
                    self.client.portal.call(game_server.rooms[code].coordinator.execute,CatchUpDeadline())
                    for socket in (h,g): self.until(socket,'question',i+1)
                    h.send_json({'type':'submit_answer','turn':i,'answer':'We will report this bounded comparison.'})
                for socket in (h,g):
                    final=self.until(socket,'complete',4,feedback_status='ready')
                    self.assertEqual(final['turns'][0]['probe']['reply'],'The same campus recruitment criteria.')
                    self.assertEqual(len(final['feedback']['answer_cards']),4)
                    if mode=='mixed': self.assertEqual(final['turns'][3]['filename'],'pilot.py')
        for call in calls:
            text=call['messages'][1]['content']
            self.assertIn('Focused accepted evidence',text)
            self.assertIn('source_description',text)
        self.assertEqual(sum('BROADER LOOKUP' in c['messages'][1]['content'] for c in calls),5)

    def test_complete_qualitative_research_with_planner_clarification_probe_lookups(self):
        self._complete('research','qualitative')

    def test_complete_theoretical_mixed_with_cross_document_lookups(self):
        self._complete('mixed','theoretical')

    def test_complete_confirmed_uncertainty_with_lookups(self):
        self._complete('research','unclear')

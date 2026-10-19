"""Same-reviewer funded interactions; OpenRouter, AI and clocks are offline."""

import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

import httpx

from backend import game_server
from backend.defense_session import ResearchDefenseSession
from backend.openrouter_questions import (
    INTERACTION_OUTPUT_TOKENS, RunQuestionClient, RunQuestionPolicy,
    establish_run_allowance, run_scope,
)
from backend.provider_allowance import ProviderAllowance
from backend.project_files import ProjectFile
from backend.question_generator import (
    CODE_PANELISTS, RESEARCH_PANELISTS, QuestionGenerationError, SubmissionDraft,
)
from backend.rooms import planning as planning_workflow
from backend.rooms.commands import CatchUpDeadline
from backend.timed_turn import ANSWER_MS, VOTE_MS
from tests import test_research_coverage as coverage
from tests import test_research_plan as maps
from tests.test_openrouter_questions import (
    HTTPClient, assessment, planner_move, reviewer_question, stream_response,
)

METHODOLOGY, ETHICS = RESEARCH_PANELISTS[:2]
PAPER = maps.PAPER
ANSWER = 'We compared queue waiting times for the pilot group.'


def clarification(text='We mean the measured pilot wait, not a guess.'):
    return {'action': 'clarify', 'clarification': text, 'probe': None}


def probe(request='Which comparison group did you use?'):
    return {'action': 'probe', 'clarification': None,
            'probe': {'request': request, 'references': []}}


def answer():
    return {'action': 'answer', 'clarification': None, 'probe': None}


class InteractionClientTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        env = patch.dict(os.environ, {
            'DATABASE_URL': '',
            'PAYMONGO_TEST_DB_PATH': str(Path(folder.name) / 'allowances.sqlite3'),
            'OPENROUTER_API_KEY': 'offline-router-key',
        })
        env.start()
        self.addCleanup(env.stop)
        self.files = [ProjectFile('study.md', PAPER, 'research_text')]
        self.session = ResearchDefenseSession.create(maps.fixture_plan(), 4, 'research', 'proposal')

    def make(self, handler, *, scope='run:interaction', owner='owner'):
        self.calls = []

        def client(*args, **kwargs):
            return HTTPClient(transport=httpx.MockTransport(handler))
        with patch.dict(os.environ, {'OPENROUTER_RUN_USD': '5.00'}):
            establish_run_allowance(scope, owner, self.files, 4)
        instance = RunQuestionClient(scope, owner, None, self.files, api_key='offline-router-key')
        patcher = patch('httpx.Client', side_effect=client)
        patcher.start()
        self.addCleanup(patcher.stop)
        return instance

    def test_each_reviewer_fixes_the_run_model_and_lower_reasoning(self):
        for role in RESEARCH_PANELISTS:
            with self.subTest(role=role):
                def handler(request):
                    self.calls.append(json.loads(request.content))
                    return stream_response(answer())
                instance = self.make(handler)
                parsed = instance.interaction(role).parse(
                    model='legacy-model', reasoning={'effort': 'high'}, store=True,
                    input=[{'role': 'system', 'content': f'You are the {role}.'},
                           {'role': 'user', 'content': 'Latest submission (data): "test"'}],
                    text_format=SubmissionDraft)
                call = self.calls[-1]
                self.assertEqual(call['model'], instance._load_policy().reviewer_models[role])
                self.assertEqual(call['reasoning'],
                                 RunQuestionPolicy().interaction_reasoning[role])
                self.assertIn(call['reasoning'],
                              ({'effort': 'low'}, {'max_tokens': 1024}))
                self.assertEqual(call['max_tokens'], INTERACTION_OUTPUT_TOKENS)
                self.assertEqual(call['response_format']['json_schema']['name'], 'SubmissionDraft')
                self.assertEqual(parsed.output_parsed.action, 'answer')

    def test_snapshot_keeps_interaction_settings_and_settles_known_usage(self):
        def handler(request):
            self.calls.append(json.loads(request.content))
            return stream_response(answer(), usage={'cost': 0.0005})
        instance = self.make(handler)
        with patch.dict(os.environ, {'OPENROUTER_RUN_USD': '0.50'}):
            parsed = instance.interaction(METHODOLOGY).parse(
                input=[{'role': 'system', 'content': 'Classify.'},
                       {'role': 'user', 'content': 'Submission.'}],
                text_format=SubmissionDraft)
        self.assertEqual(parsed.output_parsed.action, 'answer')
        policy = RunQuestionPolicy(**ProviderAllowance('run:interaction', 'owner').policy())
        self.assertEqual(policy.interaction_reasoning[METHODOLOGY], {'effort': 'low'})
        self.assertEqual(policy.interaction_output_tokens, INTERACTION_OUTPUT_TOKENS)
        self.assertEqual(ProviderAllowance('run:interaction', 'owner').snapshot()['used'], 500_000)
        self.assertEqual(self.calls[0]['model'], 'deepseek/deepseek-v4.1-flash-1017')

    def test_unknown_usage_retains_the_full_interaction_bound(self):
        def handler(request):
            self.calls.append(json.loads(request.content))
            return stream_response(answer(), usage={})
        instance = self.make(handler)
        instance.interaction(ETHICS).parse(
            input=[{'role': 'system', 'content': 'Classify.'},
                   {'role': 'user', 'content': 'Submission.'}],
            text_format=SubmissionDraft)
        policy = RunQuestionPolicy(**ProviderAllowance('run:interaction', 'owner').policy())
        call = self.calls[0]
        bound = policy.stage_bound(len(json.dumps(
            {'messages': call['messages'], 'schema': call['response_format']},
            ensure_ascii=False).encode()) + 8192, INTERACTION_OUTPUT_TOKENS)
        snapshot = ProviderAllowance('run:interaction', 'owner').snapshot()
        self.assertEqual(snapshot['used'], bound)

    def test_unassigned_panelist_is_rejected_before_dispatch(self):
        def handler(request):
            self.calls.append(json.loads(request.content))
            return stream_response(answer())
        instance = self.make(handler)
        with self.assertRaisesRegex(QuestionGenerationError, 'provider policy is unavailable'):
            instance.interaction(CODE_PANELISTS[0]).parse(
                input=[{'role': 'system', 'content': 'Classify.'}], text_format=SubmissionDraft)
        self.assertEqual(self.calls, [])


class FundedInteractionProtocolTests(coverage.CoverageProtocolTests):
    test_twelve_question_research_and_mixed_with_vote_clarification_timeout_retry_reconnect_coaching = None
    test_twelve_question_pdf_research_and_mixed_preserve_private_originals_and_citations = None

    def setUp(self):
        super().setUp()
        env = patch.dict(os.environ, {'OPENROUTER_RUN_USD': '5.00'})
        env.start()
        self.addCleanup(env.stop)
        self.plan = maps.fixture_plan()

    def funded(self, *outputs, usage=None, on_call=None):
        calls = []

        def provider(request):
            calls.append(json.loads(request.content))
            if on_call is not None:
                on_call(len(calls))
            output = outputs[min(len(calls), len(outputs)) - 1]
            return output if isinstance(output, httpx.Response) else stream_response(output, usage=usage)

        def client(*args, **kwargs):
            return HTTPClient(transport=httpx.MockTransport(provider))
        patcher = patch('httpx.Client', side_effect=client)
        patcher.start()
        self.addCleanup(patcher.stop)
        return calls

    def create_room(self):
        files = [('research_files', ('study.md', PAPER.encode(), 'text/markdown'))]
        response = self.client.post('/api/rooms', data={
            'host_name': 'Host', 'host_passcode': 'offline-passcode',
            'defense_type': 'research', 'research_stage': 'proposal'}, files=files)
        self.assertEqual(response.status_code, 201, response.text)
        host = response.json()
        guest = self.client.post(f"/api/rooms/{host['room_code']}/join",
                                 json={'name': 'Sam'}).json()
        return host, guest

    def prepare(self, socket):
        socket.send_json({'type': 'prepare_research_plan'})
        self.until(socket, research_planning_status='ready')
        socket.send_json({'type': 'approve_research_plan', 'plan_id': self.plan.id,
                          'question_budget': 4, 'confirm_profile': True})
        self.until(socket, research_plan_approved=True)
        socket.send_json({'type': 'start', 'plan_id': self.plan.id, 'question_budget': 4})

    def open_question(self, sockets):
        for socket, token in sockets:
            socket.send_json({'type': 'hello', 'token': token})
            self.until(socket, 'lobby')
        self.prepare(sockets[0][0])
        self.until(sockets[0][0], 'voting')
        sockets[0][0].send_json({'type': 'cast_vote', 'seat': 0})
        state = self.until(sockets[0][0], 'voting')
        self.now += VOTE_MS + 1
        room = game_server.rooms[state['room_code']]
        self.client.portal.call(game_server._coordinator(room).execute, CatchUpDeadline())
        for socket, _ in sockets:
            state = self.until(socket, 'question', 1)
        return state

    def test_clarification_probe_and_reply_stay_with_the_speaking_reviewer(self):
        outputs = [planner_move(METHODOLOGY, 'topic-1'),
                   reviewer_question('How will the team justify the stated pilot design?'),
                   clarification(), probe(), answer(),
                   planner_move(ETHICS, 'topic-2', assessment=assessment('topic-1', 0)),
                   reviewer_question('How will the team report claim changes?', evidence_line=6,
                                     lead_in='You described the pilot decision.')]
        host, guest = self.create_room()
        code = host['room_code']
        with patch.object(planning_workflow, 'generate_research_plan', return_value=self.plan):
            with self.client.websocket_connect(f'/ws/{code}') as h, \
                 self.client.websocket_connect(f'/ws/{code}') as g:
                calls = self.funded(*outputs)
                state = self.open_question(((h, host['player_token']), (g, guest['player_token'])))
                self.assertEqual(state['turns'][0]['question'],
                                 'How will the team justify the stated pilot design?')
                h.send_json({'type': 'submit_answer', 'turn': 0, 'answer': ANSWER})
                for socket in (h, g):
                    state = self.until(socket, phase='question')
                    self.assertEqual(len(state['turns']), 1)
                    self.assertEqual(state['turns'][0]['clarifications'],
                                     [{'request': ANSWER, 'reply': 'We mean the measured pilot wait, not a guess.'}])
                    self.assertEqual(state['turns'][0]['answer'], None)
                h.send_json({'type': 'submit_answer', 'turn': 0, 'answer': ANSWER})
                for socket in (h, g):
                    state = self.until(socket, phase='probe')
                    self.assertEqual(len(state['turns']), 1)
                    self.assertEqual(state['turns'][0]['probe']['request'],
                                     'Which comparison group did you use?')
                    self.assertEqual(state['turns'][0]['probe']['status'], 'pending')
                probe_id = state['turns'][0]['probe']['id']
                h.send_json({'type': 'submit_probe_reply', 'turn': 0, 'answer': ANSWER,
                             'probe_id': probe_id})
                for socket in (h, g):
                    state = self.until(socket, 'voting', 2)
                    self.assertEqual(state['turns'][0]['probe']['status'], 'answered')
                    self.assertEqual(state['turns'][0]['probe']['reply'], ANSWER)
                    self.assertEqual(state['turns'][1]['question'],
                                     'How will the team report claim changes?')
        self.assertEqual([call['model'] for call in calls],
                         ['z-ai/glm-5.3-flash', 'deepseek/deepseek-v4.1-flash-1017',
                          'deepseek/deepseek-v4.1-flash-1017', 'deepseek/deepseek-v4.1-flash-1017',
                          'deepseek/deepseek-v4.1-flash-1017', 'z-ai/glm-5.3-flash',
                          'anthropic/claude-haiku-5.5'])
        self.assertEqual([call['reasoning'] for call in calls],
                         [{'effort': 'low'}, {'effort': 'high'}, {'effort': 'low'},
                          {'effort': 'low'}, {'effort': 'low'}, {'effort': 'low'},
                          {'effort': 'medium'}])
        for call in calls[2:5]:
            self.assertEqual(call['response_format']['json_schema']['name'], 'SubmissionDraft')
            self.assertEqual(call['max_tokens'], INTERACTION_OUTPUT_TOKENS)
            self.assertIn('Methodology Reviewer', call['messages'][0]['content'])
            self.assertIn(ANSWER, call['messages'][1]['content'])
        self.assertIn('We mean the measured pilot wait',
                      calls[3]['messages'][1]['content'])
        self.assertIn('Which comparison group did you use?',
                      calls[4]['messages'][1]['content'])
        account = self._offline_credentials[2]
        snapshot = ProviderAllowance(f'run:{game_server.rooms[code].run_id}', account['id']).snapshot()
        self.assertEqual(snapshot['used'], 7 * 500_000)

    def test_manual_retry_keeps_the_run_assignment_and_does_not_double_dispatch(self):
        outputs = [planner_move(METHODOLOGY, 'topic-1'),
                   reviewer_question('How will the team justify the stated pilot design?'),
                   httpx.Response(503, text='{}'), clarification()]
        host, guest = self.create_room()
        code = host['room_code']
        with patch.object(planning_workflow, 'generate_research_plan', return_value=self.plan):
            with self.client.websocket_connect(f'/ws/{code}') as h, \
                 self.client.websocket_connect(f'/ws/{code}') as g:
                calls = self.funded(*outputs)
                self.open_question(((h, host['player_token']), (g, guest['player_token'])))
                h.send_json({'type': 'submit_answer', 'turn': 0, 'answer': ANSWER})
                for socket in (h, g):
                    state = self.until(socket, phase='interpretation_retry')
                    self.assertIn('HTTP 503', state['error'])
                    self.assertEqual(state['turns'][0]['answer'], None)
                self.assertEqual(len(calls), 3)
                with patch.dict(os.environ, {'OPENROUTER_RUN_USD': '0.50'}):
                    h.send_json({'type': 'retry_interpretation'})
                    for socket in (h, g):
                        state = self.until(socket, phase='question')
                        self.assertEqual(state['turns'][0]['clarifications'][0]['reply'],
                                         'We mean the measured pilot wait, not a guess.')
                self.assertEqual(len(calls), 4)
                h.send_json({'type': 'retry_interpretation'})
                for _ in range(10):
                    if h.receive_json()['type'] == 'error':
                        break
                else:
                    self.fail('The duplicate retry was accepted.')
                self.assertEqual(len(calls), 4)
        self.assertEqual([call['model'] for call in calls[2:]],
                         ['deepseek/deepseek-v4.1-flash-1017'] * 2)
        self.assertEqual([call['reasoning'] for call in calls[2:]],
                         [{'effort': 'low'}] * 2)

    def test_exhausted_allowance_keeps_the_saved_answer_and_blocks_paid_retry(self):
        outputs = [planner_move(METHODOLOGY, 'topic-1'),
                   reviewer_question('How will the team justify the stated pilot design?')]
        host, guest = self.create_room()
        code = host['room_code']
        with patch.object(planning_workflow, 'generate_research_plan', return_value=self.plan):
            with self.client.websocket_connect(f'/ws/{code}') as h, \
                 self.client.websocket_connect(f'/ws/{code}') as g:
                calls = self.funded(*outputs)
                original = self.open_question(((h, host['player_token']), (g, guest['player_token'])))
                room = game_server.rooms[code]
                account = self._offline_credentials[2]
                allowance = ProviderAllowance(run_scope(room.run_id), account['id'])
                policy = RunQuestionPolicy(**allowance.policy())
                limit = policy.question_limit_nano
                allowance.reserve(limit - allowance.snapshot()['used'] - 1_000, limit=limit)
                self.assertGreaterEqual(allowance.snapshot()['remaining'],
                                        policy.coaching_reserve_nano)
                h.send_json({'type': 'submit_answer', 'turn': 0, 'answer': ANSWER})
                for socket in (h, g):
                    state = self.until(socket, phase='interpretation_retry')
                    self.assertIn('cannot fund another question', state['error'])
                    self.assertIn('retained', state['error'])
                    self.assertIs(state['clock_paused'], False)
                    self.assertEqual(state['answer_deadline_ms'], original['answer_deadline_ms'])
                self.assertEqual(len(calls), 2)
                h.send_json({'type': 'retry_interpretation'})
                for socket in (h, g):
                    state = self.until(socket, phase='interpretation_retry')
                    self.assertIsNotNone(state['answer_deadline_ms'])
                    self.assertIs(state['clock_paused'], False)
                self.assertEqual(len(calls), 2)
                h.send_json({'type': 'use_pending_as_answer'})
                for socket in (h, g):
                    state = self.until(socket, phase='retry')
                    self.assertEqual(state['turns'][0]['answer'], ANSWER)
                    self.assertEqual(state['my_pending_submission'], None)
                self.assertEqual(len(calls), 2)

    def test_slow_interaction_cannot_extend_the_answer_deadline(self):
        outputs = [planner_move(METHODOLOGY, 'topic-1'),
                   reviewer_question('How will the team justify the stated pilot design?'),
                   clarification(),
                   planner_move(ETHICS, 'topic-2', assessment=assessment(
                       'topic-1', 0, status='needs clarification')),
                   reviewer_question('How will the team report claim changes?', evidence_line=6,
                                     lead_in='No answer was recorded.')]

        def advance(count):
            if count == 3:
                self.now += ANSWER_MS + 300_000
        host, guest = self.create_room()
        code = host['room_code']
        with patch.object(planning_workflow, 'generate_research_plan', return_value=self.plan):
            with self.client.websocket_connect(f'/ws/{code}') as h, \
                 self.client.websocket_connect(f'/ws/{code}') as g:
                self.funded(*outputs, on_call=advance)
                state = self.open_question(((h, host['player_token']), (g, guest['player_token'])))
                deadline = state['answer_deadline_ms']
                h.send_json({'type': 'submit_answer', 'turn': 0, 'answer': ANSWER})
                for socket in (h, g):
                    state = self.until(socket, 'voting', 2)
                    self.assertTrue(state['turns'][0]['timed_out'])
                    self.assertEqual(state['turns'][0]['answer'], None)
                    self.assertEqual(state['turns'][0]['clarifications'], [])
                    self.assertEqual(state['turns'][1]['question'],
                                     'How will the team report claim changes?')
                self.assertGreater(self.now, deadline)

    def test_failed_interaction_resumes_the_answer_clock(self):
        outputs = [planner_move(METHODOLOGY, 'topic-1'),
                   reviewer_question('How will the team justify the stated pilot design?'),
                   httpx.Response(503, text='{}'),
                   planner_move(ETHICS, 'topic-2',
                                assessment=assessment('topic-1', 0, status='needs clarification')),
                   reviewer_question('How will the team report claim changes?',
                                     lead_in='No answer was recorded.')]
        host, guest = self.create_room()
        code = host['room_code']
        with patch.object(planning_workflow, 'generate_research_plan', return_value=self.plan):
            with self.client.websocket_connect(f'/ws/{code}') as h, \
                 self.client.websocket_connect(f'/ws/{code}') as g:
                calls = self.funded(*outputs)
                state = self.open_question(((h, host['player_token']), (g, guest['player_token'])))
                first_deadline = state['answer_deadline_ms']
                h.send_json({'type': 'submit_answer', 'turn': 0, 'answer': ANSWER})
                for socket in (h, g):
                    failed = self.until(socket, phase='interpretation_retry')
                    self.assertIn('HTTP 503', failed['error'])
                    self.assertIs(failed['clock_paused'], False)
                    self.assertIsNone(failed['pause_deadline_ms'])
                    self.assertEqual(failed['answer_deadline_ms'], first_deadline)
                self.now = failed['answer_deadline_ms'] + 1
                self.client.portal.call(
                    game_server._coordinator(game_server.rooms[code]).execute, CatchUpDeadline())
                for socket in (h, g):
                    state = self.until(socket, 'voting', 2)
                    self.assertTrue(state['turns'][0]['timed_out'])
                    self.assertEqual(state['turns'][0]['answer'], None)
                    self.assertEqual(state['turns'][1]['question'],
                                     'How will the team report claim changes?')
        self.assertEqual(len(calls), 5)

    def test_retry_repauses_only_for_the_elapsed_processing_time(self):
        entered, release = threading.Event(), threading.Event()
        outputs = [planner_move(METHODOLOGY, 'topic-1'),
                   reviewer_question('How will the team justify the stated pilot design?'),
                   httpx.Response(503, text='{}'),
                   clarification()]

        def gate(count):
            if count == 4:
                entered.set()
                release.wait(10)
        host, guest = self.create_room()
        code = host['room_code']
        with patch.object(planning_workflow, 'generate_research_plan', return_value=self.plan):
            with self.client.websocket_connect(f'/ws/{code}') as h, \
                 self.client.websocket_connect(f'/ws/{code}') as g:
                self.funded(*outputs, on_call=gate)
                state = self.open_question(((h, host['player_token']), (g, guest['player_token'])))
                first_deadline = state['answer_deadline_ms']
                h.send_json({'type': 'submit_answer', 'turn': 0, 'answer': ANSWER})
                for socket in (h, g):
                    failed = self.until(socket, phase='interpretation_retry')
                    self.assertEqual(failed['answer_deadline_ms'], first_deadline)
                self.now += 10_000
                h.send_json({'type': 'retry_interpretation'})
                self.assertTrue(entered.wait(10))
                for socket in (h, g):
                    reviewing = self.until(socket, phase='interpreting')
                    self.assertIs(reviewing['clock_paused'], True)
                    self.assertIsNotNone(reviewing['pause_deadline_ms'])
                    self.assertEqual(reviewing['remaining_answer_ms'], ANSWER_MS - 10_000)
                self.now += 5_000
                release.set()
                for socket in (h, g):
                    state = self.until(socket, phase='question')
                    self.assertIs(state['clock_paused'], False)
                    self.assertEqual(state['answer_deadline_ms'], first_deadline + 5_000)

    def test_failed_probe_reply_resumes_the_probe_clock(self):
        outputs = [planner_move(METHODOLOGY, 'topic-1'),
                   reviewer_question('How will the team justify the stated pilot design?'),
                   probe(),
                   httpx.Response(503, text='{}')]
        host, guest = self.create_room()
        code = host['room_code']
        with patch.object(planning_workflow, 'generate_research_plan', return_value=self.plan):
            with self.client.websocket_connect(f'/ws/{code}') as h, \
                 self.client.websocket_connect(f'/ws/{code}') as g:
                self.funded(*outputs)
                self.open_question(((h, host['player_token']), (g, guest['player_token'])))
                h.send_json({'type': 'submit_answer', 'turn': 0, 'answer': ANSWER})
                for socket in (h, g):
                    state = self.until(socket, phase='probe')
                probe_id = state['turns'][0]['probe']['id']
                probe_deadline = state['answer_deadline_ms']
                h.send_json({'type': 'submit_probe_reply', 'turn': 0, 'answer': ANSWER,
                             'probe_id': probe_id})
                for socket in (h, g):
                    failed = self.until(socket, phase='interpretation_retry')
                    self.assertIn('HTTP 503', failed['error'])
                    self.assertIs(failed['clock_paused'], False)
                    self.assertIsNone(failed['pause_deadline_ms'])
                    self.assertEqual(failed['answer_deadline_ms'], probe_deadline)
                    self.assertEqual(failed['turns'][0]['probe']['status'], 'pending')

    def test_delayed_budget_retry_keeps_consumed_answer_time(self):
        self.check_delayed_retry(budget=True)

    def test_delayed_clarification_retry_keeps_consumed_answer_time(self):
        self.check_delayed_retry()

    def test_delayed_probe_clarification_retry_keeps_consumed_reply_time(self):
        self.check_delayed_retry(probe_reply=True)

    def check_delayed_retry(self, *, budget=False, probe_reply=False):
        outputs = [planner_move(METHODOLOGY, 'topic-1'),
                   reviewer_question('How will the team justify the stated pilot design?')]
        if probe_reply:
            outputs.append(probe())
        outputs += [httpx.Response(503, text='{}'), clarification()]
        host, guest = self.create_room()
        code = host['room_code']
        with patch.object(planning_workflow, 'generate_research_plan', return_value=self.plan):
            with self.client.websocket_connect(f'/ws/{code}') as h, \
                 self.client.websocket_connect(f'/ws/{code}') as g:
                calls = self.funded(*outputs)
                state = self.open_question(((h, host['player_token']), (g, guest['player_token'])))
                if probe_reply:
                    h.send_json({'type': 'submit_answer', 'turn': 0, 'answer': ANSWER})
                    for socket in (h, g):
                        state = self.until(socket, phase='probe')
                deadline = state['answer_deadline_ms']
                room = game_server.rooms[code]
                if budget:
                    allowance = ProviderAllowance(run_scope(room.run_id), self._offline_credentials[2]['id'])
                    policy = RunQuestionPolicy(**allowance.policy())
                    allowance.reserve(policy.question_limit_nano - allowance.snapshot()['used'] - 1000,
                                      limit=policy.question_limit_nano)
                command = {'type': 'submit_probe_reply' if probe_reply else 'submit_answer',
                           'turn': 0, 'answer': ANSWER}
                if probe_reply:
                    command['probe_id'] = state['turns'][0]['probe']['id']
                h.send_json(command)
                for socket in (h, g):
                    self.until(socket, phase='interpretation_retry')
                self.now += 10_000 if probe_reply else 100_000
                remaining = deadline - self.now
                h.send_json({'type': 'retry_interpretation'})
                phase = 'interpretation_retry' if budget else 'probe' if probe_reply else 'question'
                for socket in (h, g):
                    state = self.until(socket, phase=phase)
                    self.assertEqual(state['answer_deadline_ms'], deadline)
                    self.assertFalse(state['clock_paused'])
                    if budget:
                        self.assertEqual(state['remaining_answer_ms'], remaining)
                        self.assertEqual(state['my_pending_submission'], ANSWER if socket is h else None)
                    elif probe_reply:
                        self.assertEqual(state['turns'][0]['probe']['status'], 'pending')
                        self.assertEqual(state['probe_deadline_ms'], deadline)
                    self.assertEqual(len(state['turns']), 1)
                self.assertEqual(len(calls), 2 if budget else 5 if probe_reply else 4)

    def test_duplicate_submission_is_rejected_and_reconnect_sees_the_pending_answer(self):
        entered, release = threading.Event(), threading.Event()
        outputs = [planner_move(METHODOLOGY, 'topic-1'),
                   reviewer_question('How will the team justify the stated pilot design?'),
                   clarification()]

        def gate(count):
            if count == 3:
                entered.set()
                release.wait(10)
        host, guest = self.create_room()
        code = host['room_code']
        with patch.object(planning_workflow, 'generate_research_plan', return_value=self.plan):
            with self.client.websocket_connect(f'/ws/{code}') as h, \
                 self.client.websocket_connect(f'/ws/{code}') as g:
                self.funded(*outputs, on_call=gate)
                self.open_question(((h, host['player_token']), (g, guest['player_token'])))
                h.send_json({'type': 'submit_answer', 'turn': 0, 'answer': ANSWER})
                self.assertTrue(entered.wait(10))
                h.send_json({'type': 'submit_answer', 'turn': 0, 'answer': ANSWER})
                for _ in range(10):
                    event = h.receive_json()
                    if event['type'] == 'error':
                        self.assertIn('no question awaiting', event['message'])
                        break
                else:
                    self.fail('Duplicate submission was not rejected')
                with self.client.websocket_connect(f'/ws/{code}') as restored:
                    restored.send_json({'type': 'hello', 'token': guest['player_token']})
                    state = restored.receive_json()['state']
                    self.assertEqual(state['phase'], 'interpreting')
                    self.assertIsNone(state['my_pending_submission'])
                with self.client.websocket_connect(f'/ws/{code}') as restored:
                    restored.send_json({'type': 'hello', 'token': host['player_token']})
                    state = restored.receive_json()['state']
                    self.assertEqual(state['phase'], 'interpreting')
                    self.assertEqual(state['my_pending_submission'], ANSWER)
                release.set()
                for socket in (h, g):
                    self.until(socket, phase='question')

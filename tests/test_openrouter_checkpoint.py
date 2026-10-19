"""Complete authenticated two-client text runs; provider HTTP is synthetic."""

import json
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import httpx

from backend import account_store, game_server
from backend.openrouter_questions import run_scope
from backend.provider_allowance import ProviderAllowance
from backend.rooms.commands import CatchUpDeadline
from backend.timed_turn import VOTE_MS
from tests import test_research_coverage as coverage
from tests.test_openrouter_streamlit import SyntheticRouter
from tests.test_openrouter_questions import HTTPClient
from tests.test_research_plan import PAPER


class RoomAnswers:
    def __init__(self, code):
        self.code = code

    def __getitem__(self, key):
        assert key == 'defense_session'
        return game_server.rooms[self.code].defense


class OpenRouterTextCheckpointTests(unittest.TestCase):
    setUp = coverage.CoverageProtocolTests.setUp
    def until(self, socket, phase=None, count=None, **conditions):
        # Unexpected retry must fail with its public diagnostic instead of
        # waiting indefinitely for a voting state that cannot arrive.
        for _ in range(60):
            event = socket.receive_json()
            if event['type'] == 'error':
                self.fail(event['message'])
            state = event['state']
            if state['phase'] == 'retry':
                self.fail(state.get('error') or 'Unexpected question retry.')
            if ((phase is None or state['phase'] == phase) and
                (count is None or len(state['turns']) == count) and
                all(state.get(key) == value for key, value in conditions.items())):
                return state
        self.fail('Missing checkpoint room state.')

    def test_twelve_question_research_and_mixed_fund_every_stage_and_retain_partial_results(self):
        for mode in ('research', 'mixed'):
            with self.subTest(mode=mode):
                uploads = [('research_files', ('study.md', PAPER.encode(), 'text/markdown'))]
                if mode == 'mixed':
                    uploads.append(('files', ('queue.py', b'queue = []\n', 'text/x-python')))
                response = self.client.post('/api/rooms', data={'host_name': 'Host',
                    'defense_type': mode, 'research_stage': 'proposal'}, files=uploads)
                self.assertEqual(response.status_code, 201, response.text)
                host = response.json()
                code = host['room_code']
                guest = self.client.post(f'/api/rooms/{code}/join', json={'name': 'Sam'}).json()
                room = game_server.rooms[code]
                router = SyntheticRouter(mixed=mode == 'mixed')
                router.app = SimpleNamespace(session_state=RoomAnswers(code))
                profile_fields = ['Education', 'Software engineering'] if mode == 'mixed' else ['Public health']
                calls = []

                def provider(request):
                    body = json.loads(request.content)
                    calls.append(body)
                    if body['response_format']['json_schema']['name'] == 'ResearchPlanDraft':
                        # Distinct confirmed lenses, with exact accepted-source citations.
                        from tests.test_research_plan import draft
                        from tests.test_openrouter_questions import stream_response
                        output = draft()
                        output['profile']['fields'] = profile_fields
                        output['profile']['approaches'] = ['qualitative', 'computational/design'] if mode == 'mixed' else ['qualitative']
                        if mode == 'mixed':
                            for topic in output['topics']:
                                topic['references'][0]['source_file'] = 2
                            output['profile']['references'][0]['source_file'] = 2
                        return stream_response(output)
                    if body['response_format']['json_schema']['name'] == 'QuestionDraft':
                        from tests.test_openrouter_questions import stream_response
                        context = json.JSONDecoder().raw_decode(body['messages'][-1]['content'].split('Server research context (data):\n')[1])[0]
                        return stream_response({'lead_in': '',
                            'question': f"How will you explain {mode} decision {context['generated_questions']+1}?",
                            'source_file': 2 if mode == 'mixed' else 1, 'evidence_line': 4})
                    return router(request)

                with patch('httpx.Client', side_effect=lambda **kw: HTTPClient(transport=httpx.MockTransport(provider))):
                    with self.client.websocket_connect(f'/ws/{code}') as h, \
                         self.client.websocket_connect(f'/ws/{code}') as g:
                        for socket, identity in ((h, host), (g, guest)):
                            socket.send_json({'type': 'hello', 'token': identity['player_token']})
                            self.until(socket, 'lobby')
                        h.send_json({'type': 'prepare_research_plan'})
                        prepared = self.until(h, research_planning_status='ready')
                        self.assertEqual(prepared['research_plan']['profile']['fields'], profile_fields)
                        h.send_json({'type': 'approve_research_plan', 'plan_id': prepared['research_plan']['id'],
                            'question_budget': 12, 'confirm_profile': True})
                        self.until(h, research_plan_approved=True)
                        h.send_json({'type': 'start', 'plan_id': prepared['research_plan']['id'], 'question_budget': 12})
                        for index in range(12):
                            for socket in (h, g):
                                self.until(socket, 'voting', index + 1)
                            for socket in (h, g):
                                socket.send_json({'type': 'cast_vote', 'seat': index % 2})
                            self.until(h, 'voting', index + 1, vote_counts={'0': 2 if index % 2 == 0 else 0, '1': 2 if index % 2 else 0})
                            self.now += VOTE_MS
                            self.client.portal.call(game_server._coordinator(room).execute, CatchUpDeadline())
                            for socket in (h, g):
                                state = self.until(socket, 'question', index + 1)
                                self.assertEqual(state['selected_seat'], index % 2)
                                self.assertEqual(state['turns'][-1]['evidence_text'], PAPER.splitlines()[3])
                            speaker = h if index % 2 == 0 else g
                            if index == 1:
                                router.decisions = [{'action': 'clarify', 'clarification': 'Explain the comparison you plan.', 'probe': None}]
                                speaker.send_json({'type': 'submit_answer', 'turn': index, 'answer': 'Please explain the comparison.'})
                                for socket in (h, g):
                                    state = self.until(socket, 'question', index + 1, clock_paused=False)
                                    self.assertEqual(len(state['turns'][-1]['clarifications']), 1)
                            if index == 2:
                                router.decisions = [{'action': 'probe', 'clarification': None,
                                    'probe': {'request': 'Which baseline will you use?', 'references': []}}]
                            if index == 3:
                                router.fail_name = 'PlanDraft'
                            speaker.send_json({'type': 'submit_answer', 'turn': index, 'answer': 'We will limit our claim to the campus pilot.'})
                            if index == 2:
                                for socket in (h, g):
                                    state = self.until(socket, 'probe', index + 1)
                                speaker.send_json({'type': 'submit_probe_reply', 'turn': index,
                                    'probe_id': state['turns'][-1]['probe']['id'], 'answer': 'A documented baseline period.'})
                            if index == 11:
                                router.fail_turns = [3, 4, 5]
                        partial = [self.until(socket, 'complete', 12, feedback_status='failed') for socket in (h, g)]
                        self.assertEqual(partial[0]['feedback'], partial[1]['feedback'])
                        self.assertEqual(partial[0]['coaching_progress']['cards_ready'], 9)
                        before = partial[0]['feedback']['answer_cards']
                        count = len(calls)
                        h.send_json({'type': 'retry_coaching'})
                        completed = [self.until(socket, 'complete', 12, feedback_status='ready') for socket in (h, g)]
                        self.assertEqual(len(calls), count + 1)
                        self.assertEqual(completed[0]['feedback'], completed[1]['feedback'])
                        final = completed[0]
                        self.assertEqual(final['coaching_progress']['completion_status'], 'ready')
                        self.assertEqual(final['coaching_progress']['cards_ready'], 12)
                        self.assertEqual([card for card in final['feedback']['answer_cards'] if card['turn'] not in (3, 4, 5)], before)
                        self.assertEqual(final['turns'][2]['probe']['reply'], 'A documented baseline period.')
                    with self.client.websocket_connect(f'/ws/{code}') as reconnect:
                        reconnect.send_json({'type': 'hello', 'token': guest['player_token']})
                        restored = self.until(reconnect, 'complete', 12, feedback_status='ready')
                        self.assertEqual(restored['feedback'], final['feedback'])
                        self.assertEqual(restored['turns'], final['turns'])
                overview = account_store.account_overview(self._offline_credentials[2]['id'])
                record = next(run for run in overview['runs'] if run['id'] == room.run_id)
                self.assertEqual(record['status'], 'charged')
                self.assertEqual(record['cost'], 0)  # existing voucher fixture
                used = ProviderAllowance(run_scope(room.run_id), room.owner_account_id).snapshot()['used']
                self.assertGreater(used, 30_000_000)  # known usage plus conservative failed-request holds
                coaching = [body for body in calls if 'CoachingDraft' in body['response_format']['json_schema']['name']]
                self.assertEqual(len(coaching), 6)  # overview + four sections + failed-only retry
                self.assertEqual(sum(body['response_format']['json_schema']['name'] == 'CoachingDraft' for body in coaching), 1)

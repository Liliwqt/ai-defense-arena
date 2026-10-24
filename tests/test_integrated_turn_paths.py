"""Integrated eight/twelve-question defenses covering the remaining turn paths.

Complements `test_openrouter_checkpoint` (which covers the funded twelve-question
happy path and progressive coaching) with the paths ticket 09 requires: answer
timeouts, direct and saved recovery, host ending, restart, and changed-context
invalidation. Provider HTTP stays synthetic; no paid inference runs.
"""

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
from tests.test_openrouter_checkpoint import RoomAnswers
from tests.test_openrouter_streamlit import SyntheticRouter
from tests.test_openrouter_questions import HTTPClient, stream_response
from tests.test_research_plan import PAPER, draft


class IntegratedTurnPathTests(unittest.TestCase):
    setUp = coverage.CoverageProtocolTests.setUp

    def until(self, socket, phase=None, count=None, **conditions):
        for _ in range(80):
            event = socket.receive_json()
            if event['type'] == 'error':
                self.fail(event['message'])
            state = event['state']
            if ((phase is None or state['phase'] == phase)
                    and (count is None or len(state['turns']) == count)
                    and all(state.get(key) == value for key, value in conditions.items())):
                return state
        self.fail('Missing integrated room state.')

    def provider(self, router, mode, calls):
        def handle(request):
            body = json.loads(request.content)
            calls.append(body)
            name = body['response_format']['json_schema']['name']
            if name == 'ResearchPlanDraft':
                output = draft()
                output['profile']['fields'] = ['Public health']
                output['profile']['approaches'] = ['qualitative']
                return stream_response(output)
            if name == 'QuestionDraft':
                context = json.JSONDecoder().raw_decode(
                    body['messages'][-1]['content'].split('Server research context (data):\n')[1])[0]
                return stream_response({'lead_in': '',
                    'question': f"How will you explain decision {context['generated_questions']+1}?",
                    'source_file': 1, 'evidence_line': 4})
            return router(request)
        return handle

    def open_room(self, mode='research', tier='standard'):
        uploads = [('research_files', ('study.md', PAPER.encode(), 'text/markdown'))]
        if mode == 'mixed':
            uploads.append(('files', ('queue.py', b'queue = []\n', 'text/x-python')))
        response = self.client.post('/api/rooms', data={'host_name': 'Host',
            'defense_type': mode, 'research_stage': 'proposal', 'practice_tier': tier}, files=uploads)
        self.assertEqual(response.status_code, 201, response.text)
        host = response.json()
        code = host['room_code']
        guest = self.client.post(f'/api/rooms/{code}/join', json={'name': 'Sam'}).json()
        return host, guest, code, game_server.rooms[code]

    def prepare(self, h, g, budget):
        h.send_json({'type': 'prepare_research_plan'})
        prepared = self.until(h, research_planning_status='ready')
        h.send_json({'type': 'approve_research_plan', 'plan_id': prepared['research_plan']['id'],
                     'question_budget': budget, 'confirm_profile': True})
        self.until(h, research_plan_approved=True)
        return prepared

    def vote_and_ask(self, h, g, room, index):
        # The room may already be voting for this turn after a resolved answer.
        for socket in (h, g):
            if room.phase != 'voting':
                self.until(socket, 'voting', index + 1)
        for socket in (h, g):
            socket.send_json({'type': 'cast_vote', 'seat': index % 2})
        self.until(h, 'voting', index + 1,
                   vote_counts={'0': 2 if index % 2 == 0 else 0, '1': 2 if index % 2 else 0})
        self.now += VOTE_MS
        self.client.portal.call(game_server._coordinator(room).execute, CatchUpDeadline())
        return [self.until(socket, 'question', index + 1) for socket in (h, g)]

    def test_answer_timeout_records_no_answer_and_keeps_the_run_funded(self):
        host, guest, code, room = self.open_room()
        router = SyntheticRouter()
        router.app = SimpleNamespace(session_state=RoomAnswers(code))
        calls = []
        with patch('httpx.Client', side_effect=lambda **kw: HTTPClient(
                transport=httpx.MockTransport(self.provider(router, 'research', calls)))):
            with self.client.websocket_connect(f'/ws/{code}') as h, \
                 self.client.websocket_connect(f'/ws/{code}') as g:
                for socket, identity in ((h, host), (g, guest)):
                    socket.send_json({'type': 'hello', 'token': identity['player_token']})
                    self.until(socket, 'lobby')
                self.prepare(h, g, 8)
                h.send_json({'type': 'start', 'plan_id': room.research_plan.id, 'question_budget': 8})
                self.vote_and_ask(h, g, room, 0)
                # Let the answer deadline pass without a submission.
                self.now = room.answer_deadline_ms + 1
                self.client.portal.call(game_server._coordinator(room).execute, CatchUpDeadline())
                states = [self.until(socket, 'voting', 2) for socket in (h, g)]
                self.assertTrue(states[0]['turns'][0]['timed_out'])
                self.assertIsNone(states[0]['turns'][0]['answer'])
                self.assertEqual(states[0]['turns'], states[1]['turns'])
                # The timeout is a recorded turn, not a lost answer or a refund:
                # the run advances to the next question with the turn retained.
                self.assertEqual(len(states[0]['turns']), 2)
                self.assertEqual(room.phase, 'voting')
        used = ProviderAllowance(run_scope(room.run_id), room.owner_account_id).snapshot()['used']
        self.assertGreater(used, 0)

    def test_direct_and_saved_recovery_keep_the_answer_and_charge_once(self):
        host, guest, code, room = self.open_room()
        router = SyntheticRouter()
        router.app = SimpleNamespace(session_state=RoomAnswers(code))
        calls = []
        with patch('httpx.Client', side_effect=lambda **kw: HTTPClient(
                transport=httpx.MockTransport(self.provider(router, 'research', calls)))):
            with self.client.websocket_connect(f'/ws/{code}') as h, \
                 self.client.websocket_connect(f'/ws/{code}') as g:
                for socket, identity in ((h, host), (g, guest)):
                    socket.send_json({'type': 'hello', 'token': identity['player_token']})
                    self.until(socket, 'lobby')
                self.prepare(h, g, 8)
                h.send_json({'type': 'start', 'plan_id': room.research_plan.id, 'question_budget': 8})
                self.vote_and_ask(h, g, room, 0)
                # A failed interpretation keeps the accepted input for recovery.
                router.fail_name = 'CombinedSubmissionDraft'
                h.send_json({'type': 'submit_answer', 'turn': 0, 'answer': 'We will limit the claim.'})
                failed = self.until(h, 'interpretation_retry')
                # A failed interpretation does not accept the answer; the private
                # input is retained for recovery instead.
                self.assertIsNone(failed['turns'][0]['answer'])
                self.assertEqual(failed['my_pending_submission'], 'We will limit the claim.')
                # Saved recovery reuses the retained input without retyping.
                h.send_json({'type': 'use_pending_as_answer'})
                recovered = self.until(h, 'voting', 2)
                self.assertEqual(recovered['turns'][0]['answer'], 'We will limit the claim.')
                self.assertIsNone(recovered['my_pending_submission'])
                # A direct answer bypasses interpretation and still advances once.
                self.vote_and_ask(h, g, room, 1)
                g.send_json({'type': 'submit_direct_answer', 'turn': 1, 'answer': 'A documented baseline.'})
                direct = self.until(g, 'voting', 3)
                self.assertEqual(direct['turns'][1]['answer'], 'A documented baseline.')
                self.assertEqual(len(direct['turns']), 3)
        overview = account_store.account_overview(self._offline_credentials[2]['id'])
        record = next(run for run in overview['runs'] if run['id'] == room.run_id)
        self.assertEqual(record['status'], 'charged')
        self.assertEqual(record['cost'], 0)

    def test_host_ending_and_restart_do_not_duplicate_charge_or_history(self):
        host, guest, code, room = self.open_room()
        router = SyntheticRouter()
        router.app = SimpleNamespace(session_state=RoomAnswers(code))
        calls = []
        with patch('httpx.Client', side_effect=lambda **kw: HTTPClient(
                transport=httpx.MockTransport(self.provider(router, 'research', calls)))):
            with self.client.websocket_connect(f'/ws/{code}') as h, \
                 self.client.websocket_connect(f'/ws/{code}') as g:
                for socket, identity in ((h, host), (g, guest)):
                    socket.send_json({'type': 'hello', 'token': identity['player_token']})
                    self.until(socket, 'lobby')
                self.prepare(h, g, 8)
                h.send_json({'type': 'start', 'plan_id': room.research_plan.id, 'question_budget': 8})
                self.vote_and_ask(h, g, room, 0)
                h.send_json({'type': 'submit_answer', 'turn': 0, 'answer': 'We will limit the claim.'})
                self.until(h, 'voting', 2)
                first_run = room.run_id
                h.send_json({'type': 'end_defense'})
                ended = [self.until(socket, 'complete', 2, feedback_status='ready') for socket in (h, g)]
                self.assertEqual(ended[0]['turns'], ended[1]['turns'])
                # The answered turn plus the question that was already asked.
                self.assertEqual(len(ended[0]['turns']), 2)
                self.assertEqual(ended[0]['turns'][0]['answer'], 'We will limit the claim.')
                # Restarting begins a new run in the same room.
                h.send_json({'type': 'restart', 'confirm_cost': True})
                restarted = self.until(h, 'generating')
                self.assertNotEqual(room.run_id, first_run)
                self.assertEqual(restarted['turns'], [])
        overview = account_store.account_overview(self._offline_credentials[2]['id'])
        runs = [run for run in overview['runs'] if run['id'] in {first_run, room.run_id}]
        self.assertEqual(len(runs), 2)
        self.assertTrue(all(run['status'] == 'charged' for run in runs))

    def test_free_tier_completes_without_upgrading_or_charging(self):
        self.enterContext(patch.dict('os.environ', {'OPENROUTER_FREE_PER_MINUTE': '1000'}))
        host, guest, code, room = self.open_room(tier='free')
        router = SyntheticRouter()
        router.app = SimpleNamespace(session_state=RoomAnswers(code))
        calls = []

        def provider(request):
            response = self.provider(router, 'research', calls)(request)
            # The synthetic upstream supplies an explicit zero-dollar receipt.
            return httpx.Response(response.status_code,
                                  content=response.content.replace(b'0.0005', b'0.0'))

        with patch('httpx.Client', side_effect=lambda **kw: HTTPClient(
                transport=httpx.MockTransport(provider))):
            with self.client.websocket_connect(f'/ws/{code}') as h, \
                 self.client.websocket_connect(f'/ws/{code}') as g:
                for socket, identity in ((h, host), (g, guest)):
                    socket.send_json({'type': 'hello', 'token': identity['player_token']})
                    state = self.until(socket, 'lobby')
                    self.assertEqual(state['practice_tier'], 'free')
                self.prepare(h, g, 4)
                h.send_json({'type': 'start', 'plan_id': room.research_plan.id, 'question_budget': 4})
                for index in range(4):
                    self.vote_and_ask(h, g, room, index)
                    speaker = h if index % 2 == 0 else g
                    speaker.send_json({'type': 'submit_answer', 'turn': index,
                                       'answer': f'We will limit claim {index + 1}.'})
                final = [self.until(socket, 'complete', 4, feedback_status='ready') for socket in (h, g)]
                self.assertEqual(final[0]['turns'], final[1]['turns'])
                self.assertEqual(final[0]['coaching_progress']['completion_status'], 'ready')
                # Free stays Free: the tier never upgrades to a paid route.
                self.assertEqual(room.practice_tier, 'free')
                self.assertEqual(ProviderAllowance(run_scope(room.run_id),
                                                   room.owner_account_id).policy()['tier'], 'free')


if __name__ == '__main__':
    unittest.main()

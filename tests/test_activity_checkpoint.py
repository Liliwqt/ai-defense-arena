"""Complete two-client activity defenses; real provider adapters, synthetic HTTP."""
import json
from threading import Event
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import httpx

from backend import game_server
from backend.rooms.commands import CatchUpDeadline
from tests import test_research_coverage as coverage
from tests.test_openrouter_checkpoint import RoomAnswers
from tests.test_openrouter_streamlit import SyntheticRouter
from tests.test_openrouter_questions import HTTPClient
from tests.test_research_plan import PAPER


class ActivityCheckpointTests(unittest.TestCase):
    setUp = coverage.CoverageProtocolTests.setUp
    until = coverage.CoverageProtocolTests.until

    def test_standard_research_complete_activity_defense(self):
        self.complete_defense('research', 'standard')

    def test_standard_mixed_complete_activity_defense(self):
        self.complete_defense('mixed', 'standard')

    def test_free_research_complete_activity_defense(self):
        self.complete_defense('research', 'free')

    def test_free_mixed_complete_activity_defense(self):
        self.complete_defense('mixed', 'free')

    def complete_defense(self, mode, tier):
        self.enterContext(patch.dict('os.environ', {'OPENROUTER_FREE_PER_MINUTE': '1000',
            'OPENROUTER_FREE_DAILY_REQUESTS': '1000', 'OPENROUTER_FREE_OWNER_DAILY_REQUESTS': '1000'}))
        router = SyntheticRouter(mixed=mode == 'mixed')
        router.usage = {'cost': 0} if tier == 'free' else None
        holds = []
        self.observed = []  # Public synthetic snapshots, available for the local visual handoff.

        def hold(schema):
            release = Event()
            self.addCleanup(release.set)
            holds.append((schema, release))
            return release

        def provider(request):
            name = json.loads(request.content)['response_format']['json_schema']['name']
            if holds and name == holds[0][0]:
                _, release = holds.pop(0)
                if not release.wait(10):
                    raise AssertionError('Synthetic provider stage was not released')
            return router(request)

        uploads = [('research_files', ('study.md', PAPER.encode(), 'text/markdown'))]
        if mode == 'mixed':
            uploads.append(('files', ('queue.py', b'queue = []\n', 'text/x-python')))
        response = self.client.post('/api/rooms', data={'host_name': 'Host',
            'defense_type': mode, 'research_stage': 'proposal', 'practice_tier': tier}, files=uploads)
        self.assertEqual(response.status_code, 201, response.text)
        host = response.json(); code = host['room_code']
        guest = self.client.post(f'/api/rooms/{code}/join', json={'name': 'Sam'}).json()
        room = game_server.rooms[code]
        router.app = SimpleNamespace(session_state=RoomAnswers(code))
        interaction = 'CombinedSubmissionDraft' if tier == 'standard' else 'SubmissionDraft'
        with patch('httpx.Client', side_effect=lambda **kw: HTTPClient(transport=httpx.MockTransport(provider))):
            with self.client.websocket_connect(f'/ws/{code}') as h, self.client.websocket_connect(f'/ws/{code}') as g:
                sockets = (h, g)

                def shared(phase=None, *, active=False, **conditions):
                    states = []
                    for socket in sockets:
                        for _ in range(60):
                            state = self.until(socket, phase, **conditions)
                            operation = state.get('operation')
                            coaching_running = not operation or operation['kind'] != 'coaching' or any(
                                section['status'] == 'generating' for section in (state.get('coaching_progress') or {}).get('sections', []))
                            if not active or operation and coaching_running:
                                break
                        else:
                            self.fail('No current operation was published')
                        states.append(state)
                    self.assertEqual(states[0]['panelist_activity'], states[1]['panelist_activity'])
                    if active:
                        self.assertIsNotNone(states[0]['panelist_activity'])
                        self.assertEqual(states[0]['panelist_activity']['operation_id'], states[0]['operation']['id'])
                        self.assertEqual(states[0]['panelist_activity']['view_id'], states[0]['defense_view_id'])
                        self.assertNotIn('SECRET TEAM CHAT', json.dumps(states[0]['panelist_activity']))
                    else:
                        self.assertIsNone(states[0]['panelist_activity'])
                    self.observed.append(states)
                    return states[0]

                for socket, identity in zip(sockets, (host, guest)):
                    socket.send_json({'type': 'hello', 'token': identity['player_token']})
                    self.until(socket, 'lobby')
                release = hold('ResearchPlanDraft')
                h.send_json({'type': 'prepare_research_plan'})
                mapping = shared('lobby', active=True, research_planning_status='planning')
                self.assertEqual(mapping['panelist_activity']['context'], 'study.md')
                release.set()
                prepared = shared('lobby', research_planning_status='ready')
                plan_id = prepared['research_plan']['id']
                h.send_json({'type': 'approve_research_plan', 'plan_id': plan_id, 'question_budget': 4, 'confirm_profile': True})
                shared('lobby', research_plan_approved=True)
                release = hold('PlanDraft')
                h.send_json({'type': 'start', 'plan_id': plan_id, 'question_budget': 4})
                opening = shared('generating', active=True)
                self.assertIsNone(opening['panelist_activity']['context'])
                release.set()
                for index in range(4):
                    voting = shared('voting', count=index+1)
                    speaker = sockets[index % 2]
                    for socket in sockets:
                        socket.send_json({'type': 'cast_vote', 'seat': index % 2})
                    self.until(h, 'voting', vote_counts={'0': 2 if index % 2 == 0 else 0, '1': 2 if index % 2 else 0})
                    self.now = voting['vote_deadline_ms'] + 1
                    self.client.portal.call(game_server._coordinator(room).execute, CatchUpDeadline())
                    current = shared('question', count=index+1)
                    topic = next(topic['title'] for topic in prepared['research_plan']['topics'] if topic['id'] == current['turns'][-1]['topic_id'])
                    if index == 0:
                        h.send_json({'type': 'send_chat', 'text': 'SECRET TEAM CHAT'})
                        for decision, text, result in (
                            ({'action': 'clarify', 'clarification': 'Explain your planned comparison.', 'probe': None}, 'Please explain.', 'question'),
                            ({'action': 'probe', 'clarification': None, 'probe': {'request': 'Which baseline supports that?', 'references': []}}, 'We will compare pilot waiting times.', 'probe')):
                            router.decisions = [decision]
                            release = hold(interaction)
                            command = {'type': 'submit_answer', 'turn': index, 'answer': text}
                            speaker.send_json(command)
                            reviewing = shared('interpreting', active=True)
                            self.assertEqual(reviewing['panelist_activity']['context'], topic)
                            self.assertNotIn(text, json.dumps(reviewing['panelist_activity']))
                            release.set()
                            current = shared(result, count=1)
                        router.fail_name = interaction
                        speaker.send_json({'type': 'submit_probe_reply', 'turn': index,
                            'probe_id': current['turns'][-1]['probe']['id'], 'answer': 'The planned baseline record.'})
                        failed = shared('interpretation_retry')
                        self.assertEqual(failed['turns'][0]['answer'], 'We will compare pilot waiting times.')
                        release = hold(interaction)
                        h.send_json({'type': 'retry_interpretation'})
                        reviewing = shared('interpreting', active=True)
                        self.assertTrue(reviewing['operation']['retrying'])
                        self.now += 2000
                        with self.client.websocket_connect(f'/ws/{code}') as restored:
                            restored.send_json({'type': 'hello', 'token': guest['player_token']})
                            state = self.until(restored, 'interpreting')
                            self.assertEqual(state['panelist_activity'], reviewing['panelist_activity'])
                            self.assertEqual(state['operation']['started_at_ms'], reviewing['operation']['started_at_ms'])
                        release.set()
                        continue
                    if index == 1:
                        router.fail_name = 'QuestionDraft'
                    if index == 3:
                        router.fail_turns = [3]
                        release_overview = hold('CoachingDraft')
                    speaker.send_json({'type': 'submit_answer', 'turn': index, 'answer': 'We will limit our claim to the campus pilot.'})
                    if index == 1:
                        failed = shared('retry')
                        self.assertEqual(failed['turns'][index]['answer'], 'We will limit our claim to the campus pilot.')
                        release = hold('QuestionDraft')
                        h.send_json({'type': 'retry'})
                        writing_retry = shared('generating', active=True)
                        self.assertTrue(writing_retry['operation']['retrying'])
                        release.set()
                overview = shared('complete', active=True, feedback_status='generating')
                self.assertEqual(overview['panelist_activity']['context'], 'Team overview')
                release_overview.set()
                partial = shared('complete', feedback_status='failed')
                self.assertEqual(partial['coaching_progress']['cards_ready'], 3)
                before = partial['feedback']['answer_cards']
                closing_deadline = partial['closing_deadline_ms']
                release = hold('ResearchCoachingDraft')
                h.send_json({'type': 'retry_coaching'})
                retry = shared('complete', active=True, feedback_status='generating')
                self.assertEqual(retry['panelist_activity']['context'], 'Question 4')
                self.assertEqual(retry['coaching_progress']['cards_ready'], 3)
                release.set()
                final = shared('complete', feedback_status='ready')
                self.assertEqual(final['coaching_progress']['completion_status'], 'ready')
                self.assertEqual(final['coaching_progress']['cards_ready'], 4)
                self.assertEqual(final['feedback']['answer_cards'][:3], before)
                self.assertEqual(final['closing_deadline_ms'], closing_deadline)
                self.assertEqual(final['turns'][0]['probe']['reply'], 'The planned baseline record.')
                self.assertEqual(len({turn['panelist'] for turn in final['turns']}), 4)
                self.assertNotIn('panelist_activity', json.dumps(final['feedback']))
                self.assertNotIn('panelist_activity', json.dumps(final['turns']))
                self.assertFalse(holds, 'Every expected provider stage ran')
                names = [body['response_format']['json_schema']['name'] for body in router.calls]
                self.assertEqual(names.count('ResearchPlanDraft'), 1)
                self.assertEqual(names.count('QuestionDraft'), 5)
                self.assertEqual(names.count(interaction), 7)
                self.assertEqual(sum('CoachingDraft' in name for name in names), 4)
                self.assertTrue(all('SECRET TEAM CHAT' not in json.dumps(body) for body in router.calls))

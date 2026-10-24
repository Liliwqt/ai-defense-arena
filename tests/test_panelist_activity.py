"""Editor notes through authenticated room HTTP/WebSockets; AI/time mocked."""
import json
from threading import Event
import unittest
from unittest.mock import patch

from backend import game_server
from backend.openrouter_questions import SEPARATE_PLANNING
from backend.question_generator import QuestionGenerationError, SubmissionDecision
from backend.rooms import planning, questions, submissions
from backend.rooms.commands import CatchUpDeadline
from tests import test_research_coverage as fixtures


class PanelistActivityTests(unittest.TestCase):
    setUp = fixtures.CoverageProtocolTests.setUp
    until = fixtures.CoverageProtocolTests.until

    def active(self, socket, phase):
        for _ in range(60):
            state = self.until(socket, phase)
            if state.get('operation'):
                return state
        self.fail('No current operation published')

    def test_shared_opening_and_review_context_clears_on_results(self):
        self.shared_flow('research', 'standard')

    def test_free_mixed_members_get_the_same_safe_activity(self):
        self.shared_flow('mixed', 'free')

    def test_failed_question_retires_activity_and_manual_retry_keeps_the_answer(self):
        self.shared_flow('research', 'standard', fail_next=True)

    def shared_flow(self, mode, tier, *, fail_next=False):
        expected_failure = fail_next
        release_question, release_review = Event(), Event()
        self.addCleanup(release_question.set)
        self.addCleanup(release_review.set)
        prepared = fixtures.plan(4)

        def ask(*args, **kwargs):
            nonlocal fail_next
            if not release_question.wait(10):
                raise AssertionError('Synthetic question was not released')
            if kwargs.get('history') and fail_next:
                fail_next = False
                raise QuestionGenerationError('Synthetic question unavailable')
            return fixtures.mocked_move(*args, **kwargs)

        def review(*args, **kwargs):
            if not release_review.wait(10):
                raise AssertionError('Synthetic review was not released')
            return SubmissionDecision('answer')

        with patch.object(planning, 'generate_research_plan', return_value=prepared), \
             patch.object(questions, 'generate_research_move', side_effect=ask) as ai, \
             patch.object(submissions, 'interpret_submission', side_effect=review):
            uploads = [('research_files', ('paper.md', fixtures.PAPER.encode(), 'text/markdown'))]
            if mode == 'mixed':
                uploads.append(('files', ('queue.py', b'queue = []', 'text/x-python')))
            response = self.client.post('/api/rooms', data={'host_name': 'Host', 'defense_type': mode, 'practice_tier': tier}, files=uploads)
            self.assertEqual(response.status_code, 201, response.text)
            host = response.json(); code = host['room_code']
            guest = self.client.post(f'/api/rooms/{code}/join', json={'name': 'Sam'}).json()
            try:
                with self.client.websocket_connect(f'/ws/{code}') as h, self.client.websocket_connect(f'/ws/{code}') as g:
                    for ws, player in ((h, host), (g, guest)):
                        ws.send_json({'type': 'hello', 'token': player['player_token']}); self.until(ws, 'lobby')
                    h.send_json({'type': 'prepare_research_plan'})
                    for ws in (h, g): self.until(ws, research_planning_status='ready')
                    h.send_json({'type': 'approve_research_plan', 'plan_id': prepared.id, 'question_budget': 4, 'confirm_profile': True})
                    for ws in (h, g): self.until(ws, research_plan_approved=True)
                    h.send_json({'type': 'start', 'plan_id': prepared.id, 'question_budget': 4})
                    opening = [self.active(ws, 'generating') for ws in (h, g)]
                    self.assertIsNotNone(opening[0].get('panelist_activity'))
                    self.assertEqual(opening[0]['panelist_activity'], opening[1]['panelist_activity'])
                    self.assertIsNone(opening[0]['panelist_activity']['context'], 'No topic has been asked yet')
                    release_question.set()
                    ready = [self.until(ws, 'voting') for ws in (h, g)]
                    self.assertIsNone(ready[0]['panelist_activity'])
                    room = game_server.rooms[code]
                    room.planning_contract = SEPARATE_PLANNING
                    h.send_json({'type': 'cast_vote', 'seat': 0})
                    self.until(h, 'voting', my_vote=0)
                    self.now = ready[0]['vote_deadline_ms'] + 1
                    self.client.portal.call(game_server._coordinator(room).execute, CatchUpDeadline())
                    for ws in (h, g): self.until(ws, 'question')
                    h.send_json({'type': 'submit_answer', 'turn': 0, 'answer': 'We will compare pilot waiting times.'})
                    reviewing = [self.active(ws, 'interpreting') for ws in (h, g)]
                    activity = reviewing[0]['panelist_activity']
                    self.assertEqual(activity, reviewing[1]['panelist_activity'])
                    self.assertEqual(activity['context'], 'Pilot decision 1')
                    self.assertEqual(activity['reviewer'], 'Methodology Reviewer')
                    self.now += 2000
                    with self.client.websocket_connect(f'/ws/{code}') as restored:
                        restored.send_json({'type': 'hello', 'token': guest['player_token']})
                        current = self.until(restored, 'interpreting')
                        self.assertEqual(current['panelist_activity'], activity)
                        self.assertEqual(current['operation']['started_at_ms'], reviewing[0]['operation']['started_at_ms'])
                    with self.client.websocket_connect(f'/ws/{code}') as invalid:
                        invalid.send_json({'type': 'hello', 'token': 'not-a-room-member'})
                        rejected = invalid.receive_json()
                        self.assertEqual(rejected['type'], 'error')
                        self.assertNotIn('state', rejected)
                    self.assertNotIn('Pilot decision 2', json.dumps(activity))
                    self.assertNotIn('compare pilot waiting', json.dumps(activity))
                    self.assertIsNone(reviewing[0]['turns'][0]['answer'])
                    release_review.set()
                    if expected_failure:
                        for ws in (h, g):
                            failed = self.until(ws, 'retry')
                            self.assertIsNone(failed['panelist_activity'])
                            self.assertEqual(failed['turns'][0]['answer'], 'We will compare pilot waiting times.')
                        h.send_json({'type': 'retry'})
                    done = [self.until(ws, 'voting', count=2) for ws in (h, g)]
                    self.assertIsNone(done[0]['panelist_activity'])
                    self.assertEqual(done[0]['turns'][0]['answer'], 'We will compare pilot waiting times.')
                    self.assertNotIn('panelist_activity', json.dumps(done[0]['turns']))
                    self.assertEqual(ai.call_count, 3 if expected_failure else 2)
            finally:
                release_question.set(); release_review.set()

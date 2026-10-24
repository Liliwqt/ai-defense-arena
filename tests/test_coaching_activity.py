"""Progressive coaching activity through authenticated rooms; providers mocked."""
import json
from threading import Event
import unittest
from unittest.mock import patch

from backend import game_server
from backend.openrouter_questions import SEPARATE_PLANNING
from backend.question_generator import CoachingReport, QuestionGenerationError, SubmissionDecision
from backend.rooms import coaching, planning, questions, submissions
from backend.rooms.commands import CatchUpDeadline
from tests import test_research_coverage as fixtures
from tests.research_coaching_fixtures import with_cards, scope_options


class CoachingActivityTests(unittest.TestCase):
    setUp = fixtures.CoverageProtocolTests.setUp
    until = fixtures.CoverageProtocolTests.until

    def section(self, socket, section_id):
        for _ in range(80):
            state = self.until(socket, 'complete')
            sections = (state.get('coaching_progress') or {}).get('sections', [])
            running = next((section for section in sections if section['status'] == 'generating'), None)
            if not running and (state.get('operation') or {}).get('stage') != 'saving_completion':
                self.assertIsNone(state['panelist_activity'], 'A finished section must retire its highlight')
            if running and running['id'] == section_id:
                return state
        self.fail('Missing active coaching section')

    def test_standard_research_members_see_only_running_coaching_with_ready_cards_preserved(self):
        self.report_flow('research', 'standard')

    def test_free_mixed_failed_section_retry_preserves_ready_cards_and_does_not_replay_closing(self):
        self.report_flow('mixed', 'free', fail_last=True)

    def report_flow(self, mode, tier, *, fail_last=False):
        overview, first, last, retry = (Event() for _ in range(4))
        for gate in (overview, first, last, retry): self.addCleanup(gate.set)
        prepared = fixtures.plan(4)
        calls = []

        def report(files, history, *args, **kwargs):
            turns = kwargs.get('section_turns')
            calls.append(turns)
            attempt = calls.count(turns)
            gate = overview if turns is None else first if turns == (0, 1, 2) else last if attempt == 1 else retry
            if not gate.wait(10): raise AssertionError('Synthetic coaching section was not released')
            if fail_last and turns == (3,) and attempt == 1:
                raise QuestionGenerationError('Synthetic section unavailable')
            return with_cards(CoachingReport('The team discussed the pilot scope.', [], [], 'Practice the limits.', closing='Review those limits.'),
                history, **scope_options(kwargs))

        with patch.object(planning, 'generate_research_plan', return_value=prepared), \
             patch.object(questions, 'generate_research_move', side_effect=fixtures.mocked_move) as asks, \
             patch.object(submissions, 'interpret_submission', return_value=SubmissionDecision('answer')), \
             patch.object(coaching, 'generate_coaching_report', side_effect=report):
            uploads = [('research_files', ('paper.md', fixtures.PAPER.encode(), 'text/markdown'))]
            if mode == 'mixed': uploads.append(('files', ('queue.py', b'queue = []\n' * 12, 'text/x-python')))
            response = self.client.post('/api/rooms', data={'host_name': 'Host', 'defense_type': mode, 'practice_tier': tier}, files=uploads)
            self.assertEqual(response.status_code, 201, response.text)
            host = response.json(); code = host['room_code']
            guest = self.client.post(f'/api/rooms/{code}/join', json={'name': 'Sam'}).json()
            try:
                with self.client.websocket_connect(f'/ws/{code}') as h, self.client.websocket_connect(f'/ws/{code}') as g:
                    for socket, player in ((h, host), (g, guest)):
                        socket.send_json({'type': 'hello', 'token': player['player_token']}); self.until(socket, 'lobby')
                    h.send_json({'type': 'prepare_research_plan'})
                    for socket in (h, g): self.until(socket, research_planning_status='ready')
                    h.send_json({'type': 'approve_research_plan', 'plan_id': prepared.id, 'question_budget': 4, 'confirm_profile': True})
                    for socket in (h, g): self.until(socket, research_plan_approved=True)
                    h.send_json({'type': 'start', 'plan_id': prepared.id, 'question_budget': 4})
                    room = game_server.rooms[code]
                    for turn in range(4):
                        ready = [self.until(socket, 'voting', count=turn+1) for socket in (h, g)]
                        room.planning_contract = SEPARATE_PLANNING
                        h.send_json({'type': 'cast_vote', 'seat': 0}); self.until(h, 'voting', my_vote=0)
                        self.now = ready[0]['vote_deadline_ms'] + 1
                        self.client.portal.call(game_server._coordinator(room).execute, CatchUpDeadline())
                        for socket in (h, g): self.until(socket, 'question')
                        h.send_json({'type': 'submit_answer', 'turn': turn, 'answer': 'We will limit the claim to this pilot.'})
                    starting = [self.section(socket, 'overview') for socket in (h, g)]
                    self.assertEqual(starting[0]['panelist_activity'], starting[1]['panelist_activity'])
                    self.assertIsNotNone(starting[0]['panelist_activity'])
                    self.assertEqual(starting[0]['panelist_activity']['context'], 'Team overview')
                    overview.set()
                    first_states = [self.section(socket, 'answers-0') for socket in (h, g)]
                    activity = first_states[0]['panelist_activity']
                    self.assertEqual(activity, first_states[1]['panelist_activity'])
                    self.assertEqual(activity['context'], 'Questions 1, 2, 3')
                    self.assertEqual(activity['job_id'], first_states[0]['coaching_progress']['job_id'])
                    self.assertEqual(activity['section_id'], 'answers-0')
                    self.assertEqual(first_states[0]['feedback']['summary'], 'The team discussed the pilot scope.')
                    closing_deadline = first_states[0]['closing_deadline_ms']
                    first.set()
                    last_states = [self.section(socket, 'answers-3') for socket in (h, g)]
                    self.assertEqual(last_states[0]['panelist_activity']['context'], 'Question 4')
                    self.assertEqual(last_states[0]['coaching_progress']['cards_ready'], 3)
                    self.assertEqual(len(last_states[0]['feedback']['answer_cards']), 3)
                    self.assertNotIn('The team discussed', json.dumps(last_states[0]['panelist_activity']))
                    with self.client.websocket_connect(f'/ws/{code}') as restored:
                        restored.send_json({'type': 'hello', 'token': guest['player_token']})
                        current = self.section(restored, 'answers-3')
                        self.assertEqual(current['panelist_activity'], last_states[0]['panelist_activity'])
                        self.assertEqual(current['operation']['started_at_ms'], last_states[0]['operation']['started_at_ms'])
                    last.set()
                    if fail_last:
                        failed = [self.until(socket, 'complete', feedback_status='failed') for socket in (h, g)]
                        self.assertIsNone(failed[0]['panelist_activity'])
                        self.assertEqual(failed[0]['coaching_progress']['cards_ready'], 3)
                        h.send_json({'type': 'retry_coaching'})
                        for socket in (h, g): self.section(socket, 'answers-3')
                        retry.set()
                    done = [self.until(socket, 'complete', feedback_status='ready') for socket in (h, g)]
                    for state in done:
                        self.assertIsNone(state['panelist_activity'])
                        self.assertEqual(state['coaching_progress']['cards_ready'], 4)
                        self.assertEqual(state['coaching_progress']['completion_status'], 'ready')
                        self.assertEqual(state['closing_deadline_ms'], closing_deadline)
                        self.assertNotIn('panelist_activity', json.dumps(state['feedback']))
                    self.assertEqual(calls, [None, (0, 1, 2), (3,)] + ([(3,)] if fail_last else []))
                    self.assertEqual(asks.call_count, 5)
            finally:
                for gate in (overview, first, last, retry): gate.set()

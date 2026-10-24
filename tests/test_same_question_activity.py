"""Same-question activity through authenticated rooms, with AI and clock mocked."""
import json
from threading import Event
import unittest
from unittest.mock import patch

from backend import game_server
from backend.openrouter_questions import SEPARATE_PLANNING
from backend.question_generator import ProbeRequest, QuestionGenerationError, SubmissionDecision
from backend.rooms import planning, questions, submissions
from backend.rooms.commands import CatchUpDeadline
from backend.timed_turn import PROBE_MS
from tests import test_research_coverage as fixtures
from tests import test_panelist_activity as activity_fixtures


class SameQuestionActivityTests(unittest.TestCase):
    setUp = fixtures.CoverageProtocolTests.setUp
    until = fixtures.CoverageProtocolTests.until
    active = activity_fixtures.PanelistActivityTests.active

    def test_standard_research_clarification_probe_and_reply_have_current_shared_activity(self):
        self.exchange('research', 'standard')

    def test_free_mixed_probe_clarification_and_failed_reply_retry_keep_original_answer(self):
        self.exchange('mixed', 'free', probe_clarification=True, fail_reply=True)

    def test_restart_during_probe_review_cannot_attach_late_activity_or_reply_to_the_new_run(self):
        self.exchange('research', 'standard', restart_reply=True)

    def exchange(self, mode, tier, *, probe_clarification=False, fail_reply=False, restart_reply=False):
        original = 'We will compare pilot waiting times.'
        final_reply = 'We will use the pilot attendance list.'
        probe = SubmissionDecision('probe', probe=ProbeRequest('Which list supports that decision?'))
        if probe_clarification:
            messages = [original, 'What list do you mean?', final_reply]
            decisions = [probe, SubmissionDecision('clarify', 'Name the source list you plan to use.')]
        else:
            messages = ['What does that decision mean?', original, final_reply]
            decisions = [SubmissionDecision('clarify', 'Explain which decision you will use.'), probe]
        decisions.append(QuestionGenerationError('Synthetic review unavailable') if fail_reply else SubmissionDecision('answer'))
        if fail_reply:
            decisions.append(SubmissionDecision('answer'))
        gates = [Event() for _ in decisions]
        for gate in gates:
            self.addCleanup(gate.set)
        received = []
        last_finished = Event()

        def review(*args, **kwargs):
            index = len(received)
            received.append(kwargs['submission'])
            try:
                if not gates[index].wait(10):
                    raise AssertionError('Synthetic review was not released')
                decision = decisions[index]
                if isinstance(decision, Exception):
                    raise decision
                return decision
            finally:
                if index == len(messages) - 1:
                    last_finished.set()

        prepared = fixtures.plan(4)
        with patch.object(planning, 'generate_research_plan', return_value=prepared), \
             patch.object(questions, 'generate_research_move', side_effect=fixtures.mocked_move) as asks, \
             patch.object(submissions, 'interpret_submission', side_effect=review) as reviews:
            uploads = [('research_files', ('paper.md', fixtures.PAPER.encode(), 'text/markdown'))]
            if mode == 'mixed':
                uploads.append(('files', ('queue.py', b'queue = []', 'text/x-python')))
            response = self.client.post('/api/rooms', data={'host_name': 'Host', 'defense_type': mode, 'practice_tier': tier}, files=uploads)
            self.assertEqual(response.status_code, 201, response.text)
            host = response.json(); code = host['room_code']
            guest = self.client.post(f'/api/rooms/{code}/join', json={'name': 'Sam'}).json()
            try:
                with self.client.websocket_connect(f'/ws/{code}') as h, self.client.websocket_connect(f'/ws/{code}') as g:
                    for socket, player in ((h, host), (g, guest)):
                        socket.send_json({'type': 'hello', 'token': player['player_token']})
                        self.until(socket, 'lobby')
                    h.send_json({'type': 'prepare_research_plan'})
                    for socket in (h, g): self.until(socket, research_planning_status='ready')
                    h.send_json({'type': 'approve_research_plan', 'plan_id': prepared.id, 'question_budget': 4, 'confirm_profile': True})
                    for socket in (h, g): self.until(socket, research_plan_approved=True)
                    h.send_json({'type': 'start', 'plan_id': prepared.id, 'question_budget': 4})
                    ready = [self.until(socket, 'voting') for socket in (h, g)]
                    room = game_server.rooms[code]
                    room.planning_contract = SEPARATE_PLANNING  # Existing mocked interaction seam.
                    h.send_json({'type': 'cast_vote', 'seat': 0})
                    self.until(h, 'voting', my_vote=0)
                    self.now = ready[0]['vote_deadline_ms'] + 1
                    self.client.portal.call(game_server._coordinator(room).execute, CatchUpDeadline())
                    current = [self.until(socket, 'question') for socket in (h, g)]
                    question = current[0]['turns'][0]['question']
                    probe_id = None
                    for index, text in enumerate(messages):
                        self.now += 1000
                        deadline = current[0]['answer_deadline_ms']
                        command = {'type': 'submit_probe_reply' if probe_id else 'submit_answer', 'turn': 0, 'answer': text}
                        if probe_id:
                            command['probe_id'] = probe_id
                        h.send_json(command)
                        reviewing = [self.active(socket, 'interpreting') for socket in (h, g)]
                        activity = reviewing[0]['panelist_activity']
                        self.assertIsNotNone(activity)
                        self.assertEqual(activity, reviewing[1]['panelist_activity'])
                        self.assertEqual(activity['context'], 'Pilot decision 1')
                        self.assertEqual(activity['reviewer'], 'Methodology Reviewer')
                        self.assertEqual(reviewing[0]['operation']['stage'], 'reviewing_reply' if probe_id else 'reviewing_answer')
                        self.assertEqual(len(reviewing[0]['turns']), 1)
                        self.assertEqual(reviewing[0]['turns'][0]['question'], question)
                        self.assertEqual(reviewing[0]['turns'][0]['answer'], original if probe_id else None)
                        self.assertNotIn(text, json.dumps(activity))
                        self.assertNotIn('Name the source', json.dumps(activity))
                        self.assertNotIn('Which list supports', json.dumps(activity))
                        if probe_id:
                            self.assertIsNone(reviewing[0]['turns'][0]['probe']['reply'])
                            with self.client.websocket_connect(f'/ws/{code}') as restored:
                                restored.send_json({'type': 'hello', 'token': guest['player_token']})
                                snapshot = self.until(restored, 'interpreting')
                                self.assertEqual(snapshot['panelist_activity'], activity)
                                self.assertEqual(snapshot['operation']['started_at_ms'], reviewing[0]['operation']['started_at_ms'])
                        self.now += 2000
                        if restart_reply and index == len(messages) - 1:
                            h.send_json({'type': 'restart'})
                            for socket in (h, g):
                                fresh = self.until(socket, 'voting', count=1)
                                self.assertNotEqual(fresh['defense_view_id'], activity['view_id'])
                                self.assertIsNone(fresh['panelist_activity'])
                                self.assertIsNone(fresh['turns'][0]['probe'])
                                self.assertIsNone(fresh['turns'][0]['answer'])
                            gates[index].set()
                            self.assertTrue(last_finished.wait(5), 'Retired review did not finish')
                            with self.client.websocket_connect(f'/ws/{code}') as restored:
                                restored.send_json({'type': 'hello', 'token': guest['player_token']})
                                fresh = self.until(restored, 'voting', count=1)
                                self.assertIsNone(fresh['panelist_activity'])
                                self.assertIsNone(fresh['turns'][0]['probe'])
                            self.assertEqual(asks.call_count, 2)
                            self.assertEqual(reviews.call_count, 3)
                            return
                        gates[index].set()
                        if index < len(messages) - 1:
                            current = [self.until(socket, 'probe' if probe_id or decisions[index].action == 'probe' else 'question') for socket in (h, g)]
                            for state in current:
                                self.assertIsNone(state['panelist_activity'])
                                self.assertEqual(len(state['turns']), 1)
                                self.assertEqual(state['turns'][0]['question'], question)
                            if decisions[index].action == 'probe':
                                probe_id = current[0]['turns'][0]['probe']['id']
                                self.assertEqual(current[0]['answer_deadline_ms'], self.now + PROBE_MS)
                            else:
                                self.assertEqual(current[0]['answer_deadline_ms'], deadline + 2000)
                            if probe_id:
                                self.assertEqual(current[0]['turns'][0]['probe']['id'], probe_id)
                                self.assertEqual(current[0]['turns'][0]['answer'], original)
                    if fail_reply:
                        failed = [self.until(socket, 'interpretation_retry') for socket in (h, g)]
                        self.assertIsNone(failed[0]['panelist_activity'])
                        self.assertEqual(failed[0]['my_pending_submission'], final_reply)
                        self.assertEqual(failed[0]['turns'][0]['answer'], original)
                        h.send_json({'type': 'retry_interpretation'})
                        for socket in (h, g):
                            retry = self.active(socket, 'interpreting')
                            self.assertEqual(retry['panelist_activity']['context'], 'Pilot decision 1')
                        gates[3].set()
                    done = [self.until(socket, 'voting', count=2) for socket in (h, g)]
                    for state in done:
                        self.assertIsNone(state['panelist_activity'])
                        self.assertEqual(state['turns'][0]['answer'], original)
                        self.assertEqual(state['turns'][0]['probe']['reply'], final_reply)
                        self.assertEqual(state['turns'][0]['probe']['status'], 'answered')
                        self.assertNotIn('panelist_activity', json.dumps(state['turns']))
                    self.assertEqual(asks.call_count, 2)
                    self.assertEqual(reviews.call_count, 4 if fail_reply else 3)
                    self.assertEqual(received[-1], final_reply)
            finally:
                for gate in gates: gate.set()

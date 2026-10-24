"""Mapping Editor notes at authenticated HTTP/WebSocket boundaries; AI mocked."""
import json
from threading import Event
import unittest
from unittest.mock import patch

from backend.research_plan import ResearchPlanProgress
from backend.question_generator import QuestionGenerationError
from backend.rooms import planning
from tests import test_research_coverage as fixtures


class MappingActivityTests(unittest.TestCase):
    setUp = fixtures.CoverageProtocolTests.setUp
    until = fixtures.CoverageProtocolTests.until

    def stage(self, socket, expected):
        for _ in range(60):
            state = self.until(socket, research_planning_status='planning')
            if (state.get('operation') or {}).get('stage') == expected:
                return state
        self.fail('Missing mapping stage')

    def test_members_share_only_accepted_upload_context_through_mapping_and_validation(self):
        self.shared_mapping('research', 'standard')

    def test_free_mixed_remap_failure_and_retry_keep_current_context_and_retained_map(self):
        self.shared_mapping('mixed', 'free', remap=True)

    def shared_mapping(self, mode, tier, *, remap=False):
        release_validation, release_result = Event(), Event()
        release_remap = Event()
        self.addCleanup(release_validation.set)
        self.addCleanup(release_result.set)
        self.addCleanup(release_remap.set)
        prepared = fixtures.plan(4)
        attempts = 0

        def map_paper(*args, on_progress, **kwargs):
            nonlocal attempts
            attempts += 1
            if attempts == 2:
                on_progress(ResearchPlanProgress('mapping', (prepared.topics[1],)))
                if not release_remap.wait(10):
                    raise AssertionError('Remap was not released')
                raise QuestionGenerationError('Synthetic mapping unavailable')
            if attempts == 3:
                return prepared  # Immediate completion must not leave old activity.
            on_progress(ResearchPlanProgress('mapping', (prepared.topics[0],)))
            if not release_validation.wait(10):
                raise AssertionError('Validation was not released')
            on_progress(ResearchPlanProgress('validating', prepared.topics))
            if not release_result.wait(10):
                raise AssertionError('Map result was not released')
            return prepared

        with patch.object(planning, 'generate_research_plan', side_effect=map_paper) as ai:
            uploads = [('research_files', ('paper.md', fixtures.PAPER.encode(), 'text/markdown'))]
            if mode == 'mixed':
                uploads.append(('files', ('queue.py', b'queue = []', 'text/x-python')))
            response = self.client.post('/api/rooms', data={'host_name': 'Host', 'defense_type': mode, 'practice_tier': tier}, files=uploads)
            self.assertEqual(response.status_code, 201, response.text)
            host = response.json(); code = host['room_code']
            guest = self.client.post(f'/api/rooms/{code}/join', json={'name': 'Sam'}).json()
            with self.client.websocket_connect(f'/ws/{code}') as h, self.client.websocket_connect(f'/ws/{code}') as g:
                h.send_json({'type': 'hello', 'token': host['player_token']})
                self.until(h, 'lobby')
                g.send_json({'type': 'hello', 'token': guest['player_token']})
                self.until(g, 'lobby')
                self.assertEqual(ai.call_count, 0)
                h.send_json({'type': 'prepare_research_plan'})
                states = [self.stage(socket, 'mapping') for socket in (h, g)]
                activity = states[0]['panelist_activity']
                self.assertIsNotNone(activity)
                self.assertEqual(activity, states[1]['panelist_activity'])
                self.assertEqual(activity, {'operation_id': states[0]['operation']['id'],
                    'view_id': states[0]['defense_view_id'], 'reviewer': None, 'context': 'paper.md'})
                self.assertNotIn('Pilot decision', json.dumps(activity))
                self.assertEqual(len(states[0]['research_plan_progress']['topics']), 1)
                with self.client.websocket_connect(f'/ws/{code}') as restored:
                    restored.send_json({'type': 'hello', 'token': guest['player_token']})
                    current = self.stage(restored, 'mapping')
                    self.assertEqual(current['panelist_activity'], activity)
                    self.assertEqual(current['operation']['started_at_ms'], states[0]['operation']['started_at_ms'])
                    self.assertEqual(ai.call_count, 1)
                with self.client.websocket_connect(f'/ws/{code}') as stranger:
                    stranger.send_json({'type': 'hello', 'token': 'invalid'})
                    self.assertEqual(stranger.receive_json()['type'], 'error')
                release_validation.set()
                checking = [self.stage(socket, 'validating') for socket in (h, g)]
                self.assertEqual(checking[0]['panelist_activity'], activity)
                self.assertEqual(checking[1]['panelist_activity'], activity)
                release_result.set()
                ready = [self.until(socket, research_planning_status='ready') for socket in (h, g)]
                for state in ready:
                    self.assertIsNone(state['panelist_activity'])
                    self.assertIsNone(state['operation'])
                    self.assertFalse(state['research_plan_approved'])
                    self.assertEqual(state['turns'], [])
                self.assertEqual(ai.call_count, 1)
                if remap:
                    self.now += 1000
                    h.send_json({'type': 'prepare_research_plan'})
                    active = [self.stage(socket, 'mapping') for socket in (h, g)]
                    self.assertNotEqual(active[0]['operation']['id'], activity['operation_id'])
                    self.assertEqual(active[0]['panelist_activity'], active[1]['panelist_activity'])
                    self.assertEqual(active[0]['panelist_activity']['context'], 'paper.md')
                    self.assertNotIn('Pilot decision', json.dumps(active[0]['panelist_activity']))
                    release_remap.set()
                    failed = [self.until(socket, research_planning_status='failed') for socket in (h, g)]
                    for state in failed:
                        self.assertIsNone(state['panelist_activity'])
                        self.assertIsNone(state['research_plan_progress'])
                        self.assertEqual(state['research_plan']['id'], ready[0]['research_plan']['id'])
                        self.assertFalse(state['research_plan_approved'])
                    self.now += 1000
                    h.send_json({'type': 'retry_research_plan'})
                    for socket in (h, g):
                        recovered = self.until(socket, research_planning_status='ready')
                        self.assertIsNone(recovered['panelist_activity'])
                        self.assertEqual(recovered['turns'], [])
                    self.assertEqual(ai.call_count, 3)

    def test_restart_retires_mapping_and_late_progress_cannot_restore_activity(self):
        release, finished = Event(), Event()
        self.addCleanup(release.set)
        prepared = fixtures.plan(4)

        def map_paper(*args, on_progress, **kwargs):
            try:
                on_progress(ResearchPlanProgress('mapping', (prepared.topics[0],)))
                if not release.wait(10):
                    raise AssertionError('Retired mapping was not released')
                on_progress(ResearchPlanProgress('validating', prepared.topics))
                return prepared
            finally:
                finished.set()

        with patch.object(planning, 'generate_research_plan', side_effect=map_paper) as ai:
            response = self.client.post('/api/rooms', data={'host_name': 'Host', 'defense_type': 'research'},
                files=[('research_files', ('paper.md', fixtures.PAPER.encode(), 'text/markdown'))])
            self.assertEqual(response.status_code, 201, response.text)
            host = response.json(); code = host['room_code']
            with self.client.websocket_connect(f'/ws/{code}') as socket:
                socket.send_json({'type': 'hello', 'token': host['player_token']})
                self.until(socket, 'lobby')
                socket.send_json({'type': 'prepare_research_plan'})
                active = self.stage(socket, 'mapping')
                self.assertEqual(active['panelist_activity']['context'], 'paper.md')
                socket.send_json({'type': 'restart'})
                retired = self.until(socket, 'lobby', research_planning_status='none')
                self.assertNotEqual(retired['defense_view_id'], active['defense_view_id'])
                self.assertIsNone(retired['panelist_activity'])
                self.assertIsNone(retired['operation'])
                release.set()
                self.assertTrue(finished.wait(5), 'Retired worker did not finish')
                with self.client.websocket_connect(f'/ws/{code}') as restored:
                    restored.send_json({'type': 'hello', 'token': host['player_token']})
                    current = self.until(restored, 'lobby', research_planning_status='none')
                    self.assertIsNone(current['panelist_activity'])
                    self.assertIsNone(current['research_plan'])
                    self.assertIsNone(current['research_plan_progress'])
                self.assertEqual(ai.call_count, 1)

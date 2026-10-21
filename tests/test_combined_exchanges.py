"""Authorized combined exchanges with synthetic provider HTTP and a controlled clock."""

import threading
from unittest.mock import patch

import httpx

from backend import game_server
from backend.rooms import planning as planning_workflow
from backend.rooms import coaching as coaching_workflow
from backend.rooms.commands import CatchUpDeadline
from backend.question_generator import CoachingReport, RESEARCH_PANELISTS
from backend.timed_turn import VOTE_MS
from tests.research_coaching_fixtures import scope_options, with_cards
from tests.test_openrouter_interactions import (
    ANSWER, ETHICS, METHODOLOGY, FundedInteractionRooms,
    clarification, combined_answer, probe,
)
from tests.test_openrouter_questions import assessment, planner_move, reviewer_question


class CombinedExchangeProtocolTests(FundedInteractionRooms):
    def opening(self):
        # Alternate-path subcases use distinct valid openings; repeated-opening
        # acceptance is exercised independently by the opening-history suite.
        self._opening_count = getattr(self, '_opening_count', 0) + 1
        return [planner_move(METHODOLOGY, 'topic-1'),
                reviewer_question(f'How will the team justify pilot design in practice case {self._opening_count}?')]

    def schemas(self, calls):
        return [call['response_format']['json_schema']['name'] for call in calls]

    def reject(self, socket, command, message):
        socket.send_json(command)
        for _ in range(60):
            event = socket.receive_json()
            if event['type'] == 'error':
                self.assertIn(message, event['message'])
                return
        self.fail('Expected the command to be rejected.')

    def test_reassigned_probe_reply_retains_both_authors_on_writer_retry(self):
        reply = 'We will recruit a comparison group under the same criteria.'
        outputs = [*self.opening(), probe(), combined_answer(),
                   httpx.Response(404, text='{}'),
                   reviewer_question('How will voluntary participation be protected?', evidence_line=6)]
        host, guest = self.create_room()
        code = host['room_code']
        with patch.object(planning_workflow, 'generate_research_plan', return_value=self.plan):
            with self.client.websocket_connect(f'/ws/{code}') as h, \
                 self.client.websocket_connect(f'/ws/{code}') as g:
                calls = self.funded(*outputs)
                self.open_question(((h, host['player_token']), (g, guest['player_token'])))
                h.send_json({'type': 'submit_answer', 'turn': 0, 'answer': ANSWER})
                for socket in (h, g):
                    state = self.until(socket, phase='probe')
                probe_id = state['turns'][0]['probe']['id']
                deadline = state['probe_deadline_ms']
                h.close()
                self.until(g, phase='probe', selected_seat=1)
                g.send_json({'type': 'submit_probe_reply', 'turn': 0,
                             'probe_id': probe_id, 'answer': reply})
                state = self.until(g, phase='retry')
                original = state['turns'][0]
                self.assertEqual(original['answer'], ANSWER)
                self.assertEqual(original['answered_by'], 'Host')
                self.assertEqual(original['probe']['reply'], reply)
                self.assertEqual(original['probe']['speaker_name'], 'Sam')
                self.assertEqual(original['probe']['speaker_seat'], 1)
                self.assertEqual(original['probe']['status'], 'answered')
                self.assertEqual(state['coverage']['topic-1']['status'], 'discussed')
                self.assertEqual(state['coverage']['topic-2']['status'], 'pending')
                self.reject(g, {'type': 'retry'}, 'Only the host')
                with self.client.websocket_connect(f'/ws/{code}') as restored:
                    restored.send_json({'type': 'hello', 'token': host['player_token']})
                    recovered = self.until(restored, phase='retry')
                    self.assertEqual(recovered['turns'][0], original)
                    before = len(calls)
                    restored.send_json({'type': 'retry'})
                    for socket in (restored, g):
                        final = self.until(socket, 'voting', 2)
                        self.assertEqual(final['turns'][0], original)
                    self.assertEqual(self.schemas(calls[before:]), ['QuestionDraft'])
                self.assertGreater(deadline, self.now)
        self.assertEqual(self.schemas(calls), ['PlanDraft', 'QuestionDraft',
                         'CombinedSubmissionDraft', 'CombinedSubmissionDraft', 'QuestionDraft', 'QuestionDraft'])
        self.assertIn('"speaker_name": "Host"', calls[3]['messages'][-1]['content'])
        self.assertIn('Latest submission speaker (data): "Sam"', calls[3]['messages'][-1]['content'])
        writer = calls[-1]['messages'][-1]['content']
        self.assertIn(ANSWER, writer)
        self.assertIn(reply, writer)
        self.assertIn('"speaker_name": "Sam"', writer)

    def test_clarification_or_probe_with_a_plan_is_rejected_without_acceptance(self):
        for action in (clarification(), probe()):
            with self.subTest(action=action['action']):
                invalid = {**combined_answer(), **action}
                host, guest = self.create_room()
                code = host['room_code']
                with patch.object(planning_workflow, 'generate_research_plan', return_value=self.plan):
                    with self.client.websocket_connect(f'/ws/{code}') as h, \
                         self.client.websocket_connect(f'/ws/{code}') as g:
                        calls = self.funded(*self.opening(), invalid, clarification())
                        before = self.open_question(((h, host['player_token']), (g, guest['player_token'])))
                        credits = self.client.get('/api/auth/me').json()['spent_credits']
                        self.reject(g, {'type': 'submit_answer', 'turn': 0, 'answer': ANSWER}, 'Only the chosen')
                        h.send_json({'type': 'submit_answer', 'turn': 0, 'answer': ANSWER})
                        for socket in (h, g):
                            failed = self.until(socket, phase='interpretation_retry')
                            self.assertEqual(failed['turns'], before['turns'])
                            self.assertEqual(failed['coverage'], before['coverage'])
                            self.assertEqual(failed['answer_deadline_ms'], before['answer_deadline_ms'])
                            self.assertFalse(failed['clock_paused'])
                            self.assertEqual(failed['my_pending_submission'], ANSWER if socket is h else None)
                        self.assertEqual(len(calls), 3)
                        h.send_json({'type': 'retry_interpretation'})
                        for socket in (h, g):
                            final = self.until(socket, phase='question')
                            self.assertEqual(final['coverage'], before['coverage'])
                            self.assertIsNone(final['turns'][0]['answer'])
                        self.assertEqual(self.client.get('/api/auth/me').json()['spent_credits'], credits)
                        self.assertEqual(self.schemas(calls[2:]), ['CombinedSubmissionDraft'] * 2)

    def test_direct_and_saved_probe_replies_use_separate_validated_planning(self):
        for saved in (False, True):
            with self.subTest(saved=saved):
                outputs = [*self.opening(), probe()]
                if saved:
                    outputs.append(httpx.Response(404, text='{}'))
                outputs += [planner_move(ETHICS, 'topic-2', assessment=assessment('topic-1', 0)),
                            reviewer_question('How will consent work?', evidence_line=6)]
                host, guest = self.create_room()
                code = host['room_code']
                with patch.object(planning_workflow, 'generate_research_plan', return_value=self.plan):
                    with self.client.websocket_connect(f'/ws/{code}') as h, \
                         self.client.websocket_connect(f'/ws/{code}') as g:
                        calls = self.funded(*outputs)
                        self.open_question(((h, host['player_token']), (g, guest['player_token'])))
                        h.send_json({'type': 'submit_answer', 'turn': 0, 'answer': ANSWER})
                        for socket in (h, g):
                            state = self.until(socket, phase='probe')
                        probe_id = state['turns'][0]['probe']['id']
                        reply = 'We use the same selection criteria.'
                        h.send_json({'type': 'submit_probe_reply', 'turn': 0, 'probe_id': probe_id,
                                     'answer': reply, 'direct': not saved})
                        if saved:
                            for socket in (h, g):
                                failed = self.until(socket, phase='interpretation_retry')
                                self.assertEqual(failed['probe_deadline_ms'], state['probe_deadline_ms'])
                            self.reject(g, {'type': 'use_pending_as_answer'}, 'Only the chosen')
                            h.send_json({'type': 'use_pending_as_answer'})
                        for socket in (h, g):
                            final = self.until(socket, 'voting', 2)
                            self.assertEqual(final['turns'][0]['answer'], ANSWER)
                            self.assertEqual(final['turns'][0]['probe']['reply'], reply)
                        self.assertEqual(self.schemas(calls[-2:]), ['PlanDraft', 'QuestionDraft'])

    def test_invalid_probe_plan_retries_saved_reply_without_losing_original_or_time(self):
        invalid = {**combined_answer(), 'assessment': assessment('topic-1', 9)}
        outputs = [*self.opening(), probe(), invalid, combined_answer(),
                   reviewer_question('How will participants give consent?', evidence_line=6)]
        host, guest = self.create_room()
        code = host['room_code']

        def elapsed(index):
            if index == 4:
                self.now += 2000

        with patch.object(planning_workflow, 'generate_research_plan', return_value=self.plan):
            with self.client.websocket_connect(f'/ws/{code}') as h, \
                 self.client.websocket_connect(f'/ws/{code}') as g:
                calls = self.funded(*outputs, on_call=elapsed)
                self.open_question(((h, host['player_token']), (g, guest['player_token'])))
                h.send_json({'type': 'submit_answer', 'turn': 0, 'answer': ANSWER})
                for socket in (h, g):
                    before = self.until(socket, phase='probe')
                probe_id = before['turns'][0]['probe']['id']
                reply = 'The comparison uses identical selection criteria.'
                h.send_json({'type': 'submit_probe_reply', 'turn': 0, 'probe_id': probe_id, 'answer': reply})
                for socket in (h, g):
                    failed = self.until(socket, phase='interpretation_retry')
                    self.assertEqual(failed['turns'], before['turns'])
                    self.assertEqual(failed['coverage'], before['coverage'])
                    self.assertFalse(failed['clock_paused'])
                    self.assertEqual(failed['probe_deadline_ms'], before['probe_deadline_ms'] + 2000)
                    self.assertEqual(failed['my_pending_submission'], reply if socket is h else None)
                self.now += 5000
                h.send_json({'type': 'retry_interpretation'})
                for socket in (h, g):
                    state = self.until(socket, 'voting', 2)
                    self.assertEqual(state['turns'][0]['answer'], ANSWER)
                    self.assertEqual(state['turns'][0]['probe']['reply'], reply)
                self.assertEqual(self.schemas(calls[3:]), ['CombinedSubmissionDraft'] * 2 + ['QuestionDraft'])

    def test_probe_expiry_or_recovery_keeps_original_answer_without_an_invented_reply(self):
        for expire in (False, True):
            with self.subTest(expire=expire):
                outputs = [*self.opening(), probe()]
                if not expire:
                    outputs.append(httpx.Response(404, text='{}'))
                outputs += [planner_move(ETHICS, 'topic-2', assessment=assessment('topic-1', 0)),
                            reviewer_question('How will consent be documented?', evidence_line=6)]
                host, guest = self.create_room()
                code = host['room_code']
                with patch.object(planning_workflow, 'generate_research_plan', return_value=self.plan):
                    with self.client.websocket_connect(f'/ws/{code}') as h, \
                         self.client.websocket_connect(f'/ws/{code}') as g:
                        calls = self.funded(*outputs)
                        self.open_question(((h, host['player_token']), (g, guest['player_token'])))
                        h.send_json({'type': 'submit_answer', 'turn': 0, 'answer': ANSWER})
                        for socket in (h, g):
                            state = self.until(socket, phase='probe')
                        probe_id = state['turns'][0]['probe']['id']
                        if expire:
                            self.now = state['probe_deadline_ms']
                            self.client.portal.call(game_server.rooms[code].coordinator.execute, CatchUpDeadline())
                        else:
                            h.send_json({'type': 'submit_probe_reply', 'turn': 0, 'probe_id': probe_id,
                                         'answer': 'An unaccepted draft.'})
                            for socket in (h, g):
                                self.until(socket, phase='interpretation_retry')
                            h.send_json({'type': 'finish_probe', 'turn': 0, 'probe_id': probe_id})
                        for socket in (h, g):
                            final = self.until(socket, 'voting', 2)
                            original = final['turns'][0]
                            self.assertEqual(original['answer'], ANSWER)
                            self.assertFalse(original['timed_out'])
                            self.assertIsNone(original['probe']['reply'])
                            self.assertEqual(original['probe']['status'], 'expired' if expire else 'ended_early')
                        self.assertEqual(self.schemas(calls[-2:]), ['PlanDraft', 'QuestionDraft'])

    def test_direct_reply_invalidates_a_late_combined_decision(self):
        entered, release = threading.Event(), threading.Event()

        def gate(index):
            if index == 4:
                entered.set()
                if not release.wait(10):
                    raise AssertionError('The synthetic provider was not released.')

        host, guest = self.create_room()
        code = host['room_code']
        outputs = [*self.opening(), probe(), combined_answer(),
                   planner_move(ETHICS, 'topic-2', assessment=assessment('topic-1', 0)),
                   reviewer_question('How will the team collect consent?', evidence_line=6)]
        with patch.object(planning_workflow, 'generate_research_plan', return_value=self.plan):
            with self.client.websocket_connect(f'/ws/{code}') as h, \
                 self.client.websocket_connect(f'/ws/{code}') as g:
                calls = self.funded(*outputs, on_call=gate)
                self.open_question(((h, host['player_token']), (g, guest['player_token'])))
                h.send_json({'type': 'submit_answer', 'turn': 0, 'answer': ANSWER})
                for socket in (h, g):
                    state = self.until(socket, phase='probe')
                probe_id = state['turns'][0]['probe']['id']
                h.send_json({'type': 'submit_probe_reply', 'turn': 0, 'probe_id': probe_id,
                             'answer': 'An obsolete pending reply.'})
                try:
                    self.assertTrue(entered.wait(10))
                    h.send_json({'type': 'submit_probe_reply', 'turn': 0, 'probe_id': probe_id,
                                 'answer': 'The explicit direct reply.', 'direct': True})
                    for socket in (h, g):
                        final = self.until(socket, 'voting', 2)
                        self.assertEqual(final['turns'][0]['probe']['reply'], 'The explicit direct reply.')
                    expected = final['turns']
                finally:
                    release.set()
                # A later public snapshot must remain authoritative after the
                # blocked provider returns; no obsolete plan may trigger work.
                with self.client.websocket_connect(f'/ws/{code}') as restored:
                    restored.send_json({'type': 'hello', 'token': host['player_token']})
                    current = self.until(restored, 'voting', 2)
                    self.assertEqual(current['turns'], expected)
                    self.reject(restored, {'type': 'submit_probe_reply', 'turn': 0,
                                          'probe_id': probe_id, 'answer': 'Replay'}, 'no question awaiting')
                self.assertEqual(self.schemas(calls[3:]),
                                 ['CombinedSubmissionDraft', 'PlanDraft', 'QuestionDraft'])

    def test_complete_research_and_mixed_alternates_reach_coaching_once(self):
        impact, critical = RESEARCH_PANELISTS[2:]

        def coach(files, history, key, model, **kwargs):
            report = CoachingReport('The practice budget ended.', [], [], 'Review the unanswered topic.',
                                    closing='Review your final explanation in coaching.')
            return with_cards(report, history, **scope_options(kwargs))

        for mode in ('research', 'mixed'):
            with self.subTest(mode=mode):
                host, guest = self.create_room(mode)
                code = host['room_code']
                paper_id = 2 if mode == 'mixed' else 1
                outputs = [planner_move(METHODOLOGY, 'topic-1'),
                           reviewer_question(f'How will you justify the {mode} pilot design?', source_file=paper_id),
                           clarification('Giunsa ninyo pagplano sa pilot comparison?'),
                           planner_move(ETHICS, 'topic-2', assessment=assessment('topic-1', 0)),
                           reviewer_question('How will you ask for consent?', source_file=paper_id, evidence_line=6,
                                             lead_in='You described your design.'),
                           planner_move(impact, 'topic-3', assessment=assessment(
                               'topic-2', 1, status='needs clarification')),
                           reviewer_question('How will you evaluate the planned benefit?', source_file=paper_id,
                                             evidence_line=8, lead_in='No answer was recorded.'),
                           {'action': 'answer', 'clarification': None, 'probe': None,
                            'assessment': assessment('topic-3', 2),
                            'panelist': critical, 'topic_id': 'topic-4', 'is_follow_up': False},
                           reviewer_question('Which limit bounds the pilot claim?', source_file=paper_id,
                                             evidence_line=10, lead_in='You explained the planned benefit.'),
                           probe('Which participants are outside that claim?'),
                           {'action': 'answer', 'clarification': None, 'probe': None,
                            'assessment': assessment('topic-4', 3),
                            'panelist': None, 'topic_id': None, 'is_follow_up': False}]
                with patch.object(planning_workflow, 'generate_research_plan', return_value=self.plan), \
                     patch.object(coaching_workflow, 'generate_coaching_report', side_effect=coach) as coaching:
                    with self.client.websocket_connect(f'/ws/{code}') as h, \
                         self.client.websocket_connect(f'/ws/{code}') as g:
                        calls = self.funded(*outputs)
                        state = self.open_question(((h, host['player_token']), (g, guest['player_token'])))
                        h.send_json({'type': 'submit_answer', 'turn': 0,
                                     'answer': 'Please explain in modern Bisaya.'})
                        for socket in (h, g):
                            self.until(socket, phase='question')
                        h.send_json({'type': 'submit_direct_answer', 'turn': 0, 'answer': 'Yes.'})
                        for index in (1, 2, 3):
                            for socket in (h, g):
                                state = self.until(socket, 'voting', index + 1)
                                self.assertEqual(state['turns'][-1]['panelist'], RESEARCH_PANELISTS[index])
                                self.assertEqual(state['turns'][-1]['filename'], 'study.md')
                            h.send_json({'type': 'cast_vote', 'seat': 0})
                            for socket in (h, g):
                                self.until(socket, 'voting', index + 1)
                            self.now += VOTE_MS + 1
                            self.client.portal.call(game_server.rooms[code].coordinator.execute, CatchUpDeadline())
                            for socket in (h, g):
                                state = self.until(socket, 'question', index + 1)
                            if index == 1:
                                self.now = state['answer_deadline_ms']
                                self.client.portal.call(game_server.rooms[code].coordinator.execute, CatchUpDeadline())
                            else:
                                h.send_json({'type': 'submit_answer', 'turn': index,
                                             'answer': 'Ang among comparison kay campus volunteers ra.'})
                        for socket in (h, g):
                            state = self.until(socket, phase='probe')
                        h.send_json({'type': 'submit_probe_reply', 'turn': 3,
                                     'probe_id': state['turns'][3]['probe']['id'],
                                     'answer': 'Dili apil ang students outside sa campus pilot.'})
                        for socket in (h, g):
                            final = self.until(socket, 'complete', 4, feedback_status='ready')
                            self.assertEqual(final['completion_reason'], 'budget exhausted')
                            self.assertIsNone(final['turns'][1]['answer'])
                            self.assertTrue(final['turns'][1]['timed_out'])
                            cards = final['feedback']['answer_cards']
                            self.assertEqual(len(cards), 4)
                            self.assertEqual(cards[1]['original_answer'], None)
                            self.assertEqual(cards[1]['feedback']['strengths'], [])
                            self.assertEqual(final['closing_panelist'], critical)
                        count = coaching.call_count
                        deadline = final['closing_deadline_ms']
                        with self.client.websocket_connect(f'/ws/{code}') as restored:
                            restored.send_json({'type': 'hello', 'token': host['player_token']})
                            state = self.until(restored, phase='complete', feedback_status='ready')
                            self.assertEqual(state['closing_deadline_ms'], deadline)
                            self.reject(restored, {'type': 'retry_coaching'}, 'no failed coaching')
                        self.assertEqual(coaching.call_count, count)
                self.assertEqual(self.schemas(calls), ['PlanDraft', 'QuestionDraft', 'CombinedSubmissionDraft',
                                 'PlanDraft', 'QuestionDraft', 'PlanDraft', 'QuestionDraft',
                                 'CombinedSubmissionDraft', 'QuestionDraft',
                                 'CombinedSubmissionDraft', 'CombinedSubmissionDraft'])
                self.assertIn('modern, conversational Cebuano', calls[-1]['messages'][0]['content'])
                self.assertIn('practice lens, not proof', calls[-1]['messages'][0]['content'])

"""Post-answer generation recovery through the real asynchronous room boundary."""
import os
import unittest
from unittest.mock import AsyncMock, patch

from backend import game_server as server
from backend.defense_session import DefenseSession
from backend.project_files import ProjectFile
from backend.question_generator import GroundedQuestion, PanelMove, InvalidQuestionResponse


class QuestionRecoveryTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        env = patch.dict(os.environ, {'DATABASE_URL': '', 'PAYMENTS_MODE': 'test', 'OPENAI_API_KEY': 'offline-key'})
        env.start()
        self.addCleanup(env.stop)
        server.ai_rate.__init__()
        self.question = GroundedQuestion('Why this queue?', 'queue.py', 1, 'queue = []')
        session = DefenseSession.start(self.question)
        session.submit_answer('We preserve arrival order.')
        self.room = server.Room(code='RECOVERY', files=[ProjectFile('queue.py', 'queue = []')],
                                players={}, defense=session, phase='generating')
        self.next_move = PanelMove('Security Reviewer', GroundedQuestion('Who can change it?', 'queue.py', 1, 'queue = []'))

    async def test_invalid_next_question_recovers_without_manual_host_retry(self):
        with patch.object(server, 'generate_next_move', side_effect=[
            InvalidQuestionResponse('The AI cited an invalid source line. Please try again.'), self.next_move
        ]) as generator, patch.object(server, 'publish', new_callable=AsyncMock), patch.object(server, '_schedule_clock'):
            await server._generate_question(self.room, self.room.generation_id, False)
        self.assertEqual(generator.call_count, 2, 'A single rejected next question should recover without opening Controls.')
        self.assertEqual(self.room.phase, 'voting')
        self.assertEqual(len(self.room.defense.turns), 2)
        self.assertEqual(self.room.defense.turns[0].answer, 'We preserve arrival order.')
        self.assertIsNone(self.room.error)

    async def test_recovery_is_bounded_then_manual_retry_keeps_one_answer(self):
        failure = InvalidQuestionResponse('The AI cited an invalid source line.')
        snapshots = []
        async def capture(room):
            snapshots.append(room.snapshot())
        with patch.object(server, 'generate_next_move', side_effect=failure) as generator, patch.object(server, 'publish', side_effect=capture):
            await server._generate_question(self.room, self.room.generation_id, False)
        self.assertEqual(generator.call_count, 2)
        self.assertEqual(self.room.phase, 'retry')
        self.assertEqual(snapshots[0]['phase'], 'generating')
        self.assertTrue(snapshots[0]['question_retrying'])
        self.assertEqual(snapshots[0]['turns'][0]['answer'], 'We preserve arrival order.')
        self.assertFalse(snapshots[-1]['question_retrying'])
        self.assertEqual(snapshots[-1]['question_attempts_left'], 1)
        self.room.phase = 'generating'
        self.room.generation_id += 1
        with patch.object(server, 'generate_next_move', return_value=self.next_move), patch.object(server, 'publish', new_callable=AsyncMock), patch.object(server, '_schedule_clock'):
            await server._generate_question(self.room, self.room.generation_id, False)
        self.assertEqual(len(self.room.defense.turns), 2)
        self.assertEqual(len(self.room.defense.answered_history()), 1)

    async def test_nonrecoverable_provider_and_configuration_errors_stop_immediately(self):
        import httpx2
        from openai import APIStatusError
        from backend.question_generator import QuestionGenerationError
        for failure in [QuestionGenerationError('Set a valid OPENAI_API_KEY and restart the app.')] + [
            APIStatusError('provider rejected request', response=httpx2.Response(status, request=httpx2.Request('POST', 'https://provider.example.test')),
                           body={'error': {'code': 'insufficient_quota'}})
            for status in (400, 401, 403, 404, 429)
        ]:
            with self.subTest(error=type(failure).__name__, status=getattr(failure, 'status_code', None)):
                self.room.phase = 'generating'
                self.room.ai_budget.reset_run(8)
                with patch.object(server, 'generate_next_move', side_effect=failure) as generator, patch.object(server, 'publish', new_callable=AsyncMock):
                    await server._generate_question(self.room, self.room.generation_id, False)
                self.assertEqual(generator.call_count, 1)
                self.assertEqual(self.room.phase, 'retry')
                self.assertEqual(self.room.defense.turns[0].answer, 'We preserve arrival order.')

    async def test_ending_or_restarting_during_backoff_discards_recovery(self):
        async def end_during_backoff(_):
            self.room.generation_id += 1
            self.room.phase = 'complete'
        with patch.object(server, 'generate_next_move', side_effect=InvalidQuestionResponse('Invalid citation')) as generator, \
             patch.object(server, 'publish', new_callable=AsyncMock), patch.object(server.asyncio, 'sleep', side_effect=end_during_backoff):
            await server._generate_question(self.room, 0, False)
        self.assertEqual(generator.call_count, 1)
        self.assertEqual(self.room.phase, 'complete')
        self.room.phase = 'generating'
        self.assertFalse(self.room.snapshot()['question_retrying'])
        self.assertEqual(len(self.room.defense.turns), 1)

    async def test_actual_citation_validation_recovers_from_a_fresh_response(self):
        from backend.question_generator import NextMoveDraft, generate_next_move
        from tests.test_question_generator import FakeClient
        drafts = [NextMoveDraft(action='ask', panelist='Security Reviewer', lead_in='', question='Who may change the queue?', source_file=1, evidence_line=line) for line in (99, 1)]
        clients = [FakeClient(draft) for draft in drafts]
        def generate(files, key, **kwargs):
            return generate_next_move(files, key, client=clients.pop(0), **kwargs)
        with patch.object(server, 'generate_next_move', side_effect=generate) as generator, patch.object(server, 'publish', new_callable=AsyncMock), patch.object(server, '_schedule_clock'):
            await server._generate_question(self.room, 0, False)
        self.assertEqual(generator.call_count, 2)
        self.assertEqual(self.room.defense.turns[-1].question.evidence_text, 'queue = []')
        self.assertEqual(self.room.phase, 'voting')

    async def test_research_recovery_leaves_coverage_unchanged_until_a_valid_move(self):
        from copy import deepcopy
        from backend.defense_session import ResearchDefenseSession
        from tests.test_research_coverage import plan, FILES, mocked_move
        session = ResearchDefenseSession.create(plan(4), 8, 'research', 'proposal')
        session.apply_move(mocked_move(FILES, None, history=[], context=session.context(), defense_type='research'))
        session.submit_answer('We will compare measured wait times.', speaker_name='Host')
        before = deepcopy(session.coverage)
        self.room.defense, self.room.files, self.room.defense_type = session, FILES, 'research'
        calls = []
        def generate(files, key, **kwargs):
            self.assertEqual(session.coverage, before)
            self.assertEqual(len(kwargs['history']), 1)
            calls.append(kwargs['history'][0].answer)
            if len(calls) == 1: raise InvalidQuestionResponse('Invalid citation')
            return mocked_move(files, key, **kwargs)
        with patch.object(server, 'generate_research_move', side_effect=generate), patch.object(server, 'publish', new_callable=AsyncMock), patch.object(server, '_schedule_clock'), patch.object(server, 'charge_run') as charge:
            await server._generate_question(self.room, 0, False)
        self.assertEqual(calls, ['We will compare measured wait times.'] * 2)
        self.assertEqual(len(session.turns), 2)
        self.assertEqual(session.coverage['topic-1']['status'], 'addressed')
        charge.assert_not_called()

    async def test_temporary_connection_and_server_failures_recover_once(self):
        import httpx2
        from openai import APIConnectionError, APIStatusError
        request = httpx2.Request('POST', 'https://provider.example.test')
        for failure in (APIConnectionError(request=request), APIStatusError('temporary', response=httpx2.Response(503, request=request), body=None)):
            with self.subTest(error=type(failure).__name__):
                self.room.phase = 'generating'
                self.room.ai_budget.reset_run(8)
                self.room.defense = DefenseSession.start(self.question)
                self.room.defense.submit_answer('We preserve arrival order.')
                with patch.object(server, 'generate_next_move', side_effect=[failure, self.next_move]) as generator, patch.object(server, 'publish', new_callable=AsyncMock), patch.object(server, '_schedule_clock'):
                    await server._generate_question(self.room, 0, False)
                self.assertEqual(generator.call_count, 2)
                self.assertEqual(self.room.phase, 'voting')

    async def test_opening_and_last_allowed_attempt_do_not_recover_automatically(self):
        self.room.ai_budget.attempts['question:1'] = 2
        with patch.object(server, 'generate_next_move', side_effect=InvalidQuestionResponse('Invalid response')) as generator, patch.object(server, 'publish', new_callable=AsyncMock):
            await server._generate_question(self.room, 0, False)
        self.assertEqual(generator.call_count, 1)
        self.assertEqual(self.room.snapshot()['question_attempts_left'], 0)
        self.room.defense, self.room.phase = None, 'generating'
        with patch.object(server, 'generate_first_question', side_effect=InvalidQuestionResponse('Invalid response')) as generator, patch.object(server, 'publish', new_callable=AsyncMock):
            await server._generate_question(self.room, 0, True)
        self.assertEqual(generator.call_count, 1)
        self.assertEqual(self.room.phase, 'retry')

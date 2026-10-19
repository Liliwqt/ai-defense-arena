"""Protected coaching through the funded transport; providers are mocked."""

import asyncio
import json
import threading
import unittest
from unittest.mock import patch

import httpx

from backend.openrouter_questions import RunQuestionClient, RunQuestionPolicy, establish_run_allowance
from backend.provider_allowance import ProviderAllowance
from backend.question_generator import AnsweredQuestion, generate_coaching_report
from backend.coaching_progress import CoachingInput
from backend.rooms.coaching import request_coaching
from backend.rooms.coordinator import RoomCoordinator, RoomWorkflows
from backend.rooms.commands import GenerateCoaching, RetryCoaching, CatchUpDeadline, EndUnavailable
from backend.live_store import LiveStore
from backend.project_files import ProjectFile
from backend.openrouter_questions import run_scope, FRAMING_BYTES
from backend.question_generator import CoachingDraft, QuestionGenerationError
from tests import test_progressive_coaching as progressive
from tests import test_openrouter_interactions as interactions
from tests import test_research_coverage as coverage
from tests import test_research_plan as maps
from backend import game_server
from backend.rooms import planning as planning_workflow
from tests.test_openrouter_questions import planner_move, reviewer_question, assessment, METHODOLOGY, ETHICS
from tests.research_coaching_fixtures import cards_for
from tests.async_room import wait_until
from tests.test_openrouter_questions import HTTPClient, IsolatedAllowanceTests, stream_response


OVERVIEW = {'summary': 'The team described its pilot.', 'strengths': [],
            'improvements': [], 'next_step': 'Practice the limits.', 'closing': 'Review those limits.'}


class FundedCoachingClientTests(IsolatedAllowanceTests):
    def test_room_request_needs_only_openrouter_and_keeps_its_snapshot(self):
        scope, owner = 'run:request', 'owner'
        establish_run_allowance(scope, owner, self.files, 4)
        history = (AnsweredQuestion('Methodology Reviewer', 'Why this pilot?', 'A bounded comparison.'),)
        request = CoachingInput(tuple(self.files), history, None, 'research', 'proposal',
                                overview_only=True, provider_scope=scope, provider_owner=owner)
        calls = []

        def provider(request):
            calls.append(json.loads(request.content))
            return stream_response(OVERVIEW)

        with patch('httpx.Client', side_effect=lambda **kw: HTTPClient(transport=httpx.MockTransport(provider))), \
             patch.dict('os.environ', {'OPENAI_API_KEY': '', 'OPENAI_MODEL': 'unrelated'}), \
             patch('backend.openrouter_questions.COACHING_MODEL', 'changed-after-start'):
            report = asyncio.run(request_coaching(request))
        self.assertEqual(report.closing, OVERVIEW['closing'])
        self.assertEqual(calls[0]['model'], 'anthropic/claude-haiku-5.5')

    def test_overview_uses_fixed_haiku_high_and_can_spend_the_protected_reserve(self):
        scope, owner = 'run:coaching', 'owner'
        policy = establish_run_allowance(scope, owner, self.files, 4)
        allowance = ProviderAllowance(scope, owner)
        allowance.reserve(policy.question_limit_nano, limit=policy.question_limit_nano)
        calls = []

        def provider(request):
            calls.append(json.loads(request.content))
            return stream_response(OVERVIEW)

        def client(*args, **kwargs):
            return HTTPClient(transport=httpx.MockTransport(provider))

        funded = RunQuestionClient(scope, owner, None, self.files).coaching()
        history = [AnsweredQuestion('Methodology Reviewer', 'Why this pilot?', 'A bounded comparison.')]
        with patch('httpx.Client', side_effect=client), \
             patch('openai.OpenAI', side_effect=AssertionError('No direct fallback')):
            report = generate_coaching_report(self.files, history, None, client=funded,
                                              defense_type='research', overview_only=True)
        self.assertEqual(report.summary, OVERVIEW['summary'])
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]['model'], 'anthropic/claude-haiku-5.5')
        self.assertEqual(calls[0]['reasoning'], {'effort': 'high'})
        self.assertEqual(calls[0]['max_tokens'], 8192)
        self.assertEqual(allowance.snapshot()['used'], policy.question_limit_nano + 500_000)
        stored = RunQuestionPolicy(**allowance.policy())
        self.assertEqual(stored.coaching_model, calls[0]['model'])

    def test_unaffordable_retry_never_dispatches_or_resets_the_allowance(self):
        scope, owner = 'run:exhausted-coaching', 'owner'
        policy = establish_run_allowance(scope, owner, self.files, 4)
        allowance = ProviderAllowance(scope, owner)
        allowance.reserve(policy.ceiling_nano, limit=policy.ceiling_nano)
        before = allowance.snapshot()
        coach = RunQuestionClient(scope, owner, None, self.files).coaching()
        with patch('httpx.Client', side_effect=AssertionError('No unaffordable dispatch')):
            for _ in range(2):
                with self.assertRaisesRegex(QuestionGenerationError, 'cannot fund another coaching section'):
                    coach.parse(input=[{'role': 'user', 'content': 'Report.'}], text_format=CoachingDraft)
        self.assertEqual(allowance.snapshot(), before)

    def test_rejected_card_is_still_billed_and_keeps_server_originals(self):
        scope, owner = 'run:invalid-card', 'owner'
        establish_run_allowance(scope, owner, self.files, 4)
        history = [AnsweredQuestion('Methodology Reviewer', 'Why this pilot?', 'uhm a bounded comparison.', speaker_name='Sam')]
        raw = {**OVERVIEW, 'answer_cards': cards_for(history)}
        raw['answer_cards'][0]['feedback']['wording_examples'] = ['invented hesitation']
        coach = RunQuestionClient(scope, owner, None, self.files).coaching()
        with patch('httpx.Client', side_effect=lambda **kw: HTTPClient(
                transport=httpx.MockTransport(lambda request: stream_response(raw)))):
            with self.assertRaisesRegex(QuestionGenerationError, 'actual submitted words'):
                generate_coaching_report(self.files, history, None, client=coach,
                                         defense_type='research', section_turns=(0,))
        self.assertEqual(ProviderAllowance(scope, owner).snapshot()['used'], 500_000)
        self.assertEqual(history[0].answer, 'uhm a bounded comparison.')


class FundedCoachingProgressTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # Reuse the existing paid-run fixture without inheriting its tests.
        await progressive.ProgressiveRecoveryTests.asyncSetUp(self)
        self.room.files = [ProjectFile('paper.md', 'Campus pilot.', 'research_text')]
        self.room.defense.question_budget = 8
        self.allowance = ProviderAllowance(run_scope(self.room.run_id), self.account['id'])
        self.policy = establish_run_allowance(self.allowance.id, self.account['id'], self.room.files, 8)
        self.history = self.room.defense.coaching_history()
        self.now = [1000]
        self.calls = []

    def section(self, turns):
        return {**OVERVIEW, 'answer_cards': [card for card in cards_for(self.history) if card['turn'] in turns]}

    async def owner(self, outputs, *, on_call=None, on_close=None):
        def provider(request):
            self.calls.append(json.loads(request.content))
            if on_call:
                on_call(len(self.calls))
            output = outputs[len(self.calls) - 1]
            response = output if isinstance(output, httpx.Response) else stream_response(output)
            if on_close and len(self.calls) == 5:
                data = response.content
                class ObservedReply(httpx.SyncByteStream):
                    def __iter__(self):
                        yield data
                    def close(self):
                        on_close()
                return httpx.Response(200, stream=ObservedReply())
            return response
        mock = patch('httpx.Client', side_effect=lambda **kw: HTTPClient(transport=httpx.MockTransport(provider)))
        mock.start(); self.addCleanup(mock.stop)
        direct = patch('openai.OpenAI', side_effect=AssertionError('No direct fallback'))
        direct.start(); self.addCleanup(direct.stop)
        async def deliver(socket, payload):
            pass
        owner = RoomCoordinator(self.room, RoomWorkflows(now=lambda: self.now[0], deliver=deliver))
        self.addAsyncCleanup(owner.shutdown)
        return owner

    async def state(self, owner, status):
        await wait_until(lambda: owner.view(self.actor)['feedback_status'] == status, timeout=5)
        return owner.view(self.actor)

    async def test_partial_results_retry_only_failed_sections_and_settle_once(self):
        owner = await self.owner([OVERVIEW, self.section((0, 1, 2)), httpx.Response(503),
                                  self.section((6,)), self.section((3, 4, 5))])
        await owner.execute(GenerateCoaching(1))
        failed = await self.state(owner, 'failed')
        self.assertEqual(failed['coaching_progress']['cards_ready'], 4)
        self.assertEqual(failed['coaching_progress']['completion_status'], 'pending')
        self.assertFalse(self.room.settled)
        preserved = failed['feedback']['answer_cards']
        self.assertEqual(self.store.overview(self.account['id'])['live_runs'][0]['outcome'], 'unavailable')
        self.now[0] = failed['closing_deadline_ms'] + 1
        await owner.execute(CatchUpDeadline())
        self.assertTrue((await owner.execute(RetryCoaching(), self.actor)).accepted)
        ready = await self.state(owner, 'ready')
        self.assertEqual(len(self.calls), 5)
        self.assertTrue(all(call['model'] == 'anthropic/claude-haiku-5.5' for call in self.calls))
        self.assertTrue(all(call['reasoning'] == {'effort': 'high'} for call in self.calls))
        self.assertEqual([c for c in ready['feedback']['answer_cards'] if c['turn'] in {0, 1, 2, 6}], preserved)
        self.assertIsNone(ready['closing_deadline_ms'])
        self.assertEqual(ready['coaching_progress']['cards_ready'], 7)
        self.assertTrue(self.room.settled)
        wallet = self.store.overview(self.account['id'])
        self.assertEqual(wallet['live_credits'], 0)
        self.assertEqual(wallet['live_runs'][0]['outcome'], 'completed')
        failed_call = self.calls[2]
        failed_bound = self.policy.stage_bound(len(json.dumps(
            {'messages': failed_call['messages'], 'schema': failed_call['response_format']},
            ensure_ascii=False).encode()) + FRAMING_BYTES, failed_call['max_tokens'])
        self.assertEqual(self.allowance.snapshot()['used'], 2_000_000 + failed_bound)

    async def test_completion_write_retry_never_regenerates_cards(self):
        owner = await self.owner([OVERVIEW, self.section((0, 1, 2)),
                                  self.section((3, 4, 5)), self.section((6,))])
        original = LiveStore.finish_run
        writes = []
        def finish(store, run, outcome):
            writes.append(outcome)
            if len(writes) == 1:
                raise RuntimeError('Synthetic completion outage')
            return original(store, run, outcome)
        with patch.object(LiveStore, 'finish_run', finish):
            await owner.execute(GenerateCoaching(1))
            failed = await self.state(owner, 'failed')
            self.assertEqual(failed['coaching_progress']['cards_ready'], 7)
            before = self.allowance.snapshot()
            self.assertTrue((await owner.execute(RetryCoaching(), self.actor)).accepted)
            ready = await self.state(owner, 'ready')
        self.assertEqual(len(self.calls), 4)
        self.assertEqual(writes, ['completed', 'completed'])
        self.assertEqual(ready['feedback'], failed['feedback'])
        self.assertEqual(ready['closing_deadline_ms'], failed['closing_deadline_ms'])
        self.assertEqual(self.allowance.snapshot(), before)

    async def test_credit_return_fences_late_provider_and_retains_its_cost(self):
        started, release, closed = threading.Event(), threading.Event(), threading.Event()
        self.addCleanup(release.set)
        def gate(count):
            if count == 5:
                started.set(); release.wait(10)
        owner = await self.owner([OVERVIEW, self.section((0, 1, 2)), httpx.Response(503),
                                  self.section((6,)), self.section((3, 4, 5))], on_call=gate, on_close=closed.set)
        await owner.execute(GenerateCoaching(1))
        failed = await self.state(owner, 'failed')
        self.assertTrue((await owner.execute(RetryCoaching(), self.actor)).accepted)
        self.assertTrue(await asyncio.to_thread(started.wait, 3))
        reserved = self.allowance.snapshot()
        self.assertTrue((await owner.execute(EndUnavailable(), self.actor)).accepted)
        self.assertTrue((await owner.execute(EndUnavailable(), self.actor)).accepted)
        release.set()
        self.assertTrue(await asyncio.to_thread(closed.wait, 3))
        final = owner.view(self.actor)
        self.assertEqual(final['feedback'], failed['feedback'])
        self.assertEqual(final['coaching_progress']['completion_status'], 'returned')
        self.assertEqual(self.allowance.snapshot(), reserved)
        self.assertEqual(self.store.overview(self.account['id'])['live_credits'], 10)
        self.assertEqual(self.store.finish_run(self.room.run_id, 'completed'), 'ended_unavailable')


class FundedCoachingRoomTests(coverage.CoverageProtocolTests):
    test_twelve_question_research_and_mixed_with_vote_clarification_timeout_retry_reconnect_coaching = None
    test_twelve_question_pdf_research_and_mixed_preserve_private_originals_and_citations = None
    create_room = interactions.FundedInteractionProtocolTests.create_room
    prepare = interactions.FundedInteractionProtocolTests.prepare
    open_question = interactions.FundedInteractionProtocolTests.open_question

    def setUp(self):
        super().setUp()
        self.plan = maps.fixture_plan()

    def test_two_clients_receive_funded_coaching_and_reconnect_with_the_same_originals(self):
        host, guest = self.create_room()
        code = host['room_code']
        calls = []
        outputs = [planner_move(METHODOLOGY, 'topic-1'), reviewer_question('Why this pilot?'),
                   planner_move(ETHICS, 'topic-2', assessment=assessment('topic-1', 0)),
                   reviewer_question('How will participants agree?', evidence_line=6)]
        def provider(request):
            body = json.loads(request.content)
            calls.append(body)
            if len(calls) <= 4:
                output = outputs[len(calls) - 1]
            elif body['response_format']['json_schema']['name'] == 'CoachingDraft':
                output = OVERVIEW
            else:
                history = game_server.rooms[code].defense.coaching_history()
                output = {**OVERVIEW, 'answer_cards': cards_for(history)}
            return stream_response(output)
        with patch('httpx.Client', side_effect=lambda **kw: HTTPClient(transport=httpx.MockTransport(provider))), \
             patch.object(planning_workflow, 'generate_research_plan', return_value=self.plan):
            with self.client.websocket_connect(f'/ws/{code}') as h, \
                 self.client.websocket_connect(f'/ws/{code}') as g:
                self.open_question(((h, host['player_token']), (g, guest['player_token'])))
                h.send_json({'type': 'submit_direct_answer', 'turn': 0, 'answer': 'We plan a bounded pilot.'})
                for socket in (h, g):
                    self.until(socket, phase='voting', count=2)
                h.send_json({'type': 'end_defense'})
                states = [self.until(socket, feedback_status='ready') for socket in (h, g)]
                self.assertEqual(states[0]['feedback'], states[1]['feedback'])
                cards = states[0]['feedback']['answer_cards']
                self.assertEqual(cards[0]['original_answer'], 'We plan a bounded pilot.')
                self.assertEqual(cards[0]['speaker_name'], 'Host')
                self.assertIsNone(cards[1]['original_answer'])
                self.assertEqual(cards[1]['feedback']['wording_basis'], 'unanswered')
                self.assertEqual(states[0]['coaching_progress']['completion_status'], 'ready')
                with self.client.websocket_connect(f'/ws/{code}') as restored:
                    restored.send_json({'type': 'hello', 'token': guest['player_token']})
                    self.assertEqual(restored.receive_json()['state']['feedback'], states[0]['feedback'])
        self.assertEqual(len(calls), 6)
        self.assertTrue(all(c['model'] == 'anthropic/claude-haiku-5.5' for c in calls[4:]))
        self.assertEqual(ProviderAllowance(run_scope(game_server.rooms[code].run_id),
                         self._offline_credentials[2]['id']).snapshot()['used'], 3_000_000)

"""Bounded processing windows and one automatic transient retry."""

import asyncio
from dataclasses import replace
import unittest

from backend.defense_session import DefenseSession
from backend.openrouter_stream import ProviderConnectionError, ProviderStatusError
from backend.processing_policy import (
    LEGACY, STANDARD, ProcessingPolicy, ProcessingWindowExpired, decide_retry,
    transient_directive,
)
from backend.project_files import ProjectFile
from backend.question_generator import GroundedQuestion, PanelMove, SubmissionDecision
from backend.room_operations import RoomOperation
from backend.rooms.commands import GenerateQuestion, VerifiedActor
from backend.rooms.coordinator import RoomCoordinator, RoomWorkflows
from backend.rooms.model import Player, Room
from backend.rooms.submissions import (
    InterpretationWork, capture_interpretation, run_interpretation,
)


QUESTION = GroundedQuestion("Why a queue?", "queue.py", 1, "queue = []")


class ProcessingPolicyTests(unittest.TestCase):
    def test_standard_has_one_authoritative_45_second_window(self):
        policy = ProcessingPolicy.standard()
        self.assertEqual(policy.version, STANDARD)
        self.assertEqual(policy.window_ms, 45_000)
        self.assertEqual(policy.deadline_ms(10_000), 55_000)
        self.assertFalse(policy.expired(55_000, 54_999))
        self.assertTrue(policy.expired(55_000, 55_000))
        self.assertEqual(policy.remaining_ms(55_000, 54_999), 1)
        self.assertIn('45-second', policy.expiry_message())

    def test_legacy_and_free_keep_their_distinct_semantics(self):
        legacy = ProcessingPolicy.legacy()
        self.assertEqual(legacy.version, LEGACY)
        self.assertIsNone(legacy.window_ms)
        self.assertFalse(legacy.provider_directed_retry)
        self.assertEqual(legacy.automatic_retries, 1)
        free = ProcessingPolicy.free()
        self.assertIsNone(free.window_ms)
        self.assertTrue(free.provider_directed_retry)
        self.assertEqual(ProcessingPolicy.for_tier('free'), free)
        self.assertEqual(ProcessingPolicy.for_tier('standard'), ProcessingPolicy.standard())

    def test_only_transient_provider_failures_are_retryable(self):
        retryable = ProviderStatusError(503, 'temporary')
        self.assertEqual(transient_directive(retryable).delay_ms, 1_000)
        missing_wait = ProviderStatusError(429, 'limited')
        self.assertIsNone(transient_directive(missing_wait))
        connection = ProviderConnectionError('temporary')
        self.assertEqual(transient_directive(connection).delay_ms, 1_000)
        short_wait = ProviderStatusError(429, 'limited', retry_after_seconds=2)
        self.assertEqual(transient_directive(short_wait).delay_ms, 2_000)
        daily = ProviderStatusError(429, 'daily', retry_after_seconds=2, manual_only=True)
        self.assertIsNone(transient_directive(daily))

    def test_retry_must_fit_attempts_funds_and_the_remaining_window(self):
        policy = ProcessingPolicy.standard()
        error = ProviderStatusError(503, 'temporary')
        allowed = decide_retry(error, policy, 10_000, 55_000, 1)
        self.assertTrue(allowed.allowed)
        self.assertEqual(allowed.delay_ms, 1_000)
        self.assertFalse(decide_retry(error, policy, 10_000, 55_000, 0).allowed)
        self.assertFalse(decide_retry(error, policy, 54_500, 55_000, 1).allowed)
        long_wait = ProviderStatusError(429, 'limited', retry_after_seconds=12)
        denied = decide_retry(long_wait, policy, 10_000, 55_000, 1)
        self.assertFalse(denied.allowed)
        self.assertIn('12-second', denied.supplemental)

    def test_legacy_does_not_follow_provider_retry_after(self):
        error = ProviderStatusError(429, 'limited', retry_after_seconds=1)
        self.assertFalse(decide_retry(error, ProcessingPolicy.legacy(), 0, None, 1).allowed)
        self.assertTrue(decide_retry(ProviderStatusError(503, 'temporary'),
                                     ProcessingPolicy.legacy(), 0, None, 1).allowed)


class OperationWindowSnapshotTests(unittest.TestCase):
    def test_legacy_operation_shape_is_unchanged(self):
        operation = RoomOperation('question:1', 'question', 'generating', 1000, 1000)
        self.assertEqual(operation.snapshot(), {
            'id': 'question:1', 'kind': 'question', 'stage': 'generating',
            'started_at_ms': 1000, 'attempt': 1, 'retrying': False,
        })

    def test_window_and_retry_timing_are_optional(self):
        operation = RoomOperation('question:1', 'question', 'generating', 1000, 1000,
                                  window_deadline_ms=46_000, retry_at_ms=2_000)
        self.assertEqual(operation.snapshot()['window_deadline_ms'], 46_000)
        self.assertEqual(operation.snapshot()['retry_at_ms'], 2_000)


class BoundedWorkTests(unittest.IsolatedAsyncioTestCase):
    def make_room(self, policy):
        guest = Player('guest', 'Sam', 1, sockets={object()})
        code = f'PROCESS-{self._testMethodName[-12:]}'
        return guest, Room(code, [ProjectFile('queue.py', 'queue = []')],
                           {guest.token: guest}, phase='generating', generation_id=1,
                           processing_policy=policy)


    def test_answer_window_is_shared_by_interpretation_and_the_following_question(self):
        _guest, room = self.make_room(ProcessingPolicy.standard())
        room.begin_interaction_window(1000)
        self.assertEqual(room.next_processing_deadline(2000), 46_000)
        room.begin_operation(kind='question', operation_id='question:2', stage='generating',
                             now=2000, window_deadline_ms=room.next_processing_deadline(2000))
        self.assertEqual(room.operation.window_deadline_ms, 46_000)

    async def test_shared_window_does_not_restart_when_interpretation_starts_late(self):
        policy = replace(ProcessingPolicy.standard(), window_ms=50)
        guest, room = self.make_room(policy)
        room.phase, room.selected_seat, room.answer_deadline_ms = 'question', 1, 500_000
        room.defense = DefenseSession.start(QUESTION)
        room.submit(guest.token, 'Sam', 1, 0, 'We keep arrival order.', room.defense, now=1000)
        room.begin_interaction_window(1000)
        work = InterpretationWork(room.interpretation_id, room.run_id, room.pending_submission)
        request = capture_interpretation(room, room.pending_submission)
        calls = []

        async def decide(request):
            calls.append(request)
            return SubmissionDecision('answer')

        async def deliver(socket, payload):
            pass

        coordinator = RoomCoordinator(room, RoomWorkflows(
            deliver=deliver, interpretation_request=decide, now=lambda: 1050))
        self.addAsyncCleanup(coordinator.shutdown)
        await asyncio.wait_for(run_interpretation(coordinator, work, request), 1)
        self.assertEqual(calls, [])
        self.assertEqual(room.phase, 'interpretation_retry')
        self.assertIn('limit', room.error)
        self.assertIs(room.pending_submission, work.pending)

    async def test_one_transient_retry_is_shared_with_the_following_question(self):
        guest, room = self.make_room(ProcessingPolicy.standard())
        room.phase, room.selected_seat, room.answer_deadline_ms = 'question', 1, 500_000
        room.defense = DefenseSession.start(QUESTION)
        room.submit(guest.token, 'Sam', 1, 0, 'We keep arrival order.', room.defense, now=1000)
        room.begin_interaction_window(1000)
        work = InterpretationWork(room.interpretation_id, room.run_id, room.pending_submission)
        request = capture_interpretation(room, room.pending_submission)
        interpretation_calls, question_calls = [], []

        async def interpret(request):
            interpretation_calls.append(request)
            if len(interpretation_calls) == 1:
                raise ProviderStatusError(503, 'temporary')
            return SubmissionDecision('answer')

        async def ask(request, files):
            question_calls.append(request)
            raise ProviderStatusError(503, 'temporary')

        async def deliver(socket, payload):
            pass

        async def sleep(seconds):
            pass

        coordinator = RoomCoordinator(room, RoomWorkflows(
            deliver=deliver, interpretation_request=interpret, question_request=ask,
            now=lambda: 1000, sleep=sleep))
        self.addAsyncCleanup(coordinator.shutdown)
        await asyncio.wait_for(run_interpretation(coordinator, work, request), 1)
        for _ in range(100):
            if room.phase == 'retry':
                break
            await asyncio.sleep(0.01)
        self.assertEqual(len(interpretation_calls), 2)
        self.assertEqual(len(question_calls), 1)
        self.assertEqual(room.phase, 'retry')
        self.assertIsNone(room.interaction_deadline_ms)

    async def test_legacy_interpretation_keeps_its_no_retry_behavior(self):
        guest, room = self.make_room(ProcessingPolicy.legacy())
        room.phase, room.selected_seat, room.answer_deadline_ms = 'question', 1, 500_000
        room.defense = DefenseSession.start(QUESTION)
        room.submit(guest.token, 'Sam', 1, 0, 'We keep arrival order.', room.defense, now=1000)
        work = InterpretationWork(room.interpretation_id, room.run_id, room.pending_submission)
        request = capture_interpretation(room, room.pending_submission)
        calls = []

        async def fail(request):
            calls.append(request)
            raise ProviderStatusError(503, 'temporary')

        async def deliver(socket, payload):
            pass

        coordinator = RoomCoordinator(room, RoomWorkflows(
            deliver=deliver, interpretation_request=fail, now=lambda: 1000))
        self.addAsyncCleanup(coordinator.shutdown)
        await asyncio.wait_for(run_interpretation(coordinator, work, request), 1)
        self.assertEqual(len(calls), 1)
        self.assertEqual(room.phase, 'interpretation_retry')

    async def test_legacy_question_retries_one_transient_after_an_answer(self):
        guest = Player('guest', 'Sam', 1, sockets={object()})
        room = Room('PROCESS-LEGACY', [ProjectFile('queue.py', 'queue = []')],
                    {guest.token: guest}, phase='generating', generation_id=1,
                    processing_policy=ProcessingPolicy.legacy())
        room.defense = DefenseSession.start(QUESTION)
        room.defense.submit_answer('We preserve arrival order.', speaker_name='Sam')
        requests, states = [], []

        async def ask(request, files):
            requests.append(request)
            if len(requests) == 1:
                raise ProviderStatusError(503, 'temporary')
            return PanelMove('Security Reviewer', QUESTION)

        async def deliver(socket, payload):
            states.append(payload['state'])

        coordinator = RoomCoordinator(room, RoomWorkflows(
            deliver=deliver, question_request=ask, now=lambda: 1000))
        self.addAsyncCleanup(coordinator.shutdown)
        await coordinator.execute(GenerateQuestion(1, False))
        for _ in range(100):
            if room.phase == 'voting':
                break
            await asyncio.sleep(0.01)
        self.assertEqual(len(requests), 2)
        self.assertEqual(room.phase, 'voting')
        self.assertTrue(any((state.get('operation') or {}).get('stage') == 'retry_wait'
                            for state in states))

    async def test_retry_backoff_that_crosses_the_deadline_does_not_dispatch_again(self):
        policy = replace(ProcessingPolicy.standard(), window_ms=50, default_backoff_ms=20)
        guest, room = self.make_room(policy)
        room.phase, room.selected_seat, room.answer_deadline_ms = 'question', 1, 500_000
        room.defense = DefenseSession.start(QUESTION)
        room.submit(guest.token, 'Sam', 1, 0, 'We keep arrival order.', room.defense, now=1000)
        room.begin_interaction_window(1000)
        work = InterpretationWork(room.interpretation_id, room.run_id, room.pending_submission)
        request = capture_interpretation(room, room.pending_submission)
        clock = [1000]
        calls = []

        async def fail(request):
            calls.append(request)
            raise ProviderStatusError(503, 'temporary')

        async def sleep(seconds):
            clock[0] = 1050

        async def deliver(socket, payload):
            pass

        coordinator = RoomCoordinator(room, RoomWorkflows(
            deliver=deliver, interpretation_request=fail, now=lambda: clock[0], sleep=sleep))
        self.addAsyncCleanup(coordinator.shutdown)
        await asyncio.wait_for(run_interpretation(coordinator, work, request), 1)
        self.assertEqual(len(calls), 1)
        self.assertEqual(room.phase, 'interpretation_retry')
        self.assertIn('limit', room.error)
        self.assertIsNone(room.interaction_deadline_ms)

    async def test_question_result_landing_at_the_deadline_is_discarded(self):
        policy = replace(ProcessingPolicy.standard(), window_ms=50)
        guest, room = self.make_room(policy)
        clock = [1000]

        async def ask(request, files):
            clock[0] = 1050
            return PanelMove('Security Reviewer', QUESTION)

        async def deliver(socket, payload):
            pass

        coordinator = RoomCoordinator(room, RoomWorkflows(
            deliver=deliver, question_request=ask, now=lambda: clock[0]))
        self.addAsyncCleanup(coordinator.shutdown)
        await coordinator.execute(GenerateQuestion(1, True))
        for _ in range(100):
            if room.phase == 'retry':
                break
            await asyncio.sleep(0.01)
        self.assertEqual(room.phase, 'retry')
        self.assertIn('limit', room.error)
        self.assertIsNone(room.defense)
        self.assertIsNone(room.operation)

    async def test_interpretation_result_landing_at_the_deadline_is_not_applied(self):
        policy = replace(ProcessingPolicy.standard(), window_ms=50)
        guest, room = self.make_room(policy)
        room.phase, room.selected_seat, room.answer_deadline_ms = 'question', 1, 500_000
        room.defense = DefenseSession.start(QUESTION)
        room.submit(guest.token, 'Sam', 1, 0, 'We keep arrival order.', room.defense, now=1000)
        work = InterpretationWork(room.interpretation_id, room.run_id, room.pending_submission)
        request = capture_interpretation(room, room.pending_submission)
        clock = [1000]
        decisions = []

        async def decide(request):
            clock[0] = 1050
            decision = SubmissionDecision('clarify', 'Which measured wait?')
            decisions.append(decision)
            return decision

        async def deliver(socket, payload):
            pass

        coordinator = RoomCoordinator(room, RoomWorkflows(
            deliver=deliver, interpretation_request=decide, now=lambda: clock[0]))
        self.addAsyncCleanup(coordinator.shutdown)
        await asyncio.wait_for(run_interpretation(coordinator, work, request), 1)
        self.assertEqual(len(decisions), 1)
        self.assertEqual(room.phase, 'interpretation_retry')
        self.assertIn('limit', room.error)
        self.assertIs(room.pending_submission, work.pending)
        self.assertIsNone(room.operation)

    async def test_question_window_cancels_one_attempt_and_preserves_recovery(self):
        policy = replace(ProcessingPolicy.standard(), window_ms=50, default_backoff_ms=1)
        guest, room = self.make_room(policy)
        requests, states = [], []

        async def ask(request, files):
            requests.append(request)
            await asyncio.sleep(1)
            return PanelMove('Security Reviewer', QUESTION)

        async def deliver(socket, payload):
            states.append(payload['state'])

        coordinator = RoomCoordinator(room, RoomWorkflows(deliver=deliver, question_request=ask,
                                                         now=lambda: 1000))
        self.addAsyncCleanup(coordinator.shutdown)
        await coordinator.execute(GenerateQuestion(1, True))
        for _ in range(100):
            if room.phase == 'retry':
                break
            await asyncio.sleep(0.01)
        self.assertEqual(len(requests), 1)
        self.assertEqual(room.phase, 'retry')
        self.assertIn('limit', room.error)
        self.assertIsNone(room.operation)
        self.assertTrue(states)
        self.assertEqual(coordinator.view(VerifiedActor(guest.token))['question_attempts_left'], 2)

    async def test_question_retry_keeps_the_same_window_and_publishes_backoff(self):
        policy = replace(ProcessingPolicy.standard(), default_backoff_ms=1)
        guest = Player('guest', 'Sam', 1, sockets={object()})
        room = Room('PROCESS-RETRY', [ProjectFile('queue.py', 'queue = []')],
                    {guest.token: guest}, phase='generating', generation_id=2,
                    processing_policy=policy)
        room.defense = DefenseSession.start(QUESTION)
        room.defense.submit_answer('We preserve arrival order.', speaker_name='Sam')
        requests, states, sleeps = [], [], []

        async def ask(request, files):
            requests.append(request)
            if len(requests) == 1:
                raise ProviderStatusError(503, 'temporary')
            return PanelMove('Security Reviewer', GroundedQuestion(
                'Who may change it?', 'queue.py', 1, 'queue = []'))

        async def sleep(seconds):
            sleeps.append(seconds)

        async def deliver(socket, payload):
            states.append(payload['state'])

        coordinator = RoomCoordinator(room, RoomWorkflows(
            deliver=deliver, question_request=ask, now=lambda: 1000, sleep=sleep))
        self.addAsyncCleanup(coordinator.shutdown)
        await coordinator.execute(GenerateQuestion(2, False))
        for _ in range(100):
            if room.phase == 'voting':
                break
            await asyncio.sleep(0.01)
        self.assertEqual(len(requests), 2)
        self.assertEqual(sleeps[0], 0.001)
        retry = [state for state in states if (state.get('operation') or {}).get('stage') == 'retry_wait']
        self.assertTrue(retry)
        self.assertEqual(retry[0]['operation']['window_deadline_ms'], 46_000)
        self.assertEqual(states[-1]['phase'], 'voting')
        self.assertIsNone(states[-1]['operation'])

    async def test_interpretation_window_expires_without_consuming_a_retry(self):
        policy = replace(ProcessingPolicy.standard(), window_ms=50, default_backoff_ms=1)
        guest, room = self.make_room(policy)
        room.phase, room.selected_seat, room.answer_deadline_ms = 'question', 1, 500_000
        room.defense = DefenseSession.start(QUESTION)
        room.submit(guest.token, 'Sam', 1, 0, 'We keep arrival order.', room.defense, now=1000)
        work = InterpretationWork(room.interpretation_id, room.run_id, room.pending_submission)
        request = capture_interpretation(room, room.pending_submission)
        calls = []

        async def slow(request):
            calls.append(request)
            await asyncio.sleep(1)
            return SubmissionDecision('clarify', 'Measured wait?')

        async def deliver(socket, payload):
            pass

        coordinator = RoomCoordinator(room, RoomWorkflows(deliver=deliver,
                                                         interpretation_request=slow,
                                                         now=lambda: 1000))
        self.addAsyncCleanup(coordinator.shutdown)
        await asyncio.wait_for(run_interpretation(coordinator, work, request), 1)
        self.assertEqual(len(calls), 1)
        self.assertEqual(room.phase, 'interpretation_retry')
        self.assertIn('limit', room.error)
        self.assertEqual(room.interpretation_attempts, 1)
        self.assertIs(room.pending_submission, work.pending)
        self.assertIsNone(room.operation)

    async def test_one_transient_interpretation_retry_keeps_identity_and_spends_attempt(self):
        policy = replace(ProcessingPolicy.standard(), default_backoff_ms=1)
        guest, room = self.make_room(policy)
        room.phase, room.selected_seat, room.answer_deadline_ms = 'question', 1, 500_000
        room.defense = DefenseSession.start(QUESTION)
        room.submit(guest.token, 'Sam', 1, 0, 'We keep arrival order.', room.defense, now=1000)
        original_id = room.interpretation_id
        work = InterpretationWork(original_id, room.run_id, room.pending_submission)
        request = capture_interpretation(room, room.pending_submission)
        calls, sleeps = [], []

        async def flaky(request):
            calls.append(request)
            if len(calls) == 1:
                raise ProviderStatusError(503, 'temporary')
            return SubmissionDecision('clarify', 'Which measured wait?')

        async def sleep(seconds):
            sleeps.append(seconds)

        async def deliver(socket, payload):
            pass

        coordinator = RoomCoordinator(room, RoomWorkflows(
            deliver=deliver, interpretation_request=flaky, now=lambda: 1000, sleep=sleep))
        self.addAsyncCleanup(coordinator.shutdown)
        await asyncio.wait_for(run_interpretation(coordinator, work, request), 1)
        self.assertEqual(len(calls), 2)
        self.assertEqual(sleeps, [0.001])
        self.assertEqual(room.interpretation_id, original_id)
        self.assertEqual(room.interpretation_attempts, 2)
        self.assertEqual(room.phase, 'question')
        self.assertIsNone(room.error)
        self.assertIsNone(room.operation)

    async def test_expired_window_never_applies_a_late_result(self):
        policy = replace(ProcessingPolicy.standard(), window_ms=50)
        guest, room = self.make_room(policy)
        room.phase, room.selected_seat, room.answer_deadline_ms = 'question', 1, 500_000
        room.defense = DefenseSession.start(QUESTION)
        room.submit(guest.token, 'Sam', 1, 0, 'We keep arrival order.', room.defense, now=1000)
        work = InterpretationWork(room.interpretation_id, room.run_id, room.pending_submission)
        request = capture_interpretation(room, room.pending_submission)
        decisions = []

        async def late(request):
            await asyncio.sleep(0.1)
            decisions.append(SubmissionDecision('answer'))
            return decisions[-1]

        async def deliver(socket, payload):
            pass

        coordinator = RoomCoordinator(room, RoomWorkflows(deliver=deliver,
                                                         interpretation_request=late,
                                                         now=lambda: 1000))
        self.addAsyncCleanup(coordinator.shutdown)
        await asyncio.wait_for(run_interpretation(coordinator, work, request), 1)
        self.assertEqual(decisions, [])
        self.assertEqual(room.phase, 'interpretation_retry')
        self.assertIs(room.pending_submission, work.pending)

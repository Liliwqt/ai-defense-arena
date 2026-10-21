"""Operation identity, visibility and content-free timing records."""

import asyncio
import os
import subprocess
import sys
import unittest

from backend.defense_session import DefenseSession
from backend.project_files import ProjectFile
from backend.question_generator import GroundedQuestion, SubmissionDecision
from backend.rooms.coordinator import (
    GenerateQuestion, InterpretSubmission, RoomCoordinator, RoomWorkflows, VerifiedActor,
    decode_command,
)
from backend.room_operations import (
    TimingSink, install_timing_sink, record_supplied_usage, reset_timing_sink,
)
from backend.rooms.model import Player, Room


class _Sink(TimingSink):
    def __init__(self):
        self.records = []

    def emit(self, record):
        self.records.append(record)


class RoomOperationTests(unittest.TestCase):
    def setUp(self):
        self.sink = _Sink()
        install_timing_sink(self.sink)
        self.addCleanup(reset_timing_sink)
        self.guest = Player("guest", "Sam", 1, sockets={object()})
        self.room = Room("ROOMA", [ProjectFile("queue.py", "queue = []")],
                         {self.guest.token: self.guest}, phase="generating")

    def test_snapshot_keeps_identity_and_elapsed_anchor_until_finished(self):
        self.room.begin_operation(kind="question", operation_id="question:7",
                                  stage="generating", now=1000)
        first = self.room.snapshot(self.guest, now=4500)["operation"]
        self.assertEqual(first, {
            "id": "question:7", "kind": "question", "stage": "generating",
            "started_at_ms": 1000, "attempt": 1, "retrying": False,
        })

        self.room.retry_operation(5000)
        retried = self.room.snapshot(self.guest, now=6000)["operation"]
        self.assertEqual(retried["started_at_ms"], 1000)
        self.assertEqual(retried["attempt"], 2)
        self.assertTrue(retried["retrying"])

        self.room.finish_operation(6500, "failed", failure_class="TransientProviderError")
        self.assertIsNone(self.room.snapshot(self.guest, now=6500)["operation"])
        stages = [record for record in self.sink.records if record["event"] == "stage"]
        total = next(record for record in self.sink.records if record["event"] == "total")
        self.assertEqual([(item["stage"], item["outcome"], item["duration_ms"]) for item in stages],
                         [("generating", "retrying", 4000), ("retry_wait", "failed", 1500)])
        self.assertEqual(total["duration_ms"], 5500)
        self.assertEqual(total["failure_class"], "TransientProviderError")

    def test_retry_wait_is_recorded_separately_from_resumed_generation(self):
        self.room.begin_operation(kind="question", operation_id="question:11",
                                  stage="generating", now=1000)
        self.room.retry_operation(2000)
        self.room.resume_operation(3000)
        self.room.finish_operation(4000, "succeeded")
        stages = [record for record in self.sink.records if record["event"] == "stage"]
        self.assertEqual([(item["stage"], item["outcome"], item["duration_ms"]) for item in stages],
                         [("generating", "retrying", 1000),
                          ("retry_wait", "retried", 1000),
                          ("generating", "succeeded", 1000)])

    def test_operation_is_hidden_once_its_phase_no_longer_matches(self):
        self.room.begin_operation(kind="question", operation_id="question:7",
                                  stage="generating", now=1000)
        self.room.phase = "retry"
        self.assertIsNone(self.room.snapshot(self.guest, now=2000)["operation"])
        self.room.clear_operation()
        self.assertIsNone(self.room.operation)

    def test_stage_progress_records_each_known_stage_once(self):
        self.room = Room("ROOMA", [ProjectFile("queue.py", "queue = []")],
                         {self.guest.token: self.guest}, phase="lobby",
                         research_planning_status="planning")
        self.room.begin_operation(kind="mapping", operation_id="mapping:3",
                                  stage="preparing", now=1000)
        self.room.advance_operation("mapping", 1600)
        self.room.advance_operation("validating", 2500)
        self.room.advance_operation("validating", 2600)
        self.room.finish_operation(3000, "succeeded")
        stages = [record for record in self.sink.records if record["event"] == "stage"]
        self.assertEqual([(item["stage"], item["duration_ms"]) for item in stages],
                         [("preparing", 600), ("mapping", 900), ("validating", 500)])
        self.assertEqual(self.room.snapshot(self.guest, now=3000)["operation"], None)

    def test_usage_is_allowlisted_and_unknown_cost_stays_absent(self):
        self.room.begin_operation(kind="question", operation_id="question:8",
                                  stage="generating", now=1000)
        self.room.finish_operation(2500, "succeeded", usage={
            "input_tokens": 12, "output_tokens": 3, "reasoning_tokens": 0,
            "cost_nano": None, "model": "provider/model", "prompt": "private paper text",
            "answer": "private answer", "api_key": "secret",
        })
        records = [record for record in self.sink.records
                   if record["event"] in {"stage", "total"}]
        self.assertEqual(len(records), 2)
        for record in records:
            self.assertNotIn("prompt", record)
            self.assertNotIn("answer", record)
            self.assertNotIn("api_key", record)
            self.assertNotIn("cost_nano", record)
            self.assertEqual(record["input_tokens"], 12)
            self.assertEqual(record["output_tokens"], 3)
            self.assertEqual(record["reasoning_tokens"], 0)
            self.assertEqual(record["model"], "provider/model")

    def test_failed_result_without_exception_has_no_invented_failure_class(self):
        self.room.begin_operation(kind="question", operation_id="question:9",
                                  stage="generating", now=1000)
        self.room.finish_operation(2000, "failed")
        total = next(record for record in self.sink.records if record["event"] == "total")
        self.assertNotIn("failure_class", total)

    def test_default_sink_survives_standard_uvicorn_logging(self):
        env = {**os.environ}
        env.pop("OPERATION_TIMING_LOG", None)
        script = """
import logging.config
from uvicorn.config import LOGGING_CONFIG
logging.config.dictConfig(LOGGING_CONFIG)
from backend.room_operations import RoomOperation, record_stage
record_stage(RoomOperation('question:1', 'question', 'generating', 1000, 1000),
             ended_at_ms=1400, outcome='succeeded', usage={'input_tokens': 7})
"""
        result = subprocess.run([sys.executable, "-c", script], cwd=os.getcwd(),
                                env=env, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('"kind":"question"', result.stderr)
        self.assertIn('"duration_ms":400', result.stderr)
        self.assertIn('"input_tokens":7', result.stderr)

    def test_supplied_provider_usage_reaches_the_finished_record(self):
        self.room.begin_operation(kind="question", operation_id="question:10",
                                  stage="generating", now=1000)

        async def provider():
            await asyncio.to_thread(record_supplied_usage, {
                "prompt_tokens": 500, "completion_tokens": 300,
                "completion_tokens_details": {"reasoning_tokens": 7},
                "cost": 0.0005,
            }, model="provider/model")
            await asyncio.to_thread(record_supplied_usage, {
                "prompt_tokens": 20, "completion_tokens": 10,
                "completion_tokens_details": {"reasoning_tokens": 2},
                "cost": 0.0001,
            }, model="provider/model")
            self.room.finish_operation(2000, "succeeded")

        asyncio.run(provider())
        total = next(record for record in self.sink.records if record["event"] == "total")
        self.assertEqual(total["input_tokens"], 520)
        self.assertEqual(total["output_tokens"], 310)
        self.assertEqual(total["reasoning_tokens"], 9)
        self.assertEqual(total["cost_nano"], 600_000)
        self.assertEqual(total["model"], "provider/model")


class ConcurrentUsageTests(unittest.IsolatedAsyncioTestCase):
    async def test_same_public_id_in_two_rooms_keeps_usage_separate(self):
        sink = _Sink()
        install_timing_sink(sink)
        self.addCleanup(reset_timing_sink)
        a_ready, b_ready, a_done = (asyncio.Event() for _ in range(3))

        async def first():
            room = Room("AAAAA", [], {}, phase="generating")
            room.begin_operation(kind="question", operation_id="question:1",
                                 stage="generating", now=1000)
            record_supplied_usage({"prompt_tokens": 10}, model="model-a")
            a_ready.set()
            await b_ready.wait()
            room.finish_operation(2000, "succeeded")
            a_done.set()

        async def second():
            await a_ready.wait()
            room = Room("BBBBB", [], {}, phase="generating")
            room.begin_operation(kind="question", operation_id="question:1",
                                 stage="generating", now=1000)
            record_supplied_usage({"prompt_tokens": 20}, model="model-b")
            b_ready.set()
            await a_done.wait()
            record_supplied_usage({"completion_tokens": 5}, model="model-b")
            room.finish_operation(3000, "succeeded")

        await asyncio.gather(first(), second())
        totals = [record for record in sink.records if record["event"] == "total"]
        self.assertEqual([(r.get("input_tokens"), r.get("model")) for r in totals],
                         [(10, "model-a"), (20, "model-b")])
        self.assertEqual(totals[1]["output_tokens"], 5)

    async def test_cancellation_and_reused_public_id_ignore_late_usage(self):
        sink = _Sink()
        install_timing_sink(sink)
        self.addCleanup(reset_timing_sink)
        a_ready, b_ready, cancelled, late_done = (asyncio.Event() for _ in range(4))
        room_a = Room("AAAAA", [], {}, phase="generating")

        async def stale_provider():
            room_a.begin_operation(kind="mapping", operation_id="mapping:1",
                                   stage="mapping", now=1000)
            record_supplied_usage({"prompt_tokens": 10})
            a_ready.set()
            await cancelled.wait()
            record_supplied_usage({"prompt_tokens": 999})
            late_done.set()

        async def other_room():
            await a_ready.wait()
            room = Room("BBBBB", [], {}, phase="lobby")
            room.begin_operation(kind="mapping", operation_id="mapping:1",
                                 stage="mapping", now=1000)
            record_supplied_usage({"prompt_tokens": 20})
            b_ready.set()
            await late_done.wait()
            record_supplied_usage({"completion_tokens": 5})
            room.finish_operation(3000, "succeeded")

        async def replace_cancelled():
            await b_ready.wait()
            room_a.clear_operation()
            room_a.begin_operation(kind="mapping", operation_id="mapping:1",
                                   stage="mapping", now=2000)
            record_supplied_usage({"prompt_tokens": 30})
            cancelled.set()
            await late_done.wait()
            room_a.finish_operation(4000, "succeeded")

        await asyncio.gather(stale_provider(), other_room(), replace_cancelled())
        totals = [record for record in sink.records if record["event"] == "total"]
        self.assertEqual(sorted(record["input_tokens"] for record in totals), [20, 30])
        self.assertEqual(next(r for r in totals if r["input_tokens"] == 20)["output_tokens"], 5)


class InterpretationOperationTests(unittest.IsolatedAsyncioTestCase):
    async def test_snapshot_shows_in_flight_interpretation_then_stops_on_result(self):
        guest = Player("guest", "Sam", 1, sockets={object()})
        room = Room("ROOMA", [ProjectFile("queue.py", "queue = []")], {guest.token: guest},
                    phase="question", selected_seat=1, answer_deadline_ms=61000)
        room.defense = DefenseSession.start(
            GroundedQuestion("How are arrivals ordered?", "queue.py", 1, "queue = []"))
        started, release, published, operation_published, never = (asyncio.Event() for _ in range(5))
        states = []

        async def interpret(request):
            started.set()
            await release.wait()
            return SubmissionDecision("clarify", "Which arrival will be handled first?")

        async def deliver(socket, payload):
            state = payload["state"]
            states.append(state)
            if state["operation"] is not None:
                operation_published.set()
            if state["phase"] == "question" and state["turns"][0]["clarifications"]:
                published.set()

        async def sleep(seconds):
            await never.wait()

        coordinator = RoomCoordinator(room, RoomWorkflows(
            deliver=deliver, interpretation_request=interpret, now=lambda: 1000, sleep=sleep,
        ))
        self.addAsyncCleanup(coordinator.shutdown)
        actor = VerifiedActor(guest.token)
        accepted = await coordinator.execute(decode_command(
            {"type": "submit_answer", "turn": 0, "answer": "Please explain."}), actor)
        self.assertTrue(accepted.accepted)
        await asyncio.wait_for(started.wait(), 1)
        await asyncio.wait_for(operation_published.wait(), 1)
        published_operation = next(state["operation"] for state in states
                                   if state["operation"] is not None)
        self.assertEqual(published_operation["kind"], "interpretation")
        await coordinator.execute(InterpretSubmission(room.interpretation_id))
        in_flight = coordinator.view(actor)["operation"]
        self.assertEqual(in_flight, {
            "id": f"interpretation:{room.interpretation_id}", "kind": "interpretation",
            "stage": "reviewing_answer", "started_at_ms": 1000, "attempt": 1, "retrying": False,
        })
        release.set()
        await asyncio.wait_for(published.wait(), 1)
        self.assertIsNone(coordinator.view(actor)["operation"])
        self.assertEqual(len(states[-1]["turns"][0]["clarifications"]), 1)


class QuestionOperationPublicationTests(unittest.IsolatedAsyncioTestCase):
    async def test_question_operation_start_is_published_before_inference(self):
        guest = Player("guest", "Sam", 1, sockets={object()})
        room = Room("ROOMA", [ProjectFile("queue.py", "queue = []")], {guest.token: guest},
                    phase="generating", generation_id=1)
        started, release, operation_published, finished = (asyncio.Event() for _ in range(4))
        states = []

        async def ask(request, files):
            started.set()
            await release.wait()
            return GroundedQuestion("How are arrivals ordered?", "queue.py", 1, "queue = []")

        async def deliver(socket, payload):
            state = payload["state"]
            states.append(state)
            if state["operation"] is not None:
                operation_published.set()
            if state["phase"] == "voting" and state["operation"] is None:
                finished.set()

        coordinator = RoomCoordinator(room, RoomWorkflows(
            deliver=deliver, question_request=ask, now=lambda: 1000,
            sleep=lambda seconds: asyncio.Event().wait(),
        ))
        self.addAsyncCleanup(coordinator.shutdown)
        await coordinator.execute(GenerateQuestion(1, True))
        await asyncio.wait_for(started.wait(), 1)
        await asyncio.wait_for(operation_published.wait(), 1)
        published = next(state["operation"] for state in states
                         if state["operation"] is not None)
        self.assertEqual(published, {
            "id": "question:1", "kind": "question", "stage": "generating",
            "started_at_ms": 1000, "attempt": 1, "retrying": False,
        })
        release.set()
        await asyncio.wait_for(finished.wait(), 1)
        self.assertIsNone(states[-1]["operation"])


class CoachingCompletionTimingTests(unittest.IsolatedAsyncioTestCase):
    async def test_failed_batch_is_not_overwritten_by_later_successful_batch(self):
        from types import SimpleNamespace
        from unittest.mock import patch
        from backend.coaching_progress import CoachingInput, CoachingProgress
        from backend.question_generator import AnsweredQuestion, CoachingReport
        from backend.rooms.coaching import run_progressive_coaching
        from tests.research_coaching_fixtures import with_cards

        sink = _Sink()
        install_timing_sink(sink)
        self.addCleanup(reset_timing_sink)
        clock = [1000]
        history = tuple(AnsweredQuestion("Methodology Reviewer", "Why the pilot?", "A bounded pilot.")
                        for _ in range(7))
        room = Room("BATCH", [], {}, phase="complete", feedback_status="generating",
                    feedback_generation_id=1, settled=False)
        room.coaching_progress = CoachingProgress(CoachingInput((), history, None, "research", "proposal"))
        fail_once = [True]
        published_operations = []

        async def coach(request):
            clock[0] += 100
            if request.section_turns == (3, 4, 5) and fail_once[0]:
                fail_once[0] = False
                raise ValueError("Synthetic middle-batch failure")
            return with_cards(CoachingReport("The team described the pilot.", [], [], "Explain the limits."),
                              history, overview_only=request.overview_only, section_turns=request.section_turns)

        async def publish():
            published_operations.append(room.operation.snapshot() if room.operation else None)

        owner = SimpleNamespace(_room=room, _workflows=SimpleNamespace(
            now=lambda: clock[0], coaching_request=coach), _coaching_current=lambda work: True,
            _publish=publish, _clear_clock=lambda: None)
        with patch("backend.rooms.coaching.live_mode", return_value=False):
            await run_progressive_coaching(owner, SimpleNamespace(generation_id=1, run_id=None))
        stages = [record for record in sink.records if record["event"] == "stage"]
        self.assertEqual([(record["stage"], record["outcome"], record["duration_ms"]) for record in stages],
                         [("overview", "succeeded", 100), ("answers", "succeeded", 100),
                          ("answers", "failed", 100), ("answers", "succeeded", 100)])
        self.assertEqual(sink.records[-1]["failure_class"], "ValueError")
        self.assertEqual(sink.records[-1]["outcome"], "failed")
        self.assertFalse(room.settled)
        room.coaching_progress.retry()
        room.feedback_status = "generating"
        published_operations.clear()
        with patch("backend.rooms.coaching.live_mode", return_value=False):
            await run_progressive_coaching(owner, SimpleNamespace(generation_id=2, run_id=None))
        self.assertEqual(published_operations[0]["stage"], "answers")
        self.assertTrue(published_operations[0]["retrying"])
        self.assertTrue(room.settled)

    async def test_failed_overview_is_a_failed_generation_stage_without_saving(self):
        from types import SimpleNamespace
        from unittest.mock import patch
        from backend.coaching_progress import CoachingInput, CoachingProgress
        from backend.rooms.coaching import run_progressive_coaching

        sink = _Sink()
        install_timing_sink(sink)
        self.addCleanup(reset_timing_sink)
        clock = [1000]
        room = Room("SYNTH", [], {}, phase="complete", feedback_status="generating",
                    feedback_generation_id=2)
        room.coaching_progress = CoachingProgress(CoachingInput((), (), None, "research", "proposal"))
        published_operations = []

        async def fail(request):
            clock[0] += 3000
            raise ValueError("Synthetic provider failure")

        async def publish():
            published_operations.append(room.operation.snapshot() if room.operation else None)

        owner = SimpleNamespace(_room=room, _workflows=SimpleNamespace(
            now=lambda: clock[0], coaching_request=fail), _coaching_current=lambda work: True,
            _publish=publish)
        with patch("backend.rooms.coaching.has_discussion", return_value=True), \
             patch("backend.rooms.coaching.live_mode", return_value=False):
            await run_progressive_coaching(owner, SimpleNamespace(generation_id=2, run_id=None))
        self.assertFalse(published_operations[0]["retrying"])
        stages = [record for record in sink.records if record["event"] == "stage"]
        self.assertEqual([(record["stage"], record["outcome"], record["duration_ms"])
                          for record in stages], [("overview", "failed", 3000)])
        self.assertEqual(stages[0]["failure_class"], "ValueError")
        self.assertEqual(sink.records[-1]["outcome"], "failed")

    async def test_progressive_completion_includes_validation_and_storage_time(self):
        from unittest.mock import patch
        from backend.defense_session import DefenseTurn, ResearchDefenseSession
        from backend.question_generator import CoachingReport, GroundedQuestion
        from backend.rooms import coaching as coaching_workflow
        from backend.rooms.commands import GenerateCoaching
        from tests.research_coaching_fixtures import with_cards
        from tests.test_planning_coaching_coordination import completed_room
        from tests.test_research_coverage import plan

        sink = _Sink()
        install_timing_sink(sink)
        self.addCleanup(reset_timing_sink)
        clock = [1000]
        room = completed_room({"id": "synthetic-account"})
        room.defense_type = "research"
        session = ResearchDefenseSession.create(plan(4), 8, "research", "proposal")
        session.turns = [DefenseTurn("Methodology Reviewer",
                                     GroundedQuestion("Why the pilot?", "paper.md", 1, "Campus pilot."),
                                     answer="The pilot is bounded.", speaker_name="Sam",
                                     topic_id="topic-1")]
        session.end()
        room.defense = session
        ready = asyncio.Event()

        async def coach(request):
            report = with_cards(CoachingReport("The team discussed scope.", [], [],
                                               "Practice the limits.",
                                               closing="Review those limits."),
                                request.history, overview_only=request.overview_only,
                                section_turns=request.section_turns)
            return report

        async def deliver(socket, payload):
            if payload["state"]["feedback_status"] == "ready":
                ready.set()

        coordinator = RoomCoordinator(room, RoomWorkflows(
            coaching_request=coach, deliver=deliver, now=lambda: clock[0]))
        self.addAsyncCleanup(coordinator.shutdown)
        original = coaching_workflow.validate_complete

        def finish_storage(*args, **kwargs):
            clock[0] += 7000
            return original(*args, **kwargs)

        with patch.object(coaching_workflow, "validate_complete", finish_storage):
            await coordinator.execute(GenerateCoaching(1))
            await asyncio.wait_for(ready.wait(), 2)
        total = next(record for record in sink.records if record["event"] == "total")
        saving = next(record for record in sink.records
                      if record["event"] == "stage" and record["stage"] == "saving_completion")
        self.assertEqual(saving["duration_ms"], 7000)
        self.assertEqual(total["duration_ms"], 7000)
        self.assertEqual(room.terminal_ms, 8000)

    async def test_section_failure_class_reaches_the_completion_record(self):
        from backend.defense_session import DefenseTurn, ResearchDefenseSession
        from backend.question_generator import CoachingReport, GroundedQuestion
        from backend.rooms.commands import GenerateCoaching
        from tests.research_coaching_fixtures import with_cards
        from tests.test_planning_coaching_coordination import completed_room
        from tests.test_research_coverage import plan

        sink = _Sink()
        install_timing_sink(sink)
        self.addCleanup(reset_timing_sink)
        room = completed_room({"id": "synthetic-account"})
        room.defense_type = "research"
        session = ResearchDefenseSession.create(plan(4), 8, "research", "proposal")
        session.turns = [DefenseTurn("Methodology Reviewer",
                                     GroundedQuestion("Why the pilot?", "paper.md", 1, "Campus pilot."),
                                     answer="The pilot is bounded.", speaker_name="Sam",
                                     topic_id="topic-1")]
        session.end()
        room.defense = session
        failed = asyncio.Event()

        async def coach(request):
            if request.section_turns is not None:
                raise ValueError("Synthetic section failure")
            return with_cards(CoachingReport("The team discussed scope.", [], [],
                                             "Practice the limits.",
                                             closing="Review those limits."),
                              request.history, overview_only=True)

        async def deliver(socket, payload):
            if payload["state"]["feedback_status"] == "failed":
                failed.set()

        coordinator = RoomCoordinator(room, RoomWorkflows(
            coaching_request=coach, deliver=deliver, now=lambda: 1000))
        self.addAsyncCleanup(coordinator.shutdown)
        await coordinator.execute(GenerateCoaching(1))
        await asyncio.wait_for(failed.wait(), 2)
        total = next(record for record in sink.records if record["event"] == "total")
        self.assertEqual(total["failure_class"], "ValueError")
        self.assertEqual(room.coaching_progress.sections[1].failure_class, "ValueError")
        failed_stages = [record for record in sink.records
                         if record["event"] == "stage" and record["outcome"] == "failed"]
        self.assertEqual([(record["stage"], record["failure_class"]) for record in failed_stages],
                         [("answers", "ValueError")])
        self.assertNotIn("saving_completion", [record["stage"] for record in sink.records])


if __name__ == "__main__":
    unittest.main()

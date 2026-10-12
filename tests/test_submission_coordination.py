"""Observable submission coordination with controlled AI completion and clocks."""

import asyncio
import os
import unittest
from unittest.mock import patch

from backend.defense_session import DefenseSession
from backend.project_files import ProjectFile
from backend.question_generator import GroundedQuestion, SubmissionDecision, PanelMove, ProbeRequest
from backend.rooms.model import Player, Room
from backend.timed_turn import PendingSubmission
from backend.rooms.coordinator import (
    RoomCoordinator, RoomWorkflows, VerifiedActor, decode_command, InterpretSubmission, CatchUpDeadline,
)


class SubmissionCoordinationTests(unittest.IsolatedAsyncioTestCase):
    async def test_recovery_cannot_accept_or_admit_after_deadline_between_locks(self):
        for action in ("use_pending_as_answer", "retry_interpretation"):
            with self.subTest(action=action):
                guest = Player("guest", "Sam", 1, sockets={object()})
                room = Room("RACE", [ProjectFile("queue.py", "queue = []")], {guest.token: guest},
                            phase="interpretation_retry", selected_seat=1, answer_deadline_ms=1000,
                            interpretation_attempts=1, error="Failed interpretation")
                room.defense = DefenseSession.start(GroundedQuestion("Why?", "queue.py", 1, "queue = []"))
                room.pending_submission = PendingSubmission(0, guest.token, guest.name, 1, "Saved text.", 1)
                times, never, requests = iter([999, 1000]), asyncio.Event(), []

                async def deliver(socket, payload):
                    pass

                async def ask(request, files):
                    await never.wait()

                async def interpret(request):
                    requests.append(request)
                    return SubmissionDecision("answer")

                coordinator = RoomCoordinator(room, RoomWorkflows(
                    deliver=deliver, question_request=ask, interpretation_request=interpret,
                    now=lambda: next(times, 1000),
                ))
                self.addAsyncCleanup(coordinator.shutdown)
                actor = VerifiedActor(guest.token)
                result = await coordinator.execute(decode_command({"type": action}), actor)
                self.assertFalse(result.accepted)
                self.assertEqual(result.error, "Answer time is over.")
                snapshot = coordinator.view(actor)
                self.assertTrue(snapshot["turns"][0]["timed_out"])
                self.assertIsNone(snapshot["turns"][0]["answer"])
                self.assertEqual(snapshot["interpretation_attempts_left"], 5)
                self.assertEqual(requests, [])

    async def test_duplicate_interpretation_keeps_one_request_and_same_question_clarification(self):
        guest = Player("guest", "Sam", 1, sockets={object()})
        room = Room("ROOMA", [ProjectFile("queue.py", "queue = []")], {guest.token: guest},
                    phase="question", selected_seat=1, answer_deadline_ms=61000)
        question = GroundedQuestion("How are arrivals ordered?", "queue.py", 1, "queue = []")
        room.defense = DefenseSession.start(question)
        actor = VerifiedActor(guest.token)
        started, release, published, never = (asyncio.Event() for _ in range(4))
        requests, states = [], []
        now = [1000]

        async def interpret(request):
            requests.append(request)
            started.set()
            await release.wait()
            return SubmissionDecision("clarify", "Which arrival will be handled first?")

        async def deliver(socket, payload):
            state = payload["state"]
            states.append(state)
            if state["phase"] == "question":
                published.set()

        async def sleep(seconds):
            await never.wait()

        coordinator = RoomCoordinator(room, RoomWorkflows(
            deliver=deliver, interpretation_request=interpret, now=lambda: now[0], sleep=sleep,
        ))
        self.addAsyncCleanup(coordinator.shutdown)
        command = decode_command({"type": "submit_answer", "turn": 0, "answer": "Please explain."})
        self.assertTrue((await coordinator.execute(command, actor)).accepted)
        await asyncio.wait_for(started.wait(), 1)
        duplicate = await coordinator.execute(command, actor)
        self.assertFalse(duplicate.accepted)
        await coordinator.execute(InterpretSubmission(room.interpretation_id))
        self.assertEqual(len(requests), 1)
        self.assertEqual(requests[0].pending.name, "Sam")
        self.assertEqual(requests[0].question, question)
        self.assertEqual(coordinator.view(actor)["my_pending_submission"], "Please explain.")
        now[0] += 30000
        release.set()
        await asyncio.wait_for(published.wait(), 1)
        snapshot = states[-1]
        self.assertEqual(len(snapshot["turns"]), 1)
        self.assertIsNone(snapshot["turns"][0]["answer"])
        self.assertEqual(snapshot["answer_deadline_ms"], 91000)
        self.assertEqual(len(snapshot["turns"][0]["clarifications"]), 1)
        self.assertEqual(snapshot["selected_seat"], 1)

    async def test_obsolete_failure_cannot_change_another_run_or_its_pending_input(self):
        guest = Player("guest", "Sam", 1, sockets={object()})
        room = Room("ROOMB", [ProjectFile("queue.py", "queue = []")], {guest.token: guest},
                    phase="question", selected_seat=1, answer_deadline_ms=61000, run_id="old")
        room.defense = DefenseSession.start(GroundedQuestion("Why?", "queue.py", 1, "queue = []"))
        actor = VerifiedActor(guest.token)
        started, release, finished, never = (asyncio.Event() for _ in range(4))
        states = []

        async def interpret(request):
            started.set()
            await release.wait()
            finished.set()
            raise ValueError("Obsolete provider failure")

        async def deliver(socket, payload):
            state = payload["state"]
            states.append(state)

        async def sleep(seconds):
            await never.wait()

        coordinator = RoomCoordinator(room, RoomWorkflows(
            deliver=deliver, interpretation_request=interpret, now=lambda: 1000, sleep=sleep,
        ))
        self.addAsyncCleanup(coordinator.shutdown)
        await coordinator.execute(decode_command({"type": "submit_answer", "turn": 0, "answer": "Old answer."}), actor)
        await asyncio.wait_for(started.wait(), 1)
        # Run identity is independent of the operation counter; even a retained
        # pending object must not authorize a result from an earlier run.
        async with room.lock:
            room.run_id = "new"
        before = coordinator.view(actor)
        release.set()
        await asyncio.wait_for(finished.wait(), 1)
        await asyncio.sleep(0)
        self.assertEqual(coordinator.view(actor), before)
        self.assertEqual(len(states), 1)

    async def test_timeout_and_late_failure_resolve_one_unanswered_turn(self):
        guest = Player("guest", "Sam", 1, sockets={object()})
        room = Room("ROOMC", [ProjectFile("queue.py", "queue = []")], {guest.token: guest},
                    phase="question", selected_seat=1, answer_deadline_ms=2000)
        room.defense = DefenseSession.start(GroundedQuestion("Why?", "queue.py", 1, "queue = []"))
        actor = VerifiedActor(guest.token)
        started, release, published, never = (asyncio.Event() for _ in range(4))
        now, histories = [1000], []

        async def interpret(request):
            started.set()
            await release.wait()
            raise ValueError("Too late")

        async def ask(request, files):
            histories.append(request.session.answered_history())
            return PanelMove("Security Reviewer", GroundedQuestion("Who may change it?", "queue.py", 1, "queue = []"))

        async def deliver(socket, payload):
            state = payload["state"]
            if state["phase"] == "voting":
                published.set()

        async def sleep(seconds):
            await never.wait()

        coordinator = RoomCoordinator(room, RoomWorkflows(
            deliver=deliver, interpretation_request=interpret, question_request=ask,
            now=lambda: now[0], sleep=sleep,
        ))
        self.addAsyncCleanup(coordinator.shutdown)
        with patch.dict(os.environ, {"AI_PAUSE_SECONDS": "1"}):
            await coordinator.execute(decode_command({"type": "submit_answer", "turn": 0, "answer": "Late answer."}), actor)
            await asyncio.wait_for(started.wait(), 1)
            now[0] = 3000
            release.set()
            await coordinator.execute(CatchUpDeadline())
            await asyncio.wait_for(published.wait(), 1)
        snapshot = coordinator.view(actor)
        self.assertEqual(len(histories), 1)
        self.assertTrue(histories[0][0].timed_out)
        self.assertIsNone(histories[0][0].answer)
        self.assertEqual(len(snapshot["turns"]), 2)
        self.assertTrue(snapshot["turns"][0]["timed_out"])
        self.assertIsNone(snapshot["error"])
        self.assertEqual(snapshot["vote_deadline_ms"], 18000)

    async def test_failed_probe_reply_uses_saved_text_without_replacing_original_answer(self):
        guest = Player("guest", "Sam", 1, sockets={object()})
        observer = Player("observer", "Lee", 2, sockets={object()})
        room = Room("ROOMD", [ProjectFile("queue.py", "queue = []")],
                    {guest.token: guest, observer.token: observer}, phase="question",
                    selected_seat=1, answer_deadline_ms=61000)
        question = GroundedQuestion("How are arrivals ordered?", "queue.py", 1, "queue = []")
        room.defense = DefenseSession.start(question)
        actor, watching = VerifiedActor(guest.token), VerifiedActor(observer.token)
        probed, failed, advanced, never = (asyncio.Event() for _ in range(4))
        requests = []
        now = [1000]

        async def interpret(request):
            requests.append(request)
            if len(requests) == 1:
                return SubmissionDecision("probe", probe=ProbeRequest("Which arrival goes first?"))
            raise ValueError("Offline provider failure")

        async def ask(request, files):
            return PanelMove("Security Reviewer", GroundedQuestion("Who may change it?", "queue.py", 1, "queue = []"))

        async def deliver(socket, payload):
            state = payload["state"]
            if state["phase"] == "probe":
                probed.set()
            if state["phase"] == "interpretation_retry":
                failed.set()
            if state["phase"] == "voting":
                advanced.set()

        async def sleep(seconds):
            await never.wait()

        coordinator = RoomCoordinator(room, RoomWorkflows(
            deliver=deliver, interpretation_request=interpret, question_request=ask,
            now=lambda: now[0], sleep=sleep,
        ))
        self.addAsyncCleanup(coordinator.shutdown)
        await coordinator.execute(decode_command({"type": "submit_answer", "turn": 0,
                                                 "answer": "We preserve arrival order."}), actor)
        await asyncio.wait_for(probed.wait(), 1)
        first = coordinator.view(actor)["turns"][0]
        self.assertEqual(first["answer"], "We preserve arrival order.")
        self.assertEqual(first["answered_by"], "Sam")
        probe_id = first["probe"]["id"]
        now[0] = 2000
        await coordinator.execute(decode_command({"type": "submit_probe_reply", "turn": 0,
            "probe_id": probe_id, "answer": "The earliest arrival goes first."}), actor)
        await asyncio.wait_for(failed.wait(), 1)
        self.assertEqual(requests[1].original_answer, "We preserve arrival order.")
        self.assertEqual(requests[1].original_speaker_name, "Sam")
        self.assertEqual(requests[1].probe.id, probe_id)
        self.assertIsNone(coordinator.view(watching)["my_pending_submission"])
        rejected = await coordinator.execute(decode_command({"type": "use_pending_as_answer"}), watching)
        self.assertFalse(rejected.accepted)
        accepted = await coordinator.execute(decode_command({"type": "use_pending_as_answer"}), actor)
        self.assertTrue(accepted.accepted)
        await asyncio.wait_for(advanced.wait(), 1)
        self.assertEqual(len(requests), 2)
        for identity in (actor, watching):
            turn = coordinator.view(identity)["turns"][0]
            self.assertEqual(turn["answer"], "We preserve arrival order.")
            self.assertEqual(turn["question"], "How are arrivals ordered?")
            self.assertEqual(turn["evidence_text"], "queue = []")
            self.assertEqual(turn["probe"]["reply"], "The earliest arrival goes first.")
            self.assertEqual(turn["probe"]["speaker_name"], "Sam")

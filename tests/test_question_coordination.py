"""Controlled AI completions at the room command/view boundary."""

import asyncio
import unittest

from backend.rooms.coordinator import CatchUpDeadline, GenerateQuestion, RoomCoordinator, RoomWorkflows, VerifiedActor
from backend.rooms.model import Player, Room
from backend.project_files import ProjectFile
from backend.question_generator import GroundedQuestion, PanelMove
from backend.defense_session import DefenseSession


class QuestionCoordinationTests(unittest.IsolatedAsyncioTestCase):
    async def test_invalid_candidate_recovers_once_without_replaying_answer(self):
        guest = Player("guest", "Sam", 1)
        room = Room("ROOMA", [ProjectFile("queue.py", "queue = []")], {guest.token: guest},
                    phase="generating", generation_id=2)
        question = GroundedQuestion("Why a queue?", "queue.py", 1, "queue = []")
        room.defense = DefenseSession.start(question)
        room.defense.submit_answer("We preserve arrival order.", speaker_name="Sam")
        requests, states = [], []
        published, never = asyncio.Event(), asyncio.Event()
        actor = VerifiedActor(guest.token)

        async def ask(request, files):
            requests.append(request.session.answered_history())
            role = "Unknown reviewer" if len(requests) == 1 else "Security Reviewer"
            return PanelMove(role, GroundedQuestion("Who may change it?", "queue.py", 1, "queue = []"))

        async def sleep(seconds):
            if seconds != 1:
                await never.wait()

        async def publish(state):
            states.append(coordinator.view(actor))
            if state.phase == "voting":
                published.set()

        coordinator = RoomCoordinator(room, RoomWorkflows(publish=publish, question_request=ask,
                                                         now=lambda: 1000, sleep=sleep))
        self.addAsyncCleanup(coordinator.shutdown)
        await coordinator.execute(GenerateQuestion(2, False))
        await asyncio.wait_for(published.wait(), 2)
        self.assertEqual(len(requests), 2)
        self.assertEqual([history[0].answer for history in requests], ["We preserve arrival order."] * 2)
        self.assertTrue(states[0]["question_retrying"])
        self.assertEqual(states[0]["turns"][0]["answer"], "We preserve arrival order.")
        self.assertEqual(len(states[-1]["turns"]), 2)
        self.assertFalse(states[-1]["question_retrying"])

    async def test_racing_deadline_commands_record_one_timeout_and_one_next_question(self):
        guest = Player("guest", "Sam", 1, sockets={object()})
        room = Room("ROOMA", [ProjectFile("queue.py", "queue = []")], {guest.token: guest},
                    phase="question", generation_id=1, selected_seat=1, answer_deadline_ms=1000)
        room.defense = DefenseSession.start(GroundedQuestion("Why?", "queue.py", 1, "queue = []"))
        release, started, published, never = (asyncio.Event() for _ in range(4))
        requests = []

        async def ask(request, files):
            requests.append(request.session.answered_history())
            started.set()
            await release.wait()
            return PanelMove("Security Reviewer", GroundedQuestion("Who may change it?", "queue.py", 1, "queue = []"))

        async def publish(state):
            if state.phase == "voting":
                published.set()

        async def sleep(seconds):
            await never.wait()

        coordinator = RoomCoordinator(room, RoomWorkflows(publish=publish, question_request=ask,
                                                         now=lambda: 1000, sleep=sleep))
        self.addAsyncCleanup(coordinator.shutdown)
        old_clock = room.clock_id
        await asyncio.gather(coordinator.execute(CatchUpDeadline(old_clock)),
                             coordinator.execute(CatchUpDeadline(old_clock)))
        await asyncio.wait_for(started.wait(), 2)
        self.assertEqual(len(requests), 1)
        self.assertTrue(requests[0][0].timed_out)
        self.assertIsNone(requests[0][0].answer)
        release.set()
        await asyncio.wait_for(published.wait(), 2)
        await coordinator.execute(CatchUpDeadline(old_clock))
        state = coordinator.view(VerifiedActor(guest.token))
        self.assertEqual(state["phase"], "voting")
        self.assertEqual(len(state["turns"]), 2)
        self.assertEqual(state["vote_deadline_ms"], 16_000)

    async def test_stale_opening_cannot_publish_when_run_changes(self):
        guest = Player("guest", "Sam", 1)
        room = Room("ROOMA", [ProjectFile("queue.py", "queue = []")], {guest.token: guest},
                    phase="generating", generation_id=1, run_id="old-run")
        started, release, finished = asyncio.Event(), asyncio.Event(), asyncio.Event()
        published = []

        async def ask(request, files):
            started.set()
            await release.wait()
            finished.set()
            return GroundedQuestion("Why?", "queue.py", 1, "queue = []")

        async def publish(state):
            published.append(state.snapshot(guest))

        coordinator = RoomCoordinator(room, RoomWorkflows(publish=publish, question_request=ask))
        self.addAsyncCleanup(coordinator.shutdown)
        await coordinator.execute(GenerateQuestion(1, True))
        await asyncio.wait_for(started.wait(), 2)
        room.run_id = "new-run"
        release.set()
        await asyncio.wait_for(finished.wait(), 2)
        self.assertEqual(coordinator.view(VerifiedActor(guest.token))["turns"], [])
        self.assertEqual(published, [])
        self.assertEqual(room.phase, "generating")

    async def test_duplicate_question_work_admits_once_and_publishes_one_opening(self):
        guest = Player("guest", "Sam", 1)
        room = Room("ROOMA", [ProjectFile("queue.py", "queue = []")], {guest.token: guest},
                    phase="generating", generation_id=1)
        started, release, published, clock_started, never = (asyncio.Event() for _ in range(5))
        requests = []
        sleeps = []

        async def ask(request, files):
            requests.append(files)
            started.set()
            await release.wait()
            return GroundedQuestion("How does the queue work?", "queue.py", 1, "queue = []")

        async def publish(state):
            if state.phase == "voting":
                published.set()

        async def sleep(seconds):
            sleeps.append(seconds)
            clock_started.set()
            await never.wait()

        coordinator = RoomCoordinator(room, RoomWorkflows(publish=publish, now=lambda: 1000,
                                                         question_request=ask, sleep=sleep))
        self.addAsyncCleanup(coordinator.shutdown)
        actor = VerifiedActor(guest.token)
        first = await coordinator.execute(GenerateQuestion(1, True))
        await asyncio.wait_for(started.wait(), 2)
        duplicate = await coordinator.execute(GenerateQuestion(1, True))
        self.assertTrue(first.accepted)
        self.assertTrue(duplicate.accepted)
        self.assertEqual(coordinator.view(actor)["question_attempts_left"], 2)
        release.set()
        await asyncio.wait_for(published.wait(), 2)
        await asyncio.wait_for(clock_started.wait(), 2)
        state = coordinator.view(actor)
        self.assertEqual(len(requests), 1)
        self.assertEqual(len(state["turns"]), 1)
        self.assertEqual(state["turns"][0]["evidence_text"], "queue = []")
        self.assertEqual(state["vote_deadline_ms"], 16_000)
        self.assertEqual(sleeps, [15])

"""Planning/coaching coordination through commands and recipient views."""

import asyncio
import unittest

from backend.rooms.commands import GenerateResearchPlan, GenerateCoaching, decode_command, VerifiedActor
from backend.defense_session import DefenseSession, ResearchDefenseSession, PANELIST_ORDER
from backend.question_generator import GroundedQuestion, PanelMove, CoachingReport
from backend.rooms.coordinator import RoomCoordinator, RoomWorkflows
from backend.rooms.model import Player, Room
from backend.project_files import ProjectFile
from tests.offline_accounts import authenticate
from tests.test_research_plan import PAPER, fixture_plan


def completed_room(account, *, run_id=None):
    host, guest = Player("host", "Alex", 0, True, {object()}), Player("guest", "Sam", 1, sockets={object()})
    question = GroundedQuestion("Why?", "queue.py", 1, "queue = []")
    session = DefenseSession.start(question)
    for index, role in enumerate(PANELIST_ORDER):
        if index:
            session.apply_move(PanelMove(role, question))
        session.submit_answer(f"Answer {index + 1}", speaker_name="Sam")
    session.apply_move(PanelMove(None, None))
    return Room("ROOM", [ProjectFile("queue.py", "queue = []")],
                {host.token: host, guest.token: guest}, phase="complete", defense=session,
                feedback_status="generating", feedback_generation_id=1,
                owner_account_id=account["id"], settled=False, run_id=run_id)


class PlanningCoachingCoordinationTests(unittest.IsolatedAsyncioTestCase):
    async def test_coaching_is_deduplicated_and_host_retry_retains_shared_transcript(self):
        account = authenticate(self)
        room = completed_room(account)
        room.chat = [{"text": "private team chat"}]
        actor, teammate = VerifiedActor("host", account["id"]), VerifiedActor("guest")
        started, release, failed, ready = (asyncio.Event() for _ in range(4))
        requests = []
        report = CoachingReport("A useful discussion.", [], [], "Practice the unresolved points.")

        async def coach(request):
            requests.append(request)
            if len(requests) == 1:
                started.set()
                await release.wait()
                raise ValueError("Offline coaching failure")
            return report

        async def deliver(socket, payload):
            state = payload["state"]
            if state["feedback_status"] == "failed":
                failed.set()
            if state["feedback_status"] == "ready":
                ready.set()

        coordinator = RoomCoordinator(room, RoomWorkflows(deliver=deliver, coaching_request=coach, now=lambda: 1000))
        self.addAsyncCleanup(coordinator.shutdown)
        await coordinator.execute(GenerateCoaching(1))
        await asyncio.wait_for(started.wait(), 1)
        await coordinator.execute(GenerateCoaching(1))
        self.assertEqual(len(requests), 1)
        self.assertNotIn("private team chat", repr(requests[0]))
        release.set()
        await asyncio.wait_for(failed.wait(), 1)
        self.assertFalse((await coordinator.execute(decode_command({"type": "retry_coaching"}), teammate)).accepted)
        self.assertTrue((await coordinator.execute(decode_command({"type": "retry_coaching"}), actor)).accepted)
        await asyncio.wait_for(ready.wait(), 1)
        self.assertEqual(len(requests), 2)
        self.assertEqual([turn.answer for turn in requests[0].history], [f"Answer {n}" for n in range(1, 5)])
        self.assertEqual(requests[0].history, requests[1].history)
        self.assertTrue(room.settled)
        host_view, guest_view = coordinator.view(actor), coordinator.view(teammate)
        self.assertEqual(host_view["turns"], guest_view["turns"])
        self.assertEqual(host_view["feedback"], guest_view["feedback"])
        self.assertEqual(host_view["feedback"]["summary"], "A useful discussion.")
        self.assertNotIn("owner_account_id", guest_view)

    async def test_stale_planning_success_and_failure_leave_new_run_unchanged(self):
        account = authenticate(self)
        for fails in (False, True):
            with self.subTest(failure=fails):
                host = Player("host", "Alex", 0, True, {object()})
                room = Room("ROOM", [ProjectFile("study.md", PAPER, "research_text")],
                            {host.token: host}, "research", "proposal",
                            owner_account_id=account["id"], run_id="old")
                started, release, finished = (asyncio.Event() for _ in range(3))
                states = []

                async def prepare(request):
                    started.set()
                    await release.wait()
                    finished.set()
                    if fails:
                        raise ValueError("Obsolete planning failure")
                    return fixture_plan()

                async def deliver(socket, payload):
                    state = payload["state"]
                    states.append(state)

                actor = VerifiedActor(host.token, account["id"])
                coordinator = RoomCoordinator(room, RoomWorkflows(
                    deliver=deliver, plan_request=prepare, now=lambda: 1000))
                self.addAsyncCleanup(coordinator.shutdown)
                await coordinator.execute(decode_command({"type": "prepare_research_plan"}), actor)
                await asyncio.wait_for(started.wait(), 1)
                async with room.lock:
                    room.run_id = "new"
                before = coordinator.view(actor)
                release.set()
                await asyncio.wait_for(finished.wait(), 1)
                await asyncio.sleep(0)
                self.assertEqual(coordinator.view(actor), before)
                self.assertEqual(len(states), 1)

    async def test_stale_coaching_success_and_failure_neither_publish_nor_settle(self):
        account = authenticate(self)
        for fails in (False, True):
            with self.subTest(failure=fails):
                room = completed_room(account, run_id="old")
                started, release, finished = (asyncio.Event() for _ in range(3))
                states = []

                async def coach(request):
                    started.set()
                    await release.wait()
                    finished.set()
                    if fails:
                        raise ValueError("Obsolete coaching failure")
                    return CoachingReport("Old report", [], [], "Review.", closing="This obsolete closing must not appear.")

                async def deliver(socket, payload):
                    state = payload["state"]
                    states.append(state)

                actor = VerifiedActor("host", account["id"])
                coordinator = RoomCoordinator(room, RoomWorkflows(
                    deliver=deliver, coaching_request=coach, now=lambda: 1000))
                self.addAsyncCleanup(coordinator.shutdown)
                await coordinator.execute(GenerateCoaching(1))
                await asyncio.wait_for(started.wait(), 1)
                async with room.lock:
                    room.run_id = "new"
                before = coordinator.view(actor)
                release.set()
                await asyncio.wait_for(finished.wait(), 1)
                await asyncio.sleep(0)
                self.assertEqual(coordinator.view(actor), before)
                self.assertFalse(room.settled)
                self.assertTrue(states)
                self.assertEqual({state["operation"]["id"] for state in states}, {"coaching:1"})
                self.assertEqual({state["revision"] for state in states}, {1})

    async def test_map_retry_keeps_uploads_and_generates_no_questions_on_failure(self):
        account = authenticate(self)
        host = Player("host", "Alex", 0, True, {object()})
        room = Room("ROOM", [ProjectFile("study.md", PAPER, "research_text")],
                    {host.token: host}, "research", "proposal", owner_account_id=account["id"])
        actor = VerifiedActor(host.token, account["id"])
        failed, ready = asyncio.Event(), asyncio.Event()
        requests, plan = [], fixture_plan()

        async def prepare(request):
            requests.append(request)
            if len(requests) == 1:
                raise ValueError("Offline map failure")
            return plan

        async def deliver(socket, payload):
            state = payload["state"]
            if state["research_planning_status"] == "failed":
                failed.set()
            if state["research_planning_status"] == "ready":
                ready.set()

        coordinator = RoomCoordinator(room, RoomWorkflows(deliver=deliver, plan_request=prepare))
        self.addAsyncCleanup(coordinator.shutdown)
        await coordinator.execute(decode_command({"type": "prepare_research_plan"}), actor)
        await asyncio.wait_for(failed.wait(), 1)
        view = coordinator.view(actor)
        self.assertEqual(view["phase"], "lobby")
        self.assertEqual(view["turns"], [])
        self.assertIsNone(view["research_plan"])
        await coordinator.execute(decode_command({"type": "retry_research_plan"}), actor)
        await asyncio.wait_for(ready.wait(), 1)
        self.assertEqual(len(requests), 2)
        self.assertEqual(requests[0], requests[1])
        self.assertEqual(coordinator.view(actor)["research_plan"]["id"], plan.id)
        self.assertIsNone(coordinator.view(actor)["research_plan_error"])

    async def test_empty_session_summary_makes_no_ai_request_or_admission(self):
        account = authenticate(self)
        host = Player("host", "Alex", 0, True, {object()})
        session = ResearchDefenseSession.create(fixture_plan(), 8, "research", "proposal")
        session.end()
        room = Room("ROOM", [ProjectFile("study.md", PAPER, "research_text")],
                    {host.token: host}, "research", "proposal", owner_account_id=account["id"],
                    phase="complete", defense=session, feedback_generation_id=1, feedback_status="generating")
        ready, requests = asyncio.Event(), []

        async def coach(request):
            requests.append(request)
            raise AssertionError("Empty sessions must not request AI coaching")

        async def deliver(socket, payload):
            state = payload["state"]
            if state["feedback_status"] == "ready":ready.set()

        coordinator = RoomCoordinator(room, RoomWorkflows(deliver=deliver, coaching_request=coach))
        self.addAsyncCleanup(coordinator.shutdown)
        await coordinator.execute(GenerateCoaching(1))
        await asyncio.wait_for(ready.wait(), 1)
        view = coordinator.view(VerifiedActor(host.token, account["id"]))
        self.assertEqual(requests, [])
        self.assertIn("before any answer or timeout", view["feedback"]["summary"])
        self.assertEqual(view["feedback"]["strengths"], [])
        self.assertEqual(view["feedback"]["improvements"], [])
        self.assertEqual(room.ai_budget.remaining("coaching", 3), 3)

    async def test_new_closing_coaching_does_not_reuse_an_older_request(self):
        account = authenticate(self)
        room = completed_room(account)
        started, release, ready, finished = (asyncio.Event() for _ in range(4))
        requests = []

        async def coach(request):
            requests.append(request)
            if len(requests) == 1:
                started.set()
                await release.wait()
                finished.set()
                return CoachingReport("Obsolete report", [], [], "Review.")
            return CoachingReport("Current closing report", [], [], "Review.")

        async def deliver(socket, payload):
            state = payload["state"]
            if state["feedback_status"] == "ready":ready.set()

        coordinator = RoomCoordinator(room, RoomWorkflows(deliver=deliver, coaching_request=coach))
        self.addAsyncCleanup(coordinator.shutdown)
        await coordinator.execute(GenerateCoaching(1))
        await asyncio.wait_for(started.wait(), 1)
        async with room.lock:
            room.feedback_generation_id += 1
        await coordinator.execute(GenerateCoaching(2))
        await asyncio.wait_for(ready.wait(), 1)
        release.set()
        await asyncio.wait_for(finished.wait(), 1)
        await asyncio.sleep(0)
        self.assertEqual(len(requests), 2)
        self.assertEqual(coordinator.view(VerifiedActor("guest"))["feedback"]["summary"], "Current closing report")

    async def test_host_prepares_once_and_only_current_map_can_be_approved(self):
        account = authenticate(self)
        host = Player("host", "Alex", 0, True, {object()})
        guest = Player("guest", "Sam", 1, sockets={object()})
        room = Room("ROOM", [ProjectFile("study.md", PAPER, "research_text")],
                    {host.token: host, guest.token: guest}, "research", "proposal",
                    owner_account_id=account["id"])
        actor, teammate = VerifiedActor(host.token, account["id"]), VerifiedActor(guest.token)
        started, release, ready = (asyncio.Event() for _ in range(3))
        requests = []
        plan = fixture_plan()

        async def prepare(request):
            requests.append(request)
            started.set()
            await release.wait()
            return plan

        async def deliver(socket, payload):
            state = payload["state"]
            if state["research_planning_status"] == "ready":
                ready.set()

        coordinator = RoomCoordinator(room, RoomWorkflows(deliver=deliver, plan_request=prepare))
        self.addAsyncCleanup(coordinator.shutdown)
        command = decode_command({"type": "prepare_research_plan"})
        self.assertFalse((await coordinator.execute(command, teammate)).accepted)
        self.assertTrue((await coordinator.execute(command, actor)).accepted)
        await asyncio.wait_for(started.wait(), 1)
        self.assertFalse((await coordinator.execute(command, actor)).accepted)
        await coordinator.execute(GenerateResearchPlan(room.research_plan_generation_id))
        self.assertEqual(len(requests), 1)
        self.assertEqual(requests[0].files[0].name, "study.md")
        self.assertEqual(requests[0].research_stage, "proposal")
        self.assertIsNone(coordinator.view(teammate)["research_plan"])
        release.set()
        await asyncio.wait_for(ready.wait(), 1)
        self.assertEqual(coordinator.view(actor)["research_plan"], coordinator.view(teammate)["research_plan"])
        self.assertFalse((await coordinator.execute(decode_command({
            "type": "approve_research_plan", "plan_id": "obsolete", "question_budget": 12, "confirm_profile": True}), actor)).accepted)
        self.assertTrue((await coordinator.execute(decode_command({
            "type": "approve_research_plan", "plan_id": plan.id, "question_budget": 12, "confirm_profile": True}), actor)).accepted)
        self.assertTrue(coordinator.view(actor)["research_plan_approved"])
        self.assertEqual(coordinator.view(actor)["research_budget_preview"], 12)
        self.assertEqual(coordinator.view(actor)["turns"], [])

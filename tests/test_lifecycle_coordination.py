"""Lifecycle races through commands/views; providers are controlled offline."""

import asyncio
import os
import unittest
from unittest.mock import patch

from backend.rooms.commands import (VerifiedActor, decode_command, GenerateQuestion,
    InterpretSubmission, GenerateResearchPlan, GenerateCoaching, ReclaimRoom,
    DefenderDisconnected, ObserveAbsence, PublishRoom)
from backend.rooms.coordinator import RoomCoordinator, RoomWorkflows
from backend.rooms.model import Player, Room
from backend.project_files import ProjectFile
from backend import account_store
from backend import game_server
from backend.defense_session import DefenseSession, ResearchDefenseSession
from backend.question_generator import (GroundedQuestion, CoachingReport, SubmissionDecision,
    ResearchMove, TopicAssessmentDraft, InvalidQuestionResponse)
from backend.timed_turn import PendingSubmission
from tests.offline_accounts import authenticate
from tests.test_presence_coordination import CapturedSocket
from tests.test_research_coverage import plan, FILES, PAPER
from tests.test_planning_coaching_coordination import completed_room


class LifecycleCoordinationTests(unittest.IsolatedAsyncioTestCase):
    async def test_restart_cancels_retry_backoff_without_replaying_the_old_turn(self):
        account = authenticate(self)
        socket = CapturedSocket()
        host = Player("host", "Alex", 0, True, {socket})
        question = GroundedQuestion("Why?", "queue.py", 1, "queue = []")
        session = DefenseSession.start(question)
        session.submit_answer("We preserve arrival order.", speaker_name="Alex")
        room = Room("BACKOFF", [ProjectFile("queue.py", "queue = []")], {host.token: host},
                    owner_account_id=account["id"], defense=session, phase="generating", generation_id=1)
        backoff, cancelled, ready, never = (asyncio.Event() for _ in range(4))
        histories = []

        async def ask(request, files):
            histories.append(request.session.answered_history() if request.session else [])
            if request.session:
                raise InvalidQuestionResponse("Offline citation failure")
            return GroundedQuestion("New opening?", "queue.py", 1, "queue = []")

        async def sleep(seconds):
            if seconds == 1:
                backoff.set()
                try:
                    await never.wait()
                except asyncio.CancelledError:
                    cancelled.set()
                    raise
            else:
                await never.wait()

        async def deliver(recipient, payload):
            await recipient.send_json(payload)
            if payload["state"]["phase"] == "voting":
                ready.set()

        coordinator = RoomCoordinator(room, RoomWorkflows(question_request=ask, deliver=deliver,
                                                         sleep=sleep, now=lambda: 1000))
        self.addAsyncCleanup(coordinator.shutdown)
        actor = VerifiedActor(host.token, account["id"])
        await coordinator.execute(GenerateQuestion(1, False))
        await asyncio.wait_for(backoff.wait(), 1)
        self.assertTrue(coordinator.view(actor)["question_retrying"])
        self.assertTrue((await coordinator.execute(decode_command({"type": "restart"}), actor)).accepted)
        await asyncio.wait_for(cancelled.wait(), 1)
        await asyncio.wait_for(ready.wait(), 1)
        self.assertEqual(len(histories), 2)
        self.assertEqual(histories[0][0].answer, "We preserve arrival order.")
        self.assertEqual(histories[1], [])
        self.assertEqual([turn["question"] for turn in coordinator.view(actor)["turns"]], ["New opening?"])
        self.assertFalse(coordinator.view(actor)["question_retrying"])

    async def test_observed_abandonment_retires_provider_and_cannot_publish_late_question(self):
        account = authenticate(self)
        socket = CapturedSocket()
        host = Player("host", "Alex", 0, True, {socket})
        room = Room("ABSENT", [ProjectFile("queue.py", "queue = []")], {host.token: host}, owner_account_id=account["id"])
        now = 1000
        started, cancelled, release, finished = (asyncio.Event() for _ in range(4))

        async def ask(request, files):
            started.set()
            try:
                await release.wait()
            except asyncio.CancelledError:
                cancelled.set()
                await release.wait()
            finished.set()
            return GroundedQuestion("Old opening?", "queue.py", 1, "queue = []")

        coordinator = RoomCoordinator(room, RoomWorkflows(question_request=ask, now=lambda: now))
        self.addAsyncCleanup(coordinator.shutdown)
        self.addCleanup(release.set)
        actor = VerifiedActor(host.token, account["id"])
        await coordinator.execute(decode_command({"type": "start"}), actor)
        await asyncio.wait_for(started.wait(), 1)
        await coordinator.execute(DefenderDisconnected(host.token, socket))
        for _ in range(20):
            now += 30000
            await coordinator.execute(ObserveAbsence())
        await asyncio.wait_for(cancelled.wait(), 1)
        before = coordinator.view(actor)
        self.assertEqual(before["phase"], "complete")
        self.assertIn("abandoned", before["error"])
        release.set()
        await asyncio.wait_for(finished.wait(), 1)
        await asyncio.sleep(0)
        self.assertEqual(coordinator.view(actor), before)
        self.assertEqual(before["turns"], [])

    async def test_reclamation_rechecks_expiry_and_clears_only_eligible_rooms(self):
        socket = CapturedSocket()
        host = Player("host", "Alex", 0, True, {socket})
        room = Room("EXPIRY", [ProjectFile("queue.py", "queue = []")], {host.token: host},
                    owner_account_id="owner", created_ms=1000, activity_ms=1000)
        now = 1000
        coordinator = RoomCoordinator(room, RoomWorkflows(now=lambda: now))
        self.addAsyncCleanup(coordinator.shutdown)
        self.assertFalse((await coordinator.execute(ReclaimRoom(expired_only=True))).accepted)
        self.assertEqual(coordinator.view(VerifiedActor(host.token, "owner"))["files"], ["queue.py"])
        now = 1801000
        self.assertTrue((await coordinator.execute(ReclaimRoom(expired_only=True))).accepted)
        self.assertEqual(socket.closed, [1000])
        self.assertEqual(socket.messages[-1]["type"], "error")
        self.assertEqual(room.files, [])
        self.assertEqual(room.players, {})
        self.assertFalse((await coordinator.execute(decode_command({"type": "start"}), VerifiedActor(host.token, "owner"))).accepted)

    async def test_shutdown_drains_already_captured_delivery_before_returning(self):
        socket = CapturedSocket()
        player = Player("guest", "Sam", 0, sockets={socket})
        room = Room("DELIVERY", [], {player.token: player})
        started, release = asyncio.Event(), asyncio.Event()

        async def deliver(recipient, payload):
            started.set()
            await release.wait()
            await recipient.send_json(payload)

        coordinator = RoomCoordinator(room, RoomWorkflows(deliver=deliver, now=lambda: 1000))
        self.addAsyncCleanup(coordinator.shutdown)
        publication = asyncio.create_task(coordinator.execute(PublishRoom()))
        await asyncio.wait_for(started.wait(), 1)
        stopping = asyncio.create_task(coordinator.shutdown())
        await asyncio.sleep(0)
        stopping_again = asyncio.create_task(coordinator.shutdown())
        await asyncio.sleep(0)
        self.assertFalse(stopping.done())
        self.assertFalse(stopping_again.done())
        release.set()
        await asyncio.wait_for(asyncio.gather(publication, stopping, stopping_again), 2)
        self.assertEqual(len(socket.messages), 1)
        await coordinator.execute(PublishRoom())
        self.assertEqual(len(socket.messages), 1)

    async def test_cancelled_shutdown_caller_does_not_release_delivery_drain(self):
        socket = CapturedSocket()
        player = Player("guest", "Sam", 0, sockets={socket})
        room = Room("CANCEL-DRAIN", [], {player.token: player})
        started, release = asyncio.Event(), asyncio.Event()

        async def deliver(recipient, payload):
            started.set()
            await release.wait()
            await recipient.send_json(payload)

        coordinator = RoomCoordinator(room, RoomWorkflows(deliver=deliver, now=lambda: 1000))
        self.addAsyncCleanup(coordinator.shutdown)
        self.addCleanup(release.set)
        publication = asyncio.create_task(coordinator.execute(PublishRoom()))
        await asyncio.wait_for(started.wait(), 1)
        stopping = asyncio.create_task(coordinator.shutdown())
        await asyncio.sleep(0)
        stopping.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await stopping
        stopping_again = asyncio.create_task(coordinator.shutdown())
        await asyncio.sleep(0)
        self.assertFalse(stopping_again.done())
        release.set()
        await asyncio.wait_for(asyncio.gather(publication, stopping_again), 2)
        self.assertEqual(len(socket.messages), 1)
        await coordinator.execute(PublishRoom())
        self.assertEqual(len(socket.messages), 1)

    async def test_cancelled_registry_reclamation_still_removes_room_and_uploads(self):
        socket = CapturedSocket()
        player = Player("guest", "Sam", 0, sockets={socket})
        room = Room("CANCEL-RECLAIM", [ProjectFile("queue.py", "queue = []")], {player.token: player},
                    created_ms=1000, activity_ms=1000)
        started, release = asyncio.Event(), asyncio.Event()

        async def deliver(recipient, payload):
            started.set()
            await release.wait()
            await recipient.send_json(payload)

        coordinator = RoomCoordinator(room, RoomWorkflows(deliver=deliver, now=lambda: 1801000))
        self.addAsyncCleanup(coordinator.shutdown)
        self.addCleanup(release.set)
        with patch.dict(game_server.rooms, {room.code: room}, clear=True):
            removal = asyncio.create_task(game_server._remove_room(room, expired_only=True))
            await asyncio.wait_for(started.wait(), 1)
            removal.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await removal
            retry = asyncio.create_task(game_server._remove_room(room, expired_only=True))
            release.set()
            await asyncio.wait_for(retry, 2)
            self.assertNotIn(room.code, game_server.rooms)
            self.assertEqual(room.files, [])
            self.assertEqual(room.players, {})
            self.assertEqual(socket.closed, [1000])

    async def test_shutdown_fences_late_success_and_error_in_every_ai_lane(self):
        account = authenticate(self)
        for lane in ["question", "interpretation", "plan", "coaching"]:
            for fails in [False, True]:
                with self.subTest(lane=lane, fails=fails):
                    started, cancelled, release, finished, never = (asyncio.Event() for _ in range(5))
                    socket = CapturedSocket()
                    host = Player("host", "Alex", 0, True, {socket})
                    room = Room("SHUTDOWN", [ProjectFile("queue.py", "queue = []")], {host.token: host},
                                owner_account_id=account["id"])
                    question = GroundedQuestion("Why?", "queue.py", 1, "queue = []")
                    if lane == "question":
                        room.phase, room.generation_id = "generating", 1
                        command, result = GenerateQuestion(1, True), question
                    elif lane == "interpretation":
                        room.defense = DefenseSession.start(question)
                        room.phase, room.interpretation_id, room.answer_deadline_ms = "interpreting", 1, 121000
                        room.pending_submission = PendingSubmission(0, host.token, host.name, 0, "Saved text.", 120000)
                        command, result = InterpretSubmission(1), SubmissionDecision("answer")
                    elif lane == "plan":
                        room.defense_type, room.research_stage = "research", "proposal"
                        room.files = list(FILES)
                        room.research_planning_status, room.research_plan_generation_id = "planning", 1
                        command, result = GenerateResearchPlan(1), plan(4)
                    else:
                        room = completed_room(account)
                        room.players = {host.token: host}
                        command, result = GenerateCoaching(1), CoachingReport("Old report", [], [], "Review.", closing="This obsolete closing must not appear.")

                    async def blocked(*args):
                        started.set()
                        try:
                            try:
                                await release.wait()
                            except asyncio.CancelledError:
                                cancelled.set()
                                await release.wait()
                            if fails:
                                raise RuntimeError("Offline old failure")
                            return result
                        finally:
                            finished.set()

                    async def sleep(seconds):
                        await never.wait()

                    coordinator = RoomCoordinator(room, RoomWorkflows(question_request=blocked,
                        interpretation_request=blocked, plan_request=blocked, coaching_request=blocked,
                        now=lambda: 1000, sleep=sleep))
                    self.addCleanup(release.set)
                    await coordinator.execute(command)
                    await asyncio.wait_for(started.wait(), 1)
                    await asyncio.wait_for(coordinator.shutdown(), 1)
                    await asyncio.wait_for(cancelled.wait(), 1)
                    actor = VerifiedActor(host.token, account["id"])
                    before, count = coordinator.view(actor), len(socket.messages)
                    release.set()
                    await asyncio.wait_for(finished.wait(), 1)
                    await asyncio.sleep(0)
                    self.assertEqual(coordinator.view(actor), before)
                    self.assertEqual(len(socket.messages), count)
                    self.assertFalse((await coordinator.execute(decode_command({"type": "restart"}), actor)).accepted)

    async def test_research_end_keeps_answer_and_new_coaching_while_old_question_finishes(self):
        account = authenticate(self)
        for fails in [False, True]:
            with self.subTest(fails=fails):
                started, cancelled, release, ready, finished = (asyncio.Event() for _ in range(5))
                host = Player("host", "Alex", 0, True, {CapturedSocket()})
                session = ResearchDefenseSession.create(plan(4), 12, "research", "proposal")
                question = GroundedQuestion("Why this pilot?", "paper.md", 1, PAPER.splitlines()[0])
                session.apply_move(ResearchMove("Methodology Reviewer", question, "topic-1", False, None))
                session.submit_answer("We will compare completion time.", speaker_name="Alex")
                room = Room("ENDING", list(FILES), {host.token: host}, "research", "proposal", defense=session,
                            owner_account_id=account["id"], phase="generating", generation_id=1)
                reports = []

                async def ask(request, files):
                    started.set()
                    try:
                        try:
                            await release.wait()
                        except asyncio.CancelledError:
                            cancelled.set()
                            await release.wait()
                        if fails:
                            raise RuntimeError("Offline old failure")
                        return ResearchMove("Ethics Reviewer", question, "topic-2", False,
                            TopicAssessmentDraft(topic_id="topic-1", turn=1, status="addressed", reason="Explained."))
                    finally:
                        finished.set()

                async def coach(request):
                    reports.append(request)
                    return CoachingReport("Current closing report", [], [], "Review the remaining topics.")

                async def deliver(socket, payload):
                    await socket.send_json(payload)
                    if payload["state"]["feedback_status"] == "ready":
                        ready.set()

                coordinator = RoomCoordinator(room, RoomWorkflows(question_request=ask, coaching_request=coach,
                    deliver=deliver, now=lambda: 1000))
                self.addAsyncCleanup(coordinator.shutdown)
                self.addCleanup(release.set)
                actor = VerifiedActor(host.token, account["id"])
                await coordinator.execute(GenerateQuestion(1, False))
                await asyncio.wait_for(started.wait(), 1)
                self.assertTrue((await coordinator.execute(decode_command({"type": "end_defense"}), actor)).accepted)
                await asyncio.wait_for(cancelled.wait(), 1)
                await asyncio.wait_for(ready.wait(), 1)
                before = coordinator.view(actor)
                release.set()
                await asyncio.wait_for(finished.wait(), 1)
                await asyncio.sleep(0)
                self.assertEqual(coordinator.view(actor), before)
                self.assertEqual(before["turns"][0]["answer"], "We will compare completion time.")
                self.assertEqual(before["completion_reason"], "ended by host")
                self.assertEqual(before["feedback"]["summary"], "Current closing report")
                self.assertEqual(len(reports), 1)
                self.assertEqual(reports[0].history[0].speaker_name, "Alex")
                self.assertEqual(reports[0].history[0].citation, question)

    async def test_paid_restart_confirmation_failure_retry_and_unique_charges(self):
        account = authenticate(self)
        with account_store.connect_store(account_store.database_path()) as db:
            db.execute("INSERT INTO test_orders (id,token_hash,amount,currency,status,created_at,account_id,credits) VALUES ('lifecycle-fixture','offline',10000,'PHP','paid',1,?,100)", (account["id"],))
            db.execute("INSERT INTO test_credit_ledger VALUES ('lifecycle-fixture',?,100,1)", (account["id"],))
        socket, never = CapturedSocket(), asyncio.Event()
        host = Player("host", "Alex", 0, True, {socket})
        room = Room("PAID", [ProjectFile("queue.py", "queue = []")], {host.token: host}, owner_account_id=account["id"])
        published, requests = asyncio.Queue(), []

        async def ask(request, files):
            requests.append(request)
            if len(requests) == 2:
                raise RuntimeError("Offline opening failure")
            return GroundedQuestion("Why?", "queue.py", 1, "queue = []")

        async def deliver(socket, payload):
            await socket.send_json(payload)
            if payload["state"]["phase"] in {"voting", "retry"}:
                published.put_nowait(payload["state"])

        async def sleep(seconds):
            await never.wait()

        coordinator = RoomCoordinator(room, RoomWorkflows(question_request=ask, deliver=deliver,
                                                         now=lambda: 1000, sleep=sleep))
        self.addAsyncCleanup(coordinator.shutdown)
        actor = VerifiedActor(host.token, account["id"])
        with patch.dict(os.environ, {"FREE_ACCESS_VOUCHER": ""}):
            self.assertTrue((await coordinator.execute(decode_command({"type": "start", "confirm_cost": True}), actor)).accepted)
            await asyncio.wait_for(published.get(), 1)
            old_run = room.run_id
            before = coordinator.view(actor)
            self.assertFalse((await coordinator.execute(decode_command({"type": "restart"}), actor)).accepted)
            self.assertEqual(coordinator.view(actor), before)
            self.assertTrue((await coordinator.execute(decode_command({"type": "restart", "confirm_cost": True}), actor)).accepted)
            self.assertNotEqual(room.run_id, old_run)
            failed = await asyncio.wait_for(published.get(), 1)
            self.assertEqual(failed["phase"], "retry")
            self.assertEqual(account_store.account_access(account["id"])["test_credits"], 90)
            run = room.run_id
            self.assertTrue((await coordinator.execute(decode_command({"type": "retry"}), actor)).accepted)
            await asyncio.wait_for(published.get(), 1)
            self.assertEqual(room.run_id, run)
            self.assertFalse((await coordinator.execute(decode_command({"type": "retry"}), actor)).accepted)
            access = account_store.account_access(account["id"])
            self.assertEqual((access["test_credits"], access["reserved_credits"], access["spent_credits"]), (80, 0, 20))
            self.assertEqual(len(requests), 3)

    async def test_restart_retires_blocked_opening_and_only_new_run_publishes(self):
        account = authenticate(self)
        socket = CapturedSocket()
        host = Player("host", "Alex", 0, True, {socket})
        room = Room("RESTART", [ProjectFile("queue.py", "queue = []")], {host.token: host},
                    owner_account_id=account["id"])
        started, cancelled, release, ready, never = (asyncio.Event() for _ in range(5))
        requests = []

        async def ask(request, files):
            requests.append(request)
            if len(requests) == 1:
                started.set()
                try:
                    await release.wait()
                except asyncio.CancelledError:
                    cancelled.set()
                    await release.wait()
                return GroundedQuestion("Old opening?", "queue.py", 1, "queue = []")
            return GroundedQuestion("New opening?", "queue.py", 1, "queue = []")

        async def deliver(recipient, payload):
            await recipient.send_json(payload)
            if payload["state"]["phase"] == "voting":
                ready.set()

        async def sleep(seconds):
            await never.wait()

        coordinator = RoomCoordinator(room, RoomWorkflows(question_request=ask, deliver=deliver,
                                                         now=lambda: 1000, sleep=sleep))
        self.addAsyncCleanup(coordinator.shutdown)
        self.addCleanup(release.set)
        actor = VerifiedActor(host.token, account["id"])
        self.assertTrue((await coordinator.execute(decode_command({"type": "start"}), actor)).accepted)
        await asyncio.wait_for(started.wait(), 1)
        old_run = room.run_id
        self.assertTrue((await coordinator.execute(decode_command({"type": "restart"}), actor)).accepted)
        await asyncio.wait_for(cancelled.wait(), 1)
        await asyncio.wait_for(ready.wait(), 1)
        self.assertNotEqual(room.run_id, old_run)
        release.set()
        await asyncio.sleep(0)
        state = coordinator.view(actor)
        self.assertEqual([turn["question"] for turn in state["turns"]], ["New opening?"])
        self.assertEqual(len(requests), 2)
        self.assertFalse(any("Old opening?" in repr(payload) for payload in socket.messages))

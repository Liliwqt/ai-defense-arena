"""Host-described scope is attributed data, never uploaded research evidence."""

import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from backend.project_files import ProjectFile
from backend.research_plan import generate_research_plan
from tests.test_research_plan import FakeClient, PAPER, draft


class ProfileCorrectionGenerationTests(unittest.TestCase):
    def test_remapping_retains_host_description_separately_from_source_basis(self):
        from backend.research_plan import validate_profile_description
        correction = validate_profile_description({"fields": ["Education", "Public policy"],
                     "approaches": ["quantitative"], "setting": "University campus"})
        output = draft()
        output["profile"].update({"fields": ["Education"], "approaches": ["qualitative"],
             "setting": "One university", "explanation": "The paper proposes interviews with volunteers.",
             "uncertainties": ["The host describes quantitative work; the cited plan describes interviews."]})
        client = FakeClient(output)
        plan = generate_research_plan([ProjectFile("study.md", PAPER, "research_text")], "offline-key",
                profile_correction=correction, client=client)
        profile = plan.snapshot()["profile"]
        self.assertEqual(profile["fields"], ["Education", "Public policy"])
        self.assertEqual(profile["approaches"], ["quantitative"])
        self.assertEqual(profile["host_description"], correction.snapshot())
        self.assertEqual(profile["source_description"]["approaches"], ["qualitative"])
        self.assertEqual(profile["explanation"], "The paper proposes interviews with volunteers.")
        self.assertTrue(profile["needs_uncertainty_acknowledgment"])
        self.assertEqual(profile["references"][0]["evidence_text"], PAPER.splitlines()[0])
        data = json.loads(client.calls[0]["input"][1]["content"].split("\n", 1)[1])
        self.assertEqual(data["host_profile_description"], correction.snapshot())
        self.assertEqual(len(client.calls), 1)

from backend.question_generator import QuestionGenerationError
from tests import test_research_plan as fixtures

CORRECTION = {"fields": ["Education", "Public policy"], "approaches": ["quantitative"],
              "setting": "University campus"}


class ProfileCorrectionRoomTests(unittest.TestCase):
    def setUp(self):
        fixtures.ResearchPlanRoomTests.setUp(self)
        import itertools, time
        from backend import game_server
        clock = itertools.count(time.monotonic(), .3).__next__
        for limiter in (game_server.socket_message_rate, game_server.socket_room_rate):
            mocked_clock = patch.object(limiter, "clock", side_effect=clock)
            mocked_clock.start()
            self.addCleanup(mocked_clock.stop)
    create = fixtures.ResearchPlanRoomTests.create
    hello = fixtures.ResearchPlanRoomTests.hello
    until = fixtures.ResearchPlanRoomTests.until

    def test_saved_correction_invalidates_approval_and_survives_failure_retry_and_reconnect(self):
        host = self.create()
        guest = self.client.post(f"/api/rooms/{host['room_code']}/join", json={"name": "Guest"}).json()
        requests = []
        def mapping(files, key, model, **kwargs):
            requests.append(kwargs.get("profile_correction"))
            if len(requests) == 1:
                return self.plan
            if len(requests) == 2:
                raise QuestionGenerationError("Synthetic mapping failure")
            output = draft()
            output["profile"].update({"approaches": ["qualitative"], "uncertainties": ["The paper describes interviews."]})
            return generate_research_plan(files, "offline-key", client=FakeClient(output),
                profile_correction=kwargs.get("profile_correction"))
        with patch("backend.rooms.planning.generate_research_plan", side_effect=mapping) as ai:
            with self.client.websocket_connect(f"/ws/{host['room_code']}") as h:
                self.hello(h, host["player_token"])
                h.send_json({"type": "prepare_research_plan"})
                self.until(h, research_planning_status="ready")
                h.send_json({"type": "approve_research_plan", "plan_id": self.plan.id,
                             "question_budget": 8, "confirm_profile": True})
                self.until(h, research_plan_approved=True)
                h.send_json({"type": "prepare_research_plan", "profile_correction": CORRECTION})
                failed = self.until(h, research_planning_status="failed")
                self.assertFalse(failed["research_plan_approved"])
                self.assertIsNone(failed["research_plan"])
                self.assertEqual(failed["research_profile_correction"], CORRECTION)
                self.assertEqual(failed["turns"], [])
                self.assertEqual(failed["files"], ["study.md"])
            with self.client.websocket_connect(f"/ws/{host['room_code']}") as h, \
                    self.client.websocket_connect(f"/ws/{host['room_code']}") as g:
                self.hello(h, host["player_token"])
                restored = self.hello(g, guest["player_token"])
                self.assertEqual(restored["research_profile_correction"], CORRECTION)
                self.until(h, research_planning_status="failed")  # guest-presence publication
                g.send_json({"type": "prepare_research_plan", "profile_correction": {**CORRECTION, "fields": ["Other"]}})
                self.assertIn("Only the host", g.receive_json()["message"])
                h.send_json({"type": "retry_research_plan", "profile_correction": {**CORRECTION, "fields": ["Other"]}})
                self.assertIn("saved profile", h.receive_json()["message"])
                h.send_json({"type": "retry_research_plan"})
                ready = self.until(h, research_planning_status="ready")
                self.assertEqual(ready["research_plan"]["profile"]["host_description"], CORRECTION)
                self.assertEqual(ready["research_plan"]["profile"]["source_description"]["approaches"], ["qualitative"])
                self.assertNotEqual(ready["research_plan"]["id"], self.plan.id)
                self.assertFalse(ready["research_plan_approved"])
                h.send_json({"type": "approve_research_plan", "plan_id": self.plan.id,
                             "question_budget": 8, "confirm_profile": True})
                self.assertIn("changed", h.receive_json()["message"])
                h.send_json({"type": "approve_research_plan", "plan_id": ready["research_plan"]["id"],
                             "question_budget": 8, "confirm_profile": True, "acknowledge_uncertainty": True})
                self.until(h, research_plan_approved=True)
                shared = self.until(g, research_plan_approved=True)
                self.assertEqual(shared["research_plan"]["profile"]["host_description"], CORRECTION)
            self.assertEqual(ai.call_count, 3)
            self.assertEqual([r.snapshot() for r in requests[1:]], [CORRECTION, CORRECTION])

    def test_active_run_rejects_edits_and_unchanged_restart_retains_confirmed_scope(self):
        from tests.test_research_coverage import mocked_move
        from backend import game_server
        clock = {"now": game_server._now_ms()}
        host = self.create()
        output = draft()
        from backend.research_plan import validate_profile_description
        prepared = generate_research_plan([ProjectFile("study.md", PAPER, "research_text")], "offline-key",
                    profile_correction=validate_profile_description(CORRECTION), client=FakeClient(output))
        def ask(files, key, *, history, context, **kwargs):
            if history:
                raise QuestionGenerationError("Synthetic next-question failure")
            return mocked_move(files, key, history=history, context=context, **kwargs)
        with patch.object(game_server, "_now_ms", side_effect=lambda: clock["now"]), \
                patch("backend.rooms.planning.generate_research_plan", return_value=prepared), \
                patch("backend.rooms.questions.generate_research_move", side_effect=ask), \
                self.client.websocket_connect(f"/ws/{host['room_code']}") as h:
            self.hello(h, host["player_token"])
            h.send_json({"type": "prepare_research_plan", "profile_correction": CORRECTION})
            self.until(h, research_planning_status="ready")
            h.send_json({"type": "approve_research_plan", "plan_id": prepared.id,
                         "question_budget": 8, "confirm_profile": True})
            approved = self.until(h, research_plan_approved=True)
            h.send_json({"type": "start", "plan_id": prepared.id, "question_budget": 8})
            voting = self.until(h, phase="voting")
            h.send_json({"type": "cast_vote", "seat": 0})
            self.until(h, my_vote=0)
            clock["now"] = voting["vote_deadline_ms"]
            h.send_json({"type": "send_chat", "text": "Voting deadline reached"})
            self.until(h, phase="question")
            answer = "We would compare the recorded waiting times and report limitations."
            h.send_json({"type": "submit_direct_answer", "turn": 0, "answer": answer})
            retry = self.until(h, phase="retry")
            self.assertEqual(retry["turns"][0]["answer"], answer)
            h.send_json({"type": "prepare_research_plan", "profile_correction": {**CORRECTION, "fields": ["Other"]}})
            self.assertIn("before starting", h.receive_json()["message"])
            h.send_json({"type": "send_chat", "text": "Check retained answer"})
            preserved = self.until(h, phase="retry")
            self.assertEqual(preserved["turns"], retry["turns"])
            self.assertEqual(preserved["research_plan"], approved["research_plan"])
            h.send_json({"type": "restart", "confirm_cost": True})
            restarted = self.until(h, phase="voting")
            self.assertEqual(restarted["research_plan"], approved["research_plan"])
            self.assertEqual(restarted["research_profile_correction"], CORRECTION)

    def test_invalid_corrections_and_lost_access_leave_the_valid_map_unchanged(self):
        host = self.create()
        with patch("backend.rooms.planning.generate_research_plan", return_value=self.plan) as ai, \
                self.client.websocket_connect(f"/ws/{host['room_code']}") as h:
            self.hello(h, host["player_token"])
            h.send_json({"type": "prepare_research_plan"})
            self.until(h, research_planning_status="ready")
            h.send_json({"type": "approve_research_plan", "plan_id": self.plan.id,
                         "question_budget": 8, "confirm_profile": True})
            approved = self.until(h, research_plan_approved=True)
            for change in ({"fields": []}, {"fields": ["Education", "education"]}, {"fields": ["x"*121]},
                           {"approaches": ["invented"]}, {"setting": 123}, {"setting": "x"*301}, {"explanation": "forged"}):
                h.send_json({"type": "prepare_research_plan", "profile_correction": {**CORRECTION, **change}})
                self.assertEqual(h.receive_json()["type"], "error")
                h.send_json({"type": "send_chat", "text": "Check unchanged scope"})
                state = self.until(h, research_plan_approved=True)
                self.assertEqual(state["research_plan"], approved["research_plan"])
                self.assertIsNone(state["research_profile_correction"])
            import os
            with patch.dict(os.environ, {"FREE_ACCESS_VOUCHER": "rotated-offline-voucher"}):
                h.send_json({"type": "prepare_research_plan", "profile_correction": CORRECTION})
                self.assertEqual(h.receive_json()["type"], "error")
                h.send_json({"type": "send_chat", "text": "Scope after access rejection"})
                state = self.until(h, research_plan_approved=True)
                self.assertEqual(state["research_plan"], approved["research_plan"])
                self.assertIsNone(state["research_profile_correction"])
            self.assertEqual(ai.call_count, 1)

    def test_pending_edits_are_rejected_and_late_callbacks_cannot_replace_a_newer_map(self):
        import asyncio
        from threading import Event
        from backend import game_server
        from backend.rooms.coordinator import RoomWorkflows
        from backend.research_plan import ResearchPlanProgress
        started, release, finished = Event(), Event(), Event()
        requests, old_progress = [], []
        async def mapping(request):
            requests.append(request)
            if len(requests) == 1:
                started.set()
                try:
                    await asyncio.to_thread(release.wait, 5)
                except asyncio.CancelledError:
                    await asyncio.to_thread(release.wait, 5)
                old_progress.append(await request.on_progress(ResearchPlanProgress("validating", self.plan.topics)))
                finished.set()
            return generate_research_plan(list(request.files), "offline-key", client=FakeClient(draft()),
                                          profile_correction=request.profile_correction)
        self.addCleanup(release.set)
        with patch.object(game_server, "RoomWorkflows", side_effect=lambda **kw: RoomWorkflows(**kw, plan_request=mapping)):
            host = self.create()
            with self.client.websocket_connect(f"/ws/{host['room_code']}") as h:
                self.hello(h, host["player_token"])
                h.send_json({"type": "prepare_research_plan", "profile_correction": CORRECTION})
                self.until(h, research_planning_status="planning")
                self.assertTrue(started.wait(1))
                for action in ({"type": "prepare_research_plan", "profile_correction": CORRECTION},
                               {"type": "prepare_research_plan", "profile_correction": {**CORRECTION, "fields": ["Other"]}}):
                    h.send_json(action)
                    self.assertIn("already being prepared", h.receive_json()["message"])
                self.assertEqual(len(requests), 1)
                h.send_json({"type": "restart"})
                self.until(h, research_planning_status="none")
                newer = {**CORRECTION, "fields": ["Public policy"]}
                h.send_json({"type": "prepare_research_plan", "profile_correction": newer})
                ready = self.until(h, research_planning_status="ready")
                h.send_json({"type": "approve_research_plan", "plan_id": ready["research_plan"]["id"],
                             "question_budget": 8, "confirm_profile": True})
                self.until(h, research_plan_approved=True)
                release.set()
                self.assertTrue(finished.wait(1))
                h.send_json({"type": "send_chat", "text": "After the old mapping returned"})
                current = self.until(h, research_plan_approved=True)
                self.assertEqual(current["research_profile_correction"], newer)
                self.assertEqual(current["research_plan"], ready["research_plan"])
                self.assertEqual(old_progress, [False])
                self.assertEqual(len(requests), 2)




class ProfileCorrectionStreamlitTests(unittest.TestCase):
    def test_unsaved_changes_block_start_and_remap_retry_keeps_descriptions(self):
        requests = []
        def mapping(files, key, model, **kwargs):
            correction = kwargs.get("profile_correction")
            requests.append(correction)
            if len(requests) == 2:
                raise QuestionGenerationError("Synthetic unavailable map")
            return generate_research_plan(files, "offline-key", client=FakeClient(draft()),
                                          profile_correction=correction)
        with patch.dict(os.environ, {"OPENAI_API_KEY": "offline-key"}), \
                patch("backend.research_plan.generate_research_plan", side_effect=mapping):
            app = AppTest.from_file(str(Path(__file__).resolve().parents[1]/"backend/app.py")).run()
            app.selectbox[0].select("Research paper").run()
            app.file_uploader[0].set_value([("study.md", PAPER.encode(), "text/markdown")]).run()
            next(b for b in app.button if b.label == "Prepare defense").click().run()
            next(box for box in app.checkbox if box.label == "I reviewed the research profile").check().run()
            next(b for b in app.button if b.label == "Confirm profile and budget").click().run()
            self.assertFalse(next(b for b in app.button if b.label == "Start defense").disabled)
            next(item for item in app.text_area if item.label == "Research fields (one per line)").set_value("Education\nPublic policy").run()
            self.assertTrue(next(b for b in app.button if b.label == "Start defense").disabled)
            self.assertTrue(next(b for b in app.button if b.label == "Confirm profile and budget").disabled)
            next(b for b in app.button if b.label == "Apply profile and remap").click().run()
            self.assertIsNone(app.session_state["research_plan"])
            self.assertEqual(app.session_state["research_profile_correction"].fields, ("Education", "Public policy"))
            self.assertEqual(next(item for item in app.text_area if item.label == "Research fields (one per line)").value,
                             "Education\nPublic policy")
            next(b for b in app.button if b.label == "Retry research map").click().run()
            self.assertFalse(app.exception)
            self.assertEqual(app.session_state["research_plan"].profile.host_description.fields, ("Education", "Public policy"))
            self.assertFalse(app.session_state["research_plan_approved"])
            self.assertEqual([r.snapshot() for r in requests[1:]], [requests[1].snapshot()]*2)
            from backend.defense_session import ResearchDefenseSession
            from backend.question_generator import CoachingReport
            from tests.test_research_coverage import mocked_move
            completed = ResearchDefenseSession.create(app.session_state["research_plan"], 8, "research", "proposal")
            completed.apply_move(mocked_move([ProjectFile("study.md", PAPER, "research_text")], "offline-key",
                                           history=[], context=completed.context()))
            completed.submit_answer("We would compare the recorded waiting times.")
            completed.end()
            app.session_state["defense_session"] = completed
            app.session_state["defense_run_id"] = 1
            app.session_state["research_coaching"] = CoachingReport("Previous scope feedback.", [], [], "Practice again.")
            app.run()
            self.assertTrue(any(item.value == "Previous scope feedback." for item in app.markdown))
            next(item for item in app.text_input if item.label == "Research setting (optional)").set_value("City campus").run()
            next(b for b in app.button if b.label == "Apply profile and remap").click().run()
            self.assertNotIn("defense_session", app.session_state)
            self.assertNotIn("research_coaching", app.session_state)
            self.assertNotEqual(app.session_state["research_plan"].id, completed.plan.id)
            self.assertEqual(app.session_state["research_plan"].profile.setting, "City campus")
            self.assertEqual(completed.turns[0].answer, "We would compare the recorded waiting times.")
            app.file_uploader[0].set_value([("study.md", (PAPER+"New scope\n").encode(), "text/markdown")]).run()
            self.assertNotIn("research_profile_correction", app.session_state)
            self.assertNotIn("research_plan", app.session_state)
            self.assertFalse(app.exception)
            self.assertEqual(len(requests), 4)

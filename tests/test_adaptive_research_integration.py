"""Complete profile-aware defenses through authenticated HTTP/WebSocket seams.

AI responses and time are synthetic. These checks establish retained context and
room behavior, not live subject expertise or natural-language quality.
"""

from copy import deepcopy
import unittest
from unittest.mock import patch

from backend.question_generator import (
    CoachingDraft, InvalidQuestionResponse, QuestionGenerationError,
    RESEARCH_PANELISTS, SubmissionDraft, generate_coaching_report,
    generate_research_move, interpret_submission,
)
from backend.research_plan import generate_research_plan
from backend.timed_turn import ANSWER_MS, VOTE_MS
from tests import test_research_coverage as coverage
from tests.test_research_coverage import Client, PAPER, proposal


CORRECTION = {"fields": ["Education", "Software engineering"],
              "approaches": ["qualitative", "computational/design"],
              "setting": "One university campus"}
ANSWER = "We will measure waiting times and explain the limits of a single-campus pilot."


class AdaptiveResearchIntegrationTests(unittest.TestCase):
    setUp = coverage.CoverageProtocolTests.setUp
    until = coverage.CoverageProtocolTests.until

    def test_research_defense_keeps_corrected_scope_through_twelve_questions(self):
        self.defense("research")

    def test_mixed_defense_keeps_corrected_scope_and_code_citations(self):
        self.defense("mixed")

    def defense(self, mode):
        uploads = [("research_files", ("paper.md", PAPER.encode(), "text/markdown"))]
        if mode == "mixed":
            uploads.append(("files", ("queue.py", b"    save_reservation(student_id)\n", "text/x-python")))
        response = self.client.post("/api/rooms", data={"host_name": "Alex", "defense_type": mode,
                                                     "research_stage": "proposal"}, files=uploads)
        self.assertEqual(response.status_code, 201, response.text)
        host = response.json()
        code = host["room_code"]
        guest = self.client.post(f"/api/rooms/{code}/join", json={"name": "Sam"}).json()
        scope_requests, mapping_inputs = [], []
        question_requests = []
        next_failure = False

        def mapping(files, key, model, **kwargs):
            mapping_inputs.append(kwargs.get("profile_correction"))
            # This fixture supplies one completed provider response; streaming
            # progress is exercised separately by the existing mapping tests.
            kwargs.pop("on_progress", None)
            if len(mapping_inputs) == 2:
                raise QuestionGenerationError("Synthetic map failure")
            paper_id = next(i for i, file in enumerate(files, 1) if file.kind.startswith("research"))
            output = {"topics": [
                {"title": f"Pilot decision {i + 1}", "objective": "Explain the pilot decision and its evidence.",
                 "panelist": RESEARCH_PANELISTS[i % 4], "references": [{"source_file": paper_id, "evidence_line": i + 1}], "gaps": []}
                for i in range(12)], "uncertainties": [],
                "profile": {"fields": ["Education"], "approaches": ["unclear"],
                            "setting": "University campus", "explanation": "The text describes proposed queue-pilot decisions.",
                            "references": [{"source_file": paper_id, "evidence_line": 1}],
                            "uncertainties": ["The text does not establish a qualitative analysis method."]}}
            return generate_research_plan(files, key, model, client=Client(output), **kwargs)

        def question(files, key, *, history, context, **kwargs):
            nonlocal next_failure
            scope_requests.append(deepcopy(context))
            question_requests.append(len(history))
            if len(history) == 2 and not next_failure:
                next_failure = True
                raise InvalidQuestionResponse("Synthetic invalid citation; accepted answer is retained.")
            output = proposal(context, history, followup=bool(history and history[-1].timed_out), mixed=mode == "mixed")
            if output["action"] == "ask":
                code_citation = mode == "mixed" and len(history) % 2 == 1
                output["source_file"] = next(i for i, file in enumerate(files, 1)
                                             if file.kind.startswith("research") != code_citation)
            return generate_research_move(files, key, history=history, context=context, client=Client(output), **kwargs)

        def interpret(files, key, *, submission, **kwargs):
            scope_requests.append(deepcopy(kwargs["research_context"]))
            if submission == "Explain in Bisaya":
                output = SubmissionDraft(action="clarify", clarification="Unsang pilot decision ang inyong gi-basehan, ug ngano?", probe=None)
            elif submission == "We would use the pilot decision.":
                output = SubmissionDraft(action="probe", clarification=None, probe={
                    "request": "Which documented pilot decision supports that choice?",
                    "references": [{"source_file": next(i for i, file in enumerate(files, 1)
                                                         if file.kind.startswith("research")), "evidence_line": 5}]})
            else:
                output = SubmissionDraft(action="answer", clarification=None, probe=None)
            return interpret_submission(files, key, submission=submission, client=Client(output), **kwargs)

        def coach(files, history, key, model, **kwargs):
            scope_requests.append(deepcopy(kwargs["research_context"]))
            self.assertEqual(len(history), 12)
            self.assertTrue(history[0].timed_out)
            self.assertEqual(history[4].probe.reply, "Decision five supports the pilot design.")
            output = CoachingDraft(summary="The approved budget ended with unresolved topics. The opening question timed out.",
                strengths=[{"turn": 4, "text": "Alex identified the pilot decision."}],
                improvements=[{"turn": 0, "text": "Practice the unanswered pilot issue."}],
                next_step="Review outstanding topics and justify the stated approach.")
            return generate_coaching_report(files, history, key, model, client=Client(output), **kwargs)

        with patch("backend.rooms.planning.generate_research_plan", side_effect=mapping) as mapper, \
                patch("backend.rooms.questions.generate_research_move", side_effect=question) as generator, \
                patch("backend.rooms.submissions.interpret_submission", side_effect=interpret), \
                patch("backend.rooms.coaching.generate_coaching_report", side_effect=coach) as coaching, \
                self.client.websocket_connect(f"/ws/{code}") as h, \
                self.client.websocket_connect(f"/ws/{code}") as g:
            h.send_json({"type": "hello", "token": host["player_token"]}); self.until(h, "lobby")
            g.send_json({"type": "hello", "token": guest["player_token"]}); self.until(g, "lobby")
            h.send_json({"type": "prepare_research_plan"})
            original = self.until(h, research_planning_status="ready")["research_plan"]
            self.until(g, research_planning_status="ready")
            h.send_json({"type": "prepare_research_plan", "profile_correction": CORRECTION})
            failed = self.until(h, research_planning_status="failed")
            self.until(g, research_planning_status="failed")
            self.assertEqual(failed["research_profile_correction"], CORRECTION)
            self.assertEqual(failed["turns"], [])
            h.send_json({"type": "retry_research_plan"})
            ready = self.until(h, research_planning_status="ready")
            self.until(g, research_planning_status="ready")
            plan = ready["research_plan"]
            fixed = plan["profile"]
            self.assertNotEqual(plan["id"], original["id"])
            self.assertEqual(fixed["host_description"], CORRECTION)
            self.assertEqual(fixed["source_description"]["approaches"], ["unclear"])
            self.assertEqual(fixed["references"][0]["evidence_text"], PAPER.splitlines()[0])
            approval = {"type": "approve_research_plan", "plan_id": plan["id"], "question_budget": 12,
                        "confirm_profile": True, "acknowledge_uncertainty": True}
            # Drain host presence publication before asserting the guest's private error.
            g.send_json(approval)
            self.assertIn("Only the host", g.receive_json()["message"])
            h.send_json({**approval, "plan_id": original["id"]})
            self.assertIn("changed", h.receive_json()["message"])
            h.send_json({**approval, "acknowledge_uncertainty": False})
            self.assertIn("unclear", h.receive_json()["message"].lower())
            h.send_json(approval)
            self.until(h, research_plan_approved=True); self.until(g, research_plan_approved=True)
            self.assertEqual(generator.call_count, 0)
            h.send_json({"type": "start", "plan_id": plan["id"], "question_budget": 12})
            for index in range(12):
                for socket in (h, g):
                    voting = self.until(socket, "voting", index + 1)
                    self.assertEqual(voting["research_plan"]["profile"], fixed)
                    turn = voting["turns"][-1]
                    expected = "    save_reservation(student_id)" if turn["filename"] == "queue.py" else PAPER.splitlines()[turn["evidence_line"] - 1]
                    self.assertEqual(turn["evidence_text"], expected)
                seat = index % 2
                h.send_json({"type": "cast_vote", "seat": seat})
                self.until(h, "voting", index + 1); self.until(g, "voting", index + 1)
                self.now += VOTE_MS + 1
                h.send_json({"type": "send_chat", "text": "private planning detail"})
                for socket in (h, g): self.until(socket, "question", index + 1)
                if index == 0:
                    self.now += ANSWER_MS + 1
                    h.send_json({"type": "send_chat", "text": "Catch up deadline"})
                    continue
                speaker = h if seat == 0 else g
                if index == 3:
                    speaker.send_json({"type": "submit_answer", "turn": index, "answer": "Explain in Bisaya"})
                    for socket in (h, g):
                        clarified = self.until(socket, "question", index + 1)
                        while not clarified["turns"][-1]["clarifications"]:
                            clarified = self.until(socket, "question", index + 1)
                        self.assertEqual(clarified["turns"][-1]["clarifications"][0]["request"], "Explain in Bisaya")
                if index == 4:
                    speaker.send_json({"type": "submit_answer", "turn": index, "answer": "We would use the pilot decision."})
                    for socket in (h, g): probed = self.until(socket, "probe", index + 1)
                    before = generator.call_count
                    with self.client.websocket_connect(f"/ws/{code}") as reconnect:
                        reconnect.send_json({"type": "hello", "token": guest["player_token"]})
                        restored = self.until(reconnect, "probe", index + 1)
                        self.assertEqual(restored["turns"], probed["turns"])
                        self.assertEqual(restored["research_plan"]["profile"], fixed)
                    self.assertEqual(generator.call_count, before)
                    # Joining publishes presence to existing clients; consume it.
                    for socket in (h, g): self.until(socket, "probe", index + 1)
                    speaker.send_json({"type": "submit_probe_reply", "turn": index,
                        "probe_id": probed["turns"][-1]["probe"]["id"], "answer": "Decision five supports the pilot design."})
                else:
                    speaker.send_json({"type": "submit_answer", "turn": index, "answer": ANSWER})
            for socket in (h, g):
                final = self.until(socket, "complete", 12, feedback_status="ready")
                self.assertEqual(final["completion_reason"], "budget exhausted")
                self.assertTrue(final["turns"][0]["timed_out"])
                self.assertEqual(final["turns"][1]["answer"], ANSWER)
                self.assertEqual(final["turns"][4]["answered_by"], "Alex")
                self.assertEqual(final["turns"][4]["probe"]["reply"], "Decision five supports the pilot design.")
                self.assertEqual(final["coverage"]["topic-12"]["status"], "pending")
                self.assertIn("unresolved", final["feedback"]["summary"])
                self.assertEqual(final["research_plan"]["profile"], fixed)
            with self.client.websocket_connect(f"/ws/{code}") as reconnect:
                reconnect.send_json({"type": "hello", "token": guest["player_token"]})
                restored = self.until(reconnect, "complete", 12, feedback_status="ready")
                self.assertEqual(restored["turns"], final["turns"])
                self.assertEqual(restored["coverage"], final["coverage"])
            self.assertEqual(mapper.call_count, 3)
            self.assertEqual(generator.call_count, 14)  # 12 questions, final assessment and one automatic retry.
            self.assertEqual(coaching.call_count, 1)
        self.assertEqual([value.snapshot() for value in mapping_inputs[1:]], [CORRECTION, CORRECTION])
        self.assertEqual(question_requests.count(2), 2)
        for context in scope_requests:
            self.assertEqual(context["plan"]["profile"], fixed)
            self.assertNotIn("private planning detail", str(context))
            self.assertNotIn("owner_account_id", context)

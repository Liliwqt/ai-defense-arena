"""Offline checks for project-wide grounded questions."""

import unittest
from types import SimpleNamespace
from unittest.mock import patch

import httpx2
from openai import APIConnectionError, APIStatusError, OpenAIError

from project_files import ProjectFile
from question_generator import (
    AnsweredQuestion,
    CoachingDraft,
    CoachingPoint,
    QuestionDraft,
    NextMoveDraft,
    PRODUCT_JUDGE,
    CRITICAL_JUDGE,
    generate_next_move,
    generate_panel_question,
    QuestionGenerationError,
    build_project_source,
    describe_openai_error,
    generate_coaching_report,
    generate_first_question,
)


class FakeClient:
    def __init__(self, parsed=None, error=None):
        self.responses = self
        self.parsed = parsed
        self.error = error
        self.request = None

    def parse(self, **kwargs):
        self.request = kwargs
        if self.error:
            raise self.error
        return SimpleNamespace(output_parsed=self.parsed)


class QuestionGeneratorTests(unittest.TestCase):
    def setUp(self):
        self.files = [
            ProjectFile("README.md", "# Queue\nThe project uses SQLite.\n"),
            ProjectFile("src/queue.py", "# Storage\nDATABASE = 'queue.db'\n"),
        ]

    def test_question_reads_all_files_and_cites_exact_code_line(self):
        client = FakeClient(
            QuestionDraft(lead_in="", question="  Why use a local database?  ", source_file=2, evidence_line=2)
        )

        result = generate_first_question(self.files, "test-key", client=client)

        self.assertEqual(result.lead_in, "")
        self.assertEqual(result.question, "Why use a local database?")
        self.assertEqual(result.filename, "src/queue.py")
        self.assertEqual(result.evidence_line, 2)
        self.assertEqual(result.evidence_text, "DATABASE = 'queue.db'")
        self.assertEqual(client.request["model"], "gpt-6-luna")
        self.assertEqual(client.request["reasoning"], {"effort": "low"})
        self.assertIs(client.request["store"], False)
        prompt = client.request["input"][1]["content"]
        self.assertIn("FILE 1: README.md", prompt)
        self.assertIn("FILE 2: src/queue.py", prompt)
        self.assertIn("2: DATABASE = 'queue.db'", prompt)
        self.assertIn("Eligible citation file IDs: [2]", prompt)

    def test_panelist_reaction_is_bounded_to_two_short_sentences(self):
        too_long = QuestionDraft(lead_in="x" * 301, question="Why SQLite?", source_file=2, evidence_line=2)
        with self.assertRaisesRegex(QuestionGenerationError, "too long"):
            generate_first_question(self.files, "test-key", client=FakeClient(too_long))
        too_many = QuestionDraft(lead_in="One. Two. Three.", question="Why SQLite?", source_file=2, evidence_line=2)
        with self.assertRaisesRegex(QuestionGenerationError, "more than two"):
            generate_first_question(self.files, "test-key", client=FakeClient(too_many))

    def test_document_citation_is_rejected_when_code_exists(self):
        client = FakeClient(QuestionDraft(lead_in="", question="Why SQLite?", source_file=1, evidence_line=2))
        with self.assertRaisesRegex(QuestionGenerationError, "invalid project file"):
            generate_first_question(self.files, "test-key", client=client)

    def test_unknown_file_id_is_rejected(self):
        client = FakeClient(QuestionDraft(lead_in="", question="Why SQLite?", source_file=99, evidence_line=2))
        with self.assertRaisesRegex(QuestionGenerationError, "invalid project file"):
            generate_first_question(self.files, "test-key", client=client)

    def test_invalid_line_is_rejected(self):
        client = FakeClient(QuestionDraft(lead_in="", question="Why SQLite?", source_file=2, evidence_line=99))
        with self.assertRaisesRegex(QuestionGenerationError, "invalid source line"):
            generate_first_question(self.files, "test-key", client=client)

    def test_blank_line_is_rejected(self):
        files = [ProjectFile("src/queue.py", "\nDATABASE = 'queue.db'\n")]
        client = FakeClient(QuestionDraft(lead_in="", question="Why SQLite?", source_file=1, evidence_line=1))
        with self.assertRaisesRegex(QuestionGenerationError, "invalid source line"):
            generate_first_question(files, "test-key", client=client)

    def test_document_only_project_can_cite_document(self):
        files = [self.files[0]]
        client = FakeClient(QuestionDraft(lead_in="", question="Why SQLite?", source_file=1, evidence_line=2))
        result = generate_first_question(files, "test-key", client=client)
        self.assertEqual(result.filename, "README.md")

    def test_empty_files_are_not_offered_as_citations(self):
        source, lookup, eligible = build_project_source(
            [self.files[0], ProjectFile("src/empty.py", "")]
        )
        self.assertIn("README.md", source)
        self.assertNotIn("empty.py", source)
        self.assertEqual(set(lookup), {1})
        self.assertEqual(eligible, {1})

    def test_oversized_project_is_rejected(self):
        files = [ProjectFile("src/large.py", "a" * 600_001)]
        with self.assertRaisesRegex(QuestionGenerationError, "600 KB"):
            build_project_source(files)

    def test_missing_key_does_not_call_api(self):
        client = FakeClient(QuestionDraft(lead_in="", question="Why SQLite?", source_file=2, evidence_line=2))
        with self.assertRaisesRegex(QuestionGenerationError, "OPENAI_API_KEY"):
            generate_first_question(self.files, None, client=client)
        self.assertIsNone(client.request)

    def test_surrounding_whitespace_is_removed_from_key(self):
        client = FakeClient(QuestionDraft(lead_in="", question="Why SQLite?", source_file=2, evidence_line=2))
        with patch("question_generator.OpenAI", return_value=client) as constructor:
            generate_first_question(self.files, "  test-key\n")
        self.assertEqual(constructor.call_args.kwargs["api_key"], "test-key")

    def test_embedded_whitespace_in_key_is_rejected(self):
        client = FakeClient(QuestionDraft(lead_in="", question="Why SQLite?", source_file=2, evidence_line=2))
        with self.assertRaisesRegex(QuestionGenerationError, "contains whitespace"):
            generate_first_question(self.files, "test\nkey", client=client)
        self.assertIsNone(client.request)

    def test_api_error_remains_retryable(self):
        client = FakeClient(error=OpenAIError("Service unavailable"))
        with self.assertRaises(OpenAIError):
            generate_first_question(self.files, "test-key", client=client)


class AdaptiveMoveTests(unittest.TestCase):
    def setUp(self):
        self.files = [ProjectFile("README.md", "# Queue\nStudents reserve before walking in.\n"),
                      ProjectFile("queue.py", "def reserve():\n    return 1\n")]
        self.history = [AnsweredQuestion(
            "Security Reviewer", "Who sees names?", "Staff only.",
            lead_in="You said access is limited.",
        )]

    def test_product_can_cite_document_when_code_exists(self):
        draft = NextMoveDraft(action="ask", panelist=PRODUCT_JUDGE,
                              lead_in="You described staff-only access. Let's connect that to user value.",
                              question="How will you validate the reservation workflow?",
                              source_file=1, evidence_line=2)
        client = FakeClient(draft)
        move = generate_next_move(self.files, "test-key", history=self.history,
                                  allowed_panelists=(PRODUCT_JUDGE,), may_complete=False, client=client)
        self.assertEqual(move.panelist, PRODUCT_JUDGE)
        self.assertEqual(move.question.lead_in,
                         "You described staff-only access. Let's connect that to user value.")
        self.assertEqual(move.question.evidence_text, "Students reserve before walking in.")
        system_prompt = client.request["input"][0]["content"]
        self.assertIn("user value", system_prompt)
        self.assertIn("Taglish", system_prompt)
        self.assertIn("Avoid automatic praise", system_prompt)
        self.assertIn('"lead_in": "You said access is limited."',
                      client.request["input"][1]["content"])

    def test_critical_can_cite_code_and_early_completion_is_rejected(self):
        draft = NextMoveDraft(action="ask", panelist=CRITICAL_JUDGE, lead_in="I heard your answer.",
                              question="What supports this assumption?", source_file=2, evidence_line=2)
        move = generate_next_move(self.files, "test-key", history=self.history,
                                  allowed_panelists=(CRITICAL_JUDGE,), may_complete=False,
                                  client=FakeClient(draft))
        self.assertEqual(move.question.filename, "queue.py")
        done = NextMoveDraft(action="complete", panelist=None, lead_in=None, question=None,
                             source_file=None, evidence_line=None)
        with self.assertRaisesRegex(QuestionGenerationError, "too early"):
            generate_next_move(self.files, "test-key", history=self.history,
                               allowed_panelists=(CRITICAL_JUDGE,), may_complete=False,
                               client=FakeClient(done))

    def test_security_cannot_cite_document_when_code_exists(self):
        draft = NextMoveDraft(action="ask", panelist="Security Reviewer", lead_in="I heard your answer.",
                              question="How are names protected?", source_file=1, evidence_line=2)
        with self.assertRaisesRegex(QuestionGenerationError, "invalid project file"):
            generate_next_move(self.files, "test-key", history=self.history,
                               allowed_panelists=("Security Reviewer",), may_complete=False,
                               client=FakeClient(draft))

    def test_complete_requires_no_question_fields(self):
        draft = NextMoveDraft(action="complete", panelist=None, lead_in=None, question="Extra?",
                              source_file=None, evidence_line=None)
        with self.assertRaisesRegex(QuestionGenerationError, "too early"):
            generate_next_move(self.files, "test-key", history=self.history,
                               allowed_panelists=(CRITICAL_JUDGE,), may_complete=True,
                               client=FakeClient(draft))


    def test_completion_rejects_stray_dialogue(self):
        draft = NextMoveDraft(action="complete", panelist=None, lead_in="One more thought.",
                              question=None, source_file=None, evidence_line=None)
        with self.assertRaisesRegex(QuestionGenerationError, "too early"):
            generate_next_move(self.files, "test-key", history=self.history,
                               allowed_panelists=(CRITICAL_JUDGE,), may_complete=True,
                               client=FakeClient(draft))

    def test_followup_after_timeout_receives_no_invented_answer(self):
        draft = NextMoveDraft(action="ask", panelist="Security Reviewer",
                              lead_in="No answer was submitted, so this risk remains open.",
                              question="How would you restrict access?", source_file=2, evidence_line=2)
        client = FakeClient(draft)
        history = [AnsweredQuestion("Security Reviewer", "Who sees names?", None, True)]
        move = generate_next_move(self.files, "test-key", history=history,
                                  allowed_panelists=("Security Reviewer", PRODUCT_JUDGE),
                                  may_complete=False, client=client)
        self.assertEqual(move.panelist, "Security Reviewer")
        self.assertEqual(move.question.lead_in,
                         "No answer was submitted, so this risk remains open.")
        prompt = client.request["input"][1]["content"]
        self.assertIn('"answer": null', prompt)
        self.assertIn('"timed_out": true', prompt)
        self.assertIn("Never invent an answer", client.request["input"][0]["content"])


class CoachingReportTests(unittest.TestCase):
    def setUp(self):
        self.files = [
            ProjectFile("README.md", "# Queue\nThe project uses SQLite.\n"),
            ProjectFile("src/queue.py", "# Storage\nDATABASE = 'queue.db'\n"),
        ]
        self.history = [
            AnsweredQuestion(
                "Technical Architect", "Why SQLite?", "Simplicity for a prototype.",
                lead_in="Let's examine the storage tradeoff.",
            ),
            AnsweredQuestion("Security Reviewer", "How do you protect names?", "Parameterised queries."),
            AnsweredQuestion("Technical Architect", "What about concurrency?", "Single-writer SQLite is fine here."),
            AnsweredQuestion("Security Reviewer", "Who can see results?", "Only authenticated users."),
        ]

    def _draft(self, summary="Good work.", strengths=None, improvements=None, next_step="Practice more."):
        return CoachingDraft(
            summary=summary,
            strengths=strengths or [CoachingPoint(turn=0, text="Clear rationale for SQLite choice.")],
            improvements=improvements or [CoachingPoint(turn=1, text="Expand on input validation.")],
            next_step=next_step,
        )

    def test_valid_report_is_returned_with_all_fields(self):
        client = FakeClient(self._draft())
        result = generate_coaching_report(self.files, self.history, "test-key", client=client)
        self.assertEqual(result.summary, "Good work.")
        self.assertEqual(result.strengths, [{"turn": 0, "text": "Clear rationale for SQLite choice."}])
        self.assertEqual(result.improvements, [{"turn": 1, "text": "Expand on input validation."}])
        self.assertEqual(result.next_step, "Practice more.")
        prompt = client.request["input"][1]["content"]
        self.assertIn("FILE 1: README.md", prompt)
        self.assertIn("FILE 2: src/queue.py", prompt)
        self.assertIn("Why SQLite?", prompt)
        self.assertIn("Let's examine the storage tradeoff.", prompt)
        self.assertIn("Only authenticated users.", prompt)
        self.assertEqual(client.request["reasoning"], {"effort": "low"})
        self.assertIs(client.request["store"], False)

    def test_invalid_turn_reference_is_rejected(self):
        draft = self._draft(strengths=[CoachingPoint(turn=5, text="Good.")])
        client = FakeClient(draft)
        with self.assertRaisesRegex(QuestionGenerationError, "invalid turn"):
            generate_coaching_report(self.files, self.history, "test-key", client=client)

    def test_empty_strength_text_is_rejected(self):
        draft = self._draft(strengths=[CoachingPoint(turn=0, text="   ")])
        client = FakeClient(draft)
        with self.assertRaisesRegex(QuestionGenerationError, "empty"):
            generate_coaching_report(self.files, self.history, "test-key", client=client)

    def test_empty_summary_is_rejected(self):
        draft = self._draft(summary="   ")
        client = FakeClient(draft)
        with self.assertRaisesRegex(QuestionGenerationError, "summary is empty"):
            generate_coaching_report(self.files, self.history, "test-key", client=client)

    def test_empty_next_step_is_rejected(self):
        draft = self._draft(next_step="   ")
        client = FakeClient(draft)
        with self.assertRaisesRegex(QuestionGenerationError, "next step is empty"):
            generate_coaching_report(self.files, self.history, "test-key", client=client)

    def test_none_output_is_rejected(self):
        client = FakeClient(None)
        with self.assertRaisesRegex(QuestionGenerationError, "no coaching report"):
            generate_coaching_report(self.files, self.history, "test-key", client=client)

    def test_eight_turn_report_accepts_last_turn_reference(self):
        history = self.history + self.history
        draft = self._draft(strengths=[CoachingPoint(turn=7, text="Strong final answer.")])
        client = FakeClient(draft)
        result = generate_coaching_report(self.files, history, "test-key", client=client)
        self.assertEqual(result.strengths[0]["turn"], 7)
        self.assertIn("0 to 7", client.request["input"][0]["content"])

    def test_eight_turn_report_rejects_out_of_range_reference(self):
        history = self.history + self.history
        draft = self._draft(strengths=[CoachingPoint(turn=8, text="Invalid.")])
        with self.assertRaisesRegex(QuestionGenerationError, "invalid turn"):
            generate_coaching_report(self.files, history, "test-key", client=FakeClient(draft))

    def test_wrong_turn_count_is_rejected(self):
        short_history = self.history[:3]
        client = FakeClient(self._draft())
        with self.assertRaisesRegex(QuestionGenerationError, "4 to 8 resolved turns"):
            generate_coaching_report(self.files, short_history, "test-key", client=client)
        self.assertIsNone(client.request)

    def test_missing_api_key_does_not_call_api(self):
        client = FakeClient(self._draft())
        with self.assertRaisesRegex(QuestionGenerationError, "OPENAI_API_KEY"):
            generate_coaching_report(self.files, self.history, None, client=client)
        self.assertIsNone(client.request)

    def test_whitespace_key_is_rejected(self):
        client = FakeClient(self._draft())
        with self.assertRaisesRegex(QuestionGenerationError, "contains whitespace"):
            generate_coaching_report(self.files, self.history, "test\nkey", client=client)
        self.assertIsNone(client.request)

    def test_all_four_turn_references_are_valid(self):
        draft = self._draft(
            strengths=[CoachingPoint(turn=t, text=f"Good on turn {t}.") for t in range(4)],
            improvements=[CoachingPoint(turn=t, text=f"Improve turn {t}.") for t in range(4)],
        )
        client = FakeClient(draft)
        result = generate_coaching_report(self.files, self.history, "test-key", client=client)
        self.assertEqual(len(result.strengths), 4)
        self.assertEqual(len(result.improvements), 4)


    def test_all_timeouts_allow_empty_strengths_and_reject_invented_strength(self):
        history = [AnsweredQuestion(item.panelist, item.question, None, True) for item in self.history]
        draft = CoachingDraft(summary="Questions went unanswered.", strengths=[],
                              improvements=[CoachingPoint(turn=3, text="Practice this missed turn.")],
                              next_step="Practice together.")
        client = FakeClient(draft)
        result = generate_coaching_report(self.files, history, "test-key", client=client)
        self.assertEqual(result.strengths, [])
        self.assertEqual(result.improvements[0]["turn"], 3)
        self.assertIn('"timed_out": true', client.request["input"][1]["content"])
        draft.strengths = [CoachingPoint(turn=0, text="Imagined answer.")]
        with self.assertRaisesRegex(QuestionGenerationError, "unanswered turn"):
            generate_coaching_report(self.files, history, "test-key", client=FakeClient(draft))


class ErrorMessageTests(unittest.TestCase):
    def make_status_error(self, status, message="request failed", code=None, error_type=None):
        request = httpx2.Request("POST", "https://api.openai.com/v1/responses")
        response = httpx2.Response(status, request=request)
        body = {}
        if code:
            body["code"] = code
        if error_type:
            body["type"] = error_type
        return APIStatusError(message, response=response, body=body)

    def test_invalid_key_has_clear_message(self):
        error = self.make_status_error(401)
        message = describe_openai_error(error, "gpt-6-luna", "secret-key")
        self.assertIn("OPENAI_API_KEY", message)
        self.assertIn("401", message)

    def test_unavailable_model_names_override(self):
        error = self.make_status_error(404)
        message = describe_openai_error(error, "gpt-6-luna")
        self.assertIn("gpt-6-luna", message)
        self.assertIn("OPENAI_MODEL", message)

    def test_quota_error_is_distinct_from_rate_limit(self):
        quota = self.make_status_error(429, code="credit_balance_exhausted")
        limit = self.make_status_error(429, code="rate_limit_exceeded")
        self.assertIn("billing", describe_openai_error(quota, "gpt-6-luna"))
        self.assertIn("Wait briefly", describe_openai_error(limit, "gpt-6-luna"))
        quota_without_code = self.make_status_error(429, error_type="insufficient_quota")
        self.assertIn("billing", describe_openai_error(quota_without_code, "gpt-6-luna"))

    def test_bad_request_includes_redacted_detail(self):
        error = self.make_status_error(400, "Bad model; key secret-key")
        message = describe_openai_error(error, "gpt-6-luna", "secret-key")
        self.assertIn("Bad model", message)
        self.assertNotIn("secret-key", message)

    def test_connection_error_explains_network_issue(self):
        request = httpx2.Request("POST", "https://api.openai.com/v1/responses")
        error = APIConnectionError(request=request)
        self.assertIn("internet connection", describe_openai_error(error, "gpt-6-luna"))


if __name__ == "__main__":
    unittest.main()

"""Conversation-context checks; all AI responses are mocked."""

import json
import unittest

from defense_session import DefenseSession
from project_files import ProjectFile
from question_generator import (
    AnsweredQuestion, ClarificationExchange, CoachingDraft, CoachingPoint,
    CODE_PANELISTS, RESEARCH_PANELISTS, GroundedQuestion, NextMoveDraft,
    SubmissionDraft, generate_next_move, generate_coaching_report,
    interpret_submission, serialize_transcript, _language_guidance,
)
from test_question_generator import FakeClient


class ConversationContextTests(unittest.TestCase):
    def setUp(self):
        self.files = [ProjectFile("app.py", "STAFF_ONLY = True\n")]
        self.citation = GroundedQuestion("Who sees the names?", "app.py", 1,
                                        "STAFF_ONLY = True", "", "Line 1", "source")
        self.history = [AnsweredQuestion(
            "Technical Architect", self.citation.question,
            "We check staff authentication before returning reservation names.",
            clarifications=(ClarificationExchange("Please use simple English.", "Who can see the names?"),),
            speaker_name='Sam "admin"', citation=self.citation,
        )]

    def next_request(self, history=None):
        client = FakeClient(NextMoveDraft(action="ask", panelist="Security Reviewer", lead_in="",
                                          question="How is staff access checked?", source_file=1, evidence_line=1))
        move = generate_next_move(self.files, "test-key", history=history or self.history,
                                  allowed_panelists=("Security Reviewer",), may_complete=False, client=client)
        self.assertEqual(move.question.lead_in, "")
        return client.request

    def test_history_roundtrips_exact_citation_and_escaped_server_name(self):
        text = serialize_transcript(self.history)
        data = json.loads(text)[0]
        self.assertEqual(data['speaker_name'], 'Sam "admin"')
        self.assertEqual(data['citation']['excerpt'], "STAFF_ONLY = True")
        self.assertEqual(data['citation']['location'], "Line 1")
        self.assertEqual(data['turn'], 0)
        self.assertEqual(data['question_number'], 1)
        self.assertEqual(data['clarifications'][0]['request'], 'Please use simple English.')
        self.assertEqual(data['citation']['kind'], 'source')

    def test_generation_interpretation_and_coaching_share_enriched_transcript(self):
        expected = serialize_transcript(self.history)
        request = self.next_request()
        self.assertIn(expected, request['input'][1]['content'])
        self.assertIn('Allowed citation file IDs by panelist: {"Security Reviewer": [1]}', request['input'][1]['content'])
        self.assertIn('not another question or task', request['input'][0]['content'])
        client = FakeClient(SubmissionDraft(action="clarify", clarification="How is access restricted to staff?"))
        interpret_submission(self.files, "test-key", panelist="Security Reviewer", question=self.citation,
                             submission="Give an example", history=self.history, client=client)
        self.assertIn(expected, client.request['input'][1]['content'])
        self.assertEqual(client.request['input'][0]['content'].count('Security Reviewer:'), 1)
        history = self.history * 4
        client = FakeClient(CoachingDraft(summary="The team explained the access check.",
            strengths=[CoachingPoint(turn=0, text="Described the intended check.")],
            improvements=[CoachingPoint(turn=1, text="Show a test of it.")], next_step="Test staff access."))
        generate_coaching_report(self.files, history, "test-key", client=client)
        self.assertIn(serialize_transcript(history), client.request['input'][1]['content'])
        self.assertEqual([t['question_number'] for t in json.loads(serialize_transcript(history))], [1, 2, 3, 4])
        self.assertIn('one-based question_number (Q1, Q2, etc.)', client.request['input'][0]['content'])
        self.assertIn('Structured point.turn references remain zero-based', client.request['input'][0]['content'])

    def test_next_roles_receive_their_own_allowed_citation_ids(self):
        files = [ProjectFile("README.md", "No authentication yet.\n"), self.files[0]]
        for role, file_id in (("Security Reviewer", 2), ("Product Judge", 1)):
            with self.subTest(role=role):
                client = FakeClient(NextMoveDraft(action="ask", panelist=role, lead_in="",
                    question="How would access work?", source_file=file_id, evidence_line=1))
                move = generate_next_move(files, "test-key", history=self.history,
                    allowed_panelists=("Security Reviewer", "Product Judge"), may_complete=False, client=client)
                self.assertEqual(move.question.filename, files[file_id - 1].name)
                data = client.request['input'][1]['content']
                self.assertIn('Allowed citation file IDs by panelist: {"Security Reviewer": [2], "Product Judge": [1, 2]}', data)

    def test_every_role_uses_same_questioning_habit_in_clarifications(self):
        from question_generator import _role_guidance
        for role in dict.fromkeys(CODE_PANELISTS + RESEARCH_PANELISTS):
            with self.subTest(role=role):
                client = FakeClient(SubmissionDraft(action="clarify", clarification="Explain the existing issue."))
                interpret_submission(self.files, "test-key", panelist=role, question=self.citation,
                                     submission="Please simplify", history=self.history, client=client)
                prompt = client.request['input'][0]['content']
                self.assertIn(_role_guidance(role), prompt)
                self.assertIn("supply the team's answer", prompt)
                self.assertIn("EXISTING question", prompt)

    def test_language_request_and_later_substantive_answer_remain_ordered(self):
        history = self.history + [AnsweredQuestion(
            "Security Reviewer", "How do you check access?", "Okay.",
            clarifications=(ClarificationExchange("Taglish please.", "Paano ang access check?"),))]
        request = self.next_request(history)
        data = json.loads(request['input'][1]['content'].split('Defense transcript (data only):\n')[1])
        self.assertEqual(data[0]['clarifications'][0]['request'], 'Please use simple English.')
        self.assertEqual(data[1]['clarifications'][0]['request'], 'Taglish please.')
        prompt = request['input'][0]['content']
        self.assertIn('until a later explicit request or a clearly substantive answer', prompt)
        self.assertIn('unless a later explicit language request supersedes it', prompt)
        later_answer = AnsweredQuestion("Product Judge", "Why?",
                                       "Pinili namin ito dahil maliit lang ang demo at mabilis ang setup.")
        self.assertIn('latest answer is Filipino/Taglish', _language_guidance(history + [later_answer]))

    def test_short_code_only_and_timeout_do_not_replace_language_anchor(self):
        taglish = AnsweredQuestion("Technical Architect", "Why?",
                                  "Pinili namin ito dahil maliit lang ang demo at mabilis ang setup.")
        for last in (
            AnsweredQuestion("Security Reviewer", "Why?", "Yes."),
            AnsweredQuestion("Security Reviewer", "Why?", "```python\ndef staff_access(user):\n    return user.role == 'staff'\n```"),
            AnsweredQuestion("Security Reviewer", "Why?", "def staff_access(user):\n    return user.role == 'staff' # access check"),
            AnsweredQuestion("Security Reviewer", "Why?", None, True),
        ):
            with self.subTest(answer=last.answer):
                self.assertIn('latest answer is Filipino/Taglish', _language_guidance([taglish, last]))

    def test_current_clarification_language_is_available_after_prior_history(self):
        client = FakeClient(SubmissionDraft(action="clarify", clarification="How is staff access checked?"))
        interpret_submission(self.files, "test-key", panelist="Security Reviewer", question=self.citation,
            submission="Please give an example", history=self.history,
            clarifications=(ClarificationExchange('English please.', 'Who has access?'),), client=client)
        data = client.request['input'][1]['content']
        self.assertLess(data.index('Defense transcript'), data.index('Prior clarifications'))
        self.assertIn('English please.', data)
        self.assertIn('Current clarification requests occur after', client.request['input'][0]['content'])

    def test_latest_english_anchor_survives_timeout_after_earlier_taglish(self):
        from question_generator import _conversation_language_anchor
        history = [AnsweredQuestion("Methodology Reviewer", "Why?",
            "Pinili namin ito dahil maliit lang ang demo at mabilis ang setup."),
            AnsweredQuestion("Ethics Reviewer", "How?", "Yes.", clarifications=(
                ClarificationExchange("Please explain in simple English.", "What would you tell a student?"),)),
            AnsweredQuestion("Ethics Reviewer", "How?",
                "We would explain before consent that the pilot is optional and that their registrar service is unchanged."),
            AnsweredQuestion("Impact Reviewer", "Who benefits?", None, True)]
        anchor = _conversation_language_anchor(history)
        self.assertEqual(anchor['language'], 'English')
        self.assertEqual(anchor['turn'], 2)
        self.assertIn('Use English for the dialogue', _language_guidance(history))

    def test_explicit_requests_override_earlier_answers_but_later_answers_can_switch(self):
        from question_generator import _conversation_language_anchor
        history = self.history + [AnsweredQuestion("Security Reviewer", "How?", "Yes.", clarifications=(
            ClarificationExchange("Taglish please.", "Paano ito?"),))]
        self.assertEqual(_conversation_language_anchor(history)['language'], 'Taglish')
        history.append(AnsweredQuestion("Product Judge", "Why?",
            "We would compare their wait times and explain the limits before making a claim."))
        self.assertEqual(_conversation_language_anchor(history)['language'], 'English')
        current = (ClarificationExchange("Could you repeat in Spanish?", "..."),)
        self.assertEqual(_conversation_language_anchor(history, current)['language'], 'Spanish')
        self.assertEqual(_conversation_language_anchor(history, current, 'English please.')['language'], 'English')

    def test_example_requests_do_not_change_language_and_unknown_answers_are_data(self):
        from question_generator import _conversation_language_anchor
        history = [AnsweredQuestion("Methodology Reviewer", "How?", "Yes.", clarifications=(
            ClarificationExchange("Taglish please.", "Paano?"),))]
        self.assertEqual(_conversation_language_anchor(history, (ClarificationExchange(
            "Could you give an example?", "..."),))['language'], 'Taglish')
        history.append(AnsweredQuestion("Ethics Reviewer", "How?",
            "Los participantes recibirán información clara sobre sus derechos antes de aceptar participar."))
        anchor = _conversation_language_anchor(history)
        self.assertEqual(anchor['kind'], 'answer')
        self.assertIsNone(anchor['language'])
        self.assertEqual(anchor['turn'], 1)

    def test_legacy_history_defaults_and_timeout_have_no_answering_speaker(self):
        old = AnsweredQuestion("Technical Architect", "Why?", "An answer.")
        self.assertIsNone(json.loads(serialize_transcript([old]))[0]['citation'])
        timed = AnsweredQuestion("Security Reviewer", "Why?", None, True,
                                speaker_name='Sam', citation=self.citation)
        data = json.loads(serialize_transcript([timed]))[0]
        self.assertIsNone(data['speaker_name'])
        self.assertIsNone(data['answer'])
        self.assertTrue(data['timed_out'])
        self.assertEqual(data['citation']['excerpt'], 'STAFF_ONLY = True')

    def test_session_name_and_citation_are_retained_only_after_valid_answer(self):
        session = DefenseSession.start(self.citation)
        with self.assertRaises(ValueError):
            session.submit_answer(' ', speaker_name='Wrong')
        self.assertIsNone(session.turns[0].speaker_name)
        session.submit_answer('Staff authentication.', speaker_name='Sam')
        history = session.answered_history()
        self.assertEqual(history[0].speaker_name, 'Sam')
        self.assertIs(history[0].citation, self.citation)
        with self.assertRaises(ValueError):
            session.submit_answer('Late answer.', speaker_name='Alex')
        self.assertEqual(session.answered_history(), history)

"""Server-owned assessment metadata is constrained at the funded HTTP boundary."""
import json
import secrets
from dataclasses import asdict
from unittest.mock import patch

import httpx

from backend.openrouter_questions import RunQuestionClient
from backend.provider_allowance import ProviderAllowance
from backend.question_generator import InvalidQuestionResponse
from tests.critical_review_probe import interpret, replay_inputs
from tests.test_openrouter_questions import HTTPClient, IsolatedAllowanceTests, stream_response


class AssessmentResponseContractTests(IsolatedAllowanceTests):
    def request(self, result):
        case, policy, session, _, _ = replay_inputs()
        scope = 'assessment-contract:' + secrets.token_hex(8)
        ProviderAllowance(scope, 'synthetic-benchmark').establish(policy.ceiling_nano, asdict(policy))
        client = RunQuestionClient(scope, 'synthetic-benchmark', session, case.files,
                                   api_key='offline-fixture')
        self.requests = []

        def respond(request):
            self.requests.append(json.loads(request.content))
            return stream_response({'result': result, 'lookup': None})

        with patch('httpx.Client', side_effect=lambda **kw: HTTPClient(
                transport=httpx.MockTransport(respond), **kw)):
            return interpret(client.interaction('Critical Judge', combined=True))

    @staticmethod
    def answer():
        return {'action': 'answer', 'clarification': None, 'probe': None,
                'assessment': {'turn': 6, 'topic_id': 'topic-4', 'status': 'needs clarification',
                               'reason': 'The comparison assumptions still need explanation.'},
                'panelist': 'Critical Judge', 'topic_id': 'topic-4', 'is_follow_up': True}

    def test_wrong_assessment_turn_is_rejected_by_the_requested_response_contract(self):
        result = self.answer()
        result['assessment']['turn'] = 7
        with self.assertRaises(InvalidQuestionResponse):
            self.request(result)
        self.assertEqual(len(self.requests), 1)
        schema = self.requests[0]['response_format']['json_schema']['schema']
        assessment = schema['$defs']['CurrentTopicAssessment']['properties']
        self.assertEqual(assessment['turn']['const'], 6)
        self.assertEqual(assessment['topic_id']['const'], 'topic-4')

    def test_one_candidate_id_resolves_the_complete_next_move(self):
        result = {name: value for name, value in self.answer().items()
                  if name not in {'panelist', 'topic_id', 'is_follow_up'}}
        result['next_move'] = 'move-5'
        decision = self.request(result)
        self.assertEqual((decision.plan.panelist, decision.plan.topic_id, decision.plan.is_follow_up),
                         ('Critical Judge', 'topic-4', True))
        self.assertEqual(decision.plan.assessment.turn, 6)
        body = self.requests[0]
        schema = body['response_format']['json_schema']['schema']
        normal = schema['$defs']['AnswerDecision']['properties']
        self.assertIn('next_move', normal)
        self.assertTrue({'panelist', 'topic_id', 'is_follow_up'}.isdisjoint(normal))
        context = json.JSONDecoder().raw_decode(
            body['messages'][-1]['content'].split('Planning context (data):\n')[1])[0]
        self.assertEqual(context['question_options'][-1], {
            'choice_id': 'move-5', 'panelist': 'Critical Judge',
            'topic_id': 'topic-4', 'is_follow_up': True})

    def test_non_probe_action_rejects_probe_data_at_the_structured_boundary(self):
        result = self.answer()
        result['probe'] = {'request': 'Which comparison assumptions?', 'references': []}
        with self.assertRaises(InvalidQuestionResponse):
            self.request(result)
        self.assertEqual(len(self.requests), 1)

    def test_action_shapes_reject_cross_action_fields_and_malformed_tags(self):
        probe = {'request': 'Which comparison assumptions?', 'references': []}
        answer = {'action': 'answer', 'assessment': self.answer()['assessment'], 'next_move': 'move-5'}
        for result in (
                {**answer, 'clarification': 'Explain the comparison.'},
                {**answer, 'assessment': None},
                {**answer, 'action': ['answer']},
                {**answer, 'action': 'invented-action'},
                {'action': 'clarify', 'clarification': 'Explain the comparison.', 'probe': probe},
                {'action': 'clarify', 'clarification': None},
                {'action': 'probe', 'probe': probe, 'clarification': 'Explain the comparison.'},
                {'action': 'probe', 'probe': None}):
            with self.subTest(result=result), self.assertRaises(InvalidQuestionResponse):
                self.request(result)
            self.assertEqual(len(self.requests), 1)

    def test_canonical_shapes_are_exclusive_in_the_advertised_schema(self):
        expected = {'answer': {'action', 'assessment', 'next_move'},
                    'clarify': {'action', 'clarification'}, 'probe': {'action', 'probe'}}
        values = (
            {'action': 'answer', 'assessment': self.answer()['assessment'], 'next_move': 'move-5'},
            {'action': 'clarify', 'clarification': 'Explain the comparison.'},
            {'action': 'probe', 'probe': {'request': 'Which comparison assumptions?', 'references': []}})
        for result in values:
            with self.subTest(action=result['action']):
                self.assertEqual(self.request(result).action, result['action'])
                schema = self.requests[0]['response_format']['json_schema']['schema']
                variants = schema['$defs']['CombinedSubmissionDraft']['anyOf']
                self.assertEqual(len(variants), 3)
                for variant in variants:
                    definition = schema['$defs'][variant['$ref'].split('/')[-1]]
                    action = definition['properties']['action']['const']
                    self.assertEqual(set(definition['properties']), expected[action])
                    self.assertEqual(set(definition['required']), expected[action])
                    self.assertIs(definition['additionalProperties'], False)

    def test_wrong_topic_noninteger_turn_and_empty_or_oversized_reasons_are_rejected(self):
        for field, value in (('topic_id', 'topic-3'), ('turn', True), ('turn', '6'),
                             ('reason', ''), ('reason', ' \n\t'), ('reason', 'x' * 601)):
            with self.subTest(field=field, value=value):
                result = self.answer()
                result['assessment'][field] = value
                with self.assertRaises(InvalidQuestionResponse):
                    self.request(result)
                self.assertEqual(len(self.requests), 1)

    def test_valid_answer_clarification_and_probe_preserve_their_decisions(self):
        answer = self.answer()
        answer['assessment']['reason'] = 'x' * 600
        for result in (answer,
                       {'action': 'clarify', 'clarification': 'Explain which assumption you mean.',
                        'probe': None},
                       {'action': 'probe', 'clarification': None,
                        'probe': {'request': 'Which assumption supports the comparison?', 'references': []}}):
            with self.subTest(action=result['action']):
                self.assertEqual(self.request(result).action, result['action'])
                self.assertEqual(len(self.requests), 1)

    def test_invalid_or_mixed_selections_are_rejected_without_guessing_a_move(self):
        base = {name: value for name, value in self.answer().items()
                if name not in {'panelist', 'topic_id', 'is_follow_up'}}
        for changes in ({'next_move': 'invented-choice'}, {'next_move': True},
                        {'panelist': 'Critical Judge', 'topic_id': None, 'is_follow_up': True},
                        {'panelist': None, 'topic_id': 'topic-4', 'is_follow_up': False},
                        {'next_move': 'move-5', 'panelist': 'Critical Judge'},
                        {'panelist': 'Ethics Reviewer', 'topic_id': 'topic-4', 'is_follow_up': False}):
            with self.subTest(changes=changes), self.assertRaises(InvalidQuestionResponse):
                self.request({**base, **changes})
            self.assertEqual(len(self.requests), 1)

    def test_null_selection_cannot_bypass_the_existing_completion_guard(self):
        from backend.question_generator import QuestionGenerationError
        from tests.reviewer_benchmark import failure_code
        result = {name: value for name, value in self.answer().items()
                  if name not in {'panelist', 'topic_id', 'is_follow_up'}}
        with self.assertRaises(QuestionGenerationError) as raised:
            self.request({**result, 'next_move': None})
        self.assertEqual(failure_code(raised.exception), 'plan_premature_completion')
        self.assertEqual(len(self.requests), 1)

    def test_canonical_clarification_and_probe_stay_on_the_same_question(self):
        from backend.question_generator import QuestionGenerationError
        from tests.reviewer_benchmark import failure_code
        for result in (
                {'action': 'clarify', 'clarification': 'Explain the assumption you mean.', 'probe': None},
                {'action': 'probe', 'clarification': None,
                 'probe': {'request': 'Which assumption supports the comparison?', 'references': []}}):
            with self.subTest(action=result['action']):
                self.assertEqual(self.request({**result, 'assessment': None, 'next_move': None}).action,
                                 result['action'])
                with self.assertRaises(QuestionGenerationError) as raised:
                    self.request({**result, 'assessment': None, 'next_move': 'move-5'})
                self.assertEqual(failure_code(raised.exception), 'response_schema_invalid')

"""Advertised evidence response contracts through funded HTTP; provider mocked."""
import json
from unittest.mock import patch

import httpx
from jsonschema import validate

from backend.openrouter_questions import RunQuestionClient, establish_run_allowance
from backend.question_generator import RESEARCH_PANELISTS
from tests.test_openrouter_questions import IsolatedAllowanceTests, stream_response

HTTPClient = httpx.Client


class EvidenceContractTests(IsolatedAllowanceTests):
    def test_incomplete_or_mixed_normal_result_remains_rejected_with_safe_codes(self):
        from backend.evidence_response import lookup_format, read_result, EvidenceResponseError
        from backend.question_generator import QuestionDraft
        for result, lookup, code in (
            (None, None, 'evidence_missing_result'),
            ({'lead_in':'','question':'How will you compare?','source_file':1,'evidence_line':4},
             {'query':'eligibility','source_files':[1]}, 'evidence_mixed_result'),
        ):
            with self.subTest(code=code), self.assertRaises(EvidenceResponseError) as caught:
                read_result(lookup_format(QuestionDraft).model_validate({'result':result,'lookup':lookup}),QuestionDraft)
            self.assertEqual(caught.exception.reason_code,code)

    def test_nested_lookup_still_expands_once_and_returns_a_grounded_opening(self):
        from backend.defense_session import ResearchDefenseSession
        from tests.reviewer_cases import CASES
        case=CASES[2]
        self.files=case.files
        self.session=ResearchDefenseSession.create(case.plan(),4,'research','proposal')
        outputs=[{'result':None,'lookup':{'query':'Eligibility protocol','source_files':[1]}},
                 {'lookup':None,'result':{'action':'ask','panelist':RESEARCH_PANELISTS[0],
                  'topic_id':'topic-1','is_follow_up':False,'assessment':None}},
                 {'lookup':None,'result':{'lead_in':'','question':'How will you justify the theoretical argument?',
                  'source_file':1,'evidence_line':4}}]
        requests=[]
        def respond(request):
            body=json.loads(request.content);wire=outputs[len(requests)]
            validate(wire,body['response_format']['json_schema']['schema'])
            requests.append(body)
            return stream_response(wire)
        establish_run_allowance('contract:lookup','owner',self.files,4)
        with patch('httpx.Client',side_effect=lambda **kwargs:HTTPClient(transport=httpx.MockTransport(respond))):
            move=RunQuestionClient('contract:lookup','owner',self.session,self.files).research_move(self.files,
                history=[],context=self.session.context(),defense_type='research',research_stage='proposal')
        self.assertEqual(len(requests),3)
        self.assertIn('BROADER LOOKUP',requests[1]['messages'][-1]['content'])
        self.assertEqual(move.question.evidence_line,4)

    def test_schema_compliant_opening_cannot_null_its_required_question_fields(self):
        calls = []
        def respond(request):
            body = json.loads(request.content)
            schema = body['response_format']['json_schema']['schema']
            name = body['response_format']['json_schema']['name']
            if name == 'PlanDraft':
                normal = {'action': 'ask', 'panelist': RESEARCH_PANELISTS[0], 'topic_id': 'topic-1',
                          'is_follow_up': False, 'assessment': None}
            else:
                normal = {'lead_in': '', 'question': 'How will you justify the stated study design?',
                          'source_file': 1, 'evidence_line': 4}
            if 'result' in schema['properties']:
                wire = {'result': normal, 'lookup': None}
            else:
                wire = {'lookup': None, **normal}
                # A schema-following provider may use null when explicitly
                # advertised, even though a normal opening needs an empty string.
                if 'lead_in' in wire:
                    wire['lead_in'] = None
            validate(wire, schema)
            calls.append(name)
            return stream_response(wire)
        establish_run_allowance('contract:opening', 'owner', self.files, 4)
        with patch('httpx.Client', side_effect=lambda **kwargs: HTTPClient(transport=httpx.MockTransport(respond))):
            move = RunQuestionClient('contract:opening', 'owner', self.session, self.files).research_move(self.files,
                history=[], context=self.session.context(), defense_type='research', research_stage='proposal')
        self.assertEqual(move.question.lead_in, '')
        self.assertEqual(move.question.evidence_line, 4)
        self.assertEqual(calls, ['PlanDraft', 'QuestionDraft'])

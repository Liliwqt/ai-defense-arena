"""Funded defense-question contract; OpenRouter, AI and payments are offline."""

import json
import os
from dataclasses import asdict
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import httpx

from backend import game_server
from backend.defense_session import PlannedMove, ResearchDefenseSession
from backend.openrouter_questions import (
    COMBINED_PLANNING, FRAMING_BYTES, RunQuestionClient, RunQuestionPolicy,
    SEPARATE_PLANNING, establish_run_allowance,
)
from backend.provider_allowance import ProviderAllowance
from backend.project_files import ProjectFile
from backend.question_generator import (
    CoachingReport, GroundedQuestion, QuestionGenerationError, RESEARCH_PANELISTS, ResearchMove,
    TopicAssessmentDraft,
)
from backend.rooms import coaching as coaching_workflow
from backend.rooms import planning as planning_workflow
from backend.rooms.commands import CatchUpDeadline
from backend.timed_turn import VOTE_MS
from tests import test_research_coverage as coverage
from tests import test_research_plan as maps
from tests.research_coaching_fixtures import scope_options, with_cards

HTTPClient = httpx.Client
METHODOLOGY, ETHICS, IMPACT, JUDGE = RESEARCH_PANELISTS
PAPER = maps.PAPER


def stream_response(output, *, usage=None):
    events = [
        {"choices": [{"index": 0, "delta": {"content": json.dumps(output)}, "finish_reason": None}]},
        {"choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]},
        {"choices": [], "usage": usage if usage is not None else {
            "prompt_tokens": 500, "completion_tokens": 300, "cost": 0.0005}},
    ]
    return httpx.Response(200, text=''.join('data: ' + json.dumps(event) + '\n\n' for event in events) + 'data: [DONE]\n\n')


def planner_move(panelist, topic_id, *, action="ask", follow_up=False, assessment=None):
    return {"action": action, "panelist": panelist, "topic_id": topic_id,
            "is_follow_up": follow_up, "assessment": assessment}


def reviewer_question(question, *, source_file=1, evidence_line=4, lead_in=""):
    return {"lead_in": lead_in, "question": question, "source_file": source_file, "evidence_line": evidence_line}


def assessment(topic_id, turn, status="discussed", reason="The defender explained this topic."):
    return {"topic_id": topic_id, "turn": turn, "status": status, "reason": reason}


class IsolatedAllowanceTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        env = patch.dict(os.environ, {
            'DATABASE_URL': '',
            'PAYMONGO_TEST_DB_PATH': str(Path(folder.name) / 'allowances.sqlite3'),
            'OPENROUTER_API_KEY': 'offline-router-key',
        })
        env.start()
        self.addCleanup(env.stop)
        self.files = [ProjectFile('study.md', PAPER, 'research_text')]
        self.session = ResearchDefenseSession.create(maps.fixture_plan(), 4, 'research', 'proposal')


class FundedQuestionPolicyTests(IsolatedAllowanceTests):

    def test_standard_uses_the_versioned_combined_contract_and_legacy_snapshots_stay_separate(self):
        with patch.dict(os.environ, {'OPENROUTER_RUN_USD': '5.00'}):
            policy = RunQuestionPolicy.configured()
        self.assertEqual(policy.planning_contract, COMBINED_PLANNING)
        self.assertEqual(policy.combined_output_tokens, 6144)
        stored = asdict(policy)
        stored.pop('planning_contract')
        self.assertEqual(RunQuestionPolicy(**stored).planning_contract, SEPARATE_PLANNING)
        self.assertGreater(policy.question_bound(self.files, 4),
                           RunQuestionPolicy(**stored).question_bound(self.files, 4))

    def test_ceiling_configuration_is_bounded_and_explicit(self):
        with patch.dict(os.environ, {'OPENROUTER_RUN_USD': '5.00'}):
            policy = RunQuestionPolicy.configured()
        self.assertEqual(policy.ceiling_nano, 5_000_000_000)
        self.assertEqual(policy.planner_model, 'z-ai/glm-5.3-flash')
        self.assertEqual(policy.planner_reasoning, {'effort': 'low'})
        self.assertEqual(policy.reviewer_reasoning[IMPACT], {'max_tokens': 2048})
        self.assertEqual(policy.reviewer_reasoning[JUDGE], {'effort': 'high'})
        for value in ('0', '-1', 'not-money', '100.01', 'NaN'):
            with self.subTest(value=value), patch.dict(os.environ, {'OPENROUTER_RUN_USD': value}):
                with self.assertRaisesRegex(QuestionGenerationError, 'OPENROUTER_RUN_USD'):
                    RunQuestionPolicy.configured()

    def test_unfundable_budget_is_rejected_before_any_policy_exists(self):
        scope, owner = 'run:unfundable', 'owner'
        with patch.dict(os.environ, {'OPENROUTER_RUN_USD': '0.000001'}):
            with self.assertRaisesRegex(QuestionGenerationError, 'OPENROUTER_RUN_USD'):
                establish_run_allowance(scope, owner, self.files, 4)
        self.assertIsNone(ProviderAllowance(scope, owner).policy())

    def test_established_snapshot_survives_later_configuration_changes(self):
        scope, owner = 'run:snapshot', 'owner'
        with patch.dict(os.environ, {'OPENROUTER_RUN_USD': '5.00'}):
            stored = establish_run_allowance(scope, owner, self.files, 4)
        self.assertEqual(stored.coaching_reserve_nano, stored.coaching_bound(self.files, 4))
        self.assertEqual(stored.planner_reasoning, {'effort': 'low'})
        with patch.dict(os.environ, {'OPENROUTER_RUN_USD': '0.50'}):
            self.assertEqual(establish_run_allowance(scope, owner, self.files, 4).ceiling_nano, 5_000_000_000)


class FundedQuestionClientTests(IsolatedAllowanceTests):
    def make(self, handler, *, scope='run:client', owner='owner', files=None, session=None, **kwargs):
        self.calls = []
        files = self.files if files is None else files
        session = self.session if session is None else session

        def client(*args, **inner):
            return HTTPClient(transport=httpx.MockTransport(handler))
        with patch.dict(os.environ, {'OPENROUTER_RUN_USD': '5.00'}):
            establish_run_allowance(scope, owner, files, session.question_budget)
        instance = RunQuestionClient(scope, owner, session, files,
                                     api_key=kwargs.pop('api_key', 'offline-router-key'), **kwargs)
        patcher = patch('httpx.Client', side_effect=client)
        patcher.start()
        self.addCleanup(patcher.stop)
        return instance

    def call(self, client):
        return client.research_move(self.files, history=self.session.answered_history(),
                                    context=self.session.context(), defense_type='research',
                                    research_stage='proposal')

    def test_planner_then_reviewer_use_verified_models_and_settle_reported_costs(self):
        def handler(request):
            self.calls.append(json.loads(request.content))
            output = (planner_move(METHODOLOGY, 'topic-1') if len(self.calls) == 1
                      else reviewer_question('How will the team justify the stated pilot design?'))
            return stream_response(output)
        client = self.make(handler)
        move = self.call(client)
        self.assertEqual([call['model'] for call in self.calls],
                         ['z-ai/glm-5.3-flash', 'deepseek/deepseek-v4.1-flash-1017'])
        self.assertEqual([call['reasoning'] for call in self.calls], [{'effort': 'low'}, {'effort': 'high'}])
        self.assertEqual([call['max_tokens'] for call in self.calls], [4096, 8192])
        self.assertEqual([call['response_format']['json_schema']['name'] for call in self.calls],
                         ['PlanDraft', 'QuestionDraft'])
        guard = self.calls[0]['provider']
        self.assertFalse(guard['allow_fallbacks'])
        self.assertTrue(guard['require_parameters'])
        self.assertEqual(guard['data_collection'], 'deny')
        self.assertEqual(guard['max_price'], {'prompt': .30, 'completion': 1.20, 'request': 0})
        self.assertIn('Do not write the question', self.calls[0]['messages'][0]['content'])
        self.assertIn('topic-1', self.calls[1]['messages'][1]['content'])
        self.assertEqual(move.panelist, METHODOLOGY)
        self.assertEqual(move.topic_id, 'topic-1')
        self.assertEqual(move.question.question, 'How will the team justify the stated pilot design?')
        self.assertEqual((move.question.filename, move.question.evidence_line), ('study.md', 4))
        self.assertEqual(ProviderAllowance('run:client', 'owner').snapshot()['used'], 1_000_000)


    def test_ineligible_plan_is_rejected_before_any_reviewer_request(self):
        def handler(request):
            self.calls.append(json.loads(request.content))
            return stream_response(planner_move(ETHICS, 'topic-1'))
        client = self.make(handler)
        with self.assertRaisesRegex(QuestionGenerationError, 'invalid research topic or reviewer'):
            self.call(client)
        self.assertEqual(len(self.calls), 1)

    def test_invalid_assessment_is_rejected_before_any_reviewer_request(self):
        self.session.apply_move(ResearchMove(METHODOLOGY, GroundedQuestion(
            'Opening question?', 'study.md', 4, PAPER.splitlines()[3]), 'topic-1', False, None))
        self.session.turns[-1].answer = 'We will recruit volunteers for the pilot.'

        def handler(request):
            self.calls.append(json.loads(request.content))
            output = planner_move(ETHICS, 'topic-2', assessment=assessment('topic-1', 5))
            return stream_response(output)
        client = self.make(handler)
        with self.assertRaisesRegex(QuestionGenerationError, 'invalid coverage assessment'):
            self.call(client)
        self.assertEqual(len(self.calls), 1)

    def test_valid_completion_spends_one_request_and_applies_at_budget(self):
        for index, role in enumerate(RESEARCH_PANELISTS):
            prior = None if index == 0 else TopicAssessmentDraft(**assessment(f'topic-{index}', index - 1))
            self.session.apply_move(ResearchMove(role, GroundedQuestion(
                f'Question {index + 1}?', 'study.md', index * 2 + 4, PAPER.splitlines()[index * 2 + 3]),
                f'topic-{index + 1}', False, prior))
            self.session.turns[-1].answer = f'Answer {index + 1}'

        def handler(request):
            self.calls.append(json.loads(request.content))
            return stream_response(planner_move(None, None, action='complete',
                                                assessment=assessment('topic-4', 3)))
        client = self.make(handler)
        move = self.call(client)
        self.assertEqual(len(self.calls), 1)
        self.assertIsNone(move.panelist)
        self.assertIsNone(move.question)
        self.session.apply_move(move)
        self.assertTrue(self.session.completed)
        self.assertEqual(self.session.completion_reason, 'budget exhausted')

    def test_cancellation_between_the_stages_stops_before_the_reviewer(self):
        stop = {'value': False}

        def handler(request):
            self.calls.append(json.loads(request.content))
            head, tail = stream_response(planner_move(METHODOLOGY, 'topic-1')).text.rsplit('data: [DONE]', 1)

            class Bytes(httpx.SyncByteStream):
                def __iter__(self):
                    yield head.encode()
                    stop['value'] = True
                    yield ('data: [DONE]' + tail).encode()
            return httpx.Response(200, stream=Bytes())
        client = self.make(handler, stopped=lambda: stop['value'])
        with self.assertRaisesRegex(QuestionGenerationError, 'cancelled'):
            self.call(client)
        self.assertEqual(len(self.calls), 1)

    def test_focused_writer_expands_once_then_cites_beyond_the_view(self):
        from backend.room_operations import bind_operation, take_supplied_usage

        lines = [f"Section line {index}." for index in range(1, 41)]
        lines[3] = "Recruit volunteers for a two-week pilot."
        lines[5] = "Obtain consent and anonymize responses."
        lines[7] = "Compare students' wait times."
        lines[9] = "A single campus may not represent other campuses."
        lines[29] = "Retention remained stable twelve weeks after rollout."
        text = "\n".join(lines) + "\n"
        files = [ProjectFile('study.md', text, 'research_text')]
        plan = maps.generate_research_plan(files, 'offline-key', research_stage='proposal',
                                           client=maps.FakeClient(maps.draft()))
        session = ResearchDefenseSession.create(plan, 4, 'research', 'proposal')
        session.apply_move(ResearchMove(METHODOLOGY, GroundedQuestion(
            'Opening question?', 'study.md', 4, lines[3]), 'topic-1', False, None))
        session.turns[-1].answer = 'We checked retention after twelve weeks.'

        def handler(request):
            self.calls.append(json.loads(request.content))
            if len(self.calls) == 1:
                output = planner_move(ETHICS, 'topic-2',
                                      assessment=assessment('topic-1', 0))
            elif len(self.calls) == 2:
                output = {'lookup': {'query': 'retention twelve weeks after rollout', 'source_files': [1]}}
            else:
                output = reviewer_question('What does retention show?', source_file=1, evidence_line=30)
            return stream_response(output)
        client = self.make(handler, files=files, session=session)
        bind_operation('question:focus')
        try:
            move = client.research_move(files, history=session.answered_history(), context=session.context(),
                                        defense_type='research', research_stage='proposal')
        finally:
            usage = take_supplied_usage('question:focus')
        self.assertEqual(len(self.calls), 3)
        prompts = [call['messages'][1]['content'] for call in self.calls]
        self.assertIn('Accepted evidence', prompts[0])
        self.assertIn('Accepted evidence', prompts[1])
        self.assertNotIn('Retention remained stable', prompts[0])
        self.assertNotIn('Retention remained stable', prompts[1])
        self.assertIn('Retention remained stable', prompts[2])
        self.assertEqual(move.question.evidence_line, 30)
        self.assertEqual(usage['lookup_requests'], 1)
        self.assertGreater(usage['lookup_bytes'], 0)

    def test_unknown_usage_retains_both_full_reservations(self):
        def handler(request):
            self.calls.append(json.loads(request.content))
            output = (planner_move(METHODOLOGY, 'topic-1') if len(self.calls) == 1
                      else reviewer_question('How will the team justify the stated pilot design?'))
            return stream_response(output, usage={})
        client = self.make(handler)
        self.call(client)
        policy = RunQuestionPolicy(**ProviderAllowance('run:client', 'owner').policy())
        bounds = [policy.stage_bound(len(json.dumps(
            {'messages': call['messages'], 'schema': call['response_format']}, ensure_ascii=False).encode()) + FRAMING_BYTES,
            call['max_tokens']) for call in self.calls]
        snapshot = ProviderAllowance('run:client', 'owner').snapshot()
        self.assertEqual(snapshot['used'], sum(bounds))
        self.assertEqual(snapshot['remaining'], snapshot['ceiling'] - sum(bounds))

    def test_oversized_context_is_rejected_before_dispatch_or_reservation(self):
        def handler(request):
            self.calls.append(json.loads(request.content))
            return stream_response(planner_move(METHODOLOGY, 'topic-1'))
        client = self.make(handler)
        stored = ProviderAllowance('run:client', 'owner').policy()
        client.policy = RunQuestionPolicy(**{**stored, 'evidence_policy': 'full-v1'})
        huge = 'a' * 1_200_000
        with patch('backend.openrouter_questions.build_project_source',
                   return_value=(huge, {1: (self.files[0], huge)}, set())):
            with self.assertRaisesRegex(QuestionGenerationError, 'exceeds the bounded OpenRouter question context'):
                self.call(client)
        self.assertEqual(self.calls, [])
        self.assertEqual(ProviderAllowance('run:client', 'owner').snapshot()['used'], 0)

    def test_missing_or_dirty_key_is_rejected_without_dispatch(self):
        for api_key in ('', 'bad key'):
            with self.subTest(api_key=api_key):

                def handler(request):
                    self.calls.append(json.loads(request.content))
                    return stream_response(planner_move(METHODOLOGY, 'topic-1'))
                client = self.make(handler, api_key=api_key)
                with self.assertRaisesRegex(QuestionGenerationError, 'OPENROUTER_API_KEY'):
                    self.call(client)
                self.assertEqual(self.calls, [])

    def test_unestablished_run_scope_is_rejected_without_dispatch_or_snapshot(self):
        def handler(request):
            self.calls.append(json.loads(request.content))
            return stream_response(planner_move(METHODOLOGY, 'topic-1'))
        self.calls = []
        client = RunQuestionClient('run:absent', 'owner', self.session, self.files, api_key='offline-router-key')

        def http_client(*args, **kwargs):
            return HTTPClient(transport=httpx.MockTransport(handler))
        with patch('httpx.Client', side_effect=http_client):
            with self.assertRaisesRegex(QuestionGenerationError, 'allowance is unavailable'):
                self.call(client)
        self.assertEqual(self.calls, [])
        self.assertIsNone(ProviderAllowance('run:absent', 'owner').policy())

    def research_files(self):
        return [ProjectFile('study.md', PAPER, 'research_text'),
                ProjectFile('queue.py', 'def save_reservation(student_id):\n    return student_id\n', 'source')]

    def prior_turns(self, session, upto):
        for index in range(upto):
            prior = None if index == 0 else TopicAssessmentDraft(**assessment(f'topic-{index}', index - 1))
            session.apply_move(ResearchMove(RESEARCH_PANELISTS[index], GroundedQuestion(
                f'Question {index + 1}?', 'study.md', index * 2 + 4, PAPER.splitlines()[index * 2 + 3]),
                f'topic-{index + 1}', False, prior))
            session.turns[-1].answer = f'Answer {index + 1}'

    def test_mixed_mode_accepts_code_citations_from_every_reviewer(self):
        for index, role in enumerate(RESEARCH_PANELISTS):
            with self.subTest(role=role):
                files = self.research_files()
                session = ResearchDefenseSession.create(maps.fixture_plan(), 4, 'mixed', 'proposal')
                self.prior_turns(session, index)

                def handler(request):
                    self.calls.append(json.loads(request.content))
                    output = (planner_move(role, f'topic-{index + 1}',
                                           assessment=None if index == 0 else assessment(f'topic-{index}', index - 1))
                              if len(self.calls) == 1
                              else reviewer_question('What does save_reservation return?', source_file=2,
                                                     evidence_line=1,
                                                     lead_in='' if index == 0 else 'You described the pilot decision.'))
                    return stream_response(output)
                client = self.make(handler, scope=f'run:mixed-{index}', files=files, session=session)
                move = client.research_move(files, history=session.answered_history(), context=session.context(),
                                            defense_type='mixed', research_stage='proposal')
                self.assertEqual(move.panelist, role)
                self.assertEqual((move.question.filename, move.question.evidence_line), ('queue.py', 1))
                self.assertEqual(len(self.calls), 2)

    def test_research_mode_still_rejects_code_citations(self):
        files = self.research_files()

        def handler(request):
            self.calls.append(json.loads(request.content))
            output = (planner_move(METHODOLOGY, 'topic-1') if len(self.calls) == 1
                      else reviewer_question('What does save_reservation return?', source_file=2, evidence_line=1))
            return stream_response(output)
        client = self.make(handler, scope='run:research-citation', files=files)
        with self.assertRaisesRegex(QuestionGenerationError, 'invalid project file'):
            client.research_move(files, history=self.session.answered_history(), context=self.session.context(),
                                 defense_type='research', research_stage='proposal')
        self.assertEqual(len(self.calls), 2)

    def test_reviewer_prompt_carries_conversation_scenario_and_mixed_citation_policy(self):
        client = self.make(lambda request: stream_response(planner_move(METHODOLOGY, 'topic-1')))
        planned = PlannedMove(METHODOLOGY, 'topic-1', False, None)
        research = client._reviewer_messages(planned, '', [], {}, 'research', 'proposal')[0]['content']
        mixed = client._reviewer_messages(planned, '', [], {}, 'mixed', 'proposal')[0]['content']
        self.assertIn('If it resolves the requested detail', research)
        self.assertIn('Never use scenarios in consecutive questions', research)
        self.assertIn('not described here is not the same as not planned', research)
        self.assertNotIn('any reviewer may cite paper or implementation', research)
        self.assertIn('In mixed mode any reviewer may cite paper or implementation.', mixed)

    def test_processing_deadline_stops_writer_before_dispatch(self):
        import asyncio
        from backend.processing_policy import ProcessingPolicy
        from backend.rooms.coordinator import RoomCoordinator, RoomWorkflows
        from backend.rooms.model import Player, Room
        from backend.rooms.questions import QuestionWork, run_question

        clock = [1000]
        schemas = []

        def provider(request):
            body = json.loads(request.content)
            schemas.append(body['response_format']['json_schema']['name'])
            output = (planner_move(METHODOLOGY, 'topic-1') if len(schemas) == 1
                      else reviewer_question('How will the team justify the pilot?'))
            if len(schemas) == 1:
                clock[0] = 46_000
            return stream_response(output)

        def client(*args, **kwargs):
            return HTTPClient(transport=httpx.MockTransport(provider))

        room = Room('DEADLINE', self.files, {'host': Player('host', 'Host', 0, True)},
                    defense_type='research', research_stage='proposal', defense=self.session,
                    owner_account_id='owner', run_id='deadline', phase='generating',
                    generation_id=1, processing_policy=ProcessingPolicy.standard())
        room.begin_interaction_window(1000)
        establish_run_allowance('run:deadline', 'owner', self.files, 4)

        async def drive():
            async def deliver(*args):
                pass
            owner = RoomCoordinator(room, RoomWorkflows(deliver=deliver, now=lambda: clock[0]))
            try:
                with patch('backend.rooms.questions.recent_openings', return_value=[]), \
                     patch('backend.rooms.questions.charge_run'), \
                     patch('backend.rooms.questions.release_run'), \
                     patch('httpx.Client', side_effect=client):
                    await run_question(owner, QuestionWork(1, True, 'deadline'))
            finally:
                await owner.shutdown()

        asyncio.run(drive())
        self.assertEqual(schemas, ['PlanDraft'])
        self.assertEqual(room.phase, 'retry')
        self.assertIn('limit', room.error)
        self.assertFalse(room.defense.turns)
        self.assertIsNone(room.operation)


class FundedQuestionProtocolTests(maps.ResearchPlanRoomTests):
    def funded(self, *outputs, usage=None):
        calls = []

        def provider(request):
            calls.append(json.loads(request.content))
            output = outputs[min(len(calls), len(outputs)) - 1]
            return output if isinstance(output, httpx.Response) else stream_response(output, usage=usage)

        def client(*args, **kwargs):
            return HTTPClient(transport=httpx.MockTransport(provider))
        patcher = patch('httpx.Client', side_effect=client)
        patcher.start()
        self.addCleanup(patcher.stop)
        return calls

    def start(self, socket, budget=4):
        self.hello(socket, self.host['player_token'])
        socket.send_json({'type': 'prepare_research_plan'})
        self.until(socket, research_planning_status='ready')
        socket.send_json({'type': 'approve_research_plan', 'plan_id': self.plan.id,
                          'question_budget': budget, 'confirm_profile': True})
        self.until(socket, research_plan_approved=True)
        socket.send_json({'type': 'start', 'plan_id': self.plan.id, 'question_budget': budget})

    def test_funded_opening_reaches_the_room_and_settles_both_stages(self):
        self.host = self.create()
        with patch('backend.rooms.planning.generate_research_plan', return_value=self.plan), \
             self.client.websocket_connect(f"/ws/{self.host['room_code']}") as socket:
            calls = self.funded(planner_move(METHODOLOGY, 'topic-1'),
                                reviewer_question('How will the team justify the stated pilot design?'))
            self.start(socket)
            state = self.until(socket, phase='voting')
        self.assertEqual([call['model'] for call in calls],
                         ['z-ai/glm-5.3-flash', 'deepseek/deepseek-v4.1-flash-1017'])
        self.assertEqual([call['max_tokens'] for call in calls], [4096, 8192])
        self.assertEqual(state['turns'][0]['question'], 'How will the team justify the stated pilot design?')
        self.assertEqual(state['turns'][0]['evidence_line'], 4)
        room = __import__('backend.game_server', fromlist=['rooms']).rooms[self.host['room_code']]
        account = self._offline_credentials[2]
        snapshot = ProviderAllowance(f'run:{room.run_id}', account['id']).snapshot()
        self.assertEqual(snapshot['used'], 1_000_000)

    def test_failed_opening_retries_with_the_established_snapshot(self):
        self.host = self.create()
        with patch('backend.rooms.planning.generate_research_plan', return_value=self.plan), \
             self.client.websocket_connect(f"/ws/{self.host['room_code']}") as socket:
            calls = self.funded(httpx.Response(503, text='{}'),
                                httpx.Response(503, text='{}'),
                                planner_move(METHODOLOGY, 'topic-1'),
                                reviewer_question('How will the team justify the stated pilot design?'))
            self.start(socket)
            self.until(socket, phase='retry')
            room = game_server.rooms[self.host['room_code']]
            with patch.dict(os.environ, {'OPENROUTER_RUN_USD': '0.50'}):
                socket.send_json({'type': 'retry'})
                state = self.until(socket, phase='voting')
        self.assertEqual([call['model'] for call in calls],
                         ['z-ai/glm-5.3-flash', 'z-ai/glm-5.3-flash',
                          'z-ai/glm-5.3-flash', 'deepseek/deepseek-v4.1-flash-1017'])
        self.assertEqual(state['turns'][0]['question'], 'How will the team justify the stated pilot design?')
        account = self._offline_credentials[2]
        snapshot = ProviderAllowance(f'run:{room.run_id}', account['id']).snapshot()
        self.assertEqual(snapshot['ceiling'], 5_000_000_000)

    def test_unfundable_ceiling_rejects_start_before_any_charge_or_dispatch(self):
        host = self.create()
        with patch('backend.rooms.planning.generate_research_plan', return_value=self.plan), \
             self.client.websocket_connect(f"/ws/{host['room_code']}") as socket:
            self.hello(socket, host['player_token'])
            socket.send_json({'type': 'prepare_research_plan'})
            self.until(socket, research_planning_status='ready')
            socket.send_json({'type': 'approve_research_plan', 'plan_id': self.plan.id,
                              'question_budget': 4, 'confirm_profile': True})
            self.until(socket, research_plan_approved=True)
            with patch.dict(os.environ, {'OPENROUTER_RUN_USD': '0.000001'}):
                socket.send_json({'type': 'start', 'plan_id': self.plan.id, 'question_budget': 4})
                for _ in range(5):
                    event = socket.receive_json()
                    if event['type'] == 'error':
                        break
                else:
                    self.fail('No unfundable rejection')
            self.assertIn('OPENROUTER_RUN_USD', event['message'])
        room = game_server.rooms[host['room_code']]
        self.assertIsNone(room.run_id)
        self.assertIsNone(room.defense)
        self.assertEqual(room.phase, 'lobby')


class FundedQuestionRoundsTests(coverage.CoverageProtocolTests):
    # The funded rounds below replace the inherited twelve-turn coverage runs.
    test_twelve_question_research_and_mixed_with_vote_clarification_timeout_retry_reconnect_coaching = None
    test_twelve_question_pdf_research_and_mixed_preserve_private_originals_and_citations = None

    def setUp(self):
        super().setUp()
        env = patch.dict(os.environ, {'OPENROUTER_RUN_USD': '5.00'})
        env.start()
        self.addCleanup(env.stop)
        self.plan = maps.fixture_plan()

    def funded(self, *outputs, usage=None):
        calls = []

        def provider(request):
            calls.append(json.loads(request.content))
            output = outputs[min(len(calls), len(outputs)) - 1]
            return output if isinstance(output, httpx.Response) else stream_response(output, usage=usage)

        def client(*args, **kwargs):
            return HTTPClient(transport=httpx.MockTransport(provider))
        patcher = patch('httpx.Client', side_effect=client)
        patcher.start()
        self.addCleanup(patcher.stop)
        return calls

    def create_room(self):
        files = [('research_files', ('study.md', PAPER.encode(), 'text/markdown'))]
        response = self.client.post('/api/rooms', data={'host_name': 'Host', 'host_passcode': 'offline-passcode',
                                                        'defense_type': 'research', 'research_stage': 'proposal'},
                                    files=files)
        self.assertEqual(response.status_code, 201, response.text)
        host = response.json()
        guest = self.client.post(f"/api/rooms/{host['room_code']}/join", json={'name': 'Sam'}).json()
        return host, guest

    def test_two_client_funded_defense_settles_every_stage_and_completes_at_budget(self):
        questions = [f'Funded question {index + 1}?' for index in range(4)]
        outputs = [planner_move(METHODOLOGY, 'topic-1'),
                   reviewer_question(questions[0], evidence_line=4),
                   {'action': 'answer', 'clarification': None, 'probe': None,
                    'assessment': assessment('topic-1', 0),
                    'panelist': ETHICS, 'topic_id': 'topic-2', 'is_follow_up': False},
                   reviewer_question(questions[1], evidence_line=6,
                                     lead_in='You described the pilot decision.'),
                   {'action': 'answer', 'clarification': None, 'probe': None,
                    'assessment': assessment('topic-2', 1),
                    'panelist': IMPACT, 'topic_id': 'topic-3', 'is_follow_up': False},
                   reviewer_question(questions[2], evidence_line=8,
                                     lead_in='You described the pilot decision.'),
                   {'action': 'answer', 'clarification': None, 'probe': None,
                    'assessment': assessment('topic-3', 2),
                    'panelist': JUDGE, 'topic_id': 'topic-4', 'is_follow_up': False},
                   reviewer_question(questions[3], evidence_line=10,
                                     lead_in='You described the pilot decision.'),
                   {'action': 'answer', 'clarification': None, 'probe': None,
                    'assessment': assessment('topic-4', 3),
                    'panelist': None, 'topic_id': None, 'is_follow_up': False}]

        def coach(files, history, key, model, **kwargs):
            draft = CoachingReport(summary='The approved budget ended.', strengths=[], improvements=[],
                                   next_step='Review the remaining topics.', closing='You explained the pilot decisions.')
            return with_cards(draft, history, **scope_options(kwargs))
        host, guest = self.create_room()
        code = host['room_code']
        with patch.object(planning_workflow, 'generate_research_plan', return_value=self.plan), \
             patch.object(coaching_workflow, 'generate_coaching_report', side_effect=coach):
            with self.client.websocket_connect(f'/ws/{code}') as h, self.client.websocket_connect(f'/ws/{code}') as g:
                calls = self.funded(*outputs)
                for socket, token in ((h, host['player_token']), (g, guest['player_token'])):
                    socket.send_json({'type': 'hello', 'token': token})
                    self.until(socket, 'lobby')
                h.send_json({'type': 'prepare_research_plan'})
                for socket in (h, g):
                    self.until(socket, research_planning_status='ready')
                h.send_json({'type': 'approve_research_plan', 'plan_id': self.plan.id,
                             'question_budget': 4, 'confirm_profile': True})
                for socket in (h, g):
                    self.until(socket, research_plan_approved=True)
                h.send_json({'type': 'start', 'plan_id': self.plan.id, 'question_budget': 4})
                for index in range(4):
                    for socket in (h, g):
                        state = self.until(socket, 'voting', index + 1)
                        self.assertEqual(state['turns'][-1]['question'], questions[index])
                        self.assertEqual(state['turns'][-1]['panelist'], RESEARCH_PANELISTS[index])
                        if index:
                            self.assertEqual(state['turns'][-2]['answered_by'],
                                             'Host' if (index - 1) % 2 == 0 else 'Sam')
                            self.assertEqual(state['turns'][-2]['answer'], f'Answer {index}.')
                    h.send_json({'type': 'cast_vote', 'seat': index % 2})
                    for socket in (h, g):
                        self.until(socket, 'voting', index + 1)
                    self.now += VOTE_MS + 1
                    self.client.portal.call(game_server._coordinator(game_server.rooms[code]).execute,
                                            CatchUpDeadline())
                    for socket in (h, g):
                        state = self.until(socket, 'question', index + 1)
                        self.assertEqual(state['selected_seat'], index % 2)
                    speaker = h if index % 2 == 0 else g
                    speaker.send_json({'type': 'submit_answer', 'turn': index, 'answer': f'Answer {index + 1}.'})
                for socket in (h, g):
                    final = self.until(socket, 'complete', 4, feedback_status='ready')
                    self.assertEqual(final['completion_reason'], 'budget exhausted')
                    self.assertEqual(final['feedback']['summary'], 'The approved budget ended.')
        self.assertEqual([call['model'] for call in calls],
                         ['z-ai/glm-5.3-flash', 'deepseek/deepseek-v4.1-flash-1017',
                          'deepseek/deepseek-v4.1-flash-1017', 'anthropic/claude-haiku-5.5',
                          'anthropic/claude-haiku-5.5', 'qwen/qwen3.8-flash',
                          'qwen/qwen3.8-flash', 'z-ai/glm-5.3-flash',
                          'z-ai/glm-5.3-flash'])
        self.assertEqual([call['response_format']['json_schema']['name'] for call in calls],
                         ['PlanDraft', 'QuestionDraft',
                          'CombinedSubmissionDraft', 'QuestionDraft',
                          'CombinedSubmissionDraft', 'QuestionDraft',
                          'CombinedSubmissionDraft', 'QuestionDraft',
                          'CombinedSubmissionDraft'])
        self.assertEqual([call['reasoning'] for call in calls],
                         [{'effort': 'low'}, {'effort': 'high'}, {'effort': 'low'},
                          {'effort': 'medium'}, {'effort': 'low'}, {'max_tokens': 2048},
                          {'max_tokens': 1024}, {'effort': 'high'}, {'effort': 'low'}])
        account = self._offline_credentials[2]
        room = game_server.rooms[code]
        self.assertEqual(room.planning_contract, COMBINED_PLANNING)
        snapshot = ProviderAllowance(f'run:{room.run_id}', account['id']).snapshot()
        self.assertEqual(snapshot['used'], 4_500_000)

    def create_mixed_room(self):
        files = [('research_files', ('study.md', PAPER.encode(), 'text/markdown')),
                 ('files', ('queue.py', b'queue = []\n', 'text/x-python'))]
        response = self.client.post('/api/rooms', data={'host_name': 'Host', 'host_passcode': 'offline-passcode',
                                                        'defense_type': 'mixed', 'research_stage': 'proposal'},
                                    files=files)
        self.assertEqual(response.status_code, 201, response.text)
        host = response.json()
        guest = self.client.post(f"/api/rooms/{host['room_code']}/join", json={'name': 'Sam'}).json()
        return host, guest

    def test_four_question_funded_mixed_run_uses_combined_planning_and_cites_code(self):
        questions = [f'Mixed combined question {index + 1}?' for index in range(4)]
        outputs = [planner_move(METHODOLOGY, 'topic-1'),
                   reviewer_question(questions[0], source_file=1, evidence_line=1),
                   {'action': 'answer', 'clarification': None, 'probe': None,
                    'assessment': assessment('topic-1', 0),
                    'panelist': ETHICS, 'topic_id': 'topic-2', 'is_follow_up': False},
                   reviewer_question(questions[1], source_file=1, evidence_line=1,
                                     lead_in='You described the pilot decision.'),
                   {'action': 'answer', 'clarification': None, 'probe': None,
                    'assessment': assessment('topic-2', 1),
                    'panelist': IMPACT, 'topic_id': 'topic-3', 'is_follow_up': False},
                   reviewer_question(questions[2], source_file=1, evidence_line=1,
                                     lead_in='You described the pilot decision.'),
                   {'action': 'answer', 'clarification': None, 'probe': None,
                    'assessment': assessment('topic-3', 2),
                    'panelist': JUDGE, 'topic_id': 'topic-4', 'is_follow_up': False},
                   reviewer_question(questions[3], source_file=1, evidence_line=1,
                                     lead_in='You described the pilot decision.'),
                   {'action': 'answer', 'clarification': None, 'probe': None,
                    'assessment': assessment('topic-4', 3),
                    'panelist': None, 'topic_id': None, 'is_follow_up': False}]

        def coach(files, history, key, model, **kwargs):
            draft = CoachingReport(summary='The approved budget ended.', strengths=[], improvements=[],
                                   next_step='Review the remaining topics.', closing='You explained the pilot decisions.')
            return with_cards(draft, history, **scope_options(kwargs))
        host, guest = self.create_mixed_room()
        code = host['room_code']
        with patch.object(planning_workflow, 'generate_research_plan', return_value=self.plan), \
             patch.object(coaching_workflow, 'generate_coaching_report', side_effect=coach):
            with self.client.websocket_connect(f'/ws/{code}') as h, self.client.websocket_connect(f'/ws/{code}') as g:
                calls = self.funded(*outputs)
                for socket, token in ((h, host['player_token']), (g, guest['player_token'])):
                    socket.send_json({'type': 'hello', 'token': token})
                    self.until(socket, 'lobby')
                h.send_json({'type': 'prepare_research_plan'})
                for socket in (h, g):
                    self.until(socket, research_planning_status='ready')
                h.send_json({'type': 'approve_research_plan', 'plan_id': self.plan.id,
                             'question_budget': 4, 'confirm_profile': True})
                for socket in (h, g):
                    self.until(socket, research_plan_approved=True)
                h.send_json({'type': 'start', 'plan_id': self.plan.id, 'question_budget': 4})
                for index in range(4):
                    for socket in (h, g):
                        state = self.until(socket, 'voting', index + 1)
                        self.assertEqual(state['turns'][-1]['question'], questions[index])
                        self.assertEqual(state['turns'][-1]['panelist'], RESEARCH_PANELISTS[index])
                        self.assertEqual(state['turns'][-1]['filename'], 'queue.py')
                        if index:
                            self.assertEqual(state['turns'][-2]['answered_by'],
                                             'Host' if (index - 1) % 2 == 0 else 'Sam')
                            self.assertEqual(state['turns'][-2]['answer'], f'Answer {index}.')
                    h.send_json({'type': 'cast_vote', 'seat': index % 2})
                    for socket in (h, g):
                        self.until(socket, 'voting', index + 1)
                    self.now += VOTE_MS + 1
                    self.client.portal.call(game_server._coordinator(game_server.rooms[code]).execute,
                                            CatchUpDeadline())
                    for socket in (h, g):
                        state = self.until(socket, 'question', index + 1)
                        self.assertEqual(state['selected_seat'], index % 2)
                    speaker = h if index % 2 == 0 else g
                    speaker.send_json({'type': 'submit_answer', 'turn': index, 'answer': f'Answer {index + 1}.'})
                for socket in (h, g):
                    final = self.until(socket, 'complete', 4, feedback_status='ready')
                    self.assertEqual(final['completion_reason'], 'budget exhausted')
        self.assertEqual([call['response_format']['json_schema']['name'] for call in calls],
                         ['PlanDraft', 'QuestionDraft',
                          'CombinedSubmissionDraft', 'QuestionDraft',
                          'CombinedSubmissionDraft', 'QuestionDraft',
                          'CombinedSubmissionDraft', 'QuestionDraft',
                          'CombinedSubmissionDraft'])
        self.assertEqual(len(calls), 9)
        room = game_server.rooms[code]
        self.assertEqual(room.planning_contract, COMBINED_PLANNING)
        account = self._offline_credentials[2]
        snapshot = ProviderAllowance(f'run:{room.run_id}', account['id']).snapshot()
        self.assertEqual(snapshot['used'], 4_500_000)

    def test_invalid_combined_plan_is_rejected_before_the_writer_and_preserves_the_answer(self):
        outputs = [planner_move(METHODOLOGY, 'topic-1'),
                   reviewer_question('How will the team justify the stated pilot design?'),
                   {'action': 'answer', 'clarification': None, 'probe': None,
                    'assessment': assessment('topic-1', 0),
                    'panelist': 'unassigned', 'topic_id': 'topic-2', 'is_follow_up': False},
                   {'action': 'answer', 'clarification': None, 'probe': None,
                    'assessment': assessment('topic-1', 0),
                    'panelist': ETHICS, 'topic_id': 'topic-2', 'is_follow_up': False},
                   reviewer_question('How will the team report claim changes?', evidence_line=6,
                                     lead_in='You described the pilot decision.')]
        host, guest = self.create_room()
        code = host['room_code']
        with patch.object(planning_workflow, 'generate_research_plan', return_value=self.plan):
            with self.client.websocket_connect(f'/ws/{code}') as h, self.client.websocket_connect(f'/ws/{code}') as g:
                calls = self.funded(*outputs)
                for socket, token in ((h, host['player_token']), (g, guest['player_token'])):
                    socket.send_json({'type': 'hello', 'token': token})
                    self.until(socket, 'lobby')
                h.send_json({'type': 'prepare_research_plan'})
                for socket in (h, g):
                    self.until(socket, research_planning_status='ready')
                h.send_json({'type': 'approve_research_plan', 'plan_id': self.plan.id,
                             'question_budget': 4, 'confirm_profile': True})
                for socket in (h, g):
                    self.until(socket, research_plan_approved=True)
                h.send_json({'type': 'start', 'plan_id': self.plan.id, 'question_budget': 4})
                for socket in (h, g):
                    self.until(socket, 'voting', 1)
                h.send_json({'type': 'cast_vote', 'seat': 0})
                for socket in (h, g):
                    self.until(socket, 'voting', 1)
                self.now += VOTE_MS + 1
                self.client.portal.call(game_server._coordinator(game_server.rooms[code]).execute,
                                        CatchUpDeadline())
                for socket in (h, g):
                    self.until(socket, 'question', 1)
                h.send_json({'type': 'submit_answer', 'turn': 0, 'answer': 'Answer 1.'})
                for socket in (h, g):
                    failed = self.until(socket, 'interpretation_retry', 1)
                    self.assertIn('invalid structured response', failed['error'])
                    self.assertEqual(failed['turns'][0]['answer'], None)
                room = game_server.rooms[code]
                self.assertIsNotNone(room.pending_submission)
                self.assertEqual(room.pending_submission.text, 'Answer 1.')
                self.assertEqual(len(calls), 3)
                h.send_json({'type': 'retry_interpretation'})
                for socket in (h, g):
                    state = self.until(socket, 'voting', 2)
                    self.assertEqual(state['turns'][0]['answer'], 'Answer 1.')
                    self.assertEqual(state['turns'][1]['question'],
                                     'How will the team report claim changes?')
        self.assertEqual([call['response_format']['json_schema']['name'] for call in calls],
                         ['PlanDraft', 'QuestionDraft', 'CombinedSubmissionDraft',
                          'CombinedSubmissionDraft', 'QuestionDraft'])
        account = self._offline_credentials[2]
        snapshot = ProviderAllowance(f'run:{room.run_id}', account['id']).snapshot()
        self.assertEqual(snapshot['used'], 2_500_000)

    def test_transient_failure_after_an_answer_recovers_without_a_manual_retry(self):
        self.check_post_answer_recovery(httpx.Response(503, text='{}'), retry=True)

    def test_streamed_server_failure_retries_once_after_an_answer(self):
        self.check_post_answer_recovery(self.provider_error_response(503), retry=True)

    def test_http_rate_limit_preserves_the_answer_for_manual_recovery(self):
        self.check_post_answer_recovery(httpx.Response(429, text='{}'), retry=False)

    def test_streamed_rate_limit_preserves_the_answer_for_manual_recovery(self):
        self.check_post_answer_recovery(self.provider_error_response(429), retry=False)

    @staticmethod
    def provider_error_response(status):
        return httpx.Response(200, text='data: ' + json.dumps({
            'error': {'code': status, 'message': 'private upstream details', 'metadata': {
                'error_type': 'rate_limit_exceeded' if status == 429 else 'server_error'}},
            'choices': [{'index': 0, 'delta': {}, 'finish_reason': 'error'}],
        }) + '\n\n')

    def check_post_answer_recovery(self, failure, *, retry):
        outputs = [planner_move(METHODOLOGY, 'topic-1'),
                   reviewer_question('How will the team justify the stated pilot design?'),
                   {'action': 'answer', 'clarification': None, 'probe': None,
                    'assessment': assessment('topic-1', 0),
                    'panelist': ETHICS, 'topic_id': 'topic-2', 'is_follow_up': False},
                   failure,
                   reviewer_question('How will the team report claim changes?', evidence_line=6,
                                     lead_in='You described the pilot decision.')]
        host, guest = self.create_room()
        code = host['room_code']
        with patch.object(planning_workflow, 'generate_research_plan', return_value=self.plan):
            with self.client.websocket_connect(f'/ws/{code}') as h, self.client.websocket_connect(f'/ws/{code}') as g:
                calls = self.funded(*outputs)
                for socket, token in ((h, host['player_token']), (g, guest['player_token'])):
                    socket.send_json({'type': 'hello', 'token': token})
                    self.until(socket, 'lobby')
                h.send_json({'type': 'prepare_research_plan'})
                for socket in (h, g):
                    self.until(socket, research_planning_status='ready')
                h.send_json({'type': 'approve_research_plan', 'plan_id': self.plan.id,
                             'question_budget': 4, 'confirm_profile': True})
                for socket in (h, g):
                    self.until(socket, research_plan_approved=True)
                h.send_json({'type': 'start', 'plan_id': self.plan.id, 'question_budget': 4})
                for socket in (h, g):
                    self.until(socket, 'voting', 1)
                h.send_json({'type': 'cast_vote', 'seat': 0})
                for socket in (h, g):
                    self.until(socket, 'voting', 1)
                self.now += VOTE_MS + 1
                self.client.portal.call(game_server._coordinator(game_server.rooms[code]).execute,
                                        CatchUpDeadline())
                for socket in (h, g):
                    self.until(socket, 'question', 1)
                h.send_json({'type': 'submit_answer', 'turn': 0, 'answer': 'Answer 1.'})
                for socket in (h, g):
                    state = self.until(socket, 'voting' if retry else 'retry', 2 if retry else 1)
                    self.assertEqual(state['turns'][0]['answer'], 'Answer 1.')
                    if retry:
                        self.assertEqual(state['turns'][-1]['question'], 'How will the team report claim changes?')
                        self.assertIsNone(state.get('error'))
                    else:
                        self.assertIn('HTTP 429', state['error'])
                        self.assertNotIn('private upstream details', state['error'])
                room = game_server.rooms[code]
                self.assertIsNone(room.question_retry_generation_id)
        expected_models = ['z-ai/glm-5.3-flash', 'deepseek/deepseek-v4.1-flash-1017',
                           'deepseek/deepseek-v4.1-flash-1017', 'anthropic/claude-haiku-5.5']
        if retry:
            expected_models.append('anthropic/claude-haiku-5.5')
        self.assertEqual([call['model'] for call in calls], expected_models)
        account = self._offline_credentials[2]
        snapshot = ProviderAllowance(f'run:{room.run_id}', account['id']).snapshot()
        policy = RunQuestionPolicy(**ProviderAllowance(f'run:{room.run_id}', account['id']).policy())
        failed = policy.stage_bound(len(json.dumps(
            {'messages': calls[3]['messages'], 'schema': calls[3]['response_format']},
            ensure_ascii=False).encode()) + FRAMING_BYTES, calls[3]['max_tokens'])
        self.assertEqual(snapshot['used'], (2_000_000 if retry else 1_500_000) + failed)
        self.assertEqual(snapshot['remaining'], snapshot['ceiling'] - snapshot['used'])


if __name__ == '__main__':
    unittest.main()

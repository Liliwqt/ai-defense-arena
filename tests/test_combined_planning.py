"""Combined-planning contracts; all AI and provider calls stay offline."""
import unittest
from copy import deepcopy

from backend.defense_session import PlannedMove, ResearchDefenseSession
from backend.openrouter_questions import COMBINED_PLANNING, SEPARATE_PLANNING
from backend.project_files import ProjectFile
from backend.question_generator import (
    GroundedQuestion, ProbeRequest, QuestionGenerationError, RESEARCH_PANELISTS,
    ResearchMove, TopicAssessmentDraft,
)
from backend.rooms.model import Player, Room
from backend.rooms.submissions import capture_interpretation
from backend.timed_turn import PendingSubmission
from tests import test_research_plan as maps
from tests.test_openrouter_questions import IsolatedAllowanceTests


METHODOLOGY, ETHICS, IMPACT, JUDGE = RESEARCH_PANELISTS


def evidence():
    return GroundedQuestion('How will the team carry out the pilot?', 'study.md', 4,
                            maps.PAPER.splitlines()[3])


def assessment(topic_id, turn, status='discussed'):
    return TopicAssessmentDraft(topic_id=topic_id, turn=turn, status=status,
                                reason='The defender explained this topic.')


class CombinedCaptureTests(unittest.TestCase):
    def setUp(self):
        self.session = ResearchDefenseSession.create(maps.fixture_plan(), 4, 'research', 'proposal')
        self.session.apply_move(ResearchMove(METHODOLOGY, evidence(), 'topic-1', False, None))
        self.players = {'host': Player('host', 'Host', 0, True),
                        'guest': Player('guest', 'Sam', 1, False)}
        self.files = [ProjectFile('study.md', maps.PAPER, 'research_text')]

    def room(self, contract):
        return Room('OFFLINE', self.files, self.players, 'research', 'proposal',
                    defense=self.session, owner_account_id='owner', run_id='run:combined',
                    planning_contract=contract, phase='question')

    def pending(self):
        return PendingSubmission(0, 'guest', 'Sam', 1, 'We will recruit volunteers.', 1000,
                                 input_provenance={'source': 'speech'})

    def test_combined_capture_uses_a_detached_prospective_answer(self):
        room = self.room(COMBINED_PLANNING)
        before = deepcopy(self.session)
        work = capture_interpretation(room, self.pending())
        self.assertIsNot(work.planning_session, room.defense)
        self.assertEqual(room.defense.turns[0].answer, before.turns[0].answer)
        self.assertIsNone(room.defense.turns[0].answer)
        self.assertIsNone(room.defense.turns[0].speaker_name)
        prospective = work.planning_session.turns[0]
        self.assertEqual(prospective.answer, 'We will recruit volunteers.')
        self.assertEqual(prospective.speaker_name, 'Sam')
        self.assertEqual(prospective.input_provenance, {'source': 'speech'})
        self.assertEqual(work.planning_session.context()['previous_turn'], 0)
        self.assertEqual(work.recovery_namespace,
                         f'{room.code}:{room.defense_view_id}:{room.preparation_id}')

    def test_separate_capture_keeps_the_legacy_path_and_no_recovery_namespace(self):
        work = capture_interpretation(self.room(SEPARATE_PLANNING), self.pending())
        self.assertIsNone(work.planning_session)
        self.assertIsNone(work.recovery_namespace)
        self.assertEqual(work.planning_contract, SEPARATE_PLANNING)


class CombinedPlanValidationTests(unittest.TestCase):
    def setUp(self):
        self.session = ResearchDefenseSession.create(maps.fixture_plan(), 4, 'research', 'proposal')
        self.session.apply_move(ResearchMove(METHODOLOGY, evidence(), 'topic-1', False, None))
        self.session.submit_answer('We will recruit volunteers.', speaker_name='Host')

    def test_valid_plan_is_accepted(self):
        self.session.validate_plan(PlannedMove(ETHICS, 'topic-2', False, assessment('topic-1', 0)))

    def test_invalid_assessment_selection_and_premature_completion_are_rejected(self):
        cases = (
            (PlannedMove(ETHICS, 'topic-2', False, assessment('topic-2', 0)),
             'invalid coverage assessment'),
            (PlannedMove('unassigned', 'topic-2', False, assessment('topic-1', 0)),
             'invalid research topic or reviewer'),
            (PlannedMove(None, None, False, assessment('topic-1', 0)),
             'ended the research defense too early'),
        )
        for planned, message in cases:
            with self.subTest(message=message), self.assertRaisesRegex(QuestionGenerationError, message):
                self.session.validate_plan(planned)


class CombinedFundedTests(IsolatedAllowanceTests):
    def setUp(self):
        super().setUp()
        from backend.openrouter_questions import establish_run_allowance
        self.session.apply_move(ResearchMove(METHODOLOGY, evidence(), 'topic-1', False, None))
        self.room = Room('COMBINED', self.files, {'host': Player('host', 'Host', 0, True)},
                         'research', 'proposal', defense=self.session, owner_account_id='owner',
                         run_id='combined-funds', planning_contract=COMBINED_PLANNING, phase='question')
        self.request = capture_interpretation(self.room, PendingSubmission(
            0, 'host', 'Host', 0, 'We will recruit volunteers.', 1000))
        self.scope = 'run:combined-funds'
        self.policy = establish_run_allowance(self.scope, 'owner', self.files, 4)
        self.calls = []

    def response(self, request, *, unknown_usage=False):
        import json
        from tests.test_openrouter_questions import stream_response
        body = json.loads(request.content)
        self.calls.append(body)
        context = json.JSONDecoder().raw_decode(
            body['messages'][-1]['content'].split('Planning context (data):\n')[1])[0]
        output = {'action': 'answer', 'clarification': None, 'probe': None,
                  'assessment': {'topic_id': context['previous_topic'], 'turn': context['previous_turn'],
                                 'status': 'discussed', 'reason': 'The defender described volunteer recruitment.'},
                  **context['question_options'][0]}
        return stream_response(output, usage={} if unknown_usage else {'cost': 0})

    def invoke(self, handler):
        import asyncio
        import httpx
        from unittest.mock import patch
        from backend.rooms.submissions import request_interpretation
        from tests.test_openrouter_questions import HTTPClient
        with patch('httpx.Client', side_effect=lambda **kw: HTTPClient(transport=httpx.MockTransport(handler))):
            return asyncio.run(request_interpretation(self.request))

    def test_combined_prompt_targets_latest_submission_not_prior_transcript(self):
        self.session.submit_answer('The earlier design compares campus queues.', speaker_name='Sam')
        question = GroundedQuestion('How will participation be voluntary?', 'study.md', 4, maps.PAPER.splitlines()[3])
        self.session.apply_move(ResearchMove(ETHICS, question, 'topic-2', False, assessment('topic-1', 0)))
        self.request = capture_interpretation(self.room, PendingSubmission(
            1, 'host', 'Host', 0, 'We will recruit volunteers.', 1000))
        decision = self.invoke(self.response)
        system, user = (item['content'] for item in self.calls[0]['messages'])
        self.assertIn('Latest submission', system)
        self.assertIn('previous_turn', system)
        self.assertIn('previous_topic', system)
        self.assertIn('partial explanation', system)
        self.assertNotIn('(the last transcript turn)', system)
        self.assertIn(self.files[0].content.splitlines()[3], user)
        self.assertIn('The earlier design compares campus queues.', user)
        self.assertIn('We will recruit volunteers.', user)
        self.assertEqual(decision.plan.panelist, IMPACT)
        self.assertIsNone(self.session.turns[1].answer)
        self.assertEqual(self.session.coverage['topic-2']['status'], 'discussed')

    def test_probe_reply_plans_from_both_speakers_without_resolving_live_exchange(self):
        original = 'We will compare consenting campus volunteers.'
        reply = 'The comparison group follows the same recruitment criteria.'
        self.session.begin_probe(original, ProbeRequest('Which comparison group?'), speaker_name='Ana')
        probe = self.session.turns[0].probe
        self.request = capture_interpretation(self.room, PendingSubmission(
            0, 'guest', 'Sam', 1, reply, 1000, probe.id))
        decision = self.invoke(self.response)
        call = self.calls[0]
        self.assertEqual(call['response_format']['json_schema']['name'], 'CombinedSubmissionDraft')
        self.assertIsNotNone(decision.plan)
        self.assertIsNotNone(decision.plan_identity)
        system, user = (item['content'] for item in call['messages'])
        self.assertIn('original answer and the attributed probe reply together', system)
        self.assertIn(original, user)
        self.assertIn(reply, user)
        self.assertIn('"speaker_name": "Ana"', user)
        self.assertIn('Latest submission speaker (data): "Sam"', user)
        self.assertEqual(self.session.turns[0].answer, original)
        self.assertEqual(probe.status, 'pending')
        self.assertIsNone(probe.reply)
        self.assertEqual(self.session.coverage['topic-1']['status'], 'discussed')

    def test_concurrent_combined_dispatch_preserves_protected_funds_and_unknown_hold(self):
        import asyncio
        import json
        import httpx
        from unittest.mock import patch
        from backend.openrouter_questions import FRAMING_BYTES
        from backend.provider_allowance import ProviderAllowance
        from backend.rooms.submissions import request_interpretation
        from tests.test_openrouter_questions import HTTPClient
        self.invoke(self.response)
        body = self.calls.pop()
        size = len(json.dumps({'messages': body['messages'], 'schema': body['response_format']},
                              ensure_ascii=False).encode()) + FRAMING_BYTES
        bound = self.policy.stage_bound(size, body['max_tokens'])
        allowance = ProviderAllowance(self.scope, 'owner')
        allowance.reserve(self.policy.question_limit_nano - bound, limit=self.policy.question_limit_nano)

        async def race():
            return await asyncio.gather(request_interpretation(self.request),
                                        request_interpretation(self.request), return_exceptions=True)
        with patch('httpx.Client', side_effect=lambda **kw: HTTPClient(transport=httpx.MockTransport(
                lambda request: self.response(request, unknown_usage=True)))):
            outcomes = asyncio.run(race())
        self.assertEqual(sum(not isinstance(value, BaseException) for value in outcomes), 1)
        self.assertEqual(sum(isinstance(value, QuestionGenerationError) for value in outcomes), 1)
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(allowance.snapshot()['remaining'], self.policy.coaching_reserve_nano)
        self.assertEqual(ProviderAllowance(self.scope, 'owner').snapshot(), allowance.snapshot())
        self.assertIsNone(self.session.turns[0].answer)


if __name__ == "__main__":
    unittest.main()

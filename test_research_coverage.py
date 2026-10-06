from offline_accounts import authenticate
"""Coverage policy and real room protocol with offline AI and clocks."""
import asyncio
from copy import deepcopy
import os
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from pydantic import ValidationError
import game_server
from defense_session import ResearchDefenseSession, advance_defense
from project_files import ProjectFile
from question_generator import (RESEARCH_PANELISTS, ResearchMove, ResearchMoveDraft, TopicAssessmentDraft,
    GroundedQuestion, GroundedCitation, QuestionGenerationError, generate_research_move,
    generate_coaching_report, CoachingDraft, CoachingPoint, CoachingReport, SubmissionDecision, AnsweredQuestion)
from research_plan import ResearchPlan, ResearchTopic

PAPER = '\n'.join(f'Section {i}: The proposal will examine campus queue pilot decision {i}.' for i in range(1, 13))
FILES = [ProjectFile('paper.md', PAPER, 'research_text')]


def plan(count=12):
    return ResearchPlan(tuple(ResearchTopic(f'topic-{i+1}', f'Pilot decision {i+1}', 'Explain the stated pilot decision and its evidence.',
        RESEARCH_PANELISTS[i % 4], (GroundedCitation('paper.md', i+1, PAPER.splitlines()[i], f'Line {i+1}', 'research_text'),))
        for i in range(count)))


class Client:
    def __init__(self, output):
        self.responses, self.output, self.calls = self, output, []
    def parse(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(output_parsed=self.output)


def proposal(context, history, *, followup=False, mixed=False):
    previous = history[-1] if history else None
    status = 'needs clarification' if previous and (previous.timed_out or followup) else 'addressed'
    assessment = None if previous is None else {'topic_id': context['previous_topic'], 'turn': context['previous_turn'],
                                               'status': status, 'reason': 'No answer was submitted.' if previous.timed_out else 'The defender explained the pilot decision.'}
    exhausted = context['budget_exhausted']
    coverage = deepcopy(context['coverage'])
    if assessment:
        coverage[assessment['topic_id']]['status'] = status
    finished = exhausted or (all(c['status'] == 'addressed' for c in coverage.values()) and len(context['reviewers_spoken']) == 4)
    if finished:
        return dict(action='complete', panelist=None, lead_in=None, question=None, source_file=None,
                    evidence_line=None, topic_id=None, is_follow_up=False, assessment=assessment)
    choices = context['question_options']
    option = next((o for o in choices if o['is_follow_up']), None) if followup else next((o for o in choices if not o['is_follow_up']), None)
    option = option or choices[0]
    topic = next(t for t in context['plan']['topics'] if t['id'] == option['topic_id'])
    return dict(action='ask', **option, lead_in='' if previous is None else ('No answer was recorded. We can return to that issue.' if previous.timed_out else 'You described a pilot decision. Let’s examine its evidence.'),
                question=f"How will the team justify {topic['title'].lower()} in discussion {len(history)+1}?",
                source_file=2 if mixed and len(history) % 2 else 1,
                evidence_line=1 if mixed and len(history) % 2 else topic['references'][0]['evidence_line'], assessment=assessment)


def mocked_move(files, key, *, history, context, **kwargs):
    kwargs.pop("client", None)
    output = proposal(context, history, mixed=len(files) > 1)
    return generate_research_move(files, 'offline-key', history=history, context=context, client=Client(output), **kwargs)


class CoveragePolicyTests(unittest.TestCase):
    def session(self, topics=12, budget=12):
        return ResearchDefenseSession.create(plan(topics), budget, 'research', 'proposal')
    def apply(self, session, **kwargs):
        output = proposal(session.context(), session.answered_history(), **kwargs)
        client = Client(output)
        move = generate_research_move(FILES, 'offline-key', history=session.answered_history(), context=session.context(), client=client)
        session.apply_move(move)
        return client

    def test_twelve_turns_reviewer_revisits_and_exact_budget_stop(self):
        session = self.session()
        for index in range(12):
            self.apply(session)
            self.assertEqual(len(session.turns), index+1)
            self.assertEqual(session.turns[-1].panelist, RESEARCH_PANELISTS[index % 4])
            session.submit_answer('We will measure pilot waiting times and document our reasoning.', speaker_name='Sam')
        self.apply(session)
        self.assertTrue(session.completed)
        self.assertEqual(session.completion_reason, 'budget exhausted')
        self.assertEqual(len(session.turns), 12)
        self.assertEqual(sum(c['status'] == 'addressed' for c in session.coverage.values()), 12)
        self.assertTrue(all(c['turns'] for c in session.coverage.values()))
        with self.assertRaises(ValueError):
            session.submit_answer('late')
        with self.assertRaises(ValueError):
            self.apply(session)

    def test_coverage_can_complete_before_budget_but_requires_four_openings(self):
        session = self.session(1, 20)
        for role in RESEARCH_PANELISTS:
            self.apply(session)
            self.assertEqual(session.turns[-1].panelist, role)
            session.submit_answer('We explain the pilot through this reviewer’s specialty.')
        self.apply(session)
        self.assertEqual(len(session.turns), 4)
        self.assertEqual(session.completion_reason, 'coverage addressed')

    def test_one_immediate_followup_then_untouched_topic(self):
        session = self.session(4, 8)
        self.apply(session)
        session.submit_answer('We have not decided the details.')
        self.apply(session, followup=True)
        self.assertTrue(session.turns[-1].is_follow_up)
        self.assertEqual(session.turns[-1].topic_id, 'topic-1')
        session.submit_answer('We will measure queue times and justify the pilot.')
        self.apply(session)
        self.assertFalse(session.turns[-1].is_follow_up)
        self.assertEqual(session.turns[-1].panelist, RESEARCH_PANELISTS[1])
        self.assertEqual(session.turns[-1].topic_id, 'topic-2')

    def test_research_request_allows_conditional_advice_after_an_accepted_answer(self):
        session = self.session(4, 8)
        self.apply(session)
        answer = 'We can recruit classmates, but access to other departments is limited.'
        session.submit_answer(answer, speaker_name='Sam')
        advice = 'One option is broader recruitment if access permits; otherwise the team could narrow its claim.'
        output = proposal(session.context(), session.answered_history()) | {'lead_in': advice}
        client = Client(output)
        move = generate_research_move(FILES, 'offline-key', history=session.answered_history(),
            context=session.context(), client=client, research_stage='proposal')
        self.assertEqual(move.question.lead_in, advice)
        self.assertEqual(move.question.evidence_text, PAPER.splitlines()[1])
        system, data = [item['content'] for item in client.calls[0]['input']]
        self.assertIn('conditional advice', system)
        self.assertIn('not defender evidence', system)
        self.assertIn(answer, data)

    def test_opening_and_timeout_requests_have_no_reasoning_to_advise_on(self):
        session = self.session(4, 8)
        opening = self.apply(session)
        self.assertEqual(session.turns[0].question.lead_in, '')
        self.assertIn('Do not offer a suggestion in lead_in', opening.calls[0]['input'][0]['content'])
        session.time_out_current()
        client = self.apply(session, followup=True)
        self.assertIn('Do not offer a suggestion in lead_in', client.calls[0]['input'][0]['content'])
        self.assertIsNone(session.answered_history()[0].answer)
        self.assertEqual(session.coverage['topic-1']['status'], 'needs clarification')

    def test_advice_validation_retry_preserves_answer_and_unassessed_coverage(self):
        for invalid in ('too_long', 'too_many_sentences', 'citation'):
            with self.subTest(invalid=invalid):
                session = self.session(4, 8)
                self.apply(session)
                answer = 'We will retain the small pilot and limit conclusions to its participants.'
                session.submit_answer(answer, speaker_name='Sam')
                before = deepcopy(session.coverage)
                output = proposal(session.context(), session.answered_history())
                output['lead_in'] = 'One option is to narrow the claim if recruitment is limited.'
                if invalid == 'too_long': output['lead_in'] = 'x' * 301
                if invalid == 'too_many_sentences': output['lead_in'] = 'An option exists. It may help. It has costs.'
                if invalid == 'citation': output['evidence_line'] = 999
                with self.assertRaises(QuestionGenerationError):
                    move = generate_research_move(FILES, 'offline-key', history=session.answered_history(),
                        context=session.context(), client=Client(output))
                    session.apply_move(move)
                self.assertEqual(session.coverage, before)
                self.assertEqual(len(session.turns), 1)
                self.assertEqual(session.answered_history()[0].answer, answer)
                self.apply(session)
                self.assertEqual(len(session.turns), 2)
                self.assertEqual(session.turns[0].answer, answer)

    def test_invalid_move_is_atomic_and_retry_keeps_answer(self):
        for change in ('unknown_topic', 'wrong_role', 'early_completion', 'wrong_assessment_turn', 'wrong_assessment_topic', 'timeout_addressed', 'repeat_question', 'double_followup'):
            with self.subTest(change=change):
                session = self.session(4, 8)
                self.apply(session)
                if change == 'timeout_addressed': session.time_out_current()
                else: session.submit_answer('An accepted answer that must survive retry.')
                if change == 'double_followup':
                    self.apply(session, followup=True); session.submit_answer('More detail.')
                output = proposal(session.context(), session.answered_history())
                if change == 'unknown_topic': output['topic_id'] = 'unowned'
                if change == 'wrong_role': output['panelist'] = RESEARCH_PANELISTS[2]
                if change == 'early_completion':
                    output.update(action='complete', panelist=None, lead_in=None, question=None, source_file=None, evidence_line=None, topic_id=None)
                if change == 'wrong_assessment_turn': output['assessment']['turn'] = 99
                if change == 'wrong_assessment_topic': output['assessment']['topic_id'] = 'topic-3'
                if change == 'timeout_addressed': output['assessment']['status'] = 'addressed'
                if change == 'repeat_question': output['question'] = session.turns[0].question.question
                if change == 'double_followup': output.update(topic_id='topic-1', panelist=RESEARCH_PANELISTS[0], is_follow_up=True)
                before = deepcopy(session.coverage)
                move = generate_research_move(FILES, 'offline-key', history=session.answered_history(), context=session.context(), client=Client(output))
                with self.assertRaises(QuestionGenerationError): session.apply_move(move)
                self.assertEqual(session.coverage, before)
                count = len(session.turns)
                self.apply(session)
                self.assertEqual(len(session.turns), count + 1)
                self.assertTrue(session.turns[count - 1].resolved)

    def test_timeout_budget_and_clarification_do_not_invent_answers(self):
        from question_generator import ClarificationExchange
        session = self.session(4, 4)
        for i in range(4):
            self.apply(session)
            session.turns[-1].clarifications.append(ClarificationExchange('Simpler please', 'A same-question explanation.'))
            self.assertEqual(len(session.turns), i+1)
            session.time_out_current()
        client = self.apply(session)
        self.assertEqual(session.completion_reason, 'budget exhausted')
        self.assertTrue(all(c['status'] == 'needs clarification' for c in session.coverage.values()))
        self.assertTrue(all(h.answer is None for h in session.answered_history()))
        self.assertIn('A timeout is no answer', client.calls[0]['input'][0]['content'])

    def test_budget_does_not_allow_skipping_openers_or_extra_question(self):
        session = self.session(4, 4)
        for i in range(4):
            self.apply(session); session.submit_answer('We explained the topic.')
        output = proposal(session.context(), session.answered_history())
        output.update(action='ask', panelist=RESEARCH_PANELISTS[0], topic_id='topic-1', question='One extra?', source_file=1, evidence_line=1, lead_in='')
        move = generate_research_move(FILES, 'offline-key', history=session.answered_history(), context=session.context(), client=Client(output))
        before = deepcopy(session.coverage)
        with self.assertRaises(QuestionGenerationError): session.apply_move(move)
        self.assertEqual(session.coverage, before)
        self.assertEqual(len(session.turns), 4)

    def test_early_end_preserves_answers_and_labels_active_turn_separately(self):
        for count in (0, 1, 3):
            session = self.session()
            for _ in range(count):
                self.apply(session); session.submit_answer('Accepted detail.')
            self.apply(session)
            session.end()
            self.assertTrue(session.completed)
            self.assertTrue(session.turns[-1].ended_early)
            self.assertFalse(session.turns[-1].timed_out)
            self.assertEqual(len(session.answered_history()), count)
            self.assertEqual(session.completion_reason, 'ended by host')

    def test_enriched_context_prompt_variety_and_mixed_code_citations(self):
        session = ResearchDefenseSession.create(plan(4), 8, 'mixed', 'completed')
        files = FILES + [ProjectFile('queue.py', '    save_reservation(student_id)\n')]
        for i in range(2):
            output = proposal(session.context(), session.answered_history(), mixed=True)
            client = Client(output)
            move = generate_research_move(files, 'offline-key', history=session.answered_history(), context=session.context(), client=client, defense_type='mixed', research_stage='completed')
            session.apply_move(move)
            if i == 0: session.submit_answer('We compared measured waiting times.', speaker_name='Sam')
        self.assertEqual(session.turns[-1].question.filename, 'queue.py')
        self.assertEqual(session.turns[-1].question.evidence_text, '    save_reservation(student_id)')
        system = client.calls[0]['input'][0]['content']
        self.assertIn('Use direct questions by default', system)
        self.assertIn('Never use scenarios in consecutive', system)
        self.assertIn('reported results', system)
        data = client.calls[0]['input'][1]['content']
        self.assertIn('Sam', data)
        self.assertIn('topic-1', data)
        self.assertNotIn('private chat example', data)

    def test_citations_and_completion_dialogue_validation(self):
        session = self.session()
        for changes in ({'evidence_line': 99}, {'source_file': True}, {'source_file': 99}, {'lead_in': 'Invented opening reaction'}, {'is_follow_up': 'false'}):
            output = proposal(session.context(), []) | changes
            with self.assertRaises((QuestionGenerationError, ValidationError)):
                generate_research_move(FILES, 'offline-key', history=[], context=session.context(), client=Client(output))
        with self.assertRaises(QuestionGenerationError):
            generate_research_move(FILES, None, history=[], context=session.context(), client=Client(None))

    def test_structured_output_limits_opening_to_server_options(self):
        # A mixed paper can assign its first topic to Critical rather than
        # Methodology. The model must choose an allowed Methodology topic.
        prepared = plan(4)
        prepared = ResearchPlan((prepared.topics[3], *prepared.topics[:3]))
        session = ResearchDefenseSession.create(prepared, 12, 'mixed', 'proposal')
        client = Client(proposal(session.context(), []))
        generate_research_move(FILES, 'offline-key', history=[], context=session.context(), client=client)
        response_format = client.calls[0]['text_format']
        valid = proposal(session.context(), [])
        response_format.model_validate(valid)
        for changes in ({'panelist': RESEARCH_PANELISTS[3]}, {'topic_id': 'topic-4'},
                        {'topic_id': 'topic-999'}, {'is_follow_up': True}, {'panelist': None},
                        {'action': 'complete'}, {'assessment': {'topic_id': 'topic-1', 'turn': 0,
                         'status': 'addressed', 'reason': 'An opening has no answer.'}}):
            with self.subTest(changes=changes), self.assertRaises(ValidationError):
                response_format.model_validate(valid | changes)
        self.assertIn('topic-1', str(response_format.model_json_schema()))

    def test_structured_output_budget_exhaustion_allows_only_completion_choice(self):
        session = self.session(4, 4)
        for _ in range(4):
            self.apply(session)
            session.submit_answer('We explained the pilot decision.')
        client = Client(proposal(session.context(), session.answered_history()))
        generate_research_move(FILES, 'offline-key', history=session.answered_history(),
                               context=session.context(), client=client)
        response_format = client.calls[0]['text_format']
        valid = client.output
        response_format.model_validate(valid)
        for changes in ({'panelist': RESEARCH_PANELISTS[0]}, {'topic_id': 'topic-1'},
                        {'is_follow_up': True}, {'action': 'ask'}, {'question': 'An extra question?'}):
            with self.subTest(changes=changes), self.assertRaises(ValidationError):
                response_format.model_validate(valid | changes)

    def test_coaching_accepts_early_and_long_research_transcripts_and_validates_references(self):
        for length in (1, 4, 12, 100):
            session = self.session(12, 100)
            self.apply(session)
            session.submit_answer('We will measure waiting times.')
            history = session.answered_history() * length
            draft = CoachingDraft(summary='Discussion ended with some topics unresolved.', strengths=[CoachingPoint(turn=length-1, text='A concrete measure.')],
                improvements=[CoachingPoint(turn=0, text='Explain safeguards.')], next_step='Resolve remaining topics.')
            client = Client(draft)
            report = generate_coaching_report(FILES, history, 'offline-key', client=client, defense_type='research', research_context=session.context())
            self.assertEqual(report.strengths[0]['turn'], length-1)
            self.assertIn('coverage_note', client.calls[0]['input'][1]['content'])
            with self.assertRaises(QuestionGenerationError):
                generate_coaching_report(FILES, history, 'offline-key', client=Client(draft.model_copy(update={'improvements':[CoachingPoint(turn=length, text='Bad ref')]})), defense_type='research')

    def test_research_coaching_distinguishes_advice_from_the_teams_explanation(self):
        advice = 'One option is broader recruitment if access permits.'
        answer = 'We will retain classmates and narrow the claim to this department.'
        history = [AnsweredQuestion(RESEARCH_PANELISTS[0], 'Why this scope?', answer, lead_in=advice)]
        draft = CoachingDraft(summary='The team explained a narrower scope.',
            strengths=[CoachingPoint(turn=0, text='The team aligned the claim with its recruitment.')],
            improvements=[CoachingPoint(turn=0, text='Explain the remaining limitations.')],
            next_step='Document the chosen scope and its limits.')
        for mode in ('research', 'mixed'):
            with self.subTest(mode=mode):
                client = Client(draft)
                report = generate_coaching_report(FILES, history, 'offline-key', client=client,
                    defense_type=mode, research_stage='completed')
                system, data = [item['content'] for item in client.calls[0]['input']]
                self.assertIn('conditional advice', system)
                self.assertIn('Panelist suggestions are not team strengths', system)
                self.assertIn(advice, data)
                self.assertIn(answer, data)
                self.assertEqual(report.strengths[0]['turn'], 0)


class CoverageRoomTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        authenticate(self, unit_server=game_server)
        self.host = game_server.Player('host', 'Host', 0, True)
        self.guest = game_server.Player('guest', 'Sam', 1, False)
        self.room = game_server.Room('OFFLINE', FILES, {'host':self.host, 'guest':self.guest}, 'research', 'proposal')
        self.events = []
        async def send(event): self.events.append(event)
        self.socket = SimpleNamespace(send_json=send)

    async def test_research_start_requires_current_approved_budget_and_host(self):
        for player, message in ((self.guest, {'type':'start'}), (self.host, {'type':'start'})):
            await game_server._handle_action(self.room, player, self.socket, message)
            self.assertEqual(self.events[-1]['type'], 'error')
            self.assertEqual(self.room.phase, 'lobby')
        self.room.research_plan, self.room.research_planning_status = plan(), 'ready'
        await game_server._handle_action(self.room, self.host, self.socket, {'type':'approve_research_plan', 'plan_id':self.room.research_plan.id, 'question_budget':12})
        for budget in (None, True, 20):
            await game_server._handle_action(self.room, self.host, self.socket, {'type':'start', 'plan_id':self.room.research_plan.id, 'question_budget':budget})
            self.assertEqual(self.events[-1]['type'], 'error')
        with patch('game_server._schedule_generation') as schedule:
            await game_server._handle_action(self.room, self.host, self.socket, {'type':'start', 'plan_id':self.room.research_plan.id, 'question_budget':12})
            schedule.assert_called_once()
        self.assertIsInstance(self.room.defense, ResearchDefenseSession)
        self.assertEqual(self.room.snapshot()['question_budget'], 12)

    async def test_end_during_generation_discards_late_move_and_empty_summary_has_no_ai(self):
        self.room.defense = ResearchDefenseSession.create(plan(), 12, 'research', 'proposal')
        self.room.phase, self.room.generation_id = 'generating', 1
        started, release = asyncio.Event(), asyncio.Event()
        async def delayed(*args, **kwargs):
            started.set(); await release.wait()
            return ResearchMove(RESEARCH_PANELISTS[0], GroundedQuestion('How?', 'paper.md', 1, PAPER.splitlines()[0]), 'topic-1', False, None)
        with patch('game_server.asyncio.to_thread', side_effect=delayed), patch('game_server._schedule_coaching'):
            task = asyncio.create_task(game_server._generate_question(self.room, 1, True))
            await started.wait()
            await game_server._handle_action(self.room, self.guest, self.socket, {'type':'end_defense'})
            self.assertEqual(self.room.phase, 'generating')
            await game_server._handle_action(self.room, self.host, self.socket, {'type':'end_defense'})
            release.set(); await task
        self.assertEqual(self.room.phase, 'complete')
        self.assertEqual(self.room.defense.turns, [])
        with patch('game_server.generate_coaching_report') as coach:
            await game_server._generate_coaching(self.room, self.room.feedback_generation_id)
            coach.assert_not_called()
        self.assertEqual(self.room.feedback.strengths, [])
        self.assertIn('before any answer', self.room.feedback.summary)

    async def test_invalid_move_retry_reconnect_snapshot_and_early_end_cancel_clock(self):
        session = ResearchDefenseSession.create(plan(), 12, 'research', 'proposal')
        self.room.defense = session
        session.apply_move(mocked_move(FILES, None, history=[], context=session.context(), defense_type='research'))
        session.submit_answer('The pilot uses a measured wait-time comparison.', speaker_name='Host')
        before = deepcopy(session.coverage)
        self.room.phase, self.room.generation_id = 'generating', 1
        output = proposal(session.context(), session.answered_history())
        output['topic_id'] = 'unknown'
        invalid = generate_research_move(FILES, 'offline-key', history=session.answered_history(), context=session.context(), client=Client(output))
        with patch('game_server.generate_research_move', return_value=invalid):
            await game_server._generate_question(self.room, 1, False)
        self.assertEqual(self.room.phase, 'retry')
        self.assertEqual(session.coverage, before)
        restored = self.room.snapshot(self.guest)
        self.assertEqual(restored['turns'][0]['answer'], session.turns[0].answer)
        self.assertEqual(restored['coverage'], before)
        self.room.generation_id += 1
        with patch('game_server.generate_research_move', side_effect=mocked_move), patch('game_server._schedule_clock'):
            await game_server._generate_question(self.room, 2, False)
        self.assertEqual(self.room.phase, 'voting')
        self.room.clock_task = asyncio.create_task(asyncio.sleep(60))
        self.room.pending_submission = None
        with patch('game_server._schedule_coaching'):
            await game_server._handle_action(self.room, self.host, self.socket, {'type':'end_defense'})
        self.assertIsNone(self.room.vote_deadline_ms)
        self.assertIsNone(self.room.clock_task)
        self.assertTrue(session.turns[-1].ended_early)
        self.assertFalse(session.turns[-1].timed_out)
        self.assertEqual(len(session.answered_history()), 1)



class CoverageProtocolTests(unittest.TestCase):
    def setUp(self):
        game_server.rooms.clear()
        self.now = 1_000_000
        for mock in (patch.dict(os.environ, {'GAME_HOST_PASSCODE':'offline-passcode', 'OPENAI_API_KEY':'offline-key'}),
                     patch.object(game_server, '_now_ms', side_effect=lambda: self.now),
                     patch.object(game_server, '_schedule_clock')):
            mock.start(); self.addCleanup(mock.stop)
        authenticate(self)
        self.client = TestClient(game_server.app).__enter__()
        self.addCleanup(lambda:self.client.__exit__(None,None,None))
        authenticate(self, self.client)

    def until(self, socket, phase=None, count=None, **conditions):
        for _ in range(60):
            event=socket.receive_json()
            if event['type']=='error': self.fail(event['message'])
            state=event['state']
            if ((phase is None or state['phase']==phase) and (count is None or len(state['turns'])==count)
                and all(state.get(k)==v for k,v in conditions.items())): return state
        self.fail('Missing room state')

    def test_twelve_question_research_and_mixed_with_vote_clarification_timeout_retry_reconnect_coaching(self):
        for mode in ('research','mixed'):
            with self.subTest(mode=mode):
                files=[('research_files',('paper.md',PAPER.encode(),'text/markdown'))]
                if mode=='mixed': files.append(('files',('queue.py',b'    save_reservation(student_id)\n','text/x-python')))
                response=self.client.post('/api/rooms', data={'host_name':'Host', 'host_passcode':'offline-passcode', 'defense_type':mode, 'research_stage':'proposal'}, files=files)
                self.assertEqual(response.status_code,201,response.text)
                host=response.json(); code=host['room_code']
                guest=self.client.post(f'/api/rooms/{code}/join',json={'name':'Sam'}).json()
                p=plan()
                failed=False
                def generate(files,key,*,history,context,**kwargs):
                    nonlocal failed
                    if len(history)==2 and not failed:
                        failed=True
                        raise QuestionGenerationError('The AI cited an invalid source line. Please retry.')
                    kwargs.pop('client',None)
                    output=proposal(context,history,followup=bool(history and history[-1].timed_out),mixed=mode=='mixed')
                    if output['action']=='ask':
                        if history and not history[-1].timed_out:
                            output['lead_in']='One option is to narrow the pilot claim if recruitment access is limited.'
                        code_citation=mode=='mixed' and len(history)%2==1
                        output['source_file']=next(i for i,f in enumerate(files,1) if f.kind.startswith('research') != code_citation)
                    return generate_research_move(files,'offline-key',history=history,context=context,client=Client(output),**kwargs)
                def interpret(*args,submission,**kwargs):
                    return SubmissionDecision('clarify','Explain the same pilot decision, in simple terms.') if submission=='Simpler please' else SubmissionDecision('answer')
                def coach(files,history,key,model,**kwargs):
                    self.assertEqual(history[0].answer, None)
                    self.assertEqual(history[2].lead_in, 'One option is to narrow the pilot claim if recruitment access is limited.')
                    self.assertEqual(history[2].answer, 'We will compare queue times with a documented pilot method.')
                    draft=CoachingDraft(summary='The approved budget ended. Unresolved topics remain, including the missed turn.',
                        strengths=[CoachingPoint(turn=1,text='The team described a pilot comparison.')],
                        improvements=[CoachingPoint(turn=0,text='The opening question received no answer.')],next_step='Review remaining topics.')
                    return generate_coaching_report(files,history,'offline-key',client=Client(draft),**kwargs)
                with patch.object(game_server,'generate_research_plan',return_value=p), \
                     patch.object(game_server,'generate_research_move',side_effect=generate) as generator, \
                     patch.object(game_server,'interpret_submission',side_effect=interpret), \
                     patch.object(game_server,'generate_coaching_report',side_effect=coach):
                    with self.client.websocket_connect(f'/ws/{code}') as h, self.client.websocket_connect(f'/ws/{code}') as g:
                        h.send_json({'type':'hello','token':host['player_token']});self.until(h,'lobby')
                        g.send_json({'type':'hello','token':guest['player_token']});self.until(g,'lobby')
                        h.send_json({'type':'prepare_research_plan'})
                        for ws in (h,g):self.until(ws,research_planning_status='ready')
                        h.send_json({'type':'approve_research_plan','plan_id':p.id,'question_budget':12})
                        for ws in (h,g):self.until(ws,research_plan_approved=True)
                        h.send_json({'type':'start','plan_id':p.id,'question_budget':12})
                        for index in range(12):
                            if index==2:
                                for ws in (h,g):
                                    state=self.until(ws,'retry',2)
                                    self.assertEqual(state['turns'][-1]['answer'],'We will compare queue times with a documented pilot method.')
                                saved=deepcopy(game_server.rooms[code].defense.coverage)
                                h.send_json({'type':'retry'})
                            for ws in (h,g):
                                state=self.until(ws,'voting',index+1)
                                self.assertEqual(state['question_budget'],12)
                                turn=state['turns'][-1]
                                expected='    save_reservation(student_id)' if turn['filename']=='queue.py' else PAPER.splitlines()[turn['evidence_line']-1]
                                self.assertEqual(turn['evidence_text'],expected)
                                if index > 1:
                                    self.assertEqual(turn['lead_in'], 'One option is to narrow the pilot claim if recruitment access is limited.')
                            h.send_json({'type':'cast_vote','seat':index%2})
                            for ws in(h,g):self.until(ws,'voting',index+1)
                            self.now+=game_server.VOTE_MS+1
                            self.client.portal.call(game_server._expire_deadline,game_server.rooms[code])
                            for ws in(h,g):
                                state=self.until(ws,'question',index+1);self.assertEqual(state['selected_seat'],index%2)
                            if index==0:
                                self.now+=game_server.ANSWER_MS+1
                                self.client.portal.call(game_server._expire_deadline,game_server.rooms[code])
                            else:
                                speaker=h if index%2==0 else g
                                if index==3:
                                    speaker.send_json({'type':'submit_answer','turn':index,'answer':'Simpler please'})
                                    for ws in(h,g):
                                        state=self.until(ws,'question',index+1)
                                        self.assertEqual(len(state['turns'][-1]['clarifications']),1)
                                        self.assertEqual(len(state['turns']),4)
                                speaker.send_json({'type':'submit_answer','turn':index,'answer':'We will compare queue times with a documented pilot method.'})
                        for ws in(h,g):
                            final=self.until(ws,'complete',12,feedback_status='ready')
                            self.assertEqual(final['completion_reason'],'budget exhausted')
                            self.assertEqual(final['turns'][0]['timed_out'],True)
                            self.assertTrue(final['turns'][1]['is_follow_up'])
                            self.assertEqual(final['coverage']['topic-12']['status'],'pending')
                            self.assertEqual(final['feedback']['strengths'][0]['turn'],1)
                    with self.client.websocket_connect(f'/ws/{code}') as reconnect:
                        reconnect.send_json({'type':'hello','token':guest['player_token']})
                        restored=self.until(reconnect,'complete',12,feedback_status='ready')
                        self.assertEqual(restored['coverage'],final['coverage'])
                        self.assertEqual(restored['completion_reason'],final['completion_reason'])
                        self.assertEqual(restored['turns'],final['turns'])
                    self.assertEqual(generator.call_count,14) # opening, 12 assessments, one retry

class CoverageStreamlitTests(unittest.TestCase):
    def test_twelve_turn_session_coaching_and_early_end(self):
        from streamlit.testing.v1 import AppTest
        advice = 'One option is to narrow the claim if recruitment access is limited.'
        def advice_move(files, key, *, history, context, **kwargs):
            output = proposal(context, history)
            if history and output['action'] == 'ask':
                output['lead_in'] = advice
            return generate_research_move(files, 'offline-key', history=history, context=context,
                client=Client(output), **kwargs)
        with patch.dict(os.environ,{'OPENAI_API_KEY':'offline-key'}), \
             patch('research_plan.generate_research_plan',return_value=plan()), \
             patch('defense_session.generate_research_move',side_effect=advice_move), \
             patch('question_generator.interpret_submission',return_value=SubmissionDecision('answer')):
            app=AppTest.from_file('app.py').run()
            app.selectbox[0].select('Research paper').run()
            app.file_uploader[0].set_value([('paper.md',PAPER.encode(),'text/markdown')]).run()
            self.assertTrue(next(b for b in app.button if b.label=='Start defense').disabled)
            next(b for b in app.button if b.label=='Prepare defense').click().run()
            app.number_input[0].set_value(12).run()
            next(b for b in app.button if b.label=='Confirm question budget').click().run()
            next(b for b in app.button if b.label=='Start defense').click().run()
            for i in range(12):
                self.assertFalse(app.exception)
                self.assertEqual(len(app.session_state['defense_session'].turns),i+1)
                if i:
                    self.assertIn(advice, [caption.value for caption in app.caption])
                    self.assertNotEqual(app.session_state['defense_session'].turns[i-1].answer, advice)
                app.text_area[0].set_value('We will compare queue times with a documented pilot method.')
                next(b for b in app.button if b.label=='Send to panelist').click().run()
            session=app.session_state['defense_session']
            self.assertTrue(session.completed)
            self.assertEqual(session.completion_reason,'budget exhausted')
            self.assertFalse(app.exception)
            next(b for b in app.button if b.label=='Start new defense').click().run()
            next(b for b in app.button if b.label=='End defense').click().run()
            self.assertTrue(app.session_state['defense_session'].turns[-1].ended_early)
            self.assertFalse(app.exception)


class CoverageAdditionalTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        authenticate(self, unit_server=game_server)

    async def test_ending_during_interpretation_discards_result_and_marks_no_answer(self):
        host = game_server.Player('host', 'Host', 0, True)
        room = game_server.Room('OFFLINE', FILES, {'host':host}, 'research', 'proposal')
        room.defense = ResearchDefenseSession.create(plan(4), 8, 'research', 'proposal')
        room.defense.apply_move(mocked_move(FILES, None, history=[], context=room.defense.context()))
        room.phase, room.interpretation_id, room.selected_seat = 'interpreting', 1, 0
        room.pending_submission = game_server.PendingSubmission(0, host.token, host.name, 0, 'Text awaiting interpretation.', 60000)
        started, release = asyncio.Event(), asyncio.Event()
        async def delayed(*args, **kwargs):
            started.set(); await release.wait(); return SubmissionDecision('answer')
        async def send(event): pass
        with patch('game_server.asyncio.to_thread', side_effect=delayed), patch('game_server._schedule_coaching'):
            task=asyncio.create_task(game_server._interpret_pending(room, 1))
            await started.wait()
            await game_server._handle_action(room, host, SimpleNamespace(send_json=send), {'type':'end_defense'})
            release.set(); await task
        self.assertEqual(room.phase, 'complete')
        self.assertIsNone(room.defense.turns[0].answer)
        self.assertTrue(room.defense.turns[0].ended_early)
        self.assertIsNone(room.pending_submission)
        self.assertEqual(room.defense.answered_history(), [])

    async def test_opening_reviewer_uses_assigned_topics_when_they_exist(self):
        session=ResearchDefenseSession.create(plan(4),8,'research','proposal')
        output=proposal(session.context(), [])
        output['topic_id']='topic-2'
        move=generate_research_move(FILES,'offline-key',history=[],context=session.context(),client=Client(output))
        with self.assertRaises(QuestionGenerationError): session.apply_move(move)
        self.assertEqual(session.turns, [])
        self.assertTrue(all(c['status']=='pending' for c in session.coverage.values()))


class CoverageStreamlitRetryTests(unittest.TestCase):
    def test_opening_failure_can_retry_without_losing_run_identity(self):
        from streamlit.testing.v1 import AppTest
        calls=0
        def flaky(*args, **kwargs):
            nonlocal calls
            calls+=1
            if calls==1: raise QuestionGenerationError('Temporary opening failure.')
            return mocked_move(*args, **kwargs)
        with patch.dict(os.environ,{'OPENAI_API_KEY':'offline-key'}), patch('research_plan.generate_research_plan',return_value=plan(4)), patch('defense_session.generate_research_move',side_effect=flaky):
            app=AppTest.from_file('app.py').run()
            app.selectbox[0].select('Research paper').run()
            app.file_uploader[0].set_value([('paper.md',PAPER.encode(),'text/markdown')]).run()
            next(b for b in app.button if b.label=='Prepare defense').click().run()
            next(b for b in app.button if b.label=='Confirm question budget').click().run()
            next(b for b in app.button if b.label=='Start defense').click().run()
            self.assertFalse(app.exception)
            next(b for b in app.button if b.label=='Retry next question').click().run()
            self.assertFalse(app.exception)
            self.assertEqual(len(app.text_area),1)
            self.assertEqual(len(app.session_state['defense_session'].turns),1)
            self.assertGreater(app.session_state['defense_run_id'],0)


if __name__ == '__main__': unittest.main()

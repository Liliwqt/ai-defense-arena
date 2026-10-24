"""Whole fallback walkthroughs; real temporary ledger, external HTTP mocked."""

import json
from pathlib import Path
from unittest.mock import patch

import httpx
from streamlit.testing.v1 import AppTest

from backend.provider_allowance import ProviderAllowance
from tests.test_openrouter_questions import HTTPClient, IsolatedAllowanceTests, stream_response
from tests.test_research_plan import PAPER, draft
from tests.research_coaching_fixtures import cards_for


APP = str(Path(__file__).resolve().parents[1] / 'backend/app.py')


def button(app, label):
    return next(item for item in app.button if item.label == label)


def previous_timed_out(content):
    """Read the last transcript turn's timeout flag from a synthetic request.

    A timed-out turn must be assessed `needs clarification`; the server rejects
    any other status, so the synthetic router has to mirror that rule.
    """
    marker = 'Transcript (data):\n'
    if marker not in content:
        return False
    try:
        transcript = json.JSONDecoder().raw_decode(content.split(marker)[1])[0]
    except (ValueError, IndexError):
        return False
    return bool(transcript) and bool(transcript[-1].get('timed_out'))


def assessment_for(context, content):
    """The assessment a real model would return for this synthetic turn."""
    previous = context['previous_turn']
    if previous is None:
        return None
    if previous_timed_out(content):
        return {'turn': previous, 'topic_id': context['previous_topic'],
                'status': 'needs clarification', 'reason': 'No answer was submitted.'}
    return {'turn': previous, 'topic_id': context['previous_topic'],
            'status': 'discussed', 'reason': 'The defender described a limited pilot.'}


class SyntheticRouter:
    def __init__(self, *, mixed=False):
        self.calls = []
        self.app = None
        self.mixed = mixed
        self.fail_name = None
        self.fail_turns = None
        self.decisions = []
        self.on_request = None
        self.usage = None

    def __call__(self, request):
        body = json.loads(request.content)
        self.calls.append(body)
        if self.on_request is not None:
            override = self.on_request(body)
            if override is not None:
                return override
        name = body['response_format']['json_schema']['name']
        content = body['messages'][-1]['content']
        if self.fail_name == name:
            self.fail_name = None
            return httpx.Response(404, json={'error': 'Synthetic unavailable model'})
        if name == 'ResearchPlanDraft':
            output = draft()
            if self.mixed:
                for topic in output['topics']:
                    topic['references'][0]['source_file'] = 2
                output['profile']['references'][0]['source_file'] = 2
        elif name == 'PlanDraft':
            context = json.JSONDecoder().raw_decode(content.split('Server research context (data):\n')[1])[0]
            assessment = assessment_for(context, content)
            output = {'action': 'complete' if context['budget_exhausted'] else 'ask',
                **({'panelist': None, 'topic_id': None, 'is_follow_up': False} if context['budget_exhausted']
                    else context['question_options'][0]), 'assessment': assessment}
        elif name == 'QuestionDraft':
            context = json.JSONDecoder().raw_decode(content.split('Server research context (data):\n')[1])[0]
            output = {'lead_in': '', 'question': f"How will you explain decision {context['generated_questions']+1}?",
                'source_file': 2 if self.mixed else 1, 'evidence_line': 4}
        elif name == 'CombinedSubmissionDraft':
            context = json.JSONDecoder().raw_decode(content.split('Planning context (data):\n')[1])[0]
            options = context['question_options']
            choice = options[0] if options else None
            assessment = assessment_for(context, content)
            output = {'action': 'answer', 'clarification': None, 'probe': None,
                'assessment': assessment,
                'next_move': choice['choice_id'] if choice else None}
            if self.decisions:
                decision = self.decisions.pop(0)
                if decision.get('action', 'answer') == 'answer':
                    output.update(decision)
                else:
                    output = {'action': decision['action'],
                        'clarification': decision.get('clarification'),
                        'probe': decision.get('probe'), 'assessment': None, 'next_move': None}
        elif name == 'SubmissionDraft':
            output = self.decisions.pop(0) if self.decisions else {'action': 'answer', 'clarification': None, 'probe': None}
        else:
            output = {'summary': 'The team discussed a limited pilot.', 'strengths': [],
                'improvements': [], 'next_step': 'Practice the limits.', 'closing': 'Review those limits.'}
            if name == 'ResearchCoachingDraft':
                import re
                indices = json.loads(re.search(r'only these required zero-based turn indices: (\[[0-9, ]+\])', body['messages'][0]['content']).group(1))
                if self.fail_turns == indices:
                    self.fail_turns = None
                    return httpx.Response(503, json={'error': 'Synthetic unavailable section'})
                history = self.app.session_state['defense_session'].coaching_history()
                output['answer_cards'] = [card for card in cards_for(history) if card['turn'] in indices]
        return stream_response(output, usage=self.usage)


class OpenRouterFallbackTests(IsolatedAllowanceTests):
    def test_explicit_mapping_needs_only_router_and_keeps_one_preparation_allowance(self):
        calls = []

        def provider(request):
            calls.append(json.loads(request.content))
            return stream_response(draft())

        with patch.dict('os.environ', {'OPENAI_API_KEY': '', 'OPENAI_MODEL': 'unused'}), \
             patch('openai.OpenAI', side_effect=AssertionError('No direct provider')), \
             patch('httpx.Client', side_effect=lambda **kw: HTTPClient(transport=httpx.MockTransport(provider))):
            app = AppTest.from_file(APP).run()
            app.file_uploader[0].set_value([('study.md', PAPER.encode(), 'text/markdown')]).run()
            self.assertFalse(button(app, 'Prepare defense').disabled)
            self.assertEqual(calls, [])
            button(app, 'Prepare defense').click().run()
            self.assertFalse(app.exception)
            self.assertEqual(app.session_state['research_plan'].profile.fields, ('Education',))
            self.assertEqual(calls[0]['model'], 'z-ai/glm-5.3-flash')
            self.assertEqual(calls[0]['reasoning'], {'effort': 'low', 'exclude': True})
            app.run()
            self.assertEqual(len(calls), 1)
            with patch.dict('os.environ', {'OPENROUTER_PREPARATION_USD': '0.000001'}):
                button(app, 'Prepare map again').click().run()
            self.assertFalse(app.exception)
            self.assertEqual(len(calls), 2)
            practice = app.session_state['research_provider']
            self.assertEqual(ProviderAllowance(practice.preparation_scope, practice.owner).snapshot()['used'], 1_000_000)
            self.assertFalse(any('OPENAI_API_KEY' in item.value for item in app.warning))

    def test_complete_short_typed_research_uses_assigned_models_and_protected_coaching(self):
        from backend.openrouter_questions import REVIEWER_MODELS
        calls = []
        app = None

        router = SyntheticRouter()
        calls = router.calls

        with patch.dict('os.environ', {'OPENAI_API_KEY': '', 'OPENAI_MODEL': 'unrelated'}), \
             patch('openai.OpenAI', side_effect=AssertionError('No direct provider')), \
             patch('openai.OpenAI', side_effect=AssertionError('No direct provider')), \
             patch('httpx.Client', side_effect=lambda **kw: HTTPClient(transport=httpx.MockTransport(router))):
            app = AppTest.from_file(APP).run()
            router.app = app
            app.file_uploader[0].set_value([('study.md', PAPER.encode(), 'text/markdown')]).run()
            button(app, 'Prepare defense').click().run()
            app.number_input[0].set_value(4).run()
            next(box for box in app.checkbox if box.label == 'I reviewed the research profile').check().run()
            button(app, 'Confirm profile and budget').click().run()
            button(app, 'Start defense').click().run()
            self.assertFalse(app.exception)
            self.assertEqual(len(app.session_state['defense_session'].turns), 1)
            with patch.dict('os.environ', {'OPENROUTER_RUN_USD': 'invalid-after-start'}):
                for _ in range(4):
                    next(area for area in app.text_area if area.label.startswith('Your ')).set_value('We will limit our claim to the campus pilot.')
                    button(app, 'Send to panelist').click().run()
                    self.assertFalse(app.exception)
                self.assertTrue(app.session_state['defense_session'].completed)
                button(app, 'Generate coaching').click().run()
                self.assertFalse(app.exception)
            job = app.session_state['research_coaching_job']
            self.assertEqual(job.completion_status, 'ready')
            self.assertEqual(len(app.session_state['research_coaching'].answer_cards), 4)
            questions = [body for body in calls if body['response_format']['json_schema']['name'] == 'QuestionDraft']
            self.assertEqual([body['model'] for body in questions], list(REVIEWER_MODELS.values()))
            coaching = [body for body in calls if 'CoachingDraft' in body['response_format']['json_schema']['name']]
            self.assertEqual(len(coaching), 3)
            self.assertTrue(all(body['model'] == 'anthropic/claude-haiku-5.5' and body['reasoning'] == {'effort': 'low'} for body in coaching))
            interactive = [body['response_format']['json_schema']['name'] for body in calls
                           if 'Coaching' not in body['response_format']['json_schema']['name']]
            self.assertEqual(interactive, ['ResearchPlanDraft', 'PlanDraft', 'QuestionDraft',
                'CombinedSubmissionDraft', 'QuestionDraft', 'CombinedSubmissionDraft', 'QuestionDraft',
                'CombinedSubmissionDraft', 'QuestionDraft', 'CombinedSubmissionDraft'])
            practice = app.session_state['research_provider']
            self.assertEqual(ProviderAllowance(practice.run_scope, practice.owner).snapshot()['used'], 6_000_000)

    def connect(self, router):
        self.enterContext(patch.dict('os.environ', {'OPENAI_API_KEY': '', 'OPENAI_MODEL': 'unused'}))
        self.enterContext(patch('openai.OpenAI', side_effect=AssertionError('No direct provider')))
        self.enterContext(patch('openai.OpenAI', side_effect=AssertionError('No direct provider')))
        self.enterContext(patch('httpx.Client', side_effect=lambda **kw: HTTPClient(transport=httpx.MockTransport(router))))
        app = AppTest.from_file(APP).run()
        router.app = app
        if router.mixed:
            app.selectbox[0].select('Research + code').run()
            app.file_uploader[0].set_value([('queue.py', b'queue = []\n', 'text/x-python')]).run()
        app.file_uploader[1 if router.mixed else 0].set_value([('study.md', PAPER.encode(), 'text/markdown')]).run()
        return app

    def prepare(self, app, budget):
        button(app, 'Prepare defense').click().run()
        app.number_input[0].set_value(budget).run()
        next(box for box in app.checkbox if box.label == 'I reviewed the research profile').check().run()
        button(app, 'Confirm profile and budget').click().run()

    def send(self, app, text='We will limit our claim to the campus pilot.'):
        next(area for area in app.text_area if area.label.startswith('Your ')).set_value(text)
        button(app, 'Send to panelist').click().run()
        self.assertFalse(app.exception)

    def test_long_mixed_retains_answers_and_ready_sections_through_failed_only_retry(self):
        router = SyntheticRouter(mixed=True)
        app = self.connect(router)
        self.prepare(app, 12)
        button(app, 'Start defense').click().run()
        self.assertFalse(app.exception)
        practice = app.session_state['research_provider']
        scope = practice.run_scope
        router.fail_name = 'QuestionDraft'
        self.send(app)
        self.assertEqual(app.session_state['defense_session'].turns[0].answer, 'We will limit our claim to the campus pilot.')
        self.assertTrue(app.session_state['defense_session'].needs_question)
        button(app, 'Retry question writing').click().run()
        self.assertFalse(app.exception)
        self.assertEqual(practice.run_scope, scope)

        for _ in range(11):
            self.send(app)
        self.assertTrue(app.session_state['defense_session'].completed)
        router.fail_turns = [3, 4, 5]
        button(app, 'Generate coaching').click().run()
        self.assertFalse(app.exception)
        before = app.session_state['research_coaching'].answer_cards
        self.assertEqual(len(before), 9)
        job = app.session_state['research_coaching_job']
        self.assertEqual(job.completion_status, 'pending')
        count = len(router.calls)
        button(app, 'Retry failed coaching sections').click().run()
        self.assertFalse(app.exception)
        self.assertEqual(len(router.calls), count + 1)
        self.assertEqual(job.completion_status, 'ready')
        report = app.session_state['research_coaching']
        self.assertEqual(len(report.answer_cards), 12)
        self.assertEqual([card for card in report.answer_cards if card['turn'] not in (3, 4, 5)], before)
        self.assertTrue(all(card['original_answer'] == 'We will limit our claim to the campus pilot.' for card in report.answer_cards))
        self.assertIn('Review those limits.', [item.value for item in app.markdown])
        app.run()
        self.assertEqual(len(router.calls), count + 1)
        self.assertEqual(practice.run_scope, scope)

    def test_one_processing_window_retains_accepted_answer_after_late_writer(self):
        clock = [1_000_000]
        router = SyntheticRouter()
        with patch('backend.streamlit_turns.now_ms', side_effect=lambda: clock[0], create=True):
            app = self.connect(router)
            self.prepare(app, 4)
            button(app, 'Start defense').click().run()
            def advance_clock(body):
                name = body['response_format']['json_schema']['name']
                clock[0] += 30_000 if name == 'CombinedSubmissionDraft' else 15_000
            router.on_request = advance_clock
            self.send(app, 'Keep my accepted explanation.')
            session = app.session_state['defense_session']
            self.assertEqual(session.turns[0].answer, 'Keep my accepted explanation.')
            self.assertEqual(len(session.turns), 1)
            self.assertTrue(session.needs_question)
            self.assertIn('45-second', ' '.join(item.value for item in app.error))
            count = len(router.calls)
            app.run()
            self.assertEqual(len(router.calls), count)
            router.on_request = None
            button(app, 'Retry question writing').click().run()
            self.assertFalse(app.exception)
            self.assertEqual([call['response_format']['json_schema']['name'] for call in router.calls[count:]], ['QuestionDraft'])

    def test_one_transient_retry_is_shared_by_interpretation_and_writer(self):
        router = SyntheticRouter()
        app = self.connect(router)
        self.prepare(app, 4)
        button(app, 'Start defense').click().run()
        failures = {'CombinedSubmissionDraft': 1, 'QuestionDraft': 1}
        stages = []
        def transient(body):
            name = body['response_format']['json_schema']['name']
            stages.append(app.session_state['research_provider'].turns.status)
            if failures.get(name):
                failures[name] -= 1
                return httpx.Response(503, json={'error': 'Synthetic temporary failure'})
        router.on_request = transient
        before = len(router.calls)
        self.send(app, 'One explanation, not repeated submissions.')
        session = app.session_state['defense_session']
        self.assertEqual(session.turns[0].answer, 'One explanation, not repeated submissions.')
        self.assertTrue(session.needs_question)
        self.assertEqual([body['response_format']['json_schema']['name'] for body in router.calls[before:]],
                         ['CombinedSubmissionDraft', 'CombinedSubmissionDraft', 'QuestionDraft'])
        self.assertIn('Trying again', stages[1])
        self.assertIn('Answer saved', stages[2])
        before = len(router.calls)
        button(app, 'Retry question writing').click().run()
        self.assertEqual([body['response_format']['json_schema']['name'] for body in router.calls[before:]], ['QuestionDraft'])

    def test_provider_directed_retry_and_manual_limits_keep_the_draft(self):
        for headers, message, retries in [({'Retry-After': '2'}, 'upstream busy', 1),
                ({}, 'upstream busy', 0), ({'Retry-After': '50'}, 'upstream busy', 0),
                ({'Retry-After': '2'}, 'free-models-per-day limit exceeded', 0)]:
            with self.subTest(headers=headers, message=message):
                clock = [1_000_000]
                with patch('backend.streamlit_turns.now_ms', side_effect=lambda: clock[0]), \
                     patch('backend.streamlit_turns.sleep', side_effect=lambda seconds: clock.__setitem__(0, clock[0]+int(seconds*1000))):
                    router = SyntheticRouter()
                    app = self.connect(router)
                    self.prepare(app, 4)
                    button(app, 'Start defense').click().run()
                    count = len(router.calls)
                    def rate_limit(body):
                        if len(router.calls) == count+1:
                            return httpx.Response(429, headers=headers, json={'error': {'message': message}})
                    router.on_request = rate_limit
                    self.send(app, 'Do not erase this explanation.')
                    session = app.session_state['defense_session']
                    if retries:
                        self.assertEqual(session.turns[0].answer, 'Do not erase this explanation.')
                        self.assertEqual(len(router.calls)-count, 3)
                    else:
                        self.assertIsNone(session.turns[0].answer)
                        self.assertEqual(len(router.calls)-count, 1)
                        app.run()
                        self.assertEqual(next(area for area in app.text_area if area.label.startswith('Your ')).value,
                                         'Do not erase this explanation.')
                        self.assertIn('not yet accepted', ' '.join(item.value for item in app.info))
                        button(app, 'Retry saved submission').click().run()
                        self.assertEqual(session.turns[0].answer, 'Do not erase this explanation.')

    def test_whole_app_lookup_and_reply_keep_grounding_language_and_current_question(self):
        router = SyntheticRouter(mixed=True)
        app = self.connect(router)
        paper = PAPER + '\n'.join(f'Background note {n}.' for n in range(40)) + '\nDecisive comparison: repeated baseline periods.'
        app.file_uploader[1].set_value([('study.md', paper.encode(), 'text/markdown')]).run()
        self.prepare(app, 8)
        button(app, 'Start defense').click().run()
        session = app.session_state['defense_session']
        original = session.turns[0].question
        router.decisions = [
            {'action': 'clarify', 'clarification': 'Explain how the baseline supports your comparison.'},
            {'action': 'probe', 'probe': {'request': 'Which baseline period?', 'references': []}},
        ]
        self.send(app, 'What comparison do you mean?')
        self.send(app, 'We compare the proposed pilot to baseline periods.')
        self.assertEqual(session.turns[0].question, original)
        count = len(router.calls)
        def lookup(body):
            if len(router.calls) == count+1:
                self.assertNotIn('Decisive comparison:', body['messages'][-1]['content'])
                return stream_response({'lookup': {'query': 'Decisive comparison', 'source_files': [2]}})
        router.on_request = lookup
        self.send(app, 'Sa baseline mi mag-compare sa waiting time, Bisaya lang.')
        requests = router.calls[count:]
        self.assertEqual([body['response_format']['json_schema']['name'] for body in requests],
                         ['CombinedSubmissionDraft', 'CombinedSubmissionDraft', 'QuestionDraft'])
        self.assertIn('BROADER LOOKUP', requests[1]['messages'][-1]['content'])
        self.assertIn('Decisive comparison:', requests[1]['messages'][-1]['content'])
        self.assertIn('Cebuano', requests[-1]['messages'][0]['content'])
        self.assertEqual(session.turns[0].answer, 'We compare the proposed pilot to baseline periods.')
        self.assertEqual(session.turns[0].probe.reply, 'Sa baseline mi mag-compare sa waiting time, Bisaya lang.')
        self.assertEqual(len(session.turns), 2)
        for _ in range(7):
            self.send(app)
        self.assertTrue(session.completed)
        button(app, 'Generate coaching').click().run()
        self.assertEqual(len(app.session_state['research_coaching'].answer_cards), 8)
        self.assertEqual(app.session_state['research_coaching_job'].completion_status, 'ready')

    def test_free_coaching_keeps_its_original_tier_and_run_allowance(self):
        from backend.practice_tiers import FREE_MODEL
        router = SyntheticRouter()
        router.usage = {'cost': 0}
        with patch.dict('os.environ', {'OPENROUTER_FREE_PER_MINUTE': '1000',
                'OPENROUTER_FREE_DAILY_REQUESTS': '1000', 'OPENROUTER_FREE_OWNER_DAILY_REQUESTS': '1000'}):
            app = self.connect(router)
            next(item for item in app.selectbox if item.label == 'Practice tier').select('Free practice').run()
            self.prepare(app, 4)
            button(app, 'Start defense').click().run()
            practice = app.session_state['research_provider']
            scope = practice.run_scope
            for _ in range(4):
                self.send(app)
            button(app, 'Generate coaching').click().run()
            self.assertFalse(app.exception)
            self.assertEqual(app.session_state['research_coaching_job'].completion_status, 'ready')
            self.assertIs(app.session_state['research_provider'], practice)
            self.assertEqual(practice.run_scope, scope)
            self.assertTrue(all(body['model'] == FREE_MODEL for body in router.calls))
            self.assertEqual(ProviderAllowance(scope, practice.owner).policy()['tier'], 'free')
            self.assertFalse(any(body['response_format']['json_schema']['name'] == 'CombinedSubmissionDraft' for body in router.calls))

    def test_duplicate_operation_is_rejected_and_cancelled_writer_cannot_publish(self):
        from backend.question_generator import QuestionGenerationError
        router = SyntheticRouter()
        app = self.connect(router)
        self.prepare(app, 4)
        button(app, 'Start defense').click().run()
        practice = app.session_state['research_provider']
        session = app.session_state['defense_session']
        count = len(router.calls)
        def interrupt(body):
            if body['response_format']['json_schema']['name'] == 'CombinedSubmissionDraft':
                with self.assertRaisesRegex(QuestionGenerationError, 'already in progress'):
                    practice.flow(session, self.files).submit('Duplicate should not dispatch.')
            else:
                practice.cancel()
        router.on_request = interrupt
        self.send(app, 'Keep this accepted answer despite cancellation.')
        self.assertEqual(session.turns[0].answer, 'Keep this accepted answer despite cancellation.')
        self.assertEqual(len(session.turns), 1)
        self.assertEqual(len(router.calls)-count, 2)
        self.assertIsNone(practice.question_recovery.stage)
        self.assertFalse(practice.turns.busy)
        app.run()
        self.assertEqual(len(router.calls)-count, 2)

    def test_saved_legacy_policy_keeps_separate_planning_without_a_new_allowance(self):
        from dataclasses import asdict
        from backend.defense_session import ResearchDefenseSession
        from backend.openrouter_questions import RunQuestionPolicy
        router = SyntheticRouter()
        app = self.connect(router)
        self.prepare(app, 4)
        practice = app.session_state['research_provider']
        saved = ResearchDefenseSession.create(app.session_state['research_plan'], 4, 'research', 'infer')
        policy = RunQuestionPolicy().snapshotted(self.files, 4)
        ProviderAllowance('retained-legacy-run', practice.owner).establish(policy.ceiling_nano, asdict(policy))
        practice.session, practice.run_scope = saved, 'retained-legacy-run'
        app.session_state['defense_session'] = saved
        app.session_state['defense_run_id'] = 1
        app.run()
        button(app, 'Retry next question').click().run()
        count = len(router.calls)
        self.send(app)
        self.assertEqual([body['response_format']['json_schema']['name'] for body in router.calls[count:]],
                         ['SubmissionDraft', 'PlanDraft', 'QuestionDraft'])
        self.assertEqual(practice.run_scope, 'retained-legacy-run')
        self.assertNotIn('Focused accepted evidence', router.calls[-1]['messages'][-1]['content'])

    def test_failed_submission_attempt_cap_survives_reruns(self):
        router = SyntheticRouter()
        with patch.dict('os.environ', {'AI_INTERPRETATION_ATTEMPTS': '2'}):
            app = self.connect(router)
            self.prepare(app, 4)
            button(app, 'Start defense').click().run()
            count = len(router.calls)
            router.on_request = lambda body: httpx.Response(404, json={'error': 'Synthetic unavailable model'})
            self.send(app, 'Keep this draft through the bounded retries.')
            for _ in range(3):
                app.run()
                button(app, 'Retry saved submission').click().run()
                self.assertFalse(app.exception)
            self.assertEqual(len(router.calls)-count, 2)
            self.assertIsNone(app.session_state['defense_session'].turns[0].answer)
            self.assertIn('retry allowance', ' '.join(item.value for item in app.error))

    def test_blocked_provider_returns_recovery_at_deadline_and_cannot_rejoin_manual_retry(self):
        from threading import Event
        blocked, release, finished = Event(), Event(), Event()
        clock = [1_000_000]
        router = SyntheticRouter()
        with patch('backend.streamlit_turns.now_ms', side_effect=lambda: clock[0]):
            app = self.connect(router)
            self.prepare(app, 4)
            button(app, 'Start defense').click().run()
            count = len(router.calls)
            def hang(body):
                if len(router.calls) == count+1:
                    clock[0] += 45_000
                    blocked.set()
                    release.wait(2)
                    finished.set()
            router.on_request = hang
            try:
                self.send(app, 'Retain this while the provider is blocked.')
                self.assertTrue(blocked.is_set())
                self.assertFalse(finished.is_set())
                self.assertIn('45-second', ' '.join(item.value for item in app.error))
                app.run()
                button(app, 'Retry saved submission').click().run()
                session = app.session_state['defense_session']
                self.assertEqual(session.turns[0].answer, 'Retain this while the provider is blocked.')
                self.assertEqual(len(session.turns), 2)
            finally:
                release.set()
                self.assertTrue(finished.wait(3))
            app.run()
            self.assertEqual(len(session.turns), 2)
            self.assertEqual(len(router.calls)-count, 3)

    def test_exhausted_question_allowance_never_resets_and_still_funds_coaching(self):
        from backend.openrouter_questions import RunQuestionPolicy
        router = SyntheticRouter()
        app = self.connect(router)
        self.prepare(app, 4)
        button(app, 'Start defense').click().run()
        router.fail_name = 'QuestionDraft'
        self.send(app)
        practice = app.session_state['research_provider']
        allowance = ProviderAllowance(practice.run_scope, practice.owner)
        policy = RunQuestionPolicy(**allowance.policy())
        allowance.reserve(policy.question_limit_nano - int(allowance.snapshot()['used']), limit=policy.question_limit_nano)
        before = allowance.snapshot()
        count = len(router.calls)
        for _ in range(2):
            button(app, 'Retry question writing').click().run()
            self.assertFalse(app.exception)
            self.assertEqual(len(router.calls), count)
            self.assertEqual(allowance.snapshot(), before)
            self.assertIn('Retrying will not reset', ' '.join(item.value for item in app.error))
        self.assertEqual(len(app.session_state['defense_session'].answered_history()), 1)
        button(app, 'End defense').click().run()
        button(app, 'Generate coaching').click().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state['research_coaching_job'].completion_status, 'ready')
        self.assertEqual(allowance.snapshot()['used'], before['used'] + 1_000_000)

    def test_preparation_exhaustion_and_unfundable_start_do_not_dispatch(self):
        router = SyntheticRouter()
        app = self.connect(router)
        self.prepare(app, 4)
        practice = app.session_state['research_provider']
        allowance = ProviderAllowance(practice.preparation_scope, practice.owner)
        allowance.reserve(int(allowance.snapshot()['remaining']))
        count = len(router.calls)
        for label in ('Prepare map again', 'Retry research map'):
            button(app, label).click().run()
            self.assertFalse(app.exception)
            self.assertEqual(len(router.calls), count)
            self.assertIsNone(app.session_state['research_plan'])
        # A separate explicitly uploaded material scope can map, but an unfundable
        # run still stops before its first planner or reviewer request.
        app.file_uploader[0].set_value([('study.md', (PAPER + 'New material.').encode(), 'text/markdown')]).run()
        self.prepare(app, 4)
        count = len(router.calls)
        with patch.dict('os.environ', {'OPENROUTER_RUN_USD': '0.000001'}):
            button(app, 'Start defense').click().run()
        self.assertFalse(app.exception)
        self.assertEqual(len(router.calls), count)
        self.assertNotIn('defense_session', app.session_state)
        self.assertIn('protected coaching reserve', ' '.join(item.value for item in app.error))

    def test_clarification_probe_and_interaction_failure_retain_typed_draft_and_original(self):
        router = SyntheticRouter()
        app = self.connect(router)
        self.prepare(app, 4)
        button(app, 'Start defense').click().run()
        router.decisions = [
            {'action': 'clarify', 'clarification': 'Explain how you will compare waiting times.', 'probe': None},
            {'action': 'probe', 'clarification': None, 'probe': {'request': 'Which comparison will you use?', 'references': []}},
        ]
        self.send(app, 'What comparison do you mean?')
        self.send(app, 'We would compare pilot waiting times.')
        session = app.session_state['defense_session']
        self.assertEqual(len(session.turns), 1)
        self.assertEqual(len(session.turns[0].clarifications), 1)
        router.fail_name = 'CombinedSubmissionDraft'
        self.send(app, 'A documented baseline period.')
        self.assertEqual(session.turns[0].answer, 'We would compare pilot waiting times.')
        self.assertIsNone(session.turns[0].probe.reply)
        self.assertEqual(next(area for area in app.text_area if area.label.startswith('Your ')).value, 'A documented baseline period.')
        self.send(app, 'A documented baseline period.')
        self.assertEqual(session.turns[0].probe.reply, 'A documented baseline period.')
        self.assertEqual(len(session.turns), 2)
        models = [body['model'] for body in router.calls if body['response_format']['json_schema']['name'] == 'CombinedSubmissionDraft']
        self.assertEqual(models, ['deepseek/deepseek-v4.1-flash-1017'] * 4)

    def test_unavailable_preparation_ledger_shows_safe_recovery_without_provider_dispatch(self):
        router = SyntheticRouter()
        app = self.connect(router)
        # A database path naming a directory is an actual storage boundary failure.
        with patch.dict('os.environ', {'DATABASE_URL': '',
                'PAYMONGO_TEST_DB_PATH': str(Path(self.files[0].name).resolve().parent)}):
            button(app, 'Prepare defense').click().run()
        self.assertFalse(app.exception)
        self.assertEqual(router.calls, [])
        self.assertIsNone(app.session_state['research_plan'])
        self.assertIn('Retry', ' '.join(item.value for item in app.error))

    def test_coaching_exhaustion_keeps_ready_cards_without_redispatch_or_new_scope(self):
        router = SyntheticRouter()
        app = self.connect(router)
        self.prepare(app, 4)
        button(app, 'Start defense').click().run()
        for _ in range(4):
            self.send(app)
        router.fail_turns = [3]
        button(app, 'Generate coaching').click().run()
        before = app.session_state['research_coaching'].answer_cards
        self.assertEqual(len(before), 3)
        practice = app.session_state['research_provider']
        allowance = ProviderAllowance(practice.run_scope, practice.owner)
        snapshot = allowance.snapshot()
        allowance.reserve(int(snapshot['remaining']), limit=snapshot['ceiling'])
        exhausted = allowance.snapshot()
        count = len(router.calls)
        for _ in range(2):
            button(app, 'Retry failed coaching sections').click().run()
            self.assertFalse(app.exception)
            self.assertEqual(len(router.calls), count)
            self.assertEqual(allowance.snapshot(), exhausted)
            self.assertEqual(app.session_state['research_coaching'].answer_cards, before)
        job = app.session_state['research_coaching_job']
        self.assertFalse(job.can_retry)
        self.assertNotEqual(job.completion_status, 'ready')
        self.assertIn('cannot fund another coaching section', ' '.join(item.value for item in app.caption))

    def test_direct_provider_key_cannot_enable_research_without_router_configuration(self):
        router = SyntheticRouter()
        app = self.connect(router)
        with patch.dict('os.environ', {'OPENROUTER_API_KEY': '', 'OPENAI_API_KEY': 'unused-old-key'}):
            app.run()
            self.assertTrue(button(app, 'Prepare defense').disabled)
            self.assertTrue(button(app, 'Start defense').disabled)
        self.assertEqual(router.calls, [])

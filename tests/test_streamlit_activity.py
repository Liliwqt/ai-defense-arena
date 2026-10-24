"""Native activity at the whole typed-App boundary, external HTTP mocked."""
from unittest.mock import patch
import unittest

import httpx
import streamlit as st
from streamlit.testing.v1 import AppTest

from tests import test_openrouter_streamlit as fixtures


class StreamlitActivityTests(unittest.TestCase):
    setUp = fixtures.IsolatedAllowanceTests.setUp
    connect = fixtures.OpenRouterFallbackTests.connect
    prepare = fixtures.OpenRouterFallbackTests.prepare
    send = fixtures.OpenRouterFallbackTests.send

    def test_manual_submission_and_writer_retries_are_named_without_marking_the_next_stage_as_retry(self):
        router = fixtures.SyntheticRouter()
        labels = []
        native_status = st.status

        def observe_status(label, **kwargs):
            labels.append(label)
            status = native_status(label, **kwargs)
            native_update = status.update
            def update(*args, **options):
                if 'label' in options:
                    labels.append(options['label'])
                return native_update(*args, **options)
            status.update = update
            return status

        with patch('streamlit.status', side_effect=observe_status):
            app = self.connect(router)
            self.prepare(app, 4)
            fixtures.button(app, 'Start defense').click().run()
            router.fail_name = 'CombinedSubmissionDraft'
            self.send(app)
            self.assertEqual(app.get('status'), [])
            app.run()
            labels.clear()
            router.fail_name = 'QuestionDraft'
            fixtures.button(app, 'Retry saved submission').click().run()
            self.assertFalse(app.exception)
            self.assertIn('Trying again… Reviewing your answer or clarification…', labels)
            self.assertIn('Answer saved. Preparing your next question…', labels)
            self.assertNotIn('Trying again… Answer saved. Preparing your next question…', labels)
            self.assertEqual(app.get('status'), [])
            labels.clear()
            fixtures.button(app, 'Retry question writing').click().run()
            self.assertFalse(app.exception)
            self.assertIn('Trying again… Answer saved. Preparing your next question…', labels)
            self.assertEqual(app.get('status'), [])
            names = [body['response_format']['json_schema']['name'] for body in router.calls]
            self.assertEqual(names.count('CombinedSubmissionDraft'), 2)
            self.assertEqual(names.count('QuestionDraft'), 3)

    def test_mapping_and_remapping_use_native_status_without_leaving_an_activity_history(self):
        router = fixtures.SyntheticRouter()
        with patch('httpx.Client', side_effect=lambda **kwargs: fixtures.HTTPClient(transport=httpx.MockTransport(router))), \
             patch('streamlit.status', wraps=st.status) as statuses:
            app = AppTest.from_file(fixtures.APP).run()
            router.app = app
            app.file_uploader[0].set_value([('study.md', fixtures.PAPER.encode(), 'text/markdown')]).run()
            self.assertEqual(router.calls, [])
            router.fail_name = 'ResearchPlanDraft'
            fixtures.button(app, 'Prepare defense').click().run()
            self.assertFalse(app.exception)
            self.assertTrue(any(call.args[0] == 'Mapping your paper…' for call in statuses.call_args_list))
            self.assertEqual(app.get('status'), [])
            self.assertEqual(len(router.calls), 1)
            fixtures.button(app, 'Retry research map').click().run()
            self.assertFalse(app.exception)
            self.assertEqual(statuses.call_args_list[-1].args[0], 'Trying again… Mapping your paper…')
            self.assertEqual(app.get('status'), [])
            self.assertEqual(len(router.calls), 2)
            fixtures.button(app, 'Prepare map again').click().run()
            self.assertFalse(app.exception)
            self.assertEqual(statuses.call_args_list[-1].args[0], 'Mapping your paper…')
            self.assertEqual(app.get('status'), [])
            self.assertEqual(len(router.calls), 3)
            self.assertIsNotNone(app.session_state['research_plan'])

    def test_complete_typed_research_uses_temporary_exchange_and_coaching_status_without_extra_requests(self):
        router = fixtures.SyntheticRouter()
        with patch('streamlit.status', wraps=st.status) as statuses:
            app = self.connect(router)
            self.prepare(app, 4)
            fixtures.button(app, 'Start defense').click().run()
            router.decisions = [
                {'action': 'clarify', 'clarification': 'Explain the pilot boundary.'},
                {'action': 'answer'},
                {'action': 'probe', 'probe': {'request': 'Which source supports it?', 'references': []}},
                {'action': 'clarify', 'clarification': 'Name the source in the paper.'},
                {'action': 'answer'}, {'action': 'answer'}, {'action': 'answer'}]
            for text in ('Explain that?', 'We limit our claim to the pilot.', 'We compare the pilot.',
                         'What source?', 'The planned pilot record.', 'We protect the participants.', 'We will state the limitation.'):
                self.send(app, text)
                self.assertEqual(app.get('status'), [])
            self.assertTrue(app.session_state['defense_session'].completed)
            fixtures.button(app, 'Generate coaching').click().run()
            self.assertFalse(app.exception)
            self.assertEqual(app.session_state['research_coaching_job'].completion_status, 'ready')
            self.assertEqual(len(app.session_state['research_coaching'].answer_cards), 4)
            labels = [call.args[0] for call in statuses.call_args_list]
            self.assertIn('Reviewing your answer or clarification…', labels)
            self.assertIn('Reviewing your probe reply or clarification…', labels)
            self.assertIn('Preparing your coaching overview…', labels)
            self.assertIn('Preparing your answer coaching…', labels)
            self.assertIn('Saving your coaching…', labels)
            self.assertEqual(app.get('status'), [])
            names = [body['response_format']['json_schema']['name'] for body in router.calls]
            self.assertEqual(names.count('ResearchPlanDraft'), 1)
            self.assertEqual(names.count('QuestionDraft'), 4)
            self.assertEqual(names.count('CombinedSubmissionDraft'), 7)
            self.assertEqual(sum('CoachingDraft' in name for name in names), 3)

    def test_free_mixed_partial_coaching_failure_clears_activity_and_retries_only_the_failed_section(self):
        self.enterContext(patch.dict('os.environ', {'OPENROUTER_FREE_PER_MINUTE': '1000',
            'OPENROUTER_FREE_DAILY_REQUESTS': '1000', 'OPENROUTER_FREE_OWNER_DAILY_REQUESTS': '1000'}))
        router = fixtures.SyntheticRouter(mixed=True)
        router.usage = {'cost': 0}
        with patch('streamlit.status', wraps=st.status) as statuses:
            app = self.connect(router)
            next(box for box in app.selectbox if box.label == 'Practice tier').select('Free practice').run()
            self.prepare(app, 4)
            fixtures.button(app, 'Start defense').click().run()
            for _ in range(4): self.send(app)
            router.fail_turns = [3]
            fixtures.button(app, 'Generate coaching').click().run()
            self.assertFalse(app.exception)
            self.assertEqual(app.get('status'), [])
            self.assertEqual(app.session_state['research_coaching_job'].snapshot()['cards_ready'], 3)
            before = app.session_state['research_coaching'].answer_cards
            fixtures.button(app, 'Retry failed coaching sections').click().run()
            self.assertFalse(app.exception)
            self.assertEqual(app.get('status'), [])
            self.assertEqual(app.session_state['research_coaching_job'].completion_status, 'ready')
            self.assertEqual(app.session_state['research_coaching'].answer_cards[:3], before)
            self.assertIn('Trying again… Preparing your answer coaching…', [call.args[0] for call in statuses.call_args_list])
            names = [body['response_format']['json_schema']['name'] for body in router.calls]
            self.assertEqual(sum('CoachingDraft' in name for name in names), 4)

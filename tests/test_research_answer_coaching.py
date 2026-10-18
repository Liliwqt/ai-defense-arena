"""Public research report contracts with structured model output mocked."""
import unittest
from types import SimpleNamespace
from backend.project_files import ProjectFile
from backend.question_generator import AnsweredQuestion, PanelistProbe, GroundedQuestion, generate_coaching_report, QuestionGenerationError
from tests.test_research_coverage import Client


from tests.research_coaching_fixtures import cards_for


def draft_for(history, **changes):
    return SimpleNamespace(summary='The team discussed the campus pilot.', strengths=[], improvements=[],
        next_step='Practice the supported explanation.',closing='',answer_cards=cards_for(history),**changes)


class ResearchAnswerCoachingTests(unittest.TestCase):
    def setUp(self):
        self.files=[ProjectFile('paper.md','The proposal describes a campus pilot.','research_text')]
        self.history=[AnsweredQuestion('Methodology Reviewer','Why this scope?','We will limit the claim.',speaker_name='Alex',
            citation=GroundedQuestion('Why this scope?','paper.md',1,'The proposal describes a campus pilot.'),
            probe=PanelistProbe('probe-one','Which scope?',status='answered',reply='The campus pilot.',speaker_name='Sam',speaker_seat=1)),
            AnsweredQuestion('Ethics Reviewer','How will consent work?',None,timed_out=True)]

    def test_complete_report_preserves_originals_and_separate_speakers_for_each_recorded_turn(self):
        client=Client(draft_for(self.history))
        report=generate_coaching_report(self.files,self.history,'offline-key',client=client,defense_type='research')
        self.assertEqual(len(report.answer_cards),2)
        card=report.answer_cards[0]
        self.assertEqual(card['original_answer'],'We will limit the claim.')
        self.assertEqual(card['speaker_name'],'Alex')
        self.assertEqual(card['probe']['speaker_name'],'Sam')
        self.assertEqual(card['probe']['reply'],'The campus pilot.')
        self.assertEqual(card['feedback']['stronger_answer'],'We will limit our claim to the campus pilot.')
        self.assertIsNone(report.answer_cards[1]['original_answer'])
        self.assertEqual(report.answer_cards[1]['feedback']['strengths'],[])
        self.assertIsNone(report.answer_cards[1]['feedback']['stronger_answer'])
        system=client.calls[0]['input'][0]['content']
        self.assertIn('conditional scaffold',system)
        self.assertIn('audio measurements',system)

    def test_missing_duplicate_unknown_or_fabricated_cards_fail_recoverably(self):
        import copy
        from tests.research_coaching_fixtures import cards_for
        valid=cards_for(self.history)
        cases=[valid[:1],valid+[valid[0]],[valid[0],valid[0]],[{**valid[0],'turn':2},valid[1]],
               [{**valid[0],'original_answer':'Rewritten original'},valid[1]]]
        for cards in cases:
            with self.subTest(cards=cards),self.assertRaises(QuestionGenerationError):
                draft=draft_for(self.history);draft.answer_cards=copy.deepcopy(cards)
                generate_coaching_report(self.files,self.history,'offline-key',client=Client(draft),defense_type='research')

    def test_missed_strengths_fabricated_fillers_and_missing_probe_feedback_are_rejected(self):
        for change in ('missed-strength','filler','missing-reply','oversized','fake-measure'):
            draft=draft_for(self.history)
            if change=='missed-strength':draft.answer_cards[1]['feedback']['strengths']=['An invented good answer.']
            if change=='filler':draft.answer_cards[0]['feedback']['wording_examples']=['uhm']
            if change=='missing-reply':draft.answer_cards[0]['probe_feedback']=None
            if change=='oversized':draft.answer_cards[0]['feedback']['stronger_answer']='x'*1801
            if change=='fake-measure':draft.answer_cards[0]['feedback']['speaking_rate']=120
            with self.subTest(change=change),self.assertRaises(QuestionGenerationError):
                generate_coaching_report(self.files,self.history,'offline-key',client=Client(draft),defense_type='mixed')

    def test_long_report_is_rejected_before_a_model_request_and_empty_session_is_factual(self):
        client=Client(draft_for(self.history))
        with self.assertRaises(QuestionGenerationError):
            generate_coaching_report(self.files,self.history*7,'offline-key',client=client,defense_type='research')
        self.assertEqual(client.calls,[])
        report=generate_coaching_report(self.files,[],None,client=client,defense_type='research')
        self.assertEqual(report.answer_cards,[])
        self.assertEqual(client.calls,[])

    def test_observed_words_and_conditional_practice_preserve_original_and_profile_context(self):
        draft=draft_for(self.history)
        draft.answer_cards.reverse()
        draft.answer_cards[1]['feedback'].update(wording_examples=['limit the claim'],wording_basis='conditional',
            stronger_answer='If supported by the paper, explain [the reason for this scope].')
        client=Client(draft)
        report=generate_coaching_report(self.files,self.history,'offline-key',client=client,defense_type='research',
            research_stage='proposal',research_context={'profile':{'fields':['Education'],'approaches':['qualitative'],'setting':'Campus'}})
        self.assertEqual(report.answer_cards[0]['turn'],0)
        self.assertEqual(report.answer_cards[0]['feedback']['wording_basis'],'conditional')
        self.assertEqual(self.history[0].answer,'We will limit the claim.')
        self.assertIn('Education',client.calls[0]['input'][1]['content'])


class ResearchCoachingProtocolTests(unittest.TestCase):
    from tests import test_research_coverage as coverage
    from tests import test_opening_history_protocol as opening
    setUp=coverage.CoverageProtocolTests.setUp
    until=coverage.CoverageProtocolTests.until
    start_opening=opening.OpeningHistoryProtocolTests.start_opening

    def test_incomplete_report_fails_before_ready_then_host_can_retry_complete_membership(self):
        from unittest.mock import patch
        from backend import game_server
        from backend.question_generator import CoachingReport
        from backend.rooms.commands import CatchUpDeadline
        from tests import test_research_coverage as coverage
        from tests.research_coaching_fixtures import with_cards
        calls=[]
        def coach(files,history,*args,**kwargs):
            calls.append(history)
            report=CoachingReport('The team discussed scope.',[],[],'Practice the missing detail.')
            return report if len(calls)==1 else with_cards(report,history)
        def check(socket,state):
            socket.send_json({'type':'cast_vote','seat':0});self.until(socket,'voting')
            self.now=state['vote_deadline_ms']
            self.client.portal.call(game_server._coordinator(game_server.rooms[state['room_code']]).execute,CatchUpDeadline())
            self.until(socket,'question')
            socket.send_json({'type':'submit_direct_answer','turn':0,'answer':'We limit the claim to the campus.'})
            self.until(socket,'voting')
            socket.send_json({'type':'end_defense'})
            failed=self.until(socket,'complete',feedback_status='failed')
            self.assertIsNone(failed['feedback'])
            self.assertIsNone(failed['closing_deadline_ms'])
            socket.send_json({'type':'retry_coaching'})
            ready=self.until(socket,'complete',feedback_status='ready')
            self.assertEqual(len(ready['feedback']['answer_cards']),2)
            self.assertEqual(ready['feedback']['answer_cards'][0]['original_answer'],'We limit the claim to the campus.')
            self.assertIsNone(ready['feedback']['answer_cards'][1]['original_answer'])
            self.assertEqual(len(calls),2)
        with patch('backend.rooms.coaching.generate_coaching_report',side_effect=coach):
            self.start_opening(coverage.mocked_move,on_state=check)


class ResearchCoachingFallbackTests(unittest.TestCase):
    def test_typed_fallback_preserves_originals_and_selects_answer_practice_without_new_ai(self):
        from pathlib import Path
        from unittest.mock import patch
        from streamlit.testing.v1 import AppTest
        from backend.defense_session import ResearchDefenseSession
        from backend.question_generator import CoachingReport
        from tests import test_research_coverage as coverage
        from tests.research_coaching_fixtures import with_cards
        session=ResearchDefenseSession.create(coverage.plan(4),4,'research','proposal')
        for _ in range(4):
            session.apply_move(coverage.mocked_move(coverage.FILES,None,history=session.answered_history(),context=session.context()))
            session.submit_answer('We limit the claim to the campus.',speaker_name='Alex')
        if not session.completed:
            session.apply_move(coverage.mocked_move(coverage.FILES,None,history=session.answered_history(),context=session.context()))
        self.assertTrue(session.completed)
        report=with_cards(CoachingReport('The team explained scope.',[],[],'Practice the source.'),session.coaching_history())
        with patch('backend.question_generator.generate_coaching_report') as coach:
            app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/'backend/app.py')).run()
            app.selectbox[0].select('Research paper').run()
            app.file_uploader[0].set_value([('paper.md',coverage.PAPER.encode(),'text/markdown')]).run()
            app.session_state['defense_session']=session
            app.session_state['research_coaching']=report
            app.run()
            self.assertFalse(app.exception)
            selector=next(box for box in app.selectbox if box.label=='Review a question')
            self.assertIn('We limit the claim to the campus.',[m.value for m in app.markdown])
            selector.select(1).run()
            self.assertFalse(app.exception)
            self.assertIn('Practice task',[m.value for m in app.markdown])
            coach.assert_not_called()

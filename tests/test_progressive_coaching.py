"""Progressive research reports through provider, room and ledger boundaries."""
import unittest
from types import SimpleNamespace
from backend.question_generator import AnsweredQuestion, CoachingDraft, generate_coaching_report
from backend.project_files import ProjectFile
from tests.test_research_coverage import Client
from tests.research_coaching_fixtures import cards_for


class ProgressiveReportContractTests(unittest.TestCase):
    def test_overview_and_bounded_sections_use_stable_global_question_indices(self):
        history=[AnsweredQuestion('Methodology Reviewer',f'Question {i+1}?','We limit our claim.',speaker_name='Alex') for i in range(15)]
        files=[ProjectFile('paper.md','The proposal describes a campus pilot.','research_text')]
        overview=CoachingDraft(summary='The team explained the scope.',strengths=[],improvements=[],next_step='Practice the limitations.',closing='Review those limitations before the next practice.')
        client=Client(overview)
        report=generate_coaching_report(files,history,'offline-key',client=client,defense_type='research',overview_only=True)
        self.assertIsNone(report.answer_cards)
        self.assertEqual(len(client.calls),1)
        section=SimpleNamespace(**overview.model_dump(),answer_cards=cards_for(history)[12:15])
        report=generate_coaching_report(files,history,'offline-key',client=Client(section),defense_type='research',section_turns=(12,13,14))
        self.assertEqual([card['turn'] for card in report.answer_cards],[12,13,14])
        self.assertEqual(report.answer_cards[0]['question'],'Question 13?')


class ProgressiveRoomTests(unittest.IsolatedAsyncioTestCase):
    async def test_ready_sections_survive_failure_and_retry_without_replaying_closing(self):
        import asyncio
        from dataclasses import replace
        from backend.rooms.coordinator import RoomCoordinator,RoomWorkflows
        from backend.rooms.commands import GenerateCoaching,RetryCoaching,CatchUpDeadline,VerifiedActor
        from backend.question_generator import CoachingReport,GroundedQuestion
        from backend.defense_session import ResearchDefenseSession,DefenseTurn
        from tests.offline_accounts import authenticate
        from tests.test_planning_coaching_coordination import completed_room
        from tests.test_research_coverage import plan
        from tests.research_coaching_fixtures import with_cards
        account=authenticate(self);room=completed_room(account)
        room.defense_type='research';session=ResearchDefenseSession.create(plan(4),8,'research','proposal')
        session.turns=[DefenseTurn('Methodology Reviewer',GroundedQuestion(f'Question {i+1}?','paper.md',1,'Campus pilot.'),answer='We limit our claim.',speaker_name='Sam',topic_id='topic-1') for i in range(7)]
        session.end();room.defense=session
        now=[1000];calls=[];failed=asyncio.Event();ready=asyncio.Event()
        async def coach(request):
            if request.overview_only:
                calls.append('overview')
                return CoachingReport('The team discussed scope.',[],[],'Practice the remaining detail.',closing='Review the limits before the next defense.')
            calls.append(request.section_turns)
            if request.section_turns==(3,4,5) and calls.count((3,4,5))==1:raise ValueError('Synthetic section failure')
            report=with_cards(CoachingReport('The team discussed scope.',[],[],'Practice.'),request.history)
            return replace(report,answer_cards=[c for c in report.answer_cards if c['turn'] in request.section_turns])
        async def deliver(socket,payload):
            if payload['state']['feedback_status']=='failed':failed.set()
            if payload['state']['feedback_status']=='ready':ready.set()
        owner=RoomCoordinator(room,RoomWorkflows(coaching_request=coach,deliver=deliver,now=lambda:now[0]))
        self.addAsyncCleanup(owner.shutdown)
        await owner.execute(GenerateCoaching(1));await asyncio.wait_for(failed.wait(),2)
        view=owner.view(VerifiedActor('host',account['id']))
        self.assertEqual(view['coaching_progress']['cards_ready'],4)
        self.assertEqual(view['coaching_progress']['cards_required'],7)
        self.assertIsNone(view['expires_at_ms'])
        preserved=view['feedback']['answer_cards']
        closing_deadline=view['closing_deadline_ms'];self.assertIsNotNone(closing_deadline)
        now[0]=closing_deadline+1;await owner.execute(CatchUpDeadline())
        self.assertTrue((await owner.execute(RetryCoaching(),VerifiedActor('host',account['id']))).accepted)
        await asyncio.wait_for(ready.wait(),2)
        final=owner.view(VerifiedActor('host',account['id']))
        self.assertEqual(calls,['overview',(0,1,2),(3,4,5),(6,),(3,4,5)])
        self.assertIsNone(final['closing_deadline_ms'])
        self.assertEqual(final['coaching_progress']['completion_status'],'ready')
        self.assertEqual([c for c in final['feedback']['answer_cards'] if c['turn'] in {0,1,2,6}],preserved)


class ProgressiveRecoveryTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        import os
        from unittest.mock import patch
        from tests.offline_accounts import authenticate
        from backend.live_store import LiveStore
        from tests.test_planning_coaching_coordination import completed_room
        from backend.defense_session import ResearchDefenseSession, DefenseTurn
        from backend.question_generator import GroundedQuestion
        from tests.test_research_coverage import plan
        self.account=authenticate(self)
        env=patch.dict(os.environ,{'LIVE_PAID_STARTS_ENABLED':'1','PAYMENTS_MODE':'live','FREE_ACCESS_VOUCHER':'','LIVE_TOPUP_INVITED_EMAILS':'host@example.test'})
        env.start();self.addCleanup(env.stop)
        self.store=LiveStore();self.store.start_service('progressive-service')
        row,_=self.store.begin_topup(self.account['id'],'credits-10','offline-progressive-topup')
        self.store.bind_topup_intent(row['id'],'pi_progressive');self.store.register_topup(row['id'],'pi_progressive','offline',1)
        self.store.record_topup_paid(row['id'],'pi_progressive',['pay_progressive'],100,'PHP')
        self.room=completed_room(self.account,run_id='progressive-run');self.room.defense_type='research'
        self.store.reserve_run(self.account['id'],self.room.run_id,'progressive-service',self.room.code)
        self.store.charge_run(self.account['id'],self.room.run_id);self.store.service_state(self.room.run_id,'coaching')
        self.room.defense=ResearchDefenseSession.create(plan(4),100,'research','proposal')
        self.room.defense.turns=[DefenseTurn('Methodology Reviewer',GroundedQuestion(f'Question {i+1}?','paper.md',1,'Campus pilot.'),answer='We limit our claim.',speaker_name='Sam',topic_id='topic-1') for i in range(7)]
        self.room.defense.end()
        from backend.rooms.commands import VerifiedActor
        self.actor=VerifiedActor('host',self.account['id'])

    def report(self,request):
        from backend.question_generator import CoachingReport
        from tests.research_coaching_fixtures import with_cards
        return with_cards(CoachingReport('The team discussed scope.',[],[],'Practice the limits.',closing='Review those limits before your next defense.'),request.history,
            overview_only=request.overview_only,section_turns=request.section_turns)

    async def owner(self,coach):
        from backend.rooms.coordinator import RoomCoordinator,RoomWorkflows
        async def deliver(socket,payload):pass
        owner=RoomCoordinator(self.room,RoomWorkflows(coaching_request=coach,now=lambda:1000,deliver=deliver))
        self.addAsyncCleanup(owner.shutdown)
        return owner

    async def wait_status(self,owner,status):
        from tests.async_room import wait_until
        await wait_until(lambda:owner.view(self.actor)['feedback_status']==status)
        return owner.view(self.actor)

    async def test_completion_write_retry_keeps_every_card_and_never_regenerates_or_replays_closing(self):
        from unittest.mock import patch
        from backend.live_store import LiveStore
        from backend.rooms.commands import GenerateCoaching,RetryCoaching
        calls=[];writes=[];original=LiveStore.finish_run
        async def coach(request):calls.append(request.section_turns);return self.report(request)
        def finish(store,run,outcome):
            writes.append(outcome)
            if len(writes)==1:raise RuntimeError('Synthetic unavailable completion write')
            return original(store,run,outcome)
        owner=await self.owner(coach)
        with patch.object(LiveStore,'finish_run',finish):
            await owner.execute(GenerateCoaching(1));failed=await self.wait_status(owner,'failed')
            self.assertEqual(failed['coaching_progress']['cards_ready'],7)
            self.assertEqual(failed['coaching_progress']['completion_status'],'failed')
            self.assertIsNone(failed['expires_at_ms']);self.assertIsNotNone(self.store.overview(self.account['id'])['active_run'])
            self.assertEqual(self.store.overview(self.account['id'])['live_credits'],0)
            self.assertTrue((await owner.execute(RetryCoaching(),self.actor)).accepted)
            ready=await self.wait_status(owner,'ready')
        self.assertEqual(calls,[None,(0,1,2),(3,4,5),(6,)])
        self.assertEqual(writes,['completed','completed'])
        self.assertEqual(ready['feedback'],failed['feedback'])
        self.assertEqual(ready['closing_deadline_ms'],failed['closing_deadline_ms'])
        view=self.store.overview(self.account['id']);self.assertIsNone(view['active_run']);self.assertEqual(view['live_credits'],0)
        self.assertEqual(view['live_runs'][0]['outcome'],'completed')

    async def test_paid_return_fences_provider_that_delivers_success_after_cancellation(self):
        import asyncio
        from backend.rooms.commands import GenerateCoaching,RetryCoaching,EndUnavailable
        calls=[];started=asyncio.Event();release=asyncio.Event();late=asyncio.Event()
        self.addCleanup(release.set)
        async def coach(request):
            calls.append(request.section_turns)
            if request.section_turns==(3,4,5):
                if calls.count((3,4,5))==1:raise ValueError('Synthetic section error')
                started.set()
                while not release.is_set():
                    try:await release.wait()
                    except asyncio.CancelledError:pass
                late.set()
            return self.report(request)
        owner=await self.owner(coach)
        await owner.execute(GenerateCoaching(1));failed=await self.wait_status(owner,'failed')
        preserved=failed['feedback'];self.assertEqual(failed['coaching_progress']['cards_ready'],4)
        self.assertTrue((await owner.execute(RetryCoaching(),self.actor)).accepted)
        await asyncio.wait_for(started.wait(),2)
        self.assertTrue((await owner.execute(EndUnavailable(),self.actor)).accepted)
        self.assertTrue((await owner.execute(EndUnavailable(),self.actor)).accepted)
        release.set();await asyncio.wait_for(late.wait(),2);await asyncio.sleep(0)
        final=owner.view(self.actor)
        self.assertEqual(final['feedback'],preserved)
        self.assertEqual(final['coaching_progress']['completion_status'],'returned')
        self.assertEqual(final['feedback_status'],'none')
        view=self.store.overview(self.account['id']);self.assertEqual(view['live_credits'],10)
        self.assertIsNone(view['active_run']);self.assertEqual(view['live_runs'][0]['outcome'],'ended_unavailable')
        self.assertEqual(self.store.finish_run(self.room.run_id,'completed'),'ended_unavailable')
        self.assertEqual(self.store.overview(self.account['id'])['live_credits'],10)

    async def test_hundred_question_report_is_admitted_sequentially_and_duplicate_command_does_not_regenerate(self):
        import asyncio
        from copy import deepcopy
        from backend.rooms.commands import GenerateCoaching
        # The supported budget is 100, including a final one-card section.
        template=self.room.defense.turns[0]
        self.room.defense.turns=[deepcopy(template) for _ in range(100)]
        calls=[];active=0;peak=0
        async def coach(request):
            nonlocal active,peak
            active+=1;peak=max(peak,active);calls.append(request.section_turns)
            await asyncio.sleep(0)
            result=self.report(request);active-=1;return result
        owner=await self.owner(coach)
        await asyncio.gather(owner.execute(GenerateCoaching(1)),owner.execute(GenerateCoaching(1)))
        ready=await self.wait_status(owner,'ready')
        self.assertEqual(len(calls),35);self.assertEqual(peak,1)
        self.assertEqual(calls[-1],(99,));self.assertEqual(ready['coaching_progress']['cards_ready'],100)
        self.assertEqual([c['turn'] for c in ready['feedback']['answer_cards']],list(range(100)))

    async def test_exhausted_section_attempts_preserve_ready_cards_and_do_not_mint_free_credits(self):
        import os
        from unittest.mock import patch
        from backend.rooms.commands import GenerateCoaching,RetryCoaching,EndUnavailable
        # Replace the unopened paid fixture with voucher-funded access via the same public store.
        self.store.finish_run(self.room.run_id,'ended')
        self.room.run_id='voucher-progressive-run'
        with patch.dict(os.environ,{'FREE_ACCESS_VOUCHER':'offline-shareable-voucher'}):
            self.store.reserve_run(self.account['id'],self.room.run_id,'progressive-service',self.room.code)
            self.store.charge_run(self.account['id'],self.room.run_id)
        calls=[]
        async def coach(request):
            calls.append(request.section_turns)
            if request.section_turns==(3,4,5):raise ValueError('Synthetic section failure')
            return self.report(request)
        owner=await self.owner(coach)
        await owner.execute(GenerateCoaching(1));initial=await self.wait_status(owner,'failed')
        for _ in range(2):
            self.assertTrue((await owner.execute(RetryCoaching(),self.actor)).accepted)
            await self.wait_status(owner,'failed')
        self.assertFalse(owner.view(self.actor)['coaching_progress']['can_retry'])
        self.assertFalse((await owner.execute(RetryCoaching(),self.actor)).accepted)
        self.assertEqual(owner.view(self.actor)['feedback'],initial['feedback'])
        self.assertEqual(calls.count((0,1,2)),1);self.assertEqual(calls.count((3,4,5)),3)
        self.assertTrue((await owner.execute(EndUnavailable(),self.actor)).accepted)
        view=self.store.overview(self.account['id']);self.assertEqual(view['live_credits'],0)
        self.assertEqual(view['live_runs'][0]['cost'],0)


    async def test_service_restart_returns_unfinished_paid_run_and_fences_old_last_section(self):
        import asyncio
        from backend.rooms.commands import GenerateCoaching
        started,release,finished=asyncio.Event(),asyncio.Event(),asyncio.Event()
        async def coach(request):
            if request.section_turns==(6,):
                started.set()
                while not release.is_set():
                    try:await release.wait()
                    except asyncio.CancelledError:pass
                finished.set()
            return self.report(request)
        owner=await self.owner(coach)
        self.addCleanup(release.set)
        await owner.execute(GenerateCoaching(1));await asyncio.wait_for(started.wait(),2)
        before=owner.view(self.actor)['feedback']
        self.assertEqual(len(before['answer_cards']),6)
        await owner.shutdown()
        self.store.stop_service('progressive-service');self.store.start_service('replacement-service')
        release.set();await asyncio.wait_for(finished.wait(),2);await asyncio.sleep(0)
        view=self.store.overview(self.account['id'])
        self.assertEqual(view['live_credits'],10);self.assertIsNone(view['active_run'])
        self.assertEqual(owner.view(self.actor)['feedback'],before)
        self.assertNotEqual(owner.view(self.actor)['coaching_progress']['completion_status'],'ready')


class ProgressiveFallbackTests(unittest.TestCase):
    def setUp(self):
        from tests.offline_accounts import fallback
        fallback(self)

    def test_typed_fallback_preserves_ready_sections_and_retries_failed_membership_only(self):
        import os
        from pathlib import Path
        from unittest.mock import patch
        from streamlit.testing.v1 import AppTest
        from backend.defense_session import ResearchDefenseSession, DefenseTurn
        from backend.question_generator import CoachingReport, GroundedQuestion
        from tests.test_research_coverage import plan,PAPER
        from tests.research_coaching_fixtures import with_cards,scope_options
        session=ResearchDefenseSession.create(plan(4),8,'research','proposal')
        session.turns=[DefenseTurn('Methodology Reviewer',GroundedQuestion(f'Question {i+1}?','paper.md',1,'Campus pilot.'),answer='We limit our claim.',speaker_name='Sam',topic_id='topic-1') for i in range(7)]
        session.end();calls=[]
        def coach(files,history,*args,**kwargs):
            key=kwargs.get('section_turns');calls.append(key)
            if key==(3,4,5) and calls.count(key)==1:raise ValueError('Synthetic failure')
            return with_cards(CoachingReport('The team discussed scope.',[],[],'Practice the limits.'),history,**scope_options(kwargs))
        with patch.dict(os.environ,{'OPENAI_API_KEY':'offline-key'}),patch('backend.question_generator.generate_coaching_report',side_effect=coach):
            app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/'backend/app.py')).run()
            app.file_uploader[0].set_value([('paper.md',PAPER.encode(),'text/markdown')]).run()
            from backend.project_files import ProjectFile
            # A retained report belongs to an already funded run. Rendering
            # Results must never establish a replacement provider allowance.
            app.session_state['research_provider'].client(session,
                [ProjectFile('paper.md', PAPER, 'research_text')])
            app.session_state['defense_session']=session;app.run()
            next(b for b in app.button if b.label=='Generate coaching').click().run()
            self.assertFalse(app.exception)
            self.assertIn('4 of 7 answers coached',[item.value for item in app.caption])
            before=app.session_state['research_coaching'].answer_cards
            next(b for b in app.button if b.label=='Retry failed coaching sections').click().run()
            self.assertFalse(app.exception)
            self.assertIn('7 of 7 answers coached',[item.value for item in app.caption])
            report=app.session_state['research_coaching']
            self.assertEqual([c for c in report.answer_cards if c['turn'] in {0,1,2,6}],before)
            self.assertEqual(calls,[None,(0,1,2),(3,4,5),(6,),(3,4,5)])

"""Retained stages through public funded clients, room protocol and typed fallback."""
from pathlib import Path
import unittest
from unittest.mock import patch

import httpx
from streamlit.testing.v1 import AppTest

from backend.provider_allowance import ProviderAllowance
from tests import test_openrouter_streamlit as fallback
from tests import test_research_plan as maps
from tests.test_openrouter_questions import IsolatedAllowanceTests
from tests.test_research_plan import PAPER

HTTPClient = httpx.Client
APP = str(Path(__file__).resolve().parents[1] / 'backend/app.py')


class DuplicateWriterRouter(fallback.SyntheticRouter):
    """Return one grounded but repeated writer output after an accepted answer."""
    duplicate_next = False

    def __call__(self, request):
        import json
        response = super().__call__(request)
        name = json.loads(request.content)['response_format']['json_schema']['name']
        if self.duplicate_next and name == 'QuestionDraft':
            self.duplicate_next = False
            return httpx.Response(response.status_code, text=response.text.replace('decision 2?', 'decision 1?'))
        return response


class FallbackTurnRecoveryTests(IsolatedAllowanceTests):
    def test_failed_question_writing_retries_only_writer_and_retains_answer_and_hold(self):
        self._writer_recovery(duplicate=False)

    def test_grounded_duplicate_question_retries_only_writer(self):
        self._writer_recovery(duplicate=True)

    def _writer_recovery(self, *, duplicate):
        router = DuplicateWriterRouter()
        with patch('httpx.Client', side_effect=lambda **kw: HTTPClient(transport=httpx.MockTransport(router))):
            app = AppTest.from_file(APP).run()
            router.app = app
            app.file_uploader[0].set_value([('study.md', PAPER.encode(), 'text/markdown')]).run()
            fallback.button(app, 'Prepare defense').click().run()
            app.number_input[0].set_value(4).run()
            next(box for box in app.checkbox if box.label == 'I reviewed the research profile').check().run()
            fallback.button(app, 'Confirm profile and budget').click().run()
            fallback.button(app, 'Start defense').click().run()
            practice = app.session_state['research_provider']
            scope = practice.run_scope
            if duplicate:
                router.duplicate_next = True
            else:
                router.fail_name = 'QuestionDraft'
            next(area for area in app.text_area if area.label.startswith('Your ')).set_value('A bounded campus pilot.')
            fallback.button(app, 'Send to panelist').click().run()
            self.assertFalse(app.exception)
            self.assertEqual(app.session_state['defense_session'].turns[0].answer, 'A bounded campus pilot.')
            self.assertTrue(app.session_state['defense_session'].needs_question)
            count = len(router.calls)
            before = ProviderAllowance(scope, practice.owner).snapshot()['used']
            # The existing action is the recovery seam, independent of its eventual label.
            next(b for b in app.button if b.label.startswith('Retry ') and 'question' in b.label.lower()).click().run()
            self.assertFalse(app.exception)
            added = router.calls[count:]
            self.assertEqual([body['response_format']['json_schema']['name'] for body in added], ['QuestionDraft'])
            self.assertEqual(app.session_state['defense_session'].turns[0].answer, 'A bounded campus pilot.')
            self.assertEqual(practice.run_scope, scope)
            self.assertEqual(ProviderAllowance(scope, practice.owner).snapshot()['used'], before + 500_000)


class FundedPlanRecoveryTests(IsolatedAllowanceTests):
    def setUp(self):
        super().setUp()
        from backend.turn_recovery import QuestionPlanRecovery
        self.recovery = QuestionPlanRecovery()
        self.router = fallback.SyntheticRouter()
        patcher = patch('httpx.Client', side_effect=lambda **kw: HTTPClient(transport=httpx.MockTransport(self.router)))
        patcher.start()
        self.addCleanup(patcher.stop)

    def move(self, *, files=None, session=None, scope='run:retained', namespace='room:prepared:run', tier='standard'):
        from backend.openrouter_questions import RunQuestionClient, establish_run_allowance
        files = files if files is not None else self.files
        session = session if session is not None else self.session
        establish_run_allowance(scope, 'owner', files, session.question_budget, tier=tier)
        client = RunQuestionClient(scope, 'owner', session, files,
                                   recovery=self.recovery.claim(namespace))
        return client.research_move(files, history=session.answered_history(), context=session.context(),
                                    defense_type='research', research_stage='proposal')

    def test_unchanged_detached_inputs_keep_plan_but_changed_sources_or_preparation_replan(self):
        from copy import deepcopy
        from backend.project_files import ProjectFile
        from backend.question_generator import QuestionGenerationError
        for change in ('unchanged', 'source', 'preparation', 'context', 'run'):
            with self.subTest(change=change):
                self.recovery.invalidate()
                self.router.fail_name = 'QuestionDraft'
                with self.assertRaises(QuestionGenerationError):
                    self.move()
                count = len(self.router.calls)
                options = {'session': deepcopy(self.session)}
                if change == 'source': options['files'] = [ProjectFile('study.md', PAPER+'Additional accepted detail.\n', 'research_text')]
                if change == 'preparation': options['namespace'] = 'room:new-preparation:run'
                if change == 'context': options['session'].question_budget = 5
                if change == 'run': options['scope'] = 'run:new'
                result = self.move(**options)
                self.assertEqual(result.question.filename, 'study.md')
                names = [body['response_format']['json_schema']['name'] for body in self.router.calls[count:]]
                self.assertEqual(names, ['QuestionDraft'] if change == 'unchanged' else ['PlanDraft', 'QuestionDraft'])

    def test_invalid_planner_choice_is_not_retained_for_writing(self):
        from backend.question_generator import QuestionGenerationError
        original = self.router.__call__
        invalid = [True]
        from tests.test_openrouter_questions import stream_response, planner_move, ETHICS
        def provider(request):
            if invalid[0]:
                invalid[0] = False
                return stream_response(planner_move(ETHICS, 'topic-2'))
            return original(request)
        with patch('httpx.Client', side_effect=lambda **kw: HTTPClient(transport=httpx.MockTransport(provider))):
            with self.assertRaises(QuestionGenerationError): self.move()
            result = self.move()
        self.assertEqual(result.panelist, 'Methodology Reviewer')
        self.assertEqual([b['response_format']['json_schema']['name'] for b in self.router.calls],
                         ['PlanDraft', 'QuestionDraft'])

    def test_late_planner_cannot_restore_a_revoked_claim(self):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Event
        from backend.question_generator import QuestionGenerationError
        started, release = Event(), Event()
        original = self.router.__call__
        first = [True]
        def provider(request):
            if first[0]:
                first[0] = False
                started.set()
                if not release.wait(2): raise AssertionError('Synthetic response was not released')
            return original(request)
        with patch('httpx.Client', side_effect=lambda **kw: HTTPClient(transport=httpx.MockTransport(provider))), \
             ThreadPoolExecutor(max_workers=1) as pool:
            old = pool.submit(self.move)
            self.assertTrue(started.wait(2))
            self.recovery.invalidate(keep_plan=True)
            release.set()
            with self.assertRaises(QuestionGenerationError): old.result(timeout=2)
            count = len(self.router.calls)
            self.move()
        self.assertEqual([b['response_format']['json_schema']['name'] for b in self.router.calls[count:]],
                         ['PlanDraft', 'QuestionDraft'])


class RoomTurnRecoveryTests(unittest.TestCase):
    setUp = maps.ResearchPlanRoomTests.setUp
    def create(self, mode="research", tier="standard"):
        files = [("research_files", ("study.md", PAPER.encode(), "text/markdown"))]
        if mode == "mixed": files.append(("files", ("queue.py", b"queue = []", "text/x-python")))
        result = self.client.post("/api/rooms", data={"host_name": "Host", "defense_type": mode,
                                  "research_stage": "proposal", "practice_tier": tier}, files=files)
        self.assertEqual(result.status_code, 201, result.text)
        return result.json()
    hello = maps.ResearchPlanRoomTests.hello

    def until(self, socket, **conditions):
        for _ in range(50):
            event = socket.receive_json()
            if event['type'] == 'error':
                continue  # Duplicate/unauthorized recovery is an expected rejection.
            state = event['state']
            if all(state.get(key) == value for key, value in conditions.items()): return state
        self.fail('Expected recovery state not received')

    def provider(self, *, free=False):
        import json
        router = DuplicateWriterRouter()
        failed_writer = [False]
        def respond(request):
            body = json.loads(request.content)
            if failed_writer[0] == 'duplicate':
                router.duplicate_next = True
                failed_writer[0] = False
            if failed_writer[0] and body['response_format']['json_schema']['name'] == 'QuestionDraft':
                router.calls.append(body)
                return httpx.Response(404, json={'error': {'code':404,'message':'Synthetic unavailable writer'}})
            response = router(request)
            if free:
                return httpx.Response(response.status_code, text=response.text.replace('"cost": 0.0005','"cost": 0'))
            return response
        patcher=patch('httpx.Client',side_effect=lambda **kw:HTTPClient(transport=httpx.MockTransport(respond)))
        patcher.start();self.addCleanup(patcher.stop)
        return router, failed_writer

    def start(self, socket, host):
        self.hello(socket,host['player_token'])
        socket.send_json({'type':'prepare_research_plan'})
        state=self.until(socket,research_planning_status='ready')
        plan_id=state['research_plan']['id']
        socket.send_json({'type':'approve_research_plan','plan_id':plan_id,'question_budget':4,'confirm_profile':True})
        self.until(socket,research_plan_approved=True)
        socket.send_json({'type':'start','plan_id':plan_id,'question_budget':4})

    def test_failed_opening_writer_reconnect_and_duplicate_retry_charge_once(self):
        from backend import game_server, account_store
        from backend.opening_history import paper_key, recent_openings
        router, failed_writer=self.provider()
        host=self.create()
        guest=self.client.post(f"/api/rooms/{host['room_code']}/join",json={'name':'Sam'}).json()
        failed_writer[0]=True
        with self.client.websocket_connect(f"/ws/{host['room_code']}") as socket, \
             self.client.websocket_connect(f"/ws/{host['room_code']}") as teammate:
            self.hello(teammate,guest['player_token'])
            self.start(socket,host)
            failed=self.until(socket,phase='retry')
            self.assertEqual(failed['question_recovery_stage'],'writing')
            self.assertEqual(failed['turns'],[])
            count=len(router.calls)
            teammate.send_json({'type':'retry'})
            while teammate.receive_json()['type']!='error':pass
            self.assertEqual(len(router.calls),count)
        room=game_server.rooms[host['room_code']]
        owner=self._offline_credentials[2]['id']
        before=ProviderAllowance('run:'+room.run_id,owner).snapshot()['used']
        with self.client.websocket_connect(f"/ws/{host['room_code']}") as socket:
            restored=self.hello(socket,host['player_token'])
            self.assertEqual(restored['question_recovery_stage'],'writing')
            self.assertEqual(len(router.calls),count)
            failed_writer[0]=False
            socket.send_json({'type':'retry'})
            socket.send_json({'type':'retry'})
            ready=self.until(socket,phase='voting')
        self.assertEqual([body['response_format']['json_schema']['name'] for body in router.calls[count:]],['QuestionDraft'])
        self.assertEqual(len(ready['turns']),1)
        self.assertEqual(ProviderAllowance('run:'+room.run_id,owner).snapshot()['used'],before+500_000)
        runs=account_store.account_overview(owner)['runs']
        self.assertEqual([(r['id'],r['status']) for r in runs],[(room.run_id,'charged')])
        self.assertEqual(len(recent_openings(owner,paper_key(room.files))),1)

    def _accepted_answer_recovery(self, tier, *, duplicate=False):
        from backend import game_server
        from backend.rooms.commands import CatchUpDeadline
        clock=[1_000_000]
        router,failed_writer=self.provider(free=tier == "free")
        with patch('backend.game_server._now_ms',side_effect=lambda:clock[0]):
            host=self.create(tier=tier)
            guest=self.client.post(f"/api/rooms/{host['room_code']}/join",json={'name':'Sam'}).json()
            with self.client.websocket_connect(f"/ws/{host['room_code']}") as socket, \
                 self.client.websocket_connect(f"/ws/{host['room_code']}") as teammate:
                self.hello(teammate,guest['player_token'])
                self.start(socket,host)
                self.until(socket,phase='voting')
                socket.send_json({'type':'cast_vote','seat':0})
                self.until(socket,phase='voting')
                room=game_server.rooms[host['room_code']]
                clock[0]=room.vote_deadline_ms
                self.client.portal.call(room.coordinator.execute,CatchUpDeadline())
                self.until(socket,phase='question')
                failed_writer[0]='duplicate' if duplicate else True
                socket.send_json({'type':'submit_answer','turn':0,'answer':'A bounded campus pilot.'})
                failed=self.until(socket,phase='retry')
                self.assertEqual(failed['turns'][0]['answer'],'A bounded campus pilot.')
                self.assertEqual(failed['question_recovery_stage'],'writing')
                count=len(router.calls)
                failed_writer[0]=False
                socket.send_json({'type':'retry'})
                ready=self.until(socket,phase='voting')
                other=self.until(teammate,phase='voting',revision=ready['revision'])
                self.assertEqual(ready['turns'],other['turns'])
                self.assertEqual(ready['turns'][0]['answer'],'A bounded campus pilot.')
                self.assertEqual(len(ready['turns']),2)
                self.assertEqual([body['response_format']['json_schema']['name'] for body in router.calls[count:]],['QuestionDraft'])

    def test_grounded_duplicate_question_keeps_plan_and_accepted_answer(self):
        self._accepted_answer_recovery('standard', duplicate=True)

    def test_standard_accepted_answer_survives_failed_writer(self):
        self._accepted_answer_recovery('standard')

    def test_free_accepted_answer_survives_failed_writer_without_upgrading(self):
        self._accepted_answer_recovery('free')

    def test_pending_interpretation_recovery_keeps_private_input_and_original_deadline(self):
        from backend import game_server
        from backend.rooms.commands import CatchUpDeadline
        clock=[1_000_000]
        router,failed_writer=self.provider()
        with patch('backend.game_server._now_ms',side_effect=lambda:clock[0]):
            host=self.create()
            guest=self.client.post(f"/api/rooms/{host['room_code']}/join",json={'name':'Sam'}).json()
            with self.client.websocket_connect(f"/ws/{host['room_code']}") as socket, \
                 self.client.websocket_connect(f"/ws/{host['room_code']}") as teammate:
                self.hello(teammate,guest['player_token'])
                self.start(socket,host)
                self.until(socket,phase='voting')
                socket.send_json({'type':'cast_vote','seat':0})
                self.until(socket,phase='voting')
                room=game_server.rooms[host['room_code']]
                clock[0]=room.vote_deadline_ms
                self.client.portal.call(room.coordinator.execute,CatchUpDeadline())
                question=self.until(socket,phase='question')
                deadline=question['answer_deadline_ms']
                router.fail_name='SubmissionDraft'
                socket.send_json({'type':'submit_answer','turn':0,'answer':'Retain this exact explanation.'})
                failed=self.until(socket,phase='interpretation_retry')
                self.assertEqual(failed['my_pending_submission'],'Retain this exact explanation.')
                self.assertIsNone(failed['turns'][0]['answer'])
                hidden=self.until(teammate,phase='interpretation_retry',revision=failed['revision'])
                self.assertIsNone(hidden.get('my_pending_submission'))
                self.assertEqual(failed['answer_deadline_ms'],deadline)
                clock[0]+=17_000
                router.fail_name='SubmissionDraft'
                socket.send_json({'type':'retry_interpretation'})
                retried=self.until(socket,phase='interpretation_retry',interpretation_attempts_left=4)
                self.assertEqual(retried['answer_deadline_ms'],deadline)
                self.assertEqual(retried['my_pending_submission'],'Retain this exact explanation.')
                failed_writer[0]=True
                socket.send_json({'type':'use_pending_as_answer'})
                accepted=self.until(socket,phase='retry')
                self.assertEqual(accepted['turns'][0]['answer'],'Retain this exact explanation.')
                count=len(router.calls)
                failed_writer[0]=False
                socket.send_json({'type':'retry'})
                self.until(socket,phase='voting')
                self.assertEqual([body['response_format']['json_schema']['name'] for body in router.calls[count:]],['QuestionDraft'])

    def test_end_restart_and_room_closure_discard_question_plan(self):
        from backend import game_server
        router,failed_writer=self.provider()
        host=self.create()
        failed_writer[0]=True
        with self.client.websocket_connect(f"/ws/{host['room_code']}") as socket:
            self.start(socket,host)
            self.until(socket,phase='retry')
            socket.send_json({'type':'end_defense'})
            ended=self.until(socket,phase='complete',feedback_status='ready')
            self.assertIsNone(ended['question_recovery_stage'])
            count=len(router.calls)
            failed_writer[0]=False
            socket.send_json({'type':'restart'})
            self.until(socket,phase='voting')
            self.assertEqual([b['response_format']['json_schema']['name'] for b in router.calls[count:]],['PlanDraft','QuestionDraft'])
        # A separately failed opening is settled and can be closed through HTTP.
        second=self.create()
        failed_writer[0]=True
        with self.client.websocket_connect(f"/ws/{second['room_code']}") as socket:
            self.start(socket,second)
            self.until(socket,phase='retry')
        room=game_server.rooms[second['room_code']]
        self.assertEqual(room.question_recovery.stage,'writing')
        closed=self.client.delete(f"/api/rooms/{second['room_code']}")
        self.assertEqual(closed.status_code,200,closed.text)
        self.assertIsNone(room.question_recovery.stage)
        self.assertNotIn(second['room_code'],game_server.rooms)

    def test_expiry_reclaims_saved_opening_plan_without_dispatch(self):
        from backend import game_server
        clock=[1_000_000]
        router,failed_writer=self.provider()
        with patch('backend.game_server._now_ms',side_effect=lambda:clock[0]):
            host=self.create()
            failed_writer[0]=True
            with self.client.websocket_connect(f"/ws/{host['room_code']}") as socket:
                self.start(socket,host)
                self.until(socket,phase='retry')
            room=game_server.rooms[host['room_code']]
            self.assertEqual(room.question_recovery.stage,'writing')
            count=len(router.calls)
            clock[0]=room.expires_at()+1
            listed=self.client.get('/api/rooms')
            self.assertEqual(listed.status_code,200,listed.text)
            self.assertFalse(listed.json()['rooms'])
            self.assertNotIn(host['room_code'],game_server.rooms)
            self.assertIsNone(room.question_recovery.stage)
            self.assertEqual(len(router.calls),count)

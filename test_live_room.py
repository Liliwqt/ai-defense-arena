"""Existing two-client room contracts in live voucher mode; AI mocked."""
import os
from unittest.mock import patch
from unittest.mock import AsyncMock
from test_game_server import GameServerTests


class LiveRoomTests(GameServerTests):
    def setUp(self):
        live=patch.dict(os.environ,{'PAYMENTS_MODE':'live','LIVE_PAID_STARTS_ENABLED':'1',
            'PAYMONGO_LIVE_SECRET_KEY':'sk_live_offline','PAYMONGO_LIVE_WEBHOOK_SECRET':'offline',
            'PAYMONGO_PUBLIC_BASE_URL':'https://offline.example.test'})
        live.start();self.addCleanup(live.stop)
        recover=patch('payments_live.recover_payments',new_callable=AsyncMock)
        recover.start();self.addCleanup(recover.stop)
        coaching=patch('game_server.generate_coaching_report',return_value=__import__('question_generator').CoachingReport('Offline report',[],[],'Review the discussion.'))
        coaching.start();self.addCleanup(coaching.stop)
        super().setUp()

    def test_paid_code_two_client_defense_charges_once_and_preserves_guest_protocol(self):
        from starlette.testclient import WebSocketTestSession
        from live_store import LiveStore
        store=LiveStore();account_id=self._offline_credentials[2]['id']
        with patch.dict(os.environ,{'FREE_ACCESS_VOUCHER':'','LIVE_TOPUP_INVITED_EMAILS':'host@example.test'}):
            row,_=store.begin_topup(account_id,'credits-10','offline-paid-room-1234')
            store.bind_topup_intent(row['id'],'pi_room');store.register_topup(row['id'],'pi_room','unused-fixture',1)
            store.record_topup_paid(row['id'],'pi_room',['pay_room'],100,'PHP')
            send=WebSocketTestSession.send_json
            def confirmed(socket,data,*args,**kwargs):
                return send(socket,{**data,**({'confirm_cost':True} if data.get('type') in {'start','restart'} else {})},*args,**kwargs)
            with patch.object(WebSocketTestSession,'send_json',confirmed):
                self.test_two_clients_share_four_turns_and_first_answer_wins()
            view=store.overview(account_id)
            self.assertEqual(view['live_credits'],0)
            self.assertEqual(view['live_runs'][0]['cost'],10)
            self.assertEqual(view['live_runs'][0]['status'],'charged')

    def test_all_defender_absence_abandons_before_reconnect_without_credit_return(self):
        import game_server
        from live_store import LiveStore
        from unittest.mock import patch
        host=self.create_room()
        with patch.object(game_server,'generate_first_question',return_value=self.questions[0]):
            socket,_=self.connect(host['room_code'],host['player_token'])
            socket.send_json({'type':'start'})
            self.receive_phase(socket,'voting')
            socket.__exit__(None,None,None)
            for _ in range(61):
                self.clock_ms+=10_000
                self.client.portal.call(game_server._observe_absence,game_server.rooms[host['room_code']])
            reconnected,state=self.connect(host['room_code'],host['player_token'])
            self.assertEqual(state['phase'],'complete')
            self.assertIn('abandoned',state['error'])
            self.assertIsNone(LiveStore().overview(self._offline_credentials[2]['id'])['active_run'])
            reconnected.__exit__(None,None,None)

    def test_process_observation_gap_is_not_defender_abandonment(self):
        import game_server
        from live_store import LiveStore
        host=self.create_room()
        with patch.object(game_server,'generate_first_question',return_value=self.questions[0]):
            socket,_=self.connect(host['room_code'],host['player_token']);socket.send_json({'type':'start'})
            self.receive_phase(socket,'voting');socket.__exit__(None,None,None)
            self.clock_ms+=600_001
            self.client.portal.call(game_server._observe_absence,game_server.rooms[host['room_code']])
            self.assertIsNotNone(LiveStore().overview(self._offline_credentials[2]['id'])['active_run'])

    def test_coaching_persistence_failure_never_publishes_ready_and_can_retry(self):
        import game_server
        from live_store import LiveStore
        original=LiveStore.finish_run
        calls=[]
        def finish(store,ident,outcome):
            calls.append(outcome)
            if len(calls)==1:raise RuntimeError('Offline database write failure')
            return original(store,ident,outcome)
        with patch.object(game_server,'generate_first_question',return_value=self.questions[0]),patch.object(game_server,'generate_next_move',side_effect=self.short_moves),patch.object(LiveStore,'finish_run',finish):
            host=self.create_room();guest=self.join_room(host['room_code'])
            hs,_=self.connect(host['room_code'],host['player_token']);gs,_=self.connect(guest['room_code'],guest['player_token'])
            try:
                states=self._complete_four_turns(hs,gs,None)
                for state in states.values():
                    self.assertEqual(state['feedback_status'],'failed');self.assertIsNone(state['feedback'])
                self.assertIsNotNone(LiveStore().overview(self._offline_credentials[2]['id'])['active_run'])
                hs.send_json({'type':'retry_coaching'})
                for socket in (hs,gs):
                    state=self.receive_phase(socket,'complete')
                    while state['feedback_status']!='ready':state=self.receive_phase(socket,'complete')
                self.assertIsNone(LiveStore().overview(self._offline_credentials[2]['id'])['active_run'])
            finally:gs.__exit__(None,None,None);hs.__exit__(None,None,None)

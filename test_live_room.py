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
            self.clock_ms+=600001
            reconnected,state=self.connect(host['room_code'],host['player_token'])
            self.assertEqual(state['phase'],'complete')
            self.assertIn('abandoned',state['error'])
            self.assertIsNone(LiveStore().overview(self._offline_credentials[2]['id'])['active_run'])
            reconnected.__exit__(None,None,None)

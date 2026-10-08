"""Long research/mixed room contracts with live funding, AI and identity fixtures."""
import os
from unittest.mock import AsyncMock,patch
from starlette.testclient import WebSocketTestSession
import test_research_coverage
from live_store import LiveStore


class LiveResearchTests(test_research_coverage.CoverageProtocolTests):
    def setUp(self):
        env=patch.dict(os.environ,{'PAYMENTS_MODE':'live','LIVE_PAID_STARTS_ENABLED':'1',
            'PAYMONGO_LIVE_SECRET_KEY':'sk_live_offline','PAYMONGO_LIVE_WEBHOOK_SECRET':'offline',
            'PAYMONGO_PUBLIC_BASE_URL':'https://offline.example.test'})
        env.start();self.addCleanup(env.stop)
        recovery=patch('payments_live.recover_payments',new_callable=AsyncMock)
        recovery.start();self.addCleanup(recovery.stop)
        super().setUp()

    def test_paid_research_and_mixed_keep_twelve_question_budget_and_charge_once_per_run(self):
        store=LiveStore();account_id=self._offline_credentials[2]['id']
        with patch.dict(os.environ,{'FREE_ACCESS_VOUCHER':'','LIVE_TOPUP_INVITED_EMAILS':'host@example.test'}):
            row,_=store.begin_topup(account_id,'credits-50','offline-paid-research-1234')
            store.bind_topup_intent(row['id'],'pi_research');store.register_topup(row['id'],'pi_research','unused-fixture',1)
            store.record_topup_paid(row['id'],'pi_research',['pay_research'],500,'PHP')
            send=WebSocketTestSession.send_json
            def confirmed(socket,data,*args,**kwargs):
                return send(socket,{**data,**({'confirm_cost':True} if data.get('type') in {'start','restart'} else {})},*args,**kwargs)
            with patch.object(WebSocketTestSession,'send_json',confirmed):
                self.test_twelve_question_research_and_mixed_with_vote_clarification_timeout_retry_reconnect_coaching()
            view=store.overview(account_id)
            self.assertEqual(view['live_credits'],30)
            self.assertEqual(len(view['live_runs']),2)
            self.assertTrue(all(run['outcome']=='completed' and run['cost']==10 for run in view['live_runs']))

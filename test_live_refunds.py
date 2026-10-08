"""Refund review through authenticated HTTP, provider reads always mocked."""
from unittest.mock import Mock, patch
import os
import account_store
from live_store import LiveStore
from test_live_runs import LiveRunTests


class LiveRefundTests(LiveRunTests):
    def hold(self, row):
        return self.client.post('/api/payments/live/operator/refunds', json={'topup_id':row['id'],'reason':'Customer requests unused purchase refund'})

    def test_operator_hold_blocks_spending_and_duplicate_hold_is_harmless(self):
        row=self.fund()
        self.assertEqual(self.hold(row).status_code,403)
        with patch.dict(os.environ,{'PAYMENT_OPERATOR_GOOGLE_SUB':'owner'}):
            first=self.hold(row);self.assertEqual(first.status_code,201,first.text)
            self.assertEqual(self.hold(row).json()['refund']['id'],first.json()['refund']['id'])
        view=LiveStore().overview(self.account_id)
        self.assertEqual((view['live_credits'],view['live_held_credits']),(0,10))
        self.assertEqual(view['live_orders'][0]['refund_eligibility'],'held')
        with self.assertRaises(account_store.AccessError):LiveStore().reserve_run(self.account_id,'held-run','service-one','ROOM')

    def test_reservation_or_historical_spending_requires_review_without_hold(self):
        row=self.fund();store=LiveStore();store.reserve_run(self.account_id,'used','service-one','ROOM')
        with patch.dict(os.environ,{'PAYMENT_OPERATOR_GOOGLE_SUB':'owner'}):
            self.assertEqual(self.hold(row).status_code,409)
            store.charge_run(self.account_id,'used');store.service_state('used','unavailable','question');store.end_unavailable(self.account_id,'used')
            self.assertEqual(self.hold(row).status_code,409)
        self.assertEqual(store.overview(self.account_id)['live_credits'],10)
        self.assertEqual(store.overview(self.account_id)['live_orders'][0]['refund_eligibility'],'used_review')

    def test_verified_refund_success_is_terminal_and_paid_replay_cannot_reaward(self):
        row=self.fund()
        with patch.dict(os.environ,{'PAYMENT_OPERATOR_GOOGLE_SUB':'owner','PAYMONGO_REFUND_RECONCILIATION_ENABLED':'1'}):
            hold=self.hold(row).json()['refund']
            attrs={'livemode':True,'payment_id':'pay_'+row['id'],'amount':100,'currency':'PHP','status':'processing'}
            resource={'id':'ref_fixture','type':'refund','attributes':attrs}
            result=Mock();result.json.return_value={'data':resource};self.provider.get.return_value=result
            url='/api/payments/live/operator/refunds/'+hold['id']+'/reconcile'
            self.assertEqual(self.client.post(url,json={'provider_id':'ref_fixture'}).status_code,200)
            self.assertEqual(LiveStore().overview(self.account_id)['live_held_credits'],10)
            attrs['status']='succeeded'
            self.assertEqual(self.client.post(url,json={'provider_id':'ref_fixture'}).status_code,200)
            self.assertEqual(self.client.post(url,json={'provider_id':'ref_fixture'}).status_code,200)
            attrs['status']='failed'
            self.assertEqual(self.client.post(url,json={'provider_id':'ref_fixture'}).status_code,200)
        self.assertEqual(self.paid(row).status_code,200)
        view=LiveStore().overview(self.account_id)
        self.assertEqual((view['live_credits'],view['live_held_credits']),(0,0))
        self.assertEqual(view['live_orders'][0]['refund_status'],'succeeded')
        self.assertEqual(view['live_orders'][0]['refund_eligibility'],'refunded')

    def test_wrong_provider_evidence_retains_hold_and_verified_failure_releases_once(self):
        row=self.fund()
        with patch.dict(os.environ,{'PAYMENT_OPERATOR_GOOGLE_SUB':'owner','PAYMONGO_REFUND_RECONCILIATION_ENABLED':'1'}):
            hold=self.hold(row).json()['refund'];url='/api/payments/live/operator/refunds/'+hold['id']+'/reconcile'
            attrs={'livemode':True,'payment_id':'wrong','amount':100,'currency':'PHP','status':'failed'}
            result=Mock();result.json.return_value={'data':{'id':'ref_fixture','type':'refund','attributes':attrs}};self.provider.get.return_value=result
            for field,value in [('payment_id','wrong'),('livemode',False),('amount',99),('currency','USD')]:
                correct={'payment_id':'pay_'+row['id'],'livemode':True,'amount':100,'currency':'PHP'}
                attrs.update(correct);attrs[field]=value
                self.assertEqual(self.client.post(url,json={'provider_id':'ref_fixture'}).status_code,409)
                self.assertEqual(LiveStore().overview(self.account_id)['live_held_credits'],10)
            attrs.update(correct)
            self.assertEqual(self.client.post(url,json={'provider_id':'ref_fixture'}).status_code,200)
            self.assertEqual(self.client.post(url,json={'provider_id':'ref_fixture'}).status_code,200)
        self.assertEqual(LiveStore().overview(self.account_id)['live_credits'],10)
        self.assertEqual(LiveStore().overview(self.account_id)['live_orders'][0]['refund_eligibility'],'unused_review')

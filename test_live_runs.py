"""Live defense funding through supported store contracts, provider fixtures only."""
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch
import account_store
from live_store import LiveStore
from test_live_payments import LivePaymentTests


class LiveRunTests(LivePaymentTests):
    def setUp(self):
        super().setUp()
        LiveStore().start_service('service-one')

    def fund(self,amount=100,package='credits-10'):
        self.resources(amount);row=self.create(package=package).json()['topup'];self.assertEqual(self.paid(row).status_code,200)
        return row

    def test_reserve_charge_complete_is_once_only_and_host_exclusive(self):
        self.fund();store=LiveStore()
        store.reserve_run(self.account_id,'run-one','service-one','ROOM')
        self.assertEqual(store.overview(self.account_id)['live_credits'],0)
        self.assertEqual(store.overview(self.account_id)['live_reserved_credits'],10)
        with self.assertRaises(account_store.AccessError):store.reserve_run(self.account_id,'run-two','service-one','OTHER')
        store.charge_run(self.account_id,'run-one');store.charge_run(self.account_id,'run-one')
        self.assertEqual(store.overview(self.account_id)['live_reserved_credits'],0)
        store.finish_run('run-one','completed')
        self.assertIsNone(store.overview(self.account_id)['active_run'])
        self.assertEqual(store.overview(self.account_id)['live_credits'],0)

    def test_unresolved_ai_failure_can_end_and_return_once_but_completion_cannot(self):
        self.fund();store=LiveStore();store.reserve_run(self.account_id,'failed-run','service-one','ROOM');store.charge_run(self.account_id,'failed-run')
        with self.assertRaises(account_store.AccessError):store.end_unavailable(self.account_id,'failed-run')
        store.service_state('failed-run','unavailable','coaching')
        store.end_unavailable(self.account_id,'failed-run');store.end_unavailable(self.account_id,'failed-run')
        store.finish_run('failed-run','completed')
        view=store.overview(self.account_id)
        self.assertEqual(view['live_credits'],10)
        self.assertEqual([item['credits'] for item in view['credit_returns']],[10])
        self.assertEqual(view['live_runs'][0]['outcome'],'ended_unavailable')

    def test_server_loss_returns_only_unfinished_charge_and_ignores_abandoned(self):
        self.fund(amount=500,package='credits-50');store=LiveStore()
        store.stop_service('service-one')
        store.start_service('old-service',now=100)
        store.reserve_run(self.account_id,'done','old-service','ROOM');store.charge_run(self.account_id,'done');store.finish_run('done','completed')
        store.reserve_run(self.account_id,'abandoned','old-service','ROOM');store.charge_run(self.account_id,'abandoned');store.finish_run('abandoned','abandoned')
        store.reserve_run(self.account_id,'lost','old-service','ROOM');store.charge_run(self.account_id,'lost')
        with self.assertRaises(account_store.AccessError):store.start_service('overlap',now=120)
        store.start_service('replacement',now=200)
        store.start_service('replacement',now=200)
        view=store.overview(self.account_id)
        self.assertEqual(view['live_credits'],30)
        self.assertEqual(len(view['credit_returns']),1)
        self.assertIsNone(view['active_run'])

    def test_opening_restart_reuses_released_funds_and_lost_service_is_fenced(self):
        self.fund();store=LiveStore()
        store.reserve_run(self.account_id,'opening','service-one','ROOM')
        store.reserve_run(self.account_id,'replacement','service-one','ROOM',replace_id='opening')
        self.assertEqual(store.overview(self.account_id)['live_reserved_credits'],10)
        store.stop_service('service-one');store.start_service('new-service')
        self.assertEqual(store.overview(self.account_id)['live_credits'],10)
        with self.assertRaises(account_store.AccessError):store.charge_run(self.account_id,'replacement')
        with self.assertRaises(account_store.AccessError):store.reserve_run(self.account_id,'stale','service-one','ROOM')

    def test_concurrent_starts_and_paid_webhooks_do_not_overspend_or_double_award(self):
        row=self.fund();store=LiveStore()
        def start(index):
            try:store.reserve_run(self.account_id,'race-'+str(index),'service-one','ROOM');return True
            except account_store.AccessError:return False
        with ThreadPoolExecutor(max_workers=4) as workers:
            self.assertEqual(sum(workers.map(start,range(8))),1)
            self.assertEqual(list(workers.map(lambda _:self.paid(row).status_code,range(8))),[200]*8)
        self.assertEqual(store.overview(self.account_id)['live_credits'],0)

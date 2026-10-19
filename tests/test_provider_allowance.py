"""Public allowance/store contract; disposable database, no provider calls."""

from concurrent.futures import ThreadPoolExecutor
import unittest

from backend.provider_allowance import ProviderAllowance, AllowanceError
from tests.offline_accounts import authenticate


class PreparationAllowanceTests(unittest.TestCase):
    def setUp(self):
        account = authenticate(self)
        self.allowance = ProviderAllowance('preparation', account['id'])
        self.allowance.establish(1000, {'max_output_tokens': 1024})

    def test_concurrent_admission_cannot_spend_the_same_remaining_allowance(self):
        def reserve(_):
            try:
                return self.allowance.reserve(600)
            except AllowanceError:
                return None
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(reserve, range(8)))
        self.assertEqual(sum(result is not None for result in results), 1)
        self.assertEqual(self.allowance.snapshot(), {'ceiling': 1000, 'used': 600, 'remaining': 400})

    def test_reopen_preserves_policy_uncertain_request_and_once_only_cost(self):
        request = self.allowance.reserve(600)
        reopened = ProviderAllowance(self.allowance.id, self.allowance.owner)
        self.assertEqual(reopened.establish(10000, {'max_output_tokens': 9999}), {'max_output_tokens': 1024})
        self.assertEqual(reopened.snapshot()['remaining'], 400)
        reopened.settle(request, 100)
        reopened.settle(request, 100)
        self.assertEqual(self.allowance.snapshot()['remaining'], 900)
        with self.assertRaises(AllowanceError):
            ProviderAllowance(self.allowance.id, 'another-owner').reserve(1)

    def test_conflicting_or_over_bound_cost_blocks_further_dispatch(self):
        request = self.allowance.reserve(600)
        self.allowance.settle(request, 100)
        with self.assertRaises(AllowanceError):
            self.allowance.settle(request, 200)
        with self.assertRaises(AllowanceError):
            self.allowance.reserve(1)

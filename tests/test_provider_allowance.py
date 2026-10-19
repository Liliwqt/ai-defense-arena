"""Public allowance/store contract; disposable database, no provider calls."""

from concurrent.futures import ThreadPoolExecutor
import unittest

from backend.provider_allowance import AllowanceError, ProviderAllowance, reported_nano
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


class DefenseAllowanceLimitTests(unittest.TestCase):
    def setUp(self):
        account = authenticate(self)
        self.allowance = ProviderAllowance('run:limit', account['id'])
        self.allowance.establish(1000, {'ceiling_nano': 1000})

    def test_optional_limit_protects_the_coaching_reserve(self):
        request = self.allowance.reserve(400, limit=600)
        with self.assertRaisesRegex(AllowanceError, 'cannot fund another question'):
            self.allowance.reserve(300, limit=600)
        self.allowance.settle(request, 100)
        self.allowance.reserve(400, limit=600)
        self.assertEqual(self.allowance.snapshot(), {'ceiling': 1000, 'used': 500, 'remaining': 500})

    def test_limit_above_the_ceiling_still_uses_the_ceiling(self):
        with self.assertRaisesRegex(AllowanceError, 'cannot fund another question'):
            self.allowance.reserve(1001, limit=5000)

    def test_concurrent_limited_admission_cannot_overspend_the_reserve(self):
        def reserve(_):
            try:
                return self.allowance.reserve(300, limit=600)
            except AllowanceError:
                return None
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(reserve, range(8)))
        self.assertEqual(sum(result is not None for result in results), 2)
        self.assertEqual(self.allowance.snapshot()['used'], 600)

    def test_invalid_costs_and_limits_are_rejected(self):
        for limit in (0, -1, '600', True, 1.5):
            with self.subTest(limit=limit):
                with self.assertRaises(AllowanceError):
                    self.allowance.reserve(10, limit=limit)
        with self.assertRaises(AllowanceError):
            self.allowance.reserve(0)

    def test_reported_cost_evidence_is_bounded_and_rounded_up(self):
        for usage in (None, {}, {'cost': 'not-a-number'}, {'cost': -1}, {'cost': 1_000_001}):
            with self.subTest(usage=usage):
                self.assertIsNone(reported_nano(usage))
        self.assertEqual(reported_nano({'cost': 0.0005}), 500_000)
        self.assertEqual(reported_nano({'cost': '0.0000000001'}), 1)


class ProtectedCoachingAllowanceTests(unittest.TestCase):
    def setUp(self):
        account = authenticate(self)
        self.allowance = ProviderAllowance('run:protected-coaching', account['id'])
        self.allowance.establish(1000, {'coaching_reserve_nano': 400})

    def test_concurrent_coaching_reservations_and_settlement_preserve_the_ceiling(self):
        # Questions have used their whole600 limit;400 remains protected.
        self.allowance.reserve(600, limit=600)
        def coach(_):
            try:
                return self.allowance.reserve(300, limit=1000)
            except AllowanceError:
                return None
        with ThreadPoolExecutor(max_workers=4) as pool:
            requests = [item for item in pool.map(coach, range(8)) if item]
        self.assertEqual(len(requests), 1)
        self.assertEqual(self.allowance.snapshot()['remaining'], 100)
        with self.assertRaises(AllowanceError):
            self.allowance.reserve(1, limit=600)
        self.allowance.settle(requests[0], 100)
        self.allowance.settle(requests[0], 100)
        self.allowance.reserve(300, limit=1000)
        reopened = ProviderAllowance(self.allowance.id, self.allowance.owner)
        self.assertEqual(reopened.establish(10000, {}), {'coaching_reserve_nano': 400})
        self.assertEqual(reopened.snapshot(), {'ceiling': 1000, 'used': 1000, 'remaining': 0})
        with self.assertRaises(AllowanceError):
            reopened.reserve(1, limit=1000)

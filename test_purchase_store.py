"""Persisted purchase behavior; no provider, HTTP, or browser calls."""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import tempfile
import unittest

from purchase_store import PurchaseStore, PurchaseError
from account_store import connect_store


class PurchaseStoreTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.store = PurchaseStore(Path(directory.name) / "purchases.sqlite3")
        with connect_store(self.store.database) as db:
            db.execute("INSERT INTO accounts VALUES ('owner', 'synthetic-sub', 'owner@example.test', 'Owner', 0)")

    def test_registered_request_reuse_and_concurrent_award_are_once_only(self):
        order = self.store.begin("owner", "request-identifier", now=1000)
        with self.assertRaises(PurchaseError) as pending:
            self.store.begin("owner", "request-identifier", now=1001)
        self.assertEqual(pending.exception.kind, "creating")
        registered = self.store.register(order["id"], "cs_fixture", "https://checkout.paymongo.com/fixture")
        self.assertEqual(self.store.begin("owner", "request-identifier", now=1002), registered)
        with ThreadPoolExecutor(max_workers=4) as workers:
            list(workers.map(lambda _: self.store.record_paid(order["id"], "cs_fixture", ["pay_fixture"], now=1010), range(4)))
        paid = self.store.get(order["id"])
        self.assertEqual(paid["status"], "paid")
        self.assertEqual(paid["paid_at"], 1010)
        self.assertEqual(self.store.history("owner")[0]["awarded_credits"], 100)
        self.assertEqual(len(self.store.history("owner")), 1)
        self.assertEqual(self.store.history("another"), [])

    def test_duplicate_payment_rolls_back_receipt_and_award_together(self):
        first = self.store.begin("owner", "first-request-id", now=1000)
        self.store.register(first["id"], "cs_first", "https://checkout.paymongo.com/first")
        self.store.record_paid(first["id"], "cs_first", ["pay_once"], now=1001)
        second = self.store.begin("owner", "second-request-id", now=1002)
        self.store.register(second["id"], "cs_second", "https://checkout.paymongo.com/second")
        with self.assertRaises(PurchaseError) as duplicate:
            self.store.record_paid(second["id"], "cs_second", ["pay_once"], now=1003)
        self.assertEqual(duplicate.exception.kind, "duplicate_payment")
        self.assertEqual(self.store.get(second["id"])["status"], "pending")
        self.assertEqual(sum(item["awarded_credits"] for item in self.store.history("owner")), 100)

    def test_topup_reserve_register_and_concurrent_award_are_once_only(self):
        topup = self.store.begin_topup("owner", "starter", "topup-request-1", now=2000)
        self.assertEqual(topup["provider"], "payment_intent")
        self.assertEqual((topup["amount"], topup["credits"], topup["status"]), (10000, 100, "creating"))
        with self.assertRaises(PurchaseError) as pending:
            self.store.begin_topup("owner", "starter", "topup-request-1", now=2001)
        self.assertEqual(pending.exception.kind, "creating")
        registered = self.store.register_topup(topup["id"], "pi_fixture", "data:image/png;base64,AAAA", 1800003600)
        self.assertEqual((registered["status"], registered["intent_id"], registered["expires_at"]), ("pending", "pi_fixture", 1800003600))
        self.assertEqual(self.store.begin_topup("owner", "starter", "topup-request-1", now=2002), registered)
        with ThreadPoolExecutor(max_workers=4) as workers:
            list(workers.map(lambda _: self.store.record_topup_paid(topup["id"], "pi_fixture", ["pay_topup"], 10000, now=2010), range(4)))
        paid = self.store.get(topup["id"])
        self.assertEqual((paid["status"], paid["paid_at"]), ("paid", 2010))
        self.assertEqual(self.store.history("owner")[0]["awarded_credits"], 100)

    def test_topup_amount_or_reference_mismatch_awards_nothing(self):
        topup = self.store.begin_topup("owner", "starter", "topup-mismatch", now=2000)
        self.store.register_topup(topup["id"], "pi_x", "image", 1800003600)
        for intent_id, amount, currency in (("pi_x", 5000, "PHP"), ("pi_other", 10000, "PHP"), ("pi_x", 10000, "USD")):
            with self.assertRaises(PurchaseError) as mismatch:
                self.store.record_topup_paid(topup["id"], intent_id, ["pay_x"], amount, currency, now=2001)
            self.assertEqual(mismatch.exception.kind, "checkout_mismatch")
        with self.assertRaises(PurchaseError):
            self.store.record_topup_paid(topup["id"], "pi_x", [], 10000, now=2002)
        self.assertEqual(self.store.get(topup["id"])["status"], "pending")
        self.assertEqual(sum(item["awarded_credits"] for item in self.store.history("owner")), 0)

    def test_failed_or_expired_topup_awards_nothing_and_paid_is_terminal(self):
        failed = self.store.begin_topup("owner", "starter", "topup-fail", now=2000)
        self.store.register_topup(failed["id"], "pi_fail", "image", 1800003600)
        self.store.mark_topup_failed(failed["id"])
        self.assertEqual(self.store.get(failed["id"])["status"], "failed")
        expired = self.store.begin_topup("owner", "starter", "topup-exp", now=2002)
        self.store.register_topup(expired["id"], "pi_exp", "image", 1800003600)
        self.store.mark_topup_expired(expired["id"])
        self.assertEqual(self.store.get(expired["id"])["status"], "expired")
        self.assertEqual(sum(item["awarded_credits"] for item in self.store.history("owner")), 0)
        paid = self.store.begin_topup("owner", "starter", "topup-paid", now=2004)
        self.store.register_topup(paid["id"], "pi_paid", "image", 1800003600)
        self.store.record_topup_paid(paid["id"], "pi_paid", ["pay_paid"], 10000, now=2005)
        self.store.mark_topup_failed(paid["id"])
        self.store.mark_topup_expired(paid["id"])
        self.assertEqual(self.store.get(paid["id"])["status"], "paid")

    def test_unknown_package_rejected_and_topups_are_account_scoped(self):
        with self.assertRaises(PurchaseError) as unknown:
            self.store.begin_topup("owner", "gold", "topup-bad", now=2000)
        self.assertEqual(unknown.exception.kind, "unknown_package")
        self.store.begin_topup("owner", "starter", "topup-scope", now=2001)
        self.assertEqual(self.store.history("another"), [])
        self.assertEqual(len(self.store.history("owner")), 1)


if __name__ == "__main__":
    unittest.main()

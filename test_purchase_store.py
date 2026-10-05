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


if __name__ == "__main__":
    unittest.main()

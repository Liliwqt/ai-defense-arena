"""Opening history and charging through the public account-store boundary."""

from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import os
import sqlite3
import json
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from backend import account_store
from backend.opening_history import OpeningQuestion, paper_key, recent_openings
from backend.project_files import ProjectFile


class OpeningHistoryTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.db_path = Path(folder.name) / "accounts.sqlite3"
        env = patch.dict(os.environ, {"PAYMONGO_TEST_DB_PATH": str(self.db_path),
                                     "PAYMENTS_MODE": "test", "FREE_ACCESS_VOUCHER": ""})
        env.start()
        self.addCleanup(env.stop)
        token, _ = account_store.create_google_session("history-host", "host@example.test", "Host")
        self.account_id = account_store.session_account(token)["id"]
        # Fixture funding; assertions use account/history contracts, not SQL.
        with account_store.connect_store(self.db_path) as db:
            db.execute("INSERT INTO test_orders (id,token_hash,amount,currency,status,created_at,account_id,credits) VALUES ('history-order','fixture',10000,'PHP','paid',1,?,100)", (self.account_id,))
            db.execute("INSERT INTO test_credit_ledger VALUES ('history-order',?,100,1)", (self.account_id,))
        self.files = [ProjectFile("paper.md", "We plan interviews with students.", "research_text")]

    def opening(self, question="Why use student interviews?"):
        return OpeningQuestion(paper_key(self.files), question, "Methodology Reviewer", "topic-1")

    def test_committed_opening_survives_rename_and_replay_charges_once(self):
        account_store.reserve_run(self.account_id, "run-one")
        opening = self.opening()
        account_store.charge_run(self.account_id, "run-one", opening=opening)
        account_store.charge_run(self.account_id, "run-one", opening=opening)
        renamed = [ProjectFile("renamed.txt", self.files[0].content, "research_text")]
        history = recent_openings(self.account_id, paper_key(renamed))
        self.assertEqual([entry["question"] for entry in history], ["Why use student interviews?"])
        restarted = subprocess.run([sys.executable, "-c",
            "import json,sys; from backend.opening_history import recent_openings; print(json.dumps(recent_openings(sys.argv[1],sys.argv[2])))",
            self.account_id, paper_key(renamed)], capture_output=True, text=True, timeout=15)
        self.assertEqual(restarted.returncode, 0, restarted.stderr)
        self.assertEqual(json.loads(restarted.stdout), history)
        self.assertEqual(paper_key(renamed + [ProjectFile("app.py", "print('changed code')")]), paper_key(self.files))
        self.assertEqual(account_store.account_access(self.account_id)["spent_credits"], 10)
        self.assertEqual(recent_openings(self.account_id, paper_key([
            ProjectFile("paper.md", "We plan teacher interviews.", "research_text")])), [])

    def test_only_five_unexpired_openings_remain_and_old_commit_cannot_reappear(self):
        for index in range(7):
            account_store.reserve_run(self.account_id, f"run-{index}")
            with patch("backend.opening_history.time.time", return_value=1000 + index):
                account_store.charge_run(self.account_id, f"run-{index}", opening=self.opening(f"Explain decision {index}?"))
        history = recent_openings(self.account_id, paper_key(self.files), now=1006)
        self.assertEqual([entry["question"] for entry in history],
                         [f"Explain decision {index}?" for index in (6, 5, 4, 3, 2)])
        with patch("backend.opening_history.time.time", return_value=1007):
            account_store.charge_run(self.account_id, "run-0", opening=self.opening("Explain decision 0?"))
        self.assertEqual(recent_openings(self.account_id, paper_key(self.files), now=1007), history)
        self.assertEqual(recent_openings(self.account_id, paper_key(self.files), now=1006 + 30 * 86400), [])

    def test_normalized_repeat_is_rejected_without_charging_and_history_is_private(self):
        account_store.reserve_run(self.account_id, "accepted")
        account_store.charge_run(self.account_id, "accepted", opening=self.opening())
        account_store.reserve_run(self.account_id, "repeated")
        with self.assertRaisesRegex(account_store.AccessError, "recent opening"):
            account_store.charge_run(self.account_id, "repeated", opening=self.opening(" WHY use student interviews!!! "))
        view = account_store.account_access(self.account_id)
        self.assertEqual((view["spent_credits"], view["reserved_credits"]), (10, 10))
        token, _ = account_store.create_google_session("different-host", "other@example.test", "Other")
        other = account_store.session_account(token)["id"]
        self.assertEqual(recent_openings(other, paper_key(self.files)), [])
        self.assertEqual(len(recent_openings(self.account_id, paper_key(self.files))), 1)

    def test_history_write_failure_rolls_back_charge_until_retry(self):
        account_store.reserve_run(self.account_id, "failed-write")
        postgres = bool(os.environ.get("DATABASE_URL"))
        with account_store.connect_store(self.db_path) as db:
            if postgres:
                db.execute("ALTER TABLE research_openings ADD CONSTRAINT reject_opening CHECK(question <> 'Reject this question?')")
            else:
                db.execute("CREATE TRIGGER reject_opening BEFORE INSERT ON research_openings WHEN NEW.question='Reject this question?' BEGIN SELECT RAISE(ABORT,'fixture failure'); END")
        with self.assertRaises(sqlite3.IntegrityError):
            account_store.charge_run(self.account_id, "failed-write", opening=self.opening("Reject this question?"))
        view = account_store.account_access(self.account_id)
        self.assertEqual((view["spent_credits"], view["reserved_credits"]), (0, 10))
        self.assertEqual(recent_openings(self.account_id, paper_key(self.files)), [])
        with account_store.connect_store(self.db_path) as db:
            db.execute("ALTER TABLE research_openings DROP CONSTRAINT reject_opening" if postgres else "DROP TRIGGER reject_opening")
        account_store.charge_run(self.account_id, "failed-write", opening=self.opening("Reject this question?"))
        self.assertEqual(account_store.account_access(self.account_id)["spent_credits"], 10)

    def test_racing_commits_accept_one_opening_and_replays_stay_idempotent(self):
        for name in ("race-a", "race-b", "race-c"):
            account_store.reserve_run(self.account_id, name)
        def commit(name):
            try:
                account_store.charge_run(self.account_id, name, opening=self.opening())
                return name
            except account_store.AccessError:
                return None
        with ThreadPoolExecutor(max_workers=3) as pool:
            winners = [name for name in pool.map(commit, ("race-a", "race-b", "race-c")) if name]
            self.assertEqual(len(winners), 1)
            self.assertEqual(list(pool.map(commit, [winners[0]] * 3)), winners * 3)
        self.assertEqual(len(recent_openings(self.account_id, paper_key(self.files))), 1)
        self.assertEqual(account_store.account_access(self.account_id)["spent_credits"], 10)

    def test_explicit_repeat_acceptance_is_atomic_and_idempotent_under_racing_writes(self):
        account_store.reserve_run(self.account_id, "prior")
        account_store.charge_run(self.account_id, "prior", opening=self.opening())
        account_store.reserve_run(self.account_id, "accepted-repeat")
        postgres = bool(os.environ.get("DATABASE_URL"))
        with account_store.connect_store(self.db_path) as db:
            db.execute("ALTER TABLE research_openings ADD CONSTRAINT reject_repeat CHECK(run_id <> 'accepted-repeat')" if postgres else
                       "CREATE TRIGGER reject_repeat BEFORE INSERT ON research_openings WHEN NEW.run_id='accepted-repeat' BEGIN SELECT RAISE(ABORT,'fixture failure'); END")
        with self.assertRaises(sqlite3.IntegrityError):
            account_store.charge_run(self.account_id, "accepted-repeat", opening=self.opening(), accept_repeat=True)
        self.assertEqual(account_store.account_access(self.account_id)["spent_credits"], 10)
        self.assertEqual(len(recent_openings(self.account_id, paper_key(self.files))), 1)
        with account_store.connect_store(self.db_path) as db:
            db.execute("ALTER TABLE research_openings DROP CONSTRAINT reject_repeat" if postgres else "DROP TRIGGER reject_repeat")
        def accept(_):
            account_store.charge_run(self.account_id, "accepted-repeat", opening=self.opening(), accept_repeat=True)
        with ThreadPoolExecutor(max_workers=3) as pool:
            list(pool.map(accept, range(3)))
        self.assertEqual(account_store.account_access(self.account_id)["spent_credits"], 20)
        self.assertEqual(len(recent_openings(self.account_id, paper_key(self.files))), 2)
        with self.assertRaises(account_store.AccessError):
            account_store.charge_run(self.account_id, "accepted-repeat", opening=self.opening("An obsolete candidate?"), accept_repeat=True)

    def test_existing_run_schema_migrates_without_losing_funding(self):
        from backend import postgres_store
        account_store.reserve_run(self.account_id, "legacy-run")
        with account_store.connect_store(self.db_path) as db:
            db.execute("DROP TABLE research_openings")
            db.execute("ALTER TABLE defense_runs DROP COLUMN opening_commit")
            db.execute("ALTER TABLE live_runs DROP COLUMN opening_commit")
        postgres_store._initialized.clear()  # A new service process rechecks migrations.
        account_store.charge_run(self.account_id, "legacy-run", opening=self.opening())
        self.assertEqual(account_store.account_access(self.account_id)["test_credits"], 90)
        self.assertEqual(len(recent_openings(self.account_id, paper_key(self.files))), 1)

    def test_live_allocations_and_voucher_access_share_atomic_history_commit(self):
        from backend.live_store import LiveStore
        from backend.management_store import ManagementStore
        with patch.dict(os.environ, {"PAYMENTS_MODE": "live", "LIVE_PAID_STARTS_ENABLED": "1"}):
            store = LiveStore()
            store.start_service("history-service")
            ManagementStore().adjust(self.account_id, self.account_id, 30, "Offline fixture", "history-funding")
            store.reserve_run(self.account_id, "live-one", "history-service", "ROOM")
            account_store.charge_run(self.account_id, "live-one", opening=self.opening())
            account_store.charge_run(self.account_id, "live-one", opening=self.opening())
            self.assertEqual(store.overview(self.account_id)["live_credits"], 20)
            store.finish_run("live-one", "ended")
            store.reserve_run(self.account_id, "live-repeat", "history-service", "ROOM")
            with self.assertRaisesRegex(account_store.AccessError, "recent opening"):
                account_store.charge_run(self.account_id, "live-repeat", opening=self.opening())
            self.assertEqual(store.overview(self.account_id)["live_reserved_credits"], 10)
            store.release_run("live-repeat")
            self.assertEqual(store.overview(self.account_id)["live_credits"], 20)
            store.reserve_run(self.account_id, "live-repeat", "history-service", "ROOM")
            def accept(_):
                account_store.charge_run(self.account_id, "live-repeat", opening=self.opening(), accept_repeat=True)
            with ThreadPoolExecutor(max_workers=3) as pool:
                list(pool.map(accept, range(3)))
            self.assertEqual(store.overview(self.account_id)["live_credits"], 10)
            store.finish_run("live-repeat", "ended")
            with patch.dict(os.environ, {"FREE_ACCESS_VOUCHER": "history-voucher"}):
                account_store.redeem_voucher(self.account_id, "history-voucher")
                store.reserve_run(self.account_id, "live-free", "history-service", "ROOM")
                account_store.charge_run(self.account_id, "live-free", opening=self.opening("What limits the pilot?"))
            self.assertEqual(store.overview(self.account_id)["live_credits"], 10)
            self.assertEqual(len(recent_openings(self.account_id, paper_key(self.files))), 3)

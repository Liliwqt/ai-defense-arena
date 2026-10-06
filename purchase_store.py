"""Transactional sandbox purchases, independent of HTTP and the payment provider."""

from pathlib import Path
import secrets
import sqlite3
import time

from account_store import connect_store, token_hash

TEST_AMOUNT = 10_000
TEST_CREDITS = 100
CHECKOUT_WINDOW = 600
CHECKOUT_LIMIT = 5

# Sandbox top-up packages are server-owned: a caller may choose one by id but
# never its amount, currency, or credit count. Amount is in centavos.
PACKAGES = {"starter": {"amount": 10_000, "credits": 100}}


def package_for(package_id: str) -> dict:
    package = PACKAGES.get(package_id)
    if package is None:
        raise PurchaseError("unknown_package")
    return package


class PurchaseError(ValueError):
    def __init__(self, kind: str):
        self.kind = kind
        super().__init__(kind)


def purchase_history(db, account_id: str) -> list[dict]:
    """Use the caller's transaction so balance and receipts share a snapshot."""
    rows = db.execute("""SELECT o.id, o.provider, o.amount, o.currency, o.credits, o.status,
        o.created_at, o.paid_at, COALESCE(l.credits,0) AS awarded_credits
        FROM test_orders o LEFT JOIN test_credit_ledger l ON l.order_id=o.id
        WHERE o.account_id=? ORDER BY o.created_at DESC, o.id DESC LIMIT 20""", (account_id,)).fetchall()
    return [dict(row) for row in rows]


class PurchaseStore:
    def __init__(self, database: Path):
        self.database = database

    def begin(self, account_id: str, request_id: str, *, now: int | None = None) -> dict:
        return self._begin(account_id, request_id, TEST_AMOUNT, TEST_CREDITS, "checkout_session", now=now)

    def begin_topup(self, account_id: str, package_id: str, request_id: str, *, now: int | None = None) -> dict:
        package = package_for(package_id)
        return self._begin(account_id, request_id, package["amount"], package["credits"], "payment_intent", now=now)

    def _begin(self, account_id: str, request_id: str, amount: int, credits: int, provider: str, *, now: int | None) -> dict:
        now = int(time.time()) if now is None else now
        fingerprint = token_hash(account_id + ":" + request_id) if request_id else None
        with connect_store(self.database) as db:
            db.execute("BEGIN IMMEDIATE")
            if fingerprint:
                previous = db.execute("SELECT * FROM test_orders WHERE request_hash=?", (fingerprint,)).fetchone()
                if previous:
                    if previous["status"] in {"pending", "paid"}:
                        return dict(previous)
                    raise PurchaseError("creating" if previous["status"] == "creating" else "unverified")
            attempts = db.execute("SELECT count(*) FROM test_orders WHERE account_id=? AND created_at>?",
                                  (account_id, now - CHECKOUT_WINDOW)).fetchone()[0]
            if attempts >= CHECKOUT_LIMIT:
                raise PurchaseError("limited")
            order_id = "test_" + secrets.token_hex(16)
            # Retain the legacy capability column; new receipts are account-owned.
            db.execute("INSERT INTO test_orders (id, token_hash, amount, currency, status, created_at, account_id, credits, request_hash, provider) VALUES (?, ?, ?, 'PHP', 'creating', ?, ?, ?, ?, ?)",
                       (order_id, token_hash(secrets.token_urlsafe(32)), amount, now, account_id, credits, fingerprint, provider))
            return dict(db.execute("SELECT * FROM test_orders WHERE id=?", (order_id,)).fetchone())

    def creation_failed(self, order_id: str) -> None:
        with connect_store(self.database) as db:
            db.execute("UPDATE test_orders SET status='creation_failed' WHERE id=?", (order_id,))

    def register(self, order_id: str, checkout_id: str, checkout_url: str) -> dict:
        with connect_store(self.database) as db:
            db.execute("UPDATE test_orders SET checkout_id=?, checkout_url=?, status='pending' WHERE id=?", (checkout_id, checkout_url, order_id))
            return dict(db.execute("SELECT * FROM test_orders WHERE id=?", (order_id,)).fetchone())

    def register_topup(self, order_id: str, intent_id: str, qr_image_url: str, expires_at: int) -> dict:
        with connect_store(self.database) as db:
            db.execute("UPDATE test_orders SET intent_id=?, qr_image_url=?, expires_at=?, status='pending' WHERE id=?",
                       (intent_id, qr_image_url, expires_at, order_id))
            return dict(db.execute("SELECT * FROM test_orders WHERE id=?", (order_id,)).fetchone())

    def mark_topup_failed(self, order_id: str) -> None:
        self._set_topup_status(order_id, "failed")

    def mark_topup_expired(self, order_id: str) -> None:
        self._set_topup_status(order_id, "expired")

    def _set_topup_status(self, order_id: str, status: str) -> None:
        # A paid top-up is terminal; failures and expiries cannot reverse an award.
        with connect_store(self.database) as db:
            db.execute("UPDATE test_orders SET status=? WHERE id=? AND status IN ('creating', 'pending')", (status, order_id))

    def get(self, order_id: str) -> dict | None:
        with connect_store(self.database) as db:
            row = db.execute("SELECT * FROM test_orders WHERE id=?", (order_id,)).fetchone()
            return dict(row) if row is not None else None

    def history(self, account_id: str) -> list[dict]:
        with connect_store(self.database) as db:
            return purchase_history(db, account_id)

    def record_paid(self, order_id: str, checkout_id: str, payment_ids: list[str], *, now: int | None = None) -> None:
        """Reconcile a verified paid checkout event, atomically with its once-only award."""
        self._reconcile(order_id, "checkout_id", checkout_id, TEST_AMOUNT, "PHP", payment_ids, now)

    def record_topup_paid(self, order_id: str, intent_id: str, payment_ids: list[str], amount: int, currency: str = "PHP", *, now: int | None = None) -> None:
        """Reconcile a verified QR top-up payment, atomically with its once-only award."""
        self._reconcile(order_id, "intent_id", intent_id, amount, currency, payment_ids, now)

    def _reconcile(self, order_id: str, reference_field: str, reference: str, amount: int, currency: str,
                   payment_ids: list[str], now: int | None) -> None:
        now = int(time.time()) if now is None else now
        with connect_store(self.database) as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM test_orders WHERE id=?", (order_id,)).fetchone()
            if row is None:
                return  # An unrelated order from the provider account.
            if row["status"] == "creating":
                raise PurchaseError("registration_pending")
            if row[reference_field] != reference or row["amount"] != amount or row["currency"] != currency:
                raise PurchaseError("checkout_mismatch")
            self._award(db, row, payment_ids, now)

    @staticmethod
    def _award(db, row, payment_ids: list[str], now: int) -> None:
        if not payment_ids:
            raise PurchaseError("checkout_mismatch")
        try:
            if row["status"] == "pending":
                db.execute("UPDATE test_orders SET status='paid', payment_id=?, paid_at=? WHERE id=? AND status='pending'",
                           (payment_ids[0], now, row["id"]))
            elif row["status"] == "paid" and row["payment_id"] not in payment_ids:
                raise PurchaseError("payment_mismatch")
            if row["account_id"] is not None and row["credits"] > 0 and row["status"] in ("paid", "pending"):
                db.execute("INSERT INTO test_credit_ledger VALUES (?, ?, ?, ?) ON CONFLICT(order_id) DO NOTHING",
                           (row["id"], row["account_id"], row["credits"], now))
        except sqlite3.IntegrityError:
            raise PurchaseError("duplicate_payment") from None

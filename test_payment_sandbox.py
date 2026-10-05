"""Offline payment checks. PayMongo calls and webhook deliveries are mocked."""

import hashlib
import hmac
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import AsyncMock, Mock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
import httpx

import payments
import accounts
import account_store


class PaymentSandboxTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.database = Path(folder.name) / "receipts.sqlite3"
        environment = patch.dict(os.environ, {
            "PAYMONGO_SECRET_KEY": "sk_test_offline_fixture",
            "PAYMONGO_WEBHOOK_SECRET": "offline_webhook_secret",
            "PAYMONGO_PUBLIC_BASE_URL": "https://sandbox.example.com",
            "PAYMONGO_TEST_DB_PATH": str(self.database),
            "GAME_HOST_PASSCODE": "offline_host_passcode",
            "GOOGLE_CLIENT_ID": "offline-client",
            "GOOGLE_CLIENT_SECRET": "offline-google-secret",
            "AUTH_SESSION_SECRET": "offline-oauth-cookie-secret-with-32-characters",
            "AUTH_PUBLIC_BASE_URL": "http://127.0.0.1:8774",
        })
        environment.start()
        self.addCleanup(environment.stop)
        clock = patch.object(payments.time, "time", return_value=1_800_000_000)
        clock.start()
        self.addCleanup(clock.stop)
        app = FastAPI()
        app.include_router(payments.router)
        self.client = TestClient(app, base_url="http://127.0.0.1:8774")
        self.client.__enter__()
        self.addCleanup(lambda: self.client.__exit__(None, None, None))
        self.session_token, self.csrf = account_store.create_google_session("offline-google-sub", "alex@example.test", "Alex")
        self.client.cookies.set(accounts.ACCOUNT_COOKIE, self.session_token)
        self.client.headers.update({"Origin": "http://127.0.0.1:8774", "X-CSRF-Token": self.csrf})
        self.provider = AsyncMock()
        self.result = Mock()
        self.result.json.return_value = {"data": {"id": "cs_offline", "type": "checkout_session", "attributes": {
            "livemode": False, "checkout_url": "https://checkout.paymongo.com/offline",
        }}}
        self.provider.post.return_value = self.result
        provider_patch = patch.object(payments.httpx, "AsyncClient")
        provider_class = provider_patch.start()
        provider_class.return_value.__aenter__.return_value = self.provider
        self.addCleanup(provider_patch.stop)

    def create(self, **extra):
        return self.client.post("/api/payments/test/checkout", json={**extra})

    def status(self, created, token=None):
        return self.client.get("/api/payments/test/orders/" + created["order"]["id"],
                               headers={"Authorization": "Bearer " + (token or created["order_token"])})

    def event(self, created):
        return {"event_type": "send.webhook", "data": {
            "type": "checkout_session.payment.paid", "livemode": False,
            "data": {"id": "cs_offline", "type": "checkout_session", "attributes": {
                "reference_number": created["order"]["id"],
                "payments": [{"id": "pay_offline", "attributes": {"amount": 10000, "currency": "PHP", "status": "paid"}}],
            }},
        }}

    def deliver(self, event, timestamp="1800000000", signature_mode="te"):
        raw = json.dumps(event).encode()
        digest = hmac.new(b"offline_webhook_secret", timestamp.encode() + b"." + raw, hashlib.sha256).hexdigest()
        signature = f"t={timestamp},{signature_mode}={digest}"
        return self.client.post("/api/payments/test/webhook", content=raw, headers={"Paymongo-Signature": signature})

    def test_disabled_config_and_live_keys_never_call_provider(self):
        for key in ("", "sk_live_disallowed"):
            with patch.dict(os.environ, {"PAYMONGO_SECRET_KEY": key}):
                result = self.client.get("/api/payments/test/config")
                self.assertFalse(result.json()["enabled"])
                self.assertEqual(self.create().status_code, 503)
        self.provider.post.assert_not_called()
        with payments.connect_store(self.database) as db:
            self.assertEqual(db.execute("SELECT count(*) FROM test_orders").fetchone()[0], 0)

    def test_removed_passcode_and_client_amount_rejected(self):
        result = self.client.post("/api/payments/test/checkout", json={"host_passcode": "wrong"})
        self.assertEqual(result.status_code, 422)
        self.assertEqual(self.create(amount=1).status_code, 422)
        self.provider.post.assert_not_called()

    def test_base_url_is_server_owned_and_validated(self):
        for origin in ("http://example.com", "https://example.com/path", "https://user:password@example.com", "https://example.com/?override=yes", "https://[invalid", "https://example.com:bad"):
            with patch.dict(os.environ, {"PAYMONGO_PUBLIC_BASE_URL": origin}):
                self.assertEqual(self.create().status_code, 503)
        self.provider.post.assert_not_called()

    def test_checkout_server_amount_reference_and_no_secret_exposure(self):
        result = self.create()
        self.assertEqual(result.status_code, 201, result.text)
        created = result.json()
        self.assertEqual(created["order"]["status"], "pending")
        kwargs = self.provider.post.call_args.kwargs
        attrs = kwargs["json"]["data"]["attributes"]
        self.assertEqual(attrs["line_items"][0]["amount"], 10000)
        self.assertEqual(attrs["reference_number"], created["order"]["id"])
        self.assertEqual(attrs["payment_method_types"], ["qrph"])
        self.assertEqual(kwargs["auth"], ("sk_test_offline_fixture", ""))
        self.assertNotIn(created["order_token"], attrs["success_url"])
        self.assertNotIn("offline_host_passcode", result.text)
        self.assertNotIn("sk_test", result.text)
        self.assertEqual(result.headers["cache-control"], "no-store")
        with payments.connect_store(self.database) as db:
            stored = dict(db.execute("SELECT * FROM test_orders").fetchone())
        self.assertNotIn(created["order_token"], json.dumps(stored))

    def test_owned_status_requires_account_and_survives_new_client(self):
        created = self.create().json()
        self.assertEqual(self.status(created).status_code, 200)
        self.assertEqual(self.status(created, "other-token").status_code, 200)
        url = "/api/payments/test/orders/" + created["order"]["id"]
        self.assertEqual(self.client.get(url).status_code, 200)
        with TestClient(self.client.app, base_url="http://127.0.0.1:8774") as another:
            self.assertEqual(another.get(url, headers={"Authorization": "Bearer " + created["order_token"]}).status_code, 401)
            another.cookies.set(accounts.ACCOUNT_COOKIE, self.session_token)
            self.assertEqual(another.get(url).json()["order"]["status"], "pending")

    def test_api_failure_safe_no_retry(self):
        self.provider.post.side_effect = httpx.ReadTimeout("Secret provider diagnostic")
        result = self.create()
        self.assertEqual(result.status_code, 502)
        self.assertNotIn("Secret provider diagnostic", result.text)
        self.provider.post.assert_awaited_once()
        with payments.connect_store(self.database) as db:
            self.assertEqual(db.execute("SELECT status FROM test_orders").fetchone()[0], "creation_failed")

    def test_live_or_untrusted_checkout_response_rejected(self):
        for attrs in (
            {"livemode": True, "checkout_url": "https://checkout.paymongo.com/offline"},
            {"livemode": False, "checkout_url": "https://checkout.paymongo.com.evil.test"},
            {"livemode": False, "checkout_url": "javascript:alert(1)"},
            {"livemode": False, "checkout_url": "https://user:secret@checkout.paymongo.com"},
        ):
            self.result.json.return_value["data"]["attributes"] = attrs
            self.assertEqual(self.create().status_code, 502)

    def test_signed_webhook_marks_paid_once(self):
        created = self.create().json()
        event = self.event(created)
        self.assertEqual(self.deliver(event).status_code, 200)
        self.assertEqual(self.status(created).json()["order"]["status"], "paid")
        first = self.status(created).json()
        self.assertEqual(self.deliver(event).status_code, 200)
        self.assertEqual(self.status(created).json(), first)
        with payments.connect_store(self.database) as db:
            self.assertEqual(db.execute("SELECT count(*) FROM test_orders WHERE status='paid'").fetchone()[0], 1)

    def test_classic_resource_envelope(self):
        created = self.create().json()
        current = self.event(created)["data"]
        classic = {"data": {"id": "evt_offline", "type": "event", "attributes": {
            "livemode": False, "type": current["type"], "resource": current["data"],
        }}}
        self.assertEqual(self.deliver(classic).status_code, 200)
        self.assertEqual(self.status(created).json()["order"]["status"], "paid")

    def test_missing_invalid_stale_and_live_signatures_rejected(self):
        created = self.create().json()
        event = self.event(created)
        self.assertEqual(self.client.post("/api/payments/test/webhook", json=event).status_code, 401)
        self.assertEqual(self.deliver(event, timestamp="1799999600").status_code, 401)
        self.assertEqual(self.deliver(event, signature_mode="li").status_code, 401)
        self.assertEqual(self.status(created).json()["order"]["status"], "pending")

    def test_signature_uses_exact_raw_body(self):
        created = self.create().json()
        raw = json.dumps(self.event(created)).encode()
        digest = hmac.new(b"offline_webhook_secret", b"1800000000." + raw, hashlib.sha256).hexdigest()
        result = self.client.post("/api/payments/test/webhook", content=raw + b" ", headers={"Paymongo-Signature": "t=1800000000,te=" + digest})
        self.assertEqual(result.status_code, 401)

    def test_live_events_and_payment_mismatches_leave_pending(self):
        created = self.create().json()
        changes = [
            lambda e: e["data"].update(livemode=True),
            lambda e: e["data"]["data"].update(id="cs_other"),
            lambda e: e["data"]["data"]["attributes"]["payments"][0]["attributes"].update(amount=1),
            lambda e: e["data"]["data"]["attributes"]["payments"][0]["attributes"].update(currency="USD"),
            lambda e: e["data"]["data"]["attributes"]["payments"][0]["attributes"].update(status="pending"),
            lambda e: e["data"]["data"]["attributes"]["payments"][0]["attributes"].update(livemode=True),
        ]
        for change in changes:
            event = self.event(created)
            change(event)
            self.assertEqual(self.deliver(event).status_code, 400)
            self.assertEqual(self.status(created).json()["order"]["status"], "pending")

    def test_unrelated_event_and_other_order_do_not_fulfill(self):
        created = self.create().json()
        event = self.event(created)
        event["data"]["type"] = "payment.failed"
        self.assertEqual(self.deliver(event).status_code, 200)
        event = self.event(created)
        event["data"]["data"]["attributes"]["reference_number"] = "unrelated_order"
        self.assertEqual(self.deliver(event).status_code, 200)
        self.assertEqual(self.status(created).json()["order"]["status"], "pending")

    def test_early_delivery_requests_retry(self):
        created = self.create().json()
        with payments.connect_store(self.database) as db:
            db.execute("UPDATE test_orders SET status='creating', checkout_id=NULL")
        self.assertEqual(self.deliver(self.event(created)).status_code, 503)

    def test_duplicate_payment_cannot_pay_a_second_order(self):
        first = self.create().json()
        self.assertEqual(self.deliver(self.event(first)).status_code, 200)
        self.result.json.return_value["data"]["id"] = "cs_second"
        second = self.create().json()
        event = self.event(second)
        event["data"]["data"]["id"] = "cs_second"
        self.assertEqual(self.deliver(event).status_code, 400)
        self.assertEqual(self.status(first).json()["order"]["status"], "paid")
        self.assertEqual(self.status(second).json()["order"]["status"], "pending")

    def test_invalid_raw_body_and_repeated_signature_fields(self):
        raw = b"not json"
        digest = hmac.new(b"offline_webhook_secret", b"1800000000." + raw, hashlib.sha256).hexdigest()
        signature = "t=1800000000,te=" + digest
        result = self.client.post("/api/payments/test/webhook", content=raw, headers={"Paymongo-Signature": signature})
        self.assertEqual(result.status_code, 400)
        result = self.client.post("/api/payments/test/webhook", content=raw, headers={"Paymongo-Signature": signature + ",t=1800000000"})
        self.assertEqual(result.status_code, 401)

    def test_non_ascii_signature_is_a_safe_rejection(self):
        from fastapi import HTTPException
        with self.assertRaises(HTTPException) as raised:
            payments.verify_signature(b"{}", "t=1800000000,te=\u00e9", "secret", 1_800_000_000)
        self.assertEqual(raised.exception.status_code, 401)


if __name__ == "__main__":
    unittest.main()

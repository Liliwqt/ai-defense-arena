"""Offline payment checks. PayMongo calls and webhook deliveries are mocked."""

import hashlib
import hmac
import json
import os
from concurrent.futures import ThreadPoolExecutor
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

    def create(self, *, request_id=None, **extra):
        return self.client.post("/api/payments/test/checkout", json={**extra}, headers={"Idempotency-Key":request_id} if request_id else {})

    def topup(self, request_id="offline-topup-request", **extra):
        return self.client.post("/api/payments/test/topups", json={"package_id": "starter", **extra},
                                headers={"Idempotency-Key": request_id} if request_id else {})

    def qr_responses(self):
        image = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a1uoAAAAASUVORK5CYII="
        attrs = {"livemode": False, "amount": 10000, "currency": "PHP"}
        resources = [
            {"id": "pi_offline", "type": "payment_intent", "attributes": {**attrs, "client_key": "pi_offline_client_secret", "status": "awaiting_payment_method"}},
            {"id": "pm_offline", "type": "payment_method", "attributes": {"livemode": False, "type": "qrph"}},
            {"id": "pi_offline", "type": "payment_intent", "attributes": {**attrs, "status": "awaiting_next_action", "next_action": {"code": {"image_url": image}}}},
        ]
        results = [Mock() for _ in resources]
        for result, resource in zip(results, resources):
            result.json.return_value = {"data": resource}
        self.provider.post.side_effect = results
        return resources

    def test_topup_returns_qr_for_server_package_without_awarding_credits(self):
        resources = self.qr_responses()
        result = self.topup()
        self.assertEqual(result.status_code, 201, result.text)
        topup = result.json()["topup"]
        self.assertTrue(topup["id"].startswith("test_"))
        self.assertEqual((topup["amount"], topup["currency"], topup["credits"]), (10000, "PHP", 100))
        self.assertEqual(topup["qr_image_url"], resources[2]["attributes"]["next_action"]["code"]["image_url"])
        self.assertEqual(topup["expires_at"], 1800001800)
        self.assertEqual(topup["status"], "pending")
        self.assertEqual(result.headers["Cache-Control"], "no-store")
        self.assertEqual(self.provider.post.await_count, 3)
        calls = self.provider.post.await_args_list
        self.assertEqual(calls[0].args[0], "https://api.paymongo.com/v1/payment_intents")
        attributes = calls[0].kwargs["json"]["data"]["attributes"]
        self.assertEqual((attributes["amount"], attributes["currency"], attributes["payment_method_allowed"]), (10000, "PHP", ["qrph"]))
        self.assertEqual(attributes["metadata"]["topup_id"], topup["id"])
        self.assertIn(topup["id"], attributes["description"])
        self.assertEqual(calls[1].args[0], "https://api.paymongo.com/v1/payment_methods")
        self.assertEqual(calls[1].kwargs["json"]["data"]["attributes"], {"type": "qrph", "expiry_seconds": 1800})
        self.assertEqual(calls[2].args[0], "https://api.paymongo.com/v1/payment_intents/pi_offline/attach")
        self.assertEqual(calls[2].kwargs["json"]["data"]["attributes"], {"payment_method": "pm_offline", "client_key": "pi_offline_client_secret"})
        for call in calls:
            self.assertEqual(call.kwargs["auth"], ("sk_test_offline_fixture", ""))
        self.assertNotIn("client_key", result.text)
        self.assertNotIn("pi_offline_client_secret", result.text)
        self.assertNotIn("sk_test_", result.text)
        overview = account_store.account_overview(account_store.session_account(self.session_token)["id"])
        self.assertEqual(overview["test_credits"], 0)

    def test_topup_replay_reuses_qr_without_more_provider_calls(self):
        self.qr_responses()
        first = self.topup()
        second = self.topup()
        self.assertEqual((first.status_code, second.status_code), (201, 200))
        self.assertEqual(first.json(), second.json())
        self.assertEqual(self.provider.post.await_count, 3)

    def test_topup_normalizes_plain_base64_png_for_display(self):
        resources = self.qr_responses()
        image = resources[2]["attributes"]["next_action"]["code"]["image_url"]
        resources[2]["attributes"]["next_action"]["code"]["image_url"] = image.split(",", 1)[1]
        result = self.topup()
        self.assertEqual(result.status_code, 201, result.text)
        self.assertEqual(result.json()["topup"]["qr_image_url"], image)

    def test_topup_creation_concurrent_request_is_once_only(self):
        self.qr_responses()
        with ThreadPoolExecutor(max_workers=4) as workers:
            results = list(workers.map(lambda _: self.topup(), range(4)))
        self.assertEqual(sum(result.status_code == 201 for result in results), 1)
        self.assertTrue(all(result.status_code in {200, 201, 409} for result in results))
        self.assertEqual(self.provider.post.await_count, 3)
        self.assertEqual(self.topup().status_code, 200)

    def test_topup_rejects_client_financial_fields_and_unknown_package(self):
        for field in ("amount", "currency", "credits", "account_id"):
            with self.subTest(field=field):
                self.assertEqual(self.topup(**{field: 1}).status_code, 422)
        for package in ("missing", "", 1, None):
            with self.subTest(package=package):
                self.assertIn(self.topup(package_id=package).status_code, {400, 422})
        self.provider.post.assert_not_called()

    def test_topup_requires_request_id_and_authenticated_csrf(self):
        for request_id in ("", "short", "invalid request key", "x" * 129):
            self.assertEqual(self.topup(request_id=request_id).status_code, 400)
        del self.client.headers["X-CSRF-Token"]
        self.assertEqual(self.topup().status_code, 403)
        self.client.cookies.clear()
        self.assertEqual(self.topup().status_code, 401)
        self.provider.post.assert_not_called()

    def test_topup_disabled_configuration_makes_no_provider_requests(self):
        for name, value in (("PAYMONGO_SECRET_KEY", ""), ("PAYMONGO_SECRET_KEY", "sk_live_disallowed"),
                            ("PAYMONGO_WEBHOOK_SECRET", ""), ("PAYMONGO_PUBLIC_BASE_URL", "")):
            with self.subTest(setting=name, value=value), patch.dict(os.environ, {name: value}):
                self.assertEqual(self.topup().status_code, 503)
        self.provider.post.assert_not_called()

    def test_topup_and_checkout_request_ids_are_isolated(self):
        checkout = self.create(request_id="shared-checkout-topup-request").json()["order"]
        self.qr_responses()
        topup = self.topup(request_id="shared-checkout-topup-request").json()["topup"]
        self.assertNotEqual(checkout["id"], topup["id"])
        self.assertEqual(self.topup(request_id="shared-checkout-topup-request").json()["topup"], topup)
        self.provider.post.side_effect = None
        self.assertEqual(self.create(request_id="shared-checkout-topup-request").json()["order"], checkout)
        self.assertEqual(self.provider.post.await_count, 4)

    def test_topup_failure_at_each_provider_step_is_safe_and_not_recreated(self):
        for stage in range(3):
            with self.subTest(stage=stage):
                self.qr_responses()
                results = list(self.provider.post.side_effect)
                results[stage] = httpx.ConnectError("private provider details")
                self.provider.post.side_effect = results
                before = self.provider.post.await_count
                request_id = "failed-topup-step-" + str(stage)
                failed = self.topup(request_id=request_id)
                self.assertEqual(failed.status_code, 502)
                self.assertNotIn("private provider details", failed.text)
                self.assertEqual(self.topup(request_id=request_id).status_code, 409)
                self.assertEqual(self.provider.post.await_count - before, stage + 1)
        overview = account_store.account_overview(account_store.session_account(self.session_token)["id"])
        self.assertEqual(overview["test_credits"], 0)
        self.assertTrue(all(order["status"] == "creation_failed" for order in overview["orders"]))

    def test_topup_rejects_live_provider_resources_at_each_step(self):
        for stage in range(3):
            with self.subTest(stage=stage):
                resources = self.qr_responses()
                resources[stage]["attributes"]["livemode"] = True
                before = self.provider.post.await_count
                self.assertEqual(self.topup(request_id="live-response-step-" + str(stage)).status_code, 502)
                self.assertEqual(self.provider.post.await_count - before, stage + 1)

    def test_topup_expired_local_deadline_does_not_confirm_payment(self):
        self.qr_responses()
        created = self.topup().json()["topup"]
        with patch.object(payments.time, "time", return_value=1_800_002_000):
            replay = self.topup().json()["topup"]
        self.assertEqual(replay, created)
        self.assertEqual(replay["status"], "pending")
        self.assertEqual(self.provider.post.await_count, 3)

    def test_topup_request_reuse_is_account_owned(self):
        self.qr_responses()
        first = self.topup().json()["topup"]
        token, csrf = account_store.create_google_session("other-qr-sub", "other@example.test", "Other")
        self.client.cookies.set(accounts.ACCOUNT_COOKIE, token)
        self.client.headers["X-CSRF-Token"] = csrf
        resources = self.qr_responses()
        resources[0]["id"] = resources[2]["id"] = "pi_other"
        second = self.topup().json()["topup"]
        self.assertNotEqual(first["id"], second["id"])
        self.assertEqual(self.provider.post.await_count, 6)
        overview = account_store.account_overview(account_store.session_account(token)["id"])
        self.assertEqual([order["id"] for order in overview["orders"]], [second["id"]])

    def test_topup_rejects_unsafe_or_invalid_qr_images(self):
        images = ["https://attacker.example/qr.png", "data:image/svg+xml;base64,PHN2Zy8+",
                  "data:image/png;base64,not-base64!", "data:image/png;base64,aGVsbG8=", "A" * 1_000_001]
        for index, image in enumerate(images):
            with self.subTest(image=index):
                resources = self.qr_responses()
                resources[2]["attributes"]["next_action"]["code"]["image_url"] = image
                result = self.topup(request_id="invalid-qr-image-" + str(index))
                self.assertEqual(result.status_code, 502)
                self.assertNotIn(image, result.text)

    def test_topup_rejects_wrong_intent_amount_currency_and_identity(self):
        changes = [(0, "amount", 1), (0, "currency", "USD"), (2, "amount", "10000"),
                   (2, "currency", "USD"), (2, "status", "succeeded")]
        for index, (stage, field, value) in enumerate(changes):
            with self.subTest(stage=stage, field=field):
                resources = self.qr_responses()
                resources[stage]["attributes"][field] = value
                result = self.topup(request_id="invalid-intent-fields-" + str(index))
                self.assertEqual(result.status_code, 502)
        overview = account_store.account_overview(account_store.session_account(self.session_token)["id"])
        self.assertEqual(overview["test_credits"], 0)

    def test_topup_rejects_malformed_resources_and_invalid_attachment(self):
        for index in range(5):
            with self.subTest(case=index):
                resources = self.qr_responses()
                if index == 0:
                    resources[0]["id"] = "pi_bad/../../outside"
                elif index == 1:
                    resources[0]["attributes"]["client_key"] = ""
                elif index == 2:
                    resources[1]["attributes"]["type"] = "card"
                elif index == 3:
                    resources[2]["id"] = "pi_unrelated"
                else:
                    resources[2]["attributes"]["next_action"] = None
                self.assertEqual(self.topup(request_id="malformed-qr-response-" + str(index)).status_code, 502)

    def test_topup_http_error_is_sanitized_and_throttle_preserves_replay(self):
        self.qr_responses()
        created = self.topup().json()
        for index in range(4):
            resources = self.qr_responses()
            results = list(self.provider.post.side_effect)
            results[0].raise_for_status.side_effect = httpx.HTTPStatusError(
                "private provider diagnostic", request=httpx.Request("POST", "https://api.paymongo.com"),
                response=httpx.Response(400))
            self.provider.post.side_effect = results
            failed = self.topup(request_id="qr-provider-http-error-" + str(index))
            self.assertEqual(failed.status_code, 502)
            self.assertNotIn("private provider diagnostic", failed.text)
        before = self.provider.post.await_count
        result = self.topup(request_id="qr-over-throttle-limit")
        self.assertEqual(result.status_code, 429)
        self.assertEqual(result.headers["Retry-After"], "600")
        self.assertEqual(self.topup().json(), created)
        self.assertEqual(self.provider.post.await_count, before)

    def status(self, created, token=None):
        return self.client.get("/api/payments/test/orders/" + created["order"]["id"],
                               headers={"Authorization": "Bearer " + (token or "unused-legacy-token")})

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

    def test_same_checkout_request_reuses_order_without_provider_call(self):
        key = "offline-idempotency-key"
        first = self.create(request_id=key)
        second = self.create(request_id=key)
        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(first.json(), second.json())
        self.provider.post.assert_awaited_once()
        with payments.connect_store(self.database) as db:
            row = db.execute('SELECT request_hash FROM test_orders').fetchone()
            self.assertNotEqual(row[0], key)
            self.assertEqual(db.execute('SELECT count(*) FROM test_orders').fetchone()[0], 1)

    def test_concurrent_same_key_cannot_create_duplicate_checkouts(self):
        with ThreadPoolExecutor(max_workers=4) as workers:
            results = list(workers.map(lambda _: self.create(request_id='concurrent-checkout-key'), range(4)))
        self.assertEqual(sum(result.status_code == 201 for result in results), 1)
        self.assertTrue(all(result.status_code in {200, 201, 409} for result in results))
        self.provider.post.assert_awaited_once()
        self.assertEqual(self.create(request_id='concurrent-checkout-key').status_code, 200)

    def test_unverified_and_inflight_checkout_are_not_automatically_recreated(self):
        key = 'inflight-checkout-key'
        self.create(request_id=key)
        for status in ('creating', 'creation_failed'):
            with payments.connect_store(self.database) as db:
                db.execute('UPDATE test_orders SET status=?', (status,))
            self.assertEqual(self.create(request_id=key).status_code, 409)
        self.provider.post.assert_awaited_once()

    def test_idempotency_is_account_scoped_and_invalid_ids_rejected(self):
        self.assertEqual(self.create(request_id='bad\nkey').status_code, 400)
        first = self.create(request_id='account-scoped-checkout').json()
        token, csrf = account_store.create_google_session('other-sub', 'other@example.test', 'Other')
        self.client.cookies.set(accounts.ACCOUNT_COOKIE, token)
        self.client.headers['X-CSRF-Token'] = csrf
        self.result.json.return_value['data']['id'] = 'cs_other_account'
        second = self.create(request_id='account-scoped-checkout').json()
        self.assertNotEqual(first['order']['id'], second['order']['id'])
        self.assertEqual(self.provider.post.await_count, 2)

    def test_checkout_throttle_persists_and_does_not_block_existing_receipt(self):
        for index in range(payments.CHECKOUT_LIMIT):
            self.result.json.return_value['data']['id'] = 'cs_throttle_' + str(index)
            self.assertEqual(self.create(request_id='throttle-request-key-' + str(index)).status_code, 201)
        limited = self.create(request_id='new-throttle-request-key')
        self.assertEqual(limited.status_code, 429)
        self.assertEqual(limited.headers['Retry-After'], '600')
        self.assertEqual(self.create(request_id='throttle-request-key-0').status_code, 200)
        self.assertEqual(self.provider.post.await_count, payments.CHECKOUT_LIMIT)

    def test_paid_receipt_rejects_a_different_payment_identifier(self):
        created = self.create().json()
        self.assertEqual(self.deliver(self.event(created)).status_code, 200)
        event = self.event(created)
        event['data']['data']['attributes']['payments'][0]['id'] = 'pay_different'
        self.assertEqual(self.deliver(event).status_code, 400)
        self.assertEqual(self.status(created).json()['order']['status'], 'paid')

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

    def test_native_checkout_returns_to_app_without_confirming_payment(self):
        result = self.client.post("/api/payments/test/checkout", json={}, headers={"X-Arena-Native":"1"})
        self.assertEqual(result.status_code, 201, result.text)
        attributes = self.provider.post.call_args.kwargs["json"]["data"]["attributes"]
        self.assertEqual(attributes["success_url"], "https://sandbox.example.com/api/payments/test/mobile-return")
        self.assertEqual(attributes["cancel_url"], attributes["success_url"])
        page = self.client.get("/api/payments/test/mobile-return?status=paid")
        self.assertEqual(page.status_code, 200)
        self.assertIn('defensearena://payment-return', page.text)
        self.assertIn('does not confirm payment', page.text)
        order = result.json()["order"]
        checked = self.client.get("/api/payments/test/orders/" + order["id"])
        self.assertEqual(checked.json()["order"]["status"], "pending")

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
        self.assertNotIn("order_token", result.text)
        self.assertNotIn("offline_host_passcode", result.text)
        self.assertNotIn("sk_test", result.text)
        self.assertEqual(result.headers["cache-control"], "no-store")
        with payments.connect_store(self.database) as db:
            stored = dict(db.execute("SELECT * FROM test_orders").fetchone())
        self.assertNotIn("order_token", created)

    def test_owned_status_requires_account_and_survives_new_client(self):
        created = self.create().json()
        self.assertEqual(self.status(created).status_code, 200)
        self.assertEqual(self.status(created, "other-token").status_code, 200)
        url = "/api/payments/test/orders/" + created["order"]["id"]
        self.assertEqual(self.client.get(url).status_code, 200)
        with TestClient(self.client.app, base_url="http://127.0.0.1:8774") as another:
            self.assertEqual(another.get(url, headers={"Authorization": "Bearer unused-legacy-token"}).status_code, 401)
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

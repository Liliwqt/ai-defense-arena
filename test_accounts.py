"""Offline Google OIDC and account-owned credit checks; all providers mocked."""

from concurrent.futures import ThreadPoolExecutor
import hashlib
import hmac
import importlib
import json
import logging
import os
from pathlib import Path
import sqlite3
import tempfile
import time
import unittest
from unittest.mock import AsyncMock, Mock, patch
from urllib.parse import parse_qs, urlsplit

from authlib.integrations.starlette_client import OAuth
from authlib.integrations.httpx_client import AsyncOAuth2Client
from fastapi import FastAPI
from fastapi.testclient import TestClient
from joserfc import jwt
from joserfc.jwk import RSAKey

import accounts
import account_store
import payments
import payment_audit

# Authlib 1.8 uses HTTPX 2; earlier supported releases use HTTPX 1. Return
# fixture responses/streams from the same HTTP client as the real OAuth code.
provider_http = importlib.import_module(next(base.__module__ for base in AsyncOAuth2Client.__mro__ if base.__name__ == "AsyncClient").split(".")[0])


class AccountCreditTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.db_path = Path(folder.name) / "sandbox.sqlite3"
        self.origin = "http://127.0.0.1:8774"
        env = patch.dict(os.environ, {
            "GOOGLE_CLIENT_ID": "offline-google-client", "GOOGLE_CLIENT_SECRET": "offline-google-secret",
            "AUTH_PUBLIC_BASE_URL": self.origin, "AUTH_SESSION_SECRET": "offline-session-secret-with-more-than-32-characters",
            "PAYMONGO_SECRET_KEY": "sk_test_offline", "PAYMONGO_WEBHOOK_SECRET": "offline-webhook-secret",
            "PAYMONGO_PUBLIC_BASE_URL": self.origin, "PAYMONGO_TEST_DB_PATH": str(self.db_path),
            "GAME_HOST_PASSCODE": "offline-host-passcode",
        })
        env.start()
        self.addCleanup(env.stop)
        self.clock = int(time.time())
        clock = patch.object(account_store.time, "time", side_effect=lambda: self.clock)
        clock.start()
        self.addCleanup(clock.stop)
        app = FastAPI()
        accounts.configure_auth(app)
        app.include_router(payments.router)
        self.client = TestClient(app, base_url=self.origin)
        self.client.__enter__()
        self.addCleanup(lambda: self.client.__exit__(None, None, None))
        self.key = RSAKey.generate_key(2048, parameters={"kid": "offline-key"})
        self.override_claims = {}
        self.signing_key = self.key
        self.nonce = ""
        self.intent_by_topup = {}
        self.token_requests = 0
        self.google = OAuth().register("google", client_id="offline-google-client", client_secret="offline-google-secret",
            server_metadata_url=accounts.GOOGLE_METADATA,
            client_kwargs={"scope": "openid email profile", "code_challenge_method": "S256", "transport": provider_http.MockTransport(self.google_response)})
        google_patch = patch.object(accounts, "google_client", return_value=self.google)
        google_patch.start()
        self.addCleanup(google_patch.stop)

    def google_response(self, request):
        if str(request.url) == accounts.GOOGLE_METADATA:
            return provider_http.Response(200, json={"issuer": "https://accounts.google.com",
                "authorization_endpoint": "https://accounts.google.com/o/oauth2/v2/auth",
                "token_endpoint": "https://oauth2.googleapis.com/token", "jwks_uri": "https://www.googleapis.com/offline-jwks",
                "id_token_signing_alg_values_supported": ["RS256"]})
        if request.url.path == "/token":
            self.token_requests += 1
            params = parse_qs(request.content.decode())
            self.assertIn("code_verifier", params)
            claims = {"iss": "https://accounts.google.com", "aud": "offline-google-client",
                "sub": "offline-google-sub", "email": "alex@example.test", "name": "Alex", "email_verified": True,
                "nonce": self.nonce, "iat": self.clock, "exp": self.clock + 3600, **self.override_claims}
            encoded = jwt.encode({"alg": "RS256", "kid": "offline-key"}, claims, self.signing_key)
            return provider_http.Response(200, json={"access_token": "offline-google-access-token", "token_type": "Bearer", "expires_in": 3600, "id_token": encoded})
        if request.url.path == "/offline-jwks":
            return provider_http.Response(200, json={"keys": [self.key.as_dict(private=False)]})
        raise AssertionError("Unexpected Google fixture request")

    def google_login(self, client=None, return_to="/"):
        client = client or self.client
        start = client.get("/api/auth/google/login", params={"return_to":return_to}, follow_redirects=False)
        self.assertEqual(start.status_code, 302, start.text)
        params = parse_qs(urlsplit(start.headers["location"]).query)
        self.nonce = params["nonce"][0]
        self.assertEqual(params["code_challenge_method"], ["S256"])
        result = client.get("/api/auth/google/callback", params={"code": "offline-code", "state": params["state"][0]}, follow_redirects=False)
        return result, params

    def sign_in_fixture(self, sub="fixture-sub", client=None):
        client = client or self.client
        token, csrf = account_store.create_google_session(sub, sub + "@example.test", sub)
        client.cookies.set(accounts.ACCOUNT_COOKIE, token)
        client.headers.update({"Origin": self.origin, "X-CSRF-Token": csrf})
        return token, csrf

    def topup(self, client=None, **extra):
        client = client or self.client
        intent = "pi_" + os.urandom(8).hex()
        attrs = {"livemode": False, "amount": 10000, "currency": "PHP"}
        image = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a1uoAAAAASUVORK5CYII="
        resources = [
            {"id": intent, "type": "payment_intent", "attributes": {**attrs, "client_key": "offline-client-key", "status": "awaiting_payment_method"}},
            {"id": "pm_offline", "type": "payment_method", "attributes": {"livemode": False, "type": "qrph"}},
            {"id": intent, "type": "payment_intent", "attributes": {**attrs, "status": "awaiting_next_action", "next_action": {"code": {"image_url": image}}}},
        ]
        results = [Mock() for _ in resources]
        for result, resource in zip(results, resources):
            result.json.return_value = {"data": resource}
        provider = AsyncMock()
        provider.post.side_effect = results
        with patch.object(payments.httpx, "AsyncClient") as factory:
            factory.return_value.__aenter__.return_value = provider
            response = client.post("/api/payments/test/topups", json={"package_id": "starter", **extra},
                headers={"Idempotency-Key": "offline-topup-" + os.urandom(8).hex()})
        if response.status_code == 201:
            self.intent_by_topup[response.json()["topup"]["id"]] = intent
        return response

    def webhook(self, order, client=None):
        body = {"data": {"type": "payment.paid", "livemode": False, "data": {
            "id": "pay_" + order["id"], "type": "payment", "attributes": {
                "livemode": False, "payment_intent_id": self.intent_by_topup[order["id"]],
                "metadata": {"topup_id": order["id"]}, "status": "paid", "amount": 10000, "currency": "PHP"}}}}
        raw = json.dumps(body).encode()
        stamp = str(self.clock)
        digest = hmac.new(b"offline-webhook-secret", stamp.encode() + b"." + raw, hashlib.sha256).hexdigest()
        return (client or self.client).post("/api/payments/test/webhook", content=raw,
            headers={"Paymongo-Signature": f"t={stamp},te={digest}"})

    def test_login_returns_only_to_allowlisted_app_screens(self):
        for target in ('/', '/?account=1', '/?payments=test', '//evil.test', 'https://evil.test', '/?next=evil'):
            with self.subTest(target=target):
                result,_=self.google_login(return_to=target)
                self.assertEqual(result.headers['location'], target if target in ('/', '/?account=1', '/?payments=test') else '/')

    def test_real_oidc_library_validates_fixture_and_sets_private_session(self):
        result, params = self.google_login()
        self.assertEqual(result.headers["location"], "/")
        self.assertEqual(self.token_requests, 1)
        cookie = result.headers["set-cookie"]
        self.assertIn("HttpOnly", cookie)
        self.assertIn("SameSite=lax", cookie)
        identity = self.client.get("/api/auth/me").json()
        self.assertTrue(identity["authenticated"])
        self.assertEqual(identity["user"]["email"], "alex@example.test")
        self.assertEqual(identity["test_credits"], 0)
        with account_store.connect_store(self.db_path) as db:
            saved = json.dumps([dict(row) for row in db.execute("SELECT * FROM account_sessions")])
        self.assertNotIn(self.client.cookies.get(accounts.ACCOUNT_COOKIE), saved)
        self.assertNotIn("offline-google-access-token", saved)
        replay = self.client.get("/api/auth/google/callback", params={"code": "offline-code", "state": params["state"][0]}, follow_redirects=False)
        self.assertIn("signin_error=failed", replay.headers["location"])
        self.assertEqual(self.token_requests, 1)

    def test_invalid_issuer_audience_nonce_expiry_and_email_rejected(self):
        for override in ({"iss": "https://evil.example"}, {"aud": "other-client"}, {"nonce": "different-nonce"}, {"exp": self.clock - 1000}, {"email_verified": False}):
            with self.subTest(override=override):
                self.override_claims = override
                result, _ = self.google_login()
                self.assertIn("signin_error=failed", result.headers["location"])
                self.assertFalse(self.client.get("/api/auth/me").json()["authenticated"])

    def test_invalid_google_signature_is_rejected(self):
        self.signing_key = RSAKey.generate_key(2048, parameters={"kid": "offline-key"})
        result, _ = self.google_login()
        self.assertIn("signin_error=failed", result.headers["location"])
        self.assertFalse(self.client.get("/api/auth/me").json()["authenticated"])

    def test_https_origin_uses_secure_session_cookies(self):
        with patch.dict(os.environ, {"AUTH_PUBLIC_BASE_URL": "https://arena.example.test"}):
            app = FastAPI()
            accounts.configure_auth(app)
            with TestClient(app, base_url="https://arena.example.test") as client:
                start = client.get("/api/auth/google/login", follow_redirects=False)
                self.assertIn("secure", start.headers["set-cookie"].lower())
                params = parse_qs(urlsplit(start.headers["location"]).query)
                self.assertEqual(params["redirect_uri"], ["https://arena.example.test/api/auth/google/callback"])
                self.nonce = params["nonce"][0]
                result = client.get("/api/auth/google/callback", params={"code": "offline-code", "state": params["state"][0]}, follow_redirects=False)
                self.assertIn("Secure", result.headers["set-cookie"])
                self.assertTrue(client.get("/api/auth/me").json()["authenticated"])

    def test_missing_state_or_configuration_fails_closed(self):
        result = self.client.get("/api/auth/google/callback?code=offline-code&state=unknown", follow_redirects=False)
        self.assertIn("signin_error=failed", result.headers["location"])
        self.assertEqual(self.token_requests, 0)
        with patch.dict(os.environ, {"GOOGLE_CLIENT_SECRET": ""}):
            self.assertFalse(self.client.get("/api/auth/me").json()["google_enabled"])
            self.assertEqual(self.client.get("/api/auth/google/login").status_code, 503)

    def test_google_subject_not_email_controls_identity(self):
        account_store.create_google_session("subject-one", "same@example.test", "Alex")
        account_store.create_google_session("subject-one", "renamed@example.test", "Alex New")
        account_store.create_google_session("subject-two", "same@example.test", "Sam")
        with account_store.connect_store(self.db_path) as db:
            self.assertEqual(db.execute("SELECT count(*) FROM accounts").fetchone()[0], 2)
            self.assertEqual(db.execute("SELECT email FROM accounts WHERE google_sub='subject-one'").fetchone()[0], "renamed@example.test")

    def test_logout_revokes_session_and_checks_csrf_origin(self):
        token, _ = self.sign_in_fixture()
        self.assertEqual(self.client.post("/api/auth/logout", headers={"Origin": "https://evil.example"}).status_code, 403)
        self.assertEqual(self.client.post("/api/auth/logout", headers={"X-CSRF-Token": "wrong"}).status_code, 403)
        self.assertEqual(self.client.post("/api/auth/logout").status_code, 200)
        self.assertIsNone(account_store.session_account(token))
        self.assertFalse(self.client.get("/api/auth/me").json()["authenticated"])

    def test_expired_session_cannot_read_account_or_purchase(self):
        self.sign_in_fixture()
        self.clock += account_store.SESSION_SECONDS + 1
        self.assertFalse(self.client.get("/api/auth/me").json()["authenticated"])
        self.assertEqual(self.topup().status_code, 401)

    def test_topup_requires_session_csrf_and_server_owned_credit_pack(self):
        self.assertEqual(self.topup().status_code, 401)
        self.sign_in_fixture()
        self.assertEqual(self.client.post("/api/payments/test/topups", json={"package_id": "starter"}, headers={"X-CSRF-Token": "wrong"}).status_code, 403)
        self.assertEqual(self.topup(credits=99999).status_code, 422)
        self.assertEqual(self.topup(account_id="another").status_code, 422)
        created = self.topup().json()
        self.assertEqual(created["topup"]["credits"], 100)

    def test_signed_payment_awards_once_to_owner_without_browser(self):
        self.sign_in_fixture()
        order = self.topup().json()["topup"]
        owner = self.client.get("/api/auth/me").json()["user"]["id"]
        self.assertEqual(self.client.get("/api/auth/me").json()["test_credits"], 0)
        self.client.post("/api/auth/logout")
        self.assertEqual(self.webhook(order).status_code, 200)
        self.assertEqual(self.webhook(order).status_code, 200)
        with account_store.connect_store(self.db_path) as db:
            rows = db.execute("SELECT * FROM test_credit_ledger").fetchall()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["account_id"], owner)
        self.assertEqual(rows[0]["credits"], 100)
        self.sign_in_fixture()
        self.assertEqual(self.client.get("/api/auth/me").json()["test_credits"], 100)

    def test_two_users_have_private_orders_balances_and_history(self):
        self.sign_in_fixture("alex")
        created = self.topup().json()
        self.assertEqual(self.webhook(created["topup"]).status_code, 200)
        with TestClient(self.client.app, base_url=self.origin) as sam:
            self.sign_in_fixture("sam", sam)
            response = sam.get("/api/payments/test/topups/" + created["topup"]["id"], headers={"Authorization": "Bearer unused-legacy-token"})
            self.assertEqual(response.status_code, 404)
            self.assertEqual(sam.get("/api/auth/me").json()["test_credits"], 0)
            self.assertEqual(sam.get("/api/auth/me").json()["orders"], [])
        self.assertEqual(self.client.get("/api/auth/me").json()["test_credits"], 100)

    def test_concurrent_duplicate_webhooks_do_not_duplicate_credits(self):
        self.sign_in_fixture()
        order = self.topup().json()["topup"]
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: self.webhook(order), range(2)))
        self.assertTrue(all(result.status_code == 200 for result in results))
        self.assertEqual(self.client.get("/api/auth/me").json()["test_credits"], 100)

    def test_credit_failure_rolls_back_payment_until_retry(self):
        self.sign_in_fixture()
        order = self.topup().json()["topup"]
        with account_store.connect_store(self.db_path) as db:
            db.execute("CREATE TRIGGER reject_credit BEFORE INSERT ON test_credit_ledger BEGIN SELECT RAISE(ABORT, 'offline failure'); END")
        self.assertEqual(self.webhook(order).status_code, 400)
        self.assertEqual(self.client.get("/api/payments/test/topups/" + order["id"]).json()["topup"]["status"], "pending")
        self.assertEqual(self.client.get("/api/auth/me").json()["test_credits"], 0)
        with account_store.connect_store(self.db_path) as db:
            db.execute("DROP TRIGGER reject_credit")
        self.assertEqual(self.webhook(order).status_code, 200)
        self.assertEqual(self.client.get("/api/auth/me").json()["test_credits"], 100)

    def test_private_history_tracks_verified_awards_reservation_release_and_charge(self):
        token, _ = self.sign_in_fixture()
        account_id = account_store.session_account(token)['id']
        order = self.topup().json()['topup']
        pending = self.client.get('/api/auth/me').json()
        self.assertEqual(pending['orders'][0]['awarded_credits'], 0)
        self.webhook(order)
        account_store.reserve_run(account_id, 'released-run')
        self.assertEqual(self.client.get('/api/auth/me').json()['reserved_credits'], 10)
        account_store.release_run('released-run')
        account_store.reserve_run(account_id, 'charged-run')
        account_store.charge_run(account_id, 'charged-run')
        saved = self.client.get('/api/auth/me').json()
        self.assertEqual(saved['orders'][0]['awarded_credits'], 100)
        self.assertEqual(saved['test_credits'], 90)
        self.assertEqual(saved['spent_credits'], 10)
        self.assertEqual({run['status'] for run in saved['runs']}, {'charged','released'})
        self.sign_in_fixture('other-account')
        private = self.client.get('/api/auth/me').json()
        self.assertEqual(private['runs'], [])
        self.assertEqual(private['orders'], [])

    def test_audit_reports_consistent_totals_without_private_identifiers(self):
        token, _ = self.sign_in_fixture()
        account_id = account_store.session_account(token)['id']
        order = self.topup().json()['topup']; self.webhook(order)
        account_store.reserve_run(account_id, 'charged-run')
        account_store.charge_run(account_id, 'charged-run')
        result = payment_audit.audit_store()
        self.assertTrue(result['ok'])
        self.assertEqual(result['awarded_test_credits'], 100)
        self.assertEqual(result['charged_test_credits'], 10)
        self.assertNotIn(account_id, json.dumps(result))
        self.assertNotIn(order['id'], json.dumps(result))
        self.assertNotIn('example.test', json.dumps(result))

    def test_audit_detects_inconsistent_awards_and_negative_balance_without_repair(self):
        token, _ = self.sign_in_fixture()
        account_id = account_store.session_account(token)['id']
        order = self.topup().json()['topup']; self.webhook(order)
        account_store.reserve_run(account_id, 'charged-run')
        account_store.charge_run(account_id, 'charged-run')
        with account_store.connect_store(self.db_path) as db:
            db.execute('DELETE FROM test_credit_ledger')
        result = payment_audit.audit_store()
        self.assertFalse(result['ok'])
        self.assertEqual(result['problems']['paid_purchases_without_award'], 1)
        self.assertEqual(result['problems']['negative_available_balances'], 1)
        with account_store.connect_store(self.db_path) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM test_credit_ledger').fetchone()[0], 0)

    def test_audit_detects_award_mismatch(self):
        self.sign_in_fixture()
        order = self.topup().json()['topup']; self.webhook(order)
        with account_store.connect_store(self.db_path) as db:
            db.execute('UPDATE test_credit_ledger SET credits=50')
        self.assertEqual(payment_audit.audit_store()['problems']['awards_not_matching_paid_purchase'], 1)

    def test_existing_receipt_migration_preserves_anonymous_paid_record(self):
        with sqlite3.connect(self.db_path) as db:
            db.execute("""CREATE TABLE test_orders (id TEXT PRIMARY KEY, token_hash TEXT NOT NULL, checkout_id TEXT UNIQUE,
                checkout_url TEXT, amount INTEGER NOT NULL, currency TEXT NOT NULL, status TEXT NOT NULL,
                payment_id TEXT UNIQUE, created_at INTEGER NOT NULL, paid_at INTEGER)""")
            db.execute("INSERT INTO test_orders VALUES ('legacy', ?, 'cs_legacy', 'https://checkout.paymongo.com/legacy', 10000, 'PHP', 'paid', 'pay_legacy', ?, ?)",
                (account_store.token_hash("legacy-token"), self.clock, self.clock))
        self.sign_in_fixture()
        result = self.client.get("/api/payments/test/orders/legacy", headers={"Authorization": "Bearer legacy-token"})
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json()["order"]["credits"], 0)
        self.assertEqual(self.client.get("/api/auth/me").json()["test_credits"], 0)
        self.assertEqual(self.client.get("/api/auth/me").json()["orders"], [])

    def test_callback_access_log_redacts_code_and_state(self):
        record = logging.LogRecord("uvicorn.access", logging.INFO, "", 0, '%s - "%s %s HTTP/%s" %d',
            ("client", "GET", "/api/auth/google/callback?code=private-code&state=private-state", "1.1", 303), None)
        accounts.HideGoogleCallbackQuery().filter(record)
        self.assertNotIn("private-code", record.getMessage())
        self.assertNotIn("private-state", record.getMessage())


    def test_mobile_login_establishes_cookie_only_after_verifier_exchange(self):
        import base64
        verifier = "A" * 64
        challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
        start = self.client.post("/api/auth/mobile/start", json={"challenge": challenge, "return_to": "/?account=1"})
        self.assertEqual(start.status_code, 200, start.text)
        flow = start.json()["flow"]
        login = self.client.get(start.json()["login_url"], follow_redirects=False)
        params = parse_qs(urlsplit(login.headers["location"]).query)
        self.nonce = params["nonce"][0]
        returned = self.client.get("/api/auth/google/callback", params={"code": "offline-code", "state": params["state"][0]}, follow_redirects=False)
        self.assertNotIn(accounts.ACCOUNT_COOKIE, self.client.cookies)
        result = urlsplit(returned.headers["location"])
        self.assertEqual((result.scheme, result.netloc), ("defensearena", "auth"))
        code = parse_qs(result.query)["code"][0]
        wrong = self.client.post("/api/auth/mobile/complete", json={"flow": flow, "code": code, "verifier": "B" * 64})
        self.assertEqual(wrong.status_code, 400)
        exchanged = self.client.post("/api/auth/mobile/complete", json={"flow": flow, "code": code, "verifier": verifier})
        self.assertEqual(exchanged.status_code, 200, exchanged.text)
        self.assertEqual(exchanged.json(), {"return_to": "/?account=1"})
        self.assertIn("httponly", exchanged.headers["set-cookie"].lower())
        self.assertTrue(self.client.get("/api/auth/me").json()["authenticated"])
        replay = self.client.post("/api/auth/mobile/complete", json={"flow": flow, "code": code, "verifier": verifier})
        self.assertEqual(replay.status_code, 400)

    def mobile_fixture_return(self, verifier="C" * 64):
        import base64
        challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
        start = self.client.post("/api/auth/mobile/start", json={"challenge": challenge}).json()
        redirect = self.client.get(start["login_url"], follow_redirects=False)
        params = parse_qs(urlsplit(redirect.headers["location"]).query)
        self.nonce = params["nonce"][0]
        callback = self.client.get("/api/auth/google/callback", params={"code":"offline-code", "state":params["state"][0]}, follow_redirects=False)
        code = parse_qs(urlsplit(callback.headers["location"]).query)["code"][0]
        return {"flow":start["flow"], "code":code, "verifier":verifier}

    def test_mobile_expiry_does_not_create_an_account_session(self):
        import mobile_auth
        now = [1000.0]
        with patch.object(mobile_auth.time, "monotonic", side_effect=lambda: now[0]):
            body = self.mobile_fixture_return()
            now[0] += mobile_auth.TTL_SECONDS + 1
            self.assertEqual(self.client.post("/api/auth/mobile/complete", json=body).status_code, 400)
            self.assertFalse(self.client.get("/api/auth/me").json()["authenticated"])

    def test_mobile_concurrent_exchange_issues_only_one_session(self):
        body = self.mobile_fixture_return()
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: self.client.post("/api/auth/mobile/complete", json=body).status_code, range(2)))
        self.assertEqual(sorted(results), [200, 400])

    def test_mobile_rejects_foreign_flow_bad_targets_and_identity(self):
        self.assertEqual(self.client.post("/api/auth/mobile/start", json={"challenge":"x" * 43, "return_to":"https://evil.example"}).status_code, 400)
        self.assertEqual(self.client.post("/api/auth/mobile/start", json={"challenge":"short"}).status_code, 422)
        body = self.mobile_fixture_return()
        wrong = {**body, "flow":"Z" * 43}
        self.assertEqual(self.client.post("/api/auth/mobile/complete", json=wrong).status_code, 400)
        self.assertFalse(self.client.get("/api/auth/me").json()["authenticated"])
        self.override_claims = {"email_verified":False}
        import base64
        challenge = base64.urlsafe_b64encode(hashlib.sha256(b"D" * 64).digest()).decode().rstrip("=")
        start = self.client.post("/api/auth/mobile/start", json={"challenge":challenge}).json()
        redirect = self.client.get(start["login_url"], follow_redirects=False)
        params = parse_qs(urlsplit(redirect.headers["location"]).query)
        self.nonce = params["nonce"][0]
        callback = self.client.get("/api/auth/google/callback", params={"code":"offline-code", "state":params["state"][0]}, follow_redirects=False)
        self.assertEqual(callback.headers["location"], "defensearena://auth?error=signin_failed")
        self.assertFalse(self.client.get("/api/auth/me").json()["authenticated"])

    def test_mobile_secure_cookie_logout_and_original_owner_boundaries(self):
        with patch.dict(os.environ, {"AUTH_PUBLIC_BASE_URL":"https://arena.example.test"}):
            original = self.client
            with TestClient(self.client.app, base_url="https://arena.example.test") as secure_client:
                self.client = secure_client
                try:
                    body = self.mobile_fixture_return()
                    result = self.client.post("/api/auth/mobile/complete", json=body)
                    self.assertIn("Secure", result.headers["set-cookie"])
                    self.assertIn("HttpOnly", result.headers["set-cookie"])
                    self.assertTrue(self.client.get("/api/auth/me").json()["authenticated"])
                finally:
                    self.client = original
        # Same local fixture boundary exercises revocation and CSRF after handoff.
        body = self.mobile_fixture_return("E" * 64)
        self.assertEqual(self.client.post("/api/auth/mobile/complete", json=body).status_code, 200)
        account = self.client.get("/api/auth/me").json()
        self.assertEqual(self.client.post("/api/auth/logout").status_code, 403)
        self.assertEqual(self.client.post("/api/auth/logout", headers={"Origin":self.origin,"X-CSRF-Token":account["csrf_token"]}).status_code, 200)
        self.assertFalse(self.client.get("/api/auth/me").json()["authenticated"])

    def test_mobile_authenticated_host_and_guests_use_existing_room_permissions(self):
        import game_server
        self.client.app.router.routes.extend(route for route in game_server.app.router.routes if getattr(route, "path", "") in {"/api/rooms", "/api/rooms/{code}/join", "/ws/{code}"})
        body = self.mobile_fixture_return()
        self.assertEqual(self.client.post("/api/auth/mobile/complete", json=body).status_code, 200)
        account = self.client.get("/api/auth/me").json()
        headers = {"Origin":self.origin,"X-CSRF-Token":account["csrf_token"]}
        self.assertEqual(self.client.post("/api/rooms", data={"host_name":"Alex"}, files={"files":("queue.py",b"queue = []")}).status_code, 403)
        created = self.client.post("/api/rooms", data={"host_name":"Alex"}, files={"files":("queue.py",b"queue = []")}, headers=headers)
        self.assertEqual(created.status_code, 201, created.text)
        room = created.json()
        self.addCleanup(lambda: game_server.rooms.pop(room["room_code"], None))
        with self.client.websocket_connect(self.origin.replace("http", "ws", 1) + "/ws/" + room["room_code"], headers={"Origin":self.origin}) as socket:
            socket.send_json({"type":"hello","token":room["player_token"]})
            first = socket.receive_json()
            self.assertEqual(first["type"], "snapshot", first.get("message"))
            state = first["state"]
            self.assertTrue(state["self_is_host"])
            self.assertNotIn(account["user"]["email"], json.dumps(state))
            self.assertNotIn(account["csrf_token"], json.dumps(state))
        with TestClient(self.client.app, base_url=self.origin) as guest:
            joined = guest.post("/api/rooms/"+room["room_code"]+"/join",json={"name":"Sam"})
            self.assertEqual(joined.status_code, 200)
            with guest.websocket_connect("/ws/"+room["room_code"], headers={"Origin":self.origin}) as socket:
                socket.send_json({"type":"hello","token":joined.json()["player_token"]})
                self.assertFalse(socket.receive_json()["state"]["self_is_host"])
            with guest.websocket_connect("/ws/"+room["room_code"], headers={"Origin":self.origin}) as socket:
                socket.send_json({"type":"hello","token":room["player_token"]})
                self.assertEqual(socket.receive_json()["type"], "error")


if __name__ == "__main__":
    unittest.main()

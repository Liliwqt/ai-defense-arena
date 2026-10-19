"""Offline local access checks against the real room/account HTTP boundaries."""

import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.local_dev import configure_environment, create_app
from tests.test_research_plan import PAPER
from tests.test_openrouter_questions import HTTPClient
from tests.test_openrouter_streamlit import SyntheticRouter
import httpx


class LocalDevelopmentTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {}, clear=True)
        self.env.start()
        self.addCleanup(self.env.stop)
        self.folder = TemporaryDirectory(prefix="local-access-test-")
        self.addCleanup(self.folder.cleanup)
        self.origin = configure_environment(Path(self.folder.name), 8001)
        from backend import game_server
        game_server.rooms.clear()
        self.addCleanup(game_server.rooms.clear)
        self.client = self.enterContext(TestClient(create_app(), base_url=self.origin,
                                                   client=("127.0.0.1", 50000)))

    def login(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("httponly", response.headers["set-cookie"].lower())
        self.assertIn("samesite=strict", response.headers["set-cookie"].lower())
        return self.client.get("/api/auth/me").json()

    def test_automatic_free_host_creates_room_with_csrf_and_keeps_session(self):
        account = self.login()
        self.assertTrue(account["authenticated"])
        self.assertTrue(account["free_access"])
        self.assertEqual(account["test_credits"], 0)
        self.assertEqual(account["user"]["name"], "Local tester")
        self.assertNotIn("set-cookie", self.client.get("/").headers)
        denied = self.client.post("/api/rooms", data={"host_name": "Alex", "defense_type": "research", "practice_tier": "free"},
                                  files={"research_files": ("study.md", PAPER.encode(), "text/markdown")})
        self.assertEqual(denied.status_code, 403)
        created = self.client.post("/api/rooms", data={"host_name": "Alex", "defense_type": "research", "practice_tier": "free"},
            files={"research_files": ("study.md", PAPER.encode(), "text/markdown")},
            headers={"origin": self.origin, "x-csrf-token": account["csrf_token"]})
        self.assertEqual(created.status_code, 201, created.text)
        code = created.json()["room_code"]
        guest = TestClient(self.client.app, base_url=self.origin, client=("127.0.0.1", 50001))
        self.addCleanup(guest.close)
        joined = guest.post(f"/api/rooms/{code}/join", json={"name": "Sam"})
        self.assertEqual(joined.status_code, 200, joined.text)

    def test_remote_host_origins_and_proxy_headers_are_rejected(self):
        for headers in ({"host": "example.com"}, {"origin": "https://example.com"},
                        {"x-forwarded-for": "127.0.0.1"}, {"forwarded": "for=127.0.0.1"}):
            with self.subTest(headers=headers):
                self.assertEqual(self.client.get("/", headers=headers).status_code, 403)
        remote = TestClient(self.client.app, base_url=self.origin, client=("203.0.113.5", 50000))
        self.addCleanup(remote.close)
        self.assertEqual(remote.get("/").status_code, 403)

    def test_google_and_payments_are_disabled(self):
        self.login()
        for path in ("/api/auth/google/login", "/api/auth/mobile/start", "/api/payments/live/config",
                     "/api/payments/test/config"):
            self.assertEqual(self.client.get(path).status_code, 403)

    def test_free_host_can_start_with_a_guest_without_charging(self):
        from backend.practice_tiers import FREE_MODEL
        account = self.login()
        host = self.client.post("/api/rooms",
            data={"host_name": "Alex", "defense_type": "research", "practice_tier": "free"},
            files={"research_files": ("study.md", PAPER.encode(), "text/markdown")},
            headers={"origin": self.origin, "x-csrf-token": account["csrf_token"]}).json()
        guest = self.client.post(f"/api/rooms/{host['room_code']}/join", json={"name": "Sam"}).json()
        router = SyntheticRouter()

        def until(socket, **conditions):
            for _ in range(50):
                message = socket.receive_json()
                self.assertNotEqual(message["type"], "error", message)
                state = message["state"]
                if state["phase"] == "retry":
                    self.fail(state["error"])
                if all(state.get(key) == value for key, value in conditions.items()):
                    return state
            self.fail("Missing local research room state.")

        def provider(request):
            response = router(request)
            return httpx.Response(response.status_code, content=response.content.replace(b'0.0005', b'0.0'))

        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "offline-placeholder"}), \
             patch("httpx.Client", side_effect=lambda **kw: HTTPClient(transport=httpx.MockTransport(provider))), \
             self.client.websocket_connect(f"ws://127.0.0.1:8001/ws/{host['room_code']}", headers={"origin": self.origin}) as socket:
            socket.send_json({"type": "hello", "token": host["player_token"]})
            until(socket, phase="lobby")
            socket.send_json({"type": "prepare_research_plan"})
            state = until(socket, research_planning_status="ready")
            plan_id = state["research_plan"]["id"]
            socket.send_json({"type": "approve_research_plan", "plan_id": plan_id,
                "question_budget": 4, "confirm_profile": True})
            until(socket, research_plan_approved=True)
            socket.send_json({"type": "start", "plan_id": plan_id, "question_budget": 4})
            state = until(socket, phase="voting")
            self.assertEqual(len(state["players"]), 2)
            self.assertEqual(state["practice_tier"], "free")
        self.assertTrue(all(body['model'] == FREE_MODEL for body in router.calls))
        self.assertIn("player_token", guest)
        refreshed = self.client.get("/api/auth/me").json()
        self.assertTrue(refreshed["free_access"])
        self.assertEqual(refreshed["test_credits"], 0)
        self.assertEqual(refreshed["reserved_credits"], 0)

    def test_isolation_and_hosted_start_rejection(self):
        with patch.dict(os.environ, {"DATABASE_URL": "private-database", "PAYMONGO_LIVE_SECRET_KEY": "private-key",
                                     "PAYMONGO_SECRET_KEY": "private-test-key", "OPENROUTER_API_KEY": "offline-key"}):
            configure_environment(Path(self.folder.name), 8001)
            self.assertNotIn("DATABASE_URL", os.environ)
            self.assertNotIn("PAYMONGO_LIVE_SECRET_KEY", os.environ)
            self.assertNotIn("PAYMONGO_SECRET_KEY", os.environ)
            self.assertEqual(os.environ["OPENROUTER_API_KEY"], "offline-key")
            self.assertEqual(os.environ["PAYMENTS_MODE"], "test")
            self.assertEqual(os.environ["PAYMONGO_TEST_DB_PATH"], str(Path(self.folder.name) / "accounts.sqlite3"))
        with patch.dict(os.environ, {"RENDER": "true"}):
            with self.assertRaises(RuntimeError):
                configure_environment(Path(self.folder.name), 8001)
            with self.assertRaises(RuntimeError):
                create_app()
        with patch.dict(os.environ, {"LOCAL_DEV_ACCESS": "0"}):
            with self.assertRaises(RuntimeError):
                create_app()

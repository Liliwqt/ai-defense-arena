"""Bounded, one-time browser-to-WebView login handoffs. No provider tokens."""

from dataclasses import dataclass
import base64
import hashlib
import hmac
import secrets
import threading
import time
from urllib.parse import urlencode

from fastapi import HTTPException

RETURN_URL = "defensearena://auth"
TTL_SECONDS = 300
MAX_PENDING = 128


@dataclass
class Handoff:
    challenge: str
    target: str
    expires: float
    opened: bool = False
    identity: tuple[str, str, str] | None = None
    code_hash: str | None = None


class MobileHandoffs:
    def __init__(self):
        self._pending: dict[str, Handoff] = {}
        self._lock = threading.Lock()

    def _get(self, flow: str) -> Handoff:
        now = time.monotonic()
        self._pending = {key: value for key, value in self._pending.items() if value.expires > now}
        value = self._pending.get(flow)
        if value is None:
            raise HTTPException(400, "Sign-in expired or unavailable. Start sign-in again in the app.")
        return value

    def start(self, challenge: str, target: str) -> str:
        with self._lock:
            now = time.monotonic()
            self._pending = {key: value for key, value in self._pending.items() if value.expires > now}
            if len(self._pending) >= MAX_PENDING:
                raise HTTPException(429, "Sign-in is busy. Try again shortly.")
            flow = secrets.token_urlsafe(32)
            self._pending[flow] = Handoff(challenge, target, now + TTL_SECONDS)
            return flow

    def open(self, flow: str):
        with self._lock:
            value = self._get(flow)
            if value.opened:
                raise HTTPException(400, "Start a new sign-in in the app.")
            value.opened = True

    def verified_return(self, flow: str, identity: tuple[str, str, str]) -> str:
        with self._lock:
            value = self._get(flow)
            if not value.opened or value.identity is not None:
                raise HTTPException(400, "Start a new sign-in in the app.")
            code = secrets.token_urlsafe(32)
            value.identity = identity
            value.code_hash = hashlib.sha256(code.encode()).hexdigest()
            return RETURN_URL + "?" + urlencode({"flow": flow, "code": code})

    def consume(self, flow: str, code: str, verifier: str, issue_session):
        # Issuing and consuming happen under one lock, including concurrent
        # exchanges. A store failure leaves the handoff available for retry.
        challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
        with self._lock:
            value = self._get(flow)
            if value.identity is None or not hmac.compare_digest(value.challenge, challenge) or not hmac.compare_digest(value.code_hash or "", hashlib.sha256(code.encode()).hexdigest()):
                raise HTTPException(400, "Sign-in could not be verified. Start again in the app.")
            session, _ = issue_session(*value.identity)
            del self._pending[flow]
            return session, value.target


handoffs = MobileHandoffs()

"""Account-owned, duplicate-safe PayMongo sandbox checkout and credit awards."""

from dataclasses import dataclass
import hashlib
import hmac
import json
import os
from pathlib import Path
import secrets
import re
import sqlite3
import time
from urllib.parse import urlsplit

import httpx
from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict
from account_store import DEFAULT_DB, connect_store, token_hash
from accounts import check_csrf, require_account


router = APIRouter(prefix="/api/payments/test", tags=["test payments"])
TEST_AMOUNT = 10_000  # PHP 100.00 simulated, not a product price.
CHECKOUT_API = "https://api.paymongo.com/v2/checkout_sessions"
TEST_CREDITS = 100  # Sandbox fixture only, not production pricing.
CHECKOUT_WINDOW = 600
CHECKOUT_LIMIT = 5


@dataclass(frozen=True)
class Settings:
    key: str
    webhook_secret: str
    origin: str
    database: Path


def settings() -> Settings:
    key = os.environ.get("PAYMONGO_SECRET_KEY", "").strip()
    secret = os.environ.get("PAYMONGO_WEBHOOK_SECRET", "").strip()
    origin = os.environ.get("PAYMONGO_PUBLIC_BASE_URL", "").strip().rstrip("/")
    if not key.startswith("sk_test_") or not secret or not origin:
        raise HTTPException(503, "Configure a PayMongo test secret key, webhook secret, and public base URL on the server. Live keys are not accepted.")
    try:
        parsed = urlsplit(origin)
        parsed.port  # Also reject malformed ports/IPv6 in operator configuration.
    except ValueError:
        raise HTTPException(503, "The payment base URL is invalid.") from None
    local = parsed.hostname in {"localhost", "127.0.0.1"}
    if (parsed.scheme != "https" and not (parsed.scheme == "http" and local)) or not parsed.hostname or parsed.username or parsed.password or parsed.path or parsed.query or parsed.fragment:
        raise HTTPException(503, "The payment base URL must be an HTTPS origin, or localhost HTTP for local setup.")
    return Settings(key, secret, origin, Path(os.environ.get("PAYMONGO_TEST_DB_PATH", str(DEFAULT_DB))))


def public_order(row: sqlite3.Row) -> dict:
    return {key: row[key] for key in ("id", "amount", "currency", "status", "checkout_url", "created_at", "paid_at", "credits")} | {"mode": "test"}


def response(body: dict, status: int = 200) -> JSONResponse:
    return JSONResponse(body, status_code=status, headers={"Cache-Control": "no-store"})


@router.get("/config")
def payment_config():
    try:
        settings()
        ready = True
    except HTTPException:
        ready = False
    return response({"mode": "test", "enabled": ready, "amount": TEST_AMOUNT, "currency": "PHP", "credits": TEST_CREDITS})


class CheckoutRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")


@router.post("/checkout", status_code=201)
async def create_checkout(body: CheckoutRequest, request: Request, idempotency_key: str = Header(default="")):
    account = require_account(request)
    check_csrf(request, account)
    config = settings()
    if idempotency_key and not re.fullmatch(r"[A-Za-z0-9_-]{16,128}", idempotency_key):
        raise HTTPException(400, "Use a valid checkout request ID and try again.")
    request_hash = token_hash(account["id"] + ":" + idempotency_key) if idempotency_key else None
    order_id = "test_" + secrets.token_hex(16)
    with connect_store(config.database) as db:
        db.execute("BEGIN IMMEDIATE")
        if request_hash:
            previous = db.execute("SELECT * FROM test_orders WHERE request_hash=?", (request_hash,)).fetchone()
            if previous:
                if previous["status"] in {"pending", "paid"}:
                    return response({"order": public_order(previous)})
                if previous["status"] == "creating":
                    raise HTTPException(409, "This checkout is still being created. Keep the same request and try again shortly.")
                raise HTTPException(409, "The earlier checkout could not be verified. Check purchase history before explicitly starting a new attempt.")
        attempts = db.execute("SELECT count(*) FROM test_orders WHERE account_id=? AND created_at>?",
                              (account["id"], int(time.time()) - CHECKOUT_WINDOW)).fetchone()[0]
        if attempts >= CHECKOUT_LIMIT:
            raise HTTPException(429, "Too many checkout attempts. Wait ten minutes before creating another.", headers={"Retry-After": str(CHECKOUT_WINDOW)})
        # New purchases are account-owned. No browser bearer capability is needed;
        # token_hash remains populated only for legacy schema compatibility.
        db.execute("INSERT INTO test_orders (id, token_hash, amount, currency, status, created_at, account_id, credits, request_hash) VALUES (?, ?, ?, 'PHP', 'creating', ?, ?, ?, ?)",
                   (order_id, token_hash(secrets.token_urlsafe(32)), TEST_AMOUNT, int(time.time()), account["id"], TEST_CREDITS, request_hash))
    payload = {"data": {"attributes": {
        "line_items": [{"name": "AI Defense Arena sandbox test", "amount": TEST_AMOUNT, "currency": "PHP", "quantity": 1}],
        "payment_method_types": ["qrph"],
        "reference_number": order_id,
        "success_url": config.origin + "/?payments=test&payment_return=success",
        "cancel_url": config.origin + "/?payments=test&payment_return=cancel",
    }}}
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            result = await client.post(CHECKOUT_API, auth=(config.key, ""), json=payload)
            result.raise_for_status()
            resource = result.json()["data"]
        attrs = resource["attributes"]
        checkout_id, checkout_url = resource["id"], attrs["checkout_url"]
        url = urlsplit(checkout_url)
        if attrs.get("livemode") is not False or not isinstance(checkout_id, str) or not checkout_id.startswith("cs_") or url.scheme != "https" or url.hostname != "checkout.paymongo.com" or url.username or url.password or url.port not in (None, 443):
            raise ValueError("Invalid test checkout")
    except (httpx.HTTPError, ValueError, KeyError, TypeError, AttributeError):
        # A network failure can leave a provider checkout whose result is unknown.
        # Never automatically retry a creation request or infer payment success.
        with connect_store(config.database) as db:
            db.execute("UPDATE test_orders SET status='creation_failed' WHERE id=?", (order_id,))
        raise HTTPException(502, "Could not create a verified test checkout. Check your test key and connection; no payment was confirmed.") from None
    with connect_store(config.database) as db:
        db.execute("UPDATE test_orders SET checkout_id=?, checkout_url=?, status='pending' WHERE id=?", (checkout_id, checkout_url, order_id))
        row = db.execute("SELECT * FROM test_orders WHERE id=?", (order_id,)).fetchone()
    return response({"order": public_order(row)}, 201)


@router.get("/orders/{order_id}")
def get_order(order_id: str, request: Request, authorization: str = Header(default="")):
    config = settings()
    token = authorization.removeprefix("Bearer ") if authorization.startswith("Bearer ") else ""
    with connect_store(config.database) as db:
        row = db.execute("SELECT * FROM test_orders WHERE id=?", (order_id,)).fetchone()
    if row is None:
        raise HTTPException(404, "Test order not found. Use the browser that created it.")
    if row["account_id"] is not None:
        account = require_account(request)
        if row["account_id"] != account["id"]:
            raise HTTPException(404, "Test order not found.")
    elif not token or not hmac.compare_digest(row["token_hash"], token_hash(token)):
        raise HTTPException(404, "Test order not found. Use the browser that created it.")
    return response({"order": public_order(row)})


def verify_signature(raw: bytes, signature: str, secret: str, now: float) -> None:
    try:
        fields = {}
        for part in signature.split(","):
            name, value = part.strip().split("=", 1)
            if name in fields:
                raise ValueError("Repeated signature field")
            fields[name] = value
        timestamp = fields["t"]
        if abs(now - int(timestamp)) > 300:
            raise ValueError("Stale signature")
        computed = hmac.new(secret.encode(), timestamp.encode() + b"." + raw, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(computed, fields.get("te", "")):
            raise ValueError("Invalid test signature")
    except (KeyError, TypeError, ValueError):
        raise HTTPException(401, "Invalid or expired test webhook signature.") from None


def paid_session(body: dict) -> dict | None:
    """Support the current v2 envelope and the existing resource envelope."""
    try:
        event = body["data"]
        attrs = event["attributes"] if event.get("type") == "event" else event
        if attrs.get("livemode") is not False:
            raise ValueError("Only test events are accepted")
        if attrs["type"] != "checkout_session.payment.paid":
            return None
        session = attrs.get("data") or attrs.get("resource")
        if not isinstance(session, dict) or session.get("type") != "checkout_session" or session["attributes"].get("livemode") is True:
            raise ValueError("Invalid checkout session")
        return session
    except (KeyError, TypeError, AttributeError, ValueError):
        raise HTTPException(400, "Invalid test payment event.") from None


@router.post("/webhook")
async def receive_webhook(request: Request, paymongo_signature: str = Header(default="")):
    config = settings()
    raw = bytearray()
    async for chunk in request.stream():
        raw.extend(chunk)
        if len(raw) > 1_000_000:
            raise HTTPException(413, "Webhook is too large.")
    verify_signature(bytes(raw), paymongo_signature, config.webhook_secret, time.time())
    try:
        session = paid_session(json.loads(raw))
    except (ValueError, UnicodeDecodeError):
        raise HTTPException(400, "Invalid test payment event.") from None
    if session is None:
        return response({"received": True})
    try:
        attrs = session["attributes"]
        order_id, checkout_id = attrs["reference_number"], session["id"]
        payments = attrs["payments"]
        if not isinstance(order_id, str) or not isinstance(checkout_id, str) or not isinstance(payments, list):
            raise ValueError("Invalid payment fields")
        payment_ids = [payment["id"] for payment in payments
                       if isinstance(payment, dict) and isinstance(payment.get("attributes"), dict)
                       and payment["attributes"].get("status") == "paid"
                       and type(payment["attributes"].get("amount")) is int
                       and payment["attributes"]["amount"] == TEST_AMOUNT
                       and payment["attributes"].get("currency") == "PHP"
                       and payment["attributes"].get("livemode") is not True
                       and isinstance(payment.get("id"), str) and payment["id"].startswith("pay_")]
        if not payment_ids:
            raise ValueError("Amount or payment mismatch")
    except (KeyError, TypeError, ValueError):
        raise HTTPException(400, "Test payment details do not match the test order.") from None
    with connect_store(config.database) as db:
        # Immediate transaction serializes deliveries; duplicate notifications
        # cannot overwrite a paid receipt or award anything twice.
        db.execute("BEGIN IMMEDIATE")
        row = db.execute("SELECT * FROM test_orders WHERE id=?", (order_id,)).fetchone()
        if row is None:
            return response({"received": True})  # Other orders from the account.
        if row["status"] == "creating":
            raise HTTPException(503, "Checkout registration is pending; retry the webhook.")
        if row["checkout_id"] != checkout_id or row["amount"] != TEST_AMOUNT or row["currency"] != "PHP":
            raise HTTPException(400, "Test checkout does not match the order.")
        try:
            if row["status"] == "pending":
                db.execute("UPDATE test_orders SET status='paid', payment_id=?, paid_at=? WHERE id=? AND status='pending'",
                           (payment_ids[0], int(time.time()), order_id))
            elif row["status"] == "paid" and row["payment_id"] not in payment_ids:
                raise HTTPException(400, "Test payment does not match the recorded receipt.")
            if row["account_id"] is not None and row["credits"] > 0 and row["status"] in ("paid", "pending"):
                db.execute("INSERT INTO test_credit_ledger VALUES (?, ?, ?, ?) ON CONFLICT(order_id) DO NOTHING",
                           (order_id, row["account_id"], row["credits"], int(time.time())))
        except sqlite3.IntegrityError:
            raise HTTPException(400, "Test payment has already been recorded for another order.") from None
    return response({"received": True})

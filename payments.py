"""Account-owned, duplicate-safe PayMongo sandbox checkout and credit awards."""

from dataclasses import dataclass
import base64
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import sqlite3
import time
from urllib.parse import urlsplit

import httpx
from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, ConfigDict
from account_store import DEFAULT_DB, connect_store, token_hash
from purchase_store import PurchaseStore, PurchaseError, TEST_AMOUNT, TEST_CREDITS, CHECKOUT_WINDOW, CHECKOUT_LIMIT, is_simulated_topup
from accounts import check_csrf, require_account


router = APIRouter(prefix="/api/payments/test", tags=["test payments"])
CHECKOUT_API = "https://api.paymongo.com/v2/checkout_sessions"
PAYMENT_API = "https://api.paymongo.com/v1"
QR_EXPIRY_SECONDS = 1800


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


def purchase_http_error(error: PurchaseError) -> HTTPException:
    errors = {
        "creating": (409, "This checkout is still being created. Keep the same request and try again shortly."),
        "unverified": (409, "The earlier checkout could not be verified. Check purchase history before explicitly starting a new attempt."),
        "limited": (429, "Too many checkout attempts. Wait ten minutes before creating another."),
        "registration_pending": (503, "Checkout registration is pending; retry the webhook."),
        "checkout_mismatch": (400, "Test checkout does not match the order."),
        "payment_mismatch": (400, "Test payment does not match the recorded receipt."),
        "duplicate_payment": (400, "Test payment has already been recorded for another order."),
        "topup_not_found": (404, "Test top-up not found."),
        "simulation_unavailable": (409, "Sandbox simulation requires an active, fully created test QR. Create a new top-up to try again."),
    }
    status, message = errors[error.kind]
    return HTTPException(status, message, headers={"Retry-After": str(CHECKOUT_WINDOW)} if error.kind == "limited" else None)


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


class TopupRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    package_id: str


class SimulateTopupRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")


def public_topup(row: dict) -> dict:
    return {key: row[key] for key in ("id", "amount", "currency", "credits", "status",
                                    "qr_image_url", "expires_at", "created_at", "paid_at")} | {"mode": "test", "simulated": is_simulated_topup(row)}


def validated_test_intent(resource: dict, row: dict) -> dict:
    attrs = resource["attributes"]
    intent_id = resource["id"]
    if (resource.get("type") != "payment_intent" or not isinstance(intent_id, str)
            or not re.fullmatch(r"pi_[A-Za-z0-9_]+", intent_id) or attrs.get("livemode") is not False
            or type(attrs.get("amount")) is not int or attrs["amount"] != row["amount"]
            or attrs.get("currency") != row["currency"]):
        raise ValueError("Invalid test intent")
    return attrs


async def create_qr(client: httpx.AsyncClient, config: Settings, row: dict) -> tuple[str, str, int]:
    """Keep provider resources and credentials inside the payment boundary."""
    result = await client.post(PAYMENT_API + "/payment_intents", auth=(config.key, ""), json={"data": {"attributes": {
        "amount": row["amount"], "currency": row["currency"], "payment_method_allowed": ["qrph"],
        "description": "AI Defense Arena sandbox top-up " + row["id"], "metadata": {"topup_id": row["id"]},
    }}})
    result.raise_for_status()
    intent = result.json()["data"]
    attrs = validated_test_intent(intent, row)
    intent_id, client_key = intent["id"], attrs["client_key"]
    if (attrs.get("status") != "awaiting_payment_method"
            or not isinstance(client_key, str) or not client_key):
        raise ValueError("Invalid test intent")
    PurchaseStore(config.database).bind_topup_intent(row["id"], intent_id)
    result = await client.post(PAYMENT_API + "/payment_methods", auth=(config.key, ""), json={"data": {"attributes": {
        "type": "qrph", "expiry_seconds": QR_EXPIRY_SECONDS,
    }}})
    result.raise_for_status()
    method = result.json()["data"]
    method_id = method["id"]
    if (method.get("type") != "payment_method" or not isinstance(method_id, str)
            or not re.fullmatch(r"pm_[A-Za-z0-9_]+", method_id)
            or method["attributes"].get("livemode") is not False or method["attributes"].get("type") != "qrph"):
        raise ValueError("Invalid test method")
    # Conservative local display deadline: attachment activates the QR. This
    # does not mark the receipt expired; the signed event will do that later.
    expires_at = int(time.time()) + QR_EXPIRY_SECONDS
    result = await client.post(PAYMENT_API + "/payment_intents/" + intent_id + "/attach", auth=(config.key, ""), json={"data": {"attributes": {
        "payment_method": method_id, "client_key": client_key,
    }}})
    result.raise_for_status()
    attached = result.json()["data"]
    attrs = validated_test_intent(attached, row)
    if (attached["id"] != intent_id
            or attrs.get("status") != "awaiting_next_action"):
        raise ValueError("Invalid attached test intent")
    image = attrs["next_action"]["code"]["image_url"]
    if not isinstance(image, str) or len(image) > 1_000_000:
        raise ValueError("Invalid QR image")
    encoded = image.removeprefix("data:image/png;base64,")
    decoded = base64.b64decode(encoded, validate=True)
    if not decoded.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("Invalid QR image")
    return intent_id, "data:image/png;base64," + encoded, expires_at


@router.post("/topups", status_code=201)
async def create_topup(body: TopupRequest, request: Request, idempotency_key: str = Header(default="")):
    account = require_account(request)
    check_csrf(request, account)
    config = settings()
    if not re.fullmatch(r"[A-Za-z0-9_-]{16,128}", idempotency_key):
        raise HTTPException(400, "Use a valid top-up request ID and try again.")
    store = PurchaseStore(config.database)
    try:
        row = store.begin_topup(account["id"], body.package_id, idempotency_key)
    except PurchaseError as error:
        if error.kind == "unknown_package":
            raise HTTPException(400, "Choose an available test-credit package.") from None
        raise purchase_http_error(error) from None
    if row["status"] != "creating":
        return response({"topup": public_topup(row)})
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            intent_id, image, expires_at = await create_qr(client, config, row)
    except (httpx.HTTPError, ValueError, KeyError, TypeError, AttributeError, sqlite3.IntegrityError):
        # A partial provider request can exist even when its response is lost.
        # Preserve this attempt and refuse automatic re-creation on replay.
        store.creation_failed(row["id"])
        raise HTTPException(502, "Could not create a verified test QR. Check your test key and connection; no payment was confirmed.") from None
    row = store.register_topup(row["id"], intent_id, image, expires_at)
    return response({"topup": public_topup(row)}, 201)


@router.get("/mobile-return", response_class=HTMLResponse)
def mobile_return():
    # This public page only navigates. Provider webhooks remain authoritative.
    return HTMLResponse("""<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Return to AI Defense Arena</title><body>
<h1>Return to AI Defense Arena</h1>
<p>This return does not confirm payment. The app checks your server-verified receipt.</p>
<p><a href="defensearena://payment-return">Return to app</a></p>
<p>If the link does not open, switch back to the app and refresh your receipt.</p>
</body></html>""", headers={"Cache-Control": "no-store", "Referrer-Policy": "no-referrer",
                          "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"})


@router.post("/checkout", status_code=201)
async def create_checkout(body: CheckoutRequest, request: Request, idempotency_key: str = Header(default="")):
    account = require_account(request)
    check_csrf(request, account)
    config = settings()
    if idempotency_key and not re.fullmatch(r"[A-Za-z0-9_-]{16,128}", idempotency_key):
        raise HTTPException(400, "Use a valid checkout request ID and try again.")
    store = PurchaseStore(config.database)
    try:
        row = store.begin(account["id"], idempotency_key)
    except PurchaseError as error:
        raise purchase_http_error(error) from None
    if row["status"] != "creating":
        return response({"order": public_order(row)})
    order_id = row["id"]
    native = request.headers.get("X-Arena-Native") == "1"
    native_return = config.origin + "/api/payments/test/mobile-return"
    payload = {"data": {"attributes": {
        "line_items": [{"name": "AI Defense Arena sandbox test", "amount": TEST_AMOUNT, "currency": "PHP", "quantity": 1}],
        "payment_method_types": ["qrph"],
        "reference_number": order_id,
        "success_url": native_return if native else config.origin + "/?payments=test&payment_return=success",
        "cancel_url": native_return if native else config.origin + "/?payments=test&payment_return=cancel",
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
        store.creation_failed(order_id)
        raise HTTPException(502, "Could not create a verified test checkout. Check your test key and connection; no payment was confirmed.") from None
    row = store.register(order_id, checkout_id, checkout_url)
    return response({"order": public_order(row)}, 201)


@router.get("/orders/{order_id}")
def get_order(order_id: str, request: Request, authorization: str = Header(default="")):
    config = settings()
    token = authorization.removeprefix("Bearer ") if authorization.startswith("Bearer ") else ""
    row = PurchaseStore(config.database).get(order_id)
    if row is None:
        raise HTTPException(404, "Test order not found. Use the browser that created it.")
    if row["account_id"] is not None:
        account = require_account(request)
        if row["account_id"] != account["id"]:
            raise HTTPException(404, "Test order not found.")
    elif not token or not hmac.compare_digest(row["token_hash"], token_hash(token)):
        raise HTTPException(404, "Test order not found. Use the browser that created it.")
    return response({"order": public_order(row)})


@router.get("/topups/{topup_id}")
def get_topup(topup_id: str, request: Request):
    account = require_account(request)
    row = PurchaseStore(settings().database).get(topup_id)
    if row is None or row["provider"] != "payment_intent" or row["account_id"] != account["id"]:
        raise HTTPException(404, "Test top-up not found.")
    # Reads never contact PayMongo or reconcile expiry/payment/credit awards.
    return response({"topup": public_topup(row)})


@router.post("/topups/{topup_id}/simulate")
def simulate_topup(topup_id: str, body: SimulateTopupRequest, request: Request):
    account = require_account(request)
    check_csrf(request, account)
    config = settings()  # Reject missing/non-test keys before any award.
    try:
        row = PurchaseStore(config.database).simulate_topup_paid(topup_id, account["id"])
    except PurchaseError as error:
        raise purchase_http_error(error) from None
    message = ("Sandbox simulation only: test credits applied; no provider payment was processed."
               if is_simulated_topup(row) else "This test top-up is already paid; no additional credits were awarded.")
    return response({"topup": public_topup(row), "mode": "test", "message": message})


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


def reconcile_topup_event(body: dict, store: PurchaseStore) -> bool:
    """Return whether this is a QR event, after validating its signed resource."""
    try:
        event = body["data"]
        envelope = event["attributes"] if event.get("type") == "event" else event
        event_type = envelope["type"]
        if event_type not in {"payment.paid", "payment.failed", "qrph.expired"}:
            return False
        if envelope.get("livemode") is not False:
            raise ValueError("Only test events are accepted")
        resource = envelope.get("data") or envelope.get("resource")
        # Checkout resources retain their existing separate handler.
        if isinstance(resource, dict) and resource.get("type") == "checkout_session":
            return False
        attrs = resource["attributes"]
        if attrs.get("livemode") is not False:
            raise ValueError("Only test resources are accepted")
        payment_id = None
        qr_expiry = event_type == "qrph.expired" and resource.get("type") == "qrph"
        if event_type == "qrph.expired":
            if qr_expiry:
                if (not isinstance(resource.get("id"), str) or not re.fullmatch(r"qrph_[A-Za-z0-9_]+", resource["id"])
                        or attrs.get("status", "expired") != "expired"):
                    raise ValueError("Invalid expired QR")
                intent_id = attrs["payment_intent_id"]
            else:
                if resource.get("type") != "payment_intent" or attrs.get("status") != "awaiting_payment_method":
                    raise ValueError("Invalid expired intent")
                intent_id = resource["id"]
        else:
            if resource.get("type") != "payment" or attrs.get("status") != event_type.split(".")[1]:
                raise ValueError("Invalid payment resource")
            intent_id, payment_id = attrs["payment_intent_id"], resource["id"]
            if not isinstance(payment_id, str) or not re.fullmatch(r"pay_[A-Za-z0-9_]+", payment_id):
                raise ValueError("Invalid payment ID")
        if (not isinstance(intent_id, str) or not re.fullmatch(r"pi_[A-Za-z0-9_]+", intent_id)
                or (not qr_expiry or "amount" in attrs) and type(attrs.get("amount")) is not int
                or (not qr_expiry or "currency" in attrs) and not isinstance(attrs.get("currency"), str)):
            raise ValueError("Invalid payment fields")
        metadata = attrs.get("metadata")
        if metadata is None:
            metadata = {}
        if not isinstance(metadata, dict):
            raise ValueError("Invalid payment metadata")
        row = store.get_topup_by_intent(intent_id)
        if row is None:
            if "topup_id" in metadata:
                if not isinstance(metadata["topup_id"], str):
                    raise ValueError("Invalid top-up reference")
                if store.get(metadata["topup_id"]) is not None:
                    raise ValueError("Intent does not match the referenced receipt")
            return True  # A payment from another integration on this provider account.
        if ("topup_id" in metadata and metadata["topup_id"] != row["id"]
                or "amount" in attrs and attrs["amount"] != row["amount"]
                or "currency" in attrs and attrs["currency"] != row["currency"]):
            raise ValueError("Payment does not match the receipt")
    except (KeyError, TypeError, AttributeError, ValueError):
        raise HTTPException(400, "Test payment details do not match the recorded top-up.") from None
    if row["status"] == "creating":
        raise PurchaseError("registration_pending")
    if event_type == "payment.paid":
        store.record_topup_paid(row["id"], intent_id, [payment_id], attrs["amount"], attrs["currency"])
    elif event_type == "payment.failed":
        store.mark_topup_failed(row["id"])
    else:
        store.mark_topup_expired(row["id"])
    return True


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
        body = json.loads(raw)
        if reconcile_topup_event(body, PurchaseStore(config.database)):
            return response({"received": True})
        session = paid_session(body)
    except PurchaseError as error:
        raise purchase_http_error(error) from None
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
    try:
        PurchaseStore(config.database).record_paid(order_id, checkout_id, payment_ids)
    except PurchaseError as error:
        raise purchase_http_error(error) from None
    return response({"received": True})

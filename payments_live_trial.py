"""Isolated, operator-only PHP 1 real-payment trial; not the app's pricing.

Run as a separate process, never mount this router in the multiplayer service.
The existing sandbox routes and balances deliberately stay unchanged.
"""

from contextlib import asynccontextmanager
import hmac
import json
import os
from pathlib import Path
import re
import sqlite3
import time
from urllib.parse import urlsplit

import httpx
from fastapi import APIRouter, FastAPI, Header, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict

from account_store import connect_store
from accounts import auth_settings, check_csrf, configure_auth, require_account
from payments import Settings, create_qr, public_topup, reconcile_topup_event, response, verify_signature
from purchase_store import PurchaseError, PurchaseStore

router = APIRouter(prefix="/api/payments/live-trial")


def trial_settings() -> Settings:
    key = os.environ.get("PAYMONGO_LIVE_SECRET_KEY", "").strip()
    secret = os.environ.get("PAYMONGO_LIVE_WEBHOOK_SECRET", "").strip()
    origin = os.environ.get("PAYMONGO_PUBLIC_BASE_URL", "").strip().rstrip("/")
    database = Path(os.environ.get("PAYMONGO_TEST_DB_PATH", "")).resolve()
    try:
        url = urlsplit(origin)
        url.port
    except ValueError:
        raise HTTPException(503, "Configure a valid HTTPS trial origin.") from None
    if (os.environ.get("PAYMONGO_LIVE_TRIAL_ENABLED") != "1"
            or not key.startswith("sk_live_") or not secret
            or not os.environ.get("PAYMONGO_LIVE_TRIAL_OWNER_SUB", "").strip()):
        raise HTTPException(503, "The owner-only live trial is not configured.")
    if (url.scheme != "https" or not url.hostname or url.username or url.password
            or url.path or url.query or url.fragment or auth_settings()[2] != origin):
        raise HTTPException(503, "Use one matching HTTPS account and payment origin.")
    if os.environ.get("DATABASE_URL", "").strip() or database.name != "qr-one-peso-live.sqlite3":
        raise HTTPException(503, "Use the separate local qr-one-peso-live.sqlite3 receipt store, without DATABASE_URL.")
    return Settings(key, secret, origin, database, livemode=True)


def initialize_trial_store(config: Settings):
    """Fail closed rather than interpreting sandbox receipts as real payments."""
    with connect_store(config.database) as db:
        db.execute("BEGIN IMMEDIATE")
        db.execute("CREATE TABLE IF NOT EXISTS payment_environment (name TEXT PRIMARY KEY)")
        marker = db.execute("SELECT name FROM payment_environment").fetchall()
        if marker:
            if len(marker) != 1 or marker[0]["name"] != "one-peso-live-trial":
                raise HTTPException(503, "This database belongs to a different payment environment.")
        else:
            if db.execute("SELECT 1 FROM test_orders LIMIT 1").fetchone() or db.execute("SELECT 1 FROM accounts LIMIT 1").fetchone():
                raise HTTPException(503, "Do not reuse an existing account or sandbox database for this live trial.")
            db.execute("INSERT INTO payment_environment VALUES ('one-peso-live-trial')")


def owner(request: Request, config: Settings):
    account = require_account(request)
    with connect_store(config.database) as db:
        row = db.execute("SELECT google_sub FROM accounts WHERE id=?", (account["id"],)).fetchone()
    if row is None or not hmac.compare_digest(row["google_sub"].encode(), os.environ["PAYMONGO_LIVE_TRIAL_OWNER_SUB"].encode()):
        raise HTTPException(403, "This limited real-payment trial is available only to its configured owner.")
    return account


def trial_error(error: PurchaseError) -> HTTPException:
    errors = {
        "trial_exists": (409, "Your one-peso trial receipt already exists. Check its status; another QR is blocked to avoid a second payment."),
        "creating": (409, "Your trial QR is still being created. Keep the same request."),
        "unverified": (409, "The earlier trial could not be verified. Do not pay another QR; review its provider status first."),
        "registration_pending": (503, "Payment registration is pending; retry the notification."),
        "limited": (429, "Too many payment attempts."),
        "payment_mismatch": (400, "Payment does not match the trial receipt."),
        "duplicate_payment": (400, "Payment already belongs to another receipt."),
    }
    status, detail = errors.get(error.kind, (400, "The trial payment could not be verified."))
    return HTTPException(status, detail)


def trial_receipt(row):
    return public_topup(row) | {"mode": "live"}


class TrialRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    confirm_real_payment: bool


@router.get("/config")
def config(request: Request):
    settings = trial_settings()
    account = owner(request, settings)
    rows = PurchaseStore(settings.database).history(account["id"])
    return response({"mode": "live", "amount": 100, "currency": "PHP", "credits": 100,
                     "receipt_id": rows[0]["id"] if rows else None})


@router.post("/topups")
async def create(body: TrialRequest, request: Request, idempotency_key: str = Header(default="")):
    config = trial_settings()
    account = owner(request, config)
    check_csrf(request, account)
    if body.confirm_real_payment is not True:
        raise HTTPException(400, "Confirm that this is a real PHP 1.00 payment trial.")
    if not re.fullmatch(r"[A-Za-z0-9_-]{16,128}", idempotency_key):
        raise HTTPException(400, "Use a valid trial request ID.")
    store = PurchaseStore(config.database)
    try:
        row = store.begin_live_trial(account["id"], idempotency_key)
        if row["status"] != "creating":
            return response({"topup": trial_receipt(row)})
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                intent, image, expiry = await create_qr(client, config, row)
        except (httpx.HTTPError, ValueError, KeyError, TypeError, AttributeError, sqlite3.IntegrityError):
            store.creation_failed(row["id"])
            raise HTTPException(502, "Could not create a verified live QR. No payment was confirmed. Check live QR Ph activation and the provider before another attempt.") from None
        return response({"topup": trial_receipt(store.register_topup(row["id"], intent, image, expiry))}, 201)
    except PurchaseError as error:
        raise trial_error(error) from None


@router.get("/topups/{receipt_id}")
def receipt(receipt_id: str, request: Request):
    config = trial_settings()
    account = owner(request, config)
    row = PurchaseStore(config.database).get(receipt_id)
    if row is None or row["account_id"] != account["id"] or row["provider"] != "payment_intent":
        raise HTTPException(404, "Trial receipt not found.")
    return response({"topup": trial_receipt(row)})


@router.post("/webhook")
async def webhook(request: Request, paymongo_signature: str = Header(default="")):
    config = trial_settings()
    raw = bytearray()
    async for chunk in request.stream():
        raw.extend(chunk)
        if len(raw) > 1_000_000:
            raise HTTPException(413, "Webhook is too large.")
    try:
        verify_signature(bytes(raw), paymongo_signature, config.webhook_secret, time.time(), livemode=True)
        reconcile_topup_event(json.loads(raw), PurchaseStore(config.database), livemode=True)
    except PurchaseError as error:
        raise trial_error(error) from None
    except HTTPException as error:
        # Shared helpers retain legacy test wording for compatibility.
        raise HTTPException(error.status_code, "Payment notification could not be verified.") from None
    except (ValueError, UnicodeDecodeError):
        raise HTTPException(400, "Invalid payment notification.") from None
    return response({"received": True})


@asynccontextmanager
async def lifespan(app):
    initialize_trial_store(trial_settings())
    yield


def create_app():
    app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None)
    configure_auth(app)
    app.include_router(router)

    @app.get("/health")
    def health():
        return {"status": "ok", "mode": "one-peso-live-trial"}

    @app.get("/")
    def page():
        return FileResponse(Path(__file__).parent / "game" / "live-trial.html", headers={
            "Cache-Control": "no-store", "Referrer-Policy": "no-referrer"})

    return app


app = create_app()

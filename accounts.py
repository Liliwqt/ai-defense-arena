"""Google OIDC login and private local sandbox accounts; no Google tokens persisted."""

from functools import lru_cache
import hmac
import logging
import os
import secrets
from urllib.parse import urlsplit

from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, HTTPException, Request, Query
from pydantic import BaseModel, ConfigDict, Field
from fastapi.responses import JSONResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from mobile_auth import handoffs, RETURN_URL, VerifiedGoogleIdentity

from account_store import (SESSION_SECONDS, AccessError, account_access, account_overview, redeem_voucher,
                          create_google_session, remove_session, session_account)

router = APIRouter(prefix="/api/auth", tags=["accounts"])
ACCOUNT_COOKIE = "arena_account"
GOOGLE_METADATA = "https://accounts.google.com/.well-known/openid-configuration"


def auth_settings() -> tuple[str, str, str]:
    client_id = os.environ.get("GOOGLE_CLIENT_ID", "").strip()
    secret = os.environ.get("GOOGLE_CLIENT_SECRET", "").strip()
    origin = os.environ.get("AUTH_PUBLIC_BASE_URL", "").strip().rstrip("/")
    session_secret = os.environ.get("AUTH_SESSION_SECRET", "")
    if not client_id or not secret or len(session_secret) < 32:
        raise HTTPException(503, "Configure Google sign-in on the server before using accounts.")
    try:
        url = urlsplit(origin)
        url.port
    except ValueError:
        raise HTTPException(503, "Configure a valid account origin on the server.") from None
    local = url.hostname in {"127.0.0.1", "localhost"}
    if not url.hostname or url.username or url.password or url.path or url.query or url.fragment or (url.scheme != "https" and not (url.scheme == "http" and local)):
        raise HTTPException(503, "The account origin must be HTTPS, or localhost HTTP for development.")
    return client_id, secret, origin


def google_enabled() -> bool:
    try:
        auth_settings()
        return True
    except HTTPException:
        return False


@lru_cache(maxsize=4)
def google_client(client_id: str, secret: str):
    oauth = OAuth()
    return oauth.register("google", client_id=client_id, client_secret=secret,
                          server_metadata_url=GOOGLE_METADATA,
                          client_kwargs={"scope": "openid email profile", "code_challenge_method": "S256", "timeout": 20})


class HideGoogleCallbackQuery(logging.Filter):
    """Do not let Uvicorn's access log record single-use OAuth codes/state."""
    def filter(self, record):
        if isinstance(record.args, tuple) and len(record.args) == 5:
            args = list(record.args)
            if isinstance(args[2], str) and args[2].split("?", 1)[0] in {"/api/auth/google/callback", "/api/auth/google/login"}:
                args[2] = args[2].split("?", 1)[0]
                record.args = tuple(args)
        return True


def configure_auth(app):
    # OAuth's temporary state/nonce/PKCE cookie is separate from the opaque app
    # session. Missing configuration keeps login disabled, while rooms still run.
    app.add_middleware(SessionMiddleware,
                       secret_key=os.environ.get("AUTH_SESSION_SECRET") or secrets.token_urlsafe(48),
                       session_cookie="arena_oauth", max_age=600, same_site="lax",
                       https_only=os.environ.get("AUTH_PUBLIC_BASE_URL", "").startswith("https://"))
    app.include_router(router)
    access_log = logging.getLogger("uvicorn.access")
    if not any(isinstance(f, HideGoogleCallbackQuery) for f in access_log.filters):
        access_log.addFilter(HideGoogleCallbackQuery())


def require_account(request: Request):
    auth_settings()
    account = session_account(request.cookies.get(ACCOUNT_COOKIE, ""))
    if account is None:
        raise HTTPException(401, "Sign in with Google to create or control a room, or use your account.")
    return account


def check_csrf(request: Request, account):
    origin = auth_settings()[2]
    supplied = request.headers.get("x-csrf-token", "")
    if request.headers.get("origin") != origin or not hmac.compare_digest(supplied.encode(), account["csrf_token"].encode()):
        raise HTTPException(403, "Refresh your account page before trying this action again.")


def account_response(body):
    return JSONResponse(body, headers={"Cache-Control": "no-store"})


@router.get("/me")
def me(request: Request):
    enabled = google_enabled()
    account = session_account(request.cookies.get(ACCOUNT_COOKIE, "")) if enabled else None
    if account is None:
        return account_response({"authenticated": False, "google_enabled": enabled})
    return account_response({"authenticated": True, "google_enabled": enabled,
                             "user": {key: account[key] for key in ("id", "email", "name")},
                             "csrf_token": account["csrf_token"], **account_overview(account["id"])})


class VoucherRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    voucher: str = Field(min_length=1, max_length=200)


@router.post("/voucher")
def voucher(body: VoucherRequest, request: Request):
    account = require_account(request)
    check_csrf(request, account)
    try:
        redeem_voucher(account["id"], body.voucher)
    except AccessError as error:
        message = str(error)
        raise HTTPException(429 if message.startswith("Too many") else 403, message) from None
    return account_response(account_access(account["id"]))


def destination(value: str) -> str:
    return value if value in {"/", "/?payments=test", "/?payments=live", "/?account=1"} else "/"


def failed_destination(target: str, reason: str) -> str:
    return target + ("&" if "?" in target else "?") + "signin_error=" + reason


@router.get("/google/login")
async def login(request: Request, return_to: str = Query("/")):
    client_id, secret, origin = auth_settings()
    target = destination(return_to)
    request.session["return_to"] = target
    request.session.pop("mobile_flow", None)
    mobile_flow = request.query_params.get("mobile_flow")
    if mobile_flow:
        handoffs.open(mobile_flow)
        request.session["mobile_flow"] = mobile_flow
    try:
        result = await google_client(client_id, secret).authorize_redirect(request, origin + "/api/auth/google/callback", prompt="select_account")
        result.headers["Cache-Control"] = "no-store"
        result.headers["Referrer-Policy"] = "no-referrer"
        return result
    except Exception:
        # Provider errors must never echo token payloads, codes or secrets.
        request.session.clear()
        return RedirectResponse(failed_destination(target, "unavailable"), status_code=303)


def replace_account_session(request: Request, identity: VerifiedGoogleIdentity):
    session = create_google_session(identity.subject, identity.email, identity.display_name)
    old = request.cookies.get(ACCOUNT_COOKIE)
    if old:
        remove_session(old)
    return session


def attach_account_cookie(result, session: str, origin: str):
    result.set_cookie(ACCOUNT_COOKIE, session, max_age=SESSION_SECONDS, httponly=True,
                      secure=origin.startswith("https://"), samesite="lax", path="/")
    return result


@router.get("/google/callback")
async def callback(request: Request):
    client_id, secret, origin = auth_settings()
    target = destination(request.session.get("return_to", "/"))
    mobile_flow = request.session.get("mobile_flow")
    try:
        # Authlib exchanges the code, validates state, JWT signature/issuer/
        # audience/expiry and OIDC nonce, then supplies verified userinfo.
        token = await google_client(client_id, secret).authorize_access_token(request)
        info = token["userinfo"]
        sub, email = info["sub"], info["email"]
        if not isinstance(sub, str) or not 1 <= len(sub) <= 255 or not isinstance(email, str) or not 1 <= len(email) <= 320 or info.get("email_verified") is not True:
            raise ValueError("Unverified Google identity")
        name = info.get("name") if isinstance(info.get("name"), str) else email
        identity = VerifiedGoogleIdentity(subject=sub, email=email, display_name=name[:100])
        if mobile_flow:
            target = handoffs.verified_return(mobile_flow, identity)
            request.session.clear()
            return RedirectResponse(target, status_code=303, headers={"Cache-Control": "no-store", "Referrer-Policy": "no-referrer"})
        session, _ = replace_account_session(request, identity)
    except Exception:
        request.session.clear()
        return RedirectResponse(RETURN_URL + "?error=signin_failed" if mobile_flow else failed_destination(target, "failed"), status_code=303, headers={"Cache-Control": "no-store", "Referrer-Policy": "no-referrer"})
    request.session.clear()
    result = RedirectResponse(target, status_code=303, headers={"Cache-Control": "no-store", "Referrer-Policy": "no-referrer"})
    return attach_account_cookie(result, session, origin)


class MobileStart(BaseModel):
    model_config = ConfigDict(extra="forbid")
    challenge: str = Field(pattern=r"^[A-Za-z0-9_-]{43}$")
    return_to: str = Field(default="/", max_length=100)


class MobileComplete(BaseModel):
    model_config = ConfigDict(extra="forbid")
    flow: str = Field(min_length=43, max_length=43)
    code: str = Field(min_length=43, max_length=43)
    verifier: str = Field(pattern=r"^[A-Za-z0-9._~-]{43,128}$")


@router.post("/mobile/start")
def mobile_start(body: MobileStart):
    origin = auth_settings()[2]
    if destination(body.return_to) != body.return_to:
        raise HTTPException(400, "Choose an app screen for sign-in.")
    flow = handoffs.start(body.challenge, body.return_to)
    return account_response({"flow": flow, "login_url": origin + "/api/auth/google/login?mobile_flow=" + flow})


@router.post("/mobile/complete")
def mobile_complete(body: MobileComplete, request: Request):
    origin = auth_settings()[2]
    session, target = handoffs.consume(body.flow, body.code, body.verifier,
                                      lambda identity: replace_account_session(request, identity))
    result = account_response({"return_to": target})
    return attach_account_cookie(result, session, origin)


@router.post("/logout")
def logout(request: Request):
    account = require_account(request)
    check_csrf(request, account)
    remove_session(request.cookies[ACCOUNT_COOKIE])
    result = account_response({"authenticated": False})
    result.delete_cookie(ACCOUNT_COOKIE, path="/", httponly=True, samesite="lax",
                         secure=auth_settings()[2].startswith("https://"))
    return result

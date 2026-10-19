"""Opt-in loopback runner with real AI and disposable, automatic host access.

Never imported or mounted by backend.game_server, the production entry point.
"""

import argparse
from contextlib import asynccontextmanager
from ipaddress import ip_address
import os
from pathlib import Path
import secrets
from tempfile import TemporaryDirectory
from urllib.parse import urlsplit

from fastapi import FastAPI
from starlette.responses import JSONResponse


def configure_environment(folder: Path, port: int) -> str:
    """Separate local practice from configured account/payment/provider state."""
    if os.environ.get("RENDER"):
        raise RuntimeError("Local testing access cannot run on Render.")
    origin = f"http://127.0.0.1:{port}"
    for key in tuple(os.environ):
        if key.startswith("PAYMONGO_") or key in {
            "DATABASE_URL", "PAYMENT_OPERATOR_GOOGLE_SUB", "TRUSTED_PROXY_NETWORKS",
        }:
            os.environ.pop(key, None)
    os.environ.update({
        "LOCAL_DEV_ACCESS": "1",
        "PAYMENTS_MODE": "test",
        "LIVE_PAYMENTS_ENABLED": "0",
        "PAYMONGO_TEST_DB_PATH": str(folder / "accounts.sqlite3"),
        "ROOM_DOCUMENT_DIR": str(folder / "documents"),
        "GOOGLE_CLIENT_ID": "local-development-only",
        "GOOGLE_CLIENT_SECRET": "local-development-only",
        "AUTH_SESSION_SECRET": secrets.token_urlsafe(48),
        "AUTH_PUBLIC_BASE_URL": origin,
        "FREE_ACCESS_VOUCHER": secrets.token_urlsafe(32),
    })
    return origin


class LocalAccess:
    """Reject remote/proxied access and establish a free identity before React."""

    def __init__(self, app, origin: str):
        self.app = app
        self.origin = origin
        self.host = urlsplit(origin).netloc

    async def __call__(self, scope, receive, send):
        if scope["type"] not in {"http", "websocket"}:
            return await self.app(scope, receive, send)
        headers = dict(scope.get("headers", ()))
        try:
            local = ip_address(scope["client"][0]).is_loopback
        except (ValueError, TypeError, KeyError):
            local = False
        forwarded = any(key == b"forwarded" or key.startswith(b"x-forwarded-") for key in headers)
        allowed = (local and not forwarded and headers.get(b"host") == self.host.encode()
                   and headers.get(b"origin", self.origin.encode()) == self.origin.encode())
        if not allowed:
            if scope["type"] == "websocket":
                return await send({"type": "websocket.close", "code": 1008})
            return await JSONResponse({"detail": "Local testing access only."}, status_code=403)(scope, receive, send)
        # No external identity/payment operations in this disposable app.
        if scope["path"].startswith(("/api/payments/", "/api/auth/google/", "/api/auth/mobile/")):
            return await JSONResponse({"detail": "Disabled in local testing mode."}, status_code=403)(scope, receive, send)
        if scope["type"] == "http" and scope["method"] == "GET" and scope["path"] == "/":
            from starlette.requests import Request
            from backend.accounts import ACCOUNT_COOKIE
            from backend.account_store import create_google_session, redeem_voucher, session_account
            request = Request(scope)
            if session_account(request.cookies.get(ACCOUNT_COOKIE, "")) is None:
                token, _ = create_google_session(
                    "local-test-" + secrets.token_hex(16), "tester@localhost.invalid", "Local tester",
                )
                account = session_account(token)
                redeem_voucher(account["id"], os.environ["FREE_ACCESS_VOUCHER"])
                cookie = JSONResponse({})
                cookie.set_cookie(ACCOUNT_COOKIE, token, httponly=True, samesite="strict")

                async def send_with_cookie(message):
                    if message["type"] == "http.response.start":
                        message = {**message, "headers": [*message.get("headers", ()),
                            *[(key, value) for key, value in cookie.raw_headers if key == b"set-cookie"]]}
                    await send(message)

                return await self.app(scope, receive, send_with_cookie)
        await self.app(scope, receive, send)


def create_app() -> FastAPI:
    if os.environ.get("LOCAL_DEV_ACCESS") != "1" or os.environ.get("RENDER"):
        raise RuntimeError("Use python -m backend.local_dev for local testing access.")
    origin = os.environ.get("AUTH_PUBLIC_BASE_URL", "")
    parsed = urlsplit(origin)
    if parsed.scheme != "http" or parsed.hostname != "127.0.0.1" or parsed.path or not parsed.port:
        raise RuntimeError("Local testing requires a 127.0.0.1 HTTP origin with an explicit port.")
    if os.environ.get("DATABASE_URL") or os.environ.get("PAYMENTS_MODE") != "test":
        raise RuntimeError("Local testing requires isolated storage and disabled live payments.")
    from backend import game_server

    @asynccontextmanager
    async def lifespan(_):
        async with game_server.lifespan(game_server.app):
            yield

    app = FastAPI(lifespan=lifespan)
    app.add_middleware(LocalAccess, origin=origin)
    app.mount("/", game_server.app)
    return app


def main():
    import uvicorn
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("Choose a port from 1 to 65535.")
    with TemporaryDirectory(prefix="defense-local-test-") as folder:
        origin = configure_environment(Path(folder), args.port)
        print(f"LOCAL TESTING ONLY: {origin} — automatic free test host; payments disabled.")
        print("OpenRouter uses your configured key. Free practice uses free models; Standard can incur provider costs. Test accounts disappear on shutdown.")
        uvicorn.run(create_app(), host="127.0.0.1", port=args.port, proxy_headers=False,
                    ws="websockets", ws_max_size=20000, ws_max_queue=4)


if __name__ == "__main__":
    main()

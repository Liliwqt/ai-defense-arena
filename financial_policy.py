"""Server-owned live purchase terms; sandbox contracts remain separate."""
from dataclasses import dataclass
import os
from types import MappingProxyType
from urllib.parse import urlsplit


@dataclass(frozen=True)
class CreditPackage:
    id: str
    amount: int
    credits: int
    currency: str = "PHP"
    version: str = "tester-2026-10-v1"

    def public(self):
        return dict(id=self.id, amount=self.amount, credits=self.credits, currency=self.currency, version=self.version)


LIVE_PACKAGES = MappingProxyType({item.id: item for item in (
    CreditPackage("credits-10", 100, 10), CreditPackage("credits-50", 500, 50), CreditPackage("credits-100", 1000, 100))})


def live_mode():
    mode = os.environ.get("PAYMENTS_MODE", "test").strip()
    if mode not in {"test", "live"}:
        raise ValueError("Payment mode is not configured correctly.")
    return mode == "live"


def invited(email, *, db=None):
    from management_store import invitation
    if db is not None:
        return invitation(db, email)
    from account_store import connect_store, database_path
    with connect_store(database_path()) as connection:
        return invitation(connection, email)


def support_email():
    value = os.environ.get("PAYMENT_SUPPORT_EMAIL", "").strip()
    if len(value) > 254 or value.count("@") != 1 or any(c.isspace() or c in "?&#\r\n" for c in value):
        return ""
    return value


def live_payment_setup_valid():
    """Mode and deployment readiness without disclosing credential values."""
    try:
        origin=os.environ.get('PAYMONGO_PUBLIC_BASE_URL','').strip().rstrip('/')
        auth_origin=os.environ.get('AUTH_PUBLIC_BASE_URL','').strip().rstrip('/')
        parsed=urlsplit(origin);parsed.port
        local=urlsplit(auth_origin).hostname in {'localhost','127.0.0.1','::1'}
        return (live_mode() and os.environ.get('PAYMONGO_LIVE_SECRET_KEY','').strip().startswith('sk_live_')
            and bool(os.environ.get('PAYMONGO_LIVE_WEBHOOK_SECRET','').strip())
            and parsed.scheme=='https' and bool(parsed.hostname)
            and not (parsed.username or parsed.password or parsed.path or parsed.query or parsed.fragment)
            and (local or (origin==auth_origin and bool(os.environ.get('DATABASE_URL','').strip()))))
    except ValueError:return False

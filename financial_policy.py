"""Server-owned live purchase terms; sandbox contracts remain separate."""
from dataclasses import dataclass
import os
from types import MappingProxyType


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


def invited(email):
    allowed = {value.strip().casefold() for value in os.environ.get("LIVE_TOPUP_INVITED_EMAILS", "").split(",") if value.strip()}
    return email.casefold() in allowed


def support_email():
    value = os.environ.get("PAYMENT_SUPPORT_EMAIL", "").strip()
    if len(value) > 254 or value.count("@") != 1 or any(c.isspace() or c in "?&#\r\n" for c in value):
        return ""
    return value

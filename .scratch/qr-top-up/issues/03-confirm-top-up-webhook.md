# 03: Confirm a top-up by signed webhook (router, additive)

**What to build:** A valid signed `payment.paid` webhook for a top-up awards the
credits exactly once; `payment.failed` and `qrph.expired` award nothing. Duplicate
delivery awards once. Amount/currency/reference mismatches are rejected. A
display-only status read is exposed. The handler supports the payment-intent
envelope **and** continues to support the existing checkout-session envelope.

**Blocked by:** 01

**Status:** ready-for-human
**Implemented locally:** 2026-10-07; real sandbox delivery remains unverified.

- [x] A valid signed `payment.paid` for a known top-up awards the credits once
  and moves the top-up to paid.
- [x] Repeating the same paid delivery awards nothing further.
- [x] `payment.failed` marks the top-up failed and awards nothing.
- [x] `qrph.expired` marks the top-up expired and awards nothing.
- [x] Events with a wrong amount, currency, or reference mapping are rejected and
  award nothing.
- [x] Non-test (live-mode) events are rejected.
- [x] A status read returns the current top-up state for display only and never
  grants credits.
- [x] The existing checkout-session webhook path still awards once and passes its
  current tests.
- [x] Router tests drive signed webhooks through the existing harness.

## Comments

Ticket 03 implemented against `4f56918`: signed QR payment/failure/expiry,
owner-only status read, early notification retry and authoritative delayed-paid
recovery. Existing checkout is retained. Full offline gate: 267 Python tests
(external providers mocked), 186 React tests and production build.
Standards review has zero findings; Spec P1 for delayed settlement is resolved.
See `docs/QR_TOPUP_CONFIRM_REVIEW.md`. Live expiry payload, PostgreSQL,
tickets 04–06, publication and deployment remain separate.

# 01: QR top-up record and once-only award (store)

**What to build:** The transactional store gains a QR top-up record: a signed-in
host's top-up can be reserved against a preset package, registered with a payment
intent id, a base64 QR image, and an expiry, reconciled to paid with credits
awarded exactly once, and marked failed or expired awarding nothing. All
account-scoped and idempotent per request id. Existing checkout-session rows keep
working unchanged.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent
**Completed:** 0d47be9 (2026-10-06)

- [x] A top-up can be reserved for an account against a preset package and a
  request id; reserving the same request id again reuses the same top-up and
  creates no second row.
- [x] A reserved top-up can be registered with a payment intent id, QR image url,
  and expiry, moving it to awaiting payment.
- [x] Reconciling a paid event awards the package's credits exactly once, in the
  same transaction that marks the top-up paid; a repeated paid event awards
  nothing further.
- [x] A paid event whose amount, currency, or reference mapping does not match
  the package/top-up is rejected and awards nothing.
- [x] Failed and expired reconciliation mark the top-up failed/expired and award
  nothing.
- [x] Top-ups are visible only to their owning account; history returns recent
  top-ups for the account.
- [x] Existing checkout-session rows and their awards are unaffected (schema
  change is additive).
- [x] Store-level tests cover the above; no HTTP or provider is involved.

## Comments

Implemented on `feature/question-first-room`, commit `0d47be9` (amended with
review fixes). Offline gate: 223 Python tests, 184 React tests, production
build. Standards + Spec review ran over the scoped diff; it found the currency
check unreachable and an empty-`payment_ids` crash, both fixed (currency is now
compared, and an empty list is rejected), and the duplicated reconciliation
prologue extracted into one `_reconcile`. Real-local-PostgreSQL checks were not
run here (`TEST_POSTGRES_URL` unset); the migration is additive SQL validated on
SQLite.

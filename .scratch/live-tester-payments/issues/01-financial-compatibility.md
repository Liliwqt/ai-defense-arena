# 01 — Expand financial contracts without changing sandbox behavior

**What to build:** existing hosts can still inspect and use their sandbox purchases while
purchase mode, frozen receipt terms and new live configuration can be represented
safely through storage, API responses and receipt presentation.

**Blocked by:** None — can start immediately.

**Status:** ready-for-human

- [x] Add explicit environment and immutable purchase-term representation beside
  existing contracts; legacy receipts keep original amount/credits and test status.
- [x] Read old receipts independently of today's package catalog, including in the UI.
- [x] Preserve sandbox creation, simulation, legacy receipt reads and verified settlement.
- [x] Unknown/mismatched live configuration cannot enable a live payment or silently
  select local hosted storage; no live purchase/award is exposed by this slice.
- [x] Prove additive migration/history retention and compatible HTTP/React behavior;
  include actual local PostgreSQL migration evidence with providers mocked.

## Comments

2026-10-08: Implemented locally for review. Shared verification is recorded in
PROJECT_LOG.md and docs/LIVE_TESTER_PAYMENTS.md. External-provider/hosted and
physical-device gates remain separate; no payment, cash refund or deployment
was performed by this implementation.

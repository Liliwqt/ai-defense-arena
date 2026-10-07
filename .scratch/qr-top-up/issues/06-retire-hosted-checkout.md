# 06: Retire hosted checkout (contract)

**What to build:** Now that the page uses the QR-first top-up and nothing calls
the old path, the hosted-checkout creation endpoint and its page affordances are
deleted, leaving exactly one way to add credits.

**Blocked by:** 05

**Status:** ready-for-human

**Implemented:** 2026-10-07, locally on `feature/question-first-room`.
Starting review baseline: `839cbf0`. Pending user review and separate live checks.

- [x] No UI calls the hosted-checkout creation path.
- [x] The hosted-checkout creation endpoint is removed.
- [x] Checkout-session reconciliation that is still required for existing
  records is retained or explicitly retired with the leftover rows accounted for.
- [x] The full offline gate passes: Python tests (providers mocked), React tests,
  and the production build.
- [x] Documentation copy describes a single top-up path.

## Handoff

The route/schema/provider creation call is removed; legacy owner/token reads,
signed paid settlement and navigation-only mobile return remain. Existing
records and awards are untouched. Account test fixtures use the QR API.

Verification: 272 Python tests (external providers mocked), 202 working-tree
React tests and production build; 195 tests/build in an isolated selected
frontend. Focused account/payment checks pass 91 tests on temporary SQLite.
A portrait synthetic browser smoke check confirms the QR-only screen.

Independent review: Standards 0 violations and 1 low-priority possible fixture
duplication suggestion, deferred; Spec 0 findings. See
`docs/QR_TOPUP_RETIRE_REVIEW.md`. No push/deployment; live provider/PostgreSQL,
native/physical-device and user visual approval remain pending.

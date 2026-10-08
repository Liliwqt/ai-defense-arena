# 09 — Restore access after a verified server interruption

**What to build:** after a service restart loses an unfinished room, the host's orphaned
reservation is released or its ten-credit charge returned once, visibly in Account.

**Blocked by:** 07 — Unavailable-service credit return; 08 — Abandonment outcomes.

**Status:** ready-for-human

- [ ] Reuse run-return semantics and durable lifecycle evidence to recover only a
  verifiably lost service incarnation, never a healthy overlapping process.
- [ ] Exclude completed, ordinary-ended and observed-abandoned outcomes; legacy rows
  without evidence stay reviewable rather than presumed interrupted.
- [ ] Crash windows before/after charge/publication and during coaching are handled;
  repeated startup cannot produce duplicate compensation or credits for vouchers.
- [ ] Treat downtime as server interruption, not disconnected-user abandonment. Retain
  financial records while the UI acknowledges that in-memory room data is gone.
- [ ] Verify durable receipts/balances/history and active-slot cleanup through a real
  local PostgreSQL process/restart check, with external providers mocked.

## Comments

2026-10-08: Implemented locally for review. Shared verification is recorded in
PROJECT_LOG.md and docs/LIVE_TESTER_PAYMENTS.md. External-provider/hosted and
physical-device gates remain separate; no payment, cash refund or deployment
was performed by this implementation.

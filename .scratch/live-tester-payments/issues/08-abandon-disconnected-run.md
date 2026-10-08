# 08 — Abandon a defense after ten minutes with nobody connected

**What to build:** healthy-service-observed all-defender absence ends an abandoned run,
releases its active slot and permits a later run without refunding the old charge.

**Blocked by:** 05 — Paid/voucher defense lifecycle.

**Status:** ready-for-human

- [x] All defenders and their multiple connections are considered; any connected defender
  resets absence, and brief disconnects permit normal reconnect.
- [x] Ten minutes must elapse while the owning service operates; expired host sign-in,
  one closed tab or server downtime does not prove abandonment.
- [x] Persist the terminal noncompensable outcome, cancel generation/timers and release
  the active claim; stale results cannot reopen the abandoned run.
- [x] Reconnection/account history explains abandonment; no invented transcript restore
  or ten-credit return. Voucher outcomes remain zero-cost.
- [x] Fake-clock tests cover the boundary, reconnect/disconnect races, idle AI/report
  work, multi-tab presence and PostgreSQL outcome/claim persistence.

## Comments

2026-10-08: Implemented locally for review. Shared verification is recorded in
PROJECT_LOG.md and docs/LIVE_TESTER_PAYMENTS.md. External-provider/hosted and
physical-device gates remain separate; no payment, cash refund or deployment
was performed by this implementation.

# 02 — Retained answers and failed-stage recovery

**What to build:** after a provider failure, the defender's work remains and the
authorized recovery action retries the failed stage without replaying success.

**Blocked by:** 01 — Factual animated waiting and baseline timing.

**Status:** ready-for-human

Source: [confirmed specification](../spec.md). Breakdown approved on 2026-10-21.

- [x] Retain pending submissions through interpretation failure and clearly separate
  them from accepted answers. Never erase an accepted answer after a later error.
- [x] Retain a validated eligible plan if only reviewer writing fails; retry that
  reviewer with saved input rather than repeating interpretation or planning.
- [x] Scope reuse to unchanged logical room/run/turn/preparation/source/context/policy
  identity; retry counters alone cannot invalidate it or grant stale-work access.
- [x] Invalidate obsolete work/plan reuse on end/restart/closure/expiry. Deduplicate
  submissions and retry clicks; reconnect restores actual state without dispatch.
- [x] Preserve chosen-defender/host permissions, direct/saved-answer recovery and
  current timers, attempts, protected funds and once-only effects.
- [x] Apply shared recovery safely to Free without new model assignments, paid
  fallback or reset quotas; legacy snapshots remain compatible. Include the
  existing typed fallback's stage-recovery path before later optimized parity.
- [x] Demonstrate failures before/after acceptance and after planning through actual
  HTTP/WebSocket actions and whole-App recovery, with providers mocked.
- [x] Check retained ledger holds and no duplicate opening charge/history/completion;
  recovery itself cannot refund answer time or claim full coaching completion.

## Comments

Implemented locally on 2026-10-21 under the user's next-ticket authorization.
All 8 local checks pass; independent Standards0/Spec0 after a duplicate-writer
validation fix. See [review and verification](../reviews/02.md). Human visual
approval and actual-provider/hosted/device evidence remain separate. No push or
deployment. Ticket 03 is now unblocked, not implemented.

# 07 — End unavailable AI service with a once-only credit return

**What to build:** a host can retry a failed question/coaching report free or explicitly end
an unresolved unavailable run, restoring its ten credits once.

**Blocked by:** 05 — Paid/voucher defense lifecycle.

**Status:** ready-for-human

- [ ] Only server-recorded unresolved question/coaching failure enables the recovery
  action; ordinary ending, timeouts and successful service do not qualify.
- [ ] Persist the error and run epoch; atomically end service, release the active claim
  and restore original paid allocations once. An uncharged opening releases only
  its reservation; voucher runs never manufacture a credit award.
- [ ] Revalidate under concurrency with retry success; invalidate timers/pending AI
  results so stale completion cannot revive or recharge the ended run.
- [ ] Provide host-only recovery controls for code and research, private adjustment
  history and clear distinction between credits returned and a cash refund.
- [ ] Test repeated actions/reconnect, coaching failure, accepted-answer preservation,
  unauthorized recovery and race outcomes at WebSocket/React/PostgreSQL boundaries.

## Comments

2026-10-08: Implemented locally for review. Shared verification is recorded in
PROJECT_LOG.md and docs/LIVE_TESTER_PAYMENTS.md. External-provider/hosted and
physical-device gates remain separate; no payment, cash refund or deployment
was performed by this implementation.

# 12 — Review the integrated flow and prepare hosted readiness

**What to build:** a locally reviewed release candidate and clear operator checklist for a
later separately requested hosted tester release; paying users are not enabled yet.

**Blocked by:** 06 — Missed-payment recovery; 09 — Server-interruption recovery;
11 — Verified refund outcomes. These inherit all other implementation prerequisites.

**Status:** ready-for-human

- [x] Run full Python/React suites/build and real disposable-local-PostgreSQL migration,
  concurrency and financial-recovery gates with external providers mocked.
- [x] Complete mocked two-client code/research through voucher and live-credit paths,
  including purchase restoration, failure returns, timeout/clarification, coaching,
  reconnect, invitation removal and one-active-host behavior.
- [x] Review desktop/portrait/landscape/WebView browser layouts, busy/errors, keyboard,
  support, history and clean live copy; installed devices remain separate evidence.
- [x] Document setup/preflight for durable hosted storage, stable HTTPS/Google callbacks,
  live mode/webhook, invitations, public support email and independent pause controls.
- [ ] Present local screenshots/screen. Preserve explicit unresolved provider refund,
  fees/redelivery, actual Google/GCash and physical-device checks as rollout gates.
- [x] Include a later operator-authorized PHP 1 purchase/ten-credit award/run, hosted
  restart recovery and deployment checklist; execute none until separately requested.
- [x] Frozen main and current hosted service remain unchanged during this local gate.

## Comments

2026-10-08: Implemented locally for review. Shared verification is recorded in
PROJECT_LOG.md and docs/LIVE_TESTER_PAYMENTS.md. External-provider/hosted and
physical-device gates remain separate; no payment, cash refund or deployment
was performed by this implementation.

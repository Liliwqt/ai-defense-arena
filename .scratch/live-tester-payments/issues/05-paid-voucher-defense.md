# 05 — Run one paid or voucher defense per host

**What to build:** a host starts a code or research defense with live credits or a voucher,
sees reservation/charge history, and cannot accidentally run competing paid sessions.

**Blocked by:** 04 — Verified live awards.

**Status:** ready-for-human

- [x] Validate room/host/research budget before mutation; atomically acquire one active
  host claim and reserve ten credits, or authorize a zero-credit voucher run.
- [x] Allocate paid reservations to purchased lots deterministically; release the same
  allocations on opening failure and reacquire safely on opening retry.
- [x] Commit a once-only charge with validated first-question publication commitment;
  later questions, clarification and coaching add no cost.
- [x] Persist service ownership/generation and minimal outcomes; completion includes
  successful coaching, without storing papers, answers, private chat or transcripts.
- [x] Restart confirms a new cost and replaces outcomes/claims safely; denial preserves
  the current room. Current code/research flow, guest participation and clocks remain.
- [x] Show live cost/reservation/charge/restart/active-run messages in Account/Controls;
  prove concurrent starts, duplicates, opening failure, voucher rotation, logout and
  two-client progression with mocked AI and real local PostgreSQL transactions.

## Comments

2026-10-08: Implemented locally for review. Shared verification is recorded in
PROJECT_LOG.md and docs/LIVE_TESTER_PAYMENTS.md. External-provider/hosted and
physical-device gates remain separate; no payment, cash refund or deployment
was performed by this implementation.

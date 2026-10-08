# 04 — Confirm live payments and award credits once

**What to build:** after a matching signed paid event, the host sees Payment received and
exactly the frozen credit award, without manually authorizing the app.

**Blocked by:** 03 — Live QR purchase.

**Status:** ready-for-human

- [ ] Validate raw live signature, event/resource environment, bound intent/payment,
  account receipt, amount, currency and available metadata before settlement.
- [ ] Atomically record paid receipt and once-only live credit award; preserve payment
  identity uniqueness and paid terminality under registration or event retries.
- [ ] Early, delayed, duplicate and out-of-order delivery are safe; verified paid after
  failed/expired receipt can recover once, while failure/expiry itself awards nothing.
- [ ] Paid status refreshes the private balance; a refresh error preserves the confirmed
  receipt. Sandbox notifications/fixtures cannot fund the live wallet.
- [ ] Prove races, rollback and price/version preservation at HTTP/store boundaries and
  real local PostgreSQL; test the visible paid/history/balance flow with mock events.

## Comments

2026-10-08: Implemented locally for review. Shared verification is recorded in
PROJECT_LOG.md and docs/LIVE_TESTER_PAYMENTS.md. External-provider/hosted and
physical-device gates remain separate; no payment, cash refund or deployment
was performed by this implementation.

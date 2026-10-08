# 06 — Repair paid receipts that missed notifications

**What to build:** a genuinely paid receipt becomes paid and credits appear automatically
when its webhook was missed, even if the host closed the browser.

**Blocked by:** 04 — Verified live awards.

**Status:** ready-for-human

- [ ] Bounded startup/periodic server recovery retrieves the exact stored provider intent
  and validates the same binding/mode/amount/currency/payment evidence as settlement.
- [ ] Share the existing transactional once-only award with webhooks; their race cannot
  award twice. Browser status reads and redirects remain display-only.
- [ ] Persist retry/backoff and retain uncertainty on outage or unknown payment state;
  polling cannot create unlimited provider work or a new purchase.
- [ ] Recovery still honors issued receipts after invitation removal/purchase pause;
  current receipt/history/balance UI reveals its verified result.
- [ ] Test unknown/partial creation, missed/delayed notification, worker restart,
  wrong-evidence rejection and concurrent webhook/recovery against real local
  PostgreSQL with provider fixtures.

## Comments

2026-10-08: Implemented locally for review. Shared verification is recorded in
PROJECT_LOG.md and docs/LIVE_TESTER_PAYMENTS.md. External-provider/hosted and
physical-device gates remain separate; no payment, cash refund or deployment
was performed by this implementation.

# 11 — Reconcile operator-reviewed money refund outcomes

**What to build:** independently verified successful refund removes the matching held access
once; confirmed failure releases it, and uncertain processing stays visibly pending.

**Blocked by:** 10 — Refund review and credit holds.

**Status:** ready-for-human

- [x] Extend the operator procedure with verified provider refund binding, amount limits,
  environment, actor/reason/reference and once-only outcomes; no customer refund button.
- [x] Distinguish processing/claim pending from money received; uncertain submission or
  unverified reversal retains review/hold instead of retrying a cash refund blindly.
- [x] Success finalizes the correct purchase debit once; failure releases the hold once;
  later paid webhook/recovery cannot re-award refunded credits.
- [x] Show truthful private receipt/refund/credit history. Already-used-credit complaints
  remain operator-reviewed, not automatically approved or silently adjusted.
- [ ] Verify provider account capability/event contracts before enabling actual refund
  processing; unsupported evidence blocks it. Offline fixtures validate duplicate,
  wrong-identity/mode/amount, hold/charge and delayed-event races through PostgreSQL.
- [x] Writing or implementing this ticket does not authorize an actual money refund.

## Comments

2026-10-08: Implemented locally for review. Shared verification is recorded in
PROJECT_LOG.md and docs/LIVE_TESTER_PAYMENTS.md. External-provider/hosted and
physical-device gates remain separate; no payment, cash refund or deployment
was performed by this implementation.

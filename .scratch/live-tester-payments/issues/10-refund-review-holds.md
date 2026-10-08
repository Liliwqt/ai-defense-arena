# 10 — Review unused top-up refunds and protect their credits

**What to build:** a customer can contact support with a receipt, and the operator can review
unused-purchase eligibility and place an auditable hold without racing a defense.

**Blocked by:** 05 — Purchased-credit allocation and run lifecycle.

**Status:** ready-for-human

- [ ] Provide the configured email support link using receipt/category only, plus a
  private receipt's refundable/review/held state; no public admin/support form.
- [ ] Supported authenticated operator procedure verifies ownership and purchase use;
  normal unused requests differ from complaints about previously spent credits.
- [ ] A transactional hold protects the purchase lot from spending. An active reservation
  prevents that same lot entering refund processing until resolved; duplicate requests
  cannot multiply holds, and a held lot cannot fund a run.
- [ ] Record actor/reason/reference safely; historical spending and credit returns remain
  traceable. No manual SQL edits or customer claim grants/adjusts a balance.
- [ ] No cash refund is initiated by this ticket. Test email privacy, review states,
  lot/hold/reservation races and account UI against real local PostgreSQL.

## Comments

2026-10-08: Implemented locally for review. Shared verification is recorded in
PROJECT_LOG.md and docs/LIVE_TESTER_PAYMENTS.md. External-provider/hosted and
physical-device gates remain separate; no payment, cash refund or deployment
was performed by this implementation.

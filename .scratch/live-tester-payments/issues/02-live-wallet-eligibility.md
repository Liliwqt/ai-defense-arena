# 02 — Show a separate live wallet and top-up eligibility

**What to build:** a signed-in host sees live available/reserved credits and separate demo
history; invited accounts see the three live packages while all signed-in accounts
retain voucher redemption and guests retain joining.

**Blocked by:** 01 — Expand financial contracts.

**Status:** ready-for-human

- [ ] Add live wallet/credit-lot representation without transferring existing test/demo
  awards; normal migrated accounts initially have no purchased live credits.
- [ ] Derive identity from Google subject and invitation eligibility from verified email
  matched against the private server list, never client-submitted values.
- [ ] Display PHP 1/5/10 → 10/50/100 credits and ten-credit run cost; hide purchase actions
  for non-invited accounts with a brief explanation and visible voucher access.
- [ ] Voucher precedence/lifecycle, private account data and free uploads/joining remain
  intact; new-purchase and paid-start switches report truthful availability.
- [ ] Test identities, invitation removal, privacy, missing setup and migration balances
  through account/room boundaries, React and disposable local PostgreSQL.

## Comments

2026-10-08: Implemented locally for review. Shared verification is recorded in
PROJECT_LOG.md and docs/LIVE_TESTER_PAYMENTS.md. External-provider/hosted and
physical-device gates remain separate; no payment, cash refund or deployment
was performed by this implementation.

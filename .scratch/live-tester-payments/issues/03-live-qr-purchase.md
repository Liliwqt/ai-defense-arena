# 03 — Create and restore a live QR purchase

**What to build:** an invited host deliberately chooses a package, receives its verified
amount-specific live QR, and restores the same owned attempt after reload.

**Blocked by:** 02 — Live wallet and eligibility.

**Status:** ready-for-human

- [ ] Account/CSRF/origin/eligibility checks precede provider work; freeze terms on a
  durable receipt and bind the known provider intent as soon as possible.
- [ ] Replays reuse an account/provider/environment-scoped attempt; ambiguous responses
  preserve it instead of automatically creating another payable QR.
- [ ] Show exact amount/credits, generating/pending/uncertain state, expiry cue and a
  readable QR with short payment copy; no simulation or developer setup prose.
- [ ] Owner history and restoration work across clients/account changes, including an
  issued receipt whose owner later loses their top-up invitation.
- [ ] Creation awards no credits. Browser countdown/hiding/redirect cannot settle or
  promise cancellation. Test provider-response validation, replay/races, sign-out,
  privacy and desktop/phone QR readability with providers mocked.

## Comments

2026-10-08: Implemented locally for review. Shared verification is recorded in
PROJECT_LOG.md and docs/LIVE_TESTER_PAYMENTS.md. External-provider/hosted and
physical-device gates remain separate; no payment, cash refund or deployment
was performed by this implementation.

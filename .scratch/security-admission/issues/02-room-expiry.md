# 02 — Safe room expiry and reconnect recovery

**Blocked by:** 01 — Fair room creation and owner-managed closing.

**What it delivers:** Unused and finished rooms release shared capacity automatically, while active runs remain protected and teams receive readable expiry warnings instead of endless reconnect attempts.

**Status:** ready-for-human

Acceptance criteria:

- [ ] Add the proposed 30-minute meaningful-inactivity lobby expiry and 30-minute settled-terminal retention. Keepalive, polling, chat, denied actions and terminal reconnect do not extend the applicable retention.
- [ ] Expose server-owned expiry timing and two-minute warnings; preserve transcript download during retention. Expired-room handling stops reconnect loops without leaking prior membership.
- [ ] Use both periodic and admission-time cleanup, reusing the safe close/removal behavior from 01 and a consistent lock order.
- [ ] Never evict unsettled billing or pending timers, interpretation, preparation, generation or coaching. Authorized successful restart cancels terminal expiry; unauthorized/failed restart does not.
- [ ] Preserve ten-minute observed absence and financial compensation semantics. Check whether unresolved error states can settle under existing abandonment rules; resolve any required lifecycle gap explicitly before claiming those rooms are reclaimable. Never substitute forced deletion or a synthetic refund for settlement.
- [ ] Delete only in-memory room data; preserve durable receipts and run ledger. Stale asynchronous results cannot recreate rooms or duplicate financial writes.
- [ ] Fake-clock tests cover exact deadlines, meaningful activity, warning, terminal read retention, expiry/start/restart races, offline absence and settlement protection. UI tests cover expiry messaging and room-list recovery.

## Comments

2026-10-08: Implemented locally; required review against dd037d5 and selected-release gate follow. See docs/SECURITY_ADMISSION_REVIEW.md for checks and remaining hosted/native/user review boundaries. The Implement skill authorizes a local commit despite the earlier planning-only no-commit wording; no push/deploy. Checklists are retained for reviewer assessment rather than asserting unrun cases.

2026-10-09: Required review completed and behavioral findings fixed. Final selected-release gate: 384 Python (AI/Google/PayMongo mocked), 226 React/build. See the review document and final shared handoff for exact browser evidence and unverified hosted/native boundaries. Ready for user review; no deployment.

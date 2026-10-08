# 07 — Combined defenses and remediation evidence

**Blocked by:** 02 — Safe room expiry and reconnect recovery; 03 — Fair and retry-safe mobile sign-in; 05 — Bounded answer-clock pauses; 06 — Run-wide and owner-shared AI allowances.

**What it delivers:** A locally reviewable release that demonstrates the protections together without breaking code/research defenses, mobile recovery or financial invariants.

**Status:** ready-for-human

Acceptance criteria:

- [ ] Complete mocked two-client code and twelve-turn research defenses with voting, clarification, direct-answer recovery, timeout, AI failure/retry, reconnect, transcript and coaching. Include paid and voucher access, plus safe room close/expiry recovery.
- [ ] Verify desktop, portrait and landscape drafts, keyboard focus, expiry/countdown/status text, disabled retries and recovery actions. Record synthetic screenshots and preview evidence.
- [ ] Verify mobile HTTP/native-contract behavior, including reused already-open login flow and completion under admission pressure. Keep actual installed Android/iOS and hosted proxy checks explicitly pending unless separately evidenced.
- [ ] Run full Python tests with AI/Google/PayMongo mocked, full React tests and production build. Regression evidence must address each original source-validated finding and any remaining protected error-state lifecycle gap.
- [ ] Update README and the shared handoff log with final configurable limits, private data boundaries and results separated into offline, mocked browser, live and hosted evidence. Preserve unrelated files and deletions.
- [ ] Record residual many-account/distributed-network abuse risks. No production saturation, payment, credit adjustment, commit/push/deploy or frozen-main alteration is authorized by this ticket set.

## Comments

2026-10-08: Implemented locally; required review against dd037d5 and selected-release gate follow. See docs/SECURITY_ADMISSION_REVIEW.md for checks and remaining hosted/native/user review boundaries. The Implement skill authorizes a local commit despite the earlier planning-only no-commit wording; no push/deploy. Checklists are retained for reviewer assessment rather than asserting unrun cases.

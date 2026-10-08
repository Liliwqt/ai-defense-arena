# 04 — Bounded clarification and explicit direct answers

**Blocked by:** None — can start immediately.

**What it delivers:** A chosen defender can clarify twice, retry within a bounded interpretation allowance and still submit an explicit answer after the allowance is used, without triggering another interpretation request.

**Status:** ready-for-human

Acceptance criteria:

- [ ] Enforce two successful clarifications and the proposed six outbound interpretation attempts per turn before provider dispatch and before pausing the clock. Failed/invalid dispatched calls count; invalid authorization, local rejection and duplicate in-flight messages do not.
- [ ] Account for actual SDK outbound attempts; disable hidden automatic retries or prove each attempt is admitted. Introduce only the minimal reusable public attempt-accounting seam needed by 06.
- [ ] Add direct answer submission with current-turn, selected-defender, deadline, answer length and first-valid-answer validation. It records the server-owned name and bypasses interpretation, while later question generation remains normal.
- [ ] At exhausted clarification/interpretation allowance, reject ambiguous combined submissions with no interpretation call and offer the direct-answer action. Never record a request for simpler wording as an answer without explicit intent.
- [ ] Retain pending failed text and existing submitter-only use-as-answer recovery. The chosen defender can instead write a new direct answer. Host or another guest cannot convert someone else's pending text into an answer.
- [ ] Publish needed allowance/capability fields, preserve drafts on rejection, restore them and counters on reconnect, and clear drafts only after acknowledged turn resolution.
- [ ] Mocked WebSocket/React tests show exactly two clarifications, zero provider calls after rejection, bounded failure/retry, direct answer recovery, correct attribution, duplicate suppression and unchanged citation/coverage.

## Comments

2026-10-08: Implemented locally; required review against dd037d5 and selected-release gate follow. See docs/SECURITY_ADMISSION_REVIEW.md for checks and remaining hosted/native/user review boundaries. The Implement skill authorizes a local commit despite the earlier planning-only no-commit wording; no push/deploy. Checklists are retained for reviewer assessment rather than asserting unrun cases.

2026-10-09: Required review completed and behavioral findings fixed. Final selected-release gate: 384 Python (AI/Google/PayMongo mocked), 226 React/build. See the review document and final shared handoff for exact browser evidence and unverified hosted/native boundaries. Ready for user review; no deployment.

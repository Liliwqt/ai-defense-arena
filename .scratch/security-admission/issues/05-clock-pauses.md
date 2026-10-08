# 05 — Bounded answer-clock pauses

**Blocked by:** 04 — Bounded clarification and explicit direct answers.

**What it delivers:** Clarification and recovery cannot keep a question paused indefinitely; the chosen defender sees the authoritative remaining time and can answer directly before the effective deadline.

**Status:** ready-for-human

Acceptance criteria:

- [ ] Track the proposed 240-second cumulative pause allowance per turn, including failed-interpretation waiting and retries. Rejected requests grant no pause; reconnect and new submissions do not reset the allowance.
- [ ] Once the allowance is consumed, resume saved answer time on the server even in interpretation/recovery state, publish the effective deadline and maintain expiry scheduling.
- [ ] Preserve 15-second voting and 120 seconds of active answer time. Show readable pause/exhaustion/recovery status on desktop and phone layouts.
- [ ] Apply only current provider results before the effective deadline. Timeout, direct acceptance, restart and ending invalidate late results; pending text remains distinct from an accepted answer.
- [ ] Fake-clock and two-client tests cover boundary races, successful clarification, failed wait, retry, direct answer, timeout during interpretation/recovery, reassignment, reconnect and stale results without duplicate turns or invented answers.

## Comments

2026-10-08: Implemented locally; required review against dd037d5 and selected-release gate follow. See docs/SECURITY_ADMISSION_REVIEW.md for checks and remaining hosted/native/user review boundaries. The Implement skill authorizes a local commit despite the earlier planning-only no-commit wording; no push/deploy. Checklists are retained for reviewer assessment rather than asserting unrun cases.

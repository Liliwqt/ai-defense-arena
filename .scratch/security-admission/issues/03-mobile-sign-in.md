# 03 — Fair and retry-safe mobile sign-in

**Blocked by:** None — can start immediately.

**What it delivers:** Legitimate mobile sign-in retries reuse an attempt, while a single network cannot fill the shared queue without bounds. Users get a retry delay and existing verified attempts can still finish.

**Status:** ready-for-human

Acceptance criteria:

- [ ] Deduplicate a live challenge plus allowlisted destination without refreshing its five-minute expiry, resetting its opened state or replacing identity/code information.
- [ ] Apply the proposed 12 new flows per network/minute, 16 outstanding flows per network and 60 total start requests per network/minute, retaining the existing 128-flow process ceiling. Limiter state remains bounded and expiry/consumption releases capacity.
- [ ] Derive network identity only from the connection peer or a documented configured trusted proxy chain; spoofed forwarding headers and arbitrary installation IDs cannot bypass admission. Document IPv6 grouping and shared-network limits.
- [ ] Return safe HTTP 429 messages and bounded Retry-After. New-allocation throttling does not block existing OAuth return or proof-verified completion.
- [ ] Preserve verifier binding, random flow/code, one-time locked consume and session-store failure retry. An already-open reused flow must resume safely rather than reopen OAuth.
- [ ] Preserve Android/iOS compatibility, or include the minimal native change with mocked contract tests if a server-only safe resume is impossible. State clearly when installed-device evidence is unavailable.
- [ ] HTTP fake-clock/concurrency tests demonstrate deduplication, multiple legitimate users on one network, independent-network admission, forged-header rejection, expiry, store failure and one-time session issuance. No real Google call or production exhaustion test.

## Comments

2026-10-08: Implemented locally; required review against dd037d5 and selected-release gate follow. See docs/SECURITY_ADMISSION_REVIEW.md for checks and remaining hosted/native/user review boundaries. The Implement skill authorizes a local commit despite the earlier planning-only no-commit wording; no push/deploy. Checklists are retained for reviewer assessment rather than asserting unrun cases.

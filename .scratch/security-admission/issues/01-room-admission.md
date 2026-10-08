# 01 — Fair room creation and owner-managed closing

**Blocked by:** None — can start immediately.

**What it delivers:** A host can retain two rooms, inspect their own rooms and close an unused or settled room to make space. Excess or repeated creation is rejected before expensive parsing, with clear recovery controls.

**Status:** ready-for-human

Acceptance criteria:

- [ ] Enforce the proposed two-room account ceiling, three admitted creation attempts per minute and existing 20-room global ceiling, including concurrent in-flight creations.
- [ ] Reserve capacity atomically before reading/parsing uploads; preserve authentication, CSRF and validation. Release reservations on error, cancellation or the proposed 120-second processing timeout; late results cannot publish a room. Bound concurrent parsing to two workers.
- [ ] Expose owner-only room summaries and close controls. Nonowners cannot enumerate or close another account's rooms; guests retain their current join behavior. Do not expose account IDs, balances, voucher metadata or uploads in summaries.
- [ ] A host can close a lobby or settled terminal room, receiving a clear final room notice on all clients. Active/unsettled runs must use their established ending/recovery path first.
- [ ] Closing invalidates pending identities/tasks before releasing registry capacity. Neither rejected creation nor closing initiates a charge or credit return.
- [ ] Demo the two-room ceiling, successful close-and-create recovery and blocked third/concurrent upload through existing authenticated HTTP/WebSocket and React tests, with external providers mocked.

## Comments

2026-10-08: Implemented locally; required review against dd037d5 and selected-release gate follow. See docs/SECURITY_ADMISSION_REVIEW.md for checks and remaining hosted/native/user review boundaries. The Implement skill authorizes a local commit despite the earlier planning-only no-commit wording; no push/deploy. Checklists are retained for reviewer assessment rather than asserting unrun cases.

# 03 — Bounded processing and transient retry

**What to build:** new Standard interactive work has one bounded processing window
and an honest retry/recovery experience rather than an indefinite spinner.

**Blocked by:** 02 — Retained answers and failed-stage recovery.

**Status:** ready-for-human

Source: [confirmed specification](../spec.md). Breakdown approved on 2026-10-21.

- [x] Version new Standard processing policy with one 45-second authoritative window
  spanning stages, automatic retry/backoff and later evidence lookup; the window
  does not reset at stage changes or reconnect. Mapping/coaching keep deadlines.
- [x] Allow at most one automatic transient retry per processing operation, respecting
  remaining time, attempts, funds and current-work checks; no nested retry loops.
- [x] Automatically retry 429 only for a valid provider-supplied short Retry-After
  fitting all bounds. Missing/malformed/excessive delay, daily limits, exhausted
  funds or invalid configuration require honest manual/operator recovery.
- [x] Treat HTTP and streamed errors consistently with sanitized messages. Invalid
  decisions/JSON are not silently classified as transient provider failures.
- [x] Show actual retry/wait state and truthful delay when known; at expiry stop
  accepting results and expose recovery with saved work. No automatic model switch.
- [x] A deliberate manual recovery may start another bounded attempt only under
  existing checks; it cannot reset an answer/probe clock, quotas or run charge.
- [x] Preserve legacy policy semantics and Free's own limits/deadlines while applying
  shared bounded retry classification/presentation; no Free capacity promise.
- [ ] Verify before/at/after deadline, delayed retry, cancellation and stale completion
  through controlled clocks, plus real local spending-concurrency/hold checks.
- [ ] Present checkpoint 1's runnable current-pipeline status/recovery behavior and
  measured baseline capability without claiming fewer calls or faster AI yet.

## Comments

Implemented locally on top of ticket 02. One room-level 45-second interaction deadline starts at answer/probe submission, spans interpretation and the following question, and is cleared by terminal/manual paths; one transient retry is shared across that operation. Legacy retains its prior question retry but no interpretation auto-retry; Free remains windowless with one transient retry. Retry labels/countdown and expiry fencing are wired through React and snapshots. Offline evidence is 791 Python tests (AI mocked), 413 React tests and production build; isolated candidate 786 tests. Real local PostgreSQL spending/concurrency/hold checks and the checkpoint-1 runnable status presentation remain open, so this is ready-for-human at 7/9 criteria, not a live-ready claim. Committed locally as `00db48d`; no paid inference, hosted check, visual review, push or deployment.

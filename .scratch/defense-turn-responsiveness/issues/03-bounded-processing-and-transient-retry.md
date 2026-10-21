# 03 — Bounded processing and transient retry

**What to build:** new Standard interactive work has one bounded processing window
and an honest retry/recovery experience rather than an indefinite spinner.

**Blocked by:** 02 — Retained answers and failed-stage recovery.

**Status:** ready-for-agent

Source: [confirmed specification](../spec.md). Breakdown approved on 2026-10-21.

- [ ] Version new Standard processing policy with one 45-second authoritative window
  spanning stages, automatic retry/backoff and later evidence lookup; the window
  does not reset at stage changes or reconnect. Mapping/coaching keep deadlines.
- [ ] Allow at most one automatic transient retry per processing operation, respecting
  remaining time, attempts, funds and current-work checks; no nested retry loops.
- [ ] Automatically retry 429 only for a valid provider-supplied short Retry-After
  fitting all bounds. Missing/malformed/excessive delay, daily limits, exhausted
  funds or invalid configuration require honest manual/operator recovery.
- [ ] Treat HTTP and streamed errors consistently with sanitized messages. Invalid
  decisions/JSON are not silently classified as transient provider failures.
- [ ] Show actual retry/wait state and truthful delay when known; at expiry stop
  accepting results and expose recovery with saved work. No automatic model switch.
- [ ] A deliberate manual recovery may start another bounded attempt only under
  existing checks; it cannot reset an answer/probe clock, quotas or run charge.
- [ ] Preserve legacy policy semantics and Free's own limits/deadlines while applying
  shared bounded retry classification/presentation; no Free capacity promise.
- [ ] Verify before/at/after deadline, delayed retry, cancellation and stale completion
  through controlled clocks, plus real local spending-concurrency/hold checks.
- [ ] Present checkpoint 1's runnable current-pipeline status/recovery behavior and
  measured baseline capability without claiming fewer calls or faster AI yet.

## Comments

Not started. Local ticket publication does not authorize implementation, push or deployment.

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
- [x] Verify before/at/after deadline, delayed retry, cancellation and stale completion
  through controlled clocks, plus real local spending-concurrency/hold checks.
- [x] Present checkpoint 1's runnable current-pipeline status/recovery behavior and
  measured baseline capability without claiming fewer calls or faster AI yet.

## Comments

Implemented locally on top of ticket 02. One room-level 45-second interaction deadline starts at answer/probe submission, spans interpretation and the following question, and is cleared by terminal/manual paths; one transient retry is shared across that operation. Legacy retains its prior question retry but no interpretation auto-retry; Free remains windowless with one transient retry. Retry labels/countdown and expiry fencing are wired through React and snapshots. Offline evidence is 791 Python tests (AI mocked), 413 React tests and production build; isolated candidate 786 tests. Real local PostgreSQL spending/concurrency/hold checks and the checkpoint-1 runnable status presentation remain open, so this is ready-for-human at 7/9 criteria, not a live-ready claim. Committed locally as `00db48d`; no paid inference, hosted check, visual review, push or deployment.

Independent recheck, 2026-10-21: **corrections required**. Three confirmed runtime
findings: a funded writer can dispatch at the expired processing deadline; opening
history preflight can leave work generating beyond the cap; exhausted-credit429
can be automatically retried. Standards0documented violations/2nonblocking smells.
Reopened the affected criteria (4/9 remain checked);04 waits for corrected03.
Fresh57Python/providers mocked,22React/build and15real-local-PostgreSQL checks pass,
but the new deterministic probes demonstrate gaps in existing coverage. Baseline
PostgreSQL is now verified; corrected boundary regressions and checkpoint preview
remain open. See [independent recheck](../reviews/03-recheck.md). No runtime fix,
paid inference, commit, push or deployment during this review.

Correction pass, 2026-10-21: implemented the three confirmed recheck findings.
`backend/rooms/questions.py` now fences the funded provider at the captured
window deadline, checks expiry before budget admission, and bounds opening-history
preflight with the remaining window. `backend/openrouter_stream.py` and
`backend/processing_policy.py` classify exhausted-funds 429s from HTTP, SSE and
SDK errors as manual-only. Added controlled-clock regressions for no writer
dispatch after expiry, bounded history lookup with no budget leak, and no
automatic retry of exhausted funds. Offline gate: 794 Python tests (providers
mocked), 413 React tests and production build; the recheck deadline probes now
stop at expiry. Corrected real-local-PostgreSQL boundary/spending/hold evidence,
independent recheck of this correction pass, user review and checkpoint-1
presentation remain open. No paid inference, push or deployment.

Independent correction recheck, 2026-10-21: all three original correctness
findings resolved; Standards0documented breaches/0newactionable smells and
Spec0remaining correctness findings. Original probes pass;60focused Python checks
and16real-local-PostgreSQL checks pass with providers mocked, including corrected
expiry plus conservative dispatched-planner holds. Checked boundary/financial
criterion:8/9local checks complete. Checkpoint1 runnable presentation and user
review remain open;04 stays gated. Corrections remain uncommitted. See
[correction recheck](../reviews/03-fixes-recheck.md). No runtime/test change by the
reviewer, paid inference, push or deployment.

Checkpoint1 presentation, 2026-10-21: completed actual local browser workflow,
including stable operation/deadline through refresh, provider-directed retry,
retained-answer expiry/recovery, two-context question synchronization and complete
four-question mixed coaching/settlement. Desktop/portrait/landscape and keyboard
checks pass; Standard synthetic baseline/repeat emits108content-free records
across44operations. Normal accepted transitions still use3requests; no faster-AI
claim. Preview-discovered opening-retry wording corrected with red→green coverage,
independent Standards0/Spec0 and414React/build pass. All9local checks now complete;
human review remains separate. [Presentation](../reviews/03-preview.md), runnable
at http://127.0.0.1:8866/checkpoint-review. No paid inference, push or deployment.

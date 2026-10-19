# Ticket 03 — verified delayed-retry correction

Date: **2026-10-20**. User authorized fixing the remaining timer follow-up.
Source commit **c4d838d**. Correction diff `git diff 20dec1f...c4d838d`;
complete-ticket baseline **889a8e2**. Foreign dirty source and tests are excluded.

## Correction

Each Retry creates a fresh immutable pending submission containing the answer
or probe time remaining when that attempt starts. Saved text, speaker/token,
probe identity and input provenance are preserved. Existing pause settlement now
uses this attempt's remaining time, so waiting in recovery is never refunded.
The paused room snapshot also displays the correct remaining time. Coordinator
capture uses the new submission and interpretation ID, retaining stale-work
protection and direct-answer recovery.

Provider assignments, allowances, attempt limits, permissions, prices, charging
and the earlier immediate-failure correction are unchanged.

## Standards

Independent committed-source review: **0 hard violations and 0 actionable
smells**. The immutable replacement retains submission/provenance fields, and
worker captures remain consistent with production coordination. The fix, tests
and factual handoff stay within the authorized scope.

## Spec

Independent committed-source review: **0 remaining actionable findings**.
Capturing each attempt's current remaining time satisfies the preserved timeout
and failure-clock requirements without changing cumulative processing-pause
limits. Identity/version checks reject obsolete work. Tests exercise delayed
budget refusal, answer/probe clarification retries, repeated pauses and the
recipient-visible remaining-time snapshot.

## Verification

- TDD: the new repeated-retry test first failed with deadline 198000 instead of
  expected 138000. After the correction, processing time alone extends the clock;
  waiting during recovery stays consumed.
- Four focused modules pass **52 tests in 7.386s**, providers mocked, controlled
  clocks and temporary real SQLite.
- All four unchanged independent review probes pass **4/4 in 4.546s**: immediate
  provider/budget failure and delayed budget/clarification retry. The delayed
  retries retain original deadline 1135001 and time out there, with provider
  counts unchanged (2 for refusal, 4 for 503→clarification).
- Isolated artifact `.local/ticket03-retry-fix/artifact` contains the committed
  starting tree plus only the four owned runtime/test files; it excludes dirty
  reasoning/local-testing additions. Unchanged client build supplies static
  mounting. Logs `.local/ticket03-retry-fix/logs/{focused,review-probes}.log`.
- Full isolated Python discovery passes **673 tests in 125.415s**, external
  providers mocked, controlled clocks and temporary real SQLite. Log
  `python-full.log`; diagnostic stack dumps were enabled.
- Unchanged frontend passes **393 React tests in 36 files** and production build;
  logs `react.log`/`react-build.log`. This is mocked DOM/build evidence.
- No fresh PostgreSQL, visual browser, actual-provider compatibility/quality/cost,
  hosted transport or installed-device check is claimed. Database/provider code
  did not change. No paid calls, keys or private papers were used.

Final counts: **Standards 0; Spec 0**. Ticket 03 is ready for human review
locally. Ticket 04 remains independently unblocked; ticket 05 requires both
03 and 04. Actual-provider and user review remain separate. No push or deployment.

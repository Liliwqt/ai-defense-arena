# Ticket 02 — streamed provider-error fix

Date: 2026-10-19. User authorized fixing the remaining finding in
[the follow-up review](02-follow-up.md). Source commit **1efb1a1**;
correction diff `git diff c6ca8ac...1efb1a1`. The approved complete-ticket
baseline remains **bd10cc3**. Unrelated dirty source/docs were excluded.

## Correction

The shared parser now raises sanitized provider errors for HTTP200 SSE error
envelopes instead of treating them as malformed AI output. Valid numeric 4xx
statuses preserve manual recovery, including authentication, quota and 429.
Canonical `rate_limit_exceeded` also means429; supported 5xx/`server_error`
retain the existing one-retry post-answer policy. Unknown/malformed provider
errors stay manual. Malformed/truncated successful model output still uses
`InvalidQuestionResponse` and retains its earlier retry behavior.

Room lifecycle, prices, run accounting and charging are unchanged. Two-client
regressions verify that 429 leaves the accepted answer visible with exactly three
provider requests, whereas successful 503 recovery takes five. Dispatched failures
without verified usage still consume their full conservative reservation.

## Standards

Independent committed-source review: **zero hard violations and zero actionable
baseline smells**. Classification remains in the shared transport; tests live
under `tests/` with package-qualified imports and shared room setup. The log
identifies mocked evidence and does not claim provider/hosted/user approval.

## Spec

Independent review against **bd10cc3**, focused on **c6ca8ac...1efb1a1**:
**zero remaining actionable findings**. Manual versus bounded automatic recovery,
redaction, retained answers and conservative accounting satisfy the follow-up
requirement. Original citation/conversation findings remain closed. No scope
expansion or provider-readiness claim.

## Verification

- TDD: the new transport tests failed 23 subcases with the old parser, then passed
  all 3 tests after the change.
- Seven focused transport/two-client tests passed in 3.085 seconds, offline with
  providers mocked and disposable real SQLite.
- Isolated source artifact `.local/openrouter-02-sse-fix/artifact` contains the
  committed starting tree plus only the three fix/test files. Unrelated pending
  reasoning/local-testing files are excluded.
- The three original independent probes now pass 3/3 in 1.652 seconds. The unchanged
  SSE 429 reproduction now passes in 0.314 seconds. Providers mocked, dedicated
  temporary paper storage. Logs: `.local/openrouter-02-sse-fix/logs/` files
  `original-probes-recheck.log` and `sse-rate-limit.log`.
- React: all 393 tests pass in 36 files; production build passes against the unchanged
  tracked frontend in its normal project directory. Logs `react-recheck.log` and
  `react-build.log`. Initial isolated symlinked-node_modules check failed Vite's
  path restriction; the normal-directory rerun resolves that harness issue.
- Full Python discovery gate: **656 tests pass in 87.923 seconds**, offline with
  external providers mocked and real temporary SQLite. The isolated rerun used
  unittest discovery with diagnostic stack dumps and dedicated paper storage;
  log `python-full-recheck.log`. The initial run was interrupted after
  an existing guest-disconnect test waited for a missing snapshot; no assertion
  failure was reported. A separate concurrent probe hit private-storage locking.
  A clean rerun uses dedicated storage and diagnostic stack dumps, without
  altering runtime or tests to bypass a failure.
- Prior 185 real local PostgreSQL checks remain separate evidence from the earlier
  accounting implementation. Database/accounting code did not change here.
  No fresh PostgreSQL, browser, actual-provider quality/cost, hosted or installed
  native verification is claimed. No credentials or private papers were used.

Final counts: **Standards 0; Spec 0**. Ticket 02 is ready for human review
locally; tickets 03–04 are unblocked, not started. Actual-provider and user review
remain separate. No push or deployment.

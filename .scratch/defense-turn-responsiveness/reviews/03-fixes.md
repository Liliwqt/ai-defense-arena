# Ticket 03 correction pass

Date: 2026-10-21

Scope: the three confirmed runtime findings in
[the independent recheck](03-recheck.md). The recheck's nonblocking Standards
suggestions were not part of this correction pass.

## Findings addressed

1. **Funded writer dispatch after expiry.** `backend/rooms/questions.py` captures
   the operation's `window_deadline_ms` per attempt and `provider_stopped` now
   rejects dispatch once the workflow clock reaches it. Expiry is also checked
   before `ai_budget.admit`. The failure path converts a deadline-crossing error
   into `ProcessingWindowExpired`.
2. **Opening-history preflight outside the cap.** The lookup is bounded with
   `asyncio.wait_for` using the remaining window, with an expiry check before the
   lookup and before budget admission. Timeout maps to `ProcessingWindowExpired`;
   other storage errors retain the recoverable history message.
3. **Exhausted-credit 429 automatic retry.** `backend/openrouter_stream.py`
   recognizes provider funding markers in HTTP, SSE and SDK error metadata.
   `status_error` marks these responses manual-only; `ProviderStatusError.retryable`
   honors that; and `backend/processing_policy.py` returns no transient directive
   for an SDK `APIStatusError` with the same classification.

## Regressions added

- `tests/test_openrouter_questions.py::FundedQuestionClientTests.test_processing_deadline_stops_writer_before_dispatch`
  verifies the funded adapter dispatches only `PlanDraft`, publishes no turn,
  records no question operation, and fails with the bounded-window message.
- `tests/test_processing_policy.py::BoundedWorkTests.test_opening_history_lookup_is_bounded_by_the_processing_window`
  verifies a blocked history preflight yields at the logical deadline, leaves no
  operation visible, and does not admit AI budget.
- `tests/test_processing_policy.py::ProcessingPolicyTests.test_exhausted_funds_are_never_automatically_retried`
  verifies HTTP/SSE and SDK exhausted-funds 429s produce no retry directive.

## Evidence

- Full offline gate: `794` Python tests pass (providers mocked), and
  `(cd game && npm test && npm run build)` passes `413` React tests in 38 files
  plus the production build.
- Focused Python: `51` tests across `tests.test_processing_policy` and
  `tests.test_openrouter_questions`.
- Recheck controlled-clock probes now stop at the deadline. The funded-writer
  probe dispatches only `PlanDraft`, publishes no turn, and reports
  `ProcessingWindowExpired`. The history probe ends with `task_done: true` and no
  visible operation after a real 80 ms wait.
- `git diff --check` passes on the scoped files.

## Remaining

- Corrected-boundary real-local-PostgreSQL spending/concurrency/hold evidence was
  not rerun; the prior 15-check PostgreSQL baseline remains historical.
- This correction pass has not had an independent recheck or user review.
- Checkpoint-1 runnable presentation/baseline evidence remains open, so ticket 03
  is 7/9 and ticket 04 remains blocked.
- No paid/live provider, hosted, installed-device, push, deployment or visual
  approval is claimed.

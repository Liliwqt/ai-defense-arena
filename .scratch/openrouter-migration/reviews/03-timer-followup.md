# Ticket 03 — follow-up of the timer correction

**Superseding verified fix (2026-10-20):** source **c4d838d** closes the delayed-
retry time restoration issue. All four independent probes, Python 673,
React 393/build and Standards 0 / Spec 0 pass. See [the final fix handoff](03-retry-fix.md).
Earlier findings/verdicts below are historical. Actual-provider/user review
remains separate; no push/deployment.

Date: **2026-10-20**. Reviewed `git diff 84b5542...20dec1f`: source correction
**8e973ac**, handoffs **3fcdd7f** and **20dec1f**. The approved complete-ticket
baseline remains **889a8e2**. Unrelated dirty work is excluded.

**The original four-minute pause finding is fixed. One P2 remains in delayed
retry settlement.** Runtime and canonical tests were not changed by this review.

## Standards

Independent Standards review: **0 hard violations; 0 actionable code smells**.
The previous current-status P3 is corrected. Shared pause helpers appropriately
gather the timing logic. The correctness finding below belongs to the Spec axis.

## Spec

### P2 — Preserve answer time consumed while waiting before Retry

Requirements: “Preserve … timeout rules” and “Do not freeze authoritative answer
timers on provider or budget failure.”

`backend/timed_turn.py:221` restores `pending.remaining_ms`, captured when the
original submission began. Failure now correctly resumes the clock, but
`retry_interpretation()` at line322 re-arms processing without refreshing that
saved remaining time. A subsequent failure or clarification restores time that
already elapsed while the defender waited in recovery.

Two controlled-clock, two-client probes against committed **20dec1f** confirm:

- Initial immediate budget refusal or HTTP503 correctly leaves deadline
  **1135001**, unpaused.
- Wait **100000ms** before Retry, then use zero simulated processing time.
- Another allowance refusal or successful clarification changes the deadline to
  **1235001**, refunding all **100000ms** of waiting.
- Catch-up at the original deadline plus1 leaves `timed_out=false`, in
  `interpretation_retry` or `question` respectively.
- Request counts stay correct: **2** for exhausted allowance; **4** for HTTP503
  followed by clarification. This is a clock defect, not a funding bypass.

Correction: each attempt must settle against its own remaining time at attempt
start. Preserve time already consumed during recovery and all stale-work guards;
add delayed-retry coverage for both failure and clarification, including probe
replies. The new canonical retry test retries immediately, so it misses this
case. The original immediate-failure correction and two original probes pass.

No other concrete actionable Spec finding was identified.

## Verification

- Exact `git archive 20dec1f` under
  `.local/openrouter-03-timer-followup/artifact`; unchanged client build supplied
  only for FastAPI mounting. No dirty reasoning/local-dev files are included.
- Four focused modules (`tests.test_timed_turn`, `tests.test_panelist_probe`,
  `tests.test_clarification`, `tests.test_openrouter_interactions`) independently
  pass **48 tests in6.449s**.
- Both unchanged original timer probes now pass **2/2 in0.548s**, with original
  deadlines restored and timeouts occurring at those deadlines.
- Two new delayed-retry probes both **fail**, independently confirmed by parent
  in **0.567s**. Source:
  `.local/ticket03-spec-probes/ticket03_delayed_retry_probes.py`.
- Logs `.local/openrouter-03-timer-followup/logs/{focused,original-probes,delayed-retry}.log`.
  External providers mocked, controlled clocks, temporary real SQLite, dedicated
  document directories. Run exactly the two new probes from the artifact:

```bash
ROOM_DOCUMENT_DIR=/tmp/ibm-bob-ticket03-delayed-followup \
/home/jhonryl-pamaybay/IBM-BOB/.venv/bin/python -c \
"import sys, unittest; sys.path.insert(0, '/home/jhonryl-pamaybay/IBM-BOB/.local/ticket03-spec-probes'); unittest.main(module='ticket03_delayed_retry_probes', argv=['unittest', 'DelayedRetryProbes.test_delayed_budget_retry_preserves_consumed_answer_time', 'DelayedRetryProbes.test_delayed_successful_retry_preserves_consumed_answer_time'], verbosity=2)"
```

The implementation agent's full669 committed Python /393 React/build evidence
remains separate. This focused follow-up does not claim a fresh full suite,
PostgreSQL, browser, actual-provider, hosted or native check. No credentials,
private papers or paid inference were used.

Final counts: **Standards0; Spec1 P2**. Reopened only the timer criterion/status
ready-for-agent. Ticket04 remains independently unblocked;05needs corrected03
and04. No runtime/canonical test edit, commit, push or deployment.

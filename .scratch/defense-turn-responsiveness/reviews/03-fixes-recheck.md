# Ticket 03 correction recheck

Date: 2026-10-21. Outcome: all three reported correctness findings resolved.
Original full-range baseline: `c31cf8f`. Correction baseline: `d7e8181`.
The corrections are uncommitted; immutable scoped patch, hashes and candidate are
in `.local/turn03-fixes-recheck/`. Reviewed four exact owned source/test files and
only the new deadline regression graft in tests/test_openrouter_questions.py;
foreign budget diagnostics, usage-only tests, reasoning and planning were excluded.

## Standards

Independent correction review: **0 documented violations, 0 additional actionable
smells**. Existing nonblocking bounded-await duplication and version-string
suggestions from [the earlier review](03-recheck.md) remain maintainability notes.
Funding classification is centralized and reused; typed expiry failures and
package boundaries are retained. The correction does not change frontend code.

## Spec

Independent correction review: **0 remaining correctness findings, no scope creep**.
All three original failures now pass their reproductions:

1. The captured authoritative deadline reaches the funded provider's stopped
   predicate. The real-adapter synthetic probe dispatches only PlanDraft at time1000,
   stops at the45000ms boundary, publishes no turn and exposes retry. QuestionDraft
   never dispatches at expiry. Existing conservative spending holds remain intact.
2. Opening-history preflight is bounded by the same remaining window, with expiry
   checked before AI admission. The original blocked-history probe now finishes
   in recovery, with no visible operation and no provider request; late lookup
   results cannot advance the run.
3. Exhausted-credit429 with short Retry-After is denied automatic retry for HTTP,
   streamed-envelope and SDK error paths. All three original direct probes now
   return allowed=False. Sanitized operator guidance replaces raw provider text.

The independent reviewer reproduced the quota regression and inspected the other
fixes. Their restricted history test body reported success but stalled in executor
shutdown; interrupted subprocesses are not counted as completed passing gates.
The root's normally permitted local-thread runs below completed successfully.

## Verification

- **60 focused Python checks passed in19.354s** on the isolated correction artifact:
  processing policy, OpenRouter stream, retained-stage recovery, funded interactions
  and the new funded deadline regression. Provider HTTP mocked; temporary realSQLite.
- Original real-funded-adapter deadline, blocked-history and three quota probes
  pass against the corrected artifact. Logs/scripts remain under `.local/`.
- **16 real-local PostgreSQL16.15 checks passed**, external providers mocked:
  the corrected funded deadline regression plus conservative unresolved-planner
  hold check passed in1.048s;15existing allowance/concurrency, protected coaching,
  opening-history and integrated text checks passed in21.437s, including complete
  twelve-question research/mixed runs and partial-result recovery. Every check
  used its own disposable database; the loopback instance has been stopped.
- Frontend source is unchanged since the previous independent22React checks and
  production build. No frontend or full Python gate rerun was needed for this
  backend correction recheck. The implementer's794Python/413React/build totals
  remain reported historical evidence, not independently rerun full-suite totals.
- Root/frozen source hashes remained stable throughout this review. Production
  source and canonical tests were not modified by the reviewer.

The boundary/financial criterion is now checked: ticket03 has **8/9** local checks
and remains ready-for-human. Checkpoint1 runnable status/recovery/baseline preview
is still open; human visual approval is not claimed. Ticket04 remains gated on
that handoff/acceptance. Corrections remain uncommitted. No paid inference,
real-provider speed/quality/cost, hosted/native/device check, push or deployment.

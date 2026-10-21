# Ticket 06 correction review

Date: 2026-10-22. User-approved comparison: `4b25a6f` to the isolated uncommitted
candidate. Thirteen runtime/test files were frozen under
`.local/turn06-fixes/checkpoint`; foreign reasoning/budget/planning edits were
excluded. This adopts the unfinished `defense-turn-06` implementation and resolves
the six findings in [the original check](06-recheck.md).

## Standards

Independent review: **0 documented hard violations**. One minor, nonblocking
possible Speculative Generality remains: `Expansion.query` retains the lookup
query even though current recovery/rendering uses its result. It is not emitted
in operation telemetry. The final test-only PostgreSQL integer conversion adds
no new Standards findings.

## Spec

Independent review: **0 remaining actionable findings and no scope creep**.
All six original gaps are addressed:

1. Standard interpretation, clarification and probes now use focused source
   context alongside the planner/writer, preserving required history and language.
2. Numbered `FILE` identities and original locations survive source rendering;
   final citation validation still uses the complete accepted upload.
3. Explicit lookup is an alternative to the existing result contract. Mixed
   decisions, invalid IDs, repeated lookup and empty results recover honestly.
4. Current/selected evidence takes priority; eligibility uses `topic_id`.
5. Numerical limits are captured per run and supported by synthetic measurements.
   Lookup bytes/count/duration are recorded. Ordinary start sizing is restored;
   every optional lookup reserves its actual bounded request from remaining
   question funds. It cannot consume protected coaching. No promise is made that
   the initial allowance funds every possible retry/lookup.
6. Authenticated two-client tests cover late decisive evidence, cross-document
   citations, qualitative/theoretical/mixed/unclear profiles, clarification,
   probes, writer retry, pending answers, deadlines and complete defenses.

An integrated controlled-clock regression also exposed an interpretation lookup
continuation dispatching at the processing deadline. The room cancellation fence
now includes that captured deadline; the regression passes. Cached question
evidence clears when material inputs/preparation or lifecycle identity changes.

## Verification

Checks ran against the scoped isolated candidate, not the foreign dirty tree.

- `.venv/bin/python -m unittest discover -v`: **824 passed in 230.707s**, offline,
  AI/Google/payment providers mocked.
- `(cd game && npm test && npm run build)`: **414 tests passed**, production build
  passed. Existing PDF chunk-size advisory remains.
- Real local PostgreSQL 16.15: `PostgresFocusedRoutes`,
  `PostgresProtectedCoachingAllowances`, `PostgresDefenseAllowances`, and
  `PostgresCombinedInteractions.test_concurrent_combined_dispatch_preserves_protected_funds_and_unknown_hold`:
  **16 passed in 22.851s**, provider HTTP mocked. Includes complete room flows,
  concurrent reservations, unknown holds and protected funds.
- Focused evidence/provider/routes/recovery selection: **50 passed** before the
  final additional malformed-response/profile cases, which are included in the
  full gate above.
- After that full gate, the PostgreSQL test fixture needed an exact `int`
  conversion for its integral `SUM(bigint)` result. Runtime spending validation
  was unchanged. The corrected case passed once on SQLite and in the fresh
  16-case PostgreSQL gate; independent delta review remained clean.
- `python -m tests.evidence_context_harness`: four synthetic study cases compare
  4/8/14 excerpt limits. Chosen 14 retains 9/9 required passages in 7,903–8,503
  focused bytes versus 98,711–109,464 accepted-source bytes. Smaller limits drop
  required passages. These measure view sizing/coverage, not real AI quality,
  latency or total request cost.

Earlier fixture failures, sandbox-blocked localhost attempts and stalled checks
are excluded from passing evidence. The final successful PostgreSQL result
supersedes the failed fixture run. No actual inference, new browser visual review,
human approval, hosted verification or installed-device check occurred.

Ticket 06 is **ready-for-human, 8/8 local checks**. Tickets 07/08 are unblocked
but unstarted. Actual model schema compatibility, speed, grounded conversation
quality and billed cost remain separate provider evidence. Local commit only;
no push or deployment.

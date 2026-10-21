# Ticket 01 independent re-review

Date: 2026-10-21
Outcome: corrections required; ticket returns to ready-for-agent.
User-approved baseline: 4af094cbc8e281561e6d2c24b8f8e245f8c560ba.

Reviewed the corrected, uncommitted implementation with independent Standards
and Spec reviewers. The frozen patch, candidate and hashes are under
`.local/turn01-rereview/`; 26 tracked implementation/test files and seven new
files are in scope. The pre-existing budget diagnostic edits in
`backend/openrouter_questions.py` were excluded while retaining its new timing
hook. Other foreign reasoning, local-testing, QR and planning edits are excluded.
Reviewed source hashes remained unchanged through verification. No runtime fixes,
commit, push or deployment were performed.

## Standards

**Zero findings.** No documented-standard breaches or further actionable smell
recommendations. The original nonblocking label-duplication finding is resolved:
shared helpers now serve operation and fallback branches, and mapping imports
the same label helper. The usage collision independently observed by both
reviewers is recorded under Spec as correctness, not as an invented hard rule.

## Spec

**Three P2 findings remain.** No scope creep identified in the corrected patch.

1. **Concurrent rooms overwrite or consume each other's supplied usage.**
   `bind_operation` keys process-global usage storage by operation ID, but rooms
   independently generate the same IDs, such as `question:1`. Binding room B
   clears room A's receipts; finishing or cancelling either consumes the shared
   entry and unregisters both. Separate task/context probes confirmed A supplied
   10 tokens, B supplied 20, A finished with B's 20/model and B subsequently lost
   its usage. This violates the ticket's “available supplied usage” capture and
   undermines comparisons when multiple rooms are active. Use a globally unique
   internal collection identity scoped to the room/run/operation; preserve the
   compatible public snapshot if desired. Include concurrent cancellation tests.
   [Usage binding](/home/jhonryl-pamaybay/IBM-BOB/backend/room_operations.py:123),
   [usage consumption](/home/jhonryl-pamaybay/IBM-BOB/backend/room_operations.py:156),
   [room-local question ID](/home/jhonryl-pamaybay/IBM-BOB/backend/rooms/questions.py:76).

2. **Failed coaching generation stages are logged as successful.** Section
   exceptions retain their class, but the worker unconditionally advances to
   `saving_completion`, whose transition records the preceding stage as
   `succeeded`. A provider or section-validation failure therefore appears as
   successful generation followed by failed saving, even when saving never ran.
   The corrected total retains the failure class; per-stage outcomes remain
   misleading. The specification requires “provider failure/validation outcome”
   with stage timing. Record the failed stage at its actual failure, and avoid
   classifying unperformed saving as the source of failure.
   [Section failure and transition](/home/jhonryl-pamaybay/IBM-BOB/backend/rooms/coaching.py:203),
   [stage transition outcome](/home/jhonryl-pamaybay/IBM-BOB/backend/rooms/model.py:120).

3. **The synthetic baseline runner bypasses research/mixed defenses.** It now
   executes real workflow functions and carries case/condition/run metadata,
   improving on the prior JSONL-only harness. However, its default room is code,
   its fixture is Python, it manually changes/appends turns to force completion,
   and coaching blocks until cancellation. It never exercises research/mixed
   mapping, planner/reviewer progression or progressive coaching. Consequently
   the ticket's comparable baseline for “existing research/mixed flows” is still
   partial. Add bounded synthetic research/mixed cases that execute the current
   target pipeline and emit linked measurements. This does not require paid
   inference or the future optimized pipeline; model-quality evidence stays in 08.
   [Synthetic runner](/home/jhonryl-pamaybay/IBM-BOB/tests/operation_timing_harness.py:116).

The earlier operation-start publication, default logging, retry-wait
presentation and post-storage completion timing findings are corrected. Usage
forwarding and executable replay exist but remain partial as described above.

## Verification and limits

- Fresh isolated operation/harness checks: **19 passed**, excluding the
  thread-backed supplied-usage test. Includes publication and both coaching
  completion tests. A narrower repeated selection passed 17; these are not
  additional distinct checks. AI/providers and clocks are mocked.
- Fresh React checks: **72 passed** across WaitingIndicator, waiting
  presentation, QuestionCard, AnswerComposer, CoachingReport, whole-App stages
  and progressive Results.
- Controlled publication probes now observe operation identity before blocked
  question/interpretation inference. The minimal actual progressive-completion
  probe with validation/storage mocked records the full 7000 ms stage and total
  after storage advances the clock. Default Uvicorn logging test passes.
- Independent separate-context/task probes reproduce cross-room usage
  corruption. A minimal call of actual `run_progressive_coaching` with a mocked
  request failure records 3000 ms of failed overview generation as `succeeded`,
  followed by a 0 ms failed saving stage although no saving occurred. Scripts
  and output: `.local/turn01-rereview/probe_spec_remaining.py` and
  `probe_spec_remaining.jsonl`. No real provider or private paper was used.
- The broader focused Python command stalled and was interrupted (exit 130);
  it is not a passing gate. Reviewers likewise reported a thread-backed check
  stall. No cause or runtime regression is inferred merely from those stalls.
- The correction handoff reports 751 Python / 409 React and production build
  passing; those full gates were **not independently rerun** in this re-review.
  Passing tests do not contradict the uncovered concurrency/stage/path gaps.
- Integrated actual-room/browser, native Streamlit, installed-device, hosted,
  real-provider quality/cost/speed and human visual approval remain separate,
  unverified evidence. The existing two interface/lifecycle criteria stay open.

Reopened only measurement capture and comparable baseline criteria, leaving
**5/9 checked**. Ticket 01 is ready-for-agent; ticket 02 remains blocked.

Totals: Standards **0** (no worst issue); Spec **3 P2**, worst within Spec:
cross-room usage attribution corruption.

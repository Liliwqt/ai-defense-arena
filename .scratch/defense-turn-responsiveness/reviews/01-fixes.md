# Ticket 01 correction verification

Date: 2026-10-21
Outcome: all three re-review findings resolved locally; human/interface evidence remains open.
User-approved comparison baseline: 4af094cbc8e281561e6d2c24b8f8e245f8c560ba.

The user requested fixes after [the independent re-review](01-rereview.md).
Changes remain uncommitted on main. The frozen candidate, scoped patch and source
hashes are under `.local/turn01-fixes/`. Pre-existing budget, reasoning,
local-testing, QR and planning work remains separate; no foreign runtime/test
file changed during this correction. No commit, push or deployment occurred.

## Standards

Independent Standards review: **0 documented breaches or actionable smells**.
The correction preserves package boundaries, compatible room snapshots and
content-free records. The final coaching initialization hunk was also reviewed.

## Spec

Independent Spec review: **0 remaining actionable code findings** in the scoped
ticket implementation. All three prior P2 findings are resolved:

1. **Usage isolation.** Every operation has an opaque lifetime key used for
   collecting and releasing supplied usage. Public room-local operation IDs stay
   compatible. Stage/total records include a content-free measurement identity
   for correlation. Concurrent rooms, cancellation, reused public IDs and late
   callbacks no longer consume another operation's receipts.
2. **Accurate coaching outcomes.** Each generated section closes its stage with
   its actual success/failure. A later successful batch cannot overwrite an
   earlier failure. Incomplete cards bypass completion saving; total failure uses
   an available real exception class, without inventing one. Failed-only retry
   starts at pending answer work; completion-only recovery starts at saving.
   Retry labels derive from actual attempts, not generation-version increments.
3. **Target-pipeline baseline.** Research and mixed synthetic cases use real
   coordinator commands for explicit mapping, profile/budget confirmation,
   funded start, votes, alternating defenders' answers and progressive coaching.
   Real funded mapping/planner/reviewer/interaction/coaching clients run against
   mocked SSE HTTP and temporary real SQLite. No turns are manually appended to
   force completion. The runner checks retained answers, shared views, cards and
   settlement. Fingerprints reject same-ID comparisons with changed sources or
   answers. Exported records contain no source/answer text.

The stage/retry initialization correction was found during final review, made
red-capable in existing tests, fixed, and reviewed before the last full gate.

## Verification

- Regression checks were observed failing before fixes: cross-room receipts,
  cancellation/public-ID reuse, failed-stage attribution, target pipeline kinds
  and truthful first-attempt/retry labels.
- Final focused operation/harness modules: **26 passed**, offline, providers and
  clocks mocked. Covers failed overview, failed middle batch followed by success,
  failed-only retry, receipt lifetime and complete research/mixed runs.
- Final `.venv/bin/python -m unittest discover -v`: **757 passed in 136.110s**,
  offline, AI/Google/payments mocked. Normal local socket/thread access was used;
  restricted-sandbox executor cleanup stalls were not counted as passing runs.
- `(cd game && npm test && npm run build)`: **409 React tests passed** and
  production build passed. Frontend source was unchanged by these corrections.
- CLI synthetic comparison/replay: both research and mixed, baseline and
  candidate, **108 content-free records**. Each case/condition completes one map,
  five question operations (four questions plus completion planning), four answer
  interpretations and one progressive-coaching operation. Candidate timings are
  deliberately scaled fake-clock durations; they establish instrumentation and
  comparison structure, **not real provider speed, cost or quality**.
- Python compilation, owned-file whitespace and frozen-source hash checks pass.
  Runtime/test files outside the six correction files match the preceding review.

The independent Spec reviewer also ran four tight regression checks successfully.
Their harness test body passed but its restricted process stalled during cleanup;
that interrupted command is not a complete suite pass. The root's final gate and
CLI evidence above completed successfully.

## Remaining evidence

Integrated actual-room/browser lifecycle, native Streamlit, installed-device,
hosted/provider quality/speed/cost and human visual review remain separate and
uncompleted. Restored only measurement-capture and baseline criteria: **7/9
checked**, ticket 01 ready-for-human. Ticket 02 stays blocked until 01 is accepted.
No user review or live readiness is implied by independent code review.

Totals: Standards **0**, Spec **0** actionable code findings; no worst issue on
either axis. The two existing interface/lifecycle evidence criteria remain open.

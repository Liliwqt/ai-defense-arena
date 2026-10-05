# Architecture checkpoint review

Reviewed locally on 2026-10-06 against user-selected baseline `99f2433`.
Spec: [ARCHITECTURE_PLAN.md](ARCHITECTURE_PLAN.md).
Commands: `git diff 99f2433...HEAD`, `git log 99f2433..HEAD --oneline`;
review cleanup was additionally examined with `git diff HEAD` before commit.
Standards and Spec were reviewed by separate read-only agents.

Selected implementation commits:

| Commit | Scope |
| --- | --- |
| 9b8a593 | Records prior backend payment cleanup as a dependency; not new architecture scope |
| 6506267 | Timed-turn state and room adapter |
| 0476aa5 | Purchase persistence and HTTP/account adapters |
| a8f40ab | Detached generation and shared progression |
| c22f42c | Session-owned defender/clarification metadata following review |

Earlier frontend cleanup, upload progress and unrelated deletions remain outside
these commits. Payment behavior was compared with the saved pre-refactor working
files as well as the Git baseline.

## Standards

No hard documented-standard violations found. One judgment-call Feature Envy /
Message Chains finding concerned direct nested writes to session clarification
history and assigned defender. Resolved with `assign_current_defender` and
`record_clarification` on `DefenseSession`, used by TimedTurn and Streamlit.
Follow-up review confirmed resolution and no issues in approved agent guidance.

## Spec

No actionable findings. Both defense adapters share detached generation and
validated move application; multiplayer retains version checks and opening
charges before publication. Selection, deadlines, clarification time, retries,
attribution, serialized purchases, once-only awards, rollback, private history
and legacy receipts were preserved. The metadata cleanup also passed follow-up
spec review.

Standards: 0 remaining findings (1 heuristic resolved); Spec: 0 findings.

## Evidence and limits

- Full working-tree gate: 211 Python tests (external providers mocked),
  163 React tests and production build passed.
- Real-local PostgreSQL: 64 tests passed with external providers mocked.
- After review cleanup: 47 focused offline tests passed; the added metadata test
  ran red before implementation and green afterward. The earlier full gate is
  separate evidence, not a claimed 212-test rerun.
- Isolated selected-commit check: committed React build and 51 focused Python
  tests passed without pending frontend/payment work. Initial missing build
  directory was resolved by running the documented build first.
- Final real loopback two-browser check, AI/identity mocked: 4- and 8-turn code
  and 12-turn mixed/proposal defenses passed after cleanup. It checked votes,
  unauthorized answers, clarification, retry, timeout, exact citations,
  attribution, reconnect, transcript, coaching, and zero/10-credit charges.
- Synthetic desktop/landscape captures:
  `screenshots/architecture-{4,8,12}-turn-mock-{desktop,landscape}.png`.
  No horizontal page overflow was observed. Chat synchronized and reconnected;
  ArrowRight/ArrowLeft switched dock tabs with focus and selected state.

No live AI-quality, Google, PayMongo, hosted, physical-device or user visual-review
claim follows from these mocked checks. Main and hosted services are unchanged.


## Publication preparation — 2026-10-06

A release inspection caught the old committed checkout screen's requirement for
`order_token`, removed by the prior backend cleanup. The already-tested local
checkout UI dependency is now committed as `c17fd64` with shared purchase labels.
Its separate Account UI and upload-progress changes remain local. The isolated
final release passes 212 mocked-provider Python tests, 156 React tests and the
production build. These supersede the earlier isolated subset for deployment;
the prior full working-tree counts still include unpublished frontend changes.
Hosted verification is pending and no real purchase is claimed.

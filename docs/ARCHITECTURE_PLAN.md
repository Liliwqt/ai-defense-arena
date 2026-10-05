# Architecture improvement specification

Started 2026-10-06 on `feature/question-first-room`.

Status: implemented and locally verified on 2026-10-06; Standards and Spec review
complete. [Review evidence](ARCHITECTURE_REVIEW.md). The user selected all round-one
recommendations and explicitly invoked Implement. Deliver three separate local
checkpoints, preserve behavior, and use local suites/integration checks. Glossary:
[CONTEXT.md](../CONTEXT.md).

## Existing constraints

- Main remains frozen and the live releases remain unchanged during local planning.
- Preserve uncommitted payment cleanup, measured upload progress, unrelated files and screenshot deletions.
- Keep the fixed four defender seats, current room messages and source-grounding guarantees.
- Keep code defenses at four-to-eight turns and research defenses driven by their approved coverage budget.
- Keep 15-second voting, two-minute answering, clarification intent, server deadlines, retry and reconnect guarantees.
- Keep the sandbox purchase and flat run-charge distinction, host ownership, CSRF checks, duplicate protection and private account data.
- Rooms remain ephemeral; SQLite and PostgreSQL are existing account-store adapters.

## Checkpoints

### Timed-turn module

Recommendation: first checkpoint. Concentrate the rules for voting, speaker
selection, answering, interpretation, clarification pause/retry and timeout in
one deep module. Authorization, purchase reservation/charge/release, model calls
and socket publication stay outside this proposed scope. Keep the existing
defense policy and atomic research-move validation.

Evidence: game_server.py deadline helpers, action handling and interpretation
completion share ordering knowledge. test_timed_room.py and test_clarification.py
manually configure phases/deadlines and patch server scheduling helpers.

Selected design: `TimedTurn` owns synchronous turn state. Explicit millisecond time
and optional random choice make boundary tests deterministic. The room adapter
owns asynchronous tasks, sockets, account checks and charges. Clock and
interpretation IDs reject stale results.

### Purchase transaction module

Recommendation: separate checkpoint. Concentrate persisted request reuse,
checkout attempt limits, receipt transitions and atomic once-only credit awards.
Retain identity, raw-body signature verification, provider requests and HTTP error
translation in their existing adapters. Preserve database transactions and legacy
receipt compatibility.

Evidence: payments.py holds transaction rules in checkout and webhook paths;
account_store.py joins receipts and awards for private account history.

Selected design: `PurchaseStore` owns persisted purchase transitions. Domain
errors are translated by HTTP adapters; history can run in the balance snapshot
transaction. Preserve the existing schema and prior cleanup behavior; audit
remains a separate read-only consumer.

### Shared defense progression

Recommendation: separate checkpoint. Share history/context preparation and
code/research generation selection between the multiplayer and Streamlit
adapters. Keep asynchronous execution, stale-result checks and first-question
charging with the multiplayer adapter.

Evidence: defense_session.py advance_defense and game_server.py generation
orchestration repeat dispatch and move application. Calling the synchronous
mutating fallback path from asynchronous generation would not preserve stale
result or charging guarantees.

Selected design: prepare a detached session, dispatch through the same generators,
validate the candidate, and commit it while preserving the existing session
identity. Multiplayer retains generation-version and opening-charge guards;
Streamlit uses the same preparation and application without asynchronous tasks.

## Interview frontier — round 1

1. Deliver these as separate reviewed checkpoints or one combined refactor?
   Recommendation: timed turns, then purchase transactions, then shared progression.
2. Strict behavior preservation or include intentional behavior improvements?
   Recommendation: preserve behavior; report discovered defects separately.
3. What evidence is required for a local checkpoint to be ready?
   Recommendation: offline suites, mocked two-browser flows and real-local database
   checks for purchase work; optional live-provider verification separately.

All three recommendations accepted. The implementation request is confirmation to
proceed within those constraints; routine internal design choices are recorded below.

## Implementation and verification seams

- Timed turns: a synchronous state module owns vote/answer deadlines, selection,
  pending interpretation and accepted attribution. The existing room adapter keeps
  locks, task cancellation/scheduling, account checks, charging and publication.
  Tests exercise vote → interpretation → clarification/answer/timeout through the
  module's public interface, with explicit time and existing random-choice adapters.
- Purchases: a persistence module owns transactional checkout request reuse,
  limits, registration, receipt lookup, award reconciliation and private history.
  Existing checkout/webhook/receipt interfaces remain the integration test seams;
  SQLite and PostgreSQL keep their current locks and schema compatibility.
- Progression: prepare an isolated generation request and validate its result
  before applying it to a session. Both real adapters use that shared module;
  multiplayer checks generation versions and finalizes the opening charge before
  publishing. Existing public defense policy and generator-request behavior remain
  test seams.
- Keep caller-visible wire snapshots, errors, prompts and timer constants stable.
  Do not introduce new pricing, real-money mode, extra model requests or persistence.
- Run focused tests after each slice, mocked two-client flows for checkpoint
  evidence, real-local database checks for purchase changes, then the full
  Python/React gate and production build once at the end. Review Standards and
  Spec separately before final handoff. Commit selected architecture work locally;
  do not push or deploy.

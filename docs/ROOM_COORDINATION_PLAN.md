# Room coordination architecture plan

Started 2026-10-12 on `feature/question-first-room`.

Status: planning complete; consolidated scope confirmed by the user on
2026-10-12. Selected design: one command-oriented coordinator per room, focused
on coordination reliability and room lifecycle, delivered in four runnable local
checkpoints with the agreed verification checks. This is the confirmed planning
record, not an implementation specification or publication instruction.

Specification handoff completed on 2026-10-12:
[room-coordination specification](../.scratch/room-coordination/spec.md),
published to the local Markdown tracker with `Status: ready-for-agent`.
That specification is the implementation handoff; this document retains the
confirmed discovery and design context. Ticket breakdown and implementation
remain subsequent steps.

## Purpose

Concentrate the knowledge needed to coordinate a defense run asynchronously.
The room transport should not need to know how to order generation, validate
and publish a candidate, fence stale results, schedule timers, and coordinate
first-question charging. Build around the existing `TimedTurn` and
`PreparedProgression` modules rather than repeating their extractions.

Use [CONTEXT.md](../CONTEXT.md) for Room, Defense run, Defense turn, Chosen
defender, Clarification, Answer probe, Grounded citation and Research coverage.
No new domain meaning is proposed.

## Evidence and current ownership

- `backend/game_server.py` owns Room/Player, recipient-specific snapshots,
  broadcast ordering, HTTP/WebSocket adapters, authentication checks, task
  scheduling, asynchronous AI work, run charging and retention/absence handling.
- `_generate_question` already prepares a detached candidate and checks the
  generation ID before committing. The pending recovery fix adds one bounded
  automatic retry after a resolved turn and retains the accepted answer.
- `_interpret_pending`, `_prepare_research_plan` and `_generate_coaching` each
  coordinate their own state/version checks, publication and next work.
- AI work has four version checks: question generation, submission interpretation,
  paper mapping and coaching. Their current tasks are scheduled without a retained
  per-room task group; the clock task is retained and explicitly cancelled.
  Cancelling an asynchronous await does not stop provider work already executing
  in `asyncio.to_thread`. Result fencing must survive any task-management change.
- Publication uses a broadcast lock and then the room lock, builds
  recipient-specific snapshots, and performs bounded socket writes after
  releasing the room lock. Reclamation takes registry lock then room lock.
  A refactor must preserve ordering and avoid introducing reverse lock acquisition.
- `TimedTurn` owns synchronous deadlines, voting and submission rules.
  `PreparedProgression` owns detached generation preparation and validation;
  multiplayer and Streamlit share it.
- The HTTP/WebSocket tests are existing external test surfaces. Some focused
  tests patch generator, broadcaster and scheduling functions on game_server;
  migrating those tests requires deliberate module ownership, not a blanket
  patch-path rename.

Static inspection establishes the ownership map; it does not verify a new
implementation. Earlier recovery verification remains separate: 456 Python
tests with providers mocked, 261 React tests and a production build.

## Design tree

1. Behavior preservation → whether new behavior belongs in this checkpoint.
2. Coordination scope → what the new module owns and what adapters retain.
3. Local checkpoint approach → migration sequence and review gates.
4. After 1–3: compare module interfaces, settle lock/task/commit ownership and
   compatibility with current callers.
5. Verification and review → agree regression evidence and final shared scope.

The interview reached shared understanding with final Q7 confirmation. The next
handoff is an implementation specification based on this plan; implementation,
commits, push and deployment remain separate requested steps.

## Round 1 — confirmed 2026-10-12

- Q1: user chose **Include behavior improvements**, narrowed to coordination
  reliability in round 2; this does not authorize arbitrary changes to dialogue,
  layout, timing or financial rules.
- Q2: user confirmed **Focused room coordination**: asynchronous ordering,
  cancellation and validated publication. Authentication, payment transactions,
  AI prompts, document extraction and socket delivery retain their existing
  implementations.
- Q3: user confirmed **Local checkpoints first**: each keeps the app runnable;
  complete review precedes any separately requested push or deployment.

## Round 2 — confirmed 2026-10-12

- Q4: user confirmed **Coordination reliability**:
  including duplicate-work prevention, obsolete-work suppression and retained
  answers with clear recovery. Current layout, dialogue, timer lengths and prices
  stay. Existing protections must remain; newly claimed defects require regression
  evidence rather than an assumption that current code fails.
- Q5: user confirmed **Include room lifecycle**: restart, ending, closure and
  expiry, retaining global service lease, independent payment
  recovery and database transaction implementations.
- Q6: user confirmed **Use these checks**: full offline suites/build, mocked two-client
  code and twelve-question research runs, deadlines/reconnect/retry,
  duplicate/stale-result and charge/return checks, plus responsive smoke checks.
  Live AI, hosted providers and installed-device evidence remain separate.

The existing retry/cancellation/citation/charge guarantees remain mandatory;
new reliability changes require regression evidence. This does not add blanket
automatic retries, new prices or new AI calls.

## Interface comparison — selected design

Three independent, read-only designs were compared using depth, locality, caller
ordering knowledge, real adapter seams and migration cost.

| Design | Interface and leverage | Tradeoff |
| --- | --- | --- |
| A: command-oriented coordinator | One coordinator per room accepts a closed set of typed commands; callers do not publish or schedule work afterward. | Command handling needs private organization so it does not recreate the mixed ownership of game_server.py. |
| B: work/result/effect executor | Dispatch produces explicit internal work and ordered effects; completion returns through the same seam. | More internal types and a second decision/execution model; risk of a generic workflow engine for a single app. |
| C: named workflow methods | Explicit start, submit, retry, prepare, vote, presence, end and close methods match transport workflows. | A wider interface of roughly thirteen methods; internal scheduling must remain hidden to avoid a shallow facade. |

Selected: design A, using immutable captured work internally where it
helps stale-result safety. No actor broker, general effect engine, plugin handler
registry or extra deployment is needed. This concentrates task and transition
knowledge in one module while retaining the existing in-process policy modules.

### Agreed external seam

Detailed interface decisions are recorded in the linked specification;
the agreed shape is:

```python
await coordinator.execute(command, verified_actor)
snapshot = await coordinator.view(recipient)
await coordinator.shutdown()
```

- User commands map explicitly from the existing wire actions. Internal deadline,
  presence and maintenance commands cannot be manufactured by browser messages.
- A verified actor comes from server-owned token/account validation for that
  invocation. It is never accepted from payload account IDs or host flags.
- The coordinator still checks room ownership, selected-defender permissions,
  phase and operation preconditions. Auth/session/origin/CSRF and transport limits
  keep their existing implementations.
- Command acceptance is not AI completion. Safe command errors retain the
  existing message/reason protocol; asynchronous failures become existing
  recovery state. Shared results/snapshots exclude account and payment details.
- The coordinator sequences publication and next work. Callers do not mutate
  revisions, select operation IDs or manually schedule AI/timers afterward.
- Existing snapshot construction and bounded socket delivery are retained. The
  view method must not leak private pending text, votes or account state across
  recipients.

### Agreed implementation ownership

Use `backend/rooms/` for the room model and coordination implementation, with
few private helpers as required by actual workflows. Keep
`backend/game_server.py` as the existing FastAPI entry and composition site;
it retains uploads, middleware, HTTP/WebSocket parsing and integration with
unchanged auth/payment routers. This checkpoint does not make the whole backend
adopt the survey's future folder map.

- The coordinator owns admission and tracking of question, interpretation, map,
  coaching and clock work. Duplicate scheduling for the same operation identity
  creates no second task and consumes no second AI admission.
- Preserve existing operation counters initially. Capture room identity, run and
  relevant version/pending submission in each work item. Explicit legitimate
  retries create fresh work; do not coalesce separate runs or distinct turns.
- Capture stable inputs under the room lock, execute providers outside it,
  validate detached candidates and check identity/version/phase/closed state
  before applying either success or failure. Stale errors cannot overwrite a
  newer run or revive a closed room.
- Restart, ending, abandonment and closure invalidate appropriate work before
  cancelling its await. Ending can create fresh coaching; do not cancel that
  new work indiscriminately. A provider thread may still finish, so task
  cancellation never replaces result fencing or promises provider-cost recovery.
- Pending automatic next-question recovery remains bounded to its existing
  scope and limits. Opening, interpretation, mapping and coaching do not gain
  new automatic retry policies.
- Run charging and durable state calls remain explicit ordered operations using
  the existing transaction implementations. Do not defer a required opening
  charge until after committing/publishing the question.
- Keep registry-then-room reclamation and broadcast-then-room publication lock
  ordering. Never acquire registry or broadcast locks while holding the room
  lock. Preserve close/expiry eligibility and retention rules.
- Socket delivery reports failure through a presence path; chosen-defender
  reassignment and absence accounting retain their current meaning. Avoid
  recursive publication/presence callbacks while holding the delivery lock.
- Service shutdown invalidates owned room work and cleans up retained awaits
  without waiting indefinitely on provider threads. Existing global lease,
  heartbeat and payment-recovery ownership stays outside; shutdown ordering
  must not let obsolete work charge/publish after ownership is relinquished.
- Inject actual variation: existing AI functions versus controlled test
  completions, real time versus fake time, and socket delivery versus captured
  publications. Reuse real SQLite/PostgreSQL stores for transactional evidence;
  do not create an interface for every helper or change their financial policy.

The implementation must capture AI inputs under the room lock, run provider work
outside it, validate detached results, and fence stale work before changing state
or charging. Opening charge precedes state publication. Deadline expiration is
checked before accepting actions/results; revisions and snapshots preserve
publication order and recipient privacy. Cancellation cannot substitute for
checking operation identity and current state.

## Invariants already in force

- Frozen main and the deployed releases remain unchanged during planning.
- Preserve pending question-recovery changes and unrelated footprint research.
- Keep package-qualified imports, repository-root paths, existing launch
  commands and the Streamlit fallback.
- Keep accepted answers, exact citations, role/language behavior, private chat,
  research budgets, votes and server-owned deadlines.
- Existing payment ADRs constrain charges, returns, ledger separation and
  settlement; no financial-policy change is part of candidate selection.
- Rooms remain in memory with one worker and one instance.

## Agreed runnable checkpoints

1. Establish room model/coordination ownership and real dependency wiring under
   `backend/rooms/`. Preserve the existing entry points, snapshot shape and
   working recovery baseline. Keep transitional delegation short-lived.
2. Migrate deadline and all four AI workflows, with retained task tracking,
   duplicate-work prevention, safe detached commits and stale-result guards.
   Keep charging and publication order covered during the migration.
3. Route actions, restart/end/presence/close/expiry and shutdown through the
   coordinator; retain existing transport delivery and global lease/recovery.
   Remove alternate task scheduling and direct mutation paths.
4. Remove obsolete delegation and patch-forwarding helpers, update navigation
   docs and complete integration/responsive verification and two-axis review.

Each checkpoint leaves the app runnable and includes focused regression checks.
The final gate includes the agreed full suites/build. Focused tests should cross
the coordinator's real seam; do not preserve old test patch paths with permanent
forwarding modules. Keep HTTP/WebSocket tests as external contract evidence.

## Verification scenarios

- The same operation is scheduled twice while its provider is blocked: one task,
  one admission, one eventual commit. Distinct explicit retries remain allowed
  within current limits.
- Restart/end/close/expiry/abandonment occurs during blocked work or recovery
  backoff: old successes and errors cannot publish, charge or mutate the new room
  state. A new intended coaching task is not mistaken for stale work.
- Opening charge fails: publish no opening question; keep the existing release
  and retry rules. Valid opening/reconnect/retry never produces a second charge.
- Answer/reply/interpretation and deadline race: server deadline wins according
  to the existing rules, accepted turns stay unique, and next work starts once.
- Two clients and reconnect observe matching validated state, exact citations,
  retry status, transcript and coaching; recipient-private fields remain private.
- Slow/failed socket delivery retains bounded writes, reassignment and observed
  absence behavior without introducing deadlocks or unordered snapshots.
- Research mapping and twelve-question progression retain approval, coverage,
  timeout, clarification, budgets and coaching semantics.
- Service handoff and shutdown retain lease/charge/return guarantees; transaction
  implementation is unchanged. Use existing real-local database checks when
  testing this integration, with external providers mocked.
- Full Python/React suites and production build; desktop/portrait/landscape
  smoke checks. Live AI, hosted providers and installed devices remain distinct
  checks, not inferred from mocked or local evidence.

## Final confirmation — complete 2026-10-12

The user answered Q7 **Matches—finish planning**. The command-oriented design,
ownership, reliability-only improvements, four runnable checkpoints and
verification above form the confirmed scope. No planning decisions remain open.
This confirmation does not start implementation or authorize a commit, push or
deployment. Preserve the working recovery changes and frozen main throughout
subsequent ticketing and implementation work.

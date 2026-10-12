# Room-coordination ticket breakdown

Status: approved by the user on 2026-10-12; seven separate local tickets published.

Created: 2026-10-12. Based on the confirmed [specification](spec.md).

Four runnable checkpoints are divided into seven tickets, each sized for one
fresh implementation context. First expand ownership beside the existing
implementation, then migrate complete flows, then remove obsolete paths.
Every ticket must leave the app runnable; no ticket relies on a later integration
step to restore a broken build. The final ticket provides broader verification,
not permission to defer earlier correctness.

The runtime baseline includes the uncommitted next-question recovery fix.
Preserve it and the existing wire protocol, prompts, layout, prices, deadlines,
authentication and financial transactions throughout. No database or UI feature
is required by these slices. Existing transport reaches the new module through
each migrated flow, so a completed ticket is observable and verifiable.

## Approved tickets

### 01 — Establish room ownership through create, join and views

**Blocked by:** None — can start immediately.

**What it delivers:** Hosts create a room and defenders join/reconnect with the
same views and permissions while the room model and one coordinator instance
have an explicit owner. Existing vote and chat commands provide the first
complete command path through transport, validation, mutation and publication.

**Acceptance outline:**

- Establish the agreed command/view/shutdown seam and server-verified actor
  wiring without inventing a general command registry or new browser fields.
- Create/join/reconnect preserve seats, tokens, account checks, recipient privacy,
  bounded chat and snapshot shape; voting/chat use the new command seam.
- Preserve existing launch, fallback and root-relative assets/data paths.
- Unmigrated workflows retain their existing implementation through explicit,
  temporary delegation, with no duplicated policy implementation.
- Verify authenticated create/join/reconnect and vote/chat publication through
  existing HTTP/WebSocket tests and focused command/view behavior.

**Checkpoint:** 1 — ownership and wiring.

### 02 — Coordinate questions, retries and authoritative deadlines

**Blocked by:** 01 — Establish room ownership through create, join and views.

**What it delivers:** Starting a code or prepared research defense produces one
validated question and the existing reaction/vote/answer timeline. Question
retry and timeout progression share one tracked task owner, retaining accepted
answers and the pending bounded automatic recovery.

**Acceptance outline:**

- Migrate first/next/code/research question work and shared clock scheduling;
  duplicate scheduling of the same work launches one task and admits it once.
- Preserve detached validation, operation versions, exact citations, research
  coverage and charge-before-publication; failed charge publishes no question.
- Retain one automatic next-question recovery, error classification, attempt
  limits and synchronized retry snapshots; legitimate manual retries still work.
- Preserve reaction dwell, full vote duration, answer/reply clocks and pause
  expiry for both migrated and temporarily delegated flows.
- Deadline callbacks and deadline-sensitive input invoke one authoritative
  catch-up path; obsolete work and clock callbacks cannot advance new state.
- Verify start/retry, blocked duplicate work, retained answer, invalid candidate,
  timeout race, stale opening and ledger effects through the new seam and room
  contract. Retain current end/restart invalidation during this migration.

**Checkpoint:** 2 — asynchronous workflows.

### 03 — Coordinate answers, clarifications and panelist probes

**Blocked by:** 02 — Coordinate questions, retries and authoritative deadlines.

**What it delivers:** The chosen defender submits through one coordinated path;
interpretation, same-question clarification, probes and direct-answer recovery
retain their current timers and attribution, then advance the defense once.

**Acceptance outline:**

- Capture stable pending input/history and track interpretation work; validate
  its identity, phase and deadline before applying success or failure.
- Preserve selected-defender checks, accepted names, bounded pause/admission,
  clarification/probe limits and existing direct/pending-answer recovery actions.
- Keep the original answer, question number and citation during same-question
  replies; rejected or obsolete results do not lose accepted turns.
- Use shared deadline and progression ownership rather than arranging timers or
  new generation from transport handlers.
- Verify duplicate submission/interpretation, late result, timeout race, probe
  reply, recovery and two-client/reconnect transcript behavior.

**Checkpoint:** 2 — asynchronous workflows.

### 04 — Coordinate research preparation and final coaching

**Blocked by:** 02 — Coordinate questions, retries and authoritative deadlines.

**What it delivers:** Hosts prepare/retry/approve research maps and defenders
receive shared coaching through tracked room work. Stale planning/coaching
successes and errors cannot overwrite current state, while current retries
retain uploads and transcript.

**Acceptance outline:**

- Migrate map and coaching task ownership, admission, version/phase checks and
  publication without changing prompts, report validation or request count.
- Preserve host-only preparation/approval, current plan/budget matching,
  research scope, citation validation and no-question-on-planning-failure behavior.
- Preserve coaching settlement/recovery semantics and the factual empty-session
  summary without an AI request.
- Deduplicate identical map/coaching work and suppress obsolete success/failure;
  distinguish legitimate fresh retries and intended new closing coaching.
- Verify prepared research start, map retry, transcript/coverage retention,
  coaching retry, privacy and durable settlement using existing contract tests.

**Checkpoint:** 2 — asynchronous workflows.

### 05 — Coordinate ordered publication and defender presence

**Blocked by:** 02 — Coordinate questions, retries and authoritative deadlines.

**What it delivers:** Both clients see ordered recipient-private state, and
connect/disconnect or failed delivery updates the chosen defender consistently
without resetting the answer clock or blocking the room.

**Acceptance outline:**

- Move publication sequencing and presence transitions behind the coordinator;
  retain existing bounded socket delivery and message/connection limits.
- Preserve ordered/coalesced revisions, recipient-specific pending/vote fields,
  private account exclusion and guest/host reconnect rules.
- Failed delivery feeds presence/reassignment/observed-absence handling without
  recursive publication under its lock or reversed lock acquisition.
- Preserve partial disconnects across multiple tabs and the running deadline
  when the chosen defender changes.
- Verify slow/failing recipients, concurrent revision delivery, private views,
  reconnect and reassignment through captured delivery and real mocked sockets.

**Checkpoint:** 3 — action and lifecycle routing.

### 06 — Coordinate restart, ending, reclamation and shutdown

**Blocked by:**

- 03 — Coordinate answers, clarifications and panelist probes.
- 04 — Coordinate research preparation and final coaching.
- 05 — Coordinate ordered publication and defender presence.

**What it delivers:** Restart, permitted ending, unavailable-run ending, closure,
expiry, observed abandonment and shutdown consistently retire old room work.
Late success or failure cannot publish or charge; intended new runs/coaching
remain valid and existing financial outcomes stay unchanged.

**Acceptance outline:**

- Centralize applicable work invalidation before cancellation/replacement and
  retain closure, retention, settlement and abandonment eligibility.
- Preserve confirmed restart/new run charging and allowed ending/recovery modes;
  keep new closing coaching independent of retired work.
- Retain registry-then-room reclamation, current socket closure behavior and
  bounded cleanup without claiming cancellation terminates provider threads.
- Shut down room work before relinquishing ownership; keep global lease,
  heartbeat, independent payment recovery and database transactions unchanged.
- Verify every retired AI lane for both late success and late error, including
  blocked provider/backoff work, late interpretation and failed delivery.
- Verify charge/return and service-handoff outcomes with actual local stores and
  disposable PostgreSQL where integration changes, external providers mocked.

**Checkpoint:** 3 — action and lifecycle routing.

### 07 — Remove obsolete paths and verify complete defenses

**Blocked by:** 06 — Coordinate restart, ending, reclamation and shutdown.

**What it delivers:** The complete multiplayer defense runs through the agreed
coordinator, with no alternate scheduling/mutation paths. Maintainers receive
updated navigation and reviewed integration evidence without changing the UI
or deploying the release.

**Acceptance outline:**

- Remove temporary delegation and obsolete mutation/scheduling helpers; do not
  retain forwarding symbols solely to preserve old test patch paths.
- Keep meaningful domain tests; focused tests cross the coordinator seam and
  external HTTP/WebSocket tests remain authoritative.
- Complete mocked two-client code four/eight-turn and research twelve-question
  defenses covering votes, timeout, clarification/probe, retry, reconnect,
  transcript, exact citations and coaching.
- Run the full Python/React suites and production build, required real-local
  accounting/handoff checks and desktop/portrait/landscape keyboard smoke checks.
- Complete Standards/Spec review; update README, agent navigation as needed and
  the shared log with honest mocked/local/live evidence distinctions.
- Preserve pending recovery and unrelated work, frozen main and current live
  services. No push, deployment or live provider transaction in this ticket set.

**Checkpoint:** 4 — cleanup, integration and review.

## Dependency rationale and review

01 → 02 → {03, 04, 05} → 06 → 07.

Question/deadline ownership gates the dependent workflows. Submissions,
mapping/coaching and publication/presence do not semantically depend on one
another; all must be ready before lifecycle invalidation can be verified across
every lane. The final cleanup therefore waits for lifecycle integration.
The three middle tickets may still touch shared coordination code: their graph
does not authorize concurrent edits without coordination.

The user approved this size and graph on 2026-10-12. Seven separate local issue
files are published with ready-for-agent status. Ticket 01 is the only initially
unblocked task. The parent specification is unchanged. Approval did not start
implementation or authorize a commit, push or deployment.

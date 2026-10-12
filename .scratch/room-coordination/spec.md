# Room coordination and lifecycle reliability

Status: ready-for-human

Created: 2026-10-12. Work branch: feature/question-first-room.

The user confirmed the planning scope and test expectations. All seven local
implementation tickets are complete and code-reviewed; evidence and remaining
human/live review boundaries are in
[the local review](../../docs/ROOM_COORDINATION_REVIEW.md). Remote publication
and deployment remain separate steps. The problem statement below describes
the original migration trigger; requirements remain the agreed contract.

## Problem Statement

Room coordination is concentrated in the web server: transport handlers must
understand task scheduling, deadlines, operation versions, AI admission,
candidate validation, charging, state mutation and publication ordering.
Changing one defense workflow therefore requires understanding several related
paths, making future maintenance and reliable recovery harder.

The existing synchronous timed-turn and detached-progression modules already
encapsulate useful rules. The remaining problem is ownership of the asynchronous
sequences around them, including restart, ending, closure, expiry and shutdown.
AI awaits are not consistently tracked as room-owned work. Cancellation alone
cannot stop a provider request already running in a thread, so safe result
acceptance remains essential.

Hosts and defenders need dependable progress without duplicate work, lost
answers, stale room updates or duplicate charges. Maintainers need a module
whose interface hides this coordination knowledge, with observable tests that
survive internal refactoring.

## Solution

Introduce one command-oriented room coordinator per in-memory room. It owns
asynchronous task ordering, deadline catch-up, operation deduplication,
validated commits, publication sequencing and room lifecycle coordination.
Transport callers provide typed commands and server-verified actors; they no
longer mutate room revisions or manually arrange generation, publication and
timers afterward.

Retain the existing timed-turn and progression implementation, exact wire
messages and recipient-specific snapshots. Authentication, database
transactions, prompts, document extraction, bounded socket delivery, global
service leasing and independent payment recovery retain their current
implementations. Preserve the pending bounded next-question recovery fix.

Deliver four runnable local checkpoints: establish ownership and wiring;
centralize timers and AI work; migrate actions and lifecycle paths; then remove
obsolete paths, verify integration and review the final change. The intentional
behavior improvements are coordination reliability only. Layout, dialogue,
timer lengths, prices and defense policies remain unchanged.

## User Stories

1. As a maintainer, I want one owner for room coordination, so that a workflow change does not require reconstructing ordering across transport handlers.
2. As a maintainer, I want the coordinator to reuse timed-turn rules, so that voting and deadlines retain their existing behavior.
3. As a maintainer, I want detached progression reused, so that invalid AI moves cannot partially update the live defense.
4. As a maintainer, I want each migration checkpoint to leave the app runnable, so that regressions can be isolated before further work.
5. As a maintainer, I want existing entry points and repository-root paths preserved, so that local launch and deployment configuration remain compatible.
6. As a host, I want my account checked for every host action, so that room ownership remains enforced after sign-out or session expiry.
7. As a guest defender, I want to join using the existing room code and token flow, so that this refactor does not require a host account for participation.
8. As a host, I want unauthorized actions rejected before mutation or paid work, so that rejected requests cannot reset the room or spend credits.
9. As a defender, I want only permitted room commands accepted from browser messages, so that internal timer and maintenance operations cannot be forged.
10. As a host, I want duplicate starts to retain the existing safe response, so that repeated clicks do not begin another run.
11. As a defender, I want duplicate scheduling of one operation to launch only one task, so that room progress and AI admission are not duplicated.
12. As a host, I want an explicit valid retry to remain a distinct operation, so that deduplication does not prevent legitimate recovery.
13. As a defender, I want accepted answers retained during question generation, so that a temporary provider failure does not require answering again.
14. As a host, I want the existing one automatic next-question retry retained, so that recoverable failures can resume without opening Controls.
15. As a host, I want configuration, quota and exhausted-attempt failures to retain manual recovery, so that the app does not repeatedly request unavailable AI work.
16. As a defender, I want retry status restored on reconnect, so that I know the team is still preparing the next question.
17. As a host, I want obsolete question results ignored after restart, so that an earlier run cannot replace the new run's question.
18. As a host, I want obsolete errors ignored after restart, so that an earlier failure cannot put a healthy new run into recovery.
19. As a host, I want ending an eligible defense to invalidate its pending question work, so that no extra question appears afterward.
20. As a host, I want intended closing coaching to remain active after ending, so that cleanup does not cancel the report just requested.
21. As a host, I want room closure and expiry to invalidate old work, so that removed rooms cannot be revived by late provider responses.
22. As a maintainer, I want shutdown to invalidate room-owned work before releasing ownership, so that stopped instances cannot commit or charge late results.
23. As a maintainer, I want cancellation cleanup to remain bounded, so that shutdown does not wait indefinitely for an executing provider thread.
24. As a defender, I want validated dialogue and citations published together, so that I never see an unvalidated question or invented excerpt.
25. As a host, I want the opening charge finalized before the first question appears, so that the room never publishes an uncharged paid opening.
26. As a host, I want an opening charge failure to retain its existing release and retry behavior, so that failed storage operations cannot silently consume access or publish a question.
27. As a host, I want reconnect and retries not to charge again for an authorized run, so that recovery remains included.
28. As a host, I want confirmed restart costs and new run identifiers preserved, so that starting another paid defense retains its existing accounting.
29. As a host, I want voucher and sandbox/live access paths preserved, so that coordination changes do not change eligibility or balances.
30. As a defender, I want a complete fifteen-second vote after each question is presented, so that task migration does not shorten speaker selection.
31. As a chosen defender, I want the existing answer and reply deadlines enforced on the server, so that delayed browser countdowns cannot authorize late submissions.
32. As a defender, I want deadline races resolved once, so that one turn cannot be both newly answered and independently advanced by duplicate work.
33. As a defender, I want clarification to remain on the same turn, so that asking for an explanation does not consume another question.
34. As a chosen defender, I want answer probes and direct-answer recovery retained, so that same-question replies and fallback controls still work.
35. As a defender, I want selected-defender and accepted-speaker attribution preserved, so that the vote and transcript name the correct person.
36. As a defender, I want reassignment after a disconnect to retain the running clock, so that presence changes do not reset answer time.
37. As a defender, I want slow or failed socket delivery bounded, so that another client's connection cannot block the room indefinitely.
38. As a defender, I want delivery failure to update presence safely, so that voting, reassignment and absence accounting use actual connected defenders.
39. As a defender, I want ordered revision snapshots, so that reconnect and concurrent events cannot display older state after newer state.
40. As a defender, I want only my own pending submission and vote exposed privately, so that another recipient cannot see my private state.
41. As a host, I want account IDs, balances and voucher details excluded from shared snapshots, so that teammates do not receive private account information.
42. As a defender, I want team chat to retain its existing privacy and bounds, so that it stays outside AI context and the defense transcript.
43. As a research host, I want preparation and retries to retain uploads and map validation, so that a planning failure does not lose the accepted documents.
44. As a research host, I want map approval and budget matching enforced, so that starting uses the confirmed research scope.
45. As a research defender, I want stale map results ignored after the room moves on, so that an old plan cannot replace the current defense.
46. As a research defender, I want exact coverage and question-budget behavior retained, so that longer defenses and timeout outcomes remain consistent.
47. As a defender, I want coaching failures to retain their retry and recovery behavior, so that final-report generation does not lose the transcript.
48. As a host, I want an empty eligible ending to retain a factual summary without AI, so that the app does not invent discussion that never happened.
49. As a host, I want existing credit-return and service-handoff guarantees retained, so that lifecycle migration cannot change financial outcomes.
50. As a host, I want existing idle, settlement and abandonment conditions preserved, so that an active or unsettled room is not reclaimed prematurely.
51. As a phone user, I want portrait and landscape controls to remain readable, so that internal refactoring does not change room usability.
52. As a keyboard user, I want focus, drawers and recovery actions preserved, so that the room stays usable without a pointer.
53. As a Streamlit user, I want the existing single-browser progression unchanged, so that the fallback does not depend on multiplayer coordination.
54. As a maintainer, I want tests at the HTTP/WebSocket and coordinator seams, so that observable behavior stays stable when private helpers move.
55. As a maintainer, I want controlled AI completions and fake time in offline tests, so that concurrency and deadline failures are deterministic.
56. As a maintainer, I want real local transaction checks distinguished from mocked providers, so that financial evidence does not rely on a fake ledger.
57. As a maintainer, I want live AI, hosted and installed-device evidence recorded separately, so that offline success is not presented as a live-quality claim.
58. As a project owner, I want the frozen main branch and live services unchanged during this checkpoint, so that local architecture work cannot disrupt the current release.

## Implementation Decisions

- **Module shape:** one RoomCoordinator per room with a small interface: execute
  a typed command with a VerifiedActor, read a recipient-specific view, and shut
  down owned work. It is an in-process module, not an actor broker or workflow
  engine. Private organization may follow the actual workflows without making
  every helper a new external interface.
- **Ownership:** group the room model and coordination implementation together.
  The current FastAPI launch entry remains the composition and transport entry.
  This checkpoint does not reorganize the entire backend or frontend.
- **Commands:** use a closed typed set covering current user operations and
  trusted internal deadline, presence and lifecycle events. Explicit decoding
  maps only existing browser actions and payload fields. Do not add wire-level
  operation identifiers or a configurable handler registry.
- **Identity and permissions:** VerifiedActor is produced by server-owned
  authentication for the invocation. Preserve owner-session/origin/CSRF and
  player-token checks. The coordinator validates ownership, defender selection,
  phase and operation preconditions; browser IDs, names or host flags never
  establish authority. Preserve existing availability of each control by mode
  and phase, including ending and recovery.
- **Results:** CommandResult reports command acceptance or a safe existing
  rejection message/reason; it does not promise AI completion. Asynchronous
  failures update existing recovery state. Account and payment details do not
  enter shared results or snapshots.
- **Reuse:** keep TimedTurn responsible for synchronous rules and
  PreparedProgression responsible for detached preparation and validation.
  Retain session identity on committed progression and preserve code/research
  policies, citations, roles, language and coverage.
- **Task ownership:** retain and clean up question, interpretation, mapping,
  coaching and clock tasks under the coordinator. Claim each work identity
  before scheduling. Repeated scheduling of that identity creates no second
  task, AI admission or commit. Explicit permitted retries use fresh work.
- **Fencing:** initially preserve the existing separate operation counters.
  Capture room identity, run identity, operation kind/version and relevant
  pending submission in stable work context. Check closure, identity, phase,
  version and applicable pending submission before both successful and failed
  completion can affect the room. Do not coalesce distinct turns or runs.
- **Provider execution:** capture stable inputs under the room lock, run provider
  work outside it and validate detached results before committing. Cancellation
  of an await cannot terminate an executing provider thread; obsolete success
  and failure must remain harmless through result fencing.
- **Recovery baseline:** carry forward the pending bounded automatic retry after
  a resolved answer or timeout, including synchronized retry state and the inline
  host fallback. Retain its existing per-turn/account admission, error
  classifications and limits. No new automatic retries for opening,
  interpretation, mapping or coaching are introduced.
- **Deadline ordering:** catch up authoritative deadlines before accepting
  deadline-sensitive actions and interpretation results. Preserve reaction,
  voting, answer, reply and bounded-pause behavior. A stale clock callback does
  not change current state or schedule duplicate progression.
- **Commit ordering:** under the room lock, revalidate work, perform required
  opening charge through the existing transactional implementation, commit
  validated progression, establish current presentation/deadline state and
  increment revision. Publish validated state before arranging subsequent work.
  Storage failure publishes no uncharged opening and retains existing safe
  reservation/recovery semantics.
- **Lifecycle invalidation:** restart, ending, abandonment, closure and expiry
  invalidate the appropriate work before cancellation or replacement. Ending
  can deliberately start new coaching; invalidation must not cancel it.
  Existing retention, settlement eligibility, restart confirmation and durable
  run outcomes are unchanged.
- **Publication and locks:** retain registry-then-room reclamation and
  broadcast-then-room publication ordering. Never acquire registry or broadcast
  locks while holding the room lock. Build recipient-specific deliveries from
  validated state and preserve revision ordering, coalescing and current wire
  fields. Provider waits and socket sends remain outside the room lock.
- **Presence feedback:** retain bounded socket delivery and feed failed delivery
  through coordinated presence handling. Reassignment and observed absence
  retain their existing meaning. Do not recursively enter publication while
  holding its delivery lock. Preserve connection/message limits and guest/host
  reconnect rules.
- **Service integration:** global lease acquisition, heartbeat and independent
  payment recovery retain their implementations. Before ownership is
  relinquished, shut down room coordination so old work cannot charge or
  publish. Cleanup is bounded and does not claim to stop provider threads,
  recover their cost or make rooms durable.
- **Adapters:** inject actual variation: existing AI functions versus controlled
  test completions, real versus fake time, and socket delivery versus captured
  publications. Keep financial transactions in existing SQLite/PostgreSQL
  implementations; avoid interfaces for every imported helper.
- **Protocol and storage:** no HTTP/WebSocket schema, database migration,
  credentials, payment policy, room persistence or pricing change is required.
  Preserve one worker and one instance, launch entry points, package-qualified
  imports and repository-root data/asset locations.
- **Migration:** checkpoint one establishes model/coordination ownership and
  wiring; two migrates clocks and all AI workflows; three migrates actions and
  lifecycle paths; four removes obsolete paths and completes verification and
  review. Each remains runnable. Temporary delegation must end; do not retain
  alternate scheduling paths or forwarding symbols solely for old test patches.

## Testing Decisions

- **Confirmed seams:** the user approved the offline/mocked verification scope
  and then confirmed the consolidated coordinator design. No additional seam
  interview is needed. Authenticated HTTP/WebSocket flows remain the primary
  contract; focused tests cross the coordinator's execute/view/shutdown seam
  when task races require controlled completion and fake time.
- **Good tests:** assert observable outcomes, publications, accepted transcript,
  citations, admission counts and actual ledger effects. Avoid assertions about
  private helper names, task-map layout, file moves or internal effect records.
  Replace scheduler-patching coverage only when equivalent or stronger
  behavioral evidence exists; retain distinct domain regressions.
- **Prior art:** existing room tests cover two-client four/eight-turn code flows,
  reconnect, clarification, question retry and coaching; research coverage tests
  cover twelve-question progression. Existing timed-turn and submission tests
  exercise deadlines and probes. Room-access tests cover stale opening results,
  failed charging and confirmed restart. Service-handoff tests cover lease
  overlap and once-only returns. The pending recovery tests cover bounded
  automatic retry, stale backoff and unchanged research coverage.
- **Coordination races:** block a provider while scheduling identical work twice;
  require one provider request, one admission and one commit. Invalidate work
  with restart/end/closure/expiry/abandonment/shutdown; complete it successfully
  or fail it afterward and assert no stale charge, publication or mutation.
  Confirm legitimate retry and intended new coaching still proceed.
- **Deadlines and answers:** use fake time at deadline boundaries with submit,
  reply, direct-answer recovery and interpretation completion. Assert the
  existing authoritative outcome, unique accepted turns and one subsequent
  progression. Invalid candidates preserve answer, citation and coverage.
- **Private ordered delivery:** use captured publications and bounded slow/failing
  delivery to verify recipient privacy, revision order, selected-defender
  reassignment, absence handling and no deadlock. Exercise real mocked two-client
  WebSockets and reconnect as the higher seam.
- **Accounting integration:** preserve opening reserve/charge/release ordering,
  no charge on stale or invalid candidates, once-only charges/returns and existing
  service-handoff outcomes. Exercise existing real local SQLite and disposable
  PostgreSQL transaction checks for changed billing integration, with external
  providers mocked; do not replace those checks with an in-memory fake ledger.
- **End-to-end offline gate:** full Python and React suites and production build,
  plus mocked two-client code four/eight-turn and research twelve-question
  defenses covering voting, timeout, clarification/probe, retry, reconnect,
  transcript and coaching. Each migration slice also runs relevant focused
  regressions before the final gate.
- **Presentation smoke checks:** desktop, phone portrait and landscape checks for
  unchanged question/citation readability, status, drafts, keyboard drawers and
  recovery controls. These are synthetic fixtures, not proof of AI quality.
- **Evidence discipline:** distinguish static review, mocked providers, real local
  databases, synthetic browsers, live AI/provider checks, hosted behavior,
  installed devices and user visual review. Run a final Standards/Spec review of
  the selected implementation and identify the preserved baseline changes.

## Out of Scope

- Frontend redesign, new status wording, prompt/voice/language improvements,
  changed reactions, timer lengths or clarification intent.
- Changes to prices, credit returns, voucher policy, settlement verification,
  refund rules, invitations, Google authentication or financial schemas.
- Separate AI/model-record refactoring, citation ownership redesign, account
  storage untangling or project-wide folder migration from the architecture survey.
- New providers, automatic retry policies, additional substantive AI calls,
  retrieval optimization or changed code/research defense budgets.
- Actor brokers, message queues, event sourcing, generic workflow engines,
  microservices, multiple workers/instances or durable room/transcript storage.
- Rewriting the Streamlit fallback, mobile shells or existing socket delivery.
- Cleanup of unrelated local files, screenshots, footprint research or drafts.
- Implementation, commits, push, merge, Render deployment, live transactions or
  changes to frozen main as part of producing this specification.

## Further Notes

The confirmed [planning record](../../docs/ROOM_COORDINATION_PLAN.md) contains
the architecture comparison and concrete ownership context. This document is the
canonical local implementation specification for the selected scope; the shared
handoff log records session status and evidence separately.

The working tree includes a previously completed, uncommitted question-recovery
fix. Preserve it as the runtime baseline rather than reverting to the current
commit's older recovery behavior. Its earlier gate was 456 Python tests with
providers mocked, 261 React tests and a production build; producing this
specification does not rerun or extend that runtime evidence.

Existing payment ADR decisions constrain compensation, separate live/demo
balances and verified settlement. Some ADR status text still says implementation
pending despite later source and verification records; do not reinterpret that
as authorization to rewrite financial behavior. No new domain definition or
financial decision is introduced here.

Implementation handoff: all seven dependency-ordered local tickets are complete.
Review the local screen and evidence before a later requested publication or
deployment. Main and the live services remain unchanged during this local work.

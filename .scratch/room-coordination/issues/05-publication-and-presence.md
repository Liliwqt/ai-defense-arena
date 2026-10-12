# 05 — Coordinate ordered publication and defender presence

**What to build:** Both clients see ordered recipient-private state, and
connect/disconnect or failed delivery updates the chosen defender consistently
without resetting the answer clock or blocking the room.

**Blocked by:** 02 — Coordinate questions, retries and authoritative deadlines.

**Status:** ready-for-human

**Checkpoint:** 3 — action and lifecycle routing.

## Acceptance criteria

- [x] Move publication sequencing and presence transitions behind the coordinator;
  retain existing bounded socket delivery and message/connection limits.
- [x] Preserve ordered/coalesced revisions, recipient-specific pending/vote fields,
  private account exclusion and guest/host reconnect rules.
- [x] Failed delivery feeds presence/reassignment/observed-absence handling without
  recursive publication under its lock or reversed lock acquisition.
- [x] Preserve partial disconnects across multiple tabs and the running deadline
  when the chosen defender changes.
- [x] Verify slow/failing recipients, concurrent revision delivery, private views,
  reconnect and reassignment through captured delivery and real mocked sockets.

## Scope and execution constraints

- Follow the confirmed Room coordination and lifecycle reliability specification
  in this local feature tracker. Use one command-oriented coordinator per room,
  with execute/view/shutdown as the external seam and real dependency adapters.
- Work on feature/question-first-room. Keep main and current live services
  unchanged; this ticket authorizes no commit, push, deployment or provider payment.
- Preserve the working tree's uncommitted bounded next-question recovery fix as
  baseline, including retained answers, synchronized retry status, attempt limits
  and the existing inline host fallback. Earlier runtime evidence is separate
  from this ticket's required verification.
- Preserve current wire fields/errors, recipient privacy, account/CSRF/origin/token
  checks, UI, prompts, citations, language, voting/answer/reply/pause timing,
  research coverage/budgets, chat, financial policy and Streamlit behavior.
- Reuse TimedTurn and PreparedProgression. Keep charge-before-publication,
  stale-result checks even after cancellation, registry-then-room and
  broadcast-then-room lock order, bounded delivery and one worker/instance.
- Keep existing authentication, document extraction, financial transactions,
  global lease/heartbeat and independent payment-recovery implementations.
- Each slice remains runnable with focused mocked-provider regressions through
  observable command/view or HTTP/WebSocket behavior. Keep legitimate retries
  distinct; do not add blanket retries, extra substantive AI calls or new prices.
- Preserve unrelated files and edits. Coordinate shared module work even when
  dependencies allow more than one ticket to start. Temporary delegation is
  removed by the final cleanup ticket, not maintained as a permanent test facade.

## Comments

- 2026-10-12: User approved the seven-ticket size and blocking graph. Published
  to the local Markdown tracker; implementation has not started.

- 2026-10-12: Implemented locally. Publication and authenticated presence now
  use the coordinator command boundary, with ordered/coalesced private snapshots,
  bounded parallel delivery, corrected failed-socket presence, unchanged tab and
  message limits, and deadline-preserving reassignment/reconnect. Six captured
  transport tests cover concurrent updates, privacy, slow/failing delivery,
  multiple tabs, host identity and cancellation during initial send/failed close.
  Independent Standards and Spec rechecks report zero remaining findings after
  fixing the reproduced cancellation cleanup cases. User visual review is not
  claimed; no push/deployment. Lifecycle/service integration remains ticket 06.

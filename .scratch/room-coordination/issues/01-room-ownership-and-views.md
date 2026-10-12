# 01 — Establish room ownership through create, join and views

**What to build:** Hosts create a room and defenders join/reconnect with the
same views and permissions while the room model and one coordinator instance
have an explicit owner. Existing vote and chat commands provide the first
complete command path through transport, validation, mutation and publication.

**Blocked by:** None — can start immediately.

**Status:** ready-for-agent

**Checkpoint:** 1 — ownership and wiring.

## Acceptance criteria

- [ ] Establish the agreed command/view/shutdown seam and server-verified actor
  wiring without inventing a general command registry or new browser fields.
- [ ] Create/join/reconnect preserve seats, tokens, account checks, recipient privacy,
  bounded chat and snapshot shape; voting/chat use the new command seam.
- [ ] Preserve existing launch, fallback and root-relative assets/data paths.
- [ ] Unmigrated workflows retain their existing implementation through explicit,
  temporary delegation, with no duplicated policy implementation.
- [ ] Verify authenticated create/join/reconnect and vote/chat publication through
  existing HTTP/WebSocket tests and focused command/view behavior.

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

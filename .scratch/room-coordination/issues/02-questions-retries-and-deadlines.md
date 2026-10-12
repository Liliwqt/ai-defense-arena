# 02 — Coordinate questions, retries and authoritative deadlines

**What to build:** Starting a code or prepared research defense produces one
validated question and the existing reaction/vote/answer timeline. Question
retry and timeout progression share one tracked task owner, retaining accepted
answers and the pending bounded automatic recovery.

**Blocked by:** 01 — Establish room ownership through create, join and views.

**Status:** ready-for-agent

**Checkpoint:** 2 — asynchronous workflows.

## Acceptance criteria

- [ ] Migrate first/next/code/research question work and shared clock scheduling;
  duplicate scheduling of the same work launches one task and admits it once.
- [ ] Preserve detached validation, operation versions, exact citations, research
  coverage and charge-before-publication; failed charge publishes no question.
- [ ] Retain one automatic next-question recovery, error classification, attempt
  limits and synchronized retry snapshots; legitimate manual retries still work.
- [ ] Preserve reaction dwell, full vote duration, answer/reply clocks and pause
  expiry for both migrated and temporarily delegated flows.
- [ ] Deadline callbacks and deadline-sensitive input invoke one authoritative
  catch-up path; obsolete work and clock callbacks cannot advance new state.
- [ ] Verify start/retry, blocked duplicate work, retained answer, invalid candidate,
  timeout race, stale opening and ledger effects through the new seam and room
  contract. Retain current end/restart invalidation during this migration.

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

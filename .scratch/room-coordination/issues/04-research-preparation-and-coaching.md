# 04 — Coordinate research preparation and final coaching

**What to build:** Hosts prepare/retry/approve research maps and defenders
receive shared coaching through tracked room work. Stale planning/coaching
successes and errors cannot overwrite current state, while current retries
retain uploads and transcript.

**Blocked by:** 02 — Coordinate questions, retries and authoritative deadlines.

**Status:** ready-for-agent

**Checkpoint:** 2 — asynchronous workflows.

## Acceptance criteria

- [ ] Migrate map and coaching task ownership, admission, version/phase checks and
  publication without changing prompts, report validation or request count.
- [ ] Preserve host-only preparation/approval, current plan/budget matching,
  research scope, citation validation and no-question-on-planning-failure behavior.
- [ ] Preserve coaching settlement/recovery semantics and the factual empty-session
  summary without an AI request.
- [ ] Deduplicate identical map/coaching work and suppress obsolete success/failure;
  distinguish legitimate fresh retries and intended new closing coaching.
- [ ] Verify prepared research start, map retry, transcript/coverage retention,
  coaching retry, privacy and durable settlement using existing contract tests.

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

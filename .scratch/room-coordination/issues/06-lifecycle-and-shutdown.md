# 06 — Coordinate restart, ending, reclamation and shutdown

**What to build:** Restart, permitted ending, unavailable-run ending, closure,
expiry, observed abandonment and shutdown consistently retire old room work.
Late success or failure cannot publish or charge; intended new runs/coaching
remain valid and existing financial outcomes stay unchanged.

**Blocked by:**

- 03 — Coordinate answers, clarifications and panelist probes.
- 04 — Coordinate research preparation and final coaching.
- 05 — Coordinate ordered publication and defender presence.

**Status:** ready-for-agent

**Checkpoint:** 3 — action and lifecycle routing.

## Acceptance criteria

- [ ] Centralize applicable work invalidation before cancellation/replacement and
  retain closure, retention, settlement and abandonment eligibility.
- [ ] Preserve confirmed restart/new run charging and allowed ending/recovery modes;
  keep new closing coaching independent of retired work.
- [ ] Retain registry-then-room reclamation, current socket closure behavior and
  bounded cleanup without claiming cancellation terminates provider threads.
- [ ] Shut down room work before relinquishing ownership; keep global lease,
  heartbeat, independent payment recovery and database transactions unchanged.
- [ ] Verify every retired AI lane for both late success and late error, including
  blocked provider/backoff work, late interpretation and failed delivery.
- [ ] Verify charge/return and service-handoff outcomes with actual local stores and
  disposable PostgreSQL where integration changes, external providers mocked.

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

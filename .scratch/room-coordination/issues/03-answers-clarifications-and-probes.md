# 03 — Coordinate answers, clarifications and panelist probes

**What to build:** The chosen defender submits through one coordinated path;
interpretation, same-question clarification, probes and direct-answer recovery
retain their current timers and attribution, then advance the defense once.

**Blocked by:** 02 — Coordinate questions, retries and authoritative deadlines.

**Status:** ready-for-human

**Checkpoint:** 2 — asynchronous workflows.

## Acceptance criteria

- [x] Capture stable pending input/history and track interpretation work; validate
  its identity, phase and deadline before applying success or failure.
- [x] Preserve selected-defender checks, accepted names, bounded pause/admission,
  clarification/probe limits and existing direct/pending-answer recovery actions.
- [x] Keep the original answer, question number and citation during same-question
  replies; rejected or obsolete results do not lose accepted turns.
- [x] Use shared deadline and progression ownership rather than arranging timers or
  new generation from transport handlers.
- [x] Verify duplicate submission/interpretation, late result, timeout race, probe
  reply, recovery and two-client/reconnect transcript behavior.

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

- 2026-10-12: Implemented locally. Closed typed submission commands now execute
  through the coordinator. It captures pending input, source/question, probe,
  attribution and detached history before scheduling one interpretation task per
  run/version. Both success and failure recheck identity/phase/deadline. Existing
  clarification/probe/direct/saved-answer paths share authoritative timing and
  progression; no browser field, AI prompt, price or fallback changes.
- Verification: 470 Python tests pass (offline, AI/Google/PayMongo mocked), 261
  React tests pass and production build succeeds. Five new command/view tests
  cover duplicate work, same-question clarification, stale failures, timeout
  races, original-answer preservation and private saved-probe recovery. Existing
  two-client four/eight code and twelve-question research/mixed protocols pass.
- Review: zero remaining Standards and Spec findings. Fixed an inherited race
  where the deadline could pass between catch-up and saved-answer/retry handling;
  the regression failed for both actions before the fix and now passes. Shared
  task registration removes optional duplicated bookkeeping. No provider calls.
- Local human review and later workflow/lifecycle/cleanup tickets remain. No live
  AI/provider, PostgreSQL, hosted, new visual or installed-device check claimed.
  Explicit Implement authorizes a local commit; no push/deployment requested.

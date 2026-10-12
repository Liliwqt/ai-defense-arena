# 04 — Coordinate research preparation and final coaching

**What to build:** Hosts prepare/retry/approve research maps and defenders
receive shared coaching through tracked room work. Stale planning/coaching
successes and errors cannot overwrite current state, while current retries
retain uploads and transcript.

**Blocked by:** 02 — Coordinate questions, retries and authoritative deadlines.

**Status:** ready-for-human

**Checkpoint:** 2 — asynchronous workflows.

## Acceptance criteria

- [x] Migrate map and coaching task ownership, admission, version/phase checks and
  publication without changing prompts, report validation or request count.
- [x] Preserve host-only preparation/approval, current plan/budget matching,
  research scope, citation validation and no-question-on-planning-failure behavior.
- [x] Preserve coaching settlement/recovery semantics and the factual empty-session
  summary without an AI request.
- [x] Deduplicate identical map/coaching work and suppress obsolete success/failure;
  distinguish legitimate fresh retries and intended new closing coaching.
- [x] Verify prepared research start, map retry, transcript/coverage retention,
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

- 2026-10-12: Implemented locally. Preparation, retry and approval use closed
  host-only commands; maps and coaching have retained, deduplicated tasks with
  run/version/phase/closure fences before admission and both result paths.
  Inputs capture accepted sources and detached transcript/coverage. Provider
  validation, prompts, budgets, access and settlement policy remain unchanged.
- Verification: 477 Python tests pass (offline, AI/Google/PayMongo mocked), 261
  React tests pass and production build succeeds. Seven new command/view checks
  cover duplicate work, current-map approval, retained uploads after map failure,
  stale map/report success and failure, coaching retry/transcript privacy,
  distinct newer closing work and empty-session summary without AI admission.
  Existing two-client and local durable-credit fixtures pass in the full gate.
- Independent Standards and Spec reviews report zero findings. Ready for local
  human review; no new visual/live AI/provider/PostgreSQL/hosted/device evidence.
  Tickets 05–07 remain; no push/deployment requested. The explicit Implement
  invocation authorizes a local commit and preserves unrelated files.

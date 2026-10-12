# 07 — Remove obsolete paths and verify complete defenses

**What to build:** The complete multiplayer defense runs through the agreed
coordinator, with no alternate scheduling/mutation paths. Maintainers receive
updated navigation and reviewed integration evidence without changing the UI
or deploying the release.

**Blocked by:** 06 — Coordinate restart, ending, reclamation and shutdown.

**Status:** ready-for-human

**Checkpoint:** 4 — cleanup, integration and review.

## Acceptance criteria

- [x] Remove temporary delegation and obsolete mutation/scheduling helpers; do not
  retain forwarding symbols solely to preserve old test patch paths.
- [x] Keep meaningful domain tests; focused tests cross the coordinator seam and
  external HTTP/WebSocket tests remain authoritative.
- [x] Complete mocked two-client code four/eight-turn and research twelve-question
  defenses covering votes, timeout, clarification/probe, retry, reconnect,
  transcript, exact citations and coaching.
- [x] Run the full Python/React suites and production build, required real-local
  accounting/handoff checks and desktop/portrait/landscape keyboard smoke checks.
- [x] Complete Standards/Spec review; update README, agent navigation as needed and
  the shared log with honest mocked/local/live evidence distinctions.
- [x] Preserve pending recovery and unrelated work, frozen main and current live
  services. No push, deployment or live provider transaction in this ticket set.

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
- 2026-10-12: Completed migration cleanup and overall review against approved
  baseline 85c8589. Removed test-worker/seat forwarding helpers; fixtures now
  drive tracked commands and observe state/delivery. Review found transport-owned
  joining; a trusted coordinator command now owns atomic allocation/revision and
  publication, preserving full/closed HTTP responses. Concurrent-join regression
  reproduces red then green. Final gate: 495 Python tests (providers mocked),
  261 React tests, production build and 167 real disposable local PostgreSQL
  checks (providers mocked). Complete mocked two-client code four/eight-turn
  and research/mixed twelve-question/probe flows pass. Synthetic desktop,
  portrait/landscape and keyboard evidence is in docs/ROOM_COORDINATION_REVIEW.md.
  Independent Standards/Spec rechecks report zero remaining findings. Human
  visual review, live providers, hosted checks and installed devices remain
  separate/unverified. No push/deployment; unrelated local files and main preserved.

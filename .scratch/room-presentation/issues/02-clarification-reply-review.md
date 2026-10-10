# 02 — Clarify same-question replies and submission review

**What to build:** A defender can clarify or reply to the panelist without losing
the current question, and everyone understands whether a submission is being
reviewed, its timer is paused/running, and who can recover from failure.

**Blocked by:** 01 — Unify speaking, voting and answering presentation.

**Status:** ready-for-human

- [x] Migrate clarification, answer-probe, interpretation and interpretation-retry
  presentation into the shared meaning used by question, timer, seats and dock.
- [x] Keep the latest ordinary clarification request above its explanation, with
  the original grounded citation and question number unchanged. Preserve all
  original dialogue in the transcript and the existing probe clarification display.
- [x] Use Reply to panelist / Reply time / Replying for a pending answer probe;
  retain the original answer and 30-second server deadline. A new follow-up
  receives a new turn number; a reply or clarification does not.
- [x] Use Reviewing submission with paused/running time, and Selected during
  interpretation rather than implying the defender is actively answering.
- [x] Identify only available retry/direct-answer/saved-submission/continue actions
  for the relevant host or chosen defender, respecting existing attempt limits,
  pending acknowledgment and local recovery choices.
- [x] Keep drafts, failed sends, acknowledgment, reconnect and recovery state with
  their existing owners; verify their behavior survives this migration.
- [x] Add integrated real-seat checks for pending replies, accepted-versus-resolved
  progress and reviewing highlights, plus running/paused countdown evidence.

## Demonstration

original question -> clarification -> answer -> probe -> reply, plus
running/paused submission review and interpretation recovery.

## Scope and handoff

Work on feature/question-first-room within the confirmed shared-room-presentation
specification. Preserve the existing layout, exact citations, server timers,
AI flow, wire messages, local draft/socket ownership, account/payment behavior
and unrelated changes. No push, deployment, native rebuild or frozen-main change
is included. Record implemented behavior and actual verification in the handoff
log; distinguish mocked checks from live/provider/device evidence.

## Comments

2026-10-10: Implemented locally. Offline gate: 443 Python tests with external
AI/Google/PayMongo mocked, 256 React tests and TypeScript/Vite build. Existing
real HTTP/WebSocket tests complete code four/eight-turn and research/mixed
twelve-turn defenses, with clarification, probes, timeout, retry, reconnect and
coaching across the matrix. Isolated Chromium checks desktop, portrait and short
landscape previews, focus restoration, dock navigation and internal scrolling.
Review screenshots and the running preview are linked in README and the review
record. Independent final review is pending; user visual review remains pending.
No push, deployment, native rebuild or live/provider/device claim.

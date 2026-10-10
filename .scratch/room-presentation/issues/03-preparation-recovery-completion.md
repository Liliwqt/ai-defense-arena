# 03 — Make preparation, failure and completion guidance consistent

**What to build:** Hosts and teammates see accurate preparation, waiting,
question-retry and coaching status, with appropriate next-action guidance and
progress rather than stale answering highlights or clocks.

**Blocked by:** 01 — Unify speaking, voting and answering presentation.

**Status:** ready-for-human

- [x] Migrate absent-room, lobby, research mapping/scope, generation, timeout review,
  next-question retry and completion/coaching presentation into the shared meaning.
- [x] Distinguish preparing a first question from reviewing an actual answer or
  missed turn. Do not invent an answer, active reviewer, deadline or progress.
- [x] Preserve research budget/coverage and role labels, code progress, original
  questions/citations and transcript/export data. Existing aliases may reuse
  the shared role naming without changing the record or format.
- [x] Show existing host-only question/coaching recovery and guest waiting guidance
  accurately, including exhausted attempts and disconnected/preview conditions.
- [x] On completion, show no current answering highlight or live answer countdown;
  retain transcript/coaching access and the existing accepted-answer presenter moment.
- [x] Verify the real question/header/seats/dock together for mapping, generation,
  retry and coaching none/generating/failed/ready states, using mocked dependencies.

## Demonstration

research mapping -> preparation -> missed-turn review -> failed question
with host recovery, and completion with generating/failed/ready coaching.

## Scope and handoff

Work on feature/question-first-room within the confirmed shared-room-presentation
specification. Preserve the existing layout, exact citations, server timers,
AI flow, wire messages, local draft/socket ownership, account/payment behavior
and unrelated changes. No push, deployment, native rebuild or frozen-main change
is included. Record implemented behavior and actual verification in the handoff
log; distinguish mocked checks from live/provider/device evidence.

## Comments

2026-10-10: Implemented locally. Offline gate: 443 Python tests with external
AI/Google/PayMongo mocked, 257 React tests and TypeScript/Vite build. Existing
real HTTP/WebSocket tests complete code four/eight-turn and research/mixed
twelve-turn defenses, with clarification, probes, timeout, retry, reconnect and
coaching across the matrix. Isolated Chromium checks desktop, portrait and short
landscape previews, focus restoration, dock navigation and internal scrolling.
Review screenshots and the running preview are linked in README and the review
record. Independent Standards/Spec review is complete with no remaining findings
after Controls corrections in 8f9434d (implementation 99de8d4, baseline d94bccb).
The Spec reviewer independently reran 38 focused React tests. User visual review
remains pending.
No push, deployment, native rebuild or live/provider/device claim.

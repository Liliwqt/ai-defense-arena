# 04 — Complete migration and verify the local room

**What to build:** The complete room uses the shared interpretation across all
agreed displays, with responsive review evidence and end-to-end two-client
checks demonstrating preserved behavior and clearer status.

**Blocked by:** 02 — Clarify same-question replies and submission review;
03 — Make preparation, failure and completion guidance consistent.

**Status:** ready-for-human

- [x] Remove superseded turn/phase interpretation after its callers are migrated;
  retain meaningful local draft/socket/countdown effects and unrelated logic.
- [x] Run the full Python/React suites and production build. Report external
  dependencies as mocked; do not imply live AI or payment verification.
- [x] Complete mocked two-client code defenses at four/eight turns and research/mixed
  defenses beyond eight. Cover clarification, probe, timeout, retry, reconnect,
  transcript and coaching across the matrix; record what actually ran.
- [x] Check desktop, portrait and short landscape views with long question/source
  text, readable labels, internal scrolling, visible focus and keyboard access.
  The existing theme and layout remain; no new header boxes or controls.
- [x] Present the working local preview and screenshots. Update README and the
  shared handoff log with implementation evidence and remaining limitations.
- [ ] Review the completed change against the confirmed specification, including
  preservation of server timers, citation integrity, answer rules and local drafts.
- [x] Preserve unrelated files/deletions. No push, deployment, native rebuild or
  frozen-main change is part of this checkpoint.

## Demonstration

completed two-client defenses and a desktop/phone local preview showing
consistent status across all room displays.

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

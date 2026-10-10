# 01 — Unify speaking, voting and answering presentation

**What to build:** The question, header, seats and bottom dock agree on the
ordinary reaction -> vote -> chosen-defender answer flow, with clear speaking,
Choose a speaker and Your turn / named answering labels in the existing layout.

**Blocked by:** None — can start immediately.

**Status:** ready-for-human

- [x] Establish the shared read-only room-presentation module and connect it to real
  room rendering. Concentrate current/displayed turn identity, role naming,
  counts, timer mode and seat/action meaning rather than adding pass-throughs.
- [x] Preserve the output of advanced and lifecycle phases pending their slices;
  adding the module must not regress clarification, probe, review or recovery.
- [x] Generated reactions retain their own speaking display and existing server
  timing; the next question/citation and vote start remain server-owned.
- [x] Voting and answering labels, highlights and countdowns agree across question,
  header, seats and dock. Online status, votes, reassignment and no-defender
  waiting guidance stay factual.
- [x] Preserve code/research display-role aliases, accepted-versus-resolved counts,
  absent-room/optional-field compatibility and absent-deadline behavior.
- [x] Exercise actual seat rendering and the timer through room-level tests; keep
  existing layout, accessibility, draft and connection checks passing.

## Demonstration

ordinary code/research snapshot sequences with a reaction, vote and
chosen defender, including reassignment and absent deadline.

## Scope and handoff

Work on feature/question-first-room within the confirmed shared-room-presentation
specification. Preserve the existing layout, exact citations, server timers,
AI flow, wire messages, local draft/socket ownership, account/payment behavior
and unrelated changes. No push, deployment, native rebuild or frozen-main change
is included. Record implemented behavior and actual verification in the handoff
log; distinguish mocked checks from live/provider/device evidence.

## Comments

2026-10-10: Implementation complete locally. Whole-room snapshot traces render the
real question, HUD, seats and dock; external account/transport boundaries and
time are mocked. Offline gate: 443 Python tests (AI/Google/PayMongo mocked),
249 React tests and production build. Implementation commit: 0c2f52c.
Independent final Standards and Spec reviews against c567311 returned zero
findings; 65 focused React tests were independently rerun successfully.
See docs/ROOM_PRESENTATION_REVIEW.md.
Tickets 02 and 03 are now unblocked for implementation; ticket 04 owns the
combined responsive preview and user review. No push or deployment.

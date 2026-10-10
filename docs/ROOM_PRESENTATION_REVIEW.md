# Room presentation — ticket 01 review

Implementation: `0c2f52c` on `feature/question-first-room`.
Starting point: `c567311e556ce12de0cec5eb848acdfddb939321`.
Comparison: `git diff c567311...0c2f52c`.

Scope: [ticket 01](../.scratch/room-presentation/issues/01-unify-turn-presentation.md)
within the [confirmed specification](../.scratch/room-presentation/spec.md).
The approved planning documents and glossary edits were already local before
implementation and are included in this commit. Tickets 02–04 remain pending.

## Standards

No documented-standard violations or actionable baseline smells found.
The shared model concentrates ordinary turn identity, role aliases, progress,
countdown inputs and seat/action meaning. Real-room tests keep the question,
HUD, seats and dock, mocking the approved account/transport/time boundaries.
Verification distinguishes offline provider mocks from live, hosted, visual
and device evidence.

Repeated advanced-phase checks and composer recovery wording are deliberately
retained for the later tickets. Draft, transport, server and payment ownership
remains intact.

## Spec

No findings. Shared interpretation is connected to the real question, HUD,
seats, dock and countdown. Reaction/vote/answer guidance, reassignment, role
aliases, accepted/resolved counts and missing deadlines match ticket 01.
Advanced/lifecycle outputs and draft/socket ownership retain baseline behavior.

The independent Spec reviewer reran 65 focused React tests across seven files
covering real room rendering, presentation semantics, question/clarification
display, composer, dock, countdown and socket behavior. All passed offline
with synthetic snapshots and mocked boundaries; comparison whitespace passed.

## Verification and remaining work

- Full offline gate: 443 Python tests (AI/Google/PayMongo mocked), 249 React
  tests and TypeScript/Vite production build passed.
- Six added tests cover actual room views and difficult presentation semantics.
  The first room trace failed on the old vote label before implementation.
- Tickets 02 and 03 are unblocked; ticket 04 retains the combined mocked
  two-client/browser walkthrough and responsive screenshots for user review.
- No new live AI/provider, hosted or physical-device verification, user visual
  approval, push or deployment is claimed. Frozen `main` is unchanged.

Review result: **Standards 0 findings; Spec 0 findings**.

# Completed checkpoint — tickets 02–04 (2026-10-10)

Baseline: `d94bccb4c3da2635675d9a85c9154051f22b808b`. Ticket 01 was already
implemented and reviewed above. This continuation completes clarification,
reply/submission review and lifecycle/recovery presentation, then the combined
local gate. Implementation commit: `99de8d4`; reviewed Controls corrections:
`8f9434d`. Final independent review is complete.

The shared model determines clarification selection, current probe, input mode,
clock description, selected/replying states and recovery/lifecycle guidance.
Composer drafts, admission-recovery and recovery-writing choices, acknowledgment,
transport, authoritative timers, citations and AI behavior remain separate.
Controls retains account/budget/cost gating; transcript coaching uses the same
factual recovery guidance. The existing layout/theme is retained.

## Offline and protocol evidence

- 443 Python tests passed with AI, Google and PayMongo mocked; `DATABASE_URL`
  unset. No live provider or PostgreSQL check is implied.
- 257 React tests and the TypeScript/Vite production build passed after review corrections.
- Whole-room tests retain real question/HUD/seats/dock. Controlled time verifies
  frozen versus running review, replies retaining question number and accepted
  answers, and acknowledgment/ownership/attempt-aware recovery with saved drafts.
- Existing HTTP/WebSocket two-client tests completed code four/eight-turn
  defenses with reactions, probes and reconnect. Research/mixed twelve-turn
  defenses cover vote, clarification, timeout, invalid-generation retry,
  reconnect, transcript/coverage and coaching. These are protocol clients;
  the screenshots below use synthetic browser fixtures, not a live AI defense.
- Protocol evidence: `test_game_server.GameServerTests.test_two_clients_share_reactions_and_reconnect_before_vote_in_four_and_eight_turns`,
  `test_panelist_probe.ProbeProtocolTests.test_two_clients_complete_four_and_eight_turns_with_same_turn_probes`,
  `test_research_coverage.CoverageProtocolTests.test_twelve_question_research_and_mixed_with_vote_clarification_timeout_retry_reconnect_coaching`,
  plus the existing probe expiry/reassignment/retry contracts.

## Local browser review

[Working reply preview](http://127.0.0.1:8832/?preview=1&research=1&probe=1).
This isolated FastAPI preview serves the production build on localhost, with
provider credentials removed and a temporary account database.

| View | Capture |
| --- | --- |
| Desktop reply and exact document excerpt | [Screenshot](../screenshots/room-presentation-desktop-reply.png) |
| Portrait reply | [Screenshot](../screenshots/room-presentation-portrait-reply.png) |
| Short landscape reply | [Screenshot](../screenshots/room-presentation-landscape-reply.png) |
| Paused review and selected defender | [Screenshot](../screenshots/room-presentation-portrait-review.png) |
| Running review | [Screenshot](../screenshots/room-presentation-landscape-running-review.png) |
| Voting | [Screenshot](../screenshots/room-presentation-landscape-vote.png) |
| Clarification replacing question wording | [Screenshot](../screenshots/room-presentation-desktop-clarification.png) |
| Long code source | [Screenshot](../screenshots/room-presentation-landscape-source.png) |
| Interpretation recovery | [Screenshot](../screenshots/room-presentation-portrait-recovery.png) |
| Research mapping Controls | [Screenshot](../screenshots/room-presentation-portrait-controls.png) |
| Coaching and transcript | [Screenshot](../screenshots/room-presentation-portrait-transcript.png) |

Isolated Chromium checks 1440×900 desktop, 390×844 portrait and 844×390 landscape:
header, both seat rows and dock remain in view; no horizontal page overflow or
page exceptions; long question content scrolls inside its card and code source
scrolls horizontally. Keyboard drawer entry/Escape restores focus; visible focus
outlines and dock arrow navigation pass. Research excerpts and coaching are
readable in their existing internally scrolling surfaces. Preview clock assembly
was aligned to avoid a fixture-only extra second. The browser harness initially
used an incorrect source-length threshold; actual source-prefix/suffix and
horizontal-scroll assertions passed after correcting it.

User visual review, live AI/provider quality, hosted deployment and physical
Android/iOS checks remain separate. No push, deployment or native rebuild is part
of this checkpoint; frozen `main` is unchanged.


## Standards — final checkpoint

Zero findings against baseline `d94bccb`. The shared presentation keeps draft,
transport and timer ownership separate; rendering adapters retain interaction
responsibilities. The follow-up inspection also found no documented-standard
breach in the Controls corrections. Read-only static review; this reviewer did
not independently execute runtime tests.

## Spec — final checkpoint

The first review of `99de8d4` found two issues: Controls used lifecycle waiting
guidance during active turns (P2), and App omitted its shared presentation prop
when rendering Controls (P3). Both were corrected in `8f9434d`. A whole-room
Controls trace failed before the correction, then passed through voting,
answering, same-question reply, running submission review and saved/exhausted
recovery. The Spec reviewer independently reran 38 focused React tests and
whitespace checks, with no remaining findings. These checks use synthetic
snapshots and mocked account/transport boundaries.

The final frontend gate passed 257 tests and the production build. All eleven
localhost Chromium fixture checks were rerun on the corrected build and passed;
temporary captures were used so the review gallery remained intact. No server
source changed after the 443-test mocked Python gate.

Review result: **Standards 0 findings; Spec 0 remaining findings**.
User visual review remains pending; publication is outside this checkpoint.


## Publication receipt — 2026-10-10

The user subsequently requested push. Source and review commits through
`2299d77` were pushed to `origin/feature/question-first-room`, with the remote
hash independently verified. Frozen `main` remains `866e923`. All pushed commits
carry `[skip render]`; no deployment or hosted verification is claimed. README
and PROJECT_LOG.md now distinguish publication from the pending visual review
and deployment.

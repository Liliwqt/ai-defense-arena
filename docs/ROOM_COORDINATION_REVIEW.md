# Room coordination — local integration review

Date: 2026-10-12. Branch: `feature/question-first-room`.
User-approved overall review baseline: `85c8589`.
Ticket 07 starts at `2bf80b5`; prerequisite recovery/planning changes are recorded
separately in `d8c8b7f` and preserved throughout the migration.

## Implementation

All seven [tickets](../.scratch/room-coordination/issues/) implement the confirmed
[specification](../.scratch/room-coordination/spec.md).
The room coordinator owns typed commands, captured AI work, clocks, private
publication, joining/presence and lifecycle fencing. Transport retains account,
origin, token and resource checks, upload processing, registry admission and
service-lease composition. Timing semantics, detached progression, prompts,
citations, prices and database transactions retain their existing implementations.

The legacy command bridge, transport generation workers, selected-seat forwarding
symbol and test-only direct-worker shim are removed. Recovery, clarification,
timed-room and research-race fixtures now invoke tracked commands with controlled
provider/time dependencies and observe results. Distinct domain/admission tests
remain; there is no alternate test scheduling implementation.

## Offline and local-store evidence

- Final full Python gate: 495 checks in
  `/tmp/room-coordination-07-python-verified.log`, AI/Google/PayMongo mocked.
  The concurrent-join regression is included. An intermediate run exposed a
  fixture racing commit against delivery; it now waits for the observed snapshot
  before asserting retry status. All eight recovery checks also pass separately.
- React: 261 checks in 22 files, `/tmp/room-coordination-07-react-full.log`.
  Production build succeeds, `/tmp/room-coordination-07-build.log`.
  No frontend files changed during this checkpoint.
- Complete mocked two-client HTTP/WebSocket defenses: 18 checks in
  `/tmp/room-coordination-07-full-defenses-final.log`. Code four/eight-turn and
  research/mixed twelve-question flows include votes, clarification/probes,
  timeout, automatic/manual retry, reconnect, retained transcript, exact source
  references and coaching. These are transport tests, not a live browser defense.
- Final real disposable local PostgreSQL: 167 checks in
  `/tmp/room-coordination-07-postgres-reviewed.log`, external providers mocked.
  This includes verification after coordinator-owned joining.
  Each case creates/drops its own database; no hosted account store is accessed.
- Review correction: joining still updated players/revisions in transport.
  A trusted `JoinDefender` command now allocates seats and publishes under
  coordinator ownership. The new command-seam regression fails before the
  implementation and passes afterward; 33 affected command/HTTP/defense checks
  pass in `/tmp/room-coordination-07-join-green.log`. Full/closed HTTP responses
  and browser rejection of trusted commands are retained.

Earlier PostgreSQL and detailed keyboard evidence below was recorded before
session resumption; its temporary logs are no longer available. The continuation
reran the full Python/React gates and build, restarted the preview and refreshed
the three viewport screenshots/overflow checks. PostgreSQL was not repeated.

## Synthetic browser and keyboard evidence

The production build is served by a credential-free local FastAPI preview with a
separate temporary SQLite path. Review at
<http://127.0.0.1:8840/?preview=1>. Add `&research=1`, `&long=1`, `&vote=1`,
`&reaction=1`, `&clarify=1`, `&probe=1`, `&submission=paused`,
`&submission=running`, `&submission=retry`, or `&complete=1`.

| Viewport | Evidence |
| --- | --- |
| Desktop 1440 × 900 | Long question scrolls inside its card; no horizontal page overflow. Controls opens with Enter, traps focus, closes with Escape and restores its trigger focus. |
| Portrait 390 × 844 | Compact seat strips, question/document excerpt and bottom dock remain visible. No horizontal page overflow. Keyboard can focus and scroll the question. |
| Landscape 844 × 390 | Both seat rows and dock remain visible while the question scrolls. Long source line uses a 789-pixel scroller for 2694 pixels of content with `white-space: pre`. |

Temporary screenshots (not committed binary assets):

- `/tmp/room-coordination-07-desktop.png`
- `/tmp/room-coordination-07-portrait.png`
- `/tmp/room-coordination-07-landscape.png`
- `/tmp/room-coordination-07-landscape-citation.png`

Playwright also checked reaction, voting, clarification, probe, paused submission,
interpretation recovery and failed coaching previews. Mobile Team chat opens
with the keyboard; Account and Transcript drawers are accessible. The account
preview truthfully disables account actions. The only observed browser console
error was the existing missing `favicon.ico` (404); no app exception was observed.
Draft retention, acknowledgments, reconnect recovery and disabled repeat submits
are covered by the passing React/transport tests; preview submissions are
intentionally disabled, so the screenshots do not prove those behaviors.

## Review boundaries

Independent Standards/Spec review compares the complete migration with
`85c8589`. Final rechecks report zero remaining Spec findings and zero hard or
optional Standards findings. The Spec reviewer independently reran all five
coordinator checks, including concurrent joining.
User visual review is pending. No live AI-quality check, real provider payment,
hosted deployment/proxy check or installed/physical second-device confirmation
is claimed. Frozen `main`, live services and unrelated local files remain unchanged.
Publication and deployment require a later user request.

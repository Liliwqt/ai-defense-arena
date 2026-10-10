# Room presentation — approved ticket breakdown

User approved as drafted, 2026-10-10. Four separate local implementation tickets
are published with status ready-for-agent; this file retains the reviewed breakdown.
Source: confirmed Shared room presentation and clearer turn status specification.
The source specification remains unchanged.

## Delivery approach

Four slices in one local checkpoint. Each delivers a verifiable room behavior
and leaves existing behavior working. No server, schema, payment or protocol
change is needed. Expand the shared presentation meaning alongside existing
paths, migrate behavior by slice, and remove superseded interpretation only
after callers have migrated. Rendering, local drafts and socket state remain
in their existing owners.

## 01 — Unify speaking, voting and answering presentation

**What to build:** The question, header, seats and bottom dock agree on the
ordinary reaction -> vote -> chosen-defender answer flow, with clear speaking,
Choose a speaker and Your turn / named answering labels in the existing layout.

**Blocked by:** None — can start immediately.

Proposed acceptance criteria:

- Establish the shared read-only room-presentation module and connect it to real
  room rendering. Concentrate current/displayed turn identity, role naming,
  counts, timer mode and seat/action meaning rather than adding pass-throughs.
- Preserve the output of advanced and lifecycle phases pending their slices;
  adding the module must not regress clarification, probe, review or recovery.
- Generated reactions retain their own speaking display and existing server
  timing; the next question/citation and vote start remain server-owned.
- Voting and answering labels, highlights and countdowns agree across question,
  header, seats and dock. Online status, votes, reassignment and no-defender
  waiting guidance stay factual.
- Preserve code/research display-role aliases, accepted-versus-resolved counts,
  absent-room/optional-field compatibility and absent-deadline behavior.
- Exercise actual seat rendering and the timer through room-level tests; keep
  existing layout, accessibility, draft and connection checks passing.

Demo: ordinary code/research snapshot sequences with a reaction, vote and
chosen defender, including reassignment and absent deadline.

## 02 — Clarify same-question replies and submission review

**What to build:** A defender can clarify or reply to the panelist without losing
the current question, and everyone understands whether a submission is being
reviewed, its timer is paused/running, and who can recover from failure.

**Blocked by:** 01 — Unify speaking, voting and answering presentation.

Proposed acceptance criteria:

- Migrate clarification, answer-probe, interpretation and interpretation-retry
  presentation into the shared meaning used by question, timer, seats and dock.
- Keep the latest ordinary clarification request above its explanation, with
  the original grounded citation and question number unchanged. Preserve all
  original dialogue in the transcript and the existing probe clarification display.
- Use Reply to panelist / Reply time / Replying for a pending answer probe;
  retain the original answer and 30-second server deadline. A new follow-up
  receives a new turn number; a reply or clarification does not.
- Use Reviewing submission with paused/running time, and Selected during
  interpretation rather than implying the defender is actively answering.
- Identify only available retry/direct-answer/saved-submission/continue actions
  for the relevant host or chosen defender, respecting existing attempt limits,
  pending acknowledgment and local recovery choices.
- Keep drafts, failed sends, acknowledgment, reconnect and recovery state with
  their existing owners; verify their behavior survives this migration.
- Add integrated real-seat checks for pending replies, accepted-versus-resolved
  progress and reviewing highlights, plus running/paused countdown evidence.

Demo: original question -> clarification -> answer -> probe -> reply, plus
running/paused submission review and interpretation recovery.

## 03 — Make preparation, failure and completion guidance consistent

**What to build:** Hosts and teammates see accurate preparation, waiting,
question-retry and coaching status, with appropriate next-action guidance and
progress rather than stale answering highlights or clocks.

**Blocked by:** 01 — Unify speaking, voting and answering presentation.

Proposed acceptance criteria:

- Migrate absent-room, lobby, research mapping/scope, generation, timeout review,
  next-question retry and completion/coaching presentation into the shared meaning.
- Distinguish preparing a first question from reviewing an actual answer or
  missed turn. Do not invent an answer, active reviewer, deadline or progress.
- Preserve research budget/coverage and role labels, code progress, original
  questions/citations and transcript/export data. Existing aliases may reuse
  the shared role naming without changing the record or format.
- Show existing host-only question/coaching recovery and guest waiting guidance
  accurately, including exhausted attempts and disconnected/preview conditions.
- On completion, show no current answering highlight or live answer countdown;
  retain transcript/coaching access and the existing accepted-answer presenter moment.
- Verify the real question/header/seats/dock together for mapping, generation,
  retry and coaching none/generating/failed/ready states, using mocked dependencies.

Demo: research mapping -> preparation -> missed-turn review -> failed question
with host recovery, and completion with generating/failed/ready coaching.

## 04 — Complete migration and verify the local room

**What to build:** The complete room uses the shared interpretation across all
agreed displays, with responsive review evidence and end-to-end two-client
checks demonstrating preserved behavior and clearer status.

**Blocked by:** 02 — Clarify same-question replies and submission review;
03 — Make preparation, failure and completion guidance consistent.

Proposed acceptance criteria:

- Remove superseded turn/phase interpretation after its callers are migrated;
  retain meaningful local draft/socket/countdown effects and unrelated logic.
- Run the full Python/React suites and production build. Report external
  dependencies as mocked; do not imply live AI or payment verification.
- Complete mocked two-client code defenses at four/eight turns and research/mixed
  defenses beyond eight. Cover clarification, probe, timeout, retry, reconnect,
  transcript and coaching across the matrix; record what actually ran.
- Check desktop, portrait and short landscape views with long question/source
  text, readable labels, internal scrolling, visible focus and keyboard access.
  The existing theme and layout remain; no new header boxes or controls.
- Present the working local preview and screenshots. Update README and the
  shared handoff log with implementation evidence and remaining limitations.
- Review the completed change against the confirmed specification, including
  preservation of server timers, citation integrity, answer rules and local drafts.
- Preserve unrelated files/deletions. No push, deployment, native rebuild or
  frozen-main change is part of this checkpoint.

Demo: completed two-client defenses and a desktop/phone local preview showing
consistent status across all room displays.

## Blocking graph and review

01 -> {02, 03} -> 04

02 and 03 depend on the shared presentation module delivered by 01, not on each
other. They may touch shared rendering and interpretation code: sequential local
implementation is practical, but shared files alone are not a behavioral blocker.
04 waits for both to finish before deleting remaining superseded paths and
claiming complete integrated verification.

User approved the granularity and blocking edges without merges or splits.
Four separate ready-for-agent tickets are published in the local tracker, each
retaining its approved acceptance criteria and blockers. The parent specification
remains unchanged. Ticket 01 is the only initially unblocked task.

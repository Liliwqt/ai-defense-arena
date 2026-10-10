# Shared room presentation and clearer turn status

Status: ready-for-agent
Date: 2026-10-10
Branch: feature/question-first-room
Source baseline: c567311

## Problem Statement

Defenders need the question, timer, panelist seats and answer area to describe
the same moment in a defense. Those displays currently reconstruct turn and
phase meaning separately, making changes to reactions, clarification, answer
probes and recovery harder to keep consistent.

The existing wording also leaves room for confusion: a defender can appear to
be answering while the panelist reviews their submission, and an answer probe
can sound like a new follow-up question even though it belongs to the same turn.
This specification addresses that clarity and architectural friction; it does
not claim that a synchronization or financial defect has been reproduced.

## Solution

Keep the current black-and-white room layout. Concentrate interpretation of the
authoritative room snapshot in one deep presentation module, then use its
shared meaning across the question, timer, seats and bottom dock.

Use clear labels for voting, answering, selected defenders, reviewing a
submission and same-question replies. Name the next available action and who
can take it. Preserve existing server behavior, exact grounded citations,
connection handling, answer drafts and local recovery choices.

## User Stories

1. As a defender, I want the question, timer, seats and bottom dock to agree about the current defense turn, so that I know what is happening.
2. As a defender, I want the current layout and theme retained, so that I can continue using the room without learning a redesigned screen.
3. As a new participant, I want create/join and lobby guidance without an implied active question, so that I understand how to begin.
4. As a host, I want research mapping and question-preparation status to be explicit, so that I know when the panel is working and when I can act.
5. As a defender, I want a panelist reaction identified as speaking before the next question, so that I can follow the conversation.
6. As a reconnecting defender, I want to resume the current reaction or turn without replaying an earlier phase, so that I see the same moment as teammates.
7. As a voting defender, I want “Choose a speaker” and the existing vote countdown, so that I know to vote rather than answer.
8. As a defender, I want online status and vote counts identified with text as well as highlights, so that selection remains understandable without relying on color.
9. As a chosen defender, I want “Your turn” and my selected seat identified as answering, so that I know I can respond.
10. As a teammate, I want the chosen defender's name and “[name] is answering,” so that I know who is responsible and can help through team chat.
11. As a defender, I want authoritative speaker reassignment reflected consistently, so that a disconnected participant is not presented as able to answer.
12. As a defender, I want a factual waiting message when nobody can answer, so that I understand that the server clock continues.
13. As a submitting defender, I want “Reviewing submission” and explicit paused/running timer status, so that I understand what happens while the panelist reads.
14. As a teammate, I want the reviewing defender labeled “Selected” rather than “Answering,” so that selection does not imply they are actively typing.
15. As a chosen defender receiving an answer probe, I want “Reply to panelist” and “Reply time,” so that I understand the requested detail and its deadline.
16. As a teammate, I want the chosen defender identified as “Replying” during an answer probe, so that I can distinguish it from the original answer.
17. As a defender, I want an answer probe to retain the same question number, so that I do not mistake it for an additional budgeted question.
18. As a defender, I want a new follow-up question to receive its own question number, so that progress remains accurate.
19. As a defender, I want a clarification request above the latest explanation with the existing citation preserved, so that I understand the question without losing its source.
20. As a defender, I want original questions, answers and clarification exchanges retained in the transcript, so that a display change does not rewrite the defense record.
21. As a research defender, I want consistent reviewer names and research progress, so that the question, seats and timer refer to the same reviewer and coverage.
22. As a defender, I want the full question and exact code or extracted-document excerpt readable, so that status improvements do not crowd the material I am defending.
23. As a defender, I want my original answer retained during an answer probe, so that giving extra detail does not replace what I already said.
24. As a defender, I want unresolved turns distinguished from accepted answers, so that a pending reply does not falsely advance resolved progress.
25. As a chosen defender after interpretation failure, I want guidance naming the recovery actions actually available to me, so that I can retry or answer directly without guessing.
26. As a host, I want host-only retry guidance distinguished from defender recovery actions, so that teammates are not told to use controls they cannot access.
27. As a defender, I want my draft and failed-send recovery preserved, so that clearer status does not lose my response.
28. As a defender, I want submitting and reconnecting states to keep their existing protections, so that repeat submissions and stale connections do not change behavior.
29. As a defender, I want timeout, question failure and coaching failure labeled truthfully, so that missing answers or unavailable output are not presented as successful completion.
30. As a defender, I want no live answer timer or answering highlight after completion, so that I know the defense has finished and can review the transcript and coaching.
31. As a phone participant, I want concise labels that fit portrait and short landscape screens, so that the question and controls remain readable.
32. As a keyboard user, I want retained focus behavior, readable status and accessible seat labels, so that I can participate without a pointer.
33. As a maintainer, I want turn and phase interpretation concentrated behind one interface, so that future presentation changes do not require reconstructing the same rules across callers.
34. As a maintainer, I want actual room-rendering tests using real seats and timer behavior, so that mocked seats cannot hide contradictions between displays.

## Implementation Decisions

1. Build one web-room presentation module around the existing read-only room
   snapshot, including an absent-room state. Its interface supplies shared
   current-turn identity, dialogue/citation display, role labels, progress,
   timer mode and seat/next-action meaning. Derive that meaning once for the
   room and share it with its rendering adapters.
2. Concentrate interpretation rather than introducing forwarding helpers or
   merely moving rendering code. The deletion test is whether removing the
   module would force callers to reconstruct phase, pause and turn knowledge.
3. Rendering adapters retain layout, accessibility markup and local interaction.
   The presentation module performs no mutation, network request, submission
   authorization, scheduling or automatic phase advancement.
4. Current-turn interpretation must handle an accepted original answer with a
   pending answer probe. Track active/displayed turn identity separately from
   accepted-answer and resolved-turn counts; these are intentionally different.
5. Preserve existing optional-field fallbacks. An absent explicit resolved flag
   falls back to the existing answer/timeout interpretation; an explicit false
   is respected. Absent pause information retains current paused-interpretation
   compatibility. A missing deadline never produces an invented countdown.
6. Use shared code/research display-role mapping in migrated room displays.
   Preserve internal role identity, including the research display alias
   “Critical Reviewer.” Existing transcript/plan aliases may reuse that mapping
   without altering stored dialogue, export structure or reviewer assignments.
7. Keep local countdown interpolation separate: start from the server snapshot's
   time/deadline, subtract elapsed monotonic browser time and clamp at zero.
   Preserve frozen remaining time while paused. Rendering zero does not advance
   the server phase or authorize a late action.
8. During voting, use “Choose a speaker,” the existing Vote countdown, the asking
   panelist and existing online/vote seat states. The server retains the full
   15-second voting window.
9. During an active question, use “Your turn” for the chosen defender and
   “[name] is answering” for teammates, with an “Answering” seat state and the
   existing Answer countdown. The server retains the 120-second answer window.
10. During an answer probe, use “Reply to panelist,” “Reply time” and “Replying.”
    Teammates may see “[name] is replying.” Keep the original answer, question
    number, grounded citation and existing 30-second reply deadline. A new
    follow-up remains a distinct defense turn.
11. During submission interpretation, use “Reviewing submission · Timer
    paused/running” according to the snapshot and label the chosen defender
    “Selected.” Retain existing direct-answer availability when time is running;
    a status label must not disable or enable a different action.
12. During interpretation failure, name who can retry, use the saved submission,
    write/submit directly or continue with the original answer. Only describe
    actions allowed by existing ownership, attempt limits and local recovery
    choices. Preserve whether time is paused or running.
13. Keep connection retries, connection-version guards, saved room tokens,
    submission acknowledgments and transport errors in the existing socket
    module. It may continue interpreting acknowledgment identity; it is not
    migrated into presentation as part of this checkpoint.
14. Keep answer drafts, failed-send recovery, recovery-writing selection and the
    local admission-recovery flag in the existing answer composer. Preserve
    draft identity across room/turn/original-question/probe changes, clearing
    after acknowledged clarification and restoration from a saved submission.
    Combine snapshot-derived meaning with these local facts without overriding
    their permissions or pending-send state.
15. Preserve presenter-highlight behavior triggered by accepted answers. It
    remains distinct from current chosen-defender state and resolved progress;
    reviewing labels describe selection rather than active answering.
16. When the chosen defender disconnects, reflect the latest server selection.
    With no chosen online defender, show factual reconnection guidance and the
    existing running clock rather than inventing a name or pausing it.
17. Preserve generated reactions as their own existing speaking phase. Do not
    reveal the next question/citation during the reaction or start a player
    timer. Retain the server-owned 4–12-second duration, empty-reaction bypass
    and reconnect behavior.
18. Preserve clarification display: the defender's latest request appears above
    the latest explanation, replacing the large question wording. Retain the
    original grounded question/citation and all exchanges in the transcript.
    Probe clarification keeps its existing separate display.
19. Distinguish absent room, lobby, research mapping, scope ready, initial
    question preparation, reviewing an answer/missed turn, failed preparation
    and failed question generation. Guidance must identify the existing host
    action or team waiting state without implying an available answer timer.
20. Distinguish defense completion from coaching generation/failure/readiness.
    Use the existing host recovery when coaching fails; show no live answer
    countdown or current answering highlight on completed turns.
21. Retain the current theme, seat placement, question/citation layout, chat tabs,
    focus behavior and responsive scrolling. Fit concise status wording into
    existing surfaces; add no header boxes or clarification controls. Use text
    and accessible labels alongside existing highlights rather than color alone.
22. Preserve the existing wire messages, snapshots, server authorization, timer
    rules, question-generation calls, citations, research coverage and budgets.
    Code defenses remain four to eight turns; research/mixed defenses retain
    their approved coverage policy. Existing timed-turn and shared progression
    decisions remain intact. No schema or persistence change is required.

## Testing Decisions

1. The user already confirmed the testing seams during planning and the final
   plan review. Prefer the existing whole-room rendering interface as the
   primary acceptance seam; mock external dependencies, not the real question,
   HUD, seat strips or dock whose agreement is being verified.
2. Good tests assert externally observable text, timer modes, accessible
   highlights, progress and available actions for a server snapshot. Avoid
   asserting internal decomposition, implementation-specific calls or derived
   object layouts solely because the module exposes them.
3. Use a small set of focused presentation-interface checks for difficult
   semantics: null room, optional fields, missing deadline, answered-but-pending
   probe, timed-out turn and code/research role display. Keep them complementary
   to whole-room tests, not mirrors of every rendering implementation detail.
4. Preserve prior countdown and answer-composer behavioral tests for vote,
   answer/reply expiry, drafts, send failure, direct recovery, pending submission,
   clarification clearing, probe identity and reconnect. Add explicit paused
   versus running interpretation countdown checks using a controlled clock.
5. Prior art includes existing room rendering, question/citation, research
   coverage, composer, socket and countdown tests. Some current room tests mock
   the seats; add a real-seat integration trace that proves question, timer,
   role naming and highlights agree.
6. Exercise reaction -> voting -> answering; same-question clarification;
   answer -> probe -> reply; running/paused interpretation and recovery;
   reassignment/no online defender; timeout; generation retry; and complete
   coaching states. Verify new follow-ups advance turn progress, while replies
   and clarifications do not consume another question.
7. Retain existing authenticated room HTTP/WebSocket flows as the server
   integration seam, with AI and payment/account dependencies mocked. Complete
   two-client code defenses at four/eight turns and research/mixed defenses
   beyond eight, covering clarification, probe, timeout, retry, reconnect,
   transcript and coaching across the scenario matrix. Record what actually ran.
8. Check synthetic desktop, portrait and short landscape browser previews with
   long dialogue and source text. Verify full citation readability, internal
   scrolling, visible focus, keyboard navigation and no clipped status/controls.
   Present the working local preview and review screenshots.
9. Run the full Python and React suites and production build. Label offline
   evidence as AI/Google/PayMongo mocked; unchanged AI output is not live
   conversation-quality evidence. This specification's creation runs only
   documentation checks, not the implementation acceptance gate.
10. Report live conversation, hosted checks and physical installed-device checks
    separately. None may be inferred from a mocked defense or viewport preview.

## Out of Scope

- Conversation-context or asynchronous room-transition refactors from the other
  architecture candidates.
- A broader layout redesign, new themes, header boxes or question/clarification
  interaction controls.
- Moving socket acknowledgments/reconnect or draft/local recovery lifecycle into
  the presentation module.
- Altering timers, phase transitions, question counts, research coverage, reply
  limits, answer interpretation, AI prompts/models or extra AI requests.
- Changing citations, stored transcript content or export format.
- Payment/account flows, authorization, balances, storage or schema migrations.
- Streamlit changes, native app rebuilds or reintroducing a 3D room.
- Commit, push, deployment or changes to frozen main through this specification
  request. Discovered unrelated bugs are recorded separately rather than silently
  expanding the checkpoint.

## Further Notes

- Source: the confirmed room-presentation planning interview, including all
  seven user responses. This is a local Markdown tracker specification; the
  status indicates buildable work, not implementation or publication approval.
- Deliver one local checkpoint in reviewed slices: establish shared
  interpretation, migrate the room displays/countdown inputs, then verify the
  complete behavior and selected UX improvements.
- Preserve pre-existing planning/glossary work and all unrelated files or
  deletions. Update the README and handoff log with actual implementation and
  verification evidence during implementation.
- No new ADR is required: the selected consolidation is reversible and respects
  existing timed-turn, shared progression and payment decisions.
- Rooms remain in memory with one worker/instance. Do not restart or deploy the
  hosted app as part of this local specification checkpoint.

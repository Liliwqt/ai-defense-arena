# Shared room presentation — planning interview

Status: planning complete; user confirmed shared understanding, 2026-10-10.
No implementation authorized by this document.

Branch: `feature/question-first-room`. Starting source: `c567311`.

Specification published locally: [Shared room presentation](../.scratch/room-presentation/spec.md),
status `ready-for-agent`. This interview remains the decision record.

## Aim

Explore candidate 1 from the architecture review: concentrate interpretation of
the authoritative room snapshot so the question, timer, seat strips and answer
area share the same meaning of a defense turn. Keep the current layout while
improving status, highlight and next-action clarity. The module shape below is a
planning proposal; final implementation details follow the specification.

## Established facts

- `QuestionCard.tsx` and `AnswerComposer.tsx` independently search for the current
  turn, including the exception for an answered turn with a pending probe.
- `HUD.tsx`, `FlatRoom.tsx` and `useRoomCountdown.ts` separately interpret phase,
  paused interpretation and chosen-defender state.
- Latest clarification text replaces the large question wording; the original
  grounded question and citation remain in the defense turn and transcript.
- A generated reaction has a server-owned phase before voting. Server snapshots
  and deadlines remain authoritative; derived presentation is not permission to
  accept an answer.
- `useRoomSocket.ts` owns connection recovery and pending-submission acknowledgment.
  `AnswerComposer.tsx` owns its draft and local recovery choices.
- Research display naming maps internal `Critical Judge` to `Critical Reviewer`
  in multiple rendering paths; any consolidation must preserve the displayed role.
- Existing `App.test.tsx` mocks the panelist and defender seats, so that test alone
  cannot prove the question, timer and seat highlights agree. Integrated checks
  with real seat rendering are needed for that claim. Countdown tests currently
  cover vote/question/probe; running versus paused interpretation needs explicit
  coverage if the countdown input is migrated.
- Existing shared progression and synchronous timed-turn decisions are recorded
  in `ARCHITECTURE_PLAN.md`; this exploration does not reopen them.
- Main is frozen; publishing and deploying require a later user request.

## Design tree and interview frontier

Round 1 decisions confirmed by the user:

1. Include intentional UX changes alongside the refactor. The particular UX
   changes are limited by round 2 below; this is not approval for an unrestricted redesign.
2. Keep connection retries, acknowledgment handling and answer drafts in their
   existing modules. Concentrate snapshot interpretation for the question,
   timer, seat strips and answer area.
3. Use full offline Python/React suites and build,
   mocked two-client code/research checks for reactions, voting, clarifications,
   probes, timeouts, reconnect and coaching, plus desktop/portrait/landscape
   keyboard/layout checks. Live AI/provider/native-device evidence stays separate.

Round 2 decision confirmed by the user:

4. Include clearer phase/timer labels, consistent
   panelist/chosen-defender highlights and next-action guidance within the existing
   black-and-white layout. Question/clarification interaction changes and a broader
   layout redesign are outside the selected scope.

Round 3 decisions confirmed by the user:

5. Distinguish who acts next from who is merely selected, and explicitly identify
   running versus paused answer time during submission review and recovery.
6. Display the same-question answer probe as
   "Reply to panelist" / "Reply time" and "Replying" while retaining the question
   number; reserve "follow-up question" for a new defense turn.

Final confirmation received: the user selected "Matches—finish planning" for
the consolidated plan. The interview frontier is empty. Specification published locally;
implementation and publication remain later requested steps.

## Proposed module shape and ownership

- One web-room presentation module interprets a read-only `RoomState` snapshot
  (or the absent-room state), concentrating current-turn identity, displayed
  dialogue/citation, role naming, progress, timer mode and seat/action meanings.
- Use a shared derived result for the question, HUD, seat strips and bottom dock.
  Rendering adapters retain layout, accessibility markup and local interaction.
  The interface describes what the current snapshot means; it does not mutate
  snapshots, authorize submissions, send messages or start timers.
- `useRoomCountdown` retains local time interpolation from server time and
  elapsed monotonic browser time, driven by the derived timer mode/deadline.
  No fabricated deadline or automatic phase transition on browser expiry.
- `useRoomSocket` retains connection versions, reconnect, stored room tokens,
  error handling and submission acknowledgments. `AnswerComposer` retains draft
  lifecycle, send failure, local recovery-writing and admission-recovery state.
  Snapshot-derived action context is combined with these local facts; it cannot
  override them or broaden answer permissions.
- Preserve compatibility for optional snapshot fields: existing absent-field
  fallbacks, especially `clock_paused !== false`, and resolved-turn fallback.
- Preserve the distinction between an accepted original answer and a resolved
  turn: a pending answer probe is still the same unresolved turn. Keep App's
  accepted-answer presenter highlight distinct from resolved progress.
- Consolidate existing code/research role-label mapping where migrated displays
  need it, preserving internal role identity and current transcript/export data.
- No change to AI requests, schemas, role order, server phases, timer durations,
  research budget/coverage, payment/account authorization or Streamlit behavior.

Depth and deletion test: callers should stop reconstructing phase/turn/pause
meaning. Removing the new module would require rebuilding that knowledge across
them. A collection of forwarding functions or merely moving JSX is insufficient.
Existing progression and timed-turn modules stay intact. No new ADR is needed
for this reversible consolidation; existing recorded decisions are preserved.

## Display acceptance examples

| Moment | Status / next action | Highlight and timer |
| --- | --- | --- |
| No room / lobby | Create or join; host starts when ready; guests wait | No implied active question; no answer clock |
| Research mapping / preparation | Mapping research, scope ready, or preparing question as applicable | No answering highlight or invented deadline |
| Generated reaction | Panelist speaking; the question and vote follow | Speaking panelist; existing server-owned 4–12-second transition, no player clock |
| Voting | Choose a speaker | Asking panelist; votes on online defenders; existing 15-second Vote time |
| Question active | Your turn for the chosen defender; [name] is answering for teammates | Chosen defender Answering; existing 120-second Answer time |
| Chosen defender absent | Waiting for a defender to reconnect; clock continues | No invented chosen name; preserve authoritative reassignment |
| Same-question answer probe | Reply to panelist for the chosen defender; [name] is replying for teammates | Chosen defender Replying; existing 30-second Reply time; unchanged question number |
| Submission being interpreted | Reviewing submission · Timer paused/running | Chosen defender Selected; preserve paused remaining time or running deadline |
| Interpretation failure | Review failed; identify who can retry, use a saved answer, submit directly or continue the original answer | Selected defender; explicit paused/running timer; only existing available recovery actions |
| Next-question failure | Question unavailable; host can retry when allowed | No answer countdown; accepted answers retained |
| Complete / coaching | Coaching being prepared, coaching unavailable with host recovery guidance, or defense complete | No live answer highlight/countdown; report/transcript remain accessible |

Wording can be shortened for mobile without changing meaning. Do not add header
boxes, change the question/citation layout or introduce new clarification controls.
Keep disabled-action explanations factual when disconnected, awaiting an
acknowledgment, out of attempts or in preview mode.

## Acceptance scenarios and verification

- Reaction -> vote -> chosen defender: all real room displays agree, full voting
  and answering windows remain server-owned, and reconnect does not replay a reaction.
- Ordinary clarification: request stays above the latest explanation, exact
  citation and question number remain, original wording stays in the transcript.
- Answer probe: original answer remains, reply uses the same question number,
  new follow-up consumes a new question, and accepted versus resolved progress
  and presenter highlights remain distinct.
- Interpretation: verify both running and paused timers; limits and recovery
  actions stay unchanged. Retain draft/send-failure/reconnect tests.
- Reassignment, timeout, retry and completion: highlights and next-action labels
  follow the authoritative snapshot; no stale display implies an available action.
- Cover code and research roles, mixed citations, null room, optional fields,
  planning failure, missing deadline and coaching status.
- Tests exercise the derived interface and actual room rendering. Add integrated
  checks with real seat strips rather than relying on existing App seat mocks.
- Run the full Python and React suites plus production build. AI, Google and
  PayMongo remain mocked in the offline gate.
- Run mocked two-client code defenses at four/eight turns and research/mixed
  defenses beyond eight, covering reconnect, clarification, probe, timeout,
  transcript and coaching across the matrix. Record evidence by actual scenario.
- Inspect desktop, portrait and short landscape previews, long question/source
  text, keyboard focus and internal scrolling. No clipped controls or new layout
  change; labels and error guidance must fit.
- Present local screenshots and the working preview. Live AI, hosted proxy,
  payment and installed-device checks remain separate claims and are not needed
  to infer that the offline refactor preserves dialogue generation.

## Delivery and handoff

One local checkpoint in reviewed slices: establish snapshot interpretation and
its tests, migrate the room displays and countdown inputs, then verify the
complete UX and integration behavior. Preserve unrelated work. Update README
and PROJECT_LOG.md with actual implementation/verification evidence when built.
Planning does not authorize implementation, commit, push or deployment. Main
and the hosted release remain unchanged.

## Verification evidence

Planning only: static code and history inspection. No new tests, AI requests,
payments, hosted checks or physical-device checks run for this interview.

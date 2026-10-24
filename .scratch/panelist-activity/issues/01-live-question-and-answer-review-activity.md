# 01 — Live question and answer-review activity

**What to build:** Joined defenders see the selected Editor notes activity during
opening/next-question preparation and answer review, with safe current context
and immediate complete removal when the resulting question or review outcome is
ready. This first slice carries the shared presentation/context policy through
real authorized room state and the web interface.

**Blocked by:** None — can start immediately.

**Status:** ready-for-human

**Parent:** [Panelist activity specification](../spec.md).

**What it delivers:** The core visible wait/result cycle in real research/mixed
rooms, including retained-versus-accepted answer status and current-only recovery.

- [x] Opening and subsequent question preparation and answer review expose the factual task, appropriate known reviewer and safe bounded highlighted context; unknown/unsuitable context uses a truthful fallback.
- [x] Existing authorized snapshots and waiting presentation supply the shared information additively; host/guest members see the same safe update and a room code alone grants no access.
- [x] Normal and fast completion remove all activity/highlights in the ready rendered state, without a retained collapsed section or animation delay.
- [x] Failure, admitted retry/backoff, cancellation, ending, restart and stale updates preserve correct current-only display; reconnect/navigation preserve authoritative elapsed origin without replaying history.
- [x] The compact desktop/phone treatment keeps paper, timer and controls usable, renders source phrases as text, honors reduced motion and avoids stealing focus or announcing every elapsed tick.
- [x] Retained submissions are not labeled accepted prematurely; accepted answers and existing turn/timer/credit/model rules survive waits and recovery unchanged.
- [x] Whole-App and authenticated controlled-clock provider-mocked checks cover the visible cycle, safe disclosure, shared/current-only recovery, no added requests and absence of activity content from transcript/analytics.

**Primary story coverage:** 1–10, 19–21, 23–32, 33–42, 43–60, 61–68, 70–73, 75–76, 78–79.

## Shared requirements

- Use A — Editor notes: compact factual task line, vertical gutter and visible
  highlighted already-validated context. Prototype source is local branch
  `prototype/panelist-activity`, comparison `ef445a2`, explicit decision `f98d50d`.
  Preserve that primary-source pointer in each published ticket; do not copy the
  synthetic controls, state inspector or comparison variants into production.
- Use actual authorized operation state; expose only bounded context appropriate
  to reveal now. No private reasoning, pending questions, suggested answers,
  private chat, unvalidated drafts or new provider/translation requests.
- Clear the entire activity block/highlights on result, failure, cancellation,
  ending or restart. No minimum reading time, retained thinking history or late
  update resurrecting retired activity. Reconnect restores current work only.
- Retain existing model/reasoning policy, provider calls, financial/access rules,
  accepted answers, server timers, citations, voting, clarification/probe flow and
  recovery behavior. Activity is excluded from transcripts and analytics; existing
  content-free operation metrics remain separate.
- Every slice is runnable and includes its own observed end-to-end behavior and
  meaningful checks at the confirmed App/browser and authenticated HTTP/WebSocket
  boundaries. Do not defer essential cleanup/disclosure protection to 05.
- Follow existing language/factual fallback, safe plain-text wrapping, reduced
  motion and non-disruptive status semantics. Keep context details optional for
  missing/older snapshots. Verify Standard and Free where the slice applies.

## Source and verification boundaries

- [Confirmed plan](../../../docs/PANELIST_VISIBILITY_PLAN.md).
- [Selected A prototype and decision](../../../docs/PANELIST_VISIBILITY_PROTOTYPE_REVIEW.md): local branch `prototype/panelist-activity`, comparison `ef445a2`, decision `f98d50d`.
- [User-confirmed test boundaries](../test-boundaries-draft.md): whole-App/browser, authenticated controlled-clock HTTP/WebSocket with external providers mocked, and existing typed Streamlit status checks. Use these existing high boundaries; prototype simulations do not replace production lifecycle tests.
- Record implementation checks as offline/provider-mocked, local browser, hosted or installed-device evidence accurately. No paid inference or remote publication is authorized by this ticket.

## Comments

2026-10-24: Implemented locally in `fa20ec9` and corrected in `4693a30`; reviewed against user-confirmed `13870e2`. Full offline gate: 895 Python tests (providers mocked), 422 React tests and production build pass. Independent Standards and Spec reviews have zero remaining findings. Local synthetic HTTP/WebSocket/browser and responsive evidence is recorded in the [review handoff](../reviews/01.md). Ready for human review; user visual acceptance, hosted and installed-device evidence are not claimed. No push/deployment. Tickets 02 and 03 may be implemented next when requested.

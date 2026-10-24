# 03 — Clarification and probe activity in the current turn

**What to build:** Defenders see the correct activity while a clarification or
probe-related response is prepared or reviewed, then see the resulting reply or
next state with no leftover thinking display. Same-question interactions retain
their current question identity and answer/timer rules.

**Blocked by:** 01 — Live question and answer-review activity.

**Status:** ready-for-human

**Parent:** [Panelist activity specification](../spec.md).

**What it delivers:** The selected activity treatment works throughout a real
same-question exchange rather than only the normal answer-to-question path.

- [x] Clarification, probe generation and probe-reply review use truthful distinct task labels, known reviewer identity and context appropriate to the already-presented discussion.
- [x] Do not expose partial explanations, anticipated questions, suggested answers or provider internal evaluations as highlighted activity.
- [x] Remove activity completely when each explanation/probe/review result is ready, including immediate completion; preserve the existing clarification/probe presentation.
- [x] Reconnect, navigation, retry/backoff, cancellation and retirement show only current work, with unchanged saved submissions, question identity, accepted answers and server deadlines.
- [x] Standard/Free authenticated two-member and whole-App checks cover complete clarification/probe exchanges, safe context, false-acceptance prevention, stale-result cleanup and no additional provider effects.
- [x] Verify compact responsive placement, reduced motion and meaningful polite status updates without losing keyboard focus.

**Primary story coverage:** 11–12, 19–24, 28–32, 33–42, 43–55, 57–68, 70–76, 79.

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

2026-10-24: Implemented locally in `ba7be03`; test-only publication wait correction `1e4b648`. Independent final review against user-confirmed `6ebdafd` reports Standards0 / Spec0. Full offline gate passes901Python tests (providers mocked),431React tests and production build. See the [review handoff](../reviews/03.md) for same-question, recovery, browser/responsive evidence and the interrupted/failed gate history. Ready for human review; no user visual acceptance, hosted/installed-device verification, push or deployment claimed. Ticket04 is now unblocked.

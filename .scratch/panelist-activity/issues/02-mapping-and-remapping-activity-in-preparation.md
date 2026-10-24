# 02 — Mapping and remapping activity in preparation

**What to build:** Hosts and joined defenders see Editor notes within preparation
while mapping or remapping runs, with accepted-upload or already-validated safe
context and existing map progress retained. Activity disappears as soon as the
corresponding map result is ready.

**Blocked by:** 01 — Live question and answer-review activity.

**Status:** ready-for-human

**Parent:** [Panelist activity specification](../spec.md).

**What it delivers:** Preparation has the same usable activity/result behavior
as the live room without automatically starting mapping or inventing map facts.

- [x] Explicit mapping/remapping displays task-appropriate inline activity through the authorized shared preparation state and UI.
- [x] Show source-checking only when actually reported; do not promote provisional topics to validated context or reveal speculative conclusions.
- [x] Unknown context falls back to the factual task/elapsed information; accepted file/source wording remains plain text in its original language.
- [x] Complete removal on ready/fast completion and failure/cancel/restart cleanup preserve existing map review, profile/budget confirmation, Start guidance and explicit-action behavior.
- [x] Reconnect and navigation restore only the active preparation update, without rerunning mapping or restoring obsolete highlights.
- [x] Authenticated host/guest and whole-App/browser checks cover Standard/Free mapping/remapping, safe provisional-versus-validated disclosure, cleanup and readable desktop/phone placement without new provider calls.

**Primary story coverage:** 13–15, 22–24, 28–30, 33–42, 43–51, 57–64, 65–68, 70–76, 79.

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

2026-10-24: Implemented locally in `3846a92`, reviewed against user-confirmed `e170c0c`. All observed criteria pass; independent Standards and Spec reviews report zero findings. Full offline gate: 898 Python tests (providers mocked), 426 React tests and production build pass. See the [review handoff](../reviews/02.md) for authenticated/browser/responsive evidence and its limits. Ready for human review; no user visual acceptance, hosted/installed-device verification, push or deployment claimed. Ticket 03 is next; 04 still waits for 03.

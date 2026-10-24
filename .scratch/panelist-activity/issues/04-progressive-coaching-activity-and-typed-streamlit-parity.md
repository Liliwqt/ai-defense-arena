# 04 — Progressive coaching activity and typed Streamlit parity

**What to build:** Results show accurate overview/section activity while finished
coaching stays available, and the typed Streamlit interface presents equivalent
factual information and cleanup across preparation, live exchanges and coaching.

**Blocked by:** 02 — Mapping and remapping activity in preparation; 03 —
Clarification and probe activity in the current turn.

**Status:** ready-for-human

**Parent:** [Panelist activity specification](../spec.md).

**What it delivers:** All enabled AI waits have the selected activity policy in
the web interface and equivalent native status behavior in typed Streamlit.

- [x] Web Results distinguish genuinely running overview/section/saving work from completed cards, preserving completed coaching and required-report completion semantics.
- [x] Ready sections clear their own activity without hiding still-running work or leaving stale section highlights; failure and failed-only retry preserve ready cards and existing closing/settlement rules.
- [x] Results reconnect/navigation restore only currently active coaching activity, with complete cleanup on completion, failure, cancellation, ending or restart.
- [x] Typed Streamlit uses its native status area for mapping/remapping, question/answer work, clarification/probes and coaching with the same safe context, fallback and current-work cleanup policy.
- [x] Streamlit remains typed and single-browser; neither parity nor display generation changes AI requests, prices, allowances, selected models/reasoning or recovery behavior.
- [x] Whole-App progressive Results, authenticated provider-mocked coaching flows and existing Streamlit AppTest/typed-flow checks verify activity, partial results, ready/failed cleanup and no transcript/analytics archive.
- [x] Confirm readable accessible compact layouts and current interface/source language without extra inference or translation calls.

**Primary story coverage:** 16–18, 22–32, 33–42, 43–60, 61–73, 75–76, 79.

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

2026-10-24: Implemented locally in63a9a54,4564431,349a0fd; independent final
review against user-confirmed3a65962 has Standards0hard/1optional and Spec0remaining.
Full isolated907Python tests (providers mocked),436React/build and observed
App/authenticated/native/browser checks pass. [Review and evidence](../reviews/04.md).
User visual acceptance and hosted/installed-device evidence remain separate.
Ticket05 unblocked, not started. No paid inference, push or deployment.

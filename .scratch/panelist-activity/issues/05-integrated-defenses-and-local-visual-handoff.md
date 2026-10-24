# 05 — Integrated defenses and local visual handoff

**What to build:** A complete local research/mixed defense demonstrates consistent
Editor notes activity across every AI wait and no leftovers when results appear,
with regression evidence, responsive captures and an honest user handoff.

**Blocked by:** 04 — Progressive coaching activity and typed Streamlit parity.

**Status:** ready-for-human

**Parent:** [Panelist activity specification](../spec.md).

**What it delivers:** The implemented feature is reviewable as a whole, with
remaining hosted/installed-device checks distinguished from local evidence.

- [x] Complete mocked two-client Standard/Free research/mixed scenarios covering mapping, openings, normal answers, clarification/probes, retries/reconnect and progressive coaching; members observe the same safe current activity.
- [x] Exercise fast completion, missing/long/plain-text context, retired updates, navigation, failure, cancellation, ending and restart across applicable tasks; no activity/history remains after its result or retirement.
- [x] Run full Python/React suites and production build; preserve accepted-answer, timer, citation, AI-request/model-policy and financial behavior without adding a new provider or database campaign.
- [x] Review the actual local app at desktop, portrait, landscape and enlarged text, including paper/control access, focus/keyboard behavior, meaningful status announcements and reduced motion; capture synthetic screenshots.
- [x] Verify all enabled AI waits, both tiers and matching typed Streamlit behavior, and check that production has no prototype variants, comparison bar, synthetic actions or diagnostic state inspector.
- [x] Show the local implementation preview and record actual user review separately; state hosted, installed-device and real-provider evidence limits without treating prototype checks as production lifecycle proof.
- [x] Complete a final Standards/Spec review of the scoped implementation, map every specification story to delivered behavior/evidence, and preserve unrelated work. No automatic merge of the prototype branch, push or deployment.

**Primary story coverage:** 74–80 and integrated verification of all 1–80.

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

2026-10-24 — Implemented and verified locally from `6eb547c`; see [review 05](../reviews/05.md). Fixed a hanging integrated test (missing `clarification` on the Free probe decision) and a real gap it exposed: manual question retry now sets `operation.retrying`, so the UI says "Trying again…" instead of "Thinking…" (spec story 45). Offline gate: 916 Python (providers mocked, 1 unrelated pre-existing failure in another session's allowance test), 4/4 integrated two-client activity defenses, 19/19 activity suite, 436 React/build. Synthetic Chromium desktop/portrait/landscape/enlarged-text/reduced-motion/keyboard checks pass with no overflow. User visual acceptance, hosted, installed-device and real-provider evidence remain pending. No push/deployment.

2026-10-24 final recheck — User accepted the revised mapping layout. Independent complete-feature review against13870e2: Standards0hard/1optional, Spec0runtime; story mapping corrected. Full scoped915Python/providers mocked,437React/build pass;16focused mapping/presentation checks and rebuild after unreachable-branch cleanup. Wider working tree920Python passes after separate allowance-test correction. No current PostgreSQL rerun or provider readiness claim; see final review. No push/deployment.

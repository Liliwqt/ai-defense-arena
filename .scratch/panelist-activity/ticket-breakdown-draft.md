# Panelist activity — approved implementation breakdown

Status: approved as drafted; separate local tickets published
Created: 2026-10-24
Source: [ready-for-agent specification](spec.md), confirmed Q1–Q11 plan and the
explicit A — Editor notes selection.

The user approved this five-ticket breakdown as drafted on 2026-10-24. Separate
ready-for-agent issues are published in the local tracker; see [ticket index](README.md).
The parent specification remains unchanged. No implementation, commit, push or
deployment is authorized by this approval.

## Approved dependency graph

01 → 02 and 03 independently; 02 + 03 → 04; 04 → 05.

Only 01 can start initially. After 01 is complete, 02 and 03 are both unblocked;
shared presentation edits still require workspace coordination. Ticket 04 joins
those paths to deliver coaching plus complete typed Streamlit parity. Ticket 05
verifies the integrated feature after every task path exists.

No broad prefactor is required. Any small extraction of existing waiting/state
presentation belongs inside 01's complete live-turn slice, keeping the app
runnable. Do not introduce a horizontal schema-only or component-only ticket.

## Common requirements for every ticket

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

## 01 — Live question and answer-review activity

**What to build:** Joined defenders see the selected Editor notes activity during
opening/next-question preparation and answer review, with safe current context
and immediate complete removal when the resulting question or review outcome is
ready. This first slice carries the shared presentation/context policy through
real authorized room state and the web interface.

**Blocked by:** None — can start immediately.

**What it delivers:** The core visible wait/result cycle in real research/mixed
rooms, including retained-versus-accepted answer status and current-only recovery.

- [ ] Opening and subsequent question preparation and answer review expose the factual task, appropriate known reviewer and safe bounded highlighted context; unknown/unsuitable context uses a truthful fallback.
- [ ] Existing authorized snapshots and waiting presentation supply the shared information additively; host/guest members see the same safe update and a room code alone grants no access.
- [ ] Normal and fast completion remove all activity/highlights in the ready rendered state, without a retained collapsed section or animation delay.
- [ ] Failure, admitted retry/backoff, cancellation, ending, restart and stale updates preserve correct current-only display; reconnect/navigation preserve authoritative elapsed origin without replaying history.
- [ ] The compact desktop/phone treatment keeps paper, timer and controls usable, renders source phrases as text, honors reduced motion and avoids stealing focus or announcing every elapsed tick.
- [ ] Retained submissions are not labeled accepted prematurely; accepted answers and existing turn/timer/credit/model rules survive waits and recovery unchanged.
- [ ] Whole-App and authenticated controlled-clock provider-mocked checks cover the visible cycle, safe disclosure, shared/current-only recovery, no added requests and absence of activity content from transcript/analytics.

**Primary story coverage:** 1–10, 19–21, 23–32, 33–42, 43–60, 61–68, 70–73, 75–76, 78–79.

## 02 — Mapping and remapping activity in preparation

**What to build:** Hosts and joined defenders see Editor notes within preparation
while mapping or remapping runs, with accepted-upload or already-validated safe
context and existing map progress retained. Activity disappears as soon as the
corresponding map result is ready.

**Blocked by:** 01 — Live question and answer-review activity.

**What it delivers:** Preparation has the same usable activity/result behavior
as the live room without automatically starting mapping or inventing map facts.

- [ ] Explicit mapping/remapping displays task-appropriate inline activity through the authorized shared preparation state and UI.
- [ ] Show source-checking only when actually reported; do not promote provisional topics to validated context or reveal speculative conclusions.
- [ ] Unknown context falls back to the factual task/elapsed information; accepted file/source wording remains plain text in its original language.
- [ ] Complete removal on ready/fast completion and failure/cancel/restart cleanup preserve existing map review, profile/budget confirmation, Start guidance and explicit-action behavior.
- [ ] Reconnect and navigation restore only the active preparation update, without rerunning mapping or restoring obsolete highlights.
- [ ] Authenticated host/guest and whole-App/browser checks cover Standard/Free mapping/remapping, safe provisional-versus-validated disclosure, cleanup and readable desktop/phone placement without new provider calls.

**Primary story coverage:** 13–15, 22–24, 28–30, 33–42, 43–51, 57–64, 65–68, 70–76, 79.

## 03 — Clarification and probe activity in the current turn

**What to build:** Defenders see the correct activity while a clarification or
probe-related response is prepared or reviewed, then see the resulting reply or
next state with no leftover thinking display. Same-question interactions retain
their current question identity and answer/timer rules.

**Blocked by:** 01 — Live question and answer-review activity.

**What it delivers:** The selected activity treatment works throughout a real
same-question exchange rather than only the normal answer-to-question path.

- [ ] Clarification, probe generation and probe-reply review use truthful distinct task labels, known reviewer identity and context appropriate to the already-presented discussion.
- [ ] Do not expose partial explanations, anticipated questions, suggested answers or provider internal evaluations as highlighted activity.
- [ ] Remove activity completely when each explanation/probe/review result is ready, including immediate completion; preserve the existing clarification/probe presentation.
- [ ] Reconnect, navigation, retry/backoff, cancellation and retirement show only current work, with unchanged saved submissions, question identity, accepted answers and server deadlines.
- [ ] Standard/Free authenticated two-member and whole-App checks cover complete clarification/probe exchanges, safe context, false-acceptance prevention, stale-result cleanup and no additional provider effects.
- [ ] Verify compact responsive placement, reduced motion and meaningful polite status updates without losing keyboard focus.

**Primary story coverage:** 11–12, 19–24, 28–32, 33–42, 43–55, 57–68, 70–76, 79.

## 04 — Progressive coaching activity and typed Streamlit parity

**What to build:** Results show accurate overview/section activity while finished
coaching stays available, and the typed Streamlit interface presents equivalent
factual information and cleanup across preparation, live exchanges and coaching.

**Blocked by:** 02 — Mapping and remapping activity in preparation; 03 —
Clarification and probe activity in the current turn.

**What it delivers:** All enabled AI waits have the selected activity policy in
the web interface and equivalent native status behavior in typed Streamlit.

- [ ] Web Results distinguish genuinely running overview/section/saving work from completed cards, preserving completed coaching and required-report completion semantics.
- [ ] Ready sections clear their own activity without hiding still-running work or leaving stale section highlights; failure and failed-only retry preserve ready cards and existing closing/settlement rules.
- [ ] Results reconnect/navigation restore only currently active coaching activity, with complete cleanup on completion, failure, cancellation, ending or restart.
- [ ] Typed Streamlit uses its native status area for mapping/remapping, question/answer work, clarification/probes and coaching with the same safe context, fallback and current-work cleanup policy.
- [ ] Streamlit remains typed and single-browser; neither parity nor display generation changes AI requests, prices, allowances, selected models/reasoning or recovery behavior.
- [ ] Whole-App progressive Results, authenticated provider-mocked coaching flows and existing Streamlit AppTest/typed-flow checks verify activity, partial results, ready/failed cleanup and no transcript/analytics archive.
- [ ] Confirm readable accessible compact layouts and current interface/source language without extra inference or translation calls.

**Primary story coverage:** 16–18, 22–32, 33–42, 43–60, 61–73, 75–76, 79.

## 05 — Integrated defenses and local visual handoff

**What to build:** A complete local research/mixed defense demonstrates consistent
Editor notes activity across every AI wait and no leftovers when results appear,
with regression evidence, responsive captures and an honest user handoff.

**Blocked by:** 04 — Progressive coaching activity and typed Streamlit parity.

**What it delivers:** The implemented feature is reviewable as a whole, with
remaining hosted/installed-device checks distinguished from local evidence.

- [ ] Complete mocked two-client Standard/Free research/mixed scenarios covering mapping, openings, normal answers, clarification/probes, retries/reconnect and progressive coaching; members observe the same safe current activity.
- [ ] Exercise fast completion, missing/long/plain-text context, retired updates, navigation, failure, cancellation, ending and restart across applicable tasks; no activity/history remains after its result or retirement.
- [ ] Run full Python/React suites and production build; preserve accepted-answer, timer, citation, AI-request/model-policy and financial behavior without adding a new provider or database campaign.
- [ ] Review the actual local app at desktop, portrait, landscape and enlarged text, including paper/control access, focus/keyboard behavior, meaningful status announcements and reduced motion; capture synthetic screenshots.
- [ ] Verify all enabled AI waits, both tiers and matching typed Streamlit behavior, and check that production has no prototype variants, comparison bar, synthetic actions or diagnostic state inspector.
- [ ] Show the local implementation preview and record actual user review separately; state hosted, installed-device and real-provider evidence limits without treating prototype checks as production lifecycle proof.
- [ ] Complete a final Standards/Spec review of the scoped implementation, map every specification story to delivered behavior/evidence, and preserve unrelated work. No automatic merge of the prototype branch, push or deployment.

**Primary story coverage:** 74–80 and integrated verification of all 1–80.

## Approval record

The user explicitly selected “Approve as drafted” for all five tickets and their
blocking edges. Separate local ticket files were then published. Production
implementation and remote publication remain subsequent work.

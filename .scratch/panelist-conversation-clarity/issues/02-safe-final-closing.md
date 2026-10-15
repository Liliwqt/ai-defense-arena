# 02 — Safe final closing before coaching

**What to build:** after coaching succeeds, defenders may see a brief closing
from the last reviewer before the report. Generate both within the existing
coaching request, settle the completed run before the reading interval, and keep
valid coaching available when optional closing text is unusable. Reconnect,
transcript/export and inline Streamlit presentation preserve the same content.

**Blocked by:** 01 — Short questions and specific panelist reactions.

**Status:** ready-for-human

- [x] The existing coaching request may produce optional closing text using the shared conversation guidance, actual final resolved exchange, probe/reply context and current language. No separate feedback request or additional evaluator stage is introduced.
- [x] Reports, existing callers and snapshots without closing data remain compatible through no-closing defaults. Add only compatible report/snapshot/client data required to deliver the feature.
- [x] Closing text is optional and bounded to two sentences/300 characters. Empty, whitespace, invalid-type, oversized or too-many-sentence optional text is omitted without discarding an otherwise valid core coaching report or making another request.
- [x] Core coaching validation remains intact. A wholly unparseable response, invalid report, provider failure or genuine settlement failure retains existing failure/retry/recovery; do not fabricate a report or mark an unsuccessful run complete.
- [x] Derive the speaking reviewer from server-owned final resolved-turn history, never AI-supplied identity or a client claim. Distinguish actual answers from timeouts, missed probe replies and early-ended unanswered questions.
- [x] Empty-history ending retains its factual no-AI summary and skips the closing. Host ending after resolved turns considers those actual turns without inventing an answer to an active unanswered question.
- [x] On successful coaching publication, retain the ready report and finalize the existing durable run outcome exactly once before recording/displaying the closing interval. The presentation delay creates no extra charge, unresolved service outcome or credit return.
- [x] Keep the defense logically complete. Terminal presentation uses the existing 4–12-second length-based reading rule, starts no vote/answer/reply clock, adds no defense turn and changes no budget or coverage assessment.
- [x] While the interval remains, the main room shows the last reviewer as speaking with wording that leads to coaching, not another question or vote. Afterward normal coaching/completion appears; empty/unusable closing proceeds directly to it.
- [x] Snapshots carry server-owned attribution and timing. Reconnect midway resumes the remaining interval; reconnect after expiry and repeated ready updates never replay the full closing or make a new AI call.
- [x] Existing coordinator generation/run fences and lifecycle invalidate obsolete results or presentation work on restart, closure and stale coaching completion. Do not revive an ended run or extend room retention for the closing.
- [x] Transcript and exports preserve a valid final closing separately from question turns and ordinary next-reviewer reactions. Existing report, exact citations, prior answers, coverage gaps and source/transcript controls remain available.
- [x] Streamlit shares generation, optional-field compatibility and attribution, displaying a valid closing inline with its report without emulating multiplayer timing or voting.
- [x] Targeted generation/coaching contract, authenticated fake-clock room, whole-room React and Streamlit checks cover valid/legacy/empty/invalid closing, timeout/early/empty endings, interval boundaries, reconnect, coaching retry and stale results. Existing once-only completion/charging/return regressions remain valid.
- [x] The slice remains runnable and documents compatible interface changes and check evidence. Basic recovery and settlement safety land here; ticket 03 adds complete integrated/live/responsive evidence.

## Context and handoff

Originating specification: **Panelist conversation clarity and final closing**,
confirmed 2026-10-15. Ticket 01 provides the shared dialogue rules this closing
uses. Financial policy distinguishes successful coaching from a failed service
eligible for existing recovery; a presentation delay cannot change that outcome.

Preserve all game/account/citation/language/private-chat boundaries and unrelated
local work. Keep feature/question-first-room local and main/live unchanged;
remote publication is separately requested. Ticket 03 completes checkpoint 2's
integrated review, while this ticket delivers its runnable end-to-end behavior.

## Comments

2026-10-15: User approved this complete generation-to-display slice, including
safe fallback, reconnect, transcript and settlement behavior.

2026-10-15: Implemented locally after bdc81ea, retaining approved feature-review
baseline 9314379. Seven new Python tests cover optional-field/core compatibility,
terminal timing, settlement/restart, Streamlit and authenticated two-client host
ending/reconnect. Whole-App/export regressions cover closing presentation and the
final-answer presenter overlap fix. Full gates: 550 working-tree/542 selected
Python tests (AI/Google/PayMongo mocked), 278 React tests and production build.
Independent Standards/Spec review and addendum have zero findings. Synthetic
desktop/portrait/landscape keyboard checks and four screenshots are in the shared
clarity review record; preview port 8847 has no provider/account backend. Ticket
03's broader integrated/live review and user visual/native-language approval
remain pending. Local commit only; no push/deploy, main/live service unchanged.

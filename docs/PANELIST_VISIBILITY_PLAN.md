# Panelist visibility plan

Status: confirmed plan, 2026-10-24. User approved the consolidated Q11 scope after confirming Q1–Q10. Planning complete; prototype, implementation and publication remain separate subsequent actions.

## Requested outcome

The user wants an editor-style thinking display during AI work, open by default with meaningful words highlighted while waiting. It shows factual activity and brief summaries, and disappears completely when each task's result is ready. The visual reference is the thinking display in their VS Code coding assistant.

## Confirmed decisions

- Q1: open by default beneath the active panelist, with highlights visible without clicking.
- Q2, user correction: when the question appears, remove the entire thinking/activity display, its highlights and any collapsed section. Do not retain a thinking history in the question view or delay a ready question just to finish an animation. This supersedes the earlier recommendation to retain expandable activity after completion.
- Q3: cover all AI waits, including mapping/remapping, questions, answer review, clarification/probe replies and coaching. Use the correct task label and reviewer attribution where known. The display disappears when each result is ready.
- Q4: show factual activity and brief source-grounded summaries that do not disclose upcoming questions or suggested answers. Do not relay provider internal reasoning; readable reasoning support is no longer a prerequisite for this feature. Keep existing no-fictional-thinking constraints.
- Q5: build updates from the actual task and already-validated context, highlighting a few useful words. No extra AI request. Change content only when real information changes, not through a timer-driven sequence of invented thoughts.
- Q6: inline block below the active reviewer in the question area and inside the relevant mapping/coaching area for those tasks. Compact readable phone layout; gentle dots or pulse with reduced-motion support. Preserve usable controls and paper/question visibility.
- Q7: joined room members see the same safe activity; reconnect restores only the current update. Keep activity temporary and exclude it from transcripts and analytics. Clear it on completion, failure, cancellation or restart; failures show existing recovery messages instead of stale thinking.
- Q8: status wording follows the existing interface language; topic/citation phrases retain original wording. Without useful context or a new stage, retain the factual current label and elapsed time. No invented sentences, translation request or fake percentage.
- Q9: Standard and Free share the display in React web and existing Android/iOS WebViews. Typed Streamlit uses its native status area with matching information. Preserve models, reasoning, prices, timers, answer acceptance and recovery rules.
- Q10: review a local visual prototype first. Later implementation requires full Python/React suites and build, mocked two-client waits, fast completion without leftover activity, reconnect/retry/cancel/restart, partial coaching and desktop/portrait/landscape accessibility. Hosted behavior and installed-device verification are separate evidence. No paid AI call is necessary to validate this presentation.
- Q11: user confirmed the complete scope and explicitly selected “Matches—finish planning.” This concludes the interview, without starting the prototype/implementation or authorizing publication.

## Consolidated presentation

Show the work currently underway as a short factual sentence, reviewer identity when known, and a few highlighted phrases from context already validated and appropriate to reveal. The highlights are visible immediately; no expansion click is required. They do not certify correctness, hint at an expected answer, or reveal a pending question or internal evaluation.

For example, during review of an already-presented sampling question, the display could show **Reviewing your answer…** with Methodology Reviewer and **Sampling**. This illustrates the presentation; it is not a scripted thought to emit for every operation. If no suitable context exists, use the current task label alone. Meaningful text changes only when authoritative task/context information changes; dots or a subtle pulse can continue while waiting.

| Work | Activity location and factual content |
| --- | --- |
| Mapping/remapping | Preparation review area; current mapping stage and suitable already-validated context |
| Question planning/writing | Question area beneath the active reviewer where known; factual generation stage without pending question content |
| Answer/probe-reply review | Question area; current reviewer and appropriate context from the existing question, with the current saved/retained-answer status preserved |
| Clarification/probe generation | Relevant question area; current task/reviewer, without unvalidated reply text |
| Coaching | Relevant Results/status area; current overview/section work, keeping finished coaching visible |

Keep the paper, question, timers and controls usable. On phones, use a compact inline treatment. Honor reduced motion and make status updates accessible without repeatedly announcing the elapsed timer or decorative animation.

## Lifecycle and disclosure

- Bind displayed activity to the actual current operation and room/run/turn lifecycle. Do not allow a late update from failed, cancelled or retired work to resurrect a cleared display.
- Show the same safe update to authorized joined room members. Restore only the current still-active update on reconnect, not a replay/history of thoughts.
- Remove activity and highlights as soon as their result is ready, including fast completion. Do not hold a question back to finish a reading interval, animation or typewriter effect. Leave no collapsed thinking section in the completed question view.
- During progressive coaching, completed sections stay visible while any still-running coaching work uses its own truthful activity status; readiness of one section is not completion of the full report.
- On failure, cancellation, ending or restart, clear obsolete activity and use existing recovery/status guidance. An admitted retry reflects its actual retry state, not a fabricated thinking sequence.
- Keep activity ephemeral. Do not put activity text/context/highlights in transcripts, analytics or a new persistent thought archive. Existing content-free operation metrics are separate and unchanged.
- Do not forward provider reasoning, encrypted blocks, partial structured output, private prompts or unvalidated drafts. No new AI summarizer, inference request or translation request is required; no model/effort change is needed.

## Verification and delivery

1. After planning confirmation, the next workflow is a local visual prototype using synthetic safe context. Review the activity view, highlighted phrases, compact mobile version and disappearance on fast/normal completion. This plan does not itself authorize building that prototype.
2. Subsequent implementation extends the existing factual waiting presentation and authoritative operation information, preserving accepted answers, server timers, financial effects, fixed run settings, citations and recovery rules.
3. Run the repository Python/React suites and production build with external AI/payment/auth providers mocked. Include two-client mapping/question/review/clarification/probe/coaching waits, shared safe context, reconnect and stale-result suppression, retry/failure/cancel/restart, fast completion, partial coaching, and no activity retained in transcripts/analytics.
4. Review desktop, portrait and landscape layouts, keyboard/screen-reader status behavior and reduced motion. Verify matching typed Streamlit information. Preview and screenshots are local evidence; user visual approval must be recorded separately.
5. Report hosted and installed Android/iOS behavior separately. This feature does not depend on readable provider reasoning or require a paid campaign, and does not close unrelated model quality, latency or capacity gates.

## Existing facts

- `backend/openrouter_stream.py` requests streamed structured output but forwards only `delta.content`; it does not surface reasoning events to room clients.
- `game/src/components/WaitingIndicator.tsx` shows factual labels, animated dots and server-anchored elapsed/retry timing. `game/src/lib/roomPresentation.ts` derives labels from actual operation state.
- The responsiveness plan excludes exposing internal reasoning and fictional thinking. The confirmed activity/brief-summary direction preserves that constraint.
- A reasoning-effort setting alone does not guarantee readable reasoning is returned. OpenRouter documents model/provider differences and distinct reasoning detail forms. Selected-route support is unverified.
- Mapping currently explicitly excludes reasoning from its returned response. Question generation consumes content chunks on the server before publishing a validated result; neither path currently provides a thinking feed to defenders.
- Public documentation permits readable text and summaries as well as encrypted/redacted blocks. The latter cannot supply a readable display. Keepalives are not meaningful reasoning updates.
- Pre-validation provider text could disclose a future question, suggested answer, rejected draft or coaching judgment. Highlighting keywords alone does not establish that the material is appropriate to show during a timed defense; the confirmed source boundary excludes raw reasoning and uses already-validated context.

## Interview progress

Q1–Q11 are confirmed. The interview is complete; no product decision remains open in this plan.

## Next workflow

The user selected **A — Editor notes** from the local prototype on `prototype/panelist-activity` (source `ef445a2`). See [prototype review, decision and preview](PANELIST_VISIBILITY_PROTOTYPE_REVIEW.md). Carry A's compact task line, vertical gutter and highlighted context into the subsequent specification and implementation workflow, preserving all confirmed lifecycle/disclosure rules. No runtime implementation or remote publication was performed during planning or prototype selection.

The [implementation specification](../.scratch/panelist-activity/spec.md) is published to the local Markdown tracker as ready-for-agent after the user confirmed its test boundaries on 2026-10-24. Next: dependency-aware tickets; no production implementation or remote publication is authorized by specification preparation.

## Evidence

- [OpenRouter reasoning documentation](https://openrouter.ai/docs/guides/best-practices/reasoning-tokens), checked 2026-10-24: return availability varies, and reasoning details may contain summaries, readable text or encrypted blocks. This is documentation evidence, not a successful live call on the app's selected routes.

Decisions are recorded as the interview progresses. CONTEXT.md remains the canonical domain vocabulary; no new ADR is warranted yet.

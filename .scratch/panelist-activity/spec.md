# Panelist activity with Editor notes

Status: ready-for-agent
Created: 2026-10-24
Planning: Q1–Q11 confirmed; prototype A — Editor notes selected explicitly.
Test boundaries: confirmed by the user on 2026-10-24.
Publication: local Markdown tracker only; production implementation has not started.

## Problem Statement

While a paper is mapped, an answer is reviewed or a new question is prepared,
defenders want to see useful signs of the panelist's activity. Generic waiting
labels alone provide little context, and fast-changing text can be difficult to
read. The user wants an editor-style display with visible highlighted phrases,
similar to the activity display in their VS Code coding assistant.

The user explicitly requires the entire activity display to disappear when the
question appears. Retaining an expandable thinking history, slowing down a ready
question to finish an animation, or leaving an empty thinking section would
violate that requirement.

The product must describe actual work without inventing thoughts or suggesting
that it exposes a panelist's private reasoning. Provider reasoning availability
varies, and raw or unvalidated provider text could reveal a pending question,
suggested answer, rejected draft or internal evaluation. A useful waiting display
must therefore work from factual task state and already-validated safe context.

## Solution

Use the selected **A — Editor notes** design: an open inline activity block with
a compact task line, a vertical editor-style gutter, subtle animated dots or a
pulse, elapsed time where available, and a few highlighted contextual words.
Meaningful text changes only when actual task or validated contextual information
changes. There is no timed sequence of imagined thoughts and no extra AI call.

Show it during all relevant Standard and Free AI waits: mapping/remapping,
opening and subsequent question preparation, answer review, clarification,
probe-related work and coaching. Place it beneath the active reviewer in the
question area, or within the relevant preparation/Results area. Use a compact
mobile presentation that leaves paper reading, timers and controls usable.
Typed Streamlit shows matching factual information in its native status area.

All authorized joined room members see the same safe current activity. Reconnect
restores only activity that is still current. Remove the block, its highlights
and any collapsed/history affordance as soon as the corresponding result is
ready, including very fast completion. Clear retired activity on failure,
cancellation, ending or restart, preserving existing results and recovery
guidance. Activity is temporary and excluded from transcripts and analytics.

When no suitable contextual detail exists, show only the factual task label and
available elapsed time. Preserve the existing interface language; keep source
phrases in their original wording. Models, reasoning settings, provider calls,
game rules, financial effects, privacy and source validation remain unchanged.

## User Stories

1. As a defender, I want the activity block open automatically during AI work, so that I can see useful information without an extra click.
2. As a defender, I want the selected Editor notes layout, so that the display resembles the compact editor-style reference I approved.
3. As a defender, I want a short factual task line, so that I understand what is currently happening.
4. As a defender, I want a few useful contextual words highlighted, so that I can quickly identify what the displayed activity relates to.
5. As a defender, I want the vertical gutter to group task and context, so that the activity reads as one coherent block.
6. As a defender, I want the known active reviewer identified correctly, so that I can see whose work is being described.
7. As a defender, I want neutral task attribution when the reviewer is not known, so that the interface does not invent a speaker.
8. As a defender, I want activity during opening-question preparation, so that the first wait is understandable even without an earlier question.
9. As a defender, I want activity while the next question is prepared, so that an accepted answer is followed by clear waiting feedback.
10. As a defender, I want answer-review activity distinct from question preparation, so that I understand which stage is underway.
11. As a defender, I want clarification activity to describe clarification, so that I do not mistake it for a new question.
12. As a defender, I want probe generation and probe-reply review identified truthfully, so that same-question exchanges remain clear.
13. As a host, I want activity during paper mapping, so that preparation does not look stalled.
14. As a host, I want activity during remapping, so that profile corrections have clear feedback while they are processed.
15. As a host, I want source-checking activity only when that stage is actually reported, so that the interface does not fabricate a process sequence.
16. As a defender, I want overview and per-answer coaching work identified accurately, so that I can understand progressive Results.
17. As a defender, I want finished coaching sections to stay visible while other sections are prepared, so that waiting does not hide useful completed work.
18. As a defender, I want activity for a finished section removed while genuinely pending work remains distinguishable, so that partial progress is not misrepresented as full completion.
19. As a defender, I want the entire activity block removed when the question appears, so that the question has my full attention.
20. As a defender, I want highlights and collapsed thinking affordances removed with the block, so that no thinking history remains in the question view.
21. As a defender, I want fast results displayed immediately, so that the app does not delay me to finish a reading interval or animation.
22. As a defender, I want each non-question task's activity removed when its result is ready, so that preparation and Results follow the same clear behavior.
23. As a defender, I want meaningful updates only when real information changes, so that the display does not simulate imaginary progress.
24. As a defender, I want gentle motion during quiet waits, so that I can see work is still active without a fabricated narrative.
25. As a defender, I want a factual fallback when no useful context exists, so that the display remains honest for every model and task.
26. As a defender, I want real elapsed time where a reliable start time exists, so that waiting duration is understandable.
27. As a defender, I want no invented elapsed time or percentage, so that unavailable progress information is not disguised as a measurement.
28. As a defender, I want contextual phrases drawn from already-validated material appropriate to reveal, so that highlighted information is grounded.
29. As a defender, I want no preview of an upcoming question, so that the activity display does not give away the next challenge.
30. As a defender, I want no suggested answer or hidden coaching judgment during a wait, so that practice remains a fair defense exercise.
31. As a defender, I want activity distinguished from private reasoning, so that I understand what the display actually represents.
32. As a defender, I want activity to work even when my selected model returns no readable reasoning, so that provider differences do not leave the interface broken.
33. As a defender, I want existing interface-language wording, so that activity remains consistent with surrounding navigation.
34. As a defender, I want topic and citation phrases kept in their original language, so that source context is not silently mistranslated.
35. As a defender, I want long or unusual source wording rendered readably as text, so that highlights do not break the layout or execute source markup.
36. As a defender, I want private team chat excluded from activity context, so that the team's separate conversation stays separate.
37. As a host, I want my joined teammates to see the same safe current activity, so that everyone understands the shared room state.
38. As a guest defender, I want activity through my existing room membership, so that no host account is required merely to see the shared update.
39. As a room owner, I want existing membership checks preserved, so that knowing a room code alone does not expose activity or paper context.
40. As a defender, I want reconnect to restore only the still-running update, so that I can resume without replaying obsolete thoughts.
41. As a defender, I want activity elapsed time to retain its authoritative origin after reconnect, so that a refreshed connection does not restart the apparent wait.
42. As a defender, I want navigation back to the room to show only current work, so that leaving a screen does not preserve stale activity.
43. As a defender, I want activity cleared when work fails, so that a stopped task is not shown as still thinking.
44. As a defender, I want existing recovery guidance after a failure, so that I know which saved work can be retried.
45. As a defender, I want an admitted retry described as a retry, so that repeated provider work is not hidden behind misleading wording.
46. As a defender, I want provider-directed retry waiting described factually, so that backoff is not presented as active model reasoning.
47. As a defender, I want cancellation to clear the old activity, so that a cancelled response cannot remain on screen.
48. As a host, I want ending a run to retire its activity, so that no pending update appears after the run has ended.
49. As a host, I want restarting a run to clear prior activity and highlights, so that the new run starts cleanly.
50. As a defender, I want late updates from retired work ignored, so that cancelled or completed activity cannot reappear.
51. As a defender, I want activity isolated to the correct room and run, so that another operation's context is never displayed as mine.
52. As a defender, I want retained submissions distinguished from accepted answers, so that waiting feedback does not overstate what the server has accepted.
53. As a defender, I want accepted answers preserved through waiting and recovery, so that I am not asked to submit the same answer again.
54. As a defender, I want server timer behavior unchanged, so that opening activity does not pause or reset a turn.
55. As a defender, I want voting, clarification and probe rules unchanged, so that this display does not alter how I participate.
56. As a host, I want models and reasoning settings unchanged, so that the display works with the run policy already selected.
57. As a host, I want no extra provider request for activity summaries, so that a presentation improvement does not add AI cost.
58. As a host, I want existing spending and credit rules unchanged, so that activity updates cannot create charges, reservations or refunds.
59. As a Free-practice defender, I want the same factual display, so that safe waiting feedback is not limited to Standard practice.
60. As a Standard-practice defender, I want role-specific work represented consistently, so that multiple reviewer models do not produce inconsistent waiting behavior.
61. As a desktop defender, I want the activity beside the relevant work and paper, so that I can keep reading while waiting.
62. As a phone defender, I want a compact readable block, so that highlights do not crowd out the question, timer or controls.
63. As a landscape-phone defender, I want activity to fit without horizontal overflow, so that a short screen remains usable.
64. As a defender using larger text, I want highlighted phrases to wrap safely, so that context remains readable without clipping important controls.
65. As a keyboard user, I want activity to appear without stealing focus, so that my current interaction is not interrupted.
66. As a screen-reader user, I want meaningful status changes announced politely, so that I can understand new work without being interrupted every elapsed second.
67. As a reduced-motion user, I want a static equivalent of the activity display, so that decorative movement is unnecessary for understanding it.
68. As a defender in an existing Android or iOS WebView, I want the shared web presentation, so that this feature does not require a new speech capability.
69. As a typed Streamlit user, I want matching factual task information and cleanup in its native status area, so that the fallback remains understandable.
70. As a defender reviewing a transcript, I want the actual defense discussion without a thinking archive, so that temporary activity does not become part of my answer record.
71. As a defender, I want activity text and contextual highlights excluded from analytics, so that a transient display does not create a new private-content record.
72. As an operator, I want existing content-free timing metrics left separate, so that presentation changes do not corrupt performance measurements.
73. As a reviewer, I want additive compatibility for activity information and honest fallback when detail is missing, so that incomplete or older snapshots do not break the room display.
74. As a reviewer, I want real authenticated host/guest scenarios with mocked providers, so that shared activity and lifecycle behavior are verified beyond the visual prototype.
75. As a reviewer, I want fast-completion and stale-update checks, so that complete disappearance is proven at the real application boundary.
76. As a reviewer, I want tests that observe output and effects rather than helper implementation, so that refactoring does not invalidate otherwise correct behavior.
77. As a reviewer, I want local browser evidence separated from hosted and installed-device evidence, so that readiness claims remain accurate.
78. As a maintainer, I want the selected prototype retained on its separate branch, so that the visual decision is traceable without shipping demo controls.
79. As a maintainer, I want production implementation to reuse existing room and waiting boundaries, so that the feature does not introduce a second reasoning or progress subsystem.
80. As a project owner, I want specification, implementation and publication treated as separate steps, so that preparing this feature does not automatically deploy it.

## Implementation Decisions

- **Selected visual design:** implement Editor notes with its compact factual
  task statement, vertical gutter and visible highlighted current context. The
  display is open by default. Other prototype variants, synthetic controls,
  comparison bars and diagnostic state inspectors are not production features.
- **One existing presentation flow:** extend the shared waiting presentation and
  operation information used by room, preparation and coaching views. Reuse the
  existing authenticated room publication and snapshot boundary rather than
  creating a provider-reasoning relay, new polling service or progress endpoint.
- **Authoritative source:** derive activity from real operation kind/stage,
  validated room/run/turn context and known reviewer identity. The server remains
  responsible for which operation/context is current and appropriate for shared
  disclosure; the client does not guess progress from elapsed time or received
  token volume.
- **Safe context contract:** activity context is a small, bounded presentation of
  already-validated information that is appropriate to expose at that moment.
  Suitable examples include the already-presented discussion topic, accepted
  upload identity and completed validated mapping information already available
  to room members. Validation alone does not permit disclosure of pending
  questions, prospective topic selection, internal evaluation or suggested
  answers. If suitability is uncertain, omit context and use the task label.
- **Plain-text emphasis:** use known semantic fields for highlighted phrases,
  not a generative summarizer or keywords extracted from raw reasoning. Preserve
  original wording and render source content as text; do not interpret it as
  markup. Keep the number/size of displayed details bounded and allow readable
  wrapping without making the activity a second paper viewer.
- **Existing operation scope:** current activity belongs to the existing room,
  defense preparation/run, turn where relevant and logical operation lifetime.
  Enrich existing authorized snapshots only as needed; any extra presentation
  fields must be additive and optional. Older/missing-detail snapshots retain
  factual fallback behavior. No client command can choose or publish shared
  activity content.
- **Task coverage:** cover mapping/remapping, opening and next-question work,
  answer interpretation, clarification, probe-related work, and coaching overview
  and answer-section work wherever these operations occur in the enabled
  research/mixed interfaces. This does not enable disabled code-only or voice
  functionality. Pure account/payment waits are outside this AI display scope.
- **State-driven text:** labels change on actual stage/context transitions only.
  Decorative dots or pulse may animate while waiting; labels do not rotate
  through scripted thoughts. Retry backoff and retry execution remain distinct.
  Missing context is not an error and does not trigger a new provider request.
- **Readiness and removal:** the corresponding authoritative completed result
  replaces activity immediately in the same rendered state. Remove the entire
  activity subtree and highlights, with no collapsed remainder, archived history,
  minimum reading period, typewriter completion or delayed hide animation. A
  result may complete too quickly for a user to read the activity; that is valid.
- **Failure and invalidation:** failed or retired operations expose existing
  error/recovery guidance rather than active thinking. Clear activity on
  cancellation, ending and restart. Existing ordered publication and retirement
  rules must prevent late results or contextual updates from resurrecting it.
  Actual newly admitted work may display its own current activity.
- **Reconnect and navigation:** room members restore the current authorized
  operation snapshot, not historical activity events. Use existing server time
  anchoring for available elapsed/retry information. Navigation does not start
  AI work, reset elapsed time, pause a timer, submit an answer or replay history.
- **Progressive Results:** keep completed coaching visible while remaining
  sections run. Activity reflects current genuinely running work; a finished
  card clears its own pending display but does not falsely complete the report.
  On unresolved failure, preserve ready cards and existing failed-only recovery.
  Do not replay a closing reaction or change settlement for this display.
- **Temporary content:** activity text, context and highlights remain ephemeral
  and are not written into defense transcripts, exports, persistent storage or
  analytics. Leave existing content-free operation timing/usage records intact
  and exclude newly displayed contextual content from those records.
- **Access and separation:** use existing host/guest room membership; a room code
  alone does not grant activity access. Do not source activity from private team
  chat, credentials, hidden prompts, provider reasoning, encrypted blocks, partial
  structured output or rejected/unvalidated response drafts.
- **Responsive placement:** put activity below the known active reviewer in the
  question area, in preparation for mapping, and beside relevant coaching work
  in Results. Preserve current paper browsing, room controls, answer dock, timers
  and existing navigation. This is an inline enhancement, not another fullscreen
  layout or a permanent overlay.
- **Accessibility:** use semantic polite status announcements for meaningful
  changes, keep decorative motion and elapsed ticks out of repeated
  announcements, and avoid stealing focus. Respect reduced-motion preferences
  without removing useful content. Keep text/highlight contrast and wrapping
  readable in desktop, portrait, landscape and enlarged-text layouts.
- **Language and fallback:** keep task wording consistent with existing interface
  language and source phrases in original wording. No translation request or
  new language-selection feature is introduced. A generic truthful task label
  with available elapsed time is the correct quiet/unknown-context fallback.
- **Interface parity:** Standard and Free share the web presentation and existing
  Android/iOS WebViews. Typed Streamlit reuses equivalent factual status/context
  policy in its native single-browser status interface without reproducing the
  web component tree or introducing multiplayer into that fallback.
- **Preserved defense policy:** do not change model IDs, reasoning effort or
  budgets, routing, prompts, provider call count, spending ceilings, protected
  coaching funds, credit/voucher/Free access, source/citation validation,
  acceptance rules, server timers, voting or recovery behavior. Do not introduce
  artificial waiting or claim faster model inference from this UI work.
- **Delivery:** treat the selected prototype as visual evidence and implement
  production behavior against real operation state. Deliver a runnable local
  preview with the agreed verification before any separately authorized remote
  publication. This specification does not authorize merging prototype code,
  starting paid experiments or pushing/deploying.

## Testing Decisions

- **Confirmed boundaries:** the user confirmed whole-App React/browser checks,
  existing authenticated FastAPI HTTP/WebSocket room flows with controlled
  clocks and external providers mocked, and existing typed Streamlit status
  checks. Full Python/React suites and production build remain the regression
  gate. Hosted and installed Android/iOS checks are separate evidence.
- **Good tests observe behavior:** assert displayed factual labels/context,
  highlighted meaning, removal, authorized shared snapshots, correct retained
  answers and absence of new external effects. Do not lock down incidental CSS
  class names, a particular component decomposition, private helper calls,
  exact decorative timing or the synthetic prototype reducer.
- **Whole-App prior art:** use the established room-stage/navigation,
  preparation, waiting/status and progressive-coaching scenarios. Drive changes
  through external room snapshots and user navigation, and check the actual
  question/preparation/Results display rather than only isolated markup.
- **Room-flow prior art:** use existing authenticated host/guest creation,
  WebSocket membership, question recovery, operation publication and progressive
  coaching tests. Exercise two members observing the same safe current context,
  valid reconnect, rejected unauthorized access and existing server timer rules.
  Focused operation tests may cover otherwise hard-to-reach lifecycle edges;
  they supplement rather than replace high-level flows.
- **Lifecycle matrix:** cover mapping/remapping, opening and subsequent question
  work, interpretation, clarification, probes and coaching. Include immediate
  completion, ordinary completion, stage transitions, missing context, unchanged
  quiet state, transient retry, directed backoff, failure, cancellation, ending,
  restart, stale updates, reconnect and navigation away/back. Completed tasks
  must contain no activity/history affordance or leftover activity highlight.
- **Disclosure and effects:** include context that is valid but inappropriate
  for pre-question disclosure, raw reasoning/draft content, private chat and
  markup-like/long source text. Check safe omission/plain-text behavior through
  exposed snapshots and UI. Verify no added AI/translation calls, no activity in
  transcript/export/analytics and no change to model/run policy, answers,
  financial effects or provider-facing request parameters.
- **Progressive coaching:** show ready cards while remaining work runs; clear
  the relevant activity when it finishes; retain completed cards through failure
  and failed-only retry; keep existing closing and completion behavior. Do not
  confuse a completed section with a completed required report.
- **Browser review:** exercise the actual local app with synthetic sources and
  mocked providers on desktop, portrait and landscape. Check readability,
  horizontal overflow, paper/timer/control access, focus, keyboard operation,
  meaningful polite announcements and reduced motion. Include very fast
  completion without artificially stretching its display.
- **Fallback prior art:** use existing Streamlit AppTest and typed research/mixed
  defense checks to observe equivalent factual status/context and cleanup,
  including retries and partial reports. Preserve its typed single-browser
  interface and existing AI/spending policy.
- **Evidence limits:** prototype screenshots and simulated recovery are design
  evidence only. Local mocked two-client tests do not prove hosted transport or
  installed-device behavior; DOM semantics alone are not a comprehensive
  assistive-technology audit. Report the evidence actually obtained. No paid
  model call, new database concurrency campaign or provider reasoning-support
  experiment is required for this presentation feature.

## Out of Scope

- Exposing or reconstructing private chain-of-thought, provider reasoning,
  encrypted thinking, hidden prompts or raw unvalidated token streams.
- AI-generated activity summaries, extra inference/translation requests,
  provider/model replacement, reasoning tuning or new latency guarantees.
- A retained or expandable thought archive after results, persistent activity
  history, transcript additions, analytics of activity text or a new database.
- Invented thoughts, scripted progress sequences, fake percentages or minimum
  reading/typewriter intervals that delay a ready result.
- A broad redesign of navigation, the defense room, PDF reading, coaching or
  the current visual identity beyond the selected inline activity treatment.
- Changing answer/probe/clarification rules, voting, timers, prompts, citations,
  question budgets, payment/credit/spending/access rules or settlement.
- Enabling code-only defense, live voice, new native microphone permissions,
  new translations or multiplayer support in typed Streamlit.
- Shipping prototype variants, comparison controls, synthetic state inspectors
  or mock lifecycle actions into production.
- Paid provider experiments, proof of model quality/speed, hosted rollout,
  automatic merging, pushing or deployment.

## Further Notes

- Product source: [confirmed Q1–Q11 plan](../../docs/PANELIST_VISIBILITY_PLAN.md).
- Visual decision: [prototype review and selection](../../docs/PANELIST_VISIBILITY_PROTOTYPE_REVIEW.md).
- Primary prototype source is local branch `prototype/panelist-activity`,
  comparison commit `ef445a249750d177b90074660887ee3e82b6588a`; explicit selection
  is captured at `f98d50d7f3692c3f0e64c523a39c35f7c349ffd9`. Keep this pointer in
  subsequent implementation tickets; the simulation is not production code.
- [Confirmed test-boundary sketch](test-boundaries-draft.md) records the external
  seams. No new product interview was needed to produce this specification.
- [Domain vocabulary](../../CONTEXT.md) defines Panelist activity, Defender,
  Defense run, Clarification, Answer probe and Panelist reaction. Activity is
  neither a reaction nor an accepted answer or coaching judgment.
- [Combined-turn ADR](../../docs/adr/0008-combined-validated-turn-planning.md) and
  the [responsiveness plan](../../docs/DEFENSE_TURN_RESPONSIVENESS_PLAN.md) retain
  their validated state transitions and no-fictional-thinking boundaries.
  This specification extends their factual waiting presentation without
  changing the generation pipeline or resolving separate provider quality gates.
- The user originally referred to thinking visibility, then explicitly selected
  activity/brief summaries from validated context with no extra AI call. The
  latter is the settled requirement; readable provider reasoning is not a gate.
- Scope is ready for the subsequent dependency-aware ticket breakdown. Creating
  this specification does not start production implementation or authorize
  publication beyond the local Markdown tracker.

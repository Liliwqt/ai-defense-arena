# Responsive defense turns and animated AI waiting feedback

Status: ready-for-agent
Created: 2026-10-21
Planning: Q1–Q11 confirmed, followed by the explicit animated-waiting amendment.
Test boundaries: confirmed by the user on 2026-10-21.
Publication: local Markdown tracker only; implementation has not started.

## Problem Statement

After preparing a research map and starting a defense, defenders experience long
waits between answers and questions, provider failures, and recovery controls
that can make them think they must submit their answer repeatedly. The user
reported this after successfully starting an eight-question Standard defense;
the previous Luna workflow felt smoother.

The current normal transition can require three serial AI requests: interpret
the submission, plan the next reviewer/topic, and generate the next question.
Requests repeatedly send extensive accepted-source and conversation context.
Mapping produces a research profile, topics and grounded references; it does not
give different provider models permanent shared memory or prepare every question.
Recent read-only provider records established four DeepSeek/Relace HTTP 429
failures, but not their precise quota reason or correspondence to every room
failure. Longer timeouts alone do not make the interaction responsive.

Waiting presentation also needs improvement. Users need visible, restrained
animation and useful words while AI work is actually running, across mapping,
questions, submission review, clarification, probes, coaching and recovery.
They must be able to distinguish a retained submission from an accepted answer,
active generation from a retry delay, and partial coaching from completion.

## Solution

Optimize Standard research and mixed defenses first, keeping distinct reviewer
roles in React and the typed Streamlit fallback. Combine interpretation and
adaptive next-turn planning in the outgoing reviewer's request, then let the
selected next reviewer produce grounded dialogue. The normal accepted-answer
transition uses two AI requests rather than three. Opening and unanswered
transitions retain a separate planner; exceptional broader lookup and recovery
remain bounded rather than being hidden in a two-call claim.

Use focused, reusable evidence assembled from the confirmed research map,
study-wide context, exact relevant passages, neighboring text and necessary
conversation history. Keep the whole accepted source available for bounded
broader lookup. Preserve grounded citations, adaptive coverage and each
reviewer's specialty; select interactive reasoning limits and any replacement
models through comparable quality and latency measurements.

Keep validated work when a later stage fails, retry only the failed stage, and
retain answers without another defense charge. Permit one bounded automatic
retry for eligible transient failure, with restricted provider-directed 429
handling. Provide clear manual recovery when automatic work is inappropriate.

Show animated dots or a subtle pulse beside factual operation labels, such as
Thinking… Preparing your question…, Evaluating your answer…, Mapping your
paper… and Preparing your coaching…. Show truthful elapsed time and accepted
answer status; respect reduced motion and screen readers. Apply shared waiting
and answer-recovery improvements to Free without claiming its model capacity is
fixed or automatically migrating it to Standard's optimized model pipeline.

Aim for most successful answer-to-next-question transitions within 10–15 seconds,
with a 45-second total interactive processing window including automatic retry
and broader lookup. Exclude intentional reaction-reading and voting intervals.
These are acceptance targets to measure, not current performance claims. Deliver
two runnable local checkpoints and require separate real-provider evidence
before describing the optimized route as live-ready.

## User Stories

1. As a host, I want Standard research-paper defenses to continue promptly after an answer, so that practice feels conversational.
2. As a host, I want the same improvements in mixed research/code defenses, so that research involving software remains supported.
3. As a host, I want the typed Streamlit fallback to use the same Standard AI policy, so that changing interfaces does not change the defense rules.
4. As a Free-practice host, I want shared answer-retention and recovery improvements, so that a provider shortage does not require retyping my answer.
5. As a Free-practice host, I want honest capacity messages, so that animations do not imply free providers are always available.
6. As a defender, I want the four reviewer specialties preserved, so that faster responses still examine different research perspectives.
7. As a defender, I want the responding reviewer to interpret my answer and propose the next eligible step together, so that an unnecessary serial request is removed.
8. As a defender, I want the selected next reviewer to write its own question and reaction, so that reviewer-specific dialogue is preserved.
9. As a defender, I want brief reactions to remain grounded in my actual answer, so that faster generation does not introduce generic praise or imagined gaps.
10. As a defender, I want a clarification request explained within the current question, so that it is not mistaken for an accepted answer.
11. As a defender, I want one material gap handled as a same-question answer probe, so that the panel can request detail without advancing the question number.
12. As a defender, I want my original answer and probe reply considered together with correct speakers, so that coverage reflects the whole exchange.
13. As a defender, I want a sufficient explanation accepted, so that the panel does not repeat already-resolved probes.
14. As a host, I want the opening still chosen under existing reviewer/topic eligibility and opening-history rules, so that fewer calls do not change those safeguards.
15. As a defender, I want an unanswered or timed-out turn treated factually, so that the panel never fabricates an answer or strength.
16. As a host, I want completion checked against the confirmed budget and coverage rules, so that a faster planner cannot finish prematurely or continue indefinitely.
17. As a defender, I want invalid planning decisions rejected before they advance coverage, so that the room remains consistent.
18. As a defender, I want questions grounded in exact accepted sources, so that I can inspect the cited evidence.
19. As a research-paper defender, I want citations restricted to the paper, so that code is not introduced into a paper-only defense.
20. As a mixed-defense defender, I want eligible paper and implementation evidence retained, so that either can support the discussion.
21. As a defender, I want focused context to include study-wide objectives and relevant surrounding text, so that speed does not strip statements of meaning.
22. As a defender, I want broader source lookup when the focused evidence is insufficient, so that the reviewer does not guess.
23. As a defender, I want omitted text distinguished from genuinely unsupported claims, so that the map is not treated as proof that a method is missing.
24. As a host, I want my confirmed profile kept separate from source evidence, so that editing the profile does not rewrite what the paper establishes.
25. As a defender, I want necessary prior answers and language preferences retained in context, so that shorter prompts do not forget the conversation.
26. As an English-speaking defender, I want concise natural questions, so that speed does not come at the cost of comprehensibility.
27. As a modern-Bisaya-speaking defender, I want language preferences and natural research terminology preserved, so that optimization does not force translation or change the agreed style.
28. As a host, I want context reused only for the accepted material and current confirmed preparation, so that another room or outdated map cannot influence my defense.
29. As a defender, I want the submitted text retained during review, so that a temporary error does not erase my work.
30. As a defender, I want Answer saved shown only after server acceptance, so that I know whether the answer actually counts.
31. As a defender, I want a retained but unaccepted submission identified clearly, so that I do not mistake storage for acceptance.
32. As a defender, I want an already accepted answer preserved when later planning or question generation fails, so that I do not answer again unnecessarily.
33. As a host, I want a valid next-turn plan retained after reviewer-only failure, so that retry avoids planning again.
34. As a host, I want recovery to retry only the failed stage and its saved input, so that previously successful work is not repeated.
35. As a defender, I want existing permitted direct-answer and saved-answer recovery actions retained, so that the optimization does not remove an established way forward.
36. As a host, I want one bounded automatic retry for eligible transient failure, so that brief interruptions can recover without repeated clicks.
37. As a host, I want 429 automatic recovery only when an appropriate provider Retry-After fits the remaining time and funds, so that rate limits are respected.
38. As a host, I want daily limits and exhausted allowances explained without automatic loops, so that retry does not waste requests or money.
39. As a host, I want configuration and incompatible-route errors distinguished from transient work, so that I know when operator action is required.
40. As a defender, I want retry delays distinguished from active generation, so that the interface explains why I am waiting.
41. As a host, I want repeated recovery clicks deduplicated, so that they cannot dispatch duplicate paid work.
42. As a defender, I want obsolete work ignored after ending, restarting or leaving a closed room, so that late results cannot affect a different run.
43. As a defender, I want reconnect to restore the actual operation and elapsed time, so that it does not replay a pretend waiting sequence.
44. As a defender, I want navigation to preserve the room's authoritative state, so that opening Account or Controls does not restart generation.
45. As a defender, I want most successful transitions to target 10–15 seconds, so that practice maintains its rhythm.
46. As a defender, I want automatic processing bounded at 45 seconds, so that the room cannot appear to wait forever.
47. As a defender, I want my answer retained with recovery at the processing limit, so that a timeout does not force me to start over.
48. As a defender, I want reaction-reading and voting intervals distinguished from generation delay, so that performance reporting is honest.
49. As a defender, I want my existing answer/probe deadline preserved during failure and retry, so that recovery does not silently refund time.
50. As a defender, I want animations to add no artificial delay, so that ready results appear immediately.
51. As a defender, I want a small animated indicator while a question is being generated, so that I can see work is still active.
52. As a defender, I want Thinking… or Preparing your question… when question generation is known, so that the waiting label is simple and understandable.
53. As a defender, I want Evaluating your answer… during actual answer review, so that I understand which step is running.
54. As a defender, I want Preparing a clarification… for an identifiable clarification request, so that I know the current question is being explained.
55. As a defender, I want Reviewing your reply… for probe processing, so that it is distinguished from a new question.
56. As a host, I want Mapping your paper… and genuine mapping progress preserved, so that preparation also has clear waiting feedback.
57. As a host, I want Checking source references… only when validation is actually reported, so that status text does not invent internal stages.
58. As a defender, I want Preparing your coaching… while overview or answer sections generate, so that Results does not look frozen.
59. As a defender, I want finished coaching cards visible while other sections are pending, so that animation does not hide usable results.
60. As a host, I want Trying again… during an admitted retry, so that recovery activity is visible.
61. As a host, I want a provider-directed retry countdown only when its delay is known, so that the interface does not invent a wait duration.
62. As a defender, I want generic Preparing a response… when no more specific stage is known, so that the app stays truthful.
63. As a defender, I want animation replaced by a result or recovery message when work stops, so that a failed task does not look active.
64. As a defender, I want waiting feedback near the affected task, so that I can connect the indicator with what I requested.
65. As a defender, I want timers, drafts and permitted actions to remain readable while waiting, so that animation does not obscure the room.
66. As a phone user, I want compact waiting feedback in portrait and landscape, so that it does not create horizontal overflow or cover the answer area.
67. As a keyboard user, I want stable focus and reachable recovery actions, so that new status updates do not interrupt input.
68. As a user who prefers reduced motion, I want a static indicator and useful text, so that the status remains accessible without animation.
69. As a screen-reader user, I want meaningful stage changes announced politely, so that dots and elapsed seconds do not create constant announcements.
70. As a defender, I want no fake percentages or fabricated model thoughts, so that the waiting display remains trustworthy.
71. As a Free-practice defender, I want the same factual animated presentation, so that my tier does not get confusing recovery feedback.
72. As a Streamlit user, I want equivalent status text with native waiting indicators, so that the fallback stays usable without a separate animation system.
73. As a host, I want reviewer models and reasoning settings fixed for a run, so that retry or an operator edit cannot change the panel halfway through.
74. As an operator, I want role-specific model replacements accepted only after same-case evaluation, so that advertised benchmarks alone do not drive production choices.
75. As an operator, I want lighter interactive reasoning and output limits measured for valid complete responses, so that lower settings do not truncate required data.
76. As an operator, I want difficult questions to retain sufficient reasoning capacity, so that speed is not obtained by weakening research scrutiny.
77. As a host, I want no automatic model switch after failure, so that quality and spending stay predictable.
78. As an operator, I want saved legacy policies to retain compatible behavior, so that adopting the new pipeline does not rewrite active scopes.
79. As a host, I want old results and transcripts readable, so that new status or plan data does not break prior records.
80. As a host, I want the existing credit price and voucher rules preserved, so that this improvement does not add a surcharge.
81. As a host, I want an opening charged only after its existing validated commit, so that rejected or repeated drafts do not create extra charges.
82. As a host, I want the protected coaching reserve preserved, so that interactive work cannot spend the funds needed to finish Results.
83. As an operator, I want new-stage admission bounds calculated conservatively, so that two calls are not assumed to cost less without evidence.
84. As an operator, I want retries and broader lookups counted against shared allowances, so that concurrency cannot overspend a run.
85. As an operator, I want unknown or late usage retained conservatively, so that cancellation is not treated as a free provider request.
86. As a Free-practice host, I want request quotas and zero-price routing preserved, so that recovery cannot silently become paid practice.
87. As a host, I want existing eligible credit-return recovery and once-only completion retained, so that new processing states cannot settle twice.
88. As an operator, I want privacy and price-routing guards preserved, so that faster routes do not relax data policy or spending limits.
89. As an operator, I want per-stage timing and supplied usage recorded without private content, so that I can diagnose slow turns safely.
90. As an operator, I want comparable current-versus-candidate runs using identical synthetic cases, so that claimed improvements have a meaningful baseline.
91. As an operator, I want failed and recovered turns included in measurements, so that successful fast samples do not conceal poor reliability.
92. As a host, I want a local preview before publication, so that I can inspect the waiting and recovery experience.
93. As an operator, I want offline correctness, real-provider quality, hosted transport and installed-device evidence separated, so that one passing check is not presented as proof of everything.
94. As an operator, I want failed latency or quality gates reported explicitly, so that deadlines are not quietly extended or unsupported models enabled.

## Implementation Decisions

- **Scope and ownership.** Optimize new Standard research/mixed policies across
  the shared coordinator and typed fallback. Free shares safe recovery and
  waiting presentation, but retains its own model, request limits and capacity
  evaluation. Keep code-only starts disabled and voice integration unchanged.
- **Two-request normal transition.** Extend the outgoing reviewer's interaction
  result to represent answer/clarification/probe and, for a resolved accepted
  exchange, a coverage assessment plus eligible next selection or completion.
  The next selected reviewer returns grounded question/reaction dialogue. An
  ordinary accepted-answer path must not dispatch an additional standalone
  planner request behind this combined response.
- **Prospective validation.** Derive next-step options from a detached,
  prospectively resolved session, since an unresolved live turn has no valid
  next-question options. Validate action, turn identity, assessment, reviewer,
  topic, follow-up eligibility and completion against server rules before
  advancing coverage. Do not mutate the live session to construct a prompt.
- **Same-question exchanges.** Clarification and probe results cannot advance
  coverage or contain an executable next-turn plan. Preserve current question
  numbering, citation, attribution, probe limits and explanation rules. Resolve
  a probe using the original answer plus the attributed reply, without erasing
  either. Preserve existing direct-answer/saved-answer recovery permissions.
- **Nonstandard paths.** Openings, timeouts and unanswered outcomes retain the
  separate planner/assigned-reviewer path. A direct-answer route without a
  combined interpretation result still needs validated planning. Completion
  invokes existing progressive coaching. No invented assessment substitutes for
  missing work; exceptional paths are not presented as always using two calls.
- **Acceptance and publication.** A retained input is not accepted merely
  because it is stored. Acceptance follows the existing authorized, validated
  submission rules. Invalid plans must not publish questions or advance coverage.
  A later planning/question failure cannot erase an already accepted answer.
  Do not expose provider partial JSON as a question or declare success early.
- **Focused evidence module.** Build a bounded reusable view of accepted source,
  confirmed map/profile, study-wide context and exact relevant/neighboring
  passages, retaining original source identities and locations. Include relevant
  previous exchanges, current question/citation, coverage, reviewer constraints
  and language preference. In mixed mode retain eligible code evidence. Scope
  reuse to accepted content and confirmed preparation, not filenames alone.
- **Broader lookup.** Keep access to all accepted source when focused material
  cannot support a grounded decision. Make expansion explicit, finite and
  observable; its exact context/request bound is a measurement gate. Reuse source
  extraction rather than rerunning paper mapping for each question. Every extra
  provider request fits the same processing and spending limits. At exhaustion,
  retain progress and recover rather than invent evidence. A missing excerpt or
  map entry never establishes that the whole paper omits a method or finding.
- **Citation contract.** Continue strict structured output and local exact-source
  validation. Preserve paper-only versus mixed citation eligibility. The map and
  host descriptions guide interpretation but are not replacement evidence or
  proof that a study is correct. This work does not add provider memory.
- **Reusable validated plans.** Store accepted stage output with its unchanged
  logical room/run/turn/preparation/source/context/policy identity. After
  reviewer-only failure, dispatch that reviewer against the retained plan, not
  another interpretation or planner call. Retry counters may change without
  changing the logical input identity. Reject reuse when material inputs change;
  end/restart/closure/expiry invalidates both work and reusable plans.
- **Operation lifecycle.** The room coordinator retains exclusive ownership of
  commands, publication, cancellation and stale-result fencing. Duplicate
  submissions/retry clicks cannot create overlapping work. A late provider
  completion cannot overwrite a newer room state, replay a reaction or affect
  a new run; its supplied billing evidence still reconciles appropriately.
- **Shared processing window.** New optimized Standard interactive processing
  uses one authoritative 45-second window spanning its serial stages, automatic
  retry/backoff and broader lookup. Do not renew the deadline at each stage,
  socket reconnect or automatic retry. Stop accepting the operation's results
  after expiry and expose recovery with retained work. A deliberate manual
  recovery can start a fresh bounded processing attempt only under existing
  attempt, permission and allowance checks; it does not renew the answer/probe
  deadline, reset quotas or charge another defense. Mapping and final coaching
  retain separate deadlines; legacy policies retain compatible behavior.
- **Automatic recovery.** Permit at most one automatic transient retry across a
  processing operation, rather than one per stage or a nested transport loop.
  Connection/temporary server failures are eligible only while current, within
  remaining time, attempts and funds. HTTP 429 additionally needs a valid,
  provider-supplied short Retry-After that fits those bounds. Daily exhaustion,
  configuration/authorization/privacy incompatibility and malformed or absent
  delay evidence do not imply automatic retry permission. Invalid structured
  decisions are not silently classified as temporary provider failures. Preserve
  sanitized HTTP and streamed-error classification; never echo raw provider text.
- **Timer behavior.** Retain authoritative answer/probe/vote/reaction rules and
  existing bounded review-pause accounting. Failure and delayed/manual retry
  cannot refund elapsed recovery time or re-arm an old remaining-time snapshot.
  Waiting labels, navigation and animations do not pause a timer or leave a room.
- **State/API additions.** Extend existing authenticated room snapshots and
  shared presentation contracts compatibly with factual operation stage, timing,
  active/retry-wait/failure disposition and pending-versus-accepted status where
  needed. Backend state is authoritative; a missing optional field falls back to
  honest generic wording rather than a fabricated stage. Do not give the browser
  arbitrary model, source, spending or workflow-selection authority.
- **Animated waiting presentation.** Reuse one small visual treatment across
  question/submission, preparation and Results surfaces: animated dots or a
  subtle pulse paired with stable factual text. Example labels include Thinking…
  Preparing your question…, Evaluating your answer…, Reviewing your reply…,
  Preparing a clarification…, Mapping your paper…, Checking source references…,
  Preparing your coaching…, Trying again… and Waiting to retry…. Choose the
  label from known work, not a timed text carousel. Use generic Preparing a
  response… when intent/stage is unknown; do not predict a clarification before
  the system knows that is the task.
- **Presentation lifecycle and accessibility.** Preserve true mapping/coaching
  progress, visible accepted answers and ready cards. Stop active animation on
  success, terminal failure, cancellation and invalidation; distinguish backoff
  from generation. Restore actual state on reconnect. Avoid layout shifts,
  overlays that obscure actions and focus changes. Respect reduced motion with
  a static indicator. Keep decorative dots and elapsed ticks out of repeated
  screen-reader announcements; announce meaningful changes politely. WebViews
  inherit shared web presentation; Streamlit uses native waiting indicators with
  equivalent factual labels. No fake percentages, invented thoughts, additional
  AI calls or artificial minimum display duration.
- **Model and reasoning policy.** Keep distinct role assignments. Permit a new
  assignment or lighter task reasoning/output only after identical-case speed,
  grounded dialogue and combined-decision evaluation. Leave enough output for
  required schemas and citations, and enough reasoning for difficult research
  questions. Validate combined-decision capability for every outgoing reviewer.
  Numeric limits and concrete replacements remain measurement gates; none is
  selected by this specification. No automatic fallback or mid-run adjustment.
- **Saved policy compatibility.** Version the new pipeline, evidence-context and
  relevant processing/model/reasoning/output settings in server-owned snapshots
  for new runs. Absent-version legacy snapshots retain the previous compatible
  route. Operator changes affect future scopes, not active/retrying scopes.
  Preserve reading of older transcripts/results and existing room permissions.
- **Provider allowance and app finances.** Recalculate admission and dispatch
  bounds for the actual combined schemas, selected route/output/reasoning,
  possible expansion and retry work. Do not assume removal of a planner call
  proves a lower bill. Preserve the current default run ceiling, separate
  preparation allowance, coaching reserve, price/privacy caps, unknown-usage
  holds and concurrency-safe reservation/reconciliation. Decline unfundable
  work before dispatch with retained progress. Free requests remain zero-price
  and counted against their existing shared and protected quotas.
- **Once-only effects.** Retain opening-history checks and charge at the existing
  authoritative validated opening commit; retries, invalid candidates and saved
  plans do not charge again. Keep voucher access, partial-coaching completion,
  eligible credit returns and late-result safeguards. UI-visible work or partial
  Results is not a second financial completion signal.
- **Measurement.** Record complete operation duration plus stage duration,
  provider failure/validation outcome and retry/lookup overhead. Retain selected
  model/provider and token/reasoning/cost data only when available, distinguishing
  unavailable metrics from zero. Avoid logging uploaded text, submissions,
  credentials, raw provider payloads or hidden reasoning. Measure the baseline
  and candidate on identical synthetic sources/answers and disclosed conditions.
- **Delivery checkpoints.** First keep the app runnable while adding stage
  timing, factual animation/status, answer/plan retention and bounded recovery,
  including shared Free recovery. Then deliver combined Standard planning,
  focused evidence and comparison-tested model/reasoning settings with typed
  fallback parity. Both checkpoints need reviewable local evidence; no local
  publication of this spec authorizes a push or deployment.

## Testing Decisions

- Prefer observable behavior at the highest existing boundary. The user
  confirmed authenticated FastAPI HTTP/WebSocket room flows with mocked AI and
  payments and a controlled clock; whole-App React/browser behavior; existing
  provider-contract and typed fallback tests; and real local PostgreSQL checks.
  Avoid a separate test seam for every helper or assertions mirroring internal
  implementation structure. Provider request count/routing are observable
  contract behavior where the feature explicitly promises fewer requests.
- Extend the existing authenticated two-client research and OpenRouter checkpoint
  fixtures to run eight/twelve-question research/mixed defenses. Assert accepted
  snapshots, valid citations, adaptive coverage, permitted actors, probe/clarify
  semantics, retained answers, completion and once-only financial effects. The
  normal accepted-answer transition must make the combined outgoing-reviewer
  request then the selected-reviewer request without a third planner request.
- Use existing workflow injection, HTTP MockTransport and structured-stream
  fixtures for combined schemas, all reviewer assignments, ineligible decisions,
  ungrounded/mixed-invalid references, evidence expansion, truncated/invalid
  responses and completion. Prove rejection does not publish partial output or
  advance live coverage, and no response grants the browser workflow authority.
- Controlled clocks and provider barriers must cover 45-second exhaustion across
  serial stages/backoff/lookup, a valid response just before expiry, late results,
  duplicate retries, reconnect, end/restart and cancellation. Assert one shared
  automatic retry and stage-only reuse. Cover HTTP and streamed 429 with valid,
  malformed, missing, excessive or exhausted-budget Retry-After; daily/config
  failures must not auto-loop. Do not use real sleeps to establish timer policy.
- Extend existing interaction recovery tests for answer/clarification/probe and
  delayed retry without time refunds. Distinguish retained input from accepted
  answer and verify existing direct/saved-answer permissions. A planning or
  reviewer failure after acceptance must leave the accepted text unchanged.
- Exercise focused evidence through those same provider/room contracts using
  synthetic cross-section and cross-document cases. Include decisive evidence
  outside the first excerpt, ambiguous profiles, qualitative/theoretical and
  mixed studies, mixed-mode code references, changed preparation identity and
  necessary language/probe history. Demonstrate bounded expansion or honest
  recovery instead of claims that omitted material is absent from the paper.
- Reuse provider allowance/opening/coaching tests and the opt-in local PostgreSQL
  runner to verify concurrent admissions, protected coaching, once-only charging,
  duplicate/stale outcomes, unknown/late cost holds and retained legacy snapshots.
  Mocked providers with a real local database test transaction behavior, not
  actual billing or provider acceptance. Preserve current Free quota/no-paid-
  fallback checks and test shared recovery without assuming increased capacity.
- Extend whole-App navigation, stage, preparation and progressive-coaching tests
  to render realistic room transitions and activate recovery controls. Assert
  truthful labels, retained drafts/answers/ready cards, permitted actions and
  indicator cleanup. Test reduced motion and meaningful accessible status rather
  than CSS keyframe details. A component snapshot alone is insufficient evidence
  of correct action dispatch or lifecycle cleanup.
- Use local synthetic browser previews for desktop, portrait and landscape,
  including long labels, keyboard focus, reduced motion and reconnect/failure
  transitions. Inspect screenshots and actual interactions; record previews as
  synthetic, and do not call them user-reviewed before the user reviews them.
- Extend existing typed Streamlit whole-app synthetic-router tests for the same
  combined policy, source grounding, stage-specific recovery, retained draft,
  status text, bounded processing and protected funds. Use native waiting UI;
  do not build a second browser animation architecture for the fallback.
- Run the complete Python and React suites and production build, followed by the
  agreed real local database gate. Passing offline tests must be described as
  AI/provider mocked, never as evidence of realistic question quality or actual
  model latency. Do not reinterpret prior suite counts as tests of new behavior.
- Separately run comparable real-provider synthetic-paper/answer cases across
  research approaches/fields and English/modern Bisaya. Record baseline and
  candidate transition distributions, sample counts, failures, retries, source
  size, model/reasoning settings, supplied usage/cost and grounded conversation
  review for every role. Include long-context and difficult cases, not only
  short successful requests. Routing/first-token time is not complete duration.
  Report missing measurements and uncertainty rather than invented savings.
- Verify the 10–15-second usual-transition target empirically, disclosing what
  fraction and distribution achieved it; no unapproved percentile threshold or
  sample size is silently assumed. Correct 45-second cap/recovery behavior is a
  deterministic gate. A failed speed, compatibility or quality gate remains
  explicit and prevents a live-ready claim; it does not authorize raised caps,
  weaker grounding or an untested fallback.
- Keep local correctness, real-provider quality/cost, hosted transport and
  installed-device evidence separate. This spec does not require new native
  microphone work or reactivate voice; normal web layout evidence cannot prove
  installed-device behavior. No private paper is needed for the comparison set.

## Out of Scope

- Optimizing Free's model assignments/capacity or silently applying Standard's
  combined model pipeline to Free; its shared recovery/waiting changes remain in
  scope. No promise of free-provider availability or quota reset.
- A new paper-mapping or final-coaching model/prompt/deadline redesign, unless a
  measured dependency is reported for review. Their waiting presentation is in
  scope; the 45-second interactive cap does not replace their deadline policies.
- Voice enablement, speech-provider migration, audio capture or native permission
  work; code-only re-enablement; new retail tiers or revised credit prices.
- Fixed pre-generated question banks, removal of adaptive coverage, deterministic
  replacement of AI topic ranking, collapsing all reviewer dialogue into a single
  GLM route, speculative background generations or an extra evaluation AI call.
- Model training, shared permanent provider memory, new external vector hosting
  or additional paid infrastructure merely to display source context/status.
- Automatic model fallback, mid-run settings changes, relaxed privacy/routing
  price caps, increased default spending allowance or waived source validation.
- New answer content authored on behalf of the team, fabricated thoughts or
  progress percentages, full-screen redesign or changes to reaction/vote rules.
- Durable archiving of room content or changing in-memory room lifecycle. A
  server restart still removes active rooms; this work does not promise resume
  of an erased room or resurrect an obsolete plan.
- GitHub publication, merge, push or deployment as part of writing this spec.

## Further Notes

- Source of scope: [confirmed responsiveness plan](../../docs/DEFENSE_TURN_RESPONSIVENESS_PLAN.md),
  including Q1–Q11 and the animated waiting amendment.
- Architectural rationale: [combined validated turn planning](../../docs/adr/0008-combined-validated-turn-planning.md).
  Preserve [opening-history boundaries](../../docs/adr/0006-bounded-opening-question-history.md)
  and [partial coaching versus settlement](../../docs/adr/0007-progressive-coaching-before-settlement.md).
- Existing OpenRouter migration decisions are superseded only where this plan
  explicitly agrees: combined planning ownership, focused evidence, bounded
  eligible automatic recovery and measured interactive settings. Other access,
  finance, grounding, language and lifecycle decisions remain constraints.
- Exact replacement models, output/reasoning/context limits, broader-lookup
  bounds and qualifying Retry-After duration require measurement under the
  agreed processing/privacy/spending limits. They are not secretly selected by
  this document or proof that the present model bundle is faster or better.
- A user-triggered recovery remains distinct from an automatic retry inside one
  processing attempt: it may begin fresh bounded work under existing checks,
  without renewing the answer timer, resetting allowances or losing a reusable
  validated plan. This makes recovery possible after the 45-second cap while
  preserving the agreed automatic-work limit and no-time-refund rule.
- The user confirmed these testing boundaries on 2026-10-21. This specification
  publishes the confirmed design locally as ready-for-agent; it does not claim
  implementation, passing new tests, live speed/quality, hosted readiness or
  human visual review. Next workflow step is dependency-aware local tickets.

# Defense turn responsiveness plan

Status: confirmed plan; Q1–Q11 approved, with user-requested animated waiting
status amendment on 2026-10-21. Planning complete.
Updated 2026-10-21. No implementation or publication started for this plan.
User requested planning through Ask Matt; using Grill with Docs.

## Problem and evidence

The user successfully started an eight-question defense, then reported slow
question generation, retry prompts and repeatedly submitting an answer. Their
previous Luna workflow felt smoother. This is a reported regression, not an
accepted latency baseline.

Current Standard research/mixed generation uses a GLM planner followed by the
selected reviewer's model. An ordinary submitted answer first passes through
same-reviewer interpretation, which may clarify, probe or accept the answer.
An accepted non-final answer can therefore precede three sequential AI requests:
interpretation, planning and question generation. Planner/reviewer requests each
receive accepted source text, research context and transcript. A map is a reviewed
profile/topic/reference structure, not shared persistent provider memory or a
pre-generated bank of defense questions.

Read-only authenticated OpenRouter request metadata inspected on 2026-10-20
showed four DeepSeek/Relace HTTP 429 failures around 21:48–21:50 Asia/Manila.
The saved detailed error was null. This establishes upstream rejections, not a
specific quota category, exact retry delay or correspondence to every room error.
Routing latency fields do not measure full generation duration. No new inference,
key access or uploaded paper content was used for this inspection.

The published GLM low-effort switch affects new Standard mapping preparations;
Methodology questions still use DeepSeek high, Critical GLM high, Ethics Haiku
medium, and Impact Qwen with its saved reasoning-token request. Saved run policy
fixes assignments/limits, including retries. Mapping speed is separate from live
turn responsiveness.

Relevant source: backend/openrouter_questions.py, backend/rooms/questions.py,
backend/rooms/submissions.py, backend/question_generator.py,
game/src/components/AnswerComposer.tsx and game/src/lib/roomPresentation.ts.

## Existing decisions that a new plan must address explicitly

The confirmed OpenRouter migration plan selected a separate adaptive planner,
role-assigned reviewer models, selected-model retries without automatic model
fallback, fixed settings per run, bounded spending and protected coaching funds.
Any change to these decisions needs explicit agreement; it is not an incidental
performance refactor. Historical branch-freeze wording in that plan is superseded
by AGENTS.md: main is the default publication destination when requested.

Grounded citations, profile/source separation, research coverage, clarification
and same-question probes, opening history, accepted-answer retention, server
deadlines, duplicate/stale-work protection and once-only financial effects remain
constraints to discuss, not expendable speed shortcuts.

## Confirmed decisions

- Q1: Standard research/mixed defenses first, in React and typed Streamlit.
  Shared answer-preservation/retry improvements apply to Free too, but its model
  capacity is evaluated separately. This does not expand the Standard model or
  pipeline changes into Free automatically.
- Q2: keep distinct reviewer roles and allow model replacements only after
  same-paper speed, grounding and conversation-quality comparisons. Mapping and
  coaching changes stay outside this work unless measurements identify a
  dependency. Selected settings remain fixed within a run. No replacement model
  has been chosen and no automatic runtime model fallback is approved.
- Q3: combine interpretation and next-turn planning in the outgoing reviewer's
  request. For an accepted answer, that model assesses coverage and chooses the
  next eligible reviewer/topic; the selected reviewer writes the next question.
  Server validation remains authoritative. Openings and timeouts retain a
  separate planner. Planning ownership changes from fixed GLM on normal answers;
  all four assigned models therefore need combined-decision quality checks.
- Q4: retain an already-validated plan when only reviewer generation fails, then
  retry that failed stage with the accepted answer retained. Scope reuse to
  unchanged room/run/turn/generation/inputs and invalidate on restart, ending or
  other obsolete work. No extra defense charge or automatic model switch.
- Q5: tune task-specific interactive reasoning/output limits through comparisons.
  Preserve enough capacity for difficult questions, citations and complete valid
  schemas; mapping and final coaching retain their policies unless a measured
  dependency requires review. No numeric limit or new setting is selected yet.
- Q6: use reusable focused evidence from the confirmed research map, study-wide
  context, relevant exact source passages and nearby text, plus necessary
  conversation history. Retain access to the whole accepted paper for bounded
  broader lookup when evidence is insufficient. Validate citations against the
  original upload. A map or omitted excerpt cannot establish that something is
  missing from the paper. This is a new source-context policy, not persistent
  provider memory or reliance on AI summaries as evidence.
- Q7: allow one bounded automatic retry for transient connection/server failure.
  HTTP429 may retry automatically only when a provider-supplied short Retry-After
  fits remaining time and spending allowance. Otherwise retain submitted work
  and provide manual recovery. Daily limits, exhausted funds and invalid
  configuration do not cause automatic retry loops. No automatic model switch.
- Q8: show factual stages such as Reviewing your answer / Preparing the next
  question, elapsed time, and Answer saved only after acceptance. A failed
  interpretation retains the submission without claiming it was accepted.
  Recovery names the failed step and retries saved input rather than requiring
  the same answer to be resubmitted. No fictional thinking or fake percentages.
- Q9: aim for most successful answer-to-next-question transitions within 10–15
  seconds, with a 45-second total processing window including automatic retry
  and broader lookup. Exclude intentional reaction-reading and voting intervals.
  At the limit, retain work and offer recovery. These are targets to verify, not
  proven speed: report a failed quality/availability gate rather than silently
  increasing the wait. This is not a new mapping or final-coaching deadline.
- Q10: deliver two runnable local checkpoints and the agreed verification below.
  Preserve prices, privacy, authoritative timer rules and fixed per-run settings.
  Present a local preview before publication and require actual-provider evidence
  before calling the optimized route live-ready.
- User amendment, 2026-10-21: add simple animated status labels for question
  generation and other waits for AI responses, using wording such as Thinking…
  or Evaluating… when it truthfully describes active work. Include this in the
  existing waiting/status checkpoint; no extra AI request is needed.

## Animated waiting feedback

Use a small shared status treatment with gently animated dots or a subtle pulse,
matching the existing visual style. Pair it with the actual operation's label:

| Active work | Example status |
| --- | --- |
| Paper mapping/remapping | Mapping your paper… |
| Source/map validation, where actually reported | Checking source references… |
| Opening or next-question generation | Thinking… Preparing your question… |
| Answer interpretation | Evaluating your answer… |
| Clarification response | Preparing a clarification… |
| Probe-reply interpretation | Reviewing your reply… |
| Coaching overview or answer section | Preparing your coaching… |
| Admitted retry | Trying again… |
| Provider-directed retry wait | Waiting to retry… with a truthful remaining delay |

Labels follow actual room/task state, not a timed rotation through invented
steps. If only generic generation is known, show Thinking… or Preparing a
response… until a more specific state is available. Do not suggest that text
reveals the model's internal reasoning, certify that an answer is correct, or
display fake completion percentages. Retain existing genuine mapping/coaching
progress and the pending-versus-accepted answer distinction.

Show the indicator near the affected question, submission, mapping or Results
section so the reason for waiting is clear. Keep accepted answers and completed
coaching cards visible. Stop animation immediately on completion, failure,
cancellation or invalidation and replace it with the result/recovery action;
an unavailable task must not look as if it is still running. Retry-wait wording
does not imply an active generation request. Navigation/reconnect must reflect
the actual current state rather than starting a fresh pretend sequence.

Keep wording stable while the dots animate. Respect reduced-motion preferences
with a static indicator, keep decorative motion out of screen-reader text, and
announce meaningful status changes politely rather than each animation frame or
elapsed second. Avoid layout shifts and keep timers/actions readable on desktop,
portrait and landscape. This shared presentation applies to Standard and Free
web/WebView flows; Streamlit uses its native waiting indicator and matching
factual text. It does not enable voice or add new provider work.

## Planned flow and validation boundaries

Source constraints for the selected Q3/Q4 direction:

- Combine interpretation and next-turn assessment/selection in the outgoing
  reviewer's request, then let the chosen next reviewer generate its dialogue.
  This could reduce ordinary accepted-answer transitions from three requests to
  two, but changes planning ownership from GLM to the outgoing reviewer. Planning
  must use a detached prospective resolved session: live unresolved turns do not
  expose valid next-question options. Clarification/probe results cannot advance
  coverage; resolved probe exchanges must retain both speakers' contributions.
  Openings and timeouts still need a separate planning path.
- Retain a validated planner result when only reviewer generation fails, then
  retry that stage against unchanged run/turn/generation/context. Current retries
  rerun planning too. Reuse must expire when its inputs or room operation change.

An ordinary accepted answer therefore follows:

```text
Saved submission
  -> outgoing reviewer: interpretation + validated coverage/next-turn proposal
  -> selected reviewer: grounded question + optional reaction
  -> existing reaction interval and speaker vote
```

Clarification and a same-question probe stay within the current turn. Opening
questions and unanswered/timeout transitions use the separate planner and
assigned reviewer. Completion uses the existing coaching path. Broader evidence
lookup and the approved retry are exceptional bounded work, so two requests is
the normal path, not a guarantee for every recovery scenario.

Later planning/question failure cannot erase an already accepted answer. Invalid
decisions cannot advance coverage, publish an ungrounded question or charge
again. Stage reuse belongs to the logical room operation and unchanged inputs;
retry-attempt counters must not accidentally invalidate it or permit stale work
from an ended/restarted operation. Retained submissions are distinct from
accepted answers and the interface must preserve that distinction.

Changing AI-selected topic ranking to deterministic server selection would be a
different behavior choice; collapsing planner and dialogue into one GLM request
would abandon the current role-assigned question models. Neither is assumed.

Existing HTTP MockTransport and two-client tests cover model/schema dispatch,
stale work, 503/429 recovery, retained answers and failed/delayed interaction
clocks. They do not measure live latency or quality. A comparison harness would
need complete accepted-turn duration plus per-stage timing, failure/validation
outcomes and provider-supplied usage/cost, using the same synthetic material and
answers. No live benchmark was run during planning.

Any changed pipeline needs an explicit saved policy version for new runs and
compatible legacy behavior. Admission bounds must reflect actual stages and
combined schemas without releasing uncertain usage holds or spending coaching
reserves. Removing one request is not proof of a particular cost reduction.

## Delivery and verification

Checkpoint 1: stage timing, animated factual waiting labels, retained
answers/validated plans and bounded recovery.
Keep the existing pipeline runnable while establishing baseline measurements,
specific recovery actions and the shared Free recovery behavior.

Checkpoint 2: combined interpretation/planning, focused evidence with broader
lookup and measured model/reasoning tuning for new Standard research/mixed runs.
Mirror shared policy in typed Streamlit; Free model/pipeline optimization remains
a separate evaluation. Keep mapping/coaching policy unless a measured dependency
requires review.

Require the full Python/React suites and production build, real local database
spending-concurrency checks, mocked two-client eight/twelve-question
research/mixed runs, and desktop/portrait/landscape checks. Cover clarification,
probe replies, openings, timeouts, completion, retry after each failed stage,
accepted/pending answer status, reconnect, duplicate submissions, end/restart
invalidation, legacy snapshots and unchanged charge/return/settlement behavior.
Controlled-clock checks must establish the shared processing deadline and
existing answer-timer rules; retries/lookups must not reset their windows.
UI checks also cover waiting labels for mapping, generation, interpretation,
clarification/probe replies, coaching and retry; indicator cleanup on success,
failure/end/restart, retained partial results, reduced motion, meaningful
screen-reader status changes and narrow-screen layout. Animation never adds
an artificial delay or extends the 45-second interactive processing cap; mapping
and final coaching keep their separate deadline policies.

Separately compare identical synthetic papers and answers across research
fields/approaches and English/modern Bisaya. Record complete successful-transition
time and failure rates, not only model throughput or routing time; include
per-stage timing, retry/lookup overhead, provider-supplied usage/cost, validation,
coverage and dialogue/grounding quality. Preserve identical cases for the
current-pipeline baseline and candidate comparisons. Provider metrics do not
justify logging private uploads, answers, credentials or hidden reasoning.

Actual-provider evidence must validate schema/reasoning/context/privacy-route
compatibility and conversational quality for all four combined-decision roles.
No replacement is selected merely from advertised speed or benchmark rankings.
If the measured targets or quality gates fail, report the limitation before
claiming readiness. Hosted transport and installed-device behavior remain
separate from local browser/provider evidence. Present the local preview before
publication; human review must actually occur before it is recorded as reviewed.

## Compatibility and financial boundaries

Compatibility and financial boundaries remain the established defaults:
version new pipeline/context policies for new runs; preserve saved-policy
behavior for existing scopes and old results. Keep current privacy/price caps,
default run ceiling, protected coaching and once-only charge/return rules.
Recalculate conservative admission bounds for actual new stages/schemas instead
of assuming deleted planner calls make the previous bound accurate. Count
retries, broader lookups and uncertain usage; do not reset quotas or billing
holds. No automatic mid-run model/reasoning switch or extra charge is approved.

## Final review and implementation-time measurements

Q1–Q10 settled the scope and delivery direction. The user confirmed the complete
plan in Q11 on 2026-10-21. Planning is complete. The
[implementation specification](../.scratch/defense-turn-responsiveness/spec.md)
is published in the local tracker as ready-for-agent after the user confirmed
its test boundaries on 2026-10-21. Dependency-aware implementation tickets are
next and have not been created for this improvement. Planning/specification
publication does not start implementation, push or deployment. No runtime code,
operator settings or model assignments changed during planning/specification.

Implementation must measure exact model assignments, reasoning/output/context
limits, broader-lookup bound and suitable Retry-After handling within the agreed
45-second window and spending/privacy rules. These are explicit evidence gates,
not permission for arbitrary fallback, raised caps or weaker source validation.
An unresolved gate must remain documented as unresolved. No actual latency,
cost saving, dialogue quality or Free capacity improvement is established yet.

Architectural rationale: [combined validated turn planning](adr/0008-combined-validated-turn-planning.md).

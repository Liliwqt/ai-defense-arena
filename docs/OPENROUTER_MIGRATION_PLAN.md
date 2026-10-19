# OpenRouter migration plan

Status: confirmed plan; user approved consolidated scope in Q11 on 2026-10-19.
Planning complete. Checked 2026-10-19.
No implementation, key/configuration change, paid call, price change, push or deployment.
Work stays on feature/question-first-room; main remains frozen.

## Intended outcome and confirmed decisions

- Replace all direct OpenAI API dependencies with OpenRouter-backed text and speech.
  Removing a direct API dependency does not require removing the OpenAI-compatible SDK.
- Research-first, adapting to the existing confirmed research field/approach;
  retain Research + code. Q5 confirmed: temporarily disable Code project
  Experimental rather than assigning it a new model bundle.
- Configure models for reviewer roles and shared tasks; preserve the existing
  grounded citations, server ownership, opening history, question budgets, timers,
  speaker rules, manual Send, financial settlement and failed-defense recovery.
- Q1 confirmed: two delivery checkpoints. Text (mapping, questions, submission
  handling and coaching) first; speech follows only after an OpenRouter-only
  live-caption prototype proves the required behavior. Voice remains off between
  those checkpoints. The final objective still includes replacing direct speech.
- Q2 confirmed: keep bounded retries on the selected model and existing recovery;
  no automatic switch to another or more expensive model.
- Q3 confirmed: use the initial model/reasoning bundle below for evaluation.
- Q4 confirmed: a small GLM low-reasoning planner selects the eligible next
  action/reviewer/topic, then the selected reviewer model generates the question.
  Both results must validate before any room or financial change.
- Q6 confirmed: snapshot model assignments, reasoning and output limits for each
  run, including retries. Operator edits apply to new runs; the browser cannot
  choose arbitrary model IDs. Recovery retains that run's selected model.
- Q7 confirmed: bounded task output/reasoning limits and an operator-configured
  provider-spending ceiling per defense, including planner calls and retries.
  Preserve answers and pause with clear recovery before an unaffordable request.
  Select numeric limits after synthetic-run measurement; never add a user
  surcharge or alter the credit price as a consequence of the provider ceiling.
- Q8 confirmed: mapping/remapping uses a separate preparation allowance. Each
  defense protects a final-coaching reserve from question/interaction spending.
- Q9 confirmed: Streamlit research/mixed uses the same task models, reasoning
  and spending rules, retaining its typed interface; code-only is disabled there.
- Q10 confirmed: offline, mocked two-client, real local database concurrency and
  responsive checks, plus separate live provider/model and speech acceptance
  evidence as detailed below. Present local previews before publication.
- New retail defense tiers are future work. This migration does not change the
  current tester price, voucher policy or cost per defense.

## Confirmed initial model assignments and reasoning

These are evaluation policies, not validated superiority claims. The exact
provider must support the combined model/schema/reasoning/context contract.

| Task / reviewer | Exact model ID | Initial reasoning policy |
| --- | --- | --- |
| Paper mapping and corrected remapping | deepseek/deepseek-v4.1-flash-1017 | high |
| Methodology Reviewer question/reaction | deepseek/deepseek-v4.1-flash-1017 | high |
| Ethics Reviewer question/reaction | anthropic/claude-haiku-5.5 | medium |
| Impact Reviewer question/reaction | qwen/qwen3.8-flash | Explicit bounded reasoning-token budget; numeric limit pending provider/Responses compatibility check |
| Critical Reviewer question/reaction | z-ai/glm-5.3-flash | high; never silently use its max default |
| Clarification/probe/submission interpretation | Current reviewer's assigned model | Lowest supported enabled reasoning: low for DeepSeek/Haiku/GLM; bounded budget for Qwen |
| Final coaching overview and per-answer sections | anthropic/claude-haiku-5.5 | high |
| Reviewer/topic planning request | z-ai/glm-5.3-flash | low; approved two-stage routing |
| Code-only Experimental | Temporarily disabled under Q5 | No new code-only defense or hidden direct-OpenAI fallback |

The current mapping code reads OPENAI_MODEL (default gpt-6-luna); it has not
switched to DeepSeek. Mapping needs careful profile/topic/objective/reference
extraction across research approaches, so high reasoning is selected there even
when shorter interactive exchanges use less reasoning. Mapping remains explicit,
with progress and host profile/budget confirmation; a provider change does not
make the suggested map authoritative.

DeepSeek advertises low/high/max/none, Haiku a range including medium/high, and
GLM low/high/max with reasoning mandatory. Qwen3.8 Flash advertises a token-budget
control without an effort selector. Do not send one global effort value to all
models or assume unsupported values are silently equivalent.

Reasoning consumes billed output tokens. Total output limits must leave enough
room for both thinking and the largest supported visible schema. Hiding reasoning
is not a billing discount. Validate task-specific ceilings on mapping/long-report
fixtures before selecting numeric caps. Do not expose hidden reasoning in the
mapping progress UI; retain factual progress updates.

Sources: [research and prices](OPENROUTER_MODEL_RESEARCH.md),
[model capability catalog](https://openrouter.ai/api/v1/models),
[reasoning options and budgets](https://openrouter.ai/docs/guides/best-practices/reasoning-tokens),
[Responses reasoning](https://openrouter.ai/docs/api_reference/responses/reasoning).

## Confirmed text routing and spending policy

Current research generation combines prior-answer coverage assessment, next
reviewer/topic selection, completion and grounded question generation in one
request. After the opening sequence, multiple reviewers may be eligible. The
caller cannot route by a reviewer that the response has not chosen yet.

Q4 selects a small GLM low-reasoning planner that chooses an allowed next
action/reviewer/topic and proposes coverage; the selected reviewer model writes
the question/reaction. This preserves adaptive selection and adds a request on
question-producing moves. Completion does not need a reviewer-generation request.
All intermediate work stays detached until the combined result validates; no
coverage, history, charge, question or clock is committed from a partial, failed
or stale plan. Existing reviewer eligibility and follow-up rules remain enforced
by the server. Model-level retries remain bounded under Q2; stale work cannot
commit or trigger fresh work after its room operation has been invalidated.
This applies to game state and credit charges; provider usage still costs money
when a dispatched request produces rejected or stale output and must be accounted.

Centralize explicit provider credentials, model/task assignment and capability
validation behind one server transport. Use OpenRouter names in operator errors
and setup. Preserve Responses parsing/streamed mapping contracts where verified;
otherwise adapt the transport deliberately instead of weakening source/schema
validation. No model fallback or direct-OpenAI fallback is allowed by Q2.

Capture the model assignment, reasoning and output limits for a run so operator
edits cannot change reviewers halfway through an active defense. Record necessary
model/usage metadata without
logging papers, answers, raw audio or credentials. Expose actual usage/cost only
when the provider supplies it; do not infer a guaranteed retail price from token
rates. Q7 approves request limits and a defense spending ceiling. Reserve a
conservative cost bound before dispatch and reconcile known usage afterwards;
concurrent work and retries must share the same allowance. Missing provider usage
must not be counted as zero, and exhausted allowance must not repeatedly call the
provider on Retry. A provider-side billing guarantee is not claimed by a local
ceiling; route pricing, reasoning and uncertain/late usage require explicit bounds.

Q8 separates preparation spending from defense spending. Capture preparation
settings when its allowance is established, so remapping has consistent bounded
costs. Size the protected coaching reserve against the confirmed question budget,
required overview/answer sections, bounded retries and uncertain outstanding
usage. The reserve is not available to extra questions or clarification requests.
Confirm that the selected configuration can support the required report before
starting; a reserve is not a promise of success under all provider failures.
Speech at checkpoint 2 must fit an explicit allowance within the run ceiling
and preserve the coaching reserve as well as the existing ten-minute voice cap.

Exhaustion blocks new provider work, keeps accepted answers/completed coaching
and explains recovery without a paid retry loop. Existing server deadlines and
timers retain their rules; a generation spending pause does not freeze an active
answer timer. Existing eligible failed-defense credit returns stay available;
the spending ceiling does not create a new automatic money-refund policy.
Numeric dollar/token caps are selected from measured synthetic cases and checked
before rollout, including large accepted papers and long required reports.

Code-only disabling must be enforced on server entry/start paths as well as the
interface; hiding a selector is insufficient. Preserve old code-only transcripts
and results without silently converting their mode. Research + code remains
available. Exact handling of already-active code-only rooms at migration must be
documented before rollout; a restart already loses in-memory rooms.

Q9 confirms the Streamlit policy: use the same research/mixed task
assignments and limits through the shared transport, keep typed input and its
current interface, and disable new code-only defenses there too.

## Speech checkpoint

OpenRouter documents file-transcription endpoints, not a verified compatible
replacement for the current Realtime WebSocket relay. Prototype bounded chunk
transcription, ordering/deduplication, late-result rejection, manual finalizing
Send, allowance accounting and temporary audio disposal before choosing it.
File-at-Send alone would remove live captions and is not an approved substitute.
Scribe v2 is a non-OpenAI-model candidate; lower-cost alternatives and provider
retention constraints are in the research note. No voice-model decision is final.

Keep the browser/native read-only draft, explicit mic action, no automatic Send,
typing fallback and authoritative deadlines. Actual caption/finalization latency,
English quality, conditional Tagalog/Bisaya, provider retention/cost and installed
Android/iOS behavior remain separate evidence. Stop or change the design if the
OpenRouter route cannot satisfy the agreed live-caption behavior; do not silently
claim feature parity.

## Delivery and agreed verification

Checkpoint 1 migrates the shared text transport, mapping, planner/reviewer flow,
interaction and progressive coaching with fixed settings, spending controls,
Streamlit parity and code-only disablement. Voice stays off.

Checkpoint 2 starts with an OpenRouter-only caption prototype. Review its measured
caption/finalization latency, recognition and retention before selecting the
speech model and enabling integration. Preserve incremental words, manual Send,
deadline rejection, ordered/deduplicated segments, temporary audio disposal,
English-first recognition and honest conditional Tagalog/Bisaya support. If the
prototype cannot meet the agreed live behavior, keep voice off and use typing;
do not silently substitute file-at-Send or return to the direct OpenAI service.

Q10 agrees to full Python/React suites and build; mocked request/stream/error,
strict-schema/citation/context handling, correct per-task/per-reviewer selection,
retries and stale multi-stage results; complete two-client research/mixed runs,
code-only rejection and existing-results regressions; existing history/credits/
return checks; real local database checks for concurrent spending reservations,
idempotent settlement and recovery; responsive mapping/coaching/voice previews.
Provider interfaces and clocks are mocked in offline room tests. Real database
checks establish allowance concurrency, not real provider billing behavior.

Separately check actual synthetic-paper model quality across research approaches,
schema/reasoning/context compatibility, account access, measured usage and latency.
Speech-provider cost/retention, hosted transport and installed Android/iOS capture
remain distinct evidence. Present local previews before publication; mocked or
source-only native checks cannot establish installed-device readiness.

## Final confirmation and implementation-time measurements

Q1–Q10 settle the product and delivery scope above. The user confirmed the whole
plan in Q11 on 2026-10-19. This completes planning only; it does not authorize
implementation, push or deployment. Next is a specification from this confirmed
plan, followed by implementation tickets. Those artifacts have not been created
as part of this planning session.

Implementation must resolve numeric output/reasoning/spend limits from fixtures,
Qwen budget/transport compatibility and the speech model/latency/retention gate
through the agreed evidence. These are explicit measurement gates, not silent
substitutions or claims that the candidate bundle is already compatible, cheaper
or more intelligent. A failed gate must be reported before changing the agreed
model policy or voice behavior. Retail defense tiers remain later work.

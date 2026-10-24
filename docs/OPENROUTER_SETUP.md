# OpenRouter text setup

Research/mixed mapping, planner/reviewer questions, clarification/probes and
progressive coaching now use shared funded OpenRouter clients in both web and
typed Streamlit. No implicit direct OpenAI text client remains. A missing funded
client fails closed; an old OpenAI key cannot enable a fallback. Code-only starts
and the old speech pilot remain disabled. Retained results are readable.

The text checkpoint is implemented locally; actual account/model tests and
measured capacity gates remain pending. This is not deployment approval.

For the selectable zero-credit model tier, see [Free practice](FREE_PRACTICE.md).
The assignments and USD limits below describe Standard practice.

## Configure the server

Set `OPENROUTER_API_KEY` privately in the launching environment. The tracked
`./run_local.sh` prompts privately if it is absent; it does not load or save an
`.env` file. Google host sign-in, vouchers and payment/database configuration
keep their existing setup. Keep exactly one worker and one instance.

| Setting | Candidate default | Meaning |
| --- | --- | --- |
| `OPENROUTER_PREPARATION_USD` | `0.75` | Separate per-preparation ceiling, positive decimal up to USD10. |
| `OPENROUTER_MAPPING_MAX_OUTPUT_TOKENS` | `65536` | Mapping reasoning plus visible output, configurable1024–131072. |
| `OPENROUTER_MAPPING_TIMEOUT_SECONDS` | `300` | Total mapping deadline, configurable 30–600 seconds. Applies to each new attempt, including retained preparations; model/reasoning/allowance snapshots stay fixed. |
| `OPENROUTER_MAPPING_REASONING_EFFORT` | `low` | Mapping-only effort for new preparations: `low` or `high`. Saved preparations retain their effort; retained policies predating this setting stay high. |
| `OPENROUTER_MAPPING_MODEL` | `z-ai/glm-5.3-flash` | Mapping-only model for new Standard preparations. Explicit rollback: `deepseek/deepseek-v4.1-flash-1017`. Saved preparations keep their model. |
| `OPENROUTER_RUN_USD` | `5.00` | Full per-run ceiling including coaching, positive decimal up to USD100. |

These are finite local admission settings, not measured bills, universal input
capacity or provider-side billing guarantees. They remain candidates until the
checkpoint's live/context/output/affordability checks pass. `OPENAI_MODEL` and
legacy effort variables do not override funded-run assignments.

Mapping previously stopped after 90 seconds even when structured output was
still arriving. High-reasoning maps can take longer. The default now permits
five minutes, with a separate 30-second network inactivity timeout and bounded
connection/write waits. Streaming topic progress remains provisional until the
complete map validates. This extends the waiting window; it does not establish
faster generation or successful completion on a particular paper. A failed or
cancelled attempt retains uploads and does not reset its spending reservation.
Cancellation and elapsed-deadline errors now have distinct messages. Changing
this transport setting does not change models, reasoning, output caps or prices.

| Task | Model | Reasoning | Total output bound |
| --- | --- | --- | --- |
| Mapping | `z-ai/glm-5.3-flash` | low for new preparations |65536|
| Planner | `z-ai/glm-5.3-flash` | low |4096|
| Methodology | `deepseek/deepseek-v4.1-flash-1017` | low |8192|
| Ethics | `anthropic/claude-haiku-5.5` | low |8192|
| Impact | `qwen/qwen3.8-flash` | reasoning max_tokens512 |8192|
| Critical | `z-ai/glm-5.3-flash` | low |8192|
| Overview/answer coaching | `anthropic/claude-haiku-5.5` | low |8192|

Same-reviewer clarification/probes use the assigned reviewer model, low reasoning
for Methodology/Ethics/Critical and reasoning max_tokens512 for Impact, within a
2048 total-output bound. Qwen's catalog advertises token-budget reasoning, not a
named effort. Actual selected-route support still requires account tests.

Mapping now requests low reasoning for new Standard preparations to reduce
unnecessary thinking time. The user selected GLM 5.3 Flash for the mapping trial;
the server explicitly selects it for new preparations. The complete paper, map schema, coverage instructions,
streaming progress, citation checks and output capacity are unchanged. This is
an effort request, not an exact reasoning-token cap or a measured speed guarantee.
The temporary low-reasoning trial also lowers reviewer/coaching defaults and
requests a 512-token reasoning budget for all Free tasks. Create a new room (or a new Streamlit preparation session) to use
the new setting; retrying an existing preparation keeps its saved effort.
Legacy preparations keep DeepSeek, including older saved policies without an
explicit model field. Set OPENROUTER_MAPPING_MODEL to the DeepSeek ID to roll
back future preparations; this does not rewrite active rooms or enable automatic
fallback. Actual GLM mapping speed and source coverage still need a live check.
See [mapping speed research](OPENROUTER_MAPPING_SPEED_RESEARCH.md) for candidate
models, published throughput and the pending same-paper quality/timing check.

## Temporary low-reasoning trial (2026-10-24)

New Standard runs request low for every named-effort task, including coaching.
Qwen questions and interactions request reasoning max_tokens512; Free mapping,
planning, questions, interactions and coaching also request max_tokens512.
These are requested settings, not measured latency or quality improvements.
Mapping already defaults to low; an explicit OPENROUTER_MAPPING_REASONING_EFFORT
operator override still applies. Existing preparation/run snapshots are preserved;
create a new room/preparation and run to use these defaults. Models, total output
limits, prices, citations and spending/recovery rules are unchanged. Revert this
trial commit to restore the preceding defaults for future runs.

## Allowances and recovery

Explicit preparation captures one policy and allowance. Revisiting, remapping,
correcting a profile, reconnecting or changing operator settings cannot reset
it. New rooms get new preparation scopes; Streamlit uses its opaque browser
identity/material scope, described in [its setup](STREAMLIT_OPENROUTER.md).

Start snapshots one run policy and checks its confirmed question budget and
coaching reserve before any defense-credit commitment. Planner choices validate
before a reviewer request. Only a validated opening commits history/access;
retries reuse the same run policy. An explicit new run establishes another scope.

Questions/interactions cannot spend the protected coaching remainder. Coaching
uses the full ceiling; ready sections survive failures, retries process failed
membership only, and completion writes regenerate no cards. All required sections
and durable completion precede successful financial settlement. Existing eligible
credit returns remain separate from provider costs. Additional retries may stop
safely when the allowance is exhausted; they are not promised unlimited funding.

Each request reserves its exact serialized-input/output bound before dispatch.
Known usage settles once. Missing, conflicting, cancelled or stale usage is never
assumed free; conflicting/over-bound cost blocks further spending for operator
review. Provider accounting stores scope/policy/cost metadata, not source text,
answers, audio or credentials. Real SQLite/PostgreSQL transactions own admission.

Requests require supported parameters, strict structured output, no provider
fallback, data_collection deny, zero request fee and maximum routing prices of
USD0.30/M input and USD1.20/M output. Reasoning is included in billed output.
The public catalog checked2026-10-20 lists a higher Haiku tier at100000 prompt
tokens (USD0.50/M input, USD2.50/M output), above these caps. Large-input route
availability is therefore a pending gate, not a reason to silently raise caps,
switch models, truncate sources or lower research scope.

## Verification boundaries

Provider-mocked contract/HTTP/WebSocket/AppTest/browser checks establish routing,
source grounding, synchronization, bounded spending and recovery. Real local
PostgreSQL checks separately establish transactional behavior. Neither proves
model quality, actual token usage, reasoning/output sufficiency or route access.
Numeric limits must be measured against synthetic large papers and long reports
before rollout. Failed compatibility/affordability gates require a reported
operator decision; the selected models, research scope and credit prices stay
unchanged until one is made. Speech stays off pending its separate prototype.

Primary sources checked2026-10-20:

- [Model capability and price catalog](https://openrouter.ai/api/v1/models).
- [Provider parameter, fallback, data-policy and price controls](https://openrouter.ai/docs/guides/routing/provider-selection).
- [Reasoning tokens and billed output](https://openrouter.ai/docs/guides/best-practices/reasoning-tokens).
- [Structured output](https://openrouter.ai/docs/guides/features/structured-outputs).

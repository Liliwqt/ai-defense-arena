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
| `OPENROUTER_RUN_USD` | `5.00` | Full per-run ceiling including coaching, positive decimal up to USD100. |

These are finite local admission settings, not measured bills, universal input
capacity or provider-side billing guarantees. They remain candidates until the
checkpoint's live/context/output/affordability checks pass. `OPENAI_MODEL` and
legacy effort variables do not override funded-run assignments.

| Task | Model | Reasoning | Total output bound |
| --- | --- | --- | --- |
| Mapping | `deepseek/deepseek-v4.1-flash-1017` | high |65536|
| Planner | `z-ai/glm-5.3-flash` | low |4096|
| Methodology | `deepseek/deepseek-v4.1-flash-1017` | high |8192|
| Ethics | `anthropic/claude-haiku-5.5` | medium |8192|
| Impact | `qwen/qwen3.8-flash` | reasoning max_tokens2048 |8192|
| Critical | `z-ai/glm-5.3-flash` | high |8192|
| Overview/answer coaching | `anthropic/claude-haiku-5.5` | high |8192|

Same-reviewer clarification/probes use the assigned reviewer model, low reasoning
for Methodology/Ethics/Critical and reasoning max_tokens1024 for Impact, within a
2048 total-output bound. Qwen's catalog advertises token-budget reasoning, not a
named effort. Actual selected-route support still requires account tests.

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

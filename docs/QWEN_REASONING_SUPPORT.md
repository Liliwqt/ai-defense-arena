# Qwen Impact reasoning experiment support

Verified against public first-party documentation on 2026-10-23. No paid request,
credential access or application setting change was needed for this research.
A subsequent separately approved [four-request experiment](../.scratch/defense-turn-responsiveness/reviews/08-impact-reasoning-results.md)
observed zero supplied reasoning tokens in both disabled-mode responses; that is
narrow live evidence, separate from the public documentation below.

## What Alibaba documents

For `qwen3.8-flash`, Alibaba's native API exposes `low`, `medium` and `xhigh`.
With only `thinking_budget` supplied, budgets 0–4096 map to `low`, 4097–16384 to
`medium`, and 16385–262144 to `xhigh`. Supplying both native effort and budget
is an error. Native `none` maps to `enable_thinking=False`. These rules are
upstream API semantics; they do not establish OpenRouter's exact adapter behavior.
[Alibaba Chat Completions reference](https://help.aliyun.com/en/model-studio/qwen-api-via-openai-chat-completions)

Consequently, both 2048 and 512 lie in the documented native low tier. A 2048→512
comparison cannot be described beforehand as a proven reduction in reasoning
intensity or actual generated tokens. The reference also calls `thinking_budget`
a maximum, but the cross-mapping leaves the precise practical effect of two
values in one tier to measurement.

Alibaba identifies this Flash model as hybrid thinking, enabled by default;
its native `enable_thinking=false` selects direct response behavior.
[Alibaba deep-thinking guide](https://www.alibabacloud.com/help/en/model-studio/deep-thinking)

## What OpenRouter establishes, and what it does not

OpenRouter offers a normalized `reasoning` object. Its guide describes mapping
reasoning-token budgets to `thinking_budget` for some Qwen models, explicitly
warning that support varies. It documents `enabled:false` as the normalized
disabled-thinking equivalent in its API translation table. `exclude:true` only
hides reasoning; it does not disable or avoid billing it. Actual reasoning usage
must be read from supplied usage fields, with missing values kept unknown.
[OpenRouter reasoning guide](https://openrouter.ai/docs/guides/best-practices/reasoning-tokens)

The public endpoint catalog currently lists `alibaba` and `alibaba/us-east-1`,
each advertising generic `reasoning`, structured output and `max_tokens` support.
Both advertise US$0.15/M prompt and US$0.47/M completion tokens. The generic
parameter list does not prove that either endpoint honors every nested reasoning
flag or that OpenRouter translates `enabled:false` to Alibaba's exact native
field. That translation remains an inference to test, rather than a verified
route-specific fact.
[OpenRouter endpoint catalog](https://openrouter.ai/api/v1/models/qwen/qwen3.8-flash/endpoints)

`require_parameters:true` restricts routing to supporting endpoints;
`allow_fallbacks:false` disables provider fallback. Retain those controls and
report any support rejection instead of silently replacing or dropping the
candidate setting. Keep the existing privacy and price filters too.
[OpenRouter provider selection](https://openrouter.ai/docs/guides/routing/provider-selection)

## Proposed bounded comparison

Use the same reconstructed synthetic English/Bisaya Impact inputs and identical
`qwen/qwen3.8-flash` model, Alibaba route excluding US-East, structured contract,
8192 output limit and 45-second deadline. Four requests compare:

| Condition | Requested OpenRouter reasoning |
| --- | --- |
| Existing baseline | `{"max_tokens":2048}` |
| Candidate direct response | `{"enabled":false}` |

Label these as **requested settings** until evidence establishes their effect.
Record admission/errors, elapsed time, valid grounded question, any supplied
reasoning-token usage and cost separately. Zero supplied reasoning tokens would
support the observed behavior of that request, not certify every future route.
Absent usage is unknown, not zero. Two languages and four requests cannot
establish general quality, full-defense speed or all-reviewer readiness.

No automatic fallback, retry, lookup expansion, native-field adaptation or
runtime promotion belongs in this controlled comparison. At research time the campaign required separate approval. It was subsequently
authorized/completed as linked above; any further paid experiment requires its
own concrete plan and approval.

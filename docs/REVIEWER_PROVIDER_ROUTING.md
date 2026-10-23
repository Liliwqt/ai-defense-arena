# Reviewer provider comparison

Research date: 2026-10-23. The catalog research used public official documentation
and an unauthenticated GET only. A later, separately authorized paid comparison
is recorded in [the results](../.scratch/defense-turn-responsiveness/reviews/08-provider-routing-results.md);
the historical research observations below are not inference evidence.

Prepare **current automatic routing versus the DeepInfra provider family** for
the same DeepSeek snapshot, preserving its question/interaction reasoning. Do
not promote either route based on catalog metadata. DeepSeek's own endpoint is
not a confirmed candidate for this app's strict structured-output contract.

## Endpoint snapshot

The public catalog returned 31 endpoints for
`deepseek/deepseek-v4.1-flash-1017`. Prices below are USD per million uncached
input/output tokens, converted from the API's per-token strings.

| Provider | Exact catalog tag | Input | Output | Catalog status | Schema support advertised |
|---|---|---:|---:|---:|---|
| OpenInference | `open-inference/fp4` | 0.070 | 0.500 | 0 | Yes |
| DeepInfra | `deepinfra/fp8` | 0.098 | 0.294 | 0 | Yes |
| DeepInfra | `deepinfra/fp8/priority` | 0.147 | 0.441 | 0 | Yes |
| DeepInfra | `deepinfra/fp8/flex` | 0.0784 | 0.2352 | -2 | Yes |
| DeepSeek | `deepseek` | 0.150 | 0.600 | 0 | No `structured_outputs` flag |

All listed rows advertise `response_format`, `reasoning`, `reasoning_effort`
and `max_tokens`. DeepInfra advertises a 51% discount; treat rates as a snapshot.
DeepSeek has scheduled price overrides up to 0.300/1.200. Listed token prices
fit the app's 0.300/1.200 ceilings. No request-price field was supplied; retain
the request-price ceiling of zero. All rows have null `latency_last_30m` and
`throughput_last_30m`; neither speed nor current privacy eligibility is known
from this response. [Public endpoint catalog](https://openrouter.ai/api/v1/models/deepseek/deepseek-v4.1-flash-1017/endpoints)

The ignored local snapshot is
`.local/provider-routing/deepseek-flash-endpoints-2026-10-23.json`, SHA-256
`621f6862e74e3b2f3794e2876fb668e0c3016edc34d4a87b3baa9fdff88bdfdc`.
Its companion `provenance-2026-10-23.json` records the public source and method.
These are catalog observations, not an authenticated preview of this account's
admissible routes. Numeric status values are retained without inventing their
meaning; the Flex row is excluded from an affirmative availability claim.

## Structured output and privacy constraints

The app sends `response_format.type=json_schema` with strict schemas. Generic
JSON formatting support is insufficient evidence of that capability. OpenRouter
documents endpoint-specific `structured_outputs` support and recommends
`require_parameters=true` with the schema request. It also cautions that actual
schema enforcement varies across implementations. Therefore DeepInfra is an
advertised candidate requiring a real contract test; DeepSeek's own endpoint
remains unconfirmed and should be left out of this unchanged-contract comparison.
Do not downgrade the request to JSON-only output to admit it.
[Structured outputs](https://openrouter.ai/docs/guides/features/structured-outputs)

Retain `data_collection=deny`. This is a router filter, not proof obtained by
the catalog GET that a particular endpoint will pass it. It is also not an
independent provider-policy audit or a zero-retention guarantee. OpenRouter
separately distinguishes its own opt-in input/output logging from request
metadata. No account settings were inspected here.
[Provider data policies](https://openrouter.ai/docs/guides/routing/provider-selection#requiring-providers-to-comply-with-data-policies),
[OpenRouter data collection](https://openrouter.ai/docs/guides/privacy/data-collection)

## Routing semantics

`provider.only=["deepinfra"]` selects the provider family. It does not establish
a particular quantization, tier or region. Base slugs match eligible variants;
the routing guide also describes special treatment of service-tier endpoints,
including open-weight priority routes. Use a family-level claim and record the
returned provider. If only its name is returned, the exact endpoint remains
unknown. Keep `allow_fallbacks=false`, parameter/privacy filters and all price
limits. If no route satisfies them, report the failure rather than relaxing
the contract. Sorting by throughput or latency is another experiment, not proof
that the complete application transition will meet its deadline.
[Provider routing](https://openrouter.ai/docs/guides/routing/provider-selection)

## Application boundary and proposed comparison

In the current source, `RunQuestionPolicy.provider_only` is passed through
`OpenRouterRun._dispatch` for **every** dispatched model, including the GLM
planner and other reviewers. Setting that field to DeepInfra globally would
change more than the DeepSeek stage and could make unrelated stages unroutable.
Keep runtime policy unchanged. A benchmark-only interceptor should apply the
family restriction only when the exact DeepSeek snapshot is requested, capture
that decision, and leave GLM/Haiku/Qwen routing untouched.
[Policy and dispatch](../backend/openrouter_questions.py),
[Guarded request body](../backend/openrouter_stream.py)

Prepare four mini-runs: the same English and Bisaya cases under current automatic
routing and under DeepInfra-only DeepSeek routing. Preserve synthetic inputs,
model IDs, reasoning, limits, validation, retry policy and the 45-second window.
Keep a single conservative campaign allowance, including dispatched requests
without final usage receipts. This is a small diagnostic comparison, not proof
of all-role quality or general latency performance.

Record accepted questions/answers, failed stages, total transition time, request
time, actual provider if supplied, citation validity, cost receipts and unknown
cost holds. Review grounded questions and follow-ups separately from timing.
Automatic routing might itself select DeepInfra; such a result does not form
a clean two-provider comparison and must be identified honestly. The providers
can serve different quantizations, so attribute any observed difference to the
route as a whole rather than isolating hardware or provider identity as a cause.

No new paid campaign is authorized by this research note. The previous campaigns
are finished; a prepared comparison needs its own bounded spending authorization.
No runtime model/provider setting, deployment or live-readiness claim follows
from this preparation.

## Prepared local pilot

The benchmark now supports a model-scoped comparison without changing runtime
policies. Inspect it without credentials or inference:

```bash
.venv/bin/python -m tests.reviewer_benchmark --plan --provider-comparison \
  --cases quantitative-en qualitative-bisaya
```

The captured plan is
[08-provider-routing-plan.json](../.scratch/defense-turn-responsiveness/reviews/08-provider-routing-plan.json).
It contains four mini-runs, with a conservative ordinary request bound of
**US$1.047946800**. Proposed campaign admission ceiling: **US$1.25**, including
retry/lookup requests; admission may stop the campaign early. This bound is not
an expected or final bill. The user subsequently approved this exact US$1.25 campaign; all four runs
completed. See the linked results for mixed timing, application-validation failures
and the separate Qwen429 blocker. This campaign approval is now consumed; do not
reuse any completed campaign's approval or ledger.

Both conditions capture identical models, reasoning, output limits, sources and
answer scripts. Only DeepSeek requests in `provider-deepinfra` gain
`provider.only=["deepinfra"]`; the GLM planner and other reviewer models keep
current routing. The observer stores the routing map with the campaign allowance
and rejects attempts to reopen that identity with a different map. It records
`requested_provider` separately from the actual provider reported in a stream;
a request selector does not prove the route used or the exact endpoint variant.
Missing usage receipts retain conservative holds. Existing price/privacy guards
run before reservation and dispatch.

The ignored prepared launcher is
`.local/provider-routing/run-provider-comparison.py`. It requires an explicit
execution flag, checks the frozen three-file benchmark hashes and exact prepared
plan before loading the named local key, and refuses an existing output directory.
It is not a source of spending authorization. A fresh approved execution must
retain all original evidence and review the observed routes, schemas, grounding,
45-second failures, complete transition times and unknown costs before selecting
any settings. Automatic routing can choose DeepInfra too; in that case there is
no demonstrated comparison of distinct providers.

Verification: four new HTTP-mocked routing tests passed; the final isolated full
Python suite passed **856 tests in 193.830 seconds**, with external providers
mocked. The frozen source hashes and credential-free plan match the prepared
artifact. That gate was offline-only. The later authorized provider observations are
recorded separately in the linked results; no frontend/native/hosted check,
independent code-review completion or runtime settings promotion is claimed.

The subsequent [complete-candidate campaign](../.scratch/defense-turn-responsiveness/reviews/08-complete-candidate-results.md)
reached all four reviewer questions once, but DeepInfra's later three opening
writers explicitly reported upstream shared-pool429 with no Retry-After. Its
successful request latency does not establish dependable capacity. No routing
restriction or automatic provider fallback was promoted.

# DeepSeek shared-capacity follow-up

Research snapshot: **2026-10-23, 12:58 UTC**. This is public documentation and
unauthenticated catalog research. No inference, account inspection, key reads,
credential changes or runtime promotion took place.

The smallest useful next candidate is the **same DeepSeek snapshot through
`inference-net/fp8`**, keeping prompts, high writer reasoning, strict schemas,
deadlines and spending/privacy guards unchanged. Treat this as a proposed
controlled experiment, not an established capacity or speed improvement.

## What the failed campaign establishes

Three opening writers in the [complete-candidate campaign](../.scratch/defense-turn-responsiveness/reviews/08-complete-candidate-results.md)
returned HTTP429 with `limit_source=upstream_provider_shared_pool`,
`error_provider=DeepInfra`, and no Retry-After. That identifies those requests'
reported failure category. It does not establish this user's direct DeepInfra
quota, an OpenRouter daily limit, exact serving endpoint, or a permanent outage.
There was no successful serving receipt for those failures.

DeepInfra documents both an account concurrency limit and occasional busy-model
429s below that limit. Its published default of 200 concurrent requests per model
belongs to direct provider accounts; it must not be assigned to an OpenRouter
shared pool or this user without account evidence. Its general advice to retry
does not override the app's stricter rule requiring a short Retry-After for an
automatic429 retry. [DeepInfra rate limits](https://docs.deepinfra.com/account/rate-limits)

## Exact same-model candidates

Model: `deepseek/deepseek-v4.1-flash-1017`. The public response contained
33 endpoints. Selected rows below advertise `structured_outputs`,
`response_format`, `reasoning`, `reasoning_effort` and `max_tokens`.
Prices are USD/M uncached input/output; status is an uninterpreted catalog value.

| Exact tag | Input | Output | Quantization | Status |
| --- | ---: | ---: | --- | ---: |
| `inference-net/fp8` | 0.080 | 0.500 | fp8 | 0 |
| `inference-net/us` | 0.080 | 0.500 | fp8 | 0 |
| `deepinfra/fp8` | 0.098 | 0.294 | fp8 | 0 |
| `deepinfra/fp8/priority` | 0.147 | 0.441 | fp8 | -2 |
| `deepinfra/fp8/flex` | 0.0784 | 0.2352 | fp8 | 0 |
| `relace` | 0.070 | 0.500 | unknown | 0 |
| `open-inference/fp4` | 0.070 | 0.500 | fp4 | 0 |
| `morph/fp8` | 0.054 | 0.600 | fp8 | 0 |
| `cloudflare` | 0.100 | 0.600 | unknown | 0 |
| `sail-research/fp4` | 0.101 | 0.150 | fp4 | 0 |

The catalog did not supply request prices or current latency/throughput values.
InferenceNet advertises 1,040,000 context and 393,216 maximum completion tokens;
DeepInfra 1,048,576 and 131,072. DeepSeek's own `deepseek`, `novita/fp8` and
`baseten` lack the structured-output flag. Alibaba's base .330/1.320 rates
exceed the guards and its row also lacks that flag. [Endpoint catalog](https://openrouter.ai/api/v1/models/deepseek/deepseek-v4.1-flash-1017/endpoints)

The retrieved JSON SHA-256 was
`12ec4c1718537ff4d5acf8cec078975e11af148887f4ada379361f88b3e6e211`.
This note retains selected fields, not the raw response. The earlier
[31-endpoint snapshot](REVIEWER_PROVIDER_ROUTING.md) remains historical;
refresh metadata before any new paid campaign. Neither a zero status nor recent
uptime proves available capacity for a particular request. Earlier public reads
within this research also showed changing Morph prices/status, so those fields
are expressly snapshots.

## Guard-preserving routing

For a benchmark request to the exact DeepSeek model, propose:

```json
{
  "provider": {
    "only": ["inference-net/fp8"],
    "allow_fallbacks": false,
    "require_parameters": true,
    "data_collection": "deny",
    "max_price": {"prompt": 0.30, "completion": 1.20, "request": 0}
  }
}
```

Use model-scoped interception, preserving other reviewers' routing. The global
runtime `provider_only` field affects every model and is the wrong place for
this experiment. Retain the ordinary strict JSON-schema body and all domain and
source-citation validation. No request-price field in the public response is
permission to remove the zero request-price ceiling.

Exact slugs distinguish variants; base slugs can match several eligible
endpoints. A provider-only restriction is different from an ordered preference,
which may permit unlisted providers unless fallback is disabled. Keep privacy
and parameter filters even if they leave no eligible route. The public GET does
not establish that this account's request will pass `data_collection=deny`,
nor does that filter mean zero retention. [Provider routing](https://openrouter.ai/docs/guides/routing/provider-selection)

InferenceNet is preferable for the first comparison because it keeps advertised
fp8 while changing provider. `inference-net/fp8` does not claim a physical region;
`inference-net/us` explicitly changes the regional selector. Equal advertised
quantization still does not isolate hardware, kernels or implementation. Relace
is a secondary candidate, with unknown advertised quantization. OpenInference's
earlier invalid automatic plan is application-validation evidence, not proof
that its transport or schema enforcement caused that failure.

## Priority and Flex

DeepInfra says priority changes queue position/admission at 1.5 times standard
price; actual application is indicated by the echoed service tier. It also says
unsupported priority requests can run at default tier. That is a provider
description, not an SLA for this routed snapshot. [DeepInfra priority service](https://deepinfra.com/blog/priority-service-tier)

OpenRouter supports explicit tier slugs and top-level `service_tier`; an explicit
priority request can otherwise fall back to standard. Open-weight priority
endpoints can participate in ordinary routing, so previous `only=["deepinfra"]`
requests do not identify standard versus priority from a provider name alone.
For a tier comparison use the full `deepinfra/fp8/priority` slug and keep fallback
disabled, rather than quietly changing the eligible pool. Its recorded -2 status
prevents an affirmative availability recommendation here. Flex has lower
processing priority and is a weak first choice for a strict interactive deadline.
[OpenRouter service tiers](https://openrouter.ai/docs/guides/features/service-tiers)

## BYOK is a separate account and accounting change

OpenRouter describes BYOK as using the provider account's limits and billing.
It can separate traffic from shared OpenRouter credentials, but cannot guarantee
that the underlying model has spare capacity. Adding a direct DeepInfra key is
not an approved or necessary step for the smallest experiment.

BYOK shared-capacity fallback has separate account controls. A prioritized key
may fall back to shared capacity unless that is explicitly disabled for the
relevant models/provider; request `allow_fallbacks=false` alone is not evidence
that shared credential fallback is disabled. Existing data policies still apply.
Default OpenRouter guardrail/workspace budgets exclude BYOK inference spend;
including it needs a separate budget setting. Provider billing plus any
applicable OpenRouter BYOK fee must be reconciled before claiming that the app's
current receipt accounting covers both. The docs currently describe a 5% fee and
plan-dependent allowance, not proof of this account's allowance. No settings
were inspected or changed. [OpenRouter BYOK](https://openrouter.ai/docs/guides/overview/auth/byok)

## Smallest next measurement and limits

Prepare four opening-writer probes: the same saved synthetic English and Bisaya
planner selections through exact `deepinfra/fp8` and `inference-net/fp8`, in
counterbalanced order. Reuse already validated synthetic plans; do not repay for
mapping or planning. Hold model, prompt, high reasoning, schema, output bound,
45-second deadline and filters fixed. Verify selection, exact citations, actual
provider/tier where reported, failure metadata, elapsed time and usage receipts.
Preserve full conservative holds for absent receipts.

Two observations per route can decide whether an alternate is worth a larger
comparison; they cannot prove dependable capacity, full-defense quality or a
10–15-second complete transition. A failed privacy/parameter admission is a
failed gate, not a reason to weaken the request. Fix Critical's separately
unclassified rejection before attempting another complete defense, so an
unrelated known blocker does not consume a broader campaign.

This recommendation is research only. **No new paid experiment is authorized.**
Previous approvals are completed campaigns. A concrete frozen probe plan and
fresh bounded spending approval are required before dispatch. Runtime settings,
private quotas, account balances, current capacity, hosted behavior and
production readiness remain unverified.

Verification: primary-source public GETs and documentation reading only; no
application tests were needed for this Markdown note. Root session owns the
shared project-log update.

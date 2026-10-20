# OpenRouter mapping speed research

Checked: 2026-10-20. Scope: public model/endpoint metadata and official documentation; no inference, API keys, account changes, or uploaded paper text were accessed by this research task. Prices and availability are snapshots, not promises.

Subsequent user choice: try `z-ai/glm-5.3-flash`. New Standard mapping preparations
now select GLM with low reasoning; DeepSeek remains an explicit operator rollback.
This implementation choice is not a completed live benchmark. The comparison
and initial recommendations below record the research that preceded the choice.

## Recommendation

First try **mapping-only `reasoning.effort: "low"` on `deepseek/deepseek-v4.1-flash-1017`**, preserving the selected model, full paper input, validation, 65,536-token completion allowance, and privacy/price guards. Its catalog explicitly supports `max`, `high`, `low`, and `none`, defaults to `high`, and does **not** advertise `reasoning.supports_max_tokens`. Consequently, describe this as lower reasoning effort, not a hard reasoning-token budget. [OpenRouter catalog](https://openrouter.ai/api/v1/models)

If a separate model experiment is desired, **`inception/mercury-3` is the first candidate**: its endpoint advertises 1,000,000 context tokens, 131,072 completion tokens, schema output and reasoning effort; its current price is $0.10/$0.35 per million input/output tokens. [Mercury 3 endpoints](https://openrouter.ai/api/v1/models/inception/mercury-3/endpoints) Its published provider P50 is 204 tokens/sec with 0.68-second latency. These are aggregate routing statistics, not a mapping benchmark. [Mercury 3 provider statistics](https://openrouter.ai/inception/mercury-3)

Keep any switch explicit and scoped to a new preparation; do not introduce automatic model fallback. Neither lower-effort DeepSeek mapping quality nor candidate-model mapping quality/speed has been established by this investigation.

## Evidence and its limits

The parent session supplied an existing account observation of approximately 23,651 input tokens and 11,546 output tokens at 130.2 tokens/sec. Dividing output by reported throughput gives about **88.7 seconds of output generation**, before other work; this supports investigating the old 90-second application cutoff. This is arithmetic on supplied account metadata, not a fresh request or complete end-to-end measurement. The locally increased 300-second deadline removes that application rejection threshold; it does not make inference faster.

Catalog capabilities describe eligibility. Endpoint `latency_last_30m` and `throughput_last_30m` were null in the fetched candidate JSON; the figures below come from OpenRouter model-page **P50 provider rows**, with their displayed “All” reasoning setting where present. They are a different population from the supplied account request. Privacy, parameter, context and price filters can remove the fastest displayed provider. [DeepSeek endpoints](https://openrouter.ai/api/v1/models/deepseek/deepseek-v4.1-flash-1017/endpoints), [Mercury 3 endpoints](https://openrouter.ai/api/v1/models/inception/mercury-3/endpoints)

## Shortlist under the existing price caps

Caps supplied by the parent task: input at most $0.30/M, output at most $1.20/M, no request fees, required JSON Schema output and `data_collection: "deny"`. API pricing strings are **USD per token**: multiply by 1,000,000 for the table. Selected endpoint prices can differ from the catalog's representative price.

| Exact model ID | Example eligible endpoint; input/output USD per million | Endpoint context / max completion | Published provider P50 throughput / latency | Assessment |
| --- | --- | --- | --- | --- |
| `deepseek/deepseek-v4.1-flash-1017` | `inference-net/fp8`; $0.08 / $0.50 | 1,040,000 / 393,216 | inference.net: 180 tps / 0.49 s | Same-model lower effort is the smallest experiment. [Endpoint capabilities](https://openrouter.ai/api/v1/models/deepseek/deepseek-v4.1-flash-1017/endpoints), [statistics](https://openrouter.ai/deepseek/deepseek-v4.1-flash-1017) |
| `inception/mercury-3` | `inception`; $0.10 / $0.35 | 1,000,000 / 131,072 | Inception: 204 tps / 0.68 s | Best first explicit switch candidate while retaining a roughly million-token context. [Endpoint capabilities](https://openrouter.ai/api/v1/models/inception/mercury-3/endpoints), [statistics](https://openrouter.ai/inception/mercury-3) |
| `inception/mercury-2.5` | `inception`; $0.04 / $0.15 | 260,000 / 65,536 | Inception: 208 tps / 0.49 s | Cheap; only a small published throughput edge over Mercury 3 and substantially less context. [Endpoint capabilities](https://openrouter.ai/api/v1/models/inception/mercury-2.5/endpoints), [statistics](https://openrouter.ai/inception/mercury-2.5) |
| `z-ai/glm-5.3-flash` | `modal/nvfp4`; $0.15 / $0.50 | 1,048,576 / 943,718 | Modal: 201 tps / 0.45 s | Plausible alternative; default reasoning is `max`, so configure `low` explicitly. [Endpoint capabilities](https://openrouter.ai/api/v1/models/z-ai/glm-5.3-flash/endpoints), [statistics](https://openrouter.ai/z-ai/glm-5.3-flash) |
| `qwen/qwen3.8-flash` | `alibaba`; $0.15 / $0.47 | 1,000,000 / 131,072 | Alibaba: 39 tps / 2.47 s | Supports a numeric thinking budget, but no effort selector is advertised; weaker speed case and no entry in the checked ZDR list. [Endpoint capabilities](https://openrouter.ai/api/v1/models/qwen/qwen3.8-flash/endpoints), [statistics](https://openrouter.ai/qwen/qwen3.8-flash), [ZDR list](https://openrouter.ai/api/v1/endpoints/zdr) |

The selected example endpoints advertise `response_format` and `structured_outputs`; the first four also advertise `reasoning_effort`. Their fetched pricing objects contain no per-request charge field. This is metadata screening, not proof that this account can currently route an actual application schema to them; preserve the runtime no-request-fee guard. [DeepSeek](https://openrouter.ai/api/v1/models/deepseek/deepseek-v4.1-flash-1017/endpoints), [Mercury 3](https://openrouter.ai/api/v1/models/inception/mercury-3/endpoints), [Mercury 2.5](https://openrouter.ai/api/v1/models/inception/mercury-2.5/endpoints), [GLM](https://openrouter.ai/api/v1/models/z-ai/glm-5.3-flash/endpoints), [Qwen](https://openrouter.ai/api/v1/models/qwen/qwen3.8-flash/endpoints)

Mercury 3's displayed 50% discount makes its current rate $0.10/$0.35; the displayed undiscounted $0.20/$0.70 also fits these caps. Mercury 2.5's displayed undiscounted $0.20/$0.75 also fits. Do not budget against discounts remaining available. [Mercury 3 pricing](https://openrouter.ai/inception/mercury-3), [Mercury 2.5 pricing](https://openrouter.ai/inception/mercury-2.5)

## Reasoning, schema, and privacy compatibility

The catalog reports Mercury 3 and 2.5 efforts `high`, `medium`, `low`, `none` (default `medium`); GLM 5.3 Flash reports `max`, `high`, `low` (default `max`, mandatory reasoning). Qwen 3.8 Flash advertises `supports_max_tokens: true` and omits `supported_efforts`. Do not blindly reuse DeepSeek effort settings across all models. [Catalog reasoning metadata](https://openrouter.ai/api/v1/models)

OpenRouter documents that `reasoning.max_tokens` is translated to effort for effort-only models. `reasoning.exclude: true` hides reasoning without stopping its generation or billing. On most providers, the top-level completion allowance covers reasoning and visible output together; too small an allowance can produce an empty or truncated answer. A low-effort setting is therefore preferable to prematurely reducing the current completion allowance. [Reasoning controls](https://openrouter.ai/docs/guides/best-practices/reasoning-tokens)

Retain `response_format.type: "json_schema"`, `json_schema.strict: true` and `provider.require_parameters: true`, followed by application validation. OpenRouter warns that native strict enforcement varies between providers; an advertised `structured_outputs` flag alone does not establish exact constrained decoding for this schema. The first-party DeepSeek endpoint lacks that flag even though several third-party DeepSeek endpoints advertise it. [Structured output guidance](https://openrouter.ai/docs/guides/features/structured-outputs), [DeepSeek endpoint flags](https://openrouter.ai/api/v1/models/deepseek/deepseek-v4.1-flash-1017/endpoints)

The public ZDR endpoint list includes `inception` for both Mercury candidates, `modal/nvfp4` and `coreweave/nvfp4` for GLM, and `inference-net/fp8` for DeepSeek. It contains no `qwen/qwen3.8-flash` endpoint at the time checked. This supports the first four privacy candidates; absence from ZDR alone does not establish whether Qwen passes the separate no-collection filter. [OpenRouter ZDR endpoint API](https://openrouter.ai/api/v1/endpoints/zdr)

Keep `data_collection: "deny"`. OpenRouter describes this as routing only to providers that do not collect user data; `zdr: true` is a separate enforcement setting for zero retention. Provider defaults and individual endpoint policies can differ. Retain existing account restrictions; do not relax privacy to obtain a faster route. [Provider routing](https://openrouter.ai/docs/guides/routing/provider-selection), [ZDR policy](https://openrouter.ai/docs/guides/features/zdr)

## Gemini comparison

Standard `google/gemini-3.1-flash-lite` costs $0.25/$1.50 per million, exceeding the completion cap. Its displayed AI Studio Flex $0.125/$0.75 fits price alone, while Vertex Flex shows 17.67-second latency and 30 tps; these are different service tiers and require separate privacy/route validation. [Gemini 3.1 Flash Lite](https://openrouter.ai/google/gemini-3.1-flash-lite)

`google/gemini-3.5-flash-lite` costs $0.30/$2.50; even its displayed Flex output rate of $1.25 exceeds $1.20. `google/gemini-3.5-flash` is $1.50/$9.00. Neither is a cap-preserving default candidate. [Gemini 3.5 Flash Lite](https://openrouter.ai/google/gemini-3.5-flash-lite), [Gemini 3.5 Flash](https://openrouter.ai/google/gemini-3.5-flash)

`google/gemini-2.5-flash-lite` is inexpensive at $0.10/$0.40, but the catalog marks its expiration date **2026-10-20**, the research date. Do not select it for a new durable integration without rechecking retirement and endpoint availability. [Catalog expiration metadata](https://openrouter.ai/api/v1/models), [model page](https://openrouter.ai/google/gemini-2.5-flash-lite)

## Next validation

Use the same authorized representative paper and exact schema for DeepSeek high versus low, then an explicitly selected Mercury 3 experiment if requested. Record wall-clock mapping time, selected provider, reasoning and visible token counts, finish reason, schema failures, source coverage, exact citation validity and mapping usefulness. Check long-paper behavior separately before accepting smaller-context models. This investigation neither ran those comparisons nor established a quality ranking; published model benchmarks are not paper-mapping evaluations.

Verification: live read-only HTTP GETs of public OpenRouter catalog, five endpoint APIs, provider directory and ZDR endpoint API; official documentation/model pages inspected. No live inference or hosted application verification. Inception's official documentation index links structured-output/reasoning/privacy pages, but their detailed contents were inaccessible through the available fetch methods, so no first-party native strict-mode guarantee is claimed. [Inception documentation index](https://docs.inceptionlabs.ai/llms.txt)

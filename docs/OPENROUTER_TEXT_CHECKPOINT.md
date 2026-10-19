# OpenRouter text checkpoint — local evidence and remaining gates

Recorded2026-10-20. Text routing/cleanup is local; this checkpoint is not yet
rollout-ready or a passed speech dependency. Actual provider evidence must not be
inferred from offline contracts, catalog metadata or conservative estimates.

## Offline capacity observations

Reproduce without keys/network/provider requests:

```bash
.venv/bin/python -m tests.openrouter_capacity
```

The runner serializes real shared coaching prompts for synthetic accepted source
sizes and4/12/100 answers, each with4000 answer characters and4000 probe-reply
characters. It records the current Start estimate, protected reserve and exact
serialized overview input bound. This overview probe omits a real run's full
map/coverage context; those add further input. UTF-8 byte bounds are conservative
token bounds, not measured tokenizer counts. No USD figure below is a live bill.

| Source bytes | Questions | Conservative Start estimate USD | Fits default USD5 Start ceiling? | Overview input bound |
| --- | --- | --- | --- | --- |
|5000|4|0.3362976|Yes|62594|
|5000|12|1.6543008|Yes|131237|
|60000|12|2.9083008|Yes|186237|
|300000|12|8.3803008|No|426237|
|600000|4|5.3342976|No|657594|
|600000|100|186.2517504|No|1481543|

The largest case also exceeds the1M conservative context gate before output.
The current defaults therefore do not promise every upload/question-budget
combination. A source accepted for extraction can still be refused at Start;
the app names the budget/reserve/ceiling problem and retains the material.
Increasing a ceiling cannot override request context or routing-price controls.
No default was raised and no source was silently truncated based on this probe.

## Public metadata check

The [official catalog](https://openrouter.ai/api/v1/models), retrieved2026-10-20,
lists the selected IDs with structured-output parameters. DeepSeek offers high/
low efforts, GLM mandates reasoning and names high/low, Haiku names medium/high,
and Qwen advertises an explicit reasoning-token budget without named efforts.
This supports testing the proposed settings; it does not prove a selected route
will accept the schema, privacy filters, streaming or sufficient output capacity.

Haiku's catalog includes a higher tier at100000 prompt tokens, USD0.50/M input
and USD2.50/M output. Both exceed current route caps USD0.30/M and USD1.20/M.
A large prompt may therefore have no eligible route under the unchanged policy.
This is a pending affordability/compatibility gate. It does not authorize a
higher cap, different model, lower research scope or changed defense price.
See [routing filters](https://openrouter.ai/docs/guides/routing/provider-selection)
and [reasoning/output accounting](https://openrouter.ai/docs/guides/best-practices/reasoning-tokens).

## Required actual-provider evidence

No OpenRouter key was available to the implementing process. The user confirmed
“Not configured; finish offline checks first.” No paid inference was attempted.
Keep these gates pending until an operator provides a configured local route:

1. Test exact chosen account/routes, structured schemas, streaming and reasoning,
   especially Qwen token budgeting and mandatory GLM effort.
2. Compare the same synthetic papers/answers across reviewers, including different
   fields and English/modern Bisaya. Record useful/unsupported dialogue separately
   from schema success.
3. Record actual prompt/output/reasoning usage, route tier, cost and latency for
   mapping, both question stages, interactions, failed/retried requests and full
   overview/answer cards. Do not bill reasoning output twice.
4. Exercise large accepted papers, long answers/probes and required long reports;
   prove enough visible output remains after reasoning. Reconcile unknown usage.
5. Decide measured numeric limits and any explicit price-route change before
   rollout. Report a failed compatibility/affordability gate instead of silently
   substituting another model or changing credit pricing.

The independent ticket06 review records full offline/database/browser evidence.
Ticket06 remains incomplete while these actual-model/numeric gates are pending;
voice stays off and07–12cannot bypass their dependencies. No publication or
hosting change follows from this document.

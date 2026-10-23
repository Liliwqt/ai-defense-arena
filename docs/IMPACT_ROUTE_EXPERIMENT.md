# Focused Impact-route experiment

Prepared and separately authorized/executed 2026-10-23 under a **US$0.15 cap**.
[Actual results](../.scratch/defense-turn-responsiveness/reviews/08-impact-probe-results.md):
both excluding-US-East probes succeeded in21–22s; both US-East probes reported
Alibaba upstream shared-pool429. Defaults remain unchanged; further paid work
needs a new prepared campaign approval.
The previous four-run comparison is complete; its remaining nominal allowance
is not reused. Runtime defaults remain unchanged, and ticket08's actual-provider
gate remains failed/incomplete4/7.

## Why this comes first

Both DeepInfra comparison runs reached the Qwen Impact question writer and got
HTTP429. The old observer preserved status but discarded the error metadata,
so the historical cause cannot be identified offline. It might be an upstream
limit, an OpenRouter/account limit or route-specific behavior; none is established.
The later authorized probes supply that missing signal for their own failures: both
US-East requests explicitly reported upstream_provider_shared_pool and Alibaba.
They cannot retrospectively identify the original automatic-route failures.
HTTP-mocked tests only verify diagnostic capture, not an upstream fix.

OpenRouter documents typed error metadata and a `Retry-After` signal. The new
benchmark observer keeps a bounded diagnostic subset: HTTP status, numeric error
code, recognized error type/limit-source/provider labels and a bounded retry delay.
It discards arbitrary messages, raw errors, unknown strings, user/account fields
and headers. Error attribution stays separate from a serving provider identity.
[Official error documentation](https://github.com/OpenRouterTeam/docs/blob/main/api_reference/errors-and-debugging.mdx),
[official credit/rate limits](https://openrouter.ai/docs/api_reference/limits)

## Public route observations

The unauthenticated catalog currently lists two endpoints for
`qwen/qwen3.8-flash`: `alibaba` and `alibaba/us-east-1`. Both advertise strict
structured outputs, response formatting, reasoning and the existing token limits,
with listed uncached token prices of US$0.15/M input and US$0.47/M output, within
the current caps. Speed metrics are null. This is advertised metadata, not proof
of account privacy eligibility, capacity or actual schema compliance.
[Official endpoint catalog](https://openrouter.ai/api/v1/models/qwen/qwen3.8-flash/endpoints)

Both routes belong to Alibaba; this experiment does not compare two independent
provider companies. A base slug also matches its regional variants. Therefore
one condition requests `only=["alibaba"]` with
`ignore=["alibaba/us-east-1"]`; the other requests
`only=["alibaba/us-east-1"]`. The first excludes that listed region rather than
claiming an exact location. If only the name Alibaba is reported, actual endpoint
identity remains unknown. Existing no-fallback, parameter/privacy and price filters
remain intact. An unavailable route is a result, not permission to relax them.
[Official routing documentation](https://openrouter.ai/docs/guides/routing/provider-selection)

## Four single-stage probes

| Reconstructed synthetic case | Route conditions | Requests |
| --- | --- | ---: |
| Quantitative English | Alibaba excluding US-East; Alibaba US-East | 2 |
| Qualitative with Bisaya answers | Same conditions, reversed order | 2 |

Use the accepted synthetic history and saved Impact plan from the previous
comparison. Preparation runs the real funded question builder with an offline
transport to capture **only the reconstructed Impact request**. No interpretation,
planner, mapping, prior reviewer or coaching inference is replayed. The fixture
contains only selected synthetic displayed questions, saved plan/coverage and
built-in answer indices. Its case fingerprint is checked. A stable synthetic map
ID makes repeated request hashes reproducible; the original HTTP request bytes
were not retained, so this is not an exact byte replay of the old request.

Within each case, all prompt/schema/context/model/reasoning/output values match;
only routing selectors change. Keep Qwen reasoning at **2048 tokens**, output at
**8192 tokens** and a **45-second single-stage processing window**. This measures
a diagnostic writer, not answer-to-next-question latency or the complete defense.
There is no automatic retry, additional lookup request or model switch. A requested
lookup is reported without spending on expansion. Source citations and the saved
selection are validated through existing domain rules before a success is recorded.

## Bounds and execution gate

[Captured plan](../.scratch/defense-turn-responsiveness/reviews/08-impact-probe-plan.json)
and [synthetic saved-state fixture](../.scratch/defense-turn-responsiveness/reviews/08-impact-probe-fixtures.json).
Four conservative request reservations total **US$0.089341200**. Separately approved
campaign admission cap: **US$0.15**, now completed. This is not an expected/final bill. Every
request must fit the persistent campaign allowance; missing receipts retain their
holds. A timeout does not prove remote cancellation or no billing. Preserve old
ledgers and use a new output directory.

Inspect without credentials or inference:

```bash
.venv/bin/python -m tests.impact_route_probe --plan
.venv/bin/python -m unittest tests.test_impact_route_probe -v
```

Only after separate spending approval, the ignored frozen launcher
`.local/impact-probe/run-approved-probes.py --execute-approved` checks its source
hashes and exact plan before loading only the named local key and executing the
fixed four-request probe. It rejects existing output. It neither authorizes itself
nor sends keys through arguments or chat. Results include safe request diagnostics,
parsed synthetic questions/citations, elapsed time, failures, unknown usage and
funding/in-flight state. A failed or incomplete gate remains explicit.

Seven focused HTTP-mocked checks pass, including successful citation/domain
validation, no retry after429, privacy filtering for JSON/SSE errors, unknown and
oversized-body handling, unchanged non-route payloads and reproducible plan hashes.
The first diagnostics tests failed before capture was added, and a separate
reproducibility test caught random map IDs before the stable synthetic ID fixed it.
Final isolated `.venv/bin/python -m unittest discover -v` passed **863 tests
in 200.281 seconds**, with AI/Google/payments mocked. Frozen source hashes and
repeated credential-free plans match. No frontend code changed; prior414React/build
and26localPostgreSQL checks remain separate and were not rerun. Those offline checks establish no provider root cause. The linked live results
record a newly observed upstream-limit signal separately; no human language review,
hosted/native readiness or settings promotion is claimed.

After this route check, lower interactive reasoning can be tested in a separate
comparison. Combining those changes now would obscure which change helped.

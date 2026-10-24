# Recovering unavailable mapping routes

The observed failures on 2026-10-25 were Standard GLM 5.3 Flash through Darkbloom
and Free Xing4 through Phala, both returning HTTP 429. The Activity screenshot also
contains a Standard HTTP 400 whose detail has not been inspected. These records
do not prove a global outage or identify the exact cause of that 400.

The message correction in `4e40b07` did not change providers. The subsequent local
routing correction sends **new Standard GLM preparations to DeepInfra**, while
keeping the same GLM model, low reasoning, source/schema validation and allowance.
The public endpoint catalog advertises the required reasoning/structured-output
parameters and prices below the existing routing caps. Actual account access and
successful mapping need separate evidence.

## Standard configuration

`OPENROUTER_MAPPING_PROVIDER` selects the provider for new Standard preparations:

| Value | Behavior |
| --- | --- |
| `deepinfra` | Use only DeepInfra; default for GLM mapping. |
| `wafer` | Use only Wafer. |
| `z-ai` | Use only Z.AI. |
| `auto` | Use the preceding unpinned provider selection. |

If `OPENROUTER_MAPPING_MODEL` selects the legacy DeepSeek model, its default
remains `auto`; an explicit provider setting still applies. A provider must serve
the selected model and pass the existing price, parameter and account/privacy
filters. There is no automatic model or provider fallback. The app still sends
`data_collection: deny`, requires structured-output parameters and preserves the
maximum input/output prices.

After deployment, create a new room/preparation to use a changed provider.
Retrying an existing preparation preserves its saved route, model and allowance;
configuration changes do not refill spending or request limits. Streamlit also
requires a new preparation scope. This setting affects mapping only: the
planner and Critical Judge question calls that use GLM are pinned separately to
DeepInfra in `backend/openrouter_questions.py` (their auto route, Darkbloom,
also returned 429), while other reviewers and coaching keep their existing
routes.

On Render, use the default DeepInfra route or set the variable explicitly, then
deploy the correction. This document does not establish that deployment happened
or that a user’s paper will map successfully. Do not repeatedly retry a persistent 429: inspect
its Activity entry and `limit_source`, and honor any provider retry interval.

## Free tier and live checks

The preceding Free Xing model has only Phala in its public endpoint catalog.
A separate synthetic check selected `dots-studio/dots-3-note-preview:free` through
`atlas-cloud`, with zero-price routing, strict schema and no-collection filtering.
It returned a source-validated map, so new Free policies now use that pair and its
512,000-token context. Existing Xing policies retain their original 262,144-token context,
model/provider and quotas. No paid upgrade or collection-policy relaxation occurs.
See [Free practice](FREE_PRACTICE.md). Create a fresh room after deployment.

The user approved one campaign with an admission cap of US$0.10, three requests and
no automatic retries. Only a short synthetic pilot paper was used:

| Request | Result | Seconds | Reported cost |
| --- | --- | ---: | ---: |
| Standard GLM / DeepInfra | Valid 6-topic map | 136.604 | US$0.00091975 |
| Free Flint / Recursive | HTTP 404: no compatible endpoint | 0.576 | Unavailable; conservative local hold retained |
| Free Dots / AtlasCloud | Valid 6-topic map | 85.653 | US$0 |

The conservative paid admission bound was US$0.0843027. Free requests enforced
zero-price fences; the failed request's missing receipt is not assumed free in
local accounting. No additional campaign or retry is implied. The two successful
small maps establish only those exact route/request observations. They are slow,
not evidence of a latency improvement or full-defense quality/load readiness.
Actual user paper, hosted deployment and installed-device checks remain separate.

Sources checked on 2026-10-25: [GLM endpoints](https://openrouter.ai/api/v1/models/z-ai/glm-5.3-flash/endpoints),
[Xing Free endpoints](https://openrouter.ai/api/v1/models/xingchen-agi/xing4.0-29b-a4b:free/endpoints),
[Dots Free endpoints](https://openrouter.ai/api/v1/models/dots-studio/dots-3-note-preview:free/endpoints),
[provider routing](https://openrouter.ai/docs/guides/routing/provider-selection).

## Local regression verification

Full isolated Python discovery passes **920 tests**, with providers mocked,
from `4e40b07` plus the four owned source/test files. Existing Standard and
Xing/Phala snapshots keep their captured settings; new routing defaults are
tested through real mapping clients and authenticated room flows. The frontend
is unchanged. These offline checks are distinct from the three live probes
above. No hosted deployment or complete live defense is claimed.

# Free practice

Choose **Free practice · 0 credits** in Upload/setup before creating a room.
Hosts still sign in; teammates still join with the room code. This tier needs
neither credits nor a voucher. The room keeps its tier through remapping,
retries, reconnect and restart. To change tiers, explicitly create another room.
Existing rooms and API callers that omit `practice_tier` remain Standard.
Streamlit exposes the same choice under **Practice tier** (Standard remains its
existing default).

Free practice includes research and mixed defenses, four reviewer perspectives,
exact citations, clarification, same-question replies and progressive per-answer
coaching. The host confirms **4–8 questions**. A larger map can have unexplored
topics when the question limit is reached. Code-only and voice remain disabled.

## Models and cost boundary

New free-tier preparations and runs use `dots-studio/dots-3-note-preview:free`,
with separate role prompts, pinned to AtlasCloud. The public endpoint catalog
checked on 2026-10-25 lists zero prompt/completion prices, a 512,000-token context,
reasoning and structured-output parameters. A synthetic mapping request through
this route succeeded under the unchanged `data_collection: deny` and zero-price
caps. This is one account/request observation, not a blanket provider-policy,
capacity or full-defense quality guarantee.

| Task | Reasoning token bound | Total output bound |
| --- | ---: | ---: |
| Mapping | 512 | 16,384 |
| Planner | 512 | 4,096 |
| Each reviewer question | 512 | 8,192 |
| Clarification / probe | 512 | 2,048 |
| Overview / answer coaching | 512 | 8,192 |

Every request requires the explicit `:free` model, zero maximum prompt,
completion and request prices, supported parameters, strict JSON schema,
`data_collection: deny`, and no provider fallback. There is no automatic paid
model upgrade or privacy relaxation. If no endpoint satisfies these constraints,
the existing retry/recovery flow retains work. Hosted-account compatibility and complete-defense quality still require
separate live checks.

Models and task bounds are saved with preparation/run policies. Existing paid
assignments and credit/voucher rules remain available under Standard practice.
The existing conservative monetary reservations remain as defensive accounting
for missing receipts; they are not charges to the user. Explicit zero-cost
receipts settle them to zero. Any reported nonzero free-provider cost blocks
that scope for operator review. Request quotas count independently of receipts.

## Existing rooms after the routing corrections

The original NVIDIA free route conflicts with the app's no-collection rule:
OpenRouter lists NVIDIA as retaining prompts/training on them. That can reject
mapping with HTTP 404 even with a valid API key. The earlier correction selected Xing4 via
Phala; the application never enables NVIDIA collection to work around the error.

A subsequent Activity screenshot showed Xing4/Phala returning 429 repeatedly.
Its catalog lists only Phala for that exact Free model, so changing providers for
Standard does not repair it. New Free preparations now use the successful Dots
route. Existing Xing/Phala preparation and run snapshots retain their model,
provider, context and counters; they are not silently upgraded or rewritten.

After deploying the routing change, create another room and select Free practice.
For Streamlit, use a fresh preparation session. No new API key variable is needed.
New Dots policies use the verified 512,000-token endpoint context; older Xing
policies keep 262,144. Oversized requests still fail before dispatch instead of
truncating sources. Restarting or reconnecting does not refill local or upstream
quotas. A complete live Dots defense has not been verified.

## Usage limits

Each preparation permits three mapping attempts. Each run permits 80 provider
attempts, with its last 12 request slots protected for coaching. These are
attempts, not questions: one question normally requires planner plus reviewer,
and interpretation, retries and coaching also consume requests. Failed or
interrupted attempts do not replenish limits. Creating a new room cannot reset
the shared account/server daily counters.

| Operator setting | Default | Allowed range |
| --- | ---: | ---: |
| `OPENROUTER_FREE_PER_MINUTE` | 15 shared requests / rolling minute | 1–1,000 |
| `OPENROUTER_FREE_DAILY_REQUESTS` | 50 shared requests / UTC day | 1–100,000 |
| `OPENROUTER_FREE_OWNER_DAILY_REQUESTS` | 40 requests / owner / UTC day | 1–100,000 |

Configure these privately in the server environment. Raising local limits never
raises OpenRouter's account/provider quotas. The shared daily quota can interrupt
a run, including coaching; per-run coaching slots cannot guarantee upstream or
shared capacity. Quota messages explain whether to wait a minute or until the
next UTC day. They never debit credits or generate a credit-return grant. Live
free runs retain the existing one-active-run-per-host and service ownership rules.
The application keeps request metadata in the existing account database, not
uploaded text or credentials. Use PostgreSQL for durable hosted limits.

### OpenRouter HTTP 429 during mapping

HTTP 429 indicates an upstream request or capacity limit, not by itself an invalid
API key. Wait at least a minute before a manual retry. If the error persists,
the operator should inspect the failed request in OpenRouter Activity: a
`free-models-per-day` rejection requires waiting for the daily reset or changing
the account's allowance; `free-models-per-min` requires reducing the request rate;
an upstream provider limit may require waiting for that provider's capacity.
The app recognizes those explicit daily/minute messages and otherwise reports
an unknown rate/capacity limit without exposing provider text. It does not
automatically retry 429 responses or change the saved model/provider.

OpenRouter currently documents 20 free-model requests/minute and 50/day for
accounts with less than $10 purchased, or 1,000/day after at least $10 purchased.
These limits are shared across the OpenRouter account, including other apps.
A defense uses multiple requests; request counts are not question counts.
Switching API keys or creating another room does not reset upstream limits.
Purchasing credits can raise the daily allowance; it does not guarantee provider
capacity. The app's separate configured quotas still apply.

## Verification boundary

Local tests use mocked provider HTTP, disposable SQLite/PostgreSQL and controlled
room clocks. They check routing/cost fences, bounded attempts, zero-credit access,
two-client completion, coaching and UI controls. The approved 2026-10-25 synthetic mapping check is separate live evidence:
Dots/AtlasCloud succeeded in 85.653s with a reportedUS$0 receipt; a Recursive Free
candidate failed HTTP 404 and was not selected. This does not prove a complete defense,
large-paper coverage, load capacity, hosted behavior or installed-device behavior.
No push or deployment is part of this local change.

Sources: [model details](https://openrouter.ai/dots-studio/dots-3-note-preview:free),
[public endpoint metadata](https://openrouter.ai/api/v1/models/dots-studio/dots-3-note-preview:free/endpoints),
[provider routing](https://openrouter.ai/docs/guides/routing/provider-selection),
[account and free-model limits](https://openrouter.ai/docs/api_reference/limits).

Provider-policy comparison: [OpenRouter providers](https://openrouter.ai/providers), [original NVIDIA free-endpoint collection terms](https://openrouter.ai/nvidia/nemotron-3.5-super-vl).

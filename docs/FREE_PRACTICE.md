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

All free-tier tasks use `nvidia/nemotron-3.5-super-vl:free`, with separate role
prompts. Its public catalog and endpoint metadata checked on 2026-10-20 list
zero prompt/completion prices, a 1,000,000-token context, reasoning and JSON-schema
structured outputs. These facts do not prove account availability, privacy-route
availability or conversational quality.

| Task | Reasoning token bound | Total output bound |
| --- | ---: | ---: |
| Mapping | 4,096 | 16,384 |
| Planner | 512 | 4,096 |
| Each reviewer question | 2,048 | 8,192 |
| Clarification / probe | 512 | 2,048 |
| Overview / answer coaching | 2,048 | 8,192 |

Every request requires the explicit `:free` model, zero maximum prompt,
completion and request prices, supported parameters, strict JSON schema,
`data_collection: deny`, and no provider fallback. There is no automatic paid
model upgrade or privacy relaxation. If no endpoint satisfies these constraints,
the existing retry/recovery flow retains work. Actual deployment-account route
compatibility and quality still require a live synthetic-paper check.

Models and task bounds are saved with preparation/run policies. Existing paid
assignments and credit/voucher rules remain available under Standard practice.
The existing conservative monetary reservations remain as defensive accounting
for missing receipts; they are not charges to the user. Explicit zero-cost
receipts settle them to zero. Any reported nonzero free-provider cost blocks
that scope for operator review. Request quotas count independently of receipts.

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

## Verification boundary

Local tests use mocked provider HTTP, disposable SQLite/PostgreSQL and controlled
room clocks. They check routing/cost fences, bounded attempts, zero-credit access,
two-client completion, coaching and UI controls. Public catalog metadata is the
only external model check so far. No actual inference, hosted check or installed
device check is implied. No push or deployment is part of this change.

Sources: [model details](https://openrouter.ai/nvidia/nemotron-3.5-super-vl:free),
[public endpoint metadata](https://openrouter.ai/api/v1/models/nvidia/nemotron-3.5-super-vl:free/endpoints),
[provider routing](https://openrouter.ai/docs/guides/routing/provider-selection),
[account and free-model limits](https://openrouter.ai/docs/api_reference/limits).

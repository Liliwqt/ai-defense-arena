# OpenRouter mapping and question checkpoint

Ticket 01 moved multiplayer paper mapping/remapping to OpenRouter. Ticket 02
additionally moves research/mixed key-question generation to the assigned
four-reviewer bundle with a GLM low planner and a finite run allowance.
Submission interpretation, coaching and Streamlit question generation still use
the existing text configuration until their later migration tickets: that is
transitional intermediate state, and it is never an automatic fallback from a
failed OpenRouter request. Code-only starts and the old live-speech pilot are
disabled by release gates, even if old environment settings remain configured.
Research and mixed typed defenses remain available.

## Server configuration

Set `OPENROUTER_API_KEY` privately in the server environment before mapping.
Never put it in a client/Vite setting, commit it, or paste it into a support log.
Keep the existing text configuration for the unmigrated operations. There is no
automatic fallback from failed OpenRouter mapping to the old text provider.

| Setting | Initial value | Meaning |
| --- | --- | --- |
| Mapping model | `deepseek/deepseek-v4.1-flash-1017` | Exact selected model; not a browser/model override. |
| Mapping reasoning | `high` | Explicit policy, independent of legacy effort settings. |
| `OPENROUTER_MAPPING_MAX_OUTPUT_TOKENS` | `65536` | Total generated tokens including reasoning; configurable from 1024 to 131072. |
| `OPENROUTER_PREPARATION_USD` | `0.75` | Separate preparation ceiling; positive decimal up to USD 10. |
| `OPENROUTER_RUN_USD` | `5.00` | Per-run question ceiling; positive decimal up to USD 100. |

## Funded defense questions

Research and mixed Start/Restart establish one run scope (`run:<run_id>`) before
any game-credit commitment. The scope snapshots the planner/reviewer bundle, the
per-run ceiling and a protected coaching reserve computed from the confirmed
question budget; an unfundable budget is rejected at Start with the question
budget and its reserve named. Retry of the same run reuses that snapshot; a
restart or a new run receives a new scope. Reconnect, refresh and operator
configuration edits cannot reset or enlarge it.

| Stage | Model | Reasoning | Output limit |
| --- | --- | --- | --- |
| Planner | `z-ai/glm-5.3-flash` | `effort: low` (mandatory reasoning is explicit) | 4096 |
| Methodology Reviewer | `deepseek/deepseek-v4.1-flash-1017` | `effort: high` | 8192 |
| Ethics Reviewer | `anthropic/claude-haiku-5.5` | `effort: medium` | 8192 |
| Impact Reviewer | `qwen/qwen3.8-flash` | `max_tokens: 2048` (Qwen advertises `supports_max_tokens`, no named effort) | 8192 |
| Critical Judge | `z-ai/glm-5.3-flash` | `effort: high` | 8192 |

The planner chooses only from the server-provided eligible options; the server
validates reviewer, topic, follow-up, assessment and completion before the
assigned reviewer is called, so an invalid plan or a valid completion costs no
reviewer request. Both stages reserve their conservative bound before dispatch,
settle only a valid `usage.cost` receipt and keep unknown usage fully reserved.
Cancellation between stages, a stale generation and duplicate work stop before
the reviewer request; the room keeps normal duplicate-question regeneration and
explicit repeat acceptance. Question attempts, reserved provider spend and the
single opening/run charge are all accounted once per dispatched stage.

When the protected question limit cannot fund another question, the discussion
is retained and the failure explains that retry will not reset the allowance;
the coaching reserve remains available to the later coaching ticket, never to
questions. An unfundable configuration names `OPENROUTER_RUN_USD` instead.

The first preparation request snapshots the settings and allowance for that room.
Remapping, correction, reconnect, refresh, restart within the same room and
operator edits cannot reset that allowance or alter its snapshot. New rooms
receive new preparation scopes. Missing credentials do not dispatch a request.
Mapping stays explicit; visiting a page does not begin paid work.

These finite defaults are initial local settings, not measured live bills or
proof of sufficient output for every possible paper. Synthetic checks exercise
the accepted input limits, bounded generated maps, exhaustion and recovery.
Account access, actual schema/reasoning compatibility, response completeness,
quality, latency and real usage must be measured in the text checkpoint before
rollout. An output-limit failure retains accepted material and never silently
truncates a paper or approves an incomplete map.

## Reservations and recovery

The database stores provider allowances and request reservations separately from
account credits, receipts and defense run charges. Amounts use integer nano-USD.
It stores scope/model-policy/cost metadata, not paper text, answers, audio or keys.
The existing SQLite/PostgreSQL transaction boundary serializes admission.

Before dispatch, mapping reserves a conservative input/output bound. Input uses
serialized UTF-8 bytes plus framing headroom as a token upper bound and
rejects a request beyond the selected context instead of truncating it. The
request filters for supported parameters, disables provider fallbacks, denies
data-collection routes and caps routing at USD 0.30 per million input tokens,
USD 1.20 per million output tokens and zero extra request fee. Reasoning is part
of generated output, not a second output charge.

Each valid provider `usage.cost` receipt settles idempotently; a later receipt
cannot silently overwrite conflicting evidence. Missing/invalid usage,
connection failure, cancellation or process restart cannot make a dispatched
request free: its full bound remains reserved conservatively. Conflicting cost
evidence or a cost above the reservation blocks new requests for operator review.
This is a local spending control, not a provider billing guarantee. Top-up
balances, defense prices, vouchers and credit-return eligibility are unchanged.

When preparation cannot fund another request, the app retains uploads and
explains that retry will not reset the allowance. A valid prior map remains
readable during an unchanged-scope remap failure, with approval revoked and
confirmation/Start blocked. A changed profile invalidates the old map's scope;
the correction remains available for retry and fresh confirmation.

## Verification boundaries

HTTP/WebSocket and browser tests use synthetic papers and mocked provider HTTP.
Funded planner/reviewer checks cover the exact bundle, per-stage reservation and
settlement, unknown-usage retention, invalid-plan rejection before any reviewer
request, valid-completion single-call behavior, cancellation between stages and
unfundable-start rejection before credit commitment. The opt-in PostgreSQL gate
uses disposable loopback databases for concurrency and
reopen/settlement checks. Historical code/speech engine tests explicitly mock the
old release gates; dedicated policy tests verify those paths remain unavailable
under the actual release settings. There is no environment switch to bypass the
current code-only/speech gates.

No actual OpenRouter inference or microphone request is part of the offline
suite. Actual provider/model quality, account capability and billing remain
separate evidence. Voice integration requires its later OpenRouter-only prototype
and review; native builds cannot substitute for installed-device capture tests.

## Primary references checked 2026-10-19

- [Model capability catalog](https://openrouter.ai/api/v1/models).
- [Structured output and streaming](https://openrouter.ai/docs/guides/features/structured-outputs).
- [Provider parameter, fallback, data-policy and price controls](https://openrouter.ai/docs/guides/routing/provider-selection).
- [Reasoning effort and billed output](https://openrouter.ai/docs/guides/best-practices/reasoning-tokens).

The mapping and funded-question adapters share one documented chat-completion
structured/SSE transport and present the existing normalized mapping stream and
detached question results to grounding/progress code. They do not assume
Responses and chat streaming event names are interchangeable.

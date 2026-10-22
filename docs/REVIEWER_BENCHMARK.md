# Reviewer comparison and provider gate

Ticket 08 has an opt-in measurement harness. No candidate settings have been
selected for the app. Mocked results establish instrumentation and accounting;
actual schema support, dialogue quality, speed and cost remain unverified.

From the repository root, inspect the complete matrix without credentials or
network requests:

```bash
.venv/bin/python -m tests.reviewer_benchmark --plan
.venv/bin/python -m unittest tests.test_reviewer_benchmark tests.test_operation_timing_harness -v
```

The four built-in synthetic cases cover quantitative service operations,
qualitative education, theoretical applied philosophy and computational/design
software evaluation. Two use English and two modern Bisaya; two have longer
sources (about 37 KB). Source and answer fingerprints must match across conditions.
Long background is deliberately repetitive, with a relevant eligibility passage
outside the initial focused context. This is a small exploratory matrix, not
proof of performance on arbitrary long or difficult real papers.

Each case uses the same locally validated four-topic map, a five-question budget,
an opening and up to four scripted answers, plus at most one same-question reply
per answer. Actual model decisions can produce different paths or early completion;
the harness does not force acceptance or manufacture reviewer coverage. Mapping
and coaching inference are excluded; the run retains its normal coaching reserve.

Three conditions run in rotating order:

| Condition | Interactive route | Settings |
| --- | --- | --- |
| baseline | Separate interpretation, planning and writing; full evidence | Current configured models and reasoning |
| current | Combined interpretation/planning, then writing; focused evidence and bounded lookup | Current captured Standard policy |
| candidate-light | Same combined/focused route and four models | Lower supported reasoning and bounded output, only in benchmark scopes |

The baseline reconstructs the previous OpenRouter pipeline, **not GPT Luna**.
All three use the current 45-second processing policy, stage caps, transient retry
and existing price/privacy limits. Results measure synchronous typed workflow
processing, excluding reaction-reading, voting, browser and hosted transport time.
Room integration remains a separate ticket 09 check.

The candidate keeps the current Methodology, Ethics, Impact and Critical models.
It lowers question reasoning to low for DeepSeek, Haiku and GLM, and 512 reasoning
tokens for Qwen; Qwen interactions also use 512. Planner output is 2,048 tokens,
writer/combined output 4,096. The plan captures exact model IDs, settings, source
sizes, admission bounds and policy fingerprints. Environment changes can change
that plan: inspect it again before approving an actual run. No benchmark result
automatically modifies runtime defaults, mapping, coaching, saved runs or pricing.

## Paid execution

Paid execution requires operator authorization and a locally configured
`OPENROUTER_API_KEY`. Never paste a key in a command argument, document or artifact.
Do not run this command until that authorization is given:

```bash
.venv/bin/python -m tests.reviewer_benchmark --execute --max-usd 5 --output .local/reviewer-pilot-01
```

The proposed pilot is 12 mini-runs. With the recorded default configuration, the
ordinary conservative request bounds total approximately $4.24, before extra
lookup, same-question and retry requests. This is a reservation calculation, not
an expected bill. A $5 campaign admission ceiling covers the entire campaign,
including extras; it may stop the matrix early. The next request must fit both
the unchanged run allowance and campaign allowance. No model fallback or increased
price limit is allowed. Reported cost reconciles holds; missing or conflicting
receipts retain the conservative hold. The ledger persists in the new output
directory; an existing directory is rejected rather than reset. Late provider
work can retain a hold after the bounded UI wait; the report discloses requests
still in flight. Neither a local deadline nor a reservation guarantees that a
remote provider has stopped billing.

The observer intercepts only the existing OpenRouter HTTP boundary. It requires
`allow_fallbacks=false`, `require_parameters=true`, `data_collection=deny` and the
unchanged prompt/completion/request price caps. It never prints authentication,
request messages, answer text, raw response JSON or hidden reasoning. Only built-in
synthetic material is sent. Do not add private papers to these fixtures.

Artifacts are refreshed after each transition:

- `plan.json`: synthetic fingerprints and exact captured policies.
- `measurements.jsonl`: content-free transition/stage timing, safe failure classes,
  retries, bounded lookup measurements and supplied usage/cost.
- `quality-review.json`: parsed interpretation results (including proposed next
  plan/assessment even when writing fails), committed coverage, displayed synthetic
  dialogue with topic/follow-up IDs, reactions and citations, script
  indices and unfilled human review fields; no submitted answer text or reasoning.
- `report.json`: per-condition/per-model distributions, sample counts, failed
  transitions in target denominators, known/unknown metrics, comparisons, funding,
  in-flight requests and cases not run.
- `ledger.sqlite3`: private benchmark scopes and conservative accounting, separate
  from the operator's application database. Do not delete it to repeat a campaign
  under an existing approval.

`received` on a request means transport completed, not that the structured result
passed validation. Transition failure and the separate quality review are essential.
Unknown cost, provider identity and lookup measurements are not reported as zeros.
Active requests have a separate `in_flight` record and count; their elapsed time
is excluded from completed-stage distributions. Transition totals are reconciled
against request records whenever artifacts are written, so a late writer receipt
cannot leave a planner-only cost labeled as the whole transition's bill. Failed
records from capture version1 are conservatively unknown at transition level and
their request counts are lower bounds; individual supplied receipts remain visible.
Supplied token costs include reasoning where the provider reports it; reasoning
tokens are separately unknown when omitted. A first-token or catalog speed figure
cannot replace the full transition measurement.

## Acceptance before selecting settings

The report always starts `provider_gate=unreviewed`. For every condition and role,
inspect actual validated questions, combined decisions, source citations, supported
language, context sufficiency and research scrutiny. Record absent roles, rejected
schemas, refusals and incomplete runs as unresolved evidence. Check actual privacy
route compatibility, reasoning/output support and usage, not only advertised flags.
Disclose achieved fractions within 10 and 15 seconds, distributions and sample
counts including failures; preserve the 45-second cap. One rotated pass is only
a pilot. Add authorized repeats and more demanding cases before general claims.

A missing key, exhausted campaign, unusable endpoint, incomplete role coverage,
failed quality check or unavailable metric leaves the applicable gate open. Do not
promote a candidate or call the optimized route live-ready from mocked checks.
Settings promotion needs a separate reviewed change for new policies only.

Public catalog/endpoint metadata inspected on 2026-10-22 advertised all four
configured IDs. That establishes advertised availability only. It does not prove
that a compatible endpoint satisfies the existing price/privacy constraints:
[model catalog](https://openrouter.ai/api/v1/models),
[provider routing](https://openrouter.ai/docs/guides/routing/provider-selection),
[reasoning controls](https://openrouter.ai/docs/guides/best-practices/reasoning-tokens),
[structured outputs](https://openrouter.ai/docs/guides/features/structured-outputs).

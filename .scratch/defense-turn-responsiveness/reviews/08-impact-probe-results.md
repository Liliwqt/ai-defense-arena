# Ticket 08: authorized focused Qwen Impact probes

2026-10-23. The user separately approved **US$0.15** for four targeted requests.
All four completed, with no retry, lookup expansion, model switch or extra paid
call. Runtime settings remain unchanged. **The full provider gate stays
failed/incomplete4/7.** No push or deployment.

Executed the frozen `4a6be54` base plus seven hashed benchmark/fixture files,
previously verified by863isolated Python tests with providers mocked. The launcher
verified the exact [prepared plan](08-impact-probe-plan.json) before privately
loading only the named local key. Sources/history were built-in synthetic material
and selected [saved-state fixtures](08-impact-probe-fixtures.json), not private
papers or a production account database. Original raw results, plan, execution log
and ledger remain under ignored `.local/impact-probe/provider-output`.

Evidence: [sanitized measurements](08-impact-probe-measurements.jsonl) and
[captured summary, hashes and accounting](08-impact-probe-summary.json).

## Actual results

| Reconstructed case | Requested route | Valid question | Processing time |
| --- | --- | --- | ---: |
| Quantitative English | Alibaba excluding US-East | Yes, source line6 | 21.142s |
| Quantitative English | Alibaba US-East | No, HTTP429 | 6.225s |
| Qualitative/Bisaya answers | Alibaba US-East | No, HTTP429 | 7.332s |
| Qualitative/Bisaya answers | Alibaba excluding US-East | Yes, source line6 | 22.314s |

All requests used `qwen/qwen3.8-flash`, reasoning `max_tokens=2048`, output8192,
strict structured response/citation/selection checks, the original price/privacy
filters, no fallback and the45s stage window. Within each case only provider
selectors changed. English ran excluding-US-East first; Bisaya reversed that order.
No request exceeded the local processing window; final in-flight count was zero.

These are **single Impact-writer probes**, not answer-to-next-question timings.
The timed samples include local parsing/domain validation; HTTP request durations
were21.062s/22.273s for successes. They do not meet the10–15s target even before
adding preceding interpretation work. Fast429 responses are failed requests,
not a speed advantage. Two samples per condition are not a capacity guarantee
or a broad provider ranking.

Reported reasoning usage was410tokens for English and317for Bisaya, below the
configured2048token budget. A modest reduction to512would not necessarily bind
these samples or improve latency. A lower/disabled-reasoning candidate needs
support and quality validation; no speed gain is promised from the budget alone.

## What the new diagnostics establish

Both US-East-selected requests returned these controlled values:

```text
http_status: 429
error_code: 429
limit_source: upstream_provider_shared_pool
error_provider: Alibaba
```

Neither supplied a recognized error type, Retry-After nor a cost receipt. Their
absence is unknown, not a zero-delay or free-request claim. These two failures
explicitly report an Alibaba upstream shared-pool limit; they do not report an
OpenRouter account/key ceiling. They do not establish a reset time or justify
rapid retries. The original automatic-route429s in the previous campaign had
no retained error metadata or endpoint identity, so this does **not** retrospectively
prove their exact route/cause.

The excluding-US-East condition requested `only=["alibaba"]` and
`ignore=["alibaba/us-east-1"]`; the other requested
`only=["alibaba/us-east-1"]`. Successful streams named Alibaba. That is compatible
with the requested family and filters but does not independently expose an exact
served endpoint, region or physical location. Both requested alternatives belong
to the same provider, not different companies.

## Narrow compatibility and conversation observations

The two successful results passed the existing structured result, exact-source
citation and saved Impact-selection/domain validation. The English question asks
what the paired waiting-time comparison adds to the local contribution; the Bisaya
question asks what the bounded contribution is and how it would be recognized.
Neither claims completed effectiveness. The latter is in Bisaya with natural
English research terms after a Bisaya answer history.

There is a quality caveat: the English wording introduces "raw logs," which are
not explicitly named in the synthetic proposal. The source supports paired
waiting-time data and bounded contribution, but treating that data as logs adds
specificity. Exact citation validation is not semantic certification; this needs
human question-quality review before a provider/model selection. Native-language
quality also remains a human review gate. No complete defense, Impact answer
interpretation, Critical dialogue, difficult/long-context, coaching, browser,
hosted transport or installed-device behavior was tested here.

## Costs and decision

Four campaign ledger requests reconcile to four request records. Two supplied
receipts total **US$0.002126118**. Two missing receipts retain **US$0.044670600**
in conservative reservations. Known cost plus holds is **US$0.046796718**, within
the approvedUS$0.15 ceiling; the exact final bill remains unknown. No reservation
was released without evidence. The local campaign is finished, and nominal
remaining allowance does not authorize extra experiments. Prior ledgers were
preserved; no account credit or application pricing was changed.

The Alibaba route excluding US-East is a **candidate** for a later full-defense
test, alongside the previously tested DeepInfra DeepSeek route. It worked for
both reconstructed Impact inputs while the US-East requests reported rate limits.
It is still slow in these two samples, with a grounding caveat. Do not silently
promote it, claim the whole defense fixed or route saved runs differently.

Next prepare a separate supported-reasoning comparison on working routes, keeping
prompts/output limits fixed to isolate that variable; later verify complete
research/mixed defenses and every reviewer. This result does not authorize that
paid campaign. Ticket08 criteria2/4/5 remain open and ticket09 carries the gate.

Verification: actual approved four-request provider probes; safe artifact/hash,
plan/source-match and read-only ledger reconciliation checks. Source was unchanged
during inference, so prior863Python/providers-mocked remains the latest source
gate, not a live-quality claim or a new suite run. Prior414React/build and26local
PostgreSQL evidence remain separate. No independent code-review/human approval,
new model/reasoning settings, publication or deployment is claimed.

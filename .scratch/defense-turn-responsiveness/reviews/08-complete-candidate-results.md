# Complete candidate campaign — 2026-10-23

**Outcome: failed/incomplete; no runtime settings promoted.** Exactly the four
approved synthetic attempts ran under one US$5 campaign admission cap. The first
reached all four reviewer roles; none reached a completed defense or coaching.
[Exact plan](08-complete-candidate-plan.json),
[content-free measurements](08-complete-candidate-measurements.jsonl),
[summary and provenance](08-complete-candidate-summary.json),
[protocol](../../../docs/COMPLETE_DEFENSE_BENCHMARK.md).

## Scope and provenance

Executed `4a6be54` plus nine frozen benchmark/test/fixture files, with verified
source hashes and exact prepared plan. Only built-in synthetic inputs and an
isolated local ledger were used. No private paper or application account database.
Only the named local key was loaded, without disclosure. Production defaults,
prices, privacy guards, other models/reasoning, saved runs and prior campaign
holds were unchanged. No fallback or additional paid campaign was run.

Candidate: DeepSeek via DeepInfra; Qwen via Alibaba excluding US-East; Qwen
question writing requests reasoning disabled. Qwen combined answer review keeps
its 1024-token reasoning budget; Methodology high writer/low interaction, Ethics
medium writer/low interaction, Critical high writer/low interaction and GLM low
planner retain existing policy. Overview/cards would have used Haiku/high, but
**no coaching request was reached**. Maps are locally validated fixtures, with
no mapping inference.

## Complete attempts and failure recovery

| Synthetic case | Opening | Furthest accepted state | Stop |
| --- | --- | --- | --- |
| Quantitative English | Valid, 23.493s | Seven questions across all four reviewers; six accepted answers | Critical combined review failed before an interpretation was accepted, 16.499s |
| Qualitative Bisaya | Failed, 5.759s | Valid planner retained; no question displayed | DeepSeek writer HTTP429 |
| Theoretical long English | Failed, 8.018s | Valid planner retained; no question displayed | DeepSeek writer HTTP429 |
| Computational/mixed long Bisaya | Failed, 9.730s | Valid planner retained; no question displayed | DeepSeek writer HTTP429 |

Critical's request returned HTTP200, then the app raised `QuestionGenerationError`
with the existing safe code `unclassified` at `CombinedSubmissionDraft`.
No parsed interpretation was captured, so the exact response/domain rejection
reason is unknown. Do not call this a proven schema error, timeout or invalid
next-plan choice. Six previously accepted answers remain; the seventh submission
is retained as pending, not accepted. A precise safe rejection code is needed
before attributing the failure or weakening any validation.

All three new 429 errors explicitly report
`limit_source=upstream_provider_shared_pool`, `error_provider=DeepInfra`, and
no Retry-After. This identifies an upstream shared-pool rejection for these
requests, not an exhausted US$5 cap, invalid key, or proven account/day/minute
quota. The requested route is DeepInfra; failures have no serving-provider
receipt, so error-provider and observed serving-provider remain distinct.
Their saved recovery stage is `writing`; a future authorized retry can reuse
its valid plan instead of replanning. No eligible automatic retry was observed,
and no manual retry was added to these four attempts.

No completed defense, final assessment, report, closing or coaching cards.
All four cases were attempted; final in-flight request count is zero. The run
result is a typed/provider-domain check, not a multiplayer financial settlement,
browser, hosted or installed-device check.

## Timing

Six successful full answer-to-next-question transitions took **25.402, 13.472,
11.713, 10.944, 17.666 and 34.019 seconds**. Median **15.569s**, range
**10.944–34.019s**. Three of six successes met 15s; with the failed Critical
review included, **3/7 attempted original-answer transitions (42.9%)** met 15s.
None met 10s. This does not meet the “most transitions within 10–15s” gate in
this sample. There were no same-question reply operations or completion/coaching
samples; the inherited target metric excludes those phases. No operation expired
at the 45-second interactive cap. Automatic retries: zero observed. Lookup
measurements were not supplied, so lookup counts/durations remain unknown.

| Observed provider/task | Successful samples | Request time |
| --- | --- | --- |
| DeepInfra / Methodology writing, high | 2 | 11.041, 15.240s |
| DeepInfra / Methodology combined review, low | 2 | 10.047, 5.070s |
| Azure / Ethics writing, medium | 2 | 8.290, 4.539s |
| Azure / Ethics combined review, low | 2 | 7.058, 7.998s |
| Alibaba / Impact writing, requested reasoning off | 2 | 2.837, 3.100s |
| Alibaba / Impact combined review, 1024 budget | 2 | 14.448, 22.610s |
| OpenInference / Critical writing, high | 1 | 11.298s |

Qwen writer receipts explicitly report zero reasoning tokens. Its combined reviews
report 700/1024 tokens and contribute substantially to total time. Critical's
failed interpretation transport took 16.442s; HTTP200 is not accepted-result
success. Four GLM planner requests passed, taking 4.440–12.309s. Three rejected
DeepInfra writer requests took 1.166–1.233s, excluded from successful-writer
latency comparisons. No endpoint region/quantization or causal cross-campaign
speed claim is inferred from provider-family names or this unpaired sample.

## Narrow conversation observations

- Methodology asks for the workload/time-band matching rule and a concrete
  cutoff, anchored to source line4. Reactions distinguish a proposed comparison
  from a causal result and fairly identify the repeated script's missing detail.
- Ethics conditionally asks about people, voluntary participation and minimal
  identifying records, citing line5. Its follow-up explores “where relevant”
  rather than pretending safeguards are already demonstrated.
- Impact asks what bounds the local contribution, citing line6; its follow-up
  correctly identifies that the repeated script restates the boundary without
  concrete setting features. Fast generation did not bypass source/selection
  validation in these two questions.
- Critical cites line7 and asks about selection assumptions/alternative
  explanations. Its phrase **“observed waiting time differences”** risks implying
  completed findings even though this is a proposal. Treat this as a semantic
  quality concern; an exact citation does not establish that premise.

All seven displayed source locations validate through the unchanged app. Only
English question writing from all four roles is observed; no accepted Critical
interpretation, Bisaya dialogue, long/mixed question output, complete defense or
coaching quality was established. Some reactions remain empty, as allowed.
These are agent observations, not human/native-language approval or a claim of
reviewer equivalence.

## Spending and verification

**21 requests; 11 operation records; 18 supplied receipts: US$0.016413119.**
Three missing receipts retain **US$0.062592900** in conservative holds. Known
cost plus holds is **US$0.079006019**, within the approved US$5 total. This is not
an audited final invoice. No prior hold was released or reset, and remaining
nominal allowance does not authorize extra experiments.

Observed serving-provider attribution: DeepInfra4, Azure4, Alibaba4,
OpenInference6, unknown3 failed requests. Final request count/receipts/holds
match a read-only ledger reconciliation. Exact frozen/source/plan hashes and
public artifact JSON/hash checks pass. Pre-run tracked fingerprints show only
the authorized log changed during inference; no benchmark or foreign runtime
source changed. Original raw report/quality/measurements/plan/ledger are retained
under `.local/complete-benchmark/provider-output`.

The unchanged frozen code previously passed **871 offline Python tests with
providers mocked**. No suite rerun was needed for evidence-only edits. Earlier
React/build/PostgreSQL/browser evidence remains separate. No push/deployment,
new runtime policy, extra paid request or human review completion.

## Remaining gate

Ticket08 remains **partial4/7**. Do not promote the complete candidate as live-ready.
Next work should make the Critical rejection diagnosable using bounded safe
validation codes, and resolve or compare the DeepInfra capacity restriction
without inventing a retry duration or silently switching models/providers.
Another paid experiment needs its own concrete scope and approval. Keep the
promising Qwen writer setting as evidence, with interpretation/mapping/coaching
reasoning unchanged until separately tested.

# Ticket 08: authorized provider-routing comparison

2026-10-23. Four synthetic mini-runs completed under the separately approved
**US$1.25 campaign admission cap**. **Gate remains failed/incomplete (4/7).**
No runtime provider/model/reasoning settings were promoted, and no extra campaign,
push or deployment was performed.

Executed the prepared frozen `4a6be54` artifact plus the three hashed benchmark
files, previously verified by 856 isolated Python tests with providers mocked.
The [captured plan](08-provider-routing-plan.json) exactly matched before dispatch.
Only the existing DeepSeek snapshot's provider selector changed; all models,
reasoning/output limits, source/answer fingerprints, validators, price/privacy
filters, no-fallback rule and 45-second processing window remained fixed.
GLM/Haiku/Qwen routing was unchanged. English ran auto then DeepInfra; Bisaya ran
DeepInfra then auto. No private papers, application account database, mapping or
coaching inference were used.

Evidence: [content-free measurements](08-provider-routing-measurements.jsonl),
[summary, hashes, policies and offline replay](08-provider-routing-summary.json).
Original measurements, quality snapshots, report, ledger and execution log remain
under ignored `.local/provider-routing/`. Do not overwrite or reset them.

## Observed processing

| Synthetic case | Automatic opening | DeepInfra opening | Successful answer-to-next-question transitions |
| --- | ---: | ---: | --- |
| Quantitative English | 37.153 s | 13.952 s | Auto 0/1; DeepInfra 2/3 |
| Qualitative, Bisaya answers | 10.318 s | 11.906 s | Auto 0/1; DeepInfra 2/3 |

All four openings passed validation. DeepInfra's four successful follow-ups took
16.324, 22.236, 35.743 and 16.688 seconds (median 19.462s). Its remaining two
answer transitions failed at the later Qwen request. No answer attempt produced
a next question within 15 seconds: auto 0/2, DeepInfra 0/6. These denominators
include failures, not just successful responses. The 10-second counts are also
zero. No processing window expired, no automatic retry was observed, and no lookup
measurements were supplied; lookup metrics remain unknown rather than zero.

The English DeepSeek opening writer took 19.411s on OpenInference versus 6.728s
on DeepInfra. Its unpinned GLM planner also varied: 17.603s versus 7.097s. Therefore
the entire opening improvement cannot be attributed solely to changing DeepSeek's
host. In the Bisaya case, the writers were close (4.459s versus 4.221s), while
planner times differed (5.737s versus 7.569s); automatic routing had the faster
total opening there. DeepInfra was **not universally faster** in this sample.

All eight explicitly pinned DeepSeek requests reported DeepInfra. The automatic
DeepSeek requests reported OpenInference, so the requested comparison did reach
different provider families. Family names do not establish exact quantization,
endpoint tier/region or identical effective execution. Four exploratory mini-runs,
variable provider load, unpinned planner routing and divergent adaptive questions
cannot establish a general provider ranking or matched-request causal estimate.

## Failures and offline adjudication

Both automatic runs stopped after the first answer. Their original captured
transition code is `unclassified`, failure class `QuestionGenerationError`, stage
`CombinedSubmissionDraft`. The requests completed transport and parsed domain
output; transport success is not application acceptance.

Both parsed proposed plans assessed turn **1** when the server-owned previous
turn was **0**, and chose Methodology on the same topic with `is_follow_up=false`,
which was not an eligible next option. Replayed those captured synthetic decisions
offline against the frozen domain validator: the originals failed coverage
validation; correcting only the turn then failed reviewer/topic validation;
correcting the turn and follow-up flag yielded a valid plan. This is explicit
**offline domain replay of captured outputs**, not another inference call or an
alteration to accepted output. The public summary preserves those observations
separately, without rewriting the original failure codes or weakening validation.
The exact full internal exception sequence was not logged by the live harness.

Both DeepInfra runs progressed through Methodology and Ethics, then the unchanged
`qwen/qwen3.8-flash` Impact writer returned **HTTP 429** (7.734s English, 7.165s
Bisaya). No provider identity or final cost receipt was supplied for those failed
Qwen requests. The evidence does not distinguish account/platform quota, upstream
rate limiting or another 429 cause. Do not attribute these failures to DeepInfra,
change models automatically or retry beyond the approved campaign. The preceding
Ethics interpretations and valid next plans were captured before writer failure;
this is typed benchmark evidence, not a two-browser recovery/credit test.

## Narrow conversation observations

Only Methodology and Ethics displayed questions. Their citations resolved to the
synthetic source's line4 methodology and line5 ethics statements. English prompts
asked about matched baseline/pilot pairs, unmatched cases and handling identifying
information, without claiming completed results. The first Bisaya-case opening
was English; after the substantive Bisaya answer, follow-up and Ethics questions
appeared in Bisaya. This tests language adaptation after an answer, not a claim
that the opening follows an unconfigured preference.

The Methodology interpretations recognized that the script explained procedures
without fully justifying the matching rule or interview design. The follow-up
replies repeated the same scripted approach answer, and the second assessments
kept that gap unresolved rather than declaring it answered. These are limited
agent observations from synthetic displayed text, not human approval, native-
speaker quality certification or proof of strong dialogue on arbitrary papers.
Impact and Critical never spoke. No complete defense/coaching, difficult/long-
context run, browser/hosted transport or installed-device behavior was established.

## Accounting

The campaign recorded **22 requests and 12 transitions**, all four planned runs
attempted, final in-flight count zero. Twenty supplied cost receipts total
**US$0.016998490**. The two failed Qwen requests retain **US$0.045566400** in
conservative unknown-cost reservations. Known cost plus holds is
**US$0.062564890**, below the approved US$1.25 cap; **this is not an exact final
bill**. Counts/receipts/holds reconcile to the read-only campaign ledger.
No hold was released without a receipt and no extra request chased an outcome.
Observed provider names: OpenInference8, DeepInfra8, Azure4, unknown2. Request
provider identity, missing reasoning/token metrics and lookup measurements remain
explicit rather than invented. Local work has ended; no further paid run is
approved by the nominal remaining cap.

## Decision

DeepInfra is a candidate for improving DeepSeek's interactive route: it produced
valid plans and follow-ups where this automatic sample failed. It is not an
established universal speed improvement, and the full flow still misses the
10–15s target and stops at Qwen429. Keep runtime defaults unchanged pending a
reviewed selection and broader evidence. Next diagnose the Impact429 without
repeating accepted answer work, and consider a separately prepared test of lighter
interactive reasoning/limits or another compatible route. Do not silently raise
timeouts, relax schemas/privacy/prices or remove required planning.

Ticket08 stays4/7: all-role/difficult-context quality/compatibility and justified
settings selection criteria2/4/5 remain open; ticket09 must carry this gate.
The latest benchmark source check remains **856 Python tests, providers mocked**;
no source changed during this campaign, and suites were not rerun for evidence-only
updates. Prior414React/build and26localPostgreSQL results remain separate evidence.
No independent code-review/human visual approval or live-ready claim is made here.

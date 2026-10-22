# Ticket 08 actual-provider pilot

2026-10-23. **Gate: failed/incomplete; no candidate promoted.** The user approved
one twelve-run synthetic campaign with a US$5 admission ceiling, then configured
the key locally. Executed committed `507fca3` in an isolated artifact with unchanged
privacy/price/run limits. No private paper, account database or fallback model was
used. No additional campaign or paid rerun was performed.

Reproducible captured settings/case hashes and complete content-free distributions:
[summary](08-provider-summary.json), [measurements](08-provider-measurements.jsonl).
Raw pilot files and original SQLite ledger remain in ignored
`.local/turn08/provider-pilot-01`; the original measurements hash is in the summary.
The recorded baseline is separate/full OpenRouter, not GPT Luna.

## Results

All twelve case/condition pairs were attempted: quantitative English, qualitative
Bisaya, theoretical long English and computational/design mixed long Bisaya,
each across baseline, current and lower-reasoning candidate. Twenty-nine requests
produced sixteen transition records. Completed request records match the campaign
ledger count; final in-flight count is zero. Transport `received` does not establish
valid schema, decision or question acceptance.

| Condition | Validated openings | Median opening attempt | Attempt range |
| --- | --- | --- | --- |
| Baseline separate/full | 3/4 | 36.93 s | 32.49–45.00 s |
| Current combined/focused | 0/4 | 27.35 s | 15.10–45.00 s |
| Candidate lighter reasoning | 0/4 | 23.40 s | 9.28–31.85 s |

These times include failed attempts. Shorter failures are **not a speed win**.
There were four processing-window expirations, six generic generation errors and
one invalid structured-result error across opening/answer/reply transitions.
The generic failure class does not identify the precise failed validation or
internal cause; raw response/error messages were intentionally not retained.

Baseline had three scripted answer attempts: one produced same-question
clarification, two expired while processing. A further same-question reply produced
clarification. Zero of three answer attempts produced a next question within15s.
Current/candidate had no answer attempts because their openings never committed;
their achieved ordinary-transition fraction is **unknown**, not zero-percent
successful inference. No complete defense or combined-submission request ran.
The 10–15s usual-transition target is therefore unproven. Bounded waiting returned
around45s on expirations (up to1ms scheduling overhead); an individual provider
request could finish later. No limit was raised to make results look successful.

Observed planner request medians were11.97s baseline(n5),13.10s current(n4) and
10.55s candidate(n4); observed p95 values25.38s,29.67s and21.89s respectively.
Only GLM planning and DeepSeek Methodology requests were dispatched. These are
small, adaptive, nonpaired request samples, not a general model-speed ranking.
Provider metadata identified OpenInference on observed receipts, under the
unchanged routing constraints. No Haiku/Qwen role performance was measured.
No automatic retry was observed. Broader lookup measurements were not supplied;
they remain unknown rather than evidence of zero lookup work.

## Cost and reporting correction

Provider-supplied receipts total **US$0.011694779** across25 of29 requests. Four
requests have no cost receipt and retain **US$0.095164500** in reservations.
Combined reported cost plus conservative holds isUS$0.106859279, below theUS$5
admission ceiling. This is **not an exact final bill**; missing receipts are not
free requests. No reservation was reset or released without cost evidence.

The live run exposed a version1 observer gap: at a timeout it omitted an active
writer, so planner-only usage could look like total transition usage. The running
artifact was left unchanged. A separate reviewed reporting correction now retains
active request records, excludes their unfinished durations from completed-stage
distributions and reconciles late receipts/counts. Postprocessed original records
using that correction; original raw evidence and ledger were preserved. Version1
failed-transition totals remain conservatively unknown and their counts flagged
as lower bounds, while individual receipts and independently checked campaign
counts remain available. This correction changes no paid result or model policy.

## Grounding and quality observations

Agent inspection found three accepted Methodology openings with line4 citations
that match the accepted synthetic source and proposal stage:

- Qualitative: asks how negative cases and an audit trail support contrasting
  accounts. Those methods appear explicitly in the cited line.
- Theoretical: asks how a counterexample distinguishes necessary/sufficient
  assumptions without claiming experimental evidence. This respects the source.
- Computational/design mixed: asks why the documented baseline is appropriate for
  paired benchmark inputs. The source explicitly describes that comparison.

This supports only a narrow grounding observation, not certification or overall
conversation quality. The two qualitative explanations respond in Bisaya/mixed
language, but one includes Tagalog-influenced wording; native modern-Bisaya
quality is not established. Their repeated clarification does not prove a product
regression: the fixed answer script repeats “Bisaya lang” and a generic comparison
answer instead of explaining negative-case analysis. That makes this a weak
ordinary-answer comparison. The theoretical script likewise lacks a concrete
counterexample. Input limitations must be fixed before stronger quality claims.

Ethics, Impact and Critical never spoke. Combined decisions, accepted next-turn
reactions, full English/Bisaya conversations and role-specific schema/reasoning
compatibility remain untested. Long fixtures are only about37KB with repetitive
background; they do not prove demanding real-paper context sufficiency.

## Remaining work

Ticket08 remains partial: criteria1,3,6,7 have measurement/disclosure evidence;
criteria2,4,5 remain open. Selecting models/settings is unsupported. First reproduce
the focused-route failures offline with sanitized failure-stage diagnostics; refine
approach-specific scripts and avoid repeating language commands. Then prepare a
reviewed, separately authorized comparison that reaches each role and tests the
actual combined path. Preserve research scrutiny, citations, deadlines and prices.
Ticket09 must not convert this failed/incomplete provider gate into live readiness.

Reporting correction verification: thirteen benchmark checks passed after two
new regressions first failed; final isolated full Python **846 passed in175.792s**
(AI/Google/payments mocked). Real local PostgreSQL **16 passed in20.475s**, provider
HTTP mocked; owned fixture stopped. Prior unchanged frontend **414 tests/build**
remain the applicable evidence, not a new visual review. Independent correction
Standards0/Spec0 findings. No browser, hosted, installed-device or human approval
claim. No push or deployment.

A final report-only regression also reproduced an empty lookup sum appearing as
zero. It now stays null when no lookup measurements are known; the final benchmark
module passes13in12.775s after that delta. No runtime/funding behavior changed,
and no additional paid request was made. Full-suite evidence above predates this
one-line summary correction; the targeted module verifies its final behavior.

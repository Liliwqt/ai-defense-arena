# Ticket 08: authorized two-case Standard retest

2026-10-23. Executed commit `25d8a72` after the user approved a separate US$1
campaign cap. **Gate remains failed/incomplete.** No model or reasoning setting
was changed, and no additional campaign was started.

The isolated committed artifact's credential-free plan exactly matched the
[approved plan](08-retest-plan.json). Inputs were built-in quantitative English
and qualitative Bisaya synthetic cases, using the v2 source/answer scripts and
new requested normal-result/lookup response format. No private paper, application
account database or fallback model was used. Mapping/coaching inference was excluded.

Evidence: [content-free measurements](08-retest-measurements.jsonl) and
[captured summary](08-retest-summary.json). Original raw artifacts, quality snapshots
and persistent ledger are retained in ignored `.local/turn08-retest-02/provider-output`.
The summary records the executed commit, exact policies, case fingerprints and
original measurements hash. These changed inputs and wire contract are not a
controlled repeat of the first pilot; do not claim a speed improvement from them.

## Observed results

| Case and operation | Result | Processing time |
| --- | --- | --- |
| English opening | Accepted grounded Methodology question | 32.206 s |
| English answer review | Processing window expired at `CombinedSubmissionDraft` | 45.001 s |
| Bisaya opening | Processing window expired at `QuestionDraft` | 45.000 s |

Both authorized cases were attempted. Five provider requests produced three
transition records. The English opening comprised GLM low-reasoning planning
(12.458s) and DeepSeek high-reasoning writing (19.578s), plus local overhead.
The next DeepSeek combined interpretation/planning request used **low** reasoning
and still exhausted the processing window. There was no validated interpretation
or saved next plan in its result artifact.

The Bisaya case's GLM planner finished in15.277s. Its DeepSeek high-reasoning writer
was still unfinished when the remaining opening window expired, after approximately
29.6s of observed writer time. That is an in-flight elapsed observation, not a
completed request duration. Final capture contains one in-flight request; the local
process subsequently exited. Remote completion/cost is unknown, not proven canceled.
The in-flight duration is excluded from completed-stage timing distributions.

No generic incomplete-decision or schema-invalid rejection was observed in these
three transitions. One opening completed under the corrected requested contract,
but raw wire bodies were not saved, so the precise provider encoding is not asserted.
This supports limited end-to-end compatibility; it does not prove all old errors
are fixed or that the new protocol is reliable across roles and conditions.

Only Methodology reached displayed dialogue. Its accepted question asks how the
workload will be matched between baseline and pilot periods, citing synthetic
line4, which explicitly proposes matched workload/time bands. It is grounded in
the stated proposal and makes no claim of completed effectiveness. This is a narrow
agent grounding observation, not human approval or overall question-quality evidence.

Ethics, Impact and Critical were never reached. No Bisaya answer or panelist reply
was displayed, so modern-Bisaya quality remains untested. No complete defense,
coaching report, successful answer-to-next-question transition, hosted transport
or installed-device behavior was established.

The only answer attempt yielded zero next questions within15s (0/1). That sample
is too small for a general achieved-rate claim; the usual10–15s target is unproven.
Both failures returned at the preserved45s processing bound, with up to1ms local
scheduling overhead. No timeout or allowance was extended to manufacture success.
No automatic retry was observed. No lookup measurements were supplied; they remain
unknown. Available request usage and unknown metrics are separate in the summary.

## Cost and cap

Three of five requests supplied cost receipts totaling **US$0.001009595**.
Two requests have missing receipts, retaining **US$0.042272400** in conservative
benchmark reservations. Total known cost plus holds isUS$0.043281995, below the
approvedUS$1 admission ceiling. This is not an exact final bill. Reservations were
not reset or released without evidence; no extra call was made to chase a result.
Stage-record count matches the five campaign ledger requests. Four stage records
identify OpenInference; the final unfinished writer has no captured provider identity.

## Decision and remaining work

Keep the existing settings unchanged. A successful opening now exists on the
corrected route, but observed interactive latency still blocks the workflow.
Lower reasoning alone did not prevent the DeepSeek answer-review timeout in this
sample. These results do not support a new model ranking or a candidate promotion.

Next prepare a focused comparison of faster interactive settings/providers or role
models, preserving source validation, scrutiny, privacy, prices and the45s cap.
The initial planner/writer sequence also needs its combined latency measured.
Any proposed replacement requires actual role-quality evidence; any additional
paid campaign needs its own concrete plan and authorization. Do not silently switch
models, raise limits or remove agreed planning stages from these results.

Ticket08 remains4/7: all-role compatibility/quality and justified settings selection
criteria2,4,5 stay open. Ticket09 must carry this failed/incomplete gate forward.
Runtime source was unchanged by this retest. The latest offline code verification
remains852 Python tests with providers mocked,414 React tests/build and26 real-local
PostgreSQL checks with provider HTTP mocked; none was rerun or substituted for these
actual-provider observations. No visual, human, hosted or native readiness claim.
No push or deployment.

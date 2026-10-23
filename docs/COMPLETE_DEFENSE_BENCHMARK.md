# Complete typed-defense candidate benchmark

Prepared and executed on 2026-10-23 for responsiveness ticket 08 under the user-approved **US$5 total campaign cap**. **Failed/incomplete provider gate.**
See [actual results](../.scratch/defense-turn-responsiveness/reviews/08-complete-candidate-results.md).
Runtime settings remain unchanged. Earlier paid campaigns are finished and their
allowances/ledgers cannot authorize this new campaign.

## Question to answer

Can the promising routing and Qwen writer settings carry a complete typed defense,
including all four reviewer roles, final coverage assessment and every required
coaching section? Earlier mini-runs stopped before this; single-stage Qwen results
cannot establish full answer-to-question latency or complete-defense quality.

## Frozen candidate and scope

The candidate retains the current Standard models, prompts, output limits,
interaction reasoning, focused evidence/lookup, one eligible transient retry,
45-second interactive processing window, privacy/price controls and run/coaching
allowances. It changes only:

- DeepSeek requests: `provider.only=["deepinfra"]`.
- Qwen requests: `provider.only=["alibaba"]`,
  `provider.ignore=["alibaba/us-east-1"]`.
- Impact **question writing**: `reasoning={"enabled":false}`. Its combined
  answer interpretation/planning retains the existing 1024-token reasoning budget.

Four built-in synthetic papers: quantitative English, qualitative modern Bisaya,
theoretical long English and mixed computational/design long Bisaya. Each receives
an eight-question maximum, its existing four-topic confirmed fixture map and
approach-specific answer scripts. Mapping is locally validated, with no mapping
inference. Longer fixtures are about 37 KB, mostly repeated background; they do
not establish arbitrary long-paper performance.

The runner answers every question until the server validates completion, up to
eight originals and one same-question reply each. It accepts early coverage
completion only through the existing validator. It does not force reviewer
selection, correct rejected plans or invent an accepted answer. A failed stage or
unresolved exchange ends that attempt; any valid saved answer/plan is recorded.
Existing automatic retry applies, but no manual retry campaign is added silently.

After a complete defense, the runner uses the same funded coaching client and
`CoachingProgress` as typed Streamlit: overview followed by bounded three-answer
sections, full membership validation and preserved ready sections on failure.
Coaching retains its existing 90-second request deadline, separate from the
interactive 45-second transition cap. A failed section stops the attempt without
replaying completed sections. This measures provider/typed-domain completion;
it makes no claim about multiplayer UI, financial settlement, hosted transport,
installed devices or a human-reviewed report.

## Spending and execution gate

Credential-free plan:

```bash
.venv/bin/python -m tests.reviewer_benchmark --plan --complete-candidate
```

Exact plan: [08-complete-candidate-plan.json](../.scratch/defense-turn-responsiveness/reviews/08-complete-candidate-plan.json).
Ordinary conservative question-plus-coaching bounds total **US$4.6112142**.
The approved **US$5 campaign admission cap** included all requests, retries,
lookups and same-question exchanges. This exact four-case campaign is now finished;
remaining nominal allowance does not authorize more experiments. This is
an admission/reservation limit, not an expected bill or cancellation guarantee.
Supplied cost receipts reconcile holds; absent/conflicting receipts retain their
full conservative holds. Prior campaign holds remain untouched.

The isolated artifact is `.local/complete-benchmark/checkpoint`, based on
`4a6be54` plus nine hashed benchmark/test/fixture files. Root and frozen plans match.
Its ignored launcher checks frozen hashes and exact plan before loading only the
named local key, rejects existing output, and uses a separate database/ledger.
No private upload or application account database was used. The executed command
is preserved below; existing-output protection prevents repeating this campaign:

```bash
.venv/bin/python .local/complete-benchmark/run-approved-campaign.py --execute-approved
```

## Evidence and acceptance

Existing content-free timings include completed/failed/in-flight requests,
requested restrictions versus observed providers, supplied tokens/cost and
unknown metrics. Full-run outcome records add actual/missing reviewers, accepted
answer count, pending-input/recovery stage, defense completion, coaching membership,
ready sections and generated coaching feedback. Exports omit original answer
fields and raw provider JSON/hidden reasoning. Generated feedback may quote the
built-in synthetic wording; it remains quality evidence rather than telemetry.

Final-answer assessment is a completion measurement, not an answer-to-next-question
sample; coaching timings are separate. Report the fraction/distribution within
10/15 seconds including failures, timeout/retry/lookup counts and all missing
roles/sections. `provider_gate` and human-quality fields stay unreviewed even if
all requests validate. Review grounded premises, useful scrutiny, brief reactions,
source interpretation and English/Bisaya wording for every role. A citation match
alone cannot certify quality.

There is no same-campaign baseline or repeated sample here: use earlier results
as historical context without pooling different protocols or claiming a causal
speedup. A failed gate leaves production unchanged. Selecting new defaults needs
a separate reviewed policy change preserving existing saved runs.

## Preparation verification

The frozen artifact passed **871 Python tests in 208.457 seconds**, offline with
external providers mocked. Targeted benchmark checks passed 35 tests in 20.510
seconds. A separate HTTP-mocked CLI check exercised all four cases: each produced
eight resolved questions, all four roles and eight coaching cards through 21
scripted requests, with valid report/measurement artifacts and an unreviewed gate.
These are instrumentation/domain checks, not actual model completions.

Independent Standards review found zero hard violations and one optional
maintainability smell (benchmark coaching orchestration mirrors Streamlit).
Spec review found zero new confirmed findings. The inherited `target` metric
counts original-answer attempts only, excludes probe replies and completion,
and includes same-question outcomes in its denominator. Inspect phase-separated
transition distributions and report reply-to-next-question timings separately;
do not present that inherited metric as covering all successful reply paths.

No frontend/runtime code changed. Previous React/build, PostgreSQL, browser,
hosted and installed-device evidence is separate and was not rerun here.

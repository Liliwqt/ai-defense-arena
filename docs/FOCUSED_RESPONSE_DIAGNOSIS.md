# Rejected focused openings: offline diagnosis

2026-10-23, starting commit `92c99fd`. No new paid call has been made.

The prior pilot reported six generic generation failures and one invalid response,
but retained no raw model bodies. Their exact historical causes cannot be recovered.
The following is a proven contract defect that reproduces the same rejected-opening
symptom; it is not proof that every prior failure had this cause.

## Reproduction and cause

Fast feedback loop:

```bash
.venv/bin/python -m unittest tests.test_evidence_contract -v
```

Before the fix, its HTTP-boundary opening regression failed in0.141s on an isolated
committed artifact. The mock provider followed the actual advertised JSON schema,
then the app raised `QuestionGenerationError: The AI returned an incomplete decision`.
No network, secret or provider delay is needed to reproduce it.

The focused lookup wrapper made every normal decision field nullable to permit a
lookup alternative. A provider could therefore return a question with `lead_in=null`
while `lookup=null`. The outgoing schema accepted that response, but converting it
back to the required normal question rejected it. The full-evidence baseline did
not advertise that ambiguity. An empty opening reaction should be a string.

Three ranked hypotheses were checked separately: nullable normal fields, citation
validation, and timing/funding. Changing only null reaction to empty string made
the minimal loop pass. A bad citation produced a different `InvalidQuestionResponse`;
no elapsed provider time was involved. This isolates the contract mismatch.

## Correction

Focused responses now contain `result` and `lookup`. A normal response places the
original complete typed decision/question in `result` and sets `lookup=null`.
A lookup sets `result=null` and supplies the bounded query. The normal schema retains
its required fields, source IDs and types; normal reaction/source fields are not
made nullable for the lookup alternative. Empty/both-active branches are rejected.
Original citation, coverage and lifecycle validation still runs after parsing.

Older flat SDK/test responses remain accepted only through validation against the
original domain schema. Unknown outer fields and incomplete normal data remain
invalid. This compatibility path is not advertised in new provider requests.
It avoids breaking existing saved-policy/test adapters; it does not accept a null
normal reaction or invent a citation. No model/reasoning/output/spending/timer,
mapping or coaching policy changed.

Diagnostics retain only a whitelisted reason code and the failing request stage:
`response_schema_invalid`, `evidence_missing_result`, `evidence_mixed_result`,
`processing_window_expired`, a sanitized HTTP status, or `unclassified`/`invalid_result`.
No exception message, provider response, hidden reasoning, answer text or credential
is added to measurement logs. Unknown historic errors stay unknown.

## Better synthetic scripts and prepared retest

Method answers now explain the actual approach: paired time comparisons and
uncertainty; qualitative coding, negative cases and an audit trail; a counterexample
challenging sufficiency rather than necessity; or matched computational benchmarks
with failed runs retained. Those details appear in the synthetic sources. Bisaya
answers are substantive language samples without repeated “Bisaya lang” commands.
Scripts still cannot guarantee a good answer to every adaptive probe; record any
legitimate unresolved gap rather than forcing a reviewer transition.

Changed source/answer fingerprints distinguish these v2 cases from the historical
pilot. Existing evidence/ledger is immutable; do not combine their results as if
inputs or wire contracts were identical.

Inspect the two-run plan without a key or provider request:

```bash
.venv/bin/python -m tests.reviewer_benchmark --plan \
  --cases quantitative-en qualitative-bisaya --conditions current
```

It uses the existing four Standard role assignments/reasoning, the new normal/lookup
contract and approach-grounded v2 scripts. It attempts an opening and up to four
answers per case (one same-question reply each), aiming to reach every role without
forcing acceptance. Mapping/coaching calls are excluded. Under the prepared defaults,
ordinary conservative request bounds totalUS$0.5239734. Proposed campaign capUS$1
also covers extras and can stop the pilot early. This is a bound, not an expected bill.
New paid execution needs separate authorization; the previous approval covered the
completed original twelve-run pilot. Provider support, real timing, all-role quality
and modern-Bisaya quality remain open until that evidence exists.

Once authorized, configure the key locally and use a **new** output directory:

```bash
.venv/bin/python -m tests.reviewer_benchmark --execute --max-usd 1 \
  --cases quantitative-en qualitative-bisaya --conditions current \
  --output .local/reviewer-retest-02
```

This document prepares the action; it does not authorize or start it. Keep strict
privacy/price/routing constraints and the45s processing cap. No automatic model
fallback, ceiling reset, candidate promotion, push or deployment follows from mocks.

## Verification and prevention

Final isolated Python suite:852 passed in213.344s, AI/Google/payments mocked.
React414 tests/build passed on unchanged frontend. Real local PostgreSQL26 checks
passed in36.616s, provider HTTP mocked; owned fixture stopped. Independent review:
Spec0 actionable findings; Standards0 documented violations and one nonblocking
fixture-map duplication suggestion. No visual, hosted or live-provider approval.

The original funded HTTP reproduction now passes, as do nested lookup, mixed/empty
rejection, legacy compatibility and safe-diagnostics checks. No temporary debug
logging remains. The missing protection was a contract test whose mocked provider
followed the actual advertised schema, including legal nullable values. Existing
happy-path fakes returned valid flat domain decisions and missed that mismatch.
Keep schema-conforming positive/negative fixtures beside the funded HTTP tests;
this fix needs no new architectural layer.

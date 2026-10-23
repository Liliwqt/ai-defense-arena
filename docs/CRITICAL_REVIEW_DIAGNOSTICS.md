# Critical review rejection diagnostics

Prepared 2026-10-23 after the [incomplete full candidate campaign](../.scratch/defense-turn-responsiveness/reviews/08-complete-candidate-results.md).
The separate US$0.06 replay was approved and has finished: one valid decision
and one `plan_invalid_assessment` rejection. [Actual results](../.scratch/defense-turn-responsiveness/reviews/08-critical-replay-results.md).
Production model/routing settings remain unchanged. Its unused nominal allowance
does not authorize additional experiments.

## Local assessment-schema correction — 2026-10-24

The authorized replay identified an invalid assessment but did not retain the
specific bad field. It does not establish the cause of the earlier full-run
failure. The new local correction constrains a combined submission's assessment
to the server's prospective turn index and topic. Its reason must contain
non-whitespace text and remain within the existing 600-character limit. Strict
integer validation still rejects boolean or string turn identifiers.

The assessment remains nullable for clarification and probe responses. Existing
submission checks and the final prospective-plan validator still check action
combinations, coverage, timeout status and eligible next moves. Invalid responses
are rejected, without repairing their metadata or changing models, reasoning,
providers, prices, timers, retry rules or spending limits. React and typed
Streamlit share this response-construction path; separate legacy planning keeps
its existing contract.

The diagnostic now captures and parses the same response-schema class used by
the real funded request. Running `--plan` on this updated source therefore
describes a different request from the already completed replay. Its historical
plan, source checkpoint, results and ledger remain unchanged. The separately
authorized [two-request retest](../.scratch/defense-turn-responsiveness/reviews/08-assessment-retest-results.md)
has now finished: both assessments passed the constrained parser, but one review
failed an incomplete next-reviewer/topic selection and only one fully validated.
Reported total US$0.000531543, no missing receipts, final in-flight count zero.
This small result does not establish reliable combined decisions or full-defense
speed/quality. Further paid testing requires its own reviewed plan and approval.

The [local correction review](../.scratch/defense-turn-responsiveness/reviews/08-assessment-schema-correction.md)
records 884 isolated Python tests (external providers mocked), 414 React tests,
the production build and 38 targeted checks passing. Independent source review
reported zero Standards and zero Spec findings for this correction. These checks
do not establish actual model acceptance or human review of the checkpoint.

## What is known

The failed Critical combined review returned HTTP200 and a supplied usage receipt,
then raised `QuestionGenerationError` before any parsed interpretation was captured.
The original response content was deliberately not logged. Its exact rejection
cannot be recovered from that record. Do not label it a proven bad schema, null
field, invalid plan or failed lookup.

A deterministic HTTP-mocked reproduction confirmed the observability gap: a
schema-valid answer response containing conflicting clarification text was
rejected as `unclassified`. The same code path now reports
`submission_answer_has_clarification`, retaining the prior exception class,
message and rejected/pending state. This is an instrumentation fix, not proof
that the historical model returned that field.

## Content-free classifications

`backend/response_diagnostics.py` allowlists static rejection codes. Existing
interpretation, prospective-plan and bounded-lookup guards attach them to the
same exceptions they already raised. The benchmark exports only known codes;
unrecognized or non-string attributes remain `unclassified`.

The codes distinguish missing interpretation, conflicting probe/answer fields,
missing assessment or selection half, invalid clarification, invalid coverage,
premature completion, ineligible reviewer/topic, duplicate question and empty or
exhausted evidence lookup. No validation is relaxed, rejected response rewritten,
retry added, model switched or raw response/answer/reasoning logged. Failure
messages shown to users and retry classifications retain their existing behavior.

## Executed minimal paid diagnostic

The new credential-free command is:

```bash
.venv/bin/python -m tests.critical_review_probe --plan
```

[Prepared plan](../.scratch/defense-turn-responsiveness/reviews/08-critical-replay-plan.json)
replays exactly two identical **Critical combined-review requests**, using the
seven displayed synthetic questions, six role-script answers and the pending
seventh answer from the completed campaign. Citations, including kind/location
and surrounding source, are rebuilt with the original resolver. It uses a fixed new synthetic map
ID, so this is a reconstruction, not retained original request bytes. No private
paper or answer is involved.

The original GLM model, low reasoning, output6144, route selection, strict schema,
privacy/price limits and45-second diagnostic deadline stay fixed. No earlier
mapping/planner/reviewer call, next-question writer, coaching, automatic retry or
broader lookup dispatch occurs. A lookup request is reported without fetching
or spending again. Valid answers pass both the original submission validator and
prospective research-plan validator; other valid actions retain their meanings.
Nothing publishes to a room or accepts an app answer.

The two conservative reservations total **US$0.0506934**. The approved **US$0.06 total campaign cap** covered exactly these two requests, with unknown-cost
holds retained and a separate ledger. This is not expected billing or a guarantee
that remote work stops at a local timeout. A result may not reproduce the earlier
failure; it can establish the current response's accepted action or precise safe
rejection class without claiming the historical cause.

The source, exact plan and tests were frozen before approval. The ignored launcher
verified them before privately loading the named local key and refuses existing
output. This approved campaign is now finished; no extra paid request is included.

Provider capacity is a separate problem. [Public research](DEEPSEEK_PROVIDER_CAPACITY.md)
identifies exact `inference-net/fp8` as a same-model candidate; its capacity and
complete-turn quality are untested. Do not change runtime routing or add BYOK or
fallback account settings from catalog metadata.

Execute mode requires process database settings already pinned to the exact
new campaign ledger, which the prepared launcher sets. Restoring temporary
settings therefore keeps late timeout receipts in that same ledger. This does
not guarantee a late receipt will arrive before process exit; unresolved holds
and in-flight counts must still be disclosed.

Independent source review found zero hard Standards violations and zero confirmed
Spec findings; duplicated bounded-probe orchestration is an optional maintenance
concern. The ledger-pin correction passed recheck. The final citation-fidelity
refinement also passed Spec recheck. These are source reviews, not user approval
or evidence about the real model response.

Nine focused checks passed with provider HTTP mocked, including the previously
unclassified rejection, valid decisions, empty lookup, unchanged rejected state,
source citation context and refusing an unpinned execution ledger. The final isolated Python gate passed **880 tests in184.875s**, with external
providers mocked;414React tests and the production build passed. The later approved two-request evidence is separate from these mocked checks;
no account configuration change occurred.

## Local coherent-selection correction — 2026-10-24

The next correction now advertises one `next_move` candidate ID instead of
independent reviewer/topic/follow-up fields. A per-request server map resolves
the ID to one full original domain selection. Complete legacy responses must
match an entire candidate; incomplete, unknown or mixed formats are rejected.
Original action and prospective-plan guards remain authoritative, including
completion and eligibility after assessment. Clarifications and probes stay on
the existing question. Separate opening/timeout planning remains unchanged.

The [correction review](../.scratch/defense-turn-responsiveness/reviews/08-coherent-selection-correction.md)
records 888 isolated Python tests (external services mocked), 414 React tests,
the production build and 62 targeted checks passing, with zero independent
Standards/Spec findings. Replay parsing uses both the actual envelope and result
schema classes. No further provider request or key read occurred.

A [new two-request plan](../.scratch/defense-turn-responsiveness/reviews/08-coherent-selection-plan.json)
was separately approved under a fresh US$0.06 campaign cap and has
[completed](../.scratch/defense-turn-responsiveness/reviews/08-coherent-selection-results.md):
one valid answer/prospective plan in 5.980s and one rejected non-probe action
with probe data in 23.245s. Reported cost US$0.000528844, no missing receipts or
in-flight requests. The next correction should make answer, clarification and
probe response shapes mutually exclusive while retaining existing guards.
Actual complete-contract reliability, full-defense performance and provider
capacity remain open. No extra experiment, model promotion or publication followed.

## Local exclusive-action correction — 2026-10-24

The combined result now uses three strict shapes: answer requires assessment
and candidate selection; clarification requires its explanation; probe requires
its request/references. Each forbids other actions' fields. A pending probe reply
offers only answer or clarification. The lookup envelope remains unchanged.
Legacy compatibility omits only unused null slots, never contradictory non-null
data. Original domain validation and run policy settings remain intact.

The [source review](../.scratch/defense-turn-responsiveness/reviews/08-action-contract-correction.md)
records 892 isolated Python tests (external services mocked), 414 React tests,
the production build and 66 targeted checks passing, with zero independent
Standards/Spec findings. No further provider request or key read occurred.

The [fresh two-request plan](../.scratch/defense-turn-responsiveness/reviews/08-action-contract-plan.json)
was separately authorized under a fresh US$0.06 cap and has
[completed](../.scratch/defense-turn-responsiveness/reviews/08-action-contract-results.md).
Both isolated outcomes passed application validation: answer/prospective plan
19.263s and same-question probe18.665s. Reported total US$0.000532864, no missing
receipts or in-flight work. Compatibility may accept valid legacy formats, so
canonical provider enforcement and probe quality are not established. Review
alone still exceeds15s; full-defense/all-role reliability and the separate
capacity blocker remain open. No extra experiment or publication followed.

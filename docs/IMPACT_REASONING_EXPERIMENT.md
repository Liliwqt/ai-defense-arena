# Qwen Impact reasoning comparison

Prepared and separately authorized/executed2026-10-23 under a US$0.15 cap.
[Actual results](../.scratch/defense-turn-responsiveness/reviews/08-impact-reasoning-results.md):
all four writer outputs passed validation; disabled mode took2.452/3.684s and
reported zero reasoning tokens versus10.404/8.643s for the current budget. This
is a small writer-only sample. Runtime models, reasoning, routing, saved runs,
timers, credits and prices remain unchanged. This completed campaign does not
authorize more paid requests.

## One variable

Compare the same reconstructed saved Impact writer inputs on the Alibaba route
excluding US-East, which previously returned valid questions in both cases.

| Condition | Requested reasoning | Other request fields |
| --- | --- | --- |
| Baseline | `{"max_tokens":2048}` | Identical |
| Candidate | `{"enabled":false}` | Identical |

Alibaba places both2048 and512 in its documented native low tier. The previous
successful requests used410/317 reasoning tokens, already below512. A small
budget reduction is therefore not a demonstrated change in effective reasoning.
Thinking-off is a clearer candidate, but OpenRouter's exact route translation
and the observed effect still require real requests. See the primary-source
[reasoning support research](QWEN_REASONING_SUPPORT.md).

This is a **writer-only** experiment. Answer interpretation and adaptive planning,
other reviewers, mapping and coaching are not invoked. No full-turn speed or
all-role quality claim follows from its results. Source prompts, accepted history,
saved selection, model, output8192, route selectors, price/privacy filters,
strict schemas, validation and45s stage window match across conditions. No
`exclude:true`, `/no_think` prompt edit, native-field adaptation, fallback,
automatic retry or lookup expansion is introduced.

The captured base policy stays unchanged; `request_reasoning` and the request hash
record the actual benchmark-only override separately. A candidate is not applied
to a running room or treated as a selected new runtime policy. Unsupported flags,
rate limits, lookup requests, partial responses and validation errors remain
honest outcomes. Nothing retries until it happens to pass.

## Four requests and evidence

Quantitative English runs baseline then candidate. Qualitative/Bisaya reverses
that order. This is one exploratory pass, not general speed or quality evidence.
The same synthetic fixtures/case fingerprints and stable reconstructed map identity
are reused; the original prior HTTP bytes were not retained, so this does not
claim an exact historical request replay.

Use [the captured plan](../.scratch/defense-turn-responsiveness/reviews/08-impact-reasoning-plan.json).
Conservative reservations total **US$0.089341200** across four requests. Separately approved
campaign admission cap: **US$0.15**, now completed. Output limits and conservative price bounds
are not reduced to manufacture apparent savings. Supplied cost receipts reconcile
holds; omitted receipts retain reservations. This is not an expected/final bill.
Use a fresh persistent ledger and never reset an existing campaign or reuse an
old approval's nominal remainder.

Record parsed questions/reactions/citations, per-request elapsed time, errors,
provider identity, any supplied reasoning/input/output tokens and cost, unknowns,
funding and in-flight state. Check schema/citations/saved selection and read the
actual questions for unsupported assumptions (including the earlier raw-logs
caveat), research relevance, brevity and language. These are agent observations,
not human/native-speaker approval. Faster malformed or shallow output does not
pass the gate.

A request with supplied zero reasoning tokens supports thinking-off behavior for
that sample. Missing usage is unknown; a requested flag or hidden reasoning is
not evidence of zero thinking or lower billing. Provider load, output length and
caching can vary even with matching prompts; four samples cannot isolate them or
establish a reliable overall latency reduction. Full defenses and every reviewer
remain separate evidence.

## Reproduce without spending

```bash
.venv/bin/python -m tests.impact_route_probe --plan --reasoning-comparison
.venv/bin/python -m unittest tests.test_impact_reasoning_probe tests.test_impact_route_probe -v
```

The flag is explicit; default route-probe behavior/plan remains unchanged.
Tests check identical non-reasoning payloads, stable source/request hashes,
fixed routing/output, actual HTTP request/condition attribution and unknown usage.
The three new tests first failed before the comparison helpers existed; focused
30checks passed in17.562s, external provider HTTP mocked. Final isolated `.venv/bin/python -m unittest discover -v` passed **866 tests
in185.832s**, offline with AI/Google/payments mocked. Frozen hashes and repeated
credential-free plans match; the previous default route-probe plan is unchanged. No frontend/runtime changes or live readiness claim.

After separate spending approval only, the ignored launcher
`.local/impact-reasoning/run-approved-comparison.py --execute-approved` verifies
its eight frozen source/fixture hashes and exact plan before privately loading
only the named local key. It rejects an existing output directory and executes
only this fixed comparison under the approved cap. No key is sent in arguments,
artifacts or chat. Defaults remain unchanged after measurement; any selection
needs its own reviewed change and broader full-defense evidence.

The separately authorized [complete-candidate campaign](../.scratch/defense-turn-responsiveness/reviews/08-complete-candidate-results.md)
then produced two more valid English Impact questions with requested thinking off,
2.837/3.100s and supplied zero reasoning tokens. Impact combined interpretation
kept1024budget and took14.448/22.610s. This reinforces the writer-only finding,
not a whole-transition speed promise or reason to disable other tasks' reasoning.
The complete gate failed elsewhere; no runtime defaults were promoted.

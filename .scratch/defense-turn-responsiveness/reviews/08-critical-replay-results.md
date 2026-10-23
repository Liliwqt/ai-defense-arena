# Critical isolated replay — 2026-10-23

**Two approved requests completed: one valid decision, one rejected coverage
assessment.** This reveals a concrete current failure category; it does not prove
the exact cause of the earlier full-defense failure. Runtime policies remain
unchanged and ticket08's full provider gate stays failed/incomplete4/7.

[Exact plan](08-critical-replay-plan.json),
[content-free measurements](08-critical-replay-measurements.jsonl),
[summary/provenance](08-critical-replay-summary.json),
[protocol](../../../docs/CRITICAL_REVIEW_DIAGNOSTICS.md).

## Executed scope

Exactly the two user-approved synthetic Critical combined-review requests ran
under a fresh **US$0.06 total campaign admission cap**. Frozen base `4a6be54` plus
18 scoped file hashes and the exact prepared plan were checked before privately
loading the named local key. Three runtime files contain only the reviewed
diagnostic delta over that base; unrelated pending reasoning/budget work was
excluded from the frozen artifact and preserved in the workspace.

Both requests used the same reconstructed seven-question English synthetic state,
six role-script answers and pending seventh answer, grounded source/citation
context, model `z-ai/glm-5.3-flash`, low reasoning and output6144. The new stable
map ID means reconstruction rather than retained original request bytes. Actual
provider was **OpenInference** for both requests. Strict schemas, validation,
45-second diagnostic window, privacy/price filters and no fallback remained.
No earlier mapping/planning/question request, next-question writer, coaching,
lookup expansion, automatic retry, app credit transaction or room publication.

## Results

| Attempt | Full diagnostic time | Provider request time | HTTP | App validation | Supplied reasoning tokens |
| --- | ---: | ---: | ---: | --- | ---: |
| 1 | 21.871s | 21.715s | 200 | Valid `answer` decision and prospective plan | 1154 |
| 2 | 12.206s | 12.167s | 200 | `QuestionGenerationError`, `plan_invalid_assessment` | 493 |

Same prepared request hash/input context and9921supplied input tokens each.
Supplied completion totals1261/608 include reported reasoning; hidden reasoning
text and response bodies were not retained or exported. One pass and one failure
from identical inputs demonstrate variable outcomes in this small sample, not a
stable failure rate or a speed comparison. Both provider transports completed;
HTTP200 does not establish application-level correctness.

The second response passed submission interpretation far enough to construct an
answer's next-turn plan, then failed the unchanged prospective coverage-assessment
validator. That guard checks the prior turn/topic, allowed status and bounded
nonempty reason. In this non-timeout fixture, after typed response validation,
the remaining possible failures are an incorrect zero-based turn (expected6),
incorrect topic (expected`topic-4`), empty/whitespace reason or reason over600chars.
**Which predicate actually failed is unknown.** This narrowing is source/fixture
inference, not a retained response inspection.

The historical full campaign had no parsed interpretation captured before its
failure. This new replay reaches a later validation guard, so it may expose an
additional failure mode. Do not relabel the historical artifact or claim its
original cause is now proved. Original reports/ledgers remain unchanged.

No failed review was accepted or published. A valid isolated decision is not a
completed defense turn: no next question or coaching was generated. No rate-limit,
lookup request, observed automatic retry or45-second expiry occurred in these
two probes. Final in-flight requests:0. No semantic quality/native-language,
complete-defense, multiplayer, hosted or installed-device acceptance follows.

## Accounting and verification

Two campaign ledger requests, two supplied receipts: **US$0.000474176** total
(US$0.000301898 andUS$0.000172278). **No missing-receipt holds** in this campaign.
This is reported usage, not an audited account invoice. No previous campaign hold
was released or reset. The six-cent approval covered only these two requests;
remaining nominal allowance does not authorize extra experiments.

Read-only ledger reconciliation matches request counts, receipts and funding.
Exact executed18frozen hashes,15exactrootfiles/3ownpatch provenance, fixture/plan
hashes and public artifact hashes pass. Pre-run tracked fingerprints showed only
the authorized project log changed during inference. The subprocess database was
pinned to its isolated campaign ledger before execution. Raw results/plan/log/
ledger remain under `.local/critical-diagnostics/provider-output`.

The unchanged executed source previously passed **880 isolated Python tests
with providers mocked,414React tests and a production build**. Evidence-only
updates do not require a suite rerun; no fresh runtime change, push/deployment,
model/routing promotion, extra paid call or human-review completion.

## Next correction

Make the generated coverage assessment conform to server-owned turn/topic and
nonempty bounded reason constraints in its response schema, preserving the
existing rejection checks as the authority. Test all four possible violations
offline before a narrow live retest; do not silently repair an invalid assessment
or add an AI evaluation request. This is a proposed correction, not implemented
or proven here.

DeepInfra shared-pool429s remain a separate capacity blocker from the prior
campaign. Public metadata identifies same-model `inference-net/fp8` as a candidate,
not evidence of available or admissible capacity. No provider comparison or
runtime switch was included in this six-cent approval.

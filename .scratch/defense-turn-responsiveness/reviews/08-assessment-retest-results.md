# Assessment-schema live retest — 2026-10-24

**One validated review; one incomplete next-move selection.** Both requests
passed the new assessment constraints, but the combined review is still
unreliable. Ticket 08 remains **4/7**, with its full provider gate open.

[Exact plan](08-assessment-retest-plan.json),
[content-free measurements](08-assessment-retest-measurements.jsonl),
[summary and provenance](08-assessment-retest-summary.json),
[offline correction](08-assessment-schema-correction.md).

## Scope

The user's “go ahead” authorized the proposed fresh two-request campaign under
a **US$0.06 total admission cap**. Exactly two synthetic Critical combined
reviews ran from the verified assessment-schema checkpoint: base `4a6be54`
plus reviewed local diagnostics and response constraints, with 19 frozen source
hashes. Foreign pending reasoning/budget changes were excluded from that
checkpoint and preserved in the workspace.

Model `z-ai/glm-5.3-flash`, low reasoning, output limit 6144, privacy/price guards,
no fallback and the 45-second diagnostic window were unchanged. Both requests
used the same reconstructed English seven-question state and pending seventh
answer. The synthetic paper, prompts, policy and fixture match the earlier replay; only
the assessment schema changed. Actual serving provider: OpenInference for both.

No earlier mapping/planning request, next-question writer, coaching, lookup
expansion, automatic retry, private paper, app credit transaction or room
publication occurred. This is not a complete answer-to-next-question transition.

## Results

| Attempt | Diagnostic time | Provider time | HTTP | Application result | Reported reasoning tokens |
| --- | ---: | ---: | ---: | --- | ---: |
| 1 | 19.262s | 19.185s | 200 | Rejected: `submission_incomplete_selection` | 1063 |
| 2 | 14.594s | 14.551s | 200 | Valid `answer` and prospective plan | 852 |

Both responses passed parsing with the exact constrained schema sent to the
provider. The first reached the existing guard that requires next reviewer and
next topic to be either both present or both null. One was null and the other
was present. Which half was missing is unknown because raw responses were not
retained. The valid assessment does not make that inconsistent plan acceptable.
The second passed both submission and prospective-plan validation.

No assessment rejection, rate-limit error, lookup request or deadline expiry
was observed in these two requests. That is a small observation, not proof of
reliable schema enforcement, a reduced failure rate or improvement over the
earlier one-pass/one-failure sample. No invalid decision was repaired or accepted.
The historical full-run failure's exact cause remains unknown.

## Accounting and verification

Two requests and two supplied receipts: **US$0.000531543** total
(US$0.000286614 + US$0.000244929). No missing receipts or retained unknown-cost
holds in this campaign; final in-flight count **0**. The read-only isolated ledger
matches the request IDs, receipt sum, funding and US$0.06 ceiling. These are
provider-reported charges, not an audited invoice. Earlier campaigns and their
unresolved holds were not reset. This approval is finished; its unused nominal
allowance does not authorize more requests.

The launcher checked the frozen source, exact plan and absent output before
privately loading the named local key. Database settings were pinned to the new
campaign ledger. Post-run verification confirmed all 19 source hashes, exact
prepared/public plan, result/measurement provenance and unchanged source.
Only the authorized project log changed among tracked files during inference.
Raw content-free results, plan, log and ledger are retained under ignored
`.local/assessment-schema/`; historical replay artifacts remain unchanged.

The executed code previously passed **884 Python tests with external providers
mocked, 414 React tests and the production build**. Evidence updates did not
change runtime code, so those suites were not repeated. Actual provider evidence
here is separate from offline, browser, hosted and installed-device evidence.
No runtime promotion, push, deployment or human-review completion is claimed.

## Next correction

Represent the eligible next move as one coherent selection, rather than
independently nullable reviewer/topic fields. Preserve server eligibility,
assessment, completion and action validation, including clarification/probe
behavior. Add an HTTP-mocked regression for the mismatched pair before a new
live test. This is a proposed correction, not implemented or proven here.

Do not spend on a complete defense while the combined decision remains a known
blocker. The separate DeepInfra shared-pool 429 issue also remains open; these
GLM requests did not test it. A same-model provider-capacity comparison needs
its own concrete plan and spending authorization. No further paid test ran.

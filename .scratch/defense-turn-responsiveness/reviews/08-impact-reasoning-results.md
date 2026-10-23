# Ticket 08: authorized Qwen current-versus-disabled reasoning probes

2026-10-23. Four approved requests completed under a separate **US$0.15 campaign
cap**. All returned valid Impact questions. Disabled-mode responses reported zero
reasoning tokens and were faster in this small batch. **The full provider gate
remains failed/incomplete4/7; app settings remain unchanged.** No extra paid
campaign, push or deployment.

Executed frozen `4a6be54` plus eight hashed benchmark/fixture files, previously
verified by866isolated Python tests with providers mocked. The launcher matched
the exact [prepared plan](08-impact-reasoning-plan.json) before privately loading
the named local key. Only synthetic reconstructed saved Impact state was sent;
no private paper or production account database. Original results/plan/log/ledger
remain unchanged under ignored `.local/impact-reasoning/`.

Evidence: [sanitized measurements](08-impact-reasoning-measurements.jsonl) and
[summary, hashes, captured policies and actual overrides](08-impact-reasoning-summary.json).

## Observed writer results

| Synthetic case | Current budget2048 | Requested reasoning off | Reported reasoning tokens: current / off |
| --- | ---: | ---: | ---: |
| Quantitative English | 10.404s | 2.452s | 346 / 0 |
| Qualitative/Bisaya answers | 8.643s | 3.684s | 378 / 0 |

Both conditions kept `qwen/qwen3.8-flash`, the Alibaba route excluding US-East,
visible prompts/history/schema, output8192, strict citation/selection validation,
privacy/price/no-fallback controls and45s window. Only the requested reasoning
object changed: `{"max_tokens":2048}` versus `{"enabled":false}`. English ran
current then disabled; Bisaya reversed the order. All requests reported Alibaba.
Serving family names do not expose an exact endpoint or location.

The disabled request's zero reasoning usage is explicitly supplied evidence,
not an inference from an omitted field. Its observed output-token counts were
63and90 versus423and477 for current mode, including supplied reasoning usage.
The captured base policy remains unchanged; actual request overrides/hashes are
recorded separately. No runtime run had its settings rewritten.

There were no errors, lookup requests, retries or processing-window expirations;
final in-flight count was zero. These are **single Impact writer** timings,
including local parsing/domain validation, not complete answer-to-next-question
timings. Earlier interpretation/planning, reading/voting and browser transport
were not measured. No mapping, other reviewer or coaching request was made.

## Quality and limits

All four results passed the existing structured response, exact source-line6
citation and saved Impact selection/domain validation. Current English asks what
local decision/understanding the paired comparison provides; disabled English
asks how its bounded finding would matter operationally. The latter is phrased
as a future evaluation question, not a claim that findings already exist.
Current Bisaya asks about the specific contribution and recognition of its aim;
disabled Bisaya asks why the local education study matters. They examine related
Impact concerns without asserting a completed effectiveness result. The earlier
raw-logs specificity was not repeated in these four questions.

This is a narrow agent observation, not a semantic-quality certificate or human
native-speaker approval. The actual wording varies; the disabled Bisaya question
focuses on significance rather than the baseline's success-criteria emphasis.
Exact citation/eligible selection checks cannot establish equal research scrutiny.
The cases are short synthetic quantitative/service and qualitative/education
proposals. No theoretical/computational, difficult/long-context, Critical dialogue,
Impact answer interpretation, complete defense/coaching, browser/hosted transport
or installed-device evidence was added.

There is one sample per case/condition. Visible prompts match, but provider usage
reports24fewer input tokens in disabled mode; upstream adaptation, output length,
load and caching were not controlled independently. The same current-budget
writer took21–22s in the previous campaign but8.6–10.4s here, demonstrating timing
variability. Do not pool batches as a controlled speed estimate or promise a
production2–4s response. The zero-token/valid-output observations support the
candidate for these requests, not universal disabling of reasoning.

## Accounting and next decision

Four ledger requests match four request records and four outcomes. All four
supplied cost receipts, totaling **US$0.003903346**. Missing receipts and unknown
cost holds are zero for this campaign. This reconciles to the persistent ledger
and is below the approvedUS$0.15 cap; it is supplied receipt evidence, not an
audited account invoice. Prior campaigns' unresolved holds are unchanged.
The campaign is finished; no additional request is authorized by its remaining
nominal allowance.

Reasoning-off is a promising **Qwen Impact question-writer candidate** on the
tested route. Keep answer interpretation/planning, mapping, other reviewers and
coaching at their existing settings: none was evaluated for disabled reasoning.
Next prepare a complete research/mixed defense test using candidate routes/settings,
checking scrutiny, conversation continuity, all reviewers, deadline/retry behavior
and full transition times before a reviewed selection. That would be a new paid
campaign requiring a concrete plan and separate authorization.

Ticket08 stays4/7 and ticket09 carries the gate: this does not establish all-role/
difficult-context quality or final policy selection. No default was promoted.
Verification: actual approved four-request provider comparison, plan/source/artifact
hash and read-only ledger checks. No source changed during inference; latest
source gate remains866Python tests with providers mocked, not rerun for evidence
edits. Prior414React/build and26localPostgreSQL remain separate. No independent
code-review/human/hosted/native readiness or publication claim.

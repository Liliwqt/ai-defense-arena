# 08 — Measured reviewer settings and provider gate

**What to build:** operators can select defensible fixed interactive settings from
real comparable speed/quality evidence, or see an explicit gate preventing an
unsupported readiness claim.

**Blocked by:** 06 — Focused evidence and bounded broader lookup.

**Status:** ready-for-human

Source: [confirmed specification](../spec.md). Breakdown approved on 2026-10-21.

- [x] Reuse 01's baseline harness for identical synthetic papers/answers across fields,
  approaches, source sizes and English/modern Bisaya. Measure the current route,
  combined/focused route and bounded candidate role settings under disclosed
  comparable conditions; no private paper or key value is needed in artifacts.
- [ ] Validate actual combined schema/reasoning/context/privacy-route compatibility
  and grounded dialogue for every role, including difficult/long-context cases.
- [x] Report full transition/stage distributions, sample counts, failures, retries,
  broader lookup and supplied provider usage/cost. Routing time/first token alone
  is insufficient; missing metrics are unknown, not zero or invented savings.
- [ ] Tune supported interactive reasoning/output/context bounds without truncating
  required citations/schema or weakening research scrutiny. Keep distinct roles;
  replacement models require evidence, not advertised speed or intelligence.
- [ ] Capture any selected settings only for new policies, retaining current privacy/
  price/default ceiling/coaching guards and saved-run immutability. No automatic
  model fallback or mapping/coaching redesign without a reviewed dependency.
- [x] Evaluate the 10–15-second usual-transition target with disclosed achieved fraction
  and distribution, and preserve the deterministic 45-second processing bound.
  Report unmet targets before making a live-ready claim; do not silently extend
  waits or weaken validation.
- [x] Provide reproducible harness/output and record actual-provider acceptance
  separately from mocks. If credentials/evidence are unavailable, record the
  unsatisfied gate and keep required criteria open; no bypass for final readiness.

## Comments

2026-10-23 — Offline harness checkpoint implemented against user-approved
`8465a88`. [Protocol and commands](../../../docs/REVIEWER_BENCHMARK.md).
Four built-in synthetic cases compare separate/full, current combined/focused
and bounded lower-reasoning settings through the actual typed/provider contracts.
Persistent campaign admission, conservative unknown-cost holds, supplied usage,
retry/lookup measurement and safe synthetic decision/dialogue artifacts are wired.
No runtime defaults changed. Independent review corrections are implemented;
final verification is recorded in [review 08](../reviews/08.md).

**Historical offline checkpoint: 1/7 criteria checked.** Criteria 1–6 had scaffolding but
remain open pending actual comparable inference, per-role/schema/grounding and
language review, achieved timing/cost evidence and any justified settings selection.
Mocked results cannot satisfy them. Public catalog metadata is not that evidence.
No key is configured in the agent shell, and paid inference has not been authorized.
The proposed pilot is twelve synthetic mini-runs with a $5 campaign admission cap;
it can stop early if retries/lookups consume its allowance. Inspect the plan before
authorizing/configuring a local key; never send the key in chat. Gate is explicitly
unreviewed. Ticket09 must not treat this checkpoint as live acceptance.
No paid calls, push/deployment, human visual approval or provider-readiness claim
at that offline checkpoint.

2026-10-23 — Authorized live pilot completed; **partial4/7, failed/incomplete gate**.
[Actual evidence and limitations](../reviews/08-provider-pilot.md). All12
case/condition pairs attempted,29 provider requests and16 transition records.
Baseline openings3/4; current and lighter candidates0/4. No full defense or
combined submission ran, and only Methodology reached dialogue. Answer-to-next
question target is unproven; no model/reasoning settings promoted. Criteria1,3,6,7
now have actual measurement/disclosure evidence; per-role quality/compatibility
and justified settings selection criteria2,4,5 stay open. Fixed scripts contain
repeated language commands and insufficient approach-specific detail; do not
attribute those effects to model quality alone.

User approved oneUS$5-capped synthetic pilot and configured the key locally;
no credential was disclosed. Supplied chargesUS$0.011694779, plusUS$0.095164500
retained holds for4 missing receipts; final bill unknown. Original evidence/ledger
preserved; a reviewed active/late-request reporting correction reconciles stage
records and keeps incomplete legacy totals unknown. Final correction846 Python
(providers mocked),16 real-local-PostgreSQL checks pass; previous unchanged
414 React/build evidence applies. No additional paid campaign, push/deployment,
human visual approval or live-readiness claim. Ticket09 retains this unresolved gate.

2026-10-23 — Offline rejected-opening correction implemented and reviewed.
[Correction review](../reviews/08-contract-fix.md) records the schema-valid nullable
reaction reproduction and the normal-result/lookup envelope fix. Citation, budget,
timer and model policies remain intact; legacy flat responses still require a valid
original domain result. Diagnostics now identify safe failure reason/stage. V2
approach-specific scripts remove repeated language commands and use new fingerprints.
852 Python/providers mocked,414 React/build and26 localPostgreSQL checks pass.
Historical exact causes remain unknown. The prepared two-case Standard retest has
ordinary boundsUS$0.5239734 and proposedUS$1cap; no new paid call or authorization.
Actual-provider criteria2/4/5 stay open; no model promotion or publication.

2026-10-23 — User authorized the separate US$1 retest; both cases now ran on
`25d8a72`. [Retest evidence](../reviews/08-retest-results.md): English opening
accepted in32.206s, then low-reasoning DeepSeek combined answer review expired at45s.
Bisaya opening expired at45s while its writer was unfinished. Only Methodology
spoke; no successful answer-to-next-question transition or other-role quality
evidence. No schema-invalid/incomplete-decision error was observed in this small
sample, but the live gate remains failed/incomplete4/7. Five requests supplied
US$0.001009595 in receipts plusUS$0.042272400 retained holds for two missing receipts.
No model/reasoning changes, extra campaign, push/deployment or readiness claim.


2026-10-23 — Separately approved USD1.25 provider comparison completed: four
English/Bisaya mini-runs with identical policy/models/reasoning; only DeepSeek
gets model-scoped DeepInfra routing. [Results and limitations](../reviews/08-provider-routing-results.md).
All four openings passed. English auto37.153s versus DeepInfra13.952s; Bisaya
auto10.318s versus DeepInfra11.906s. DeepInfra yielded4successful follow-ups
(16.324–35.743s) from6attempts; auto0/2. Both DeepInfra runs stopped at unchanged
Qwen Impact writer HTTP429; automatic runs returned ineligible plans. Captured
auto plans used turn1 instead of0 and a non-follow-up Methodology option; offline
frozen-domain replay confirms both violations without changing validation or
claiming an unlogged exact exception sequence. Only Methodology/Ethics spoke,
no complete defense or all-role/difficult-context evidence. No next-question
transition met15s. Gate stays failed/incomplete4/7; no settings selected.
22requests/12transitions, finalinflight0;20supplied receipts USD0.016998490 plus
USD0.045566400 conservative holds for2missing Qwen receipts, accounted
USD0.062564890, not an exact bill. Original campaign/ledger preserved; no extra
paid request. Prepared benchmark source previously passed856Python/provider
mocks; source unchanged during inference. No publication or readiness claim.


2026-10-23 — Authorized USD0.15 focused Qwen Impact diagnostic completed.
[Results](../reviews/08-impact-probe-results.md):4single-stage requests, same
reconstructed synthetic saved-state inputs/model/reasoning2048/output8192.
Alibaba excludingUS-East returned2valid Impact questions in21.142/22.314s;
US-East requests both reportedHTTP429 with limit_sourceupstream_provider_shared_pool
and error_providerAlibaba, noRetry-After. This identifies these new failures,
not the exact historical automaticroute errors. English wording adds raw-logs
specificity not explicit in the source; quality/human review remains. No full
turn/defense, Critical or all-role/difficult-context proof. Gate remains4/7.
2receiptsUSD0.002126118 plusUSD0.044670600 unknowncostholds, accountedUSD0.046796718,
not exactbill.4requests/4outcomes, finalinflight0, no retries/extra paidcall or
settingspromotion. Source unchanged during inference; prior863offlinePython
providersmocked remains applicable. No push/deployment.


2026-10-23 — Separately approved USD0.15 same-route Qwen reasoning comparison
completed. [Results](../reviews/08-impact-reasoning-results.md):4/4writeroutputs
validated. Current2048budget versusrequestedenabledfalse:English10.404/2.452s,
Bisaya8.643/3.684s. Suppliedreasoning346/378current versus0/0disabled. Same
visibleprompts/model/route/output/schema/guards; no retries/lookups/timeouts.
Single-stageonly, smallcounterbalanced sample, upstreaminputtokens/cache/load
uncontrolled; notfull-turn orall-rolequalityproof. Candidatequestionfocus differs,
human/nativequalityreview pending. No settingspromoted; keepinterpretation, mapping
andcoaching reasoning unchanged.4receiptsUSD0.003903346, no missingholds,
finalinflight0. Originalledger/evidence preserved; no extrapaidcall/publication.
Ticket08 stays4/7 withall-role/difficultcontext/finalselectioncriteriaopen.

2026-10-23 — Complete typed-defense candidate benchmark prepared (not paid-run
approval). [Protocol](../../../docs/COMPLETE_DEFENSE_BENCHMARK.md) attempts four
synthetic eight-question defenses through final assessment and protected coaching;
records absent roles, partial sections and recovery without manufacturing completion.
Candidate uses DeepSeek/DeepInfra, Qwen/Alibaba excludingUS-East and writer-only
reasoning off; interactions/other reasoning unchanged. Ordinary conservative
boundsUSD4.6112142; proposed newUSD5campaign, not authorized/executed. Existing
4/7/provider gates remain open and production defaults unchanged.

2026-10-23 — User approved the separate USD5complete-candidate campaign; exactly
four attempts now finished. [Actual results](../reviews/08-complete-candidate-results.md):
English reached all4reviewers/7questions/6acceptedanswers, six valid transitions
10.944–34.019s (median15.569);3/7original-answer attempts met15s including failure.
Critical combined review returnedHTTP200 but no accepted interpretation, exact
rejectionunknown; pending seventh submission retained. Other3openings failed
at DeepSeek writer429, explicitly DeepInfra upstreamsharedpool/noRetryAfter;
saved plans remain writing-stage. No complete defense/coaching/Bisaya/longmixed
quality proof. Qwen2writerrequests2.837/3.100s reported0reasoning; interaction
still14.448/22.610s. No automaticretry/windowexpiry, lookupmetricsunknown.
21requests/11operations/finalinflight0;18receiptsUSD0.016413119 plus3unknowncost
holdsUSD0.062592900, accountedUSD0.079006019. Read-only ledger/hashes match;
no extra paidrequest/oldholdreset/runtimepromotion/publication. Gate stays4/7;
current frozen code retains prior871Python/provider-mocked evidence. Diagnose
Critical's safe rejection and providercapacity before another scoped paid test.

2026-10-23 — [Safe rejection diagnostics and minimal Critical replay](../reviews/08-critical-diagnostics-preparation.md)
verified locally: static allowlisted codes preserve validation/errorclasses/messages,
accepted/pending state and retryrules. Historicalcauseunknown, no semanticfixclaim.
New replay2identical GLMlow/6144requests reconstructs7questions/6savedanswers with
originalgroundedcitationcontext, no earlierstages/nextwriter/lookupdispatch/roomchange.
NewcapUSD0.06 proposed (boundsUSD0.0506934), notapproved/executed; oldapprovals/holds
untouched. Executeledger mustalreadybepinned; no latewrite toappdefaultpath.
880isolatedPython/providersmocked,414React/build pass;9newfocusedpass,wholemockCLI
2requests verified. IndependentStandards0hard/1optionalduplication,Spec0; lifecycle
concerncorrected/rechecked. Publicsame-modelinference-net/fp8 candidateunproven,
no runtimepromotion. Ticket08 remains4/7 with actualprovider gates unresolved.

2026-10-23 — User-approvedUSD0.06 [two-request Critical replay](../reviews/08-critical-replay-results.md)
finished. SameGLMlow/6144/syntheticturn: one valid answer+prospectiveplan21.871s,
one plan_invalid_assessment rejection12.206s; bothHTTP200/OpenInference. This new
failure is at prospective-plan validation, while historicalfailure had no parsed
interpretation captured: exacthistoricalcause remainsunproven. Remaining guard
possibilities inthisfixture: wrongturn/topic or empty/oversizedreason, actualbad
predicateunknown. No invaliddecisionpublication, earlierstage/writer/coaching,
retry/lookupdispatch/timeoutrateerror.2receiptsUSD0.000474176,0unknownholds,
finalinflight0; ledger/hash/sourcechecks pass. No runtimechange/extraexperiment/
oldholdreset/publication; gate stays4/7. Nextproposedfix: constrain known assessment
metadata/reason in response schema while preserving all original validators.


2026-10-24 — [Assessment-schema correction verified locally](../reviews/08-assessment-schema-correction.md).
Combined reviews now constrain assessment turn/topic to the prospective server
context, preserve strict integers, and require a non-whitespace reason within
600 characters. Original action/prospective-plan validators remain unchanged;
nullable clarification/probe assessment and separate legacy planning retained.
Replay parses its actual submitted schema. Independent Standards/Spec: zero
findings. Full isolated 884 Python (providers mocked), 414 React/build and 38
targeted checks pass. No new inference or runtime model promotion; historical
invalid field remains unknown. Gate remains 4/7, all scoped work local/uncommitted.


2026-10-24 — [Authorized assessment retest completed](../reviews/08-assessment-retest-results.md).
Exactly two GLM low/6144 synthetic Critical reviews: one rejected with
submission_incomplete_selection in 19.262s, one valid answer/prospective plan in
14.594s. Both constrained assessments passed parsing; independent nullable next
reviewer/topic fields remain inconsistent in one result. Both OpenInference
HTTP200. Two supplied receipts US$0.000531543, no unknown holds, final in-flight
zero. Exact plan/source/ledger/hash checks pass. No runtime change, additional
campaign, next writer/coaching or complete defense. Gate remains 4/7. Proposed
next fix: one coherent eligible-next-move selection with original guards retained.
DeepInfra shared-pool capacity is a separate untested gate; no route promotion.


2026-10-24 — [Coherent candidate selection verified offline](../reviews/08-coherent-selection-correction.md).
Combined review emits one next_move candidate ID, resolved to the full original
selection. Strict legacy matching rejects half/mixed/unknown selections, without
repair. Assessment/action/prospective completion/eligibility guards retained;
shared room/typed flows and opening/timeout separation preserved. 888 isolated
Python checks (providers mocked), 414 React/build and 62 targeted checks pass;
independent Standards/Spec zero findings. Fresh two-request plan is prepared,
ordinary bound US$0.0508296/proposed new US$0.06 cap, not approved or executed.
Gate remains 4/7, no model/routing promotion or publication; capacity separate.


2026-10-24 — [Authorized coherent-selection retest completed](../reviews/08-coherent-selection-results.md).
Two GLM low/6144 synthetic Critical reviews: valid answer/prospective plan in
5.980s, then submission_unexpected_probe rejection in 23.245s. Both OpenInference
HTTP200. A non-probe action contained probe data; exact action/content unknown.
No assessment/selection failure observed, but combined contract remains unreliable.
Two receipts US$0.000528844, no missing holds, final in-flight zero; source/plan/
ledger/hash checks pass. Gate stays4/7; no next writer/coaching/full defense,
extra campaign, model promotion or publication. Next proposed correction:
mutually exclusive answer/clarification/probe wire shapes with all guards retained.


2026-10-24 — [Exclusive action contract verified locally](../reviews/08-action-contract-correction.md).
Combined result advertises strict answer/clarification/probe variants; pending
probe replies exclude another probe. Required answer assessment/candidate and
all original domain guards retained. Legacy adapter omits only unused nulls,
rejecting non-null conflicts. Guidance aligned; no run-policy change.
892 isolated Python/provider-mocked,414 React/build and66 targeted checks pass;
independent Standards/Spec zero findings. New two-request plan boundUS$0.0511776/
proposed fresh US$0.06 cap is unapproved/unexecuted. Gate stays4/7, no new paid
calls, model/routing promotion or publication; full/provider/capacity gates open.


2026-10-24 — [Authorized exclusive-action retest completed](../reviews/08-action-contract-results.md).
Both Critical reviews passed application validation: answer+prospective plan
19.263s, same-question probe18.665s (not another accepted answer). Both GLM low/
6144/OpenInference HTTP200. Reported US$0.000532864, two receipts/no missing holds,
final in-flight zero; source/plan/ledger hashes match. Canonical provider enforcement,
probe appropriateness and stable success-rate unproved. Review stage alone exceeds
15s; all-role/full-defense/coaching/capacity gates remain open, overall4/7.
No further campaign, runtime promotion or publication.

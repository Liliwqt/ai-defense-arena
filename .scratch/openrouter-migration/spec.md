# OpenRouter migration for research defenses

Status: ready-for-agent

Date: 2026-10-19. The user confirmed the consolidated migration plan in Q11
and explicitly confirmed this specification's test boundaries. This is a local
Markdown tracker specification. Implementation tickets, implementation, remote
publication and deployment are separate steps.

## Problem Statement

The host wants to run affordable, subject-aware research defense practice through
OpenRouter, choosing different models for the four reviewer roles instead of
using one directly configured OpenAI model for every task. Paper mapping,
questions, clarification, answer interpretation and coaching currently depend on
the same direct-provider configuration. Changing only the API key would not
establish compatible structured responses, task routing or live transcription.

Research question generation currently chooses the next reviewer and writes the
question together. Routing to a role-specific model therefore requires choosing
an eligible reviewer first without weakening adaptive coverage, grounded citations
or the once-only opening/history/credit commit. More models and an extra planning
request also make provider spending harder to predict, especially with full-paper
context, reasoning, retries and a coaching card for every answer.

Defenders still need reliable practice when a model, allowance or speech service
is unavailable. They must retain accepted answers, understand recovery, and avoid
hidden charges or misleading claims that mocked checks prove model intelligence,
language quality or installed-device readiness.

## Solution

Replace all direct OpenAI service calls with a shared, server-controlled
OpenRouter integration in two runnable local checkpoints. Preserve research and
mixed research/code defenses across fields. Temporarily disable new code-only
defenses in both interfaces, retaining existing code-only results rather than
converting them to research sessions.

First migrate text: DeepSeek high for mapping and Methodology, Haiku medium for
Ethics, Qwen with a verified bounded reasoning budget for Impact, GLM high for
Critical, and Haiku high for coaching. A small GLM low-reasoning planner selects
the eligible next move before the assigned reviewer generates its question and
reaction. Same-question interactions retain the current reviewer's model with
lower supported reasoning. Keep task settings fixed for a defense run, validate
combined results before publishing them, and retain selected-model retry/recovery.

Bound provider spending separately from the user's credits. Give preparation its
own allowance, give each defense a ceiling, and protect the final-coaching
reserve from other requests. Track reservations and known usage conservatively,
including rejected results, reasoning and retries. Retain current credit prices,
vouchers, payment verification and eligible credit returns. Streamlit shares the
research AI policy while keeping its typed interface.

Keep voice off during that migration. The second checkpoint begins with an
OpenRouter-only speech prototype. Enable the replacement only after reviewed
evidence establishes incremental captions, finalizing manual Send, authoritative
deadlines, ten shared voice minutes, bounded spending, privacy and relevant
browser/native behavior. If the prototype fails, keep typing available and voice
disabled; do not silently restore direct OpenAI calls or replace live words with
transcription only after Send.

## User Stories

### Research scope and preparation

1. As a host, I want Research paper to remain the default, so that setup reflects the app's principal purpose.
2. As a host, I want Research + code to remain available, so that software-supported studies retain research-focused practice.
3. As a host, I want code-only practice clearly marked temporarily unavailable, so that I do not begin an unsupported defense.
4. As a returning host, I want a restored code-only selection explained without silently changing its mode, so that I can deliberately choose a supported workflow.
5. As a defender, I want existing code-only results preserved where they are already available, so that disabling new defenses does not rewrite past practice.
6. As a researcher, I want mapping and reviewers to use the confirmed subject, approaches, stage and setting, so that practice fits different fields.
7. As a researcher, I want host descriptions kept distinct from paper evidence, so that changing the profile does not manufacture research facts.
8. As a host, I want mapping and remapping to remain explicit actions, so that opening or refreshing a page cannot spend provider allowance unexpectedly.
9. As a host, I want factual mapping progress and grounded topic previews retained, so that I can understand preparation without seeing hidden reasoning.
10. As a host, I want profile and question-budget confirmation retained before Start, so that a provider migration cannot bypass preparation.

### Reviewer models and conversation

11. As a host, I want paper mapping assigned to the selected DeepSeek model with high reasoning, so that it receives the agreed preparation policy.
12. As a defender, I want Methodology, Ethics, Impact and Critical to use their assigned models, so that each perspective can be evaluated independently.
13. As a defender, I want the next question to use the model for its actual chosen reviewer, so that routing does not depend on guessing who a response will choose.
14. As a defender, I want the planner constrained to server-eligible reviewers, topics and follow-ups, so that a separate planning call cannot skip the defense rules.
15. As a host, I want completion accepted only when the established coverage and reviewer rules permit it, so that a planner cannot end practice prematurely.
16. As a defender, I want a partial or invalid planner/reviewer result kept out of the room, so that it cannot change coverage or begin a vote.
17. As a paying host, I want an opening charged only after the complete grounded move and opening history commit succeed, so that a rejected proposal does not cost defense credits.
18. As a returning host, I want recent-opening variation and explicit repeat acceptance preserved, so that routing changes do not erase practice history.
19. As a defender, I want clarification, interpretation and answer probes to retain the speaking reviewer's assigned model, so that same-question exchanges remain coherent.
20. As a defender, I want shorter questions, specific optional reactions and natural modern Bisaya preferences retained, so that the migration preserves the agreed conversational style.
21. As a defender, I want exact citations and appropriate code-versus-paper evidence rules retained, so that cross-model output remains grounded.
22. As a defender, I want no invented answer, strength or result after a missed turn, so that feedback reflects the actual discussion.
23. As a host, I want existing bounded retries to keep the selected model, so that failures do not silently change the model or its expense.
24. As an operator, I want unsupported schema, context or reasoning settings rejected clearly, so that the app does not pretend incompatible settings worked.

### Configuration and provider spending

25. As a host, I want a defense run's model, reasoning and output settings fixed through retries, so that operator edits do not change an active run halfway through.
26. As an operator, I want configuration changes to apply to future runs, so that I can tune policy without mutating accepted practice.
27. As an operator, I want credentials and model selection controlled on the server, so that clients cannot spend the provider key on arbitrary models.
28. As an operator, I want bounded visible-output and reasoning policies per task, so that a model's default cannot create unexpectedly large generations.
29. As an operator, I want a separate preparation allowance, so that repeated mapping cannot consume a started defense's coaching reserve.
30. As an operator, I want the defense allowance sized against its required coaching and confirmed question budget, so that an obviously unfundable run is rejected before starting.
31. As a defender, I want final-coaching funding protected from extra interactions, so that question generation does not deliberately spend the reserved report allowance.
32. As an operator, I want every planner, reviewer, remapping, retry and coaching request admitted against the correct allowance, so that splitting one operation into two calls cannot bypass limits.
33. As an operator, I want concurrent requests to reserve against one authoritative remaining allowance, so that races cannot each spend the same funds.
34. As an operator, I want billable rejected, cancelled or stale work accounted conservatively, so that unpublished results are not treated as free requests.
35. As an operator, I want missing or late usage treated as uncertain rather than zero, so that transport failure cannot reopen an unsafe allowance.
36. As an operator, I want duplicate usage settlement applied once, so that retries of an accounting write cannot double the recorded expense.
37. As a defender, I want an exhausted allowance explained while my accepted answers and ready coaching remain visible, so that I understand recovery without losing work.
38. As a host, I want Retry at an exhausted allowance to avoid another unaffordable request, so that recovery cannot become a paid failure loop.
39. As a defender, I want existing timers to keep their authoritative rules during provider-budget failure, so that navigating or waiting does not create extra answer time.
40. As a paying host, I want the current defense credit price and voucher rules unchanged, so that provider tuning adds no hidden surcharge.
41. As an operator, I want usage and cost evidence labeled accurately, so that a local ceiling or estimate is not presented as a provider billing guarantee.
42. As a defender, I want errors to explain the usable next action without exposing keys, provider payloads or another user's data, so that recovery is clear and private.

### Coaching and fallback interface

43. As a defender, I want the overview and every required answer card generated with the agreed Haiku coaching policy, so that the model change preserves complete answer-delivery coaching.
44. As a defender, I want original answers, actual speakers, probe exchanges and grounded stronger wording retained, so that advice is attributable to what the team said.
45. As a defender, I want supported filler examples distinguished from normal language particles and transcription mistakes, so that delivery feedback remains fair.
46. As a defender, I want unavailable timing or confidence measures stated honestly, so that a different provider cannot create invented delivery scores.
47. As a defender, I want the closing shown once and completed cards retained while later sections run, so that progressive Results remain useful.
48. As a host, I want retry to regenerate only eligible failed sections within the remaining allowance, so that completed coaching is not paid for again unnecessarily.
49. As a paying host, I want incomplete required coaching to remain financially incomplete, so that visible partial Results are not mistaken for successful service completion.
50. As a host, I want existing eligible end-unavailable credit-return recovery retained, so that a recorded unresolved failure does not remove the agreed remedy.
51. As a Streamlit user, I want the same research/mixed model and spending policy with typed input, so that the fallback does not silently use direct OpenAI or different research rules.
52. As a Streamlit user, I want code-only starts disabled and existing typed research recovery preserved, so that both interfaces describe supported access consistently.

### Speech replacement

53. As a defender, I want voice clearly unavailable during text migration while typing works, so that I do not start capture through an unfinished replacement.
54. As an operator, I want an OpenRouter-only caption prototype before enabling speech, so that file-transcription support is not mistaken for proven live parity.
55. As a defender, I want the chosen speech service and its retention disclosed accurately, so that I know where audio goes before starting capture.
56. As a chosen defender, I want microphone capture to require an explicit action for my answer or probe reply, so that selection or navigation never starts recording.
57. As a chosen defender, I want recognized words displayed read-only as I speak, so that I can inspect the captured explanation before manually sending it.
58. As a defender, I want provisional, finalized and accepted text distinguished, so that visible captions are not mistaken for an accepted answer.
59. As a chosen defender, I want Send to stop capture, finalize remaining speech and submit once, so that the end of my explanation is included without automatic submission after silence.
60. As a defender, I want finalization to obey the original answer or probe deadline, so that slow recognition cannot extend my turn.
61. As a defender, I want duplicate or out-of-order speech results assembled safely and stale results ignored, so that delayed chunks cannot corrupt a later answer.
62. As a defender, I want rerecording and switching to typing retained, so that inaccurate recognition does not trap me in an uneditable draft.
63. As a teammate, I want only the currently authorized speaker able to stream, so that another player cannot consume allowance or submit speech for me.
64. As a team, I want the existing ten shared voice minutes counted across forwarded attempts and reconnects, so that the visible time allowance remains authoritative.
65. As an operator, I want speech spending bounded within the defense allowance without consuming the coaching reserve, so that voice does not create unaccounted expense.
66. As a defender, I want the mic stopped and typing offered when speech becomes unavailable or its allowance ends, so that the defense can continue without a hidden provider fallback.
67. As an English-speaking defender, I want recognition quality checked before voice is advertised as ready, so that the pilot has evidence for its first language.
68. As a Tagalog or Bisaya speaker, I want support and code-switching claimed only when tested, so that the app does not promise recognition it cannot deliver.
69. As a defender, I want temporary audio disposed of after bounded processing, so that the migration does not create an app audio archive.
70. As a defender, I want submitted transcript and supported measurements kept separate from discarded speech, so that unsent attempts are not treated as accepted performance.
71. As a native-app user, I want trusted-origin microphone permission and lifecycle protections retained, so that changing the backend does not broaden capture access.
72. As a native-app user, I want capture stopped on backgrounding, interruption or obsolete document state, so that returning requires a fresh appropriate mic action.
73. As a defender, I want a voice feature that fails its prototype gate to remain disabled with typing available, so that a failed experiment does not degrade normal practice.

### Reliability and evidence

74. As a host, I want duplicate commands and stale work unable to change an ended or restarted run, so that multi-stage generation preserves coordinator reliability.
75. As a paying host, I want verified interrupted-run credit returns and existing abandonment rules retained, so that migration does not change financial recovery.
76. As a defender, I want two clients to see the same accepted question, timer, reactions and progressive Results, so that model diversity does not split the shared room.
77. As a phone or keyboard user, I want mapping, recovery, coaching and voice controls to remain readable and reachable, so that the migration works in the existing interface.
78. As an operator, I want real database concurrency and recovery checked separately from mocks, so that allowance correctness is demonstrated on the deployment database engine.
79. As an operator, I want same-fixture model quality, latency and actual cost records, so that later model or premium-tier choices rest on evidence.
80. As a maintainer, I want offline, live-provider, hosted and installed-device results reported separately, so that readiness claims match the checks actually run.

## Implementation Decisions

1. **Scope and delivery.** Deliver two runnable local checkpoints. The first
   replaces all reachable direct-provider text calls and enforces code-only
   disablement with voice off. The second begins with a reviewed OpenRouter-only
   speech prototype, then integrates the proven replacement. The user has
   authorized this specification, not implementation or publication. Keep work
   on the feature branch and preserve the frozen main branch.

2. **Shared integration boundary.** Put credentials, task/reviewer assignments,
   supported request options, output limits, safe errors and provider usage
   handling behind one server-owned integration used by room workflows and the
   typed fallback. An OpenAI-compatible SDK may remain an implementation tool;
   no reachable operation may depend on a direct OpenAI service or silently fall
   back to one. Retain existing room command, recipient-view and publication
   boundaries rather than distributing model routing into client components.

3. **Exact initial assignments.** Use the following confirmed bundle. These are
   candidate policies to validate, not established claims of superior quality.

   | Task | Exact model ID | Reasoning policy |
   | --- | --- | --- |
   | Mapping and remapping | `deepseek/deepseek-v4.1-flash-1017` | high |
   | Methodology question and reaction | `deepseek/deepseek-v4.1-flash-1017` | high |
   | Ethics question and reaction | `anthropic/claude-haiku-5.5` | medium |
   | Impact question and reaction | `qwen/qwen3.8-flash` | verified bounded reasoning-token budget |
   | Critical question and reaction | `z-ai/glm-5.3-flash` | high, explicitly set |
   | Next-move planner | `z-ai/glm-5.3-flash` | low |
   | Coaching overview and answer sections | `anthropic/claude-haiku-5.5` | high |
   | Clarification, probe and submission interpretation | current reviewer's assigned model | low where supported for DeepSeek/Haiku/GLM; verified lower bounded budget for Qwen |

4. **Capability compatibility.** Validate the combination of model, eligible
   provider route, schema, context, reasoning and total output limits. Qwen's
   budget must be verified through the chosen transport; do not invent a named
   effort selector. Explicitly set GLM's agreed reasoning instead of inheriting a
   larger default. Preserve strict parsing and source validation even if adapting
   the transport away from the current Responses helpers is necessary. Unsupported
   settings, excessive context, refusal, malformed output or truncated output
   must fail safely, without silent source truncation or model substitution.

5. **Fixed run configuration.** Capture the selected models, reasoning and output
   limits for a defense run before its provider work; retries and progressive
   coaching use that snapshot. Capture preparation settings when its separate
   allowance is established. Operator changes affect future work scopes rather
   than mutating an active snapshot. Clients cannot supply arbitrary model IDs,
   provider URLs or credential values. Preserve existing attempt/admission limits
   in addition to the new monetary controls.

6. **Two-stage question contract.** The planner receives the accepted source,
   confirmed research profile, relevant history and eligible next moves. It may
   propose prior-answer coverage assessment, an eligible reviewer/topic/follow-up,
   or valid completion. Validate that proposal against server-owned rules. For a
   question move, call only the selected reviewer's assigned model to produce
   the grounded question and optional reaction from consistent context. Validate
   the combined move against the same snapshot before any game-state commit.
   A valid completion skips reviewer-question generation. The planner is not a
   new answer grader and cannot create an extra turn through clarification.

7. **Atomic publication and stale work.** Keep intermediate plans and generated
   questions detached from the live defense. Neither stage alone may update
   coverage, append a turn, start a clock, write opening history or charge defense
   credits. Preserve coordinator ordering, duplicate-work suppression, generation
   ownership and checks after asynchronous boundaries. Rejected, cancelled or
   stale work cannot publish, settle, revive a returned run or schedule a new
   reviewer call after invalidation. Provider work already dispatched can still
   be billable and must be accounted independently of game-state acceptance.

8. **Existing conversation and opening rules.** Preserve first-reviewer ordering,
   eligibility, topic coverage, question budgets, follow-up rules, citations,
   reaction timing, modern language preferences, same-question clarification and
   probe behavior. Preserve five private recent openings per host and accepted
   paper content for 30 days, bounded duplicate regeneration and explicit repeat
   acceptance. The authoritative accepted opening/history/credit transition
   remains once-only; an invalid intermediate result cannot trigger it.

9. **Provider allowance persistence.** Extend the existing transactional storage
   boundary with preparation/run allowances and uniquely identified request
   reservations/settlements. Retain only the minimal scope, model/configuration,
   reservation, rate-bound, usage/cost and status metadata needed for admission,
   reconciliation and recovery. Keep it distinct from live/test credit balances,
   run-credit reservations, payment receipts and opening-question history. Do not
   store papers, answers, audio or secrets in provider-accounting records.

10. **Conservative admission and settlement.** Before every dispatched request,
    reserve a conservative bound covering input, billed output/reasoning and
    applicable route charges within the correct allowance. Concurrent work must
    observe the same authoritative remaining amount. Account for planner calls,
    failed validation, duplicates that reached the provider, retries, remapping,
    cancelled/stale work and later speech requests. Settle known usage once;
    avoid double counting reasoning already included in billed output. Missing,
    late or conflicting usage must not be treated as zero or release funds
    optimistically. Database failure before reservation prevents dispatch; an
    uncertain dispatched request retains conservative accounting until safely
    reconciled. A restart must not blindly free unresolved provider reservations.

11. **Preparation and protected coaching.** Preparation/remapping has a separate
    bounded allowance that page visits and retries cannot reset. Each defense
    ceiling protects required coaching from question/interaction spending. Size
    the reserve against the confirmed question budget, bounded required sections,
    retries and outstanding uncertainty. Check viability before Start rather
    than deliberately admitting a configuration unable to fund the required
    report. Speech at the second checkpoint gets an explicit share of the run
    allowance and cannot consume the protected coaching reserve.

12. **Measured numeric limits.** Select finite operator-configured dollar/token
    limits from synthetic measurements before rollout, covering large accepted
    papers, long answers and required long reports. Provide enough total output
    capacity for both reasoning and visible structured content. Published token
    rates alone do not establish the complete cost of a run. Do not label a local
    spending ceiling as a provider-side billing guarantee. A failed compatibility
    or affordability gate requires a reported decision, not a silent change to
    the agreed models, research scope or credit price.

13. **Budget and provider failure recovery.** Preserve accepted answers, valid
    maps and finished coaching when further provider work is blocked. Explain
    configuration failure, provider unavailability, exhausted allowance and
    ordinary retryable generation failure through safe existing recovery views.
    Do not offer a retry that repeatedly dispatches unaffordable work; bounded
    retries retain the selected model. Do not freeze authoritative answer timers
    merely because provider work is paused. Retain current eligible credit-return
    rules without creating a new automatic payment-refund category.

14. **Progressive coaching and financial rules.** Preserve overview generation,
    bounded per-answer batches, retained originals/speakers/probes, grounded
    wording improvements, factual unanswered cards and truthful delivery evidence.
    Show the closing once; retry only eligible failed sections. Required partial
    coaching remains financially incomplete until every section and durable
    completion write succeed. Keep the current ten-credit price, voucher access,
    verified payment awards, once-only charges/returns, interruption recovery and
    abandonment rules. Provider expenditure does not debit extra user credits.

15. **Temporary code-only disablement.** Reject new code-only creation/start and
    restart paths on the server and show the unavailable state consistently in
    web and Streamlit setup. A restored code-only selection must not silently
    become research or mixed. Preserve readable existing results where retained;
    do not rewrite transcripts or remove mixed-defense code citations. Document
    rollout handling of already-active code-only rooms before release, preserving
    existing recovery rules rather than assuming in-memory rooms survive deploy.

16. **Streamlit parity.** Use the shared text transport, task/reviewer routing,
    fixed settings, allowance controls and selected-model recovery in research
    and mixed fallback defenses. Keep its current typed, single-browser interface
    and inline report behavior. Prevent a fallback path from bypassing budgets
    or using the old direct-provider key.

17. **Speech prototype gate.** Do not assume OpenRouter file transcription is a
    drop-in replacement for the existing Realtime relay. Prototype bounded chunks
    or another verified OpenRouter-only transport with ordered/deduplicated
    results, cancellation, temporary buffers and complete finalization. No speech
    model is finalized; Scribe v2 is only a research candidate. Record measured
    first-caption/intermediate/finalization latency, recognition, account support,
    cost and provider retention before review. If the experiment cannot preserve
    the agreed live experience, stop voice integration and retain typed practice;
    do not claim parity from HTTP endpoint availability or a fake-audio test.

18. **Speech contract preservation.** Preserve authenticated room/turn/probe/
    speaker scope, explicit Start mic, read-only live words, manual Send that
    stops capture and finalizes once, no silence-triggered submission, authoritative
    deadlines and accepted-answer acknowledgments. Preserve rerecord/switch to
    typing, late-result rejection, reconnect distinctions between drafts and
    accepted answers, and ten shared minutes based on forwarded audio, including
    discarded/retried attempts. Count duplicated or overlapping forwarded audio
    honestly in usage without weakening the existing audio-time cap. Bound stream
    duration, attempts, buffers and concurrency; stop capture safely on allowance
    exhaustion without automatically sending the draft.

19. **Privacy, measurements and native capture.** Keep credentials server-side,
    disclose the actual selected speech service's retention, and keep no app audio
    archive. Use only accepted transcript and reliable attributable measurements
    for coaching; never infer missing linguistic pauses, confidence, accent grades
    or filler counts from unavailable evidence. English is first; Tagalog/Bisaya
    and natural code-switching need support and quality evidence. Preserve Android/
    iOS exact-origin/main-frame microphone authorization, foreground/document
    lifecycle protections, explicit rearming and typing fallback. Identify any
    necessary native rebuild separately; source or build success is not installed
    capture evidence.

20. **Operator setup and diagnostics.** Replace reachable direct-OpenAI setup
    dependencies and misleading error instructions with OpenRouter configuration
    guidance. Keep errors redacted and diagnostics limited to necessary task/model/
    usage/latency metadata. Do not expose hidden reasoning in the mapping UI,
    publish credentials to clients, log full provider requests/responses, or claim
    the role assignments have already proved intelligence or cost superiority.

## Testing Decisions

1. **Confirmed highest boundaries.** The user confirmed authenticated FastAPI
   HTTP/WebSocket room flows with a controlled clock and AI, speech, Google and
   payments mocked; existing generation/mapping/coaching contracts; real local
   PostgreSQL allowance checks; and whole-App React/browser plus native lifecycle
   checks. Prefer these existing boundaries over adding public test-only APIs or
   testing each new internal helper independently.

2. **What makes a good test.** Assert observable requests at the provider boundary,
   recipient-visible room state, accepted/rejected actions, authoritative timing
   and durable allowance/credit outcomes. Avoid assertions about private helper
   call order, internal field layout or exact AI prose. Deterministic mock output
   proves handling and context, not conversational quality.

3. **Contract-test prior art.** Extend the existing fake-client generation tests,
   streamed research-map tests, research-move/coverage validation and coaching
   contracts. Check exact role/task model selection, fixed settings through retry,
   supported reasoning options, total limits, schema preservation, truncated or
   malformed output, missing key, unsupported model/context and redacted errors.
   No mocked request may silently point to a direct OpenAI service.

4. **Planner/reviewer integration.** Through room actions and provider requests,
   demonstrate valid adaptive selection, a valid completion without reviewer
   generation, incompatible reviewer/topic rejection and atomic failure at either
   stage. Delayed stage results after ending/restarting must not alter coverage,
   accepted questions, history, clocks or charges. Invalid planner output must
   not dispatch a reviewer request. Preserve duplicate-opening retry/acceptance.

5. **Preparation and source contracts.** Verify explicit mapping/remapping,
   grounded streamed progress, cancellation, retry, profile correction and current
   profile/budget confirmation. Check accepted source/context limits and mixed
   code citations. No silent truncation, invented cited text or hidden reasoning
   may appear in a successful result.

6. **Real storage seam.** Extend the existing opt-in disposable local PostgreSQL
   runner and existing store contracts. Check migrations preserve credit/payment/
   history data; concurrent request reservations cannot overspend; preparation is
   separate; coaching reserve is protected; settlement is idempotent; and restart/
   cancellation/unknown usage cannot release uncertain costs as free allowance.
   Providers remain mocked. Do not substitute mocked SQL or a SQLite-only run for
   PostgreSQL concurrency evidence; never use a hosted production database.

7. **Spending failure cases.** Check admission failure prevents dispatch, retry
   and two-stage work each reserve their actual requests, reasoning is counted
   according to the billing contract, partial/absent usage stays conservative,
   duplicate usage settlement is once-only, and ledger failures preserve a safe
   outcome. Exhausted limits must retain answers/cards and avoid a new provider
   call. Config changes must not mutate active model/reasoning/output snapshots.

8. **Shared room regressions.** Reuse the complete mocked twelve-question,
   two-client research/mixed defenses, including PDF citations, voting, reaction,
   clarification, probes, timeout, reconnect, retry and coaching. Check stage
   parity across clients, protected answer drafts and server-authoritative timers.
   Include research approaches beyond quantitative studies in contract fixtures.

9. **Financial/recovery prior art.** Reuse existing opening-history protocol,
   live-run, service-handoff and progressive-coaching recovery cases. Verify
   once-only accepted opening/history/credit commit, retained partial report,
   failed-only retries, one closing, no premature successful settlement and
   stale-result fencing after a return. Preserve payment verification, vouchers,
   ten-credit cost, interruption returns and abandonment behavior.

10. **Code-only and Streamlit.** Check server rejection despite forged/restored
    code-only selections, clear interface guidance and unchanged retained results.
    Check mixed defenses remain usable. Extend current typed fallback coverage
    and coaching cases to show the same model/routing/allowance policy, correct
    recovery and absence of any direct-provider bypass.

11. **Speech contract and whole-App prior art.** Reuse authenticated speech/room
    protocol tests with synthetic audio and fake provider events, whole-App voice
    tests and accepted delivery-evidence tests. Adapt the fake transport at the
    existing external boundary rather than asserting the old upstream protocol.
    Cover incremental read-only words, manual finalizing Send, deadline crossing,
    one accepted answer, forged/stale speech attempts, ordered/duplicate chunks,
    reconnect, discarded audio usage, minute/dollar caps and typing recovery.

12. **Native lifecycle checks.** Extend existing Android policy and iOS policy
    checks and native bridge browser tests where integration changes touch them.
    Check trusted-origin/main-frame mic scope, permission races, foreground
    recovery, document teardown and explicit rearming. Record toolchain/build
    availability honestly. Installed Android and iOS capture remains separate
    physical-device evidence, including interruptions and reconnect.

13. **Responsive local review.** Present desktop, portrait-phone and landscape
    previews covering mapping, disabled code-only setup, blocked/retry state,
    progressive coaching and, after the gate, live voice. Check keyboard access,
    focus, visible status, manual Send and readable read-only text. Use actual
    browser checks with synthetic room/provider fixtures; do not present preview
    transcripts as live model results.

14. **Full offline gate.** Run the repository's full Python unittest suite with
    its virtual environment, React tests and TypeScript/production build. Run the
    explicit real-local-PostgreSQL gate for new accounting transactions. Report
    AI/speech/Google/payment mocks and database evidence separately. Do not add a
    permanent live-provider dependency to the offline suite.

15. **Separate actual-provider evidence.** Use the same synthetic papers and
    answers across subject/approach fixtures to assess source faithfulness,
    question clarity, reviewer relevance, coaching usefulness, latency and actual
    total usage/cost including planner and retries. Verify account/route schema,
    context and reasoning behavior, especially Qwen. Numeric caps must be checked
    against long accepted inputs/reports before rollout. Do not replace the
    confirmed bundle merely because one mock or headline rate looks favorable.

16. **Speech enablement evidence.** Review actual incremental and finalization
    latency, English recognition and language claims, budget use, endpoint access
    and provider retention before enabling the pilot. Hosted transport and
    installed Android/iOS audio are distinct from localhost browser tests and
    native policy tests. Keep voice disabled when evidence or compatibility is
    insufficient and record the limitation; no direct-provider fallback is allowed.

## Out of Scope

- Premium defense tiers, new retail credit prices, per-model user surcharges or
  changing top-up, voucher, payment refund or credit-return policy.
- New code-only reviewer bundles or improvements while code-only practice is
  temporarily disabled; mixed research/code remains in scope.
- Automatically switching models or restoring direct OpenAI on failure.
- A broad navigation, room layout or branding redesign; preserve the current
  Guided preparation, paper viewer, Speaker desk and progressive Results.
- Adding voice to Streamlit or replacing its current typed interface.
- Recording audio archives, collecting private papers for benchmarks, displaying
  hidden reasoning, manufacturing delivery measurements or grading accents.
- Switching to file-at-Send alone as a substitute for live captions.
- Promising a particular speech model, fixed latency, final numeric token/dollar
  caps, universal language support, quality superiority or guaranteed savings
  before the explicit measurement gates.
- Persisting full in-memory rooms/results across deployments, changing the single
  worker/instance architecture or altering the existing service lease.
- Modifying the frozen main branch, pushing, merging or deploying from this spec.

## Further Notes

- Authority: [confirmed migration plan](../../docs/OPENROUTER_MIGRATION_PLAN.md)
  and [primary-source model/speech research](../../docs/OPENROUTER_MODEL_RESEARCH.md).
  The latter is dated research, not proof of account-specific compatibility or a
  permanent price guarantee. Recheck selected routes at implementation time.
- Preserve the accepted [interrupted-run credit recovery](../../docs/adr/0002-live-run-credit-compensation.md),
  [bounded opening history](../../docs/adr/0006-bounded-opening-question-history.md)
  and [partial-coaching settlement boundary](../../docs/adr/0007-progressive-coaching-before-settlement.md).
  This spec intentionally supersedes earlier code-only availability for new
  defenses; it does not supersede their retained-results or financial guarantees.
- Existing uncommitted task-reasoning and local-testing changes predate this spec.
  They are not a published OpenRouter migration and must be preserved and scoped
  explicitly when implementation starts.
- Ready-for-agent means ready for local ticket breakdown/implementation work; it
  does not declare the models, voice prototype, hosted service or native apps ready
  for users. Checkpoint 2 can correctly end at a failed prototype gate with voice
  still off and the text checkpoint usable, while reporting speech replacement as
  incomplete rather than claiming the whole migration achieved parity.
- Unknown numeric limits and speech transport/model choices are planned empirical
  gates. Document the observations and obtain a new decision before departing
  from the confirmed model policy, voice behavior or financial rules.

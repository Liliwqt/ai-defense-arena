# OpenRouter migration — approved ticket breakdown

Approved as drafted by the user on 2026-10-19. Source: [confirmed specification](spec.md).
All twelve individual local tickets are now published in the [dependency index](README.md).
No implementation has started.

## Delivery and dependency rules

- Tickets 01–06 complete the text checkpoint; voice stays off. Tickets 07–12
  cover the gated speech checkpoint. A failed speech experiment leaves text
  usable and voice off, with speech replacement explicitly incomplete.
- Each implementation slice includes its user-visible behavior, authoritative
  admission/accounting, safe failure/recovery and tests at the agreed boundaries.
  No separate infrastructure-only or accounting-at-the-end ticket is proposed.
- Begin ticket 01 by expanding a shared provider boundary alongside unmigrated
  callers, then exercise it through real mapping behavior. Migrate remaining
  callers in the following slices and remove obsolete direct-provider paths at
  ticket 06. Existing unmigrated callers are transitional local code, never an
  automatic fallback from a migrated request. No intermediate slice is a claim
  that the entire app has migrated or that all provider spending is yet covered.
- Each slice leaves the application runnable and its completed behavior
  verifiable. Do not publish intermediate migration states as a finished release.
- All model/output/reasoning choices follow the spec. Keep research/mixed scope,
  exact citations, run-credit rules, safe source handling and single-instance
  coordinator behavior. Preserve unrelated working changes.
- Dependency edges below identify actual prerequisites. The suggested order
  does not require concurrent agents; 03/04 and 10/11 are independent frontiers.
- Any live provider or installed-device evidence must be distinguished from
  offline mocks. Failed or unavailable gates remain pending, never silently
  waived by a passing mocked suite.

## Approved slices

### 01 — Bounded OpenRouter paper mapping

**Blocked by:** None — can start immediately.

**What it delivers:** A host explicitly maps/remaps a research or mixed paper
through DeepSeek high, sees grounded progress and safe recovery, and cannot start
the temporarily unavailable code-only or voice workflows.

- Expand the shared server integration before migrating mapping; use the exact
  assigned model, supported schema/reasoning/context limits and redacted errors.
- Give preparation fixed settings and a separate finite allowance with atomic
  request reservation, known-usage settlement and conservative unknown usage.
  Refresh, remapping and retry cannot reset that allowance or dispatch unpaid work.
- Keep profile corrections, current budget/profile confirmation, source checks,
  streamed progress, stale-work cancellation and retained valid preparation.
- Enforce code-only creation/start/restart disablement on server and both setup
  interfaces, explaining restored selections and preserving existing results.
  Research + code remains available. Voice stays off server-side and in clients.
- Verify the complete mapping path, accounting failures/races and real local
  PostgreSQL reservation/settlement behavior, plus mocked room/contract and setup
  browser checks. Choose bounded initial mapping settings from synthetic evidence.

### 02 — Funded defense runs with assigned reviewer questions

**Blocked by:** 01 — Bounded OpenRouter paper mapping.

**What it delivers:** A host starts a funded research/mixed run whose GLM low
planner selects the next eligible move and whose assigned reviewer asks the
validated question, with consistent state and once-only charging.

- Snapshot task/reviewer models, reasoning and output limits for the run. Establish
  its provider ceiling and protected coaching reserve sized to the confirmed
  question budget; reject an unfundable start before game-credit commitment.
- Apply the confirmed four-reviewer model bundle; verify Qwen's actual supported
  bounded reasoning contract rather than inventing an effort selector.
- Validate planner selection/coverage/completion before reviewer dispatch. Validate
  both stages together before question, coverage, history, vote/clock or credit
  commit; valid completion needs no reviewer-generation call.
- Preserve reviewer order, follow-ups, citation policy, recent openings, bounded
  duplicate regeneration and explicit repeat acceptance. Include every dispatched
  stage/retry in provider accounting, including rejected or stale results.
- Retain answers and safe selected-model recovery; enforce cancellation between
  stages, duplicate-work suppression, fixed settings and once-only game charging.
  Verify controlled-clock/two-client flows and real database funding races.

### 03 — Same-reviewer clarification, probes and answer recovery

**Blocked by:** 02 — Funded defense runs with assigned reviewer questions.

**What it delivers:** Defenders answer, ask for clarification or reply to an
answer probe using the current reviewer's model and lower supported reasoning,
with existing time limits and clear recovery when further work is blocked.

- Migrate submission interpretation, clarification and probe generation to the
  selected reviewer's fixed assignment and verified lower reasoning policy.
- Reserve and reconcile each interaction/retry against the run's non-coaching
  allowance; exhaustion retains accepted work and does not become a paid retry loop.
- Preserve direct-answer recovery, chosen-defender permissions, same-question
  numbering, answer/probe drafts, timeout rules and source/language boundaries.
- Do not freeze authoritative answer timers on provider or budget failure; stale
  interpretation/clarification/probe work cannot overwrite a later turn/run.
- Verify actual room actions and recipient views with mocked providers and a
  controlled clock, including duplicate commands, errors, reconnect and phone controls.

### 04 — OpenRouter progressive coaching from protected funds

**Blocked by:** 02 — Funded defense runs with assigned reviewer questions.

**What it delivers:** A finished discussion produces its Haiku high overview and
every-answer coaching cards progressively, using protected funds and preserving
partial Results and eligible failed-defense recovery.

- Use the fixed Haiku high policy for overview and bounded answer sections, with
  request admission/settlement from the run's protected coaching allowance.
- Preserve actual originals/speakers/probes, source-grounded stronger wording,
  factual unanswered cards, captured filler examples and truthful missing measures.
- Keep completed sections/progress visible, the closing once-only and retries
  failed-only/bounded/affordable. No card regeneration after completion-write failure.
- Do not settle the defense successfully until every required section and durable
  write succeed. Retain existing eligible end-unavailable credit returns and
  stale-result fencing; provider expense never adds user credit charges.
- Verify progressive room/report behavior, real database reserve/settlement cases
  and Results/export/browser recovery, with AI/payment providers mocked.

### 05 — Typed Streamlit research policy parity

**Blocked by:** 03 — Same-reviewer clarification, probes and answer recovery;
04 — OpenRouter progressive coaching from protected funds.

**What it delivers:** A Streamlit user can prepare and finish a typed research or
mixed defense using the same OpenRouter model, reasoning and allowance policy.

- Reuse the migrated preparation, planner/reviewer, interaction and coaching
  behavior with fixed scope settings and authoritative spending reservations.
- Preserve the current single-browser typed interface, explicit preparation,
  grounded citations, inline report, failed-only recovery and disabled code-only.
- Prevent direct-provider key dependencies or spending-limit bypass through the
  fallback. Preserve accepted answers and sections through its retry lifecycle.
- Demonstrate complete short/long typed research/mixed runs and safe failures
  through existing fallback/session/report seams, with provider mocks.

### 06 — Complete text checkpoint and measured local handoff

**Blocked by:** 05 — Typed Streamlit research policy parity.

**What it delivers:** The complete text experience runs without reachable direct
OpenAI service dependencies, with verified limits, useful setup guidance and a
local review that clearly identifies actual-provider evidence still required.

- Contract obsolete text provider paths/setup requirements only after all callers
  have migrated. An OpenAI-compatible SDK may remain; direct-service fallback may
  not. Keep voice off, code-only disabled and typing usable.
- Run full offline suites/build, real local PostgreSQL accounting/recovery checks
  and complete two-client twelve-question research/mixed defenses covering the
  protected history/credit/coaching rules and cross-field source contexts.
- Present desktop/portrait/landscape keyboard previews for setup, mapping,
  blocked/retry states and progressive Results. Preserve main and unrelated work.
- Separately check the chosen account/routes against schema/context/reasoning
  contracts, especially Qwen; compare the same synthetic papers/answers for
  usefulness, latency and actual total usage including planner and retries.
- Finalize measured numeric task/preparation/run/coaching limits against large
  accepted inputs and long required reports before claiming rollout readiness.
  Unavailable evidence remains pending; a failed model gate must be reported.
- Complete checkpoint 1 locally, without a push/deployment or voice enablement.

### 07 — OpenRouter-only live-caption feasibility prototype

**Blocked by:** 06 — Complete text checkpoint and measured local handoff.

**What it delivers:** A reviewable speech experiment shows whether an OpenRouter
route can provide the agreed incremental captions and finalizing Send behavior
without exposing a key or enabling an unproven pilot.

- Compare a verified chunk/transport approach against the current authenticated
  mic/read-only-draft/manual-Send contract; no final speech model is assumed.
- Demonstrate bounded buffers, temporary audio disposal, ordered/deduplicated
  results, cancellation, last-segment finalization and failure/typing outcomes.
- Record actual first/intermediate/finalization latency, English recognition,
  account/endpoint support, usage/cost and retention. Tagalog/Bisaya claims require
  separate evidence; synthetic events alone cannot pass actual speech quality.
- Review provider limits and a speech share of the defense ceiling that protects
  coaching and the existing shared ten-minute cap.
- Present the local prototype and a clear gate outcome. A failed or unreviewed
  outcome keeps voice off and blocks 08 onward; do not substitute file-at-Send,
  restore direct OpenAI or mark speech replacement complete.

### 08 — Authorized OpenRouter voice answers in Speaker desk

**Blocked by:** 07 — OpenRouter-only live-caption feasibility prototype, with
its compatibility and review gate passed.

**What it delivers:** The chosen defender can explicitly start a mic, see
read-only recognized words and manually finalize/send a normal answer through
the verified OpenRouter speech transport.

- Integrate the proven route behind existing authenticated room/turn/speaker
  authorization with credentials kept on the server and actual retention disclosed.
- Preserve explicit capture, incremental/finalized/accepted distinctions,
  Finishing transcript, one submission and authoritative answer deadlines.
- Reserve and reconcile actual speech requests within the run's speech share,
  protect coaching funds, and preserve ten shared minutes across forwarded,
  discarded and retried audio. Missing usage remains conservative.
- Retain rerecord/switch-to-typing, no automatic silence/limit submission,
  late-result rejection and bounded capture/buffers/attempts.
- Verify fake-audio authenticated flows, real database speech-admission races and
  whole-App desktop/phone/manual-Send behavior; actual recognition is separate.
  Pilot enablement remains gated until integrated review.

### 09 — Voice probe replies, lifecycle and truthful coaching evidence

**Blocked by:** 08 — Authorized OpenRouter voice answers in Speaker desk.

**What it delivers:** Same-question voice replies and interrupted capture recover
safely across screens/reconnect, and accepted speech contributes only reliable,
attributable evidence to coaching.

- Extend the verified route to answer-probe replies without a new question number
  or altered reply deadline; original and reply speakers/provenance stay distinct.
- Stop capture on obsolete selection/turn/probe/run, navigation, disconnect and
  lifecycle events; delayed or duplicate chunks cannot populate later work.
- Preserve valid finalized-unsent draft recovery without replaying Send; reject
  forged text/provenance and never treat an unsent transcript as an answer.
- Preserve shared time/dollar usage through reconnect, cap/error typing recovery
  and temporary audio disposal. Adapt delivery facts honestly to provider support:
  no invented rates, pauses, confidence, filler counts or accent judgments.
- Verify two-client deadline/reconnect/retry/end/restart cases, Results/export
  attribution and responsive keyboard behavior with synthetic audio/providers.

### 10 — Android speech integration and readiness evidence

**Blocked by:** 09 — Voice probe replies, lifecycle and truthful coaching evidence.

**What it delivers:** The Android app uses the proven speech path while retaining
trusted-origin microphone permission, safe foreground recovery and typed fallback.

- Adapt only what the verified transport requires; preserve exact-origin/main-page
  mic-only authorization, fresh explicit arming and stale permission protection.
- Verify background/interruption/document teardown and retry/reconnect do not
  resume capture or submit automatically; server scope/time/spend rules still apply.
- Run available policy/bridge tests and build the changed app where required.
  Record build metadata and distinguish tests/build from installed recording.
- Collect or explicitly leave pending real installed Android capture, denial,
  interruption and return-to-typing/provider behavior evidence. No Android voice
  readiness claim without its relevant gate; web typing remains usable.

### 11 — iOS speech integration and readiness evidence

**Blocked by:** 09 — Voice probe replies, lifecycle and truthful coaching evidence.

**What it delivers:** The iOS app uses the proven speech path while retaining
trusted-main-frame microphone permission, interruption safety and typed fallback.

- Adapt only what the verified transport requires; preserve microphone purpose
  disclosure, trusted-origin/main-frame grant, single-use arm and permission races.
- Preserve teardown, inactive/background interruption handling and fresh explicit
  capture after recovery, without changing answer/probe/deadline/spending rules.
- Run available native/bridge checks; execute iOS policy tests/build on a suitable
  toolchain or record them pending. Source inspection is not a passing build.
- Collect or explicitly leave pending installed iOS capture, TCC/denial,
  interruption and reconnect/provider behavior evidence. No iOS voice readiness
  claim without its relevant gate; web typing remains usable.

### 12 — Complete migration review and local handoff

**Blocked by:** 10 — Android speech integration and readiness evidence;
11 — iOS speech integration and readiness evidence.

**What it delivers:** The integrated research/mixed experience has a complete
local review and an accurate readiness record, with no direct-provider bypass or
unsupported speech/native claim.

- Run the full offline suites/build and real local PostgreSQL allowance/recovery
  gate; complete two-client research/mixed runs with answers, probes, reconnect,
  caps, retries, stale results, coaching and unchanged financial/history rules.
- Confirm no reachable direct OpenAI services, code-only starts, key leaks,
  automatic model fallback or accounting bypass in web/native/typed Streamlit.
- Present responsive local previews/screenshots, mic/typing/recovery controls,
  progressive Results and truthful transcript/measurement exports for review.
- Consolidate actual model/speech quality, numeric-limit/cost/retention, hosted
  transport and installed Android/iOS evidence separately from mocked/build checks.
  Unavailable evidence remains open; do not claim enabled/production-ready voice.
- Complete checkpoint 2 only to the evidenced extent. Do not publish/deploy or
  change main; provide the explicit remaining gates and user review handoff.

## Coverage check

The table assigns every numbered story to at least one slice; cross-cutting
criteria also appear in the relevant slices rather than only in final review.

| Spec stories | Primary slices |
| --- | --- |
| 1–10 | 01; 05–06 verify parity and integration |
| 11 | 01 |
| 12–18 | 02 |
| 19 | 03 |
| 20–24 | 02–04; 06 actual-provider contract/quality evidence |
| 25–28 | 01–04; 05 parity; 06 integration |
| 29 | 01 |
| 30–31 | 02 and 04 |
| 32–36 | 01–04, 08–09; 06/12 integrated accounting |
| 37–42 | 01–06 and 08–09 |
| 43–50 | 04; 05 parity; 06/12 integration |
| 51–52 | 01 and 05 |
| 53 | 01–06 |
| 54–55 | 07–08 |
| 56–60 | 08–09 |
| 61–62 | 07–09 |
| 63–65 | 08–09 |
| 66 | 08–11 |
| 67–68 | 07; 12 separate actual-quality evidence |
| 69–70 | 07–09 |
| 71–72 | 09–11 |
| 73 | 07–12, with the failed gate blocking integration/enablement |
| 74–76 | 02–04; 06 and 12 integration |
| 77 | 01–09 and 12 |
| 78 | 01–04, 06, 08 and 12 |
| 79–80 | 06–07 and 10–12 |

## Approval record

The user approved the granularity, slices and blocking edges unchanged on
2026-10-19. Published one local ready-for-agent file per ticket and a dependency
index. Approval does not start implementation or authorize a push/deployment.

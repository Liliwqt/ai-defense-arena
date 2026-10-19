# OpenRouter migration — implementation tickets

Status: ready-for-agent

**Ticket 03 correction verified:** source **c4d838d** closes the delayed-retry
clock issue. All four independent probes and the full offline gates pass, with
Standards 0 / Spec 0. See [the final handoff](reviews/03-retry-fix.md).
Ticket 03 is ready for human review locally; ticket 04 remains unblocked.

The user approved this twelve-ticket breakdown as drafted on **2026-10-19**.
All twelve separate local tickets are published. Tickets 01–03 are ready for
human review ([01](reviews/01.md), [02](reviews/02-sse-fix.md),
[03](reviews/03-retry-fix.md)). Ticket 04 can proceed under its separate dependency
on 02; ticket 05 requires both 03 and 04. Tickets 04–12 have not started.
The tickets contain **58 acceptance criteria**, with coverage of all
**80 specification stories** recorded in the approved breakdown.

Parent: [OpenRouter migration specification](spec.md), preserved unchanged.
Design and coverage: [approved breakdown](ticket-breakdown-draft.md).

## Tickets and dependencies

| Ticket | Blocked by | Status | Criteria |
| --- | --- | --- | --- |
| [01 — Bounded OpenRouter paper mapping](issues/01-bounded-paper-mapping.md) | None | ready-for-human | 5 |
| [02 — Funded defense runs with assigned reviewer questions](issues/02-funded-reviewer-questions.md) | [01](issues/01-bounded-paper-mapping.md) | ready-for-human | 5 |
| [03 — Same-reviewer clarification, probes and answer recovery](issues/03-reviewer-interactions-recovery.md) | [02](issues/02-funded-reviewer-questions.md) | ready-for-human | 5 |
| [04 — OpenRouter progressive coaching from protected funds](issues/04-protected-progressive-coaching.md) | [02](issues/02-funded-reviewer-questions.md) | ready-for-agent | 5 |
| [05 — Typed Streamlit research policy parity](issues/05-typed-streamlit-parity.md) | [03](issues/03-reviewer-interactions-recovery.md), [04](issues/04-protected-progressive-coaching.md) | ready-for-agent | 4 |
| [06 — Complete text checkpoint and measured local handoff](issues/06-text-checkpoint-handoff.md) | [05](issues/05-typed-streamlit-parity.md) | ready-for-agent | 6 |
| [07 — OpenRouter-only live-caption feasibility prototype](issues/07-speech-feasibility-prototype.md) | [06](issues/06-text-checkpoint-handoff.md) | ready-for-agent | 5 |
| [08 — Authorized OpenRouter voice answers in Speaker desk](issues/08-authorized-web-voice-answers.md) | [07](issues/07-speech-feasibility-prototype.md) + passed prototype/review gate | ready-for-agent | 5 |
| [09 — Voice probe replies, lifecycle and truthful coaching evidence](issues/09-voice-probes-lifecycle-evidence.md) | [08](issues/08-authorized-web-voice-answers.md) | ready-for-agent | 5 |
| [10 — Android speech integration and readiness evidence](issues/10-android-speech-integration.md) | [09](issues/09-voice-probes-lifecycle-evidence.md) | ready-for-agent | 4 |
| [11 — iOS speech integration and readiness evidence](issues/11-ios-speech-integration.md) | [09](issues/09-voice-probes-lifecycle-evidence.md) | ready-for-agent | 4 |
| [12 — Complete migration review and local handoff](issues/12-integrated-migration-handoff.md) | [10](issues/10-android-speech-integration.md), [11](issues/11-ios-speech-integration.md) | ready-for-agent | 5 |

## Where to start

Tickets 01–03 have passed their local implementation/review gates. Ticket 04
is the unstarted frontier; 05 requires both 03 and 04. After 09, tickets 10 and
11 form an independent frontier. Coordinate shared edits. Dependencies do not
authorize parallel agents or external-model sharing, and ready-for-agent does
not waive evidence gates.

## Two runnable local checkpoints

| Checkpoint | Tickets | Result |
| --- | --- | --- |
| 1 — OpenRouter text | 01–06 | Bounded mapping, planner/reviewer questions, interactions, complete progressive coaching and typed Streamlit parity, with fixed settings and protected spending; code-only disabled and voice off. |
| 2 — Proven speech replacement | 07–12 | Reviewed OpenRouter-only caption prototype, then authorized web answers/probes, lifecycle/evidence preservation, Android/iOS integration and integrated handoff only to the evidenced extent. |

Expand the shared integration before migrating mapping in 01. Migrate remaining
callers by user-visible operation, then remove obsolete direct-provider text
paths in 06. Unmigrated local paths during this sequence are transitional code;
they must never be an automatic fallback from an OpenRouter request. Every slice
keeps the app runnable and includes its own accounting, recovery and verification.
Intermediate slices are not a finished migration or permission to deploy.

## Gates and preserved rules

- Use the exact model/reasoning assignments in the parent spec; no silent model
  fallback, provider default escalation or direct OpenAI fallback.
- Keep preparation separate, run settings fixed and coaching funds protected.
  Unknown or stale provider usage is not free. Preserve current defense prices,
  vouchers, opening/history charging and eligible credit-return rules.
- Ticket 07 is a real compatibility/review gate. A failed or unreviewed prototype
  blocks 08 and its descendants and leaves voice off with typing usable. Do not
  call text-only completion a successful full speech migration.
- Numeric caps, Qwen compatibility, actual model/speech quality, cost and retention
  require the specified measurements. No chosen speech model, savings or quality
  superiority is assumed.
- Offline AI/speech/Google/payment mocks, real local PostgreSQL, browser previews,
  live providers, hosted transport and installed Android/iOS recording are distinct
  evidence. Builds and source checks cannot stand in for installed-device capture.
- Android/iOS toolchain or device gaps may be documented as pending in 10/11 and
  carried into 12; they cannot be treated as passing enablement gates. Preserve
  typed access and make remaining readiness limits explicit.
- The parent specification is unchanged. No runtime, provider configuration,
  credentials, price, main branch or deployment was changed by ticket publication.

## Next step

Implement ticket 04 (protected progressive coaching). Ticket 05 requires both
03 and 04. Actual-provider compatibility/quality/cost, user review and publication
remain separate gates. No push or deployment is authorized by this handoff.

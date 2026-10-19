# 02 — Funded defense runs with assigned reviewer questions

**What to build:** A host starts a funded research/mixed run whose GLM low
planner selects the next eligible move and whose assigned reviewer asks the
validated question, with consistent state and once-only charging.

**Blocked by:** [01 — Bounded OpenRouter paper mapping](01-bounded-paper-mapping.md).

**Status:** ready-for-human

- [x] Snapshot task/reviewer models, reasoning and output limits for the run. Establish
  its provider ceiling and protected coaching reserve sized to the confirmed
  question budget; reject an unfundable start before game-credit commitment.
- [x] Apply the confirmed four-reviewer model bundle; verify Qwen's actual supported
  bounded reasoning contract rather than inventing an effort selector.
- [x] Validate planner selection/coverage/completion before reviewer dispatch. Validate
  both stages together before question, coverage, history, vote/clock or credit
  commit; valid completion needs no reviewer-generation call.
- [x] Preserve reviewer order, follow-ups, citation policy, recent openings, bounded
  duplicate regeneration and explicit repeat acceptance. Include every dispatched
  stage/retry in provider accounting, including rejected or stale results.
- [x] Retain answers and safe selected-model recovery; enforce cancellation between
  stages, duplicate-work suppression, fixed settings and once-only game charging.
  Verify controlled-clock/two-client flows and real database funding races.

## Comments

- Approved as drafted on 2026-10-19. Parent: [OpenRouter migration specification](../spec.md).
- Read the [approved dependency index](../README.md) for checkpoint boundaries and evidence gates. This ticket does not authorize a push, deployment or change to main.
- Implemented and independently reviewed locally on 2026-10-19 against baseline `bd10cc3`; see the [verified handoff](../reviews/02.md) for evidence and review findings. User visual approval and actual-provider evidence remain separate and pending.

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

- 2026-10-19 streamed-error correction verified: **1efb1a1** preserves manual recovery for HTTP200 SSE auth/quota/rate errors and unknown envelopes, bounded server-error retries and redacted messages. New paired HTTP/SSE two-client checks preserve answers and full failure-cost reservations. Full isolated Python **656**, React **393** and build pass; independent Standards **0**, Spec **0**. Original three probes and unchanged SSE429 probe all pass. See [final handoff](../reviews/02-sse-fix.md). All criteria restored; tickets 03–04 unblocked, not started. Actual provider/user review remains separate; no push or deployment. Supersedes the remaining-finding notes below.

- 2026-10-19 independent follow-up: all three original probes pass and90focused tests pass againstc6ca8ac. One P2remains: documented HTTP200SSE rate-limit errors become InvalidQuestionResponse and automatically dispatch again instead of preserving manual429recovery. See [follow-up](../reviews/02-follow-up.md). Only recovery criterion reopened; mixed citations and conversation guidance are verified fixed. Runtime source unchanged by review;03–04stillgated.
- 2026-10-19 recheck fixes: all three P2 findings corrected locally with mocked evidence — typed retryable transport errors feed the bounded post-answer automatic retry with every dispatched attempt accounted, the funded route restores legacy mixed-mode citation eligibility (per-role code-citation tests; research stays paper-only), and the reviewer composer reuses the shared conversation/scenario policy. The recheck's own three probes now pass; artifact gates: focused90, full650, React393/build, real-local-PostgreSQL185. Corrected diff awaits the user's follow-up recheck; tickets03–04 stay gated on it.
- 2026-10-19 independent recheck: reopened citation/recovery criteria after three reproduced P2 findings: mixed implementation citations rejected, transient post-answer errors skip automatic retry, and shared conversation/probe/scenario guidance omitted. See [recheck](../reviews/02-recheck.md). Existing86focused tests pass but three additional review probes reproduce failures. Runtime source unchanged; fixes and follow-up review required before publication or dependent work.
- Approved as drafted on 2026-10-19. Parent: [OpenRouter migration specification](../spec.md).
- Read the [approved dependency index](../README.md) for checkpoint boundaries and evidence gates. This ticket does not authorize a push, deployment or change to main.
- Implemented and independently reviewed locally on 2026-10-19 against baseline `bd10cc3`; see the [verified handoff](../reviews/02.md) for evidence and review findings. User visual approval and actual-provider evidence remain separate and pending.

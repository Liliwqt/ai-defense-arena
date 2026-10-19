# 05 — Typed Streamlit research policy parity

**What to build:** A Streamlit user can prepare and finish a typed research or
mixed defense using the same OpenRouter model, reasoning and allowance policy.

**Blocked by:** [03 — Same-reviewer clarification, probes and answer recovery](03-reviewer-interactions-recovery.md); [04 — OpenRouter progressive coaching from protected funds](04-protected-progressive-coaching.md).

**Status:** ready-for-human

- [x] Reuse the migrated preparation, planner/reviewer, interaction and coaching
  behavior with fixed scope settings and authoritative spending reservations.
- [x] Preserve the current single-browser typed interface, explicit preparation,
  grounded citations, inline report, failed-only recovery and disabled code-only.
- [x] Prevent direct-provider key dependencies or spending-limit bypass through the
  fallback. Preserve accepted answers and sections through its retry lifecycle.
- [x] Demonstrate complete short/long typed research/mixed runs and safe failures
  through existing fallback/session/report seams, with provider mocks.

## Comments

- Approved as drafted on 2026-10-19. Parent: [OpenRouter migration specification](../spec.md).
- Read the [approved dependency index](../README.md) for checkpoint boundaries and evidence gates. This ticket does not authorize a push, deployment or change to main.

- Implemented locally in **1fa64ed**, reviewed against user-confirmed **d53f22e** on 2026-10-20. Standards 0 / Spec 0. See [verification and remaining gates](../reviews/05.md). Actual-provider checks and publication remain separate; no push/deployment.

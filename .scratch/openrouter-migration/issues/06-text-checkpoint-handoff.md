# 06 — Complete text checkpoint and measured local handoff

**What to build:** The complete text experience runs without reachable direct
OpenAI service dependencies, with verified limits, useful setup guidance and a
local review that clearly identifies actual-provider evidence still required.

**Blocked by:** [05 — Typed Streamlit research policy parity](05-typed-streamlit-parity.md).

**Status:** needs-info

- [x] Contract obsolete text provider paths/setup requirements only after all callers
  have migrated. An OpenAI-compatible SDK may remain; direct-service fallback may
  not. Keep voice off, code-only disabled and typing usable.
- [x] Run full offline suites/build, real local PostgreSQL accounting/recovery checks
  and complete two-client twelve-question research/mixed defenses covering the
  protected history/credit/coaching rules and cross-field source contexts.
- [x] Present desktop/portrait/landscape keyboard previews for setup, mapping,
  blocked/retry states and progressive Results. Preserve main and unrelated work.
- [ ] Separately check the chosen account/routes against schema/context/reasoning
  contracts, especially Qwen; compare the same synthetic papers/answers for
  usefulness, latency and actual total usage including planner and retries.
- [ ] Finalize measured numeric task/preparation/run/coaching limits against large
  accepted inputs and long required reports before claiming rollout readiness.
  Unavailable evidence remains pending; a failed model gate must be reported.
- [ ] Complete checkpoint 1 locally, without a push/deployment or voice enablement.

## Comments

- Approved as drafted on 2026-10-19. Parent: [OpenRouter migration specification](../spec.md).
- Read the [approved dependency index](../README.md) for checkpoint boundaries and evidence gates. This ticket does not authorize a push, deployment or change to main.

- Offline slice implemented in **46a72d3**, README correction **b16b2b6**, reviewed against user-confirmed **197edbe** on2026-10-20. Standards0 / Spec0 remaining for authorized offline work. [Review/evidence](../reviews/06.md).
- User explicitly chose **“Not configured; finish offline checks first.”** No paid inference. Actual chosen-account/model contracts, quality/latency/billed usage and finalized numeric limits remain pending; checkpoint1 is incomplete and07stays blocked. Need a configured local OpenRouter route/account and measurements before closing these three remaining criteria. No push/deployment or voice enablement.

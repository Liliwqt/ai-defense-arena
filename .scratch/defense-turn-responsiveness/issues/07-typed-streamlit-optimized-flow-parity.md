# 07 — Typed Streamlit optimized-flow parity

**What to build:** a typed fallback user completes the same optimized Standard
defense with grounded context, preserved draft/answers and correct recovery.

**Blocked by:** 06 — Focused evidence and bounded broader lookup.

**Status:** ready-for-human

Source: [confirmed specification](../spec.md). Breakdown approved on 2026-10-21.

- [x] Use shared combined interpretation/planning, focused evidence/broader lookup
  and retained-plan recovery across normal/probe/clarification/alternate paths.
- [x] Preserve the same per-run model/reasoning/output/context policy and spending
  rules; no fallback-specific credentials, model switch or allowance reset.
- [x] Apply bounded processing/retry with equivalent truthful stage text/native
  indicator; reruns cannot replay a submission or restart an active operation.
- [x] Preserve drafts and accepted answers, legacy snapshots, citations, language,
  opening history, coaching progression and once-only financial effects.
- [x] Keep Free's capacity/model policy and code-only disablement/voice-off boundary.
- [x] Verify complete synthetic-router whole-app research/mixed defenses, failure
  after acceptance, stage-only retry, deadline and allowance exhaustion; mocked
  results do not establish actual conversation quality.

## Comments

2026-10-22: Implemented and independently reviewed against `e415ca6`. All 6 local
checks pass; [review and evidence](../reviews/07.md) records 833 Python tests
(providers mocked), 414 React tests/build and 24 real-local-PostgreSQL checks.
[Typed flow details](../../../docs/TYPED_RESEARCH_FLOW.md). Human review and
actual-provider speed/quality/cost remain separate. No push or deployment.

# 06 — Focused evidence and bounded broader lookup

**What to build:** Standard reviewers receive the relevant verified paper context
without resending the whole source on every interaction, while broader evidence
remains available when necessary.

**Blocked by:** 05 — Clarification, probes and alternate turn paths.

**Status:** ready-for-human

Source: [confirmed specification](../spec.md). Breakdown approved on 2026-10-21.

- [x] Provide a reusable accepted-source evidence view with study-wide context,
  confirmed map/profile, exact relevant/neighboring passages and necessary
  coverage/conversation/language/probe history. Scope reuse to confirmed content.
- [x] Preserve original identities/locations and validate every returned citation
  against the accepted source, retaining paper-only versus mixed/code eligibility.
- [x] Support finite explicit broader lookup for insufficient context within the same
  processing/retry/spending window; record expansion overhead and supplied usage.
- [x] Measure/select context and lookup bounds using representative fixtures; if
  evidence remains inadequate, retain work and recover rather than guess.
- [x] Never equate a missing excerpt/map entry with absence in the paper, or treat a
  host profile edit/AI summary as replacement source evidence.
- [x] Use the focused policy on all migrated interactive paths, including separate
  opening/timeout planning. Mapping/coaching policy stays intact; no per-question
  remapping, new external vector service or implicit persistent provider memory.
- [x] Recalculate conservative bounds for actual serialized context/extra work;
  preserve quotas, uncertain holds, protected coaching and policy immutability.
- [x] Verify cross-section/cross-document evidence, qualitative/theoretical and mixed
  studies, code citations, ambiguous profiles and changed preparation identity
  through provider-contract and complete room tests. Prove broader lookup or
  honest recovery when decisive evidence is outside the initial context.

## Comments

2026-10-22: Implemented and independently reviewed against `4b25a6f`, including
corrections to all six findings in [the initial check](../reviews/06-recheck.md).
[Final review](../reviews/06-fixes.md) records 824 Python tests (providers mocked),
414 React tests/build, 16 real-local-PostgreSQL checks and the synthetic context
measurements. Captured bounds and dispatch-time funding are described in
[focused evidence](../../../docs/FOCUSED_EVIDENCE.md). All 8 local checks pass;
human review remains open. Actual provider compatibility, speed, quality and
cost remain separate ticket 08 evidence. No push or deployment.

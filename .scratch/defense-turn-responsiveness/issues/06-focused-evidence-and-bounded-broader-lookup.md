# 06 — Focused evidence and bounded broader lookup

**What to build:** Standard reviewers receive the relevant verified paper context
without resending the whole source on every interaction, while broader evidence
remains available when necessary.

**Blocked by:** 05 — Clarification, probes and alternate turn paths.

**Status:** ready-for-agent

Source: [confirmed specification](../spec.md). Breakdown approved on 2026-10-21.

- [ ] Provide a reusable accepted-source evidence view with study-wide context,
  confirmed map/profile, exact relevant/neighboring passages and necessary
  coverage/conversation/language/probe history. Scope reuse to confirmed content.
- [ ] Preserve original identities/locations and validate every returned citation
  against the accepted source, retaining paper-only versus mixed/code eligibility.
- [ ] Support finite explicit broader lookup for insufficient context within the same
  processing/retry/spending window; record expansion overhead and supplied usage.
- [ ] Measure/select context and lookup bounds using representative fixtures; if
  evidence remains inadequate, retain work and recover rather than guess.
- [ ] Never equate a missing excerpt/map entry with absence in the paper, or treat a
  host profile edit/AI summary as replacement source evidence.
- [ ] Use the focused policy on all migrated interactive paths, including separate
  opening/timeout planning. Mapping/coaching policy stays intact; no per-question
  remapping, new external vector service or implicit persistent provider memory.
- [ ] Recalculate conservative bounds for actual serialized context/extra work;
  preserve quotas, uncertain holds, protected coaching and policy immutability.
- [ ] Verify cross-section/cross-document evidence, qualitative/theoretical and mixed
  studies, code citations, ambiguous profiles and changed preparation identity
  through provider-contract and complete room tests. Prove broader lookup or
  honest recovery when decisive evidence is outside the initial context.

## Comments

Not started. Local ticket publication does not authorize implementation, push or deployment.

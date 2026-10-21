# 05 — Clarification, probes and alternate turn paths

**What to build:** the optimized flow preserves a natural, correct defense when
defenders ask for explanation, supply a probe reply, miss a turn or use recovery.

**Blocked by:** 04 — Combined planning for accepted answers.

**Status:** ready-for-agent

Source: [confirmed specification](../spec.md). Breakdown approved on 2026-10-21.

- [ ] Clarification/probe decisions stay on the same question and cannot advance
  coverage or execute a next-turn plan. Preserve probe limits and language intent.
- [ ] Resolve accepted probe exchanges using the original answer plus attributed
  reply and perform combined planning without discarding either contribution.
- [ ] Keep the separate planner for openings/unanswered/timeout transitions and
  direct/saved answers that have no valid combined result; do not invent one.
- [ ] Preserve existing opening-history repeated-candidate/explicit-acceptance rules,
  reviewer eligibility and commit-before-charge/publication semantics.
- [ ] Validate completion, then use existing progressive coaching/closing/results
  settlement; no fabricated answer/strength for missed turns or replayed closing.
- [ ] Retain reaction timing/next-reviewer attribution, exact citations, conversation
  history, profile/source separation and English/modern Bisaya preferences.
- [ ] Verify each interaction/alternate path through two-client authorized commands,
  recovery after every relevant stage and unchanged deadline/pause accounting.
- [ ] Prove failed decisions leave live coverage/financial state unchanged; completed
  work and stale callbacks cannot be applied twice or affect a newer run.

## Comments

Not started. Local ticket publication does not authorize implementation, push or deployment.

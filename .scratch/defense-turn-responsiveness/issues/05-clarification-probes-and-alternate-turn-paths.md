# 05 — Clarification, probes and alternate turn paths

**What to build:** the optimized flow preserves a natural, correct defense when
defenders ask for explanation, supply a probe reply, miss a turn or use recovery.

**Blocked by:** 04 — Combined planning for accepted answers.

**Status:** ready-for-human

Source: [confirmed specification](../spec.md). Breakdown approved on 2026-10-21.

- [x] Clarification/probe decisions stay on the same question and cannot advance
  coverage or execute a next-turn plan. Preserve probe limits and language intent.
- [x] Resolve accepted probe exchanges using the original answer plus attributed
  reply and perform combined planning without discarding either contribution.
- [x] Keep the separate planner for openings/unanswered/timeout transitions and
  direct/saved answers that have no valid combined result; do not invent one.
- [x] Preserve existing opening-history repeated-candidate/explicit-acceptance rules,
  reviewer eligibility and commit-before-charge/publication semantics.
- [x] Validate completion, then use existing progressive coaching/closing/results
  settlement; no fabricated answer/strength for missed turns or replayed closing.
- [x] Retain reaction timing/next-reviewer attribution, exact citations, conversation
  history, profile/source separation and English/modern Bisaya preferences.
- [x] Verify each interaction/alternate path through two-client authorized commands,
  recovery after every relevant stage and unchanged deadline/pause accounting.
- [x] Prove failed decisions leave live coverage/financial state unchanged; completed
  work and stale callbacks cannot be applied twice or affect a newer run.

## Comments

Implemented locally against `0388fc4`; all eight acceptance checks have evidence.
See [independent review and verification](../reviews/05.md). Accepted Standard
probe replies use combined planning with original and reply attribution retained;
alternate routes preserve separate validated planning and existing recovery.
806 Python tests (providers mocked), 414 React tests/build and 8 real-local
PostgreSQL checks passed. Human review and actual-provider/hosted/device evidence
remain separate. Ticket 06 is next, unstarted. No push or deployment.

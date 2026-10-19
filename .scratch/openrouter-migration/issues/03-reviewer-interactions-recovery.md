# 03 — Same-reviewer clarification, probes and answer recovery

**What to build:** Defenders answer, ask for clarification or reply to an
answer probe using the current reviewer's model and lower supported reasoning,
with existing time limits and clear recovery when further work is blocked.

**Blocked by:** [02 — Funded defense runs with assigned reviewer questions](02-funded-reviewer-questions.md).

**Status:** ready-for-human

- [x] Migrate submission interpretation, clarification and probe generation to the
  selected reviewer's fixed assignment and verified lower reasoning policy.
- [x] Reserve and reconcile each interaction/retry against the run's non-coaching
  allowance; exhaustion retains accepted work and does not become a paid retry loop.
- [x] Preserve direct-answer recovery, chosen-defender permissions, same-question
  numbering, answer/probe drafts, timeout rules and source/language boundaries.
- [x] Do not freeze authoritative answer timers on provider or budget failure; stale
  interpretation/clarification/probe work cannot overwrite a later turn/run.
- [x] Verify actual room actions and recipient views with mocked providers and a
  controlled clock, including duplicate commands, errors, reconnect and phone controls.

## Comments

- Approved as drafted on 2026-10-19. Parent: [OpenRouter migration specification](../spec.md).
- Read the [approved dependency index](../README.md) for checkpoint boundaries and evidence gates. This ticket does not authorize a push, deployment or change to main.
- Implemented and verified locally on 2026-10-19; see the [local validation and code review](../reviews/03.md). Funded interactions now use the run-assigned reviewer model and bounded lower reasoning, reserved against the non-coaching allowance. Offline evidence: 10 new interaction tests, 674-test Python discovery (only two pre-existing foreign `tests/test_local_dev.py` failures), unchanged React 393 tests/build. User visual review, actual-provider quality/cost and publication remain pending.

# 03 — Same-reviewer clarification, probes and answer recovery

**What to build:** Defenders answer, ask for clarification or reply to an
answer probe using the current reviewer's model and lower supported reasoning,
with existing time limits and clear recovery when further work is blocked.

**Blocked by:** [02 — Funded defense runs with assigned reviewer questions](02-funded-reviewer-questions.md).

**Status:** ready-for-agent

- [ ] Migrate submission interpretation, clarification and probe generation to the
  selected reviewer's fixed assignment and verified lower reasoning policy.
- [ ] Reserve and reconcile each interaction/retry against the run's non-coaching
  allowance; exhaustion retains accepted work and does not become a paid retry loop.
- [ ] Preserve direct-answer recovery, chosen-defender permissions, same-question
  numbering, answer/probe drafts, timeout rules and source/language boundaries.
- [ ] Do not freeze authoritative answer timers on provider or budget failure; stale
  interpretation/clarification/probe work cannot overwrite a later turn/run.
- [ ] Verify actual room actions and recipient views with mocked providers and a
  controlled clock, including duplicate commands, errors, reconnect and phone controls.

## Comments

- Approved as drafted on 2026-10-19. Parent: [OpenRouter migration specification](../spec.md).
- Read the [approved dependency index](../README.md) for checkpoint boundaries and evidence gates. This ticket does not authorize a push, deployment or change to main.

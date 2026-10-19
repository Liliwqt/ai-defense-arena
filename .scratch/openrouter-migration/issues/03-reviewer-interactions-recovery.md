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

- 2026-10-20 delayed-retry fix verified: source **c4d838d** captures each retry's current remaining time while preserving saved text, provenance and stale-work guards. Recovery waiting time remains consumed and paused snapshots show the correct remaining time. Four unchanged independent probes and 52 focused tests pass; full isolated Python **673**, React **393/build**, independent Standards **0**, Spec **0**. See [final fix handoff](../reviews/03-retry-fix.md). Timer criterion restored, ready-for-human locally. Ticket 04 remains unblocked; 05 needs both 03 and 04. Actual-provider/user review remains separate; no push/deployment. Supersedes the remaining-finding notes below.

- 2026-10-20 timer follow-up: the original four-minute pause is independently verified fixed (both old probes pass), but delayed retries refund time already spent waiting in recovery. Two new room probes wait100seconds, retry withzero processing, then observe100seconds added back after another refusal or successful clarification. See [follow-up evidence](../reviews/03-timer-followup.md). Focused48 tests pass; Standards0, Spec1P2. Only timer criterion reopened;04remains independently unblocked and05needs corrected03+04. Runtime/canonical tests unchanged by review; no push/deployment.

- 2026-10-20 independent recheck: one P2 remains in failure-clock handling. Immediate allowance refusal and HTTP503 leave clock_paused=true and the unused 240-second pause intact, despite the timer criterion. Full committed Python 666, new module 10 and React 393/build pass; two additional targeted room probes fail. See [independent recheck](../reviews/03-recheck.md). Only timer criterion reopened; routing/accounting work remains verified. Ticket 04 remains independently unblocked, and 05 still waits 03+04. Runtime/canonical tests unchanged; no push/deployment.

- 2026-10-20 timer correction: the unused processing pause now ends on failure. `TimedTurn.interpretation_failed` settles the pause (charging only elapsed time beyond the AI-pause budget), clears the pause fields, restores the remaining answer/probe deadline and bumps the clock; the funded failure path schedules that restored clock, and `retry_interpretation` re-arms the pause for the new request. Coverage added: instant HTTP503 and allowance refusal assert `clock_paused=false`, `pause_deadline_ms=null` and a deadline equal to the original; retry re-pauses only for elapsed processing time; a failed probe reply restores the probe deadline; a stale failure cannot touch a timed-out clock. Both independent probes now pass with `failure_deadline == original_deadline == 1135001`; the interaction module passes 12/12; full Python discovery passes 677 with only the two pre-existing foreign `tests/test_local_dev.py` failures; React 393 tests/build pass. Offline, providers mocked. Criterion re-checked; ticket ready for human review again.

- Approved as drafted on 2026-10-19. Parent: [OpenRouter migration specification](../spec.md).
- Read the [approved dependency index](../README.md) for checkpoint boundaries and evidence gates. This ticket does not authorize a push, deployment or change to main.
- Implemented and verified locally on 2026-10-19; see the [local validation and code review](../reviews/03.md). Funded interactions now use the run-assigned reviewer model and bounded lower reasoning, reserved against the non-coaching allowance. Offline evidence: 10 new interaction tests, 674-test Python discovery (only two pre-existing foreign `tests/test_local_dev.py` failures), unchanged React 393 tests/build. User visual review, actual-provider quality/cost and publication remain pending.

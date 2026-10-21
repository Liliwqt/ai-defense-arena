# 04 — Combined planning for accepted answers

**What to build:** an ordinary accepted Standard answer leads to the next grounded
question through two serial AI requests rather than the existing three.

**Blocked by:** 03 — Bounded processing and transient retry.

**Status:** ready-for-agent

Source: [confirmed specification](../spec.md). Breakdown approved on 2026-10-21.

- [ ] Introduce a versioned combined interaction/assessment/selection contract for
  new supported Standard runs, with unchanged saved legacy routes.
- [ ] Derive eligible next options from a detached prospectively resolved session;
  never mutate live coverage just to construct a request.
- [ ] The outgoing reviewer's assigned model interprets an accepted normal answer
  and proposes coverage/eligible next selection or completion in one request.
- [ ] The chosen next reviewer generates exact-source question/reaction dialogue;
  no third standalone planner call appears on the ordinary accepted-answer path.
- [ ] Validate assessments, identities, allowed reviewer/topic/follow-up and budget
  completion before advancing coverage or publishing; reject partial/ungrounded
  results and preserve original answer and speaker attribution.
- [ ] Reuse the new validated plan through 02/03 recovery; failed planning cannot erase
  an accepted answer, and successful combined work is not repeated on writer retry.
- [ ] Recalculate conservative admission/dispatch bounds for the combined schema and
  actual stages with unchanged ceilings, coaching protection and unknown holds;
  include a real local concurrency case and no duplicate financial effects.
- [ ] Keep full-source grounding for this slice and compatible routes for exchanges
  completed in 05. Do not change model assignments based only on mocks. Exact
  output/reasoning compatibility remains a gate, not a claimed quality upgrade.
- [ ] Verify complete short research/mixed normal-answer runs across all reviewers
  and observable request routing/counts, showing correct stages/accepted status.

## Comments

Not started. Local ticket publication does not authorize implementation, push or deployment.

# Combine submission interpretation and adaptive next-turn planning

Status: accepted design; Q3/Q4 direction agreed on 2026-10-20 and consolidated
plan confirmed in Q11 on 2026-10-21. The shared pipeline is implemented locally;
actual-provider reliability and performance gates remain open.

The OpenRouter research flow currently interprets an answer, plans the next turn
with GLM, then asks the selected reviewer to write a question. Combine
interpretation and an accepted answer's coverage/eligible-next-selection proposal
in the outgoing reviewer's request to remove one sequential call, while retaining
the next reviewer's assigned model for dialogue and exact-source citations.

This deliberately changes normal planning ownership from fixed GLM to each
outgoing reviewer; every role needs quality validation. Plan against a detached
prospectively resolved session and validate before advancing live coverage.
Clarifications/probes must not advance the turn, and openings/timeouts retain a
separate planner. Reuse a validated plan after reviewer-only failure only within
the unchanged logical operation; ending/restarting invalidates it.

Keep the existing pipeline for saved legacy policies and version new policy
snapshots, including correct spending bounds. The alternative of retaining the
separate planner preserves its ownership but leaves the extra call; using GLM
for both planning and dialogue would lose role-assigned question models. See the
[responsiveness plan](../DEFENSE_TURN_RESPONSIVENESS_PLAN.md) for the confirmed
constraints, measurement targets and separate live-evidence requirements.

The 2026-10-24 local correction represents a combined review's next move as one
candidate ID. The server sends named candidates derived from its existing
question options and resolves a validated ID to the original complete
reviewer/topic/follow-up tuple. It still validates the prospective plan after
assessment; a candidate is not guaranteed eligible for every proposed coverage
status. A null selection means completion only when the existing completion
guard permits it. Clarifications and probes must keep assessment/selection null.

This changes the provider response representation, not the stored domain plan
or a run's model/reasoning/timer/spending settings. Separate legacy planning is
unchanged. Complete legacy response tuples remain compatible only if they match
one whole candidate; unknown, half-complete or mixed-format selections are
rejected. No field is invented to repair an invalid response. Live compatibility
and performance require separate evidence before promoting the optimized route.

The subsequent local action-contract correction gives the existing lookup
envelope three strict result variants. Answer contains a required assessment and
candidate selection (null only for permitted completion); clarification contains
its explanation; probe contains its request/references. Pending-probe replies
offer only answer or clarification. Each variant forbids the others' fields.
The compatibility parser may omit unused null slots from older flat responses,
but never drops contradictory non-null data. All domain validation still runs
after conversion, and provider acceptance remains a separate live gate.

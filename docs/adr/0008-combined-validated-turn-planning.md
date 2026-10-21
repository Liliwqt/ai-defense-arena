# Combine submission interpretation and adaptive next-turn planning

Status: accepted design; Q3/Q4 direction agreed on 2026-10-20 and consolidated
plan confirmed in Q11 on 2026-10-21. Implementation has not started.

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

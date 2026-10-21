# Defense-turn responsiveness tickets

Approved breakdown: 2026-10-21. Ticket 01 has 9/9 local implementation checks and
is ready-for-human; visual sign-off is separate. Ticket 02 now has 8/8 local checks and is ready-for-human; see
[its review](reviews/02.md). Ticket 03 is unblocked; later tickets remain unstarted.
See [fix verification](reviews/01-fixes.md) and [interface evidence](reviews/01-interface.md).

| Ticket | Blocked by | Status |
| --- | --- | --- |
| [01 — Factual animated waiting and baseline timing](issues/01-factual-animated-waiting-and-baseline-timing.md) | None | ready-for-human |
| [02 — Retained answers and failed-stage recovery](issues/02-retained-answers-and-failed-stage-recovery.md) | 01 | ready-for-human |
| [03 — Bounded processing and transient retry](issues/03-bounded-processing-and-transient-retry.md) | 02 | ready-for-agent |
| [04 — Combined planning for accepted answers](issues/04-combined-planning-for-accepted-answers.md) | 03 | ready-for-agent |
| [05 — Clarification, probes and alternate turn paths](issues/05-clarification-probes-and-alternate-turn-paths.md) | 04 | ready-for-agent |
| [06 — Focused evidence and bounded broader lookup](issues/06-focused-evidence-and-bounded-broader-lookup.md) | 05 | ready-for-agent |
| [07 — Typed Streamlit optimized-flow parity](issues/07-typed-streamlit-optimized-flow-parity.md) | 06 | ready-for-agent |
| [08 — Measured reviewer settings and provider gate](issues/08-measured-reviewer-settings-and-provider-gate.md) | 06 | ready-for-agent |
| [09 — Integrated defenses and local review handoff](issues/09-integrated-defenses-and-local-review-handoff.md) | 07, 08 | ready-for-agent |

Checkpoint 1 ends at 03. Checkpoint 2 joins typed fallback 07 and measured
provider gate 08 in the final review 09. Pending live evidence must stay explicit;
a blocked or failed provider gate is not a live-ready completion.

Start with [the confirmed specification](spec.md). Each ticket has its own
acceptance checks; integrated verification does not replace those checks.

Ticket publication and implementation are local only. No GitHub publication or
deployment of this ticket work has occurred.

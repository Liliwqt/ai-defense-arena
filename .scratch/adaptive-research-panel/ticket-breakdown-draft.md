# Adaptive research panel: approved ticket breakdown

Started: 2026-10-14
Status: approved and published locally on 2026-10-14.
Source: [ready-for-agent specification](spec.md).

The user approved the size and blocking edges as drafted. Four separate ready-for-agent implementation tickets are now published locally; the parent specification remains unchanged. Each slice includes its observable behavior and appropriate existing room, structured-AI and presentation checks; every slice leaves the app runnable. No standalone prefactoring ticket is necessary: introduce the bounded profile value and validation with its first visible use, then reuse that boundary.

## Published tickets

- [01 — Grounded profile review and confirmation](issues/01-grounded-profile-review.md)
- [02 — Profile corrections, remapping and safe recovery](issues/02-profile-corrections-remapping.md)
- [03 — Consistent subject-aware reviewer conversations](issues/03-subject-aware-reviewers.md)
- [04 — Integrated defenses and local review handoff](issues/04-integrated-local-review.md)

Implementation frontier: ticket 01 only. Work 01 → 02 → 03 → 04; each ticket starts after its blocker is complete. Publication does not start implementation or authorize a commit, push or deployment.

## Approved slices

1. **Grounded profile review and confirmation**

   **Blocked by:** None — can start immediately.

   **What it delivers:** Preparing a research or mixed defense presents a grounded, multi-field/multi-approach suggested profile alongside the existing map. The host can inspect and confirm the profile, uncertainty and question budget; teammates can inspect the same state. React and Streamlit both support this read/confirm path. Starting captures the confirmed profile without changing existing reviewer dialogue yet.

   Approved acceptance criteria:

   - The existing single structured mapping request returns validated fields, approach choices, optional setting, source explanation, grounded paper references and explicit uncertainty. No extra classification request is made.
   - Multiple fields/approaches are supported; an explicitly confirmed Unclear profile is permitted without inventing a method. Stage remains separate.
   - Server-owned profile excerpts use existing citation/location validation. Invalid references, unsupported choices, excessive values or incomplete final output fail preparation safely.
   - Existing streamed topics remain Draft until final validation; neither streamed nor final-but-unconfirmed profiles appear host-confirmed.
   - React and Streamlit show the suggested profile and cited basis; only the host can confirm the current map/profile/budget. Guests see read-only profile and confirmation state.
   - Start requires current confirmation; older research maps without a validated profile require preparing again. A run captures a fixed profile and reconnect restores it without another AI call.
   - Code-only defenses and existing account, timer, coverage and run-charge behavior remain unchanged. Existing tests/fixtures stay compatible through explicit profile-aware research fixtures rather than an anonymous approval bypass.
   - Mocked normal HTTP/WebSocket and mapping-request checks demonstrate host/guest authority, uncertainty acknowledgment, invalid output rejection, legacy-map handling and restored snapshots. React tests and the Streamlit read/confirm path are checked.

2. **Profile corrections, remapping and safe recovery**

   **Blocked by:** 01 — Grounded profile review and confirmation.

   **What it delivers:** The host corrects fields, approaches or setting, prepares a new map and reconfirms the resulting profile/budget in React or Streamlit. Corrections remain attributed host descriptions, survive failure/retry and cannot be mistaken for source evidence or silently reset by the next map.

   Approved acceptance criteria:

   - Edits are host-only and limited to preparation; active-run edits are rejected without resetting answers or other valid state.
   - Unsaved changes prevent the host UI from presenting old approval as ready to start. Accepted changes invalidate old map approval and Start eligibility.
   - Remapping receives immutable correction input as data, retains host-selected descriptions, and keeps its citation-grounded explanation and uncertainties distinct. The model may flag supported conflicts rather than overwrite the correction or claim it is paper evidence.
   - The host receives a fresh map identity and must confirm the updated profile and budget. Stale approval or results cannot re-enable Start or replace a newer correction/map.
   - Failed mapping retains uploads and corrections; retry uses the same saved input. Duplicate preparation, edits during pending work and late callbacks are handled consistently with existing coordinator fences, without duplicate AI work or silent state loss.
   - Reconnect restores saved correction and approval state. Streamlit correction changes invalidate its old map/session/coaching scope. An unchanged restart retains the confirmed profile under existing cost/access rules; changing profile cannot bypass preparation or rewrite a prior run.
   - Mocked public room/AI boundaries verify host edits, unchanged guest state, remap/retry, uncertainty and host/source conflict, invalid commands, stale work, reconnect, active-run rejection and preserved access/credit rules. Relevant frontend and fallback checks pass.
   - Finish checkpoint 1: run the full offline suites/build and present profile/map review on desktop, portrait and landscape. Record screenshots and factual implementation/verification notes; adaptive dialogue remains the next checkpoint.

3. **Consistent subject-aware reviewer conversations**

   **Blocked by:** 02 — Profile corrections, remapping and safe recovery.

   **What it delivers:** Research and mixed defenses use the confirmed profile across visible questions, reactions, clarification, answer probes and coaching. The four familiar reviewers challenge reasoning appropriate to each topic and research approach, while host descriptions remain distinct from paper evidence.

   Approved acceptance criteria:

   - One shared profile/guidance boundary supplies the same immutable confirmed profile to every relevant existing request, including submission interpretation and the Streamlit paths. No classifier, separate evaluator or extra dialogue request is added.
   - Methodology adapts to relevant empirical, qualitative, theoretical or computational/design reasoning; Ethics avoids invented participants/approvals; Impact recognizes contribution to knowledge without demanding commercial benefit; Critical examines subject-relevant theory, evidence, alternatives and limitations.
   - Multiple fields/approaches inform the applicable mapped topic. A set of labels does not prove a mixed-methods design. Confirmed uncertainty prompts inquiry rather than fabricated methods or results.
   - A material host/source discrepancy remains attributed context and a grounded question, without presuming either the label or an excerpt proves the interpretation correct.
   - Preserve stable reviewer identities, four opening turns, proposal/completed/inferred-stage handling, existing full source context, exact citations, coverage/budget validation and code-only prompts/policy.
   - Preserve reviewer voices, brief answer-aware reactions, direct-question preference, occasional grounded scenarios, conditional advice, language continuity, same-question clarification intent and answer-probe rules. No fabricated credentials or institutional/country compliance judgments are introduced.
   - Visible dialogue, reconnect, transcript and coaching continue through the existing interfaces without replaying/reclassifying the profile. Timers, voting, retries, account/privacy and charge/return behavior remain unchanged.
   - Mocked request-contract checks and visible room/fallback flows exercise qualitative, quantitative, theoretical, computational/design, ambiguous and interdisciplinary examples plus mixed paper/code. Assertions check shared context and grounded outcomes rather than exact prompt wording or claimed live quality.

4. **Integrated defenses and local review handoff**

   **Blocked by:** 03 — Consistent subject-aware reviewer conversations.

   **What it delivers:** A complete reviewable local feature with two-client research and mixed defenses, responsive preparation/conversation checks, documented limitations and separate evidence for real AI conversation quality.

   Approved acceptance criteria:

   - Complete mocked two-client research and mixed defenses, including a run beyond eight turns, with profile review/correction, explicit uncertainty where relevant, clarification, probes, voting, timeout, retry, reconnect, transcript and coaching.
   - Verify the profile stays fixed, source citations stay exact, outstanding coverage and ending reasons are retained, and no new question/AI call/charge comes from reconnect or profile confirmation.
   - Exercise stale approval/results, failed map recovery, host/source conflicts, legacy-map guidance, unchanged code-only behavior and existing account/payment regression boundaries as part of integrated verification.
   - Run full Python/React suites and production build. Review desktop, portrait and landscape for readable profile/source explanations, keyboard focus, internal scrolling, unclipped controls and preserved question/timer/dock readability.
   - Present screenshots and the actual local preview; update user documentation and the shared handoff log after each checkpoint. Do not mark user visual approval or device/hosted checks complete without evidence.
   - Separately inspect live empirical, theoretical and interdisciplinary conversations when a local key is configured, recording subject relevance, reactions, uncertainty, Ethics/Impact framing and language behavior without secrets/private uploaded text. If credentials are unavailable, explicitly record the missing evidence and keep live quality/publication readiness pending.
   - Preserve existing local reasoning/test-access work, unrelated files, frozen main and the current live service. No publication or deployment occurs within these tickets without a later user request.

## Dependency rationale

The approved graph is 01 → 02 → 03 → 04. Ticket 02 needs the profile/map identity introduced by 01. Ticket 03 needs the authoritative corrected/confirmed profile and run binding completed by 02. Ticket 04 reviews the complete behavior delivered by 03. Only immediate blockers are listed; transitive edges are not repeated.

Tickets 01–02 form checkpoint 1. Tickets 03–04 form checkpoint 2. Every ticket contains feature verification; ticket 04 adds complete defense and visual/live handoff evidence, rather than deferring all testing to the end.

## Approval and publication boundary

The user answered “Approve as drafted.” Published one separate local file per ticket in dependency order with Status: ready-for-agent and its blocking edges. The parent specification was not modified and no implementation has started. The next workflow step is Implement for ticket 01 in a fresh context.

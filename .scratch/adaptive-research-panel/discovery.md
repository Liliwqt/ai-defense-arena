# Adaptive research panel discovery

Started: 2026-10-14
Status: planning complete; specification published as ready-for-agent on 2026-10-14.

Implementation specification: [spec.md](spec.md).

The user requested planning after discussing whether the existing research reviewer roles suit researchers across disciplines. Ask Matt routes this through Grill with Docs before specification, tickets and implementation.

Confirmed plan: [ADAPTIVE_RESEARCH_PANEL_PLAN.md](../../docs/ADAPTIVE_RESEARCH_PANEL_PLAN.md).

## Design tree

- Panel scope → reviewer identity and discipline-specific guidance.
- Profile authority → fields, uncertainty, host corrections, approval and run locking.
- Standards boundary → handling local settings and any supplied institutional rubrics.
- Settled feature behavior → interfaces, compatibility and verification.
- Agreed plan → shared-understanding confirmation and later specification handoff.

Round 1 settled scope, profile authority and standards boundary. Round 2 settled profile details, uncertain classification and correction/remapping policy. Round 3 settled evidence conflicts, interdisciplinary representation and delivery/verification scope. Q10 confirmed the consolidated plan; the decision frontier is empty and no implementation has started.

Read-only interface investigation completed: stable reviewer identities, map approval, separate submission context, streamed validation, reconnect and Streamlit invalidation constraints are recorded in the plan. No provider requests or runtime checks were performed.

## Confirmed context

- Work stays on `feature/question-first-room`.
- The goal is subject-appropriate research practice, building on existing roles and coverage mapping.
- Keep four perspectives for research and mixed defenses; code-only defenses remain unchanged.
- AI suggests field/approach during mapping; the host confirms or corrects the profile before starting.
- Adapt to subject and setting first; institutional rubrics and country-specific compliance judgments are deferred.
- Include editable field, study approach, optional setting and citation-grounded explanation; approach choices include quantitative, qualitative, mixed-methods, theoretical, computational/design, other and unclear.
- Allow the host to confirm uncertainty and continue without fabricated methods.
- Corrections require remapping and renewed budget confirmation; fix the confirmed profile during an active run.
- Attribute host descriptions separately from paper evidence and ask about material discrepancies.
- Support multiple fields/approaches in one profile, applying appropriate perspectives by mapped topic while retaining the four reviewers.
- Mirror React and Streamlit with two runnable checkpoints, full offline suites/build, mocked two-client research/mixed defenses and desktop/phone checks. Present the local preview first; live AI quality remains separate evidence.

## Final confirmation

The user answered Q10 with “Matches—finish planning.” The consolidated plan contains all nine accepted interview choices, compatibility boundaries, acceptance cases and agreed verification. Shared understanding is confirmed. The later To Spec invocation authorized specification synthesis and local tracker publication. The accepted Q9/Q10 testing boundaries were reused without another interview; next is To Tickets. No implementation, push or deployment is authorized by these documentation steps.

Recorded the confirmed Research profile term in `CONTEXT.md`, distinct from study stage, coverage and reviewer credentials. No architectural decision record was needed for these planning choices.

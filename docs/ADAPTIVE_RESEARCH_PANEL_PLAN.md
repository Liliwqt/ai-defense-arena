# Adaptive research panel: consolidated plan

Started: 2026-10-14
Status: planning complete; consolidated plan confirmed by the user on 2026-10-14.
Branch: `feature/question-first-room`. Documentation only; no implementation or remote publication.

Implementation specification published locally on 2026-10-14: [spec.md](../.scratch/adaptive-research-panel/spec.md), Status: ready-for-agent. This plan remains the decision record; the specification is the implementation contract. No feature code or remote publication is included.

## Purpose

Make research questions fit the paper's discipline and study approach while preserving the established reviewer voices. Four broad perspectives alone do not establish disciplinary expertise. The panel remains an AI practice simulation, without invented examiner credentials or institutional approval.

## Planned experience

1. Upload the paper and any accompanying code; retain the existing research-stage choice.
2. Prepare defense with the existing structured mapping request. Alongside grounded topics, propose a concise research profile and identify uncertain classification.
3. Let the host review and correct the profile, then confirm the map and question budget. Teammates can inspect the confirmed profile.
4. Use the same confirmed profile throughout questioning, reactions, clarification, answer probes and coaching. Reconnect restores it without reclassification.

The user confirmed all nine interview choices and the consolidated plan on 2026-10-14. This completes planning; it does not authorize implementation or publication.

## Confirmed decisions

- Keep Methodology, Ethics, Impact and Critical perspectives for research and mixed defenses. Code-only defenses remain unchanged.
- Suggest the research field and study approach during the existing mapping request; the host confirms or corrects the suggested research profile before starting.
- Adapt to the paper's subject and setting first. Institution-specific defense rubrics and country-specific compliance judgments are deferred; do not invent local requirements.
- Include an editable research field, study approach, optional research setting and a short explanation grounded in paper citations. Broad approach choices are quantitative, qualitative, mixed-methods, theoretical, computational/design, other and unclear; these are practice lenses rather than an exhaustive research taxonomy.
- Expose ambiguous classification. The host may correct it or explicitly confirm Unclear and continue; reviewers explore that uncertainty without inventing missing methods.
- A profile correction requires preparing the map again and reconfirming its question budget. This uses another mapping request. Keep the confirmed profile fixed during an active defense; reconnect and same-question clarification preserve it.
- Keep host descriptions distinct from paper evidence. Retain attributed host context, cite what the uploaded material actually says, and ask about material discrepancies without claiming the host's label proves the source describes that method.
- Support multiple fields and approaches within one confirmed profile when appropriate. Each mapped topic guides which perspective applies; neither multiple fields nor multiple method labels automatically establish a mixed-methods design.
- Mirror the flow in React and Streamlit, with two runnable local checkpoints and the agreed verification below. Present the local preview first; live AI quality and publication remain separate steps.

## Confirmed profile and approval behavior

The suggested profile is provisional until final map validation and host confirmation. Cite server-owned paper excerpts for the AI's explanation, retaining explicit gaps when the material is unclear. Host-editable descriptions must be treated as data, not instructions to bypass reviewer roles or source validation.

After a correction, invalidate the old map approval and Start eligibility; retain uploaded files and correction inputs for remapping or retry. A successful reprepare must produce a fresh map identity, after which the host reviews the resulting profile and reconfirms the budget. Unchanged approval and reconnect do not require another AI call. Do not silently discard a host correction in favor of another inferred classification.

During a run, all requests use the same confirmed profile. A different profile belongs to a newly prepared map and a subsequent run, without rewriting the previous transcript or coverage. Research stage remains the existing separate Proposal / Completed study / Let AI infer choice.

## Reviewer adaptation

| Existing perspective | Subject-sensitive focus |
| --- | --- |
| Methodology Reviewer | Study design and feasibility; appropriate sampling, measures and analysis where relevant; qualitative interpretation, theoretical reasoning or reproducibility when appropriate. |
| Ethics Reviewer | The actual research setting: participants, data, consent, privacy, bias, integrity and proportionate risks. Do not force human-participant questions onto a study without participants. |
| Impact Reviewer | Contribution to knowledge as well as practical relevance. Basic or theoretical work need not demonstrate commercial benefits. |
| Critical Reviewer | Research gap, theoretical basis, claims, evidence, alternative explanations and limitations within the identified subject. |

Preserve internal role identifiers and the existing four-reviewer opening order. Proposal questions address planned work; completed-study questions examine reported evidence. A research profile must not invent missing methods or results.

## Concrete acceptance cases

- An education interview study should be questioned about recruitment, interpretation and credibility rather than automatically demanding experimental statistics.
- An engineering prototype with an experiment should connect measurement and evaluation claims to supplied implementation evidence.
- A theoretical mathematics paper should examine definitions, assumptions, reasoning and contribution without forcing participant consent or customer metrics.
- An interdisciplinary paper or two papers with conflicting approaches should expose uncertainty; do not quietly select one convenient discipline.
- A host correction that conflicts with the paper should remain an attributed host description, not proof of what the uploaded paper says.

The profile guides a practice perspective; the uploaded text remains the evidence for questions and citations. Do not announce fabricated disciplinary credentials or treat a valid citation as proof that the AI's interpretation is correct. Prefer direct questions, retaining the existing occasional grounded what-if policy, answer-aware reactions, language matching and same-question clarification intent.

## Existing implementation facts

- `backend/research_plan.py` returns ordered topics with reviewer assignments, validated references and gaps, plus map uncertainties and a budget suggestion. It currently has no discipline/study-approach profile.
- `backend/question_generator.py` centralizes reviewer focus/voice and distinguishes proposal, completed and inferred stage. Current Impact guidance emphasizes practical beneficiaries; the proposed change would also recognize contributions to knowledge.
- Research and mixed defenses use Methodology, Ethics, Impact and Critical perspectives. Code-only defenses have their own established roles and four-to-eight-turn policy.
- Planning uses one structured AI request and can stream validated draft topics. A profile should be additional validated data, not a new evaluator request or private reasoning display.
- Research question budgets, topic coverage and exact citations already have server validation. Their behavior remains a boundary for this proposed feature.

Read-only interface review also identified these implementation considerations for the later specification:

- Capture the profile with the map and research session, so question generation and coaching can reuse their existing context. Submission interpretation needs an explicit profile field because it currently receives stage/type without the research session context.
- Bind host confirmation to the current map identity. Per the confirmed policy, profile corrections require remapping and invalidate previous approval.
- Streamed topics are drafts. Do not present an inferred profile as confirmed before final response validation and host review.
- Keep the profile stable during a run and restore it from server snapshots. Restart currently reuses the approved map; specialization must remain bound to that map.
- Research stage, study approach and mapping progress are different concepts. The existing “Let AI infer” stage is not a persisted resolved classification; do not quietly overwrite it as part of discipline inference.
- Mirror confirmed settings in Streamlit's project fingerprint so changing them cannot reuse a stale map or session.
- Four opening reviewer turns remain mandatory today, even when no topic is assigned to a particular reviewer. The proposed prompts should make those perspectives appropriate to the work instead of inventing participants, experiments or practical beneficiaries.

## Planning completion

The user answered Q10 with “Matches—finish planning.” All feature choices from rounds 1–3 and the consolidated scope are confirmed. Existing-room compatibility, validation bounds and transport details can be specified using these policies without changing their meaning. The next workflow step is To Spec, followed by To Tickets and later implementation; no implementation has started.

## Agreed verification boundary

Use mocked mapping/generator/room tests for profile validation, uncertain classification, host-only correction, stale approval, reconnect, shared reviewer context and unchanged code-only rules. Test proposal/completed, qualitative/quantitative/theoretical/interdisciplinary and mixed paper/code cases. Include React profile controls and complete mocked two-client research and mixed defenses. Run the full offline Python and React suites and production build. Check desktop, portrait and landscape controls, citations, question readability and confirmation states before presenting a local preview. Review live conversations separately; mocked prompt assertions cannot establish disciplinary accuracy or natural dialogue quality.

Verify failed preparation retains uploads/corrections, retries cannot restore stale approval, old research maps require preparing a confirmed profile, and profile edits cannot mutate an active run. Confirm teammate read-only access, host-only confirmation, snapshot restoration, consistent Streamlit invalidation and the preservation of server deadlines, coverage and charges.

## Agreed local checkpoints

1. Profile and map review: structured profile output, validated source explanation, host correction/remapping/confirmation, shared snapshots and reconnect. Existing research plans lacking a confirmed profile must be prepared again before starting; do not invent a legacy classification. A failed map keeps files and corrections available for retry.
2. Reviewer adaptation: consistently carry the confirmed profile through questions, reactions, clarification, answer probes and coaching, including the Streamlit fallback. Verify source conflicts, uncertainty and subject-appropriate perspectives, then complete integrated local review.

Each checkpoint leaves the app runnable and records its verification in README.md and PROJECT_LOG.md. These checkpoints describe later implementation; the current request authorizes planning only.

## Completion criteria for later implementation

- A host can review a grounded profile, correct it, reprepare and confirm the current map/budget; guests can inspect but cannot alter it.
- Confirmed uncertainty permits a defense without invented methods, and source/host discrepancies remain clearly attributed.
- Multiple disciplines and approaches influence the appropriate topics while preserving reviewer identities and the four opening turns.
- Every dialogue and coaching path uses the same confirmed profile; reconnect, clarification and retry do not silently reclassify the work.
- Corrected or obsolete mapping results cannot enable Start or replace a newer profile. All displayed source explanations resolve from server-owned text.
- Agreed offline, mocked two-client and responsive checks pass, with live conversation evidence reported separately. A local preview is presented before publication.

## Delivery boundary

The interview is complete. Use this confirmed plan as input to the later implementation specification and tickets. Preserve pending reasoning/local-access changes and unrelated footprint research. No changes to pricing, provider/model, production authentication, timers, citation semantics, frozen `main` or the hosted service are authorized by this planning request.

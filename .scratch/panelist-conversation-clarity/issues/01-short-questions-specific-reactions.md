# 01 — Short questions and specific panelist reactions

**What to build:** defenders in code, research and mixed defenses receive one
concise main question and optional natural feedback that recognizes a specific
reason, correction or remaining gap in their actual explanation. Preserve the
current reviewer handoff, reaction moment and Streamlit's inline conversation.
This completes the first runnable local checkpoint.

**Blocked by:** None — can start immediately.

**Status:** ready-for-human

- [x] Shared conversation guidance prefers one short spoken main question, usually one sentence, while retaining necessary qualifications and meaningful uncertainty.
- [x] Source context remains available separately; valid longer questions are accepted without a new hard length/sentence rejection rule or weakened citation validation.
- [x] Reactions identify one actual reason, useful correction or material uncertainty rather than paraphrasing the answer, praising automatically or certifying the project/study.
- [x] Reactions remain optional, with no required acknowledgment prefix or quota, and retain the existing two-sentence/300-character bound. Empty reactions and opening introductions retain their existing behavior.
- [x] A normal transition remains attributed to the next reviewer, with matching speaking identity and the current 4–12-second reading interval before the full vote; vote, answer and reply durations are unchanged.
- [x] Clarification explains the same question; one important gap may receive an existing same-question probe; sufficient explanations and resolved probe replies are accepted without repeated challenges. No reaction adds another question or supplies the team's answer.
- [x] Direct questions remain the default, with occasional grounded hypothetical scenes and no forced consecutive scenarios. Conditional advice remains optional and is not credited as defender reasoning.
- [x] Distinct code/research role perspectives, study stage, confirmed research profile and host-description/source-evidence separation remain intact.
- [x] Explicit language preferences, including modern conversational Bisaya, retain existing precedence. Brief/code-only replies and timeouts do not spuriously switch language; missed and incomplete answers receive neutral context without invented content.
- [x] Existing generation and submission requests carry these refinements without a new evaluator, classifier or provider stage, changed response contracts, coverage rules or financial behavior.
- [x] At the agreed existing seams, mocked generation/context regressions and an authenticated room exchange verify exact citations, answer/probe retention, reaction attribution and unchanged progression. Shared Streamlit dialogue uses the same guidance.
- [x] Record the implementation's starting revision and safe nonsecret model/configuration information needed for the later same-source/answer live comparison. Preserve unrelated local work rather than silently including it.
- [x] The app remains runnable; update the README and project handoff with this checkpoint's changes, checks and remaining final-closing/live-review work. Mocked evidence must not be reported as dialogue-quality proof.

## Context and handoff

Originating specification: **Panelist conversation clarity and final closing**,
confirmed 2026-10-15, including its 44 user stories and agreed test boundaries.
Use the project's distinctions between panelist reaction, clarification, answer
probe, defense turn and research coverage. All substantive dialogue remains
generated; interview examples are not embedded scripts.

Keep work on feature/question-first-room and retain frozen main/current hosted
behavior. This ticket authorizes no remote push/deployment. Do not implement the
final closing here; it is ticket 02. Full integrated/responsive/live handoff is
ticket 03, but relevant safety/contract checks belong with this slice.

## Comments

2026-10-15: User approved the three-ticket breakdown and dependency chain.

2026-10-15: Implemented checkpoint 1 locally against approved starting revision
9314379. Shared prompt refinement and three new provider-contract/authenticated
two-client tests; no schemas, timers, budgets, charges or frontend code changed.
Full working-tree Python gate: 543 tests; isolated selected artifact: 535;
React: 275 tests and production build. External providers were mocked. Independent
Standards and Spec reviews of immutable candidate 8468a29 report zero findings.
Ready for human conversation review; live comparison/visual integrated handoff
remains ticket 03, and final closing remains ticket 02. No push/deploy or user
visual/native-language approval claimed; unrelated pending edits preserved.

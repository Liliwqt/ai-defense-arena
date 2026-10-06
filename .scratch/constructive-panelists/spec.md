# Constructive suggestions in research defenses

Status: ready-for-human
Created: 2026-10-07

Implementation: local guidance and regression checks are complete. The user's Implement request authorized this checkpoint using the synthesized defaults below. Human preview/conversation review and separate live-AI quality checks remain pending; see [review evidence](../../docs/CONSTRUCTIVE_PANELIST_REVIEW.md). No push or deployment is authorized by this checkpoint.

Basis: [panelist-questioning research](../../docs/PANELIST_QUESTIONING_RESEARCH.md) and [discovery record](discovery.md).

The user requested specification synthesis before answering the three discovery choices. This spec uses the recommended defaults as explicit assumptions: selective advice during research and mixed defenses, including conditional alternatives not named in uploads. These are not recorded as separately approved interview answers. The user confirmed the proposed test boundaries on 2026-10-07. This specification does not authorize publication or deployment.

## Problem Statement

Students want a practice research defense that helps them understand how to improve their study. The panelists already ask grounded questions and provide final coaching, but do not have an explicit policy for offering a useful methodological alternative during the conversation. An examiner can sound repetitive or overly challenging when it keeps asking about a limitation without helping the team understand a possible improvement.

Advice can also undermine the defense if it replaces the student's explanation, assumes one method is universally superior, invents research findings, or is later counted as something the team demonstrated. Students need constructive suggestions that respect their actual research objectives, constraints, and decisions.

## Solution

For Research paper and Research + code defenses, let panelists occasionally offer a brief, conditional improvement after hearing the team's reasoning. First explore the choice; when an important unresolved limitation or tradeoff warrants advice, explain one possible alternative and its relevant benefit or constraint, then ask one focused question. Accept a sufficient explanation and move forward rather than trying to force adoption of the panelist's preference.

Use the current panelist lead-in and existing final coaching report. Keep the grounded question separate and prominent, retain its exact citation, and preserve the existing defense-turn flow. No extra advice turn, consultation action, timer, or AI request is added. Code-only defenses retain their current questioning behavior.

For this feature, a **panelist suggestion** means an optional recommendation offered by a reviewer to improve the team's research reasoning or approach. It is examiner advice, not a team answer, a finding, a verified source claim, or a clarification of the question. This term is proposed here; no glossary agreement is implied.

## User Stories

1. As a research defender, I want the panelist to understand my stated objective before proposing an alternative, so that its advice fits the study I am defending.
2. As a research defender, I want to explain why I chose an approach before hearing replacement advice, so that my reasoning and constraints receive a fair hearing.
3. As a research defender, I want occasional suggestions rather than advice after every answer, so that the session still feels like a defense conversation.
4. As a research defender, I want each suggestion to address one meaningful limitation or tradeoff, so that I can understand what it is meant to improve.
5. As a research defender, I want alternatives presented conditionally, so that I am not told there is one universally correct method.
6. As a research defender, I want a short explanation of an alternative's benefit or practical constraint, so that I can judge its suitability.
7. As a research defender, I want suggestions to respect recruitment, access, time, and resource constraints I have actually described, so that the advice is realistic.
8. As a research defender, I want unsupported assumptions identified as uncertain, so that the panelist does not silently invent my circumstances.
9. As a research defender, I want the panelist to consider narrowing a claim or scope when appropriate, so that improvement does not always mean adding more work.
10. As a research defender, I want to justify retaining my current approach, so that a reasonable decision is not treated as wrong merely because I declined advice.
11. As a research defender, I want a sufficient explanation accepted, so that suggestions do not create repetitive follow-ups.
12. As a research defender, I want the question to remain one focused request, so that a suggestion does not turn it into a checklist of tasks.
13. As a research defender, I want advice and the question presented separately, so that I can identify what I am expected to answer.
14. As a research defender, I want the original exact citation retained, so that I can inspect the uploaded premise behind the question.
15. As a research defender, I want a suggested alternative distinguished from the cited paper's contents, so that the citation does not appear to verify advice absent from the paper.
16. As a research defender, I want useful general alternatives allowed even when my paper does not name them, so that the panelist can help me consider options beyond my draft.
17. As a research defender, I want uncertainty acknowledged when the panelist cannot justify an alternative, so that it does not invent a named study, numerical claim, or authoritative requirement.
18. As a proposal defender, I want advice about planned methods, feasibility, and safeguards, so that panelists do not pretend I already collected results.
19. As a completed-study defender, I want advice about limitations, justified reanalysis, or future work, so that the panelist does not pretend I can retroactively change completed recruitment or collected data.
20. As a defender whose research stage is unclear, I want the panelist to clarify the stage before assuming results, so that its advice remains appropriate.
21. As a mixed-defense participant, I want suggestions to connect documented research claims with actual implementation choices, so that paper and code are examined together.
22. As a mixed-defense participant, I want unsupported software features identified as possibilities rather than existing capabilities, so that recommendations do not become fabricated implementation claims.
23. As a defender questioned by the Methodology Reviewer, I want advice relevant to design, sampling, measurement, analysis, or feasibility, so that it reflects that reviewer's specialty.
24. As a defender questioned by the Ethics Reviewer, I want advice about relevant participant safeguards and research integrity, so that the panelist helps without inventing a violation.
25. As a defender questioned by the Impact Reviewer, I want advice about beneficiaries, practical use, or impact assessment, so that recommendations relate to the study's intended value.
26. As a defender questioned by the Critical Reviewer, I want advice that explores assumptions, evidence, limitations, or alternative explanations, so that challenges remain respectful and useful.
27. As a defender changing reviewers, I want any reaction correctly attributed to the reviewer currently speaking, so that the conversation does not fabricate another panelist's agreement.
28. As a defender, I want advice to follow the existing conversational language, so that an English, Filipino, or Taglish conversation remains understandable.
29. As a defender asking for clarification, I want the panelist to explain the existing question without supplying my defense answer, so that clarification still supports practice.
30. As a defender who misses a turn, I want the panelist to acknowledge the missing answer neutrally, so that it does not claim to have learned my reasoning.
31. As a chosen defender, I want the existing vote and answer windows preserved, so that receiving advice does not silently alter the time available.
32. As a teammate, I want the same published dialogue on every client, so that everyone can discuss the same question and suggestion.
33. As a reconnecting teammate, I want previous advice restored from room state, so that reconnecting does not generate new or contradictory recommendations.
34. As a teammate reviewing the transcript, I want panelist advice kept distinct from accepted team answers, so that the record accurately attributes each statement.
35. As a teammate downloading the summary, I want suggestions retained with the appropriate panelist turn, so that I can review the conversation later.
36. As a team receiving coaching, I want suggested improvements tied to actual answers or unresolved topics, so that the report gives usable next steps.
37. As a team receiving coaching, I want strengths based only on what we explained, so that advice from the panel is not credited as our own reasoning.
38. As a research host, I want topic coverage based on accepted team explanations rather than panelist suggestions, so that an addressed topic retains its current meaning.
39. As a host retrying failed generation, I want the submitted answer retained and no duplicate turn, so that advice generation does not weaken recovery behavior.
40. As a team finishing or ending a defense, I want remaining advice in the existing coaching report, so that completion does not manufacture another question beyond the approved budget.
41. As a Streamlit research defender, I want the same panelist advice policy, so that the fallback conversation stays consistent with the multiplayer app.
42. As a code-only defender, I want my existing panelist flow retained, so that this research-focused change does not silently redesign code defenses.
43. As a phone or WebView participant, I want bounded advice readable with the question and source excerpt, so that it does not consume the space needed to understand the question.
44. As a project owner, I want mocked reliability checks and a separate live dialogue review, so that passing structural tests is not mistaken for evidence of natural or correct advice.

## Implementation Decisions

- Apply the policy only to research and mixed defense modes through shared, mode-aware research guidance. Preserve the existing code-only role instructions and question policy. Do not add a new host toggle in this checkpoint.
- Generate substantive advice in the existing structured question-generation request. Use the current lead-in field: zero to two short sentences and at most 300 characters, containing at most one proposed improvement. A reaction and suggestion together share that limit. When meaningful advice cannot fit, shorten it or defer it to coaching; do not expand the field or overflow the question card.
- Retain an empty lead-in for the opening question. During later turns, base advice on an actual accepted answer and a relevant source-grounded issue. An empty lead-in remains valid. Do not produce a suggestion merely to fill a turn or supply advice as a reaction to a nonexistent timed-out answer.
- Eligibility is semantic guidance: a material unresolved limitation, mismatch, unsupported claim, or important tradeoff makes advice useful. Avoid automatic replacement advice and repetitive suggestions on consecutive turns. If the team gives a sufficient explanation, advance even when it retains its original approach. This is a prompt policy, not a new deterministic scoring system or suggestion quota.
- Prioritize examining the team's reasoning before proposing an alternative. A suggestion names one option and makes its possible benefit, condition, or cost clear. Never assert that the examiner's preferred method is inherently better. If source and answer provide too little context, ask about the missing decision rather than confidently prescribing a solution.
- The next speaking reviewer owns its lead-in, even when reacting to another reviewer's previous question. Keep current role voices and specialties. New questions address the team because the chosen defender is selected after publication. Use server-owned speaker names only when attribution adds meaning.
- Alternatives absent from uploads are permitted as general, conditional advice. Do not claim that the paper contains them, that the exact citation validates their effectiveness, or that the team already implemented them. Do not fabricate literature, links, statistics, legal requirements, findings, or facts about figures unavailable through accepted text. External literature search and reference verification are not added.
- Keep one main question separate from advice. A suggestion is a brief statement, not an extra question, command, or request to complete several tasks. The question continues targeting an allowed research topic and requiring a validated citation. Advice must not introduce an unrelated replacement project or expand the research objectives without acknowledging that this would be a scope change.
- Preserve stage-aware guidance. For proposals, discuss planned feasibility and safeguards. For completed studies, distinguish current findings from possible future changes and condition any reanalysis on data that actually exists. If the stage is unclear, clarify it instead of inventing results.
- Preserve explicit language-request precedence and meaningful-answer language adaptation. Keep filenames, identifiers, and exact source text unchanged. Suggestions and acknowledgments are conversational prose; uploaded documents, answers, names, and prior AI dialogue remain data rather than instructions. Private team chat stays excluded.
- Keep clarification intent unchanged. Requests to simplify, translate, repeat, explain terminology, or illustrate the current question receive explanation of that question without advancing the turn, introducing a new issue, or supplying the team's answer. Do not reinterpret the existing clarification action as a new research-advice consultation endpoint. Broader advice-on-request behavior is outside this checkpoint.
- Preserve the current research policy: the approved question maximum, reviewer participation, immediate-follow-up rules, topic selection, assessment validation, and completion reasons. Recommendations do not count as defender evidence or make a topic addressed. A later accepted team explanation may engage with advice, but merely receiving advice is never sufficient coverage.
- Reuse current lead-in persistence, shared transcript serialization, snapshots, reconnect, question-card display, transcript, summary export, and Streamlit presentation. Introduce no new AI response fields, WebSocket actions, database tables, or independent suggestion history. Label conditional advice explicitly in its wording; do not require a new visual badge or infer suggestion classifications in the browser.
- Keep the existing 15-second vote and 120-second answer window for each generated question, including follow-ups. Advice adds neither a turn nor additional time. Retain current interpretation-time handling and chosen-defender authorization.
- Preserve atomic publication and retry: validate the full move, citation, lead-in, topic, and assessment before applying it. Invalid output retains the accepted answer and prior coverage for host retry. Reconnect displays published dialogue without new generation. Stale results remain ignored by existing run ownership rules.
- Completion carries no extra question or dialogue. Final recommendations belong in the existing coaching improvements and next step, with valid references to the actual transcript. Coaching must distinguish panelist advice from what the team said, maintain factual treatment of timeouts and early endings, and leave strengths empty when no answers exist. An empty session retains its current factual summary behavior.
- No additional paid model calls are introduced. Research preparation, question budgets, access, charging, account ownership, and payment behavior remain unchanged. Build and review locally on the existing feature branch; publication requires a later request.

## Testing Decisions

- The user confirmed these boundaries on 2026-10-07: existing mocked question-generation and two-client room tests, React display tests, and a separate live conversation review. Prefer these established boundaries rather than a new suggestion service, evaluator, or database seam.
- Good offline tests observe externally visible output, validated state transitions, snapshots, and rendered/exported dialogue. Avoid full prompt snapshots, tests of private helpers, or tests claiming that a mocked response proves recommendation quality. Small request-contract checks may verify mode gating, actual answer context, and instruction/data separation.
- At the existing question-generation boundary, mock model output and verify a bounded suggestion-bearing lead-in retains the separate question and exact citation. Cover empty introductions, length/sentence rejection, invalid citations, research/mixed mode guidance, accepted answer context, proposal/completed handling, timeout context, completion without dialogue, and unchanged code-only behavior.
- At the existing defense-session and room boundary, run mocked two-client research and mixed defenses. Cover useful immediate follow-ups, sufficient-answer advancement, clarification without another vote or question, chosen-defender answers, deadline/timeout progression, generation failure and host retry without duplication, reconnect, early ending, and exact budget stopping. Include a research defense exceeding eight turns and paper/code citation changes in mixed mode.
- Verify that assessment and coaching receive the panelist lead-in as dialogue while retaining the original team answer as the evidence source. A suggestion alone cannot become an answer, an addressed-topic rationale, or a claimed strength. Mocked tests verify supplied context and validation boundaries; semantic fidelity also needs live inspection.
- At the existing React whole-room display boundary, exercise suggestions in the question card, transcript, and downloaded summary, with bounded long text on desktop, portrait phones, and landscape phones. Check reading order, panelist attribution, source text, internal scrolling, keyboard access, and no page-level horizontal overflow. Both clients must display the same published text.
- Prior art includes the existing question-generator, adaptive research/session, timed-turn, room-server and coaching tests, plus React question-card, transcript, defense-summary, and coaching tests. Extend those suites rather than inventing separate low-level tests for wording alone. Streamlit reuses the same generator/session policy; inspect its rendered research dialogue separately where adapter behavior differs.
- Run the complete Python suite with AI, Google, and payment providers mocked, the React suite, and the production build. Preserve unrelated local account/upload/payment edits and screenshot deletions when selecting changes.
- Separately inspect live synthetic proposal, completed-study, and mixed conversations with sufficient, vague, contradictory, constrained, and Taglish answers. Check whether advice identifies a real point, respects constraints, offers a defensible option with uncertainty, varies naturally, and accepts a reasonable refusal. Check that a final answer or budget exhaustion leads to coaching rather than another question. This is human-reviewed evidence, not an automated proof of research correctness.
- Record mocked, browser, live-AI, hosted, and physical-device evidence separately. A local live check requires a configured key and makes model calls; it is not part of the offline suite. Present the local conversation and preview before any later publication decision.

## Out of Scope

- QR top-up implementation, its pending tickets and review findings, real-money payments, pricing, credits, vouchers, or account changes.
- Code-only prompt redesign or changing its existing four-to-eight-turn structure.
- A separate research advisor, advice-on-request action, suggestion-only turns, new timers, automatic answer writing, or rewriting the paper for the team.
- External literature retrieval, fabricated references, automatically selecting an optimal research method, or guaranteeing ethics/regulatory compliance.
- New response schemas, suggestion persistence outside existing turns, report sections, scores, rubrics, or mandatory adoption of examiner advice.
- Voice, panel-to-panel discussion, extra reviewers, new native mobile screens, OCR, figure interpretation, or a room redesign.
- Production deployment, changes to frozen main, or claiming institutional approval of an AI-generated recommendation.

## Further Notes

- Research guidance describes institutional expectations, not proof that every human examiner behaves identically. Degree level, discipline, and institution affect the appropriate challenge and feedback; this feature does not copy a doctoral marking system into all student defenses.
- This spec synthesizes the requested behavior without another discovery interview. Its timing, scope, and alternative-source defaults remain explicitly assumption-based. The subsequent To Spec request supersedes the unfinished interview; it is not a claim that the user answered those questions or confirmed the earlier shared-understanding gate.
- General suggestions are not newly verified external facts. An exact grounded citation establishes where the question premise originated, not whether an alternative method is suitable. Respectful conditional advice still requires live quality inspection and the student's judgment.
- Use one focused implementation checkpoint if this remains guidance plus reuse of existing dialogue plumbing. A separate ticket breakdown is useful only if implementation discovery reveals independent deliverables; no additional feature scope is implied here.

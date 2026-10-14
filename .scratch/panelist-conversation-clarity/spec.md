# Panelist conversation clarity and final closing

Status: ready-for-agent

Planning and test boundaries confirmed by the user on 2026-10-15.
Local specification only; implementation and remote publication require later requests.

## Problem Statement

Defenders need questions they can understand on first hearing and brief reactions
that show the panelist understood their reasoning. Existing instructions already
ask for natural, concise dialogue, but actual questions can contain too much
background or several qualifications, and reactions can leave unclear which part
of an answer was resolved. The final resolved answer currently receives no
standalone panelist reaction because ordinary reactions belong to the next
question and a completed defense has no next question.

The user wants clearer spoken dialogue without grading each response, supplying
answers during questioning, adding repetitive praise or changing the defense's
rules and price. Public comparison informed this request; it was not a controlled
comparison of identical papers, models or settings.

## Solution

Across Code project, Research paper and Research + code defenses, prefer one
short, natural main question, usually a single sentence, while retaining detail
needed for accurate interpretation. Use optional brief reactions to identify a
specific reason, correction or unresolved issue in actual defender dialogue.
Keep the current next-reviewer handoff and reaction reading interval.

When coaching succeeds, allow the last reviewer to give an optional brief closing
generated within that same coaching request. Present it before the room's coaching
report, retain it in the transcript, and resume its remaining interval after
reconnect. Empty or unusable optional closing text must not prevent valid coaching.
Settle the successful run before that presentation interval; it is not another
defense turn. Streamlit shares the wording and closing but displays it inline.

Deliver two runnable local checkpoints, then present the integrated preview and
verification evidence before any separately requested publication.

## User Stories

1. As a defender, I want one clear main question, so that I know what reasoning the panelist is asking me to explain.
2. As a defender, I want necessary qualifications retained, so that shorter wording does not misrepresent my study or code.
3. As a defender, I want source context visible separately, so that I can inspect the evidence without parsing a long spoken preamble.
4. As a defender, I want an opening question without a fabricated reaction, so that the panelist does not pretend I have already answered.
5. As a defender, I want reactions to refer to a specific reason or correction I actually gave, so that I can tell the panelist listened.
6. As a defender, I want the panelist to identify a remaining gap only when useful, so that feedback adds meaning rather than repeating my answer.
7. As a defender, I want empty reactions allowed, so that the conversation does not require filler after every answer.
8. As a defender, I want encouragement tied to an actual explanation, so that praise does not imply the whole study is correct.
9. As a defender, I want calm concern grounded in evidence, so that an omission is not treated as proof that work was never planned or done.
10. As a defender, I want the panelist to distinguish my claims from the uploaded evidence, so that assertions are not certified as findings.
11. As a defender, I want a sufficient explanation accepted, so that resolved issues do not lead to repetitive challenges.
12. As a defender, I want one material gap probed, so that I can add needed detail without starting another defense turn.
13. As a defender, I want my probe reply considered with my original answer, so that feedback does not ignore my correction or additional reasoning.
14. As a defender, I want clarification to explain the existing question, so that confusion is not graded as a weak substantive answer.
15. As a defender, I want clarification to preserve question intent and citation, so that a simpler explanation does not silently change the task.
16. As a defender, I want optional advice stated conditionally, so that I can weigh benefits and constraints without being forced to agree.
17. As a defender, I want suggestions excluded from my credited reasoning, so that the panelist's own advice is not counted as my achievement.
18. As a defender, I want direct questions to remain the default, so that hypothetical scenes do not dominate the defense.
19. As a defender, I want clearly hypothetical examples, so that imagined consequences are not presented as observed results.
20. As a defender, I want explicit language preferences respected, so that questions and feedback remain understandable in modern Bisaya or another requested language.
21. As a defender, I want brief, code-only or missed answers to preserve the existing language preference, so that the conversation does not switch languages unexpectedly.
22. As a defender, I want timeouts acknowledged neutrally, so that the panelist does not invent an answer or speculate about my motives.
23. As a teammate, I want the displayed speaking reviewer to match the reaction's attribution, so that I know who is responding.
24. As a teammate, I want the next reviewer to make a useful connection when changing specialties, so that the handoff feels coherent without a second speaking moment.
25. As a chosen defender, I want the full existing voting and answering windows preserved, so that reaction reading does not take away my response time.
26. As a defender, I want an optional closing from the last reviewer, so that the final explanation is acknowledged before coaching.
27. As a defender, I want the closing to arrive only after coaching generation finishes, so that the interface does not imply an immediate response it cannot provide.
28. As a defender, I want the closing to use the actual final resolved exchange, so that a missed or unfinished answer is not praised as successful.
29. As a defender, I want the closing to lead to coaching rather than another vote, so that completion is clear.
30. As a reconnecting defender, I want the remaining closing interval restored without replay, so that returning does not restart the presentation.
31. As a host, I want valid coaching retained when its optional closing is empty or invalid, so that a decorative field cannot block the report.
32. As a host, I want failed coaching to use existing retry and recovery, so that accepted answers and financial protections remain intact.
33. As a host, I want successful completion settled before the closing interval, so that a presentation delay cannot keep a paid run unfinished.
34. As a host, I want restarting or closing the room to invalidate old closing work, so that obsolete results do not affect another run.
35. As a host, I want ending an empty defense to retain a factual summary without AI-generated praise, so that the system does not invent discussion.
36. As a teammate, I want reactions and the closing retained in transcript exports, so that the shared record preserves what the panel said.
37. As a research defender, I want coverage to remain discussion coverage, so that a conversational acknowledgment is not proof that a topic or study is correct.
38. As a code defender, I want existing code-only progression retained, so that a dialogue refinement does not introduce research-budget rules.
39. As a Streamlit user, I want the same concise dialogue and optional closing, so that the fallback retains equivalent conversational content.
40. As a mobile defender, I want readable closing content and reachable existing controls, so that feedback does not clip the room or disrupt keyboard use.
41. As a maintainer, I want existing report callers and older snapshots supported, so that additive closing data does not break compatible clients or tests.
42. As an operator, I want no additional evaluator request, so that clearer feedback does not introduce another AI stage per answer.
43. As the project owner, I want mocked functionality and live quality documented separately, so that passing tests do not overstate how the panelist sounds.
44. As the project owner, I want local checkpoints and previews before publication, so that I can review the complete experience while the live service remains unchanged.

## Implementation Decisions

1. Refine shared conversation guidance used by questions, reactions, clarification
   and probes across all defense types. Preserve subject-aware research guidance,
   confirmed-profile/source provenance and stage distinctions. Do not create a
   separate question bank, scripted reactions or a per-answer evaluator.
2. Prefer one brief spoken question, usually one sentence, with concrete project
   terms. Necessary detail is permitted; avoid stacked tasks and checklist-style
   phrasing. Keep needed context in the source display or useful brief reaction
   where appropriate. Do not add a hard question-length rejection rule or remove
   meaningful uncertainty to meet a wording target.
3. Keep reactions optional and bounded to two sentences and 300 characters. They
   should identify one consequential point from actual dialogue; they are neither
   grades nor evidence that a study is correct. Useful acknowledgments remain
   varied and language-appropriate without a required prefix or praise quota.
4. Preserve opening, same-question clarification, probe/reply, sufficient-answer
   acceptance and follow-up rules. Do not turn a reaction into another question or
   use a short answer alone as reason to probe. Do not repeat an issue resolved by
   a probe reply. Conditional advice retains its existing grounding and bounds;
   panelist advice is not credited as defender reasoning.
5. Preserve direct-question preference, occasional grounded hypothetical scenes,
   no consecutive forced scenarios, distinct role voices, modern Bisaya guidance
   and existing explicit/substantive-answer language precedence. Neutral timeout
   and incomplete-reply context must never imply a defender answered.
6. Ordinary reactions remain attributed to the next question's reviewer and use
   the existing server-owned 4–12-second reading interval. Empty reactions skip
   it. The full vote starts afterward; existing answer and reply timers stay
   unchanged. No separate previous-reviewer handoff is added.
7. Extend the existing coaching response/report with optional closing text and a
   compatibility default of no closing. Existing callers and reports without that
   field remain valid. The closing shares the two-sentence/300-character bound;
   existing core coaching validation and reference rules remain in force.
8. Generate the optional closing in the existing coaching request using actual
   transcript context, including probe replies and current language. Derive its
   reviewer identity from server-owned final resolved-turn data, rather than an
   AI-supplied identity or client claim. Early ending must not convert an active
   unanswered question into a resolved answer. Empty history retains the current
   factual no-AI summary with no closing.
9. Separate optional closing validation from valid core coaching. Normalize and
   accept usable closing text; omit empty or invalid optional text without losing
   the valid report or scheduling another request. Missing legacy fields are
   treated as empty. A wholly unparseable response, invalid core report or failed
   provider call still follows existing coaching failure/recovery; never fabricate
   a report to conceal that failure.
10. Keep the defense logically complete while presenting a closing. At successful
    coaching publication, finalize existing durable run settlement exactly once,
    retain the ready report and record server-owned terminal presentation timing.
    The display interval is not a live gameplay phase, additional turn, unresolved
    service error or new charge. Do not postpone settlement or extend room lifetime
    because the closing is being read.
11. Add compatible closing data, attribution and deadline metadata to existing
    room snapshots and client models. No new WebSocket action or client-owned
    timer authority is required. Use the room coordinator's existing publication,
    lifecycle and stale-work protection; a restart, closure or changed generation
    must invalidate obsolete closing work. Reconnect restores the same deadline
    without another AI call or full-interval replay.
12. During the valid remaining interval, the main room presents the last reviewer
    as speaking and uses completion-to-coaching wording. Afterward, reveal normal
    coaching/completion content; never promise a next question or vote. An empty
    closing proceeds directly to coaching. Keep existing controls and source/
    transcript access usable; transcript retains the report and valid closing.
13. Preserve the last closing in transcript/export separately from defense turns
    and from ordinary next-question reactions. It consumes no question budget,
    adds no answer and changes no research coverage assessment. Coaching must
    retain actual-turn references and topic titles for uncovered topics.
14. Mirror shared guidance, report compatibility and optional final closing in
    Streamlit while retaining its existing single-browser, inline presentation.
    Do not emulate multiplayer voting or add an artificial timed transition to
    the fallback.
15. Preserve exact citations, speaker attribution, private-team-chat exclusion,
    account authorization, room ownership, generation retries, deadlines, question
    budgets, payment/credit-return policies and AI admission limits. No extra
    logical provider stage is added; ordinary existing retries may still occur,
    and provider token cost or latency is not guaranteed to decrease.
16. Deliver two runnable local checkpoints: shared question/reaction guidance and
    regressions first; optional final closing, compatible presentation/fallback,
    integration and review evidence second. Keep unrelated local changes separate.

## Testing Decisions

1. The user explicitly confirmed the test boundaries on 2026-10-15: authenticated
   room HTTP/WebSocket flows with AI/payment providers mocked and a controlled
   clock; existing question-generation/coaching contracts and Streamlit checks;
   whole-room React/browser checks. These supplement the earlier agreed full
   suites/build, integration and separate live review. Prefer these existing high
   boundaries over a new harness or tests tied to helper structure.
2. Good automated tests assert published state, accepted answers, valid citations,
   transcript content, user actions, deadlines, once-only settlement and report
   compatibility. Mocked dialogue demonstrates plumbing, not natural wording or
   intelligence. Avoid arbitrary exact-string checks for free-form generated
   prose; narrowly inspect request context where the mock boundary cannot measure
   whether the model obeyed it.
3. Prior art includes the existing conversation-context and clarification tests,
   parsed fake AI clients, timed-turn/fake-clock room tests, coordinated coaching
   failure/stale-result tests, authenticated adaptive two-client twelve-question
   integration flows, Streamlit AppTest, and room presentation/question/coaching/
   transcript React tests. Extend these seams without duplicating implementation.
4. Verify code/research/mixed requests preserve role perspective, evidence versus
   claims, language chronology, empty openings/reactions, resolved probe context,
   conditional advice and no new provider stage. Verify valid longer questions
   remain accepted with unchanged exact citations.
5. Verify legacy reports/callers and snapshots without closing data; empty,
   whitespace, oversized, too-many-sentence and invalid-type optional closing
   data with otherwise valid reports; genuine core-report/provider failures; valid
   attribution from server history; no-resolved-turn and timeout/early-ending
   context. Isolate optional-field failures without weakening core validation.
6. Verify terminal interval bounds, no new vote/answer clock, ready report and
   financial settlement before display, reconnect midway/after the interval,
   repeated ready snapshots without replay, coaching retry without duplicate
   closing/charge, and stale results after ending/restarting/closing. Preserve
   existing coaching-error credit-return and service-interruption protections.
7. Complete mocked two-client code and twelve-question research/mixed defenses
   covering voting, adequate/vague/contradictory answer outcomes, clarification,
   probe/reply, timeout, normal/budget/coverage/host endings, next-question retry,
   reconnect, exact transcript/citations, coverage gaps and coaching/closing.
8. Check whole-room React behavior plus local desktop, portrait and landscape
   browser previews for readable content, correct speaking reviewer, completion
   wording, timing, keyboard focus, transcript/export and controls without clipped
   content or horizontal overflow. Keep the existing layout and phone tabs.
9. Run the full Python and React suites and production build. Record provider
   mocks and check names explicitly. Reuse existing financial regression checks
   for unchanged once-only charging, completion and returns.
10. Separately review live before/after conversations with the same synthetic
    sources, defender answers and safely recorded model/configuration. Cover code,
    empirical/theoretical research, mixed integration and English/modern Bisaya;
    inspect strong, vague, contradictory and clarification answers, meaningful
    reactions, preservation of qualifications and sensible progression. Evaluate
    final closing and coaching too. Do not use secrets/private papers as evidence
    or claim a controlled model benchmark from unmatched historical samples.
11. Present local previews/screenshots and record implementation/checkpoint
    evidence in the project handoff log and README. Native-speaker user review,
    hosted behavior, external-provider checks and installed Android/iOS checks
    remain separate claims. Missing live credentials must be recorded rather than
    represented as a passed live check.

## Out of Scope

- Numeric scores, per-answer rubrics, model answers during questioning or a new
  live answer-evaluation product.
- A separate AI feedback request, new question-generation stage, scripted
  substantive dialogue or guaranteed lower token use/latency.
- Strict question-length rejection, semantic correctness guarantees or universal
  claims of human examiner equivalence.
- Changes to role count, code-only progression, research mapping/profile policy,
  coverage definitions, question budgets, voting/answer/reply durations, probe
  limits, citation validation, prices or payment/refund/storage architecture.
- Broader layout redesign, native-app rebuild, deployment or changes to frozen
  main or the live feature service.
- Incorporating unrelated reasoning settings, local authentication bypass tools,
  footprint research or payment work into this feature.

## Further Notes

- Originating plan: [confirmed conversation clarity plan](../../docs/PANELIST_CONVERSATION_CLARITY_PLAN.md).
- Domain terms distinguish panelist reaction, clarification, answer probe,
  defense turn, coaching, research coverage and credit return.
- Existing financial decisions require coaching failure to remain an unresolved
  service outcome eligible for established recovery, while successful coaching
  completes the run. A closing presentation cannot reverse that distinction.
- The confirmed interview settles Q1–Q11; no further product interview is needed
  to implement this scope. New bugs or required scope changes should be recorded
  separately rather than folded silently into the refinement.
- Local tracker publication means this Markdown specification is ready for
  ticketing. It does not authorize implementation, commits, pushes or deployment.

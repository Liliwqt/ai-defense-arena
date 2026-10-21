# Ticket 06 — independent implementation check

Date: 2026-10-22. User-approved baseline: `4b25a6f`.
Verdict: **incomplete; corrections required before completion or publication**.

The five-file uncommitted candidate is frozen under `.local/turn06-review/`.
`review.patch` compares each scoped file against the baseline; `manifest.json`
identifies exact hashes. Older budget diagnostics, reasoning, local-testing,
QR and planning changes are excluded. There are no commits after the baseline.
The implementation ticket still has eight unchecked criteria and ready-for-agent
status; its existing implementation-session claim is not treated as completed.
This review changes no runtime code, canonical tests or ticket criteria.

## Standards

Independent Standards review: **0 documented hard violations; 3 nonblocking
judgement-call smells**. Runtime/test paths, imports and content-free telemetry
follow the documented conventions.

1. Possible duplicated passage rendering in `focused_evidence.py:93` and `:150`.
   A shared private window renderer could keep source-location formatting aligned.
2. Possible duplicated reviewer dispatch in `openrouter_questions.py:506` and
   `:527`. Initial and expanded writing repeat model/schema/reasoning/limit policy.
3. Possible speculative retained state: `FocusedEvidence.files` is stored but
   never read; the accepted-source lookup already retains the needed file objects.

Standards total: **0 hard / 3 optional findings**. The most consequential optional
concern is writer-dispatch duplication, which could allow policy drift later.

## Spec

Independent Spec review: **6 findings; no scope creep**.

1. **P1 — Focused policy misses answer, clarification and probe review.** Ticket:
   “Use the focused policy on all migrated interactive paths.”
   `ReviewerInteractionClient.parse` forwards its incoming messages unchanged
   (`backend/openrouter_questions.py:302`), and shared interpretation still builds
   the complete source (`backend/question_generator.py:323`). Only
   `research_move` builds the focused view. Root's actual funded-adapter synthetic
   capture confirms a CombinedSubmissionDraft request includes an unrelated source
   sentinel and no focused-evidence section. The principal combined stage retains
   the large payload this ticket was intended to remove.

2. **P1 — Focused prompts omit numeric source identities.** Ticket: “Preserve
   original identities/locations.” `_study`, reference windows and expansion emit
   `FILE filename` headers (`backend/focused_evidence.py:95`, `:118`, `:152`),
   but QuestionDraft requires numeric `source_file` and reviewer guidance refers
   to numbered FILE IDs. Two-document reproduction retains accepted IDs 1 and 2
   internally while rendering no numbered headers. Mocks supplying the correct ID
   conceal the missing mapping, particularly for mixed/cross-document citations.

3. **P1 — No explicit insufficient-evidence lookup contract.** Ticket: “Support
   finite explicit broader lookup for insufficient context.” Only an invalid
   citation from `_ground_question` triggers expansion
   (`backend/openrouter_questions.py:516`). Neither the planner nor reviewer can
   request additional evidence through a validated insufficiency response.
   Coverage/completion planning cannot expand at all; a valid citation paired with
   an incomplete interpretation never triggers lookup. The sole provider test
   forces a nonexistent line 999 rather than requesting unavailable evidence.

4. **P2 — Relevant-topic selection uses the wrong key and can drop current
   evidence.** Ticket requires “exact relevant/neighboring passages.”
   `_excerpts` reads option `id` (`backend/focused_evidence.py:168`); actual options
   contain `topic_id`. All map-topic references then precede the current citation.
   In a synthetic 16-topic reproduction, the 14-window cap drops both selected
   topic 16's passage and the current citation, while earlier topics consume the
   capacity. Prioritize the selected/current exact evidence before optional topics.

5. **P2 — Context/lookup bounds lack the required selection evidence and a start
   regression remains.** Ticket asks to “Measure/select context and lookup bounds
   using representative fixtures,” and recalculate actual-context work bounds.
   The limits at `backend/focused_evidence.py:15` are unexplained constants; no
   size/coverage/lookup-overhead comparison supports them. Only the evidence-policy
   version is captured, not the individual numeric limits. Lookup telemetry has
   byte/count fields but no separate expansion duration. The isolated existing
   19-question-start test now fails at the default $5 ceiling after adding a
   full-context writer bound per question. This is an admission regression to
   assess and fix/test, not evidence of an actual $5 provider bill.

6. **P2 — Required lookup-aware integration coverage is missing.** Ticket requires
   cross-section/document, qualitative/theoretical, ambiguous-profile, changed
   preparation and complete-room checks. The new tests consist of six helper
   cases and one writer expansion case; mixed eligibility calls grounding
   directly. Existing complete-room tests do not demonstrate focused interaction
   payloads, an explicit insufficient-context decision, expansion under the shared
   deadline, or retained expanded recovery with protected/concurrent allowances.

Spec total: **3 P1 / 3 P2**. The worst issues are the unoptimized interaction route,
missing source-ID mapping and absent explicit evidence-insufficiency protocol.
Full-source citation validation, legacy defaults and reservation before added
writer dispatch are present; these do not close the gaps above.

## Independent verification

- Isolated `.venv/bin/python -m unittest tests.test_focused_evidence
  tests.test_openrouter_questions tests.test_combined_planning
  tests.test_combined_exchanges -v`: **51 run, 50 passed, 1 failed** in 11.579s.
  AI/provider/payment behavior is mocked. Failure:
  `FundedQuestionProtocolTests.test_confirmed_budget_starts_the_research_policy`,
  inherited from the research-plan room tests; starting the confirmed 19-question
  budget is refused by the new allowance bound.
- The exact 19-question-start case passes on the reviewed ticket-05 baseline
  (1 test, 0.136s), confirming the failure was introduced by this candidate.
- Synthetic funded-adapter/context reproductions confirm findings 1, 2 and 4;
  their content-free results are `.local/turn06-review/reproductions.json`.
- Full Python/React/build, new PostgreSQL and browser suites were not rerun for
  this review. The known failing focused gate and concrete findings are sufficient
  to withhold completion; prior ticket-05 evidence is historical, not a passing
  ticket-06 gate. No actual-provider speed/quality/cost, hosted or device checks.

The next step is to correct these findings and rerun the required checks.
No implementation fixes, commit, push or deployment were made by this review.

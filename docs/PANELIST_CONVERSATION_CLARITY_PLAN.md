# Panelist conversation clarity — planning interview

Status: ready-for-human. Planning complete; user confirmed Q1–Q11 on 2026-10-15.
Specification published locally on 2026-10-15:
[ready-for-agent specification](../.scratch/panelist-conversation-clarity/spec.md).
Test boundaries explicitly confirmed. The user approved the three-ticket
breakdown on 2026-10-15; separate ready-for-agent local tickets are published:

1. [Short questions and specific reactions](../.scratch/panelist-conversation-clarity/issues/01-short-questions-specific-reactions.md) — no blockers.
2. [Safe final closing](../.scratch/panelist-conversation-clarity/issues/02-safe-final-closing.md) — blocked by 01.
3. [Integrated conversation review](../.scratch/panelist-conversation-clarity/issues/03-integrated-conversation-review.md) — blocked by 02.

Ticket 01 is now implemented and independently reviewed locally; offline gates
passed (543 working-tree/535 selected Python with providers mocked, 275 React and
production build). See the [checkpoint review](PANELIST_CONVERSATION_CLARITY_REVIEW.md).
Ticket 02's final closing is also implemented and reviewed locally: 550 working-
tree/542 selected Python tests (providers mocked), 278 React tests/build, targeted
synthetic responsive/keyboard checks and screenshots passed. A presenter overlap
regression was reproduced/fixed and independently reviewed. Ticket 03 subsequently
completed the integrated offline/browser handoff below; live quality and user
approval remain pending. No remote-publication authorization is implied.

## Consolidated scope

Improve spoken question and reaction clarity across all three defense types.
Keep necessary qualifications, source grounding, distinct reviewers and existing
same-question rules. Keep optional current-timed reactions from the next reviewer,
and add an optional final closing from the last reviewer within coaching, with
safe empty/invalid-text fallback, transcript retention and reconnect continuity.
Reuse existing requests, preserve game/financial behavior, mirror shared dialogue
in Streamlit and deliver two locally reviewed checkpoints with separate mocked
and live evidence. No numeric scoring, supplied answers during questioning,
scripted dialogue, broader layout redesign or payment changes are included.

## Starting point

The user wants to plan improvements following a public comparison with DefendIt:
shorter spoken questions and clearer feedback about what an answer resolved.
That comparison used the competitor's built-in sample and this project's recorded
synthetic live papers, not a controlled same-paper or same-model benchmark.

Existing shared conversation guidance already asks for short natural sentences,
one main question, specific answer-aware reactions, respectful clarification and
acceptance of sufficient explanations. Reactions can be empty and remain bounded
to two sentences and 300 characters. The web room displays a reaction separately
before the next question; same-question probes and clarification have distinct
meanings in CONTEXT.md. Further planning should refine this behavior rather than
silently introducing scoring or a second assessment request.

Primary local evidence: backend/question_generator.py (CONVERSATION_GUIDANCE),
game/src/components/QuestionCard.tsx, and
[recorded live review](ADAPTIVE_RESEARCH_PANEL_LIVE_REVIEW.md).

Initial read-only exploration also found that a reaction belongs to the next
question. Completion moves require dialogue fields to be null, so a final
resolved answer does not currently get a standalone reaction. A complete plan
must explicitly decide that boundary rather than promising feedback after every
answer through the existing field alone. Question brevity is currently prompt
guidance; adding a strict rejection limit would introduce new failure behavior.

## Confirmed decisions — round 1

- Q1: apply conversation clarity to Code project, Research paper and Research +
  code, retaining their distinct reviewer specialties and flow policies.
- Q2: prefer one short spoken question, usually one sentence, with necessary
  detail allowed. Do not add a strict question-length rejection limit.
- Q3: use natural brief feedback about what an actual answer explained and,
  where useful, one remaining gap. Scores and detailed per-answer evaluation are
  outside this change; fuller feedback stays in post-defense coaching.

## Confirmed decisions — round 2

- Q4: keep useful reactions optional and retain the existing 4–12-second reading
  interval before the full speaker vote. Empty reactions skip that moment.
- Q5: the next reviewer continues to respond to the preceding answer when a
  meaningful connection exists, rather than adding a separate previous-reviewer
  handoff. The visible speaker must match the generated reaction's attribution.
- Q6: allow an optional final reaction attributed to the last reviewer, generated
  within the existing coaching request. It arrives when that request completes,
  not immediately on answer submission. Missed answers require neutral language;
  sessions without resolved turns retain a factual summary.

## Confirmed decisions — round 3

- Q7: retain same-question clarification, one consequential probe and advancement
  after a sufficient explanation. React to a specific reason/correction/gap;
  do not certify the study, repeat a resolved probe or supply the team's answer.
  Preserve explicit language preferences, including modern conversational Bisaya,
  neutral timeouts and occasional grounded conditional advice.
- Q8: present a valid final closing for the same brief reading interval, then
  show coaching without starting another vote or answer timer. Reconnect resumes
  the remaining interval. Preserve the closing in transcript/export. Empty or
  invalid optional closing text must not discard an otherwise valid report.
  Failed coaching retains its existing recovery. Successful coaching settles the
  run before any presentation delay, preserving charging/credit-return behavior.
- Q9: reuse existing generation, interpretation and coaching requests, with no
  separate evaluator/request stage. Compatible closing/report/snapshot additions
  are permitted. Preserve game rules, budgets, coverage, voting, timer lengths,
  prices, exact citations and private-data boundaries. Streamlit shares the
  dialogue/closing but shows its closing inline with the report. No claim of lower
  per-request cost or guaranteed fewer retries is made.

## Intended conversation

- Ask a concise main question; keep necessary source context visible separately.
- Let a useful reaction identify an actual reason, correction or unresolved issue.
- Accept adequate answers; use an existing probe for one material gap.
- Preserve grounded citation, clarification intent, language continuity and reviewer
  perspective. Defer numeric grades and supplied model answers during questioning.

The confirmed decisions above are agreed requirements. All substantive dialogue
remains generated; examples used during the interview are not embedded scripts.
Brief reactions remain at most two sentences and 300 characters. Brevity does
not remove necessary qualifications or turn speculative claims into evidence.

The opening question has no fabricated reaction. Normal transitions retain the
next reviewer's attribution. A final closing uses server-owned reviewer identity
and the actual final resolved exchange, including its probe/reply where present.
Early ending and missed replies must never be described as successful answers;
no-resolved-turn sessions keep their existing factual no-AI summary. The closing
must use completion wording rather than promising a next question or speaker vote.

## Confirmed delivery and verification — Q10

Two runnable local checkpoints on feature/question-first-room:

1. Shared question/reaction guidance and offline conversation regressions for all
   defense types, preserving existing interfaces and flow rules.
2. Optional final closing through coaching, compatible state/presentation and
   Streamlit integration, plus full integration and review evidence.

Agreed verification:

- Full Python/React suites and production build, with provider-mocked evidence
  explicitly separated from live quality claims.
- Mocked two-client code and twelve-question research/mixed defenses covering
  short/adequate/vague/contradictory answers, same-question clarification/probes,
  timeouts, early/budget/coverage endings, retry and reconnect.
- Optional closing tests for empty/invalid text without loss of valid coaching,
  coaching failure/retry, stale results after restart/closure, reconnect without
  replay, exact transcript retention and unchanged once-only financial settlement.
- Desktop/portrait/landscape keyboard and overflow checks, speaker attribution,
  closing/completion labels and preserved question/citation/answer access.
- Separate live before/after review using the same synthetic source and scripted
  answers under a recorded model/configuration: English and modern Bisaya, code,
  empirical and theoretical research, including strong, vague and contradictory
  answers. Compare concise wording, specific reactions, useful probing, evidence
  boundaries and completion without treating one sample as universal proof.
- Present local preview/screenshots and update README/PROJECT_LOG. Keep main and
  the live service unchanged. Hosted proxy/providers and installed Android/iOS
  checks remain separate evidence; no current physical-device claim.

## Decision tree

Q1–Q11 are settled. The user confirmed the complete plan and shared understanding
with “Matches—finish planning” on 2026-10-15.
No additional ADR is proposed:
these dialogue/presentation decisions are reversible and the existing domain
terms already distinguish reactions, clarification, probes and coverage.

No implementation, push or deployment is authorized by this planning interview.

## Integrated local handoff — 2026-10-16

Ticket 03 now has complete mocked integration and browser evidence in the
[review record](PANELIST_CONVERSATION_CLARITY_REVIEW.md): 550 working-tree/542
selected Python tests (providers mocked), 278 React tests and production build.
The user explicitly deferred live checks for now. Live before/after dialogue,
user/native-language approval and hosted/installed-device checks remain pending;
local handoff is ready-for-human, not approved or published.

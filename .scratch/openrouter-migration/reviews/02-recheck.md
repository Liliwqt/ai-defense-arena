# Ticket 02 — independent implementation recheck

Date: 2026-10-19. User requested checking the other agent's implementation.
Fixed diff: `git diff bd10cc3...bbc7a11`.
Commits: `39a7bf6` implementation, `bbc7a11` handoff. Reviewed committed source;
pre-existing dirty reasoning, local-testing, QR and documentation work excluded.

**Three P2 Spec findings require correction before publication.** No runtime
source was changed by this review. This supersedes the earlier zero-remaining
verdict for the affected preservation criteria.

## Standards

Independent Standards reviewer found **zero hard documented-standard
violations**: backend/test placement, package imports, tracker conventions and
mocked-versus-live evidence boundaries are followed.

One optional design judgment: new reviewer prompt assembly duplicates a reduced
subset of the previous research composer. Shared conversation policy would
reduce divergence while retaining distinct planner/reviewer instructions. This
is possible Duplicated Code, not a separate hard-standard failure. Its observable
policy loss is recorded under Spec below, not counted twice as a new bug.

## Spec

### P2 — Post-answer transient failures skip bounded automatic retry

Requirement: ticket 02 retains “safe selected-model recovery”; confirmed plan Q2
keeps bounded retries and existing recovery. README also documents one automatic
attempt after an accepted answer for temporary provider failures or invalid
responses.

`backend/openrouter_stream.py:102` wraps HTTP status failures in plain
`QuestionGenerationError`; line105 does the same for connection errors, and
lines85/89/93 do so for malformed/truncated structured output. The automatic
retry handler at `backend/rooms/questions.py:127` only catches the old provider
and validation exception types. These new exceptions bypass it and immediately
enter the outer manual-retry state.

Reproduction: funded Q1 accepted, defender answer preserved, next planner returns
mock HTTP503, with a valid planner/reviewer response available afterward. The
room immediately reports `phase=retry`, with only three provider calls total
(Q1 planner/reviewer plus failed next planner); automatic recovery never runs.

Correction: preserve typed retryable errors for server/network/invalid-output
failures. Keep credentials, allowance exhaustion, cancellation and incompatible
configuration outside automatic retries. Add funded post-answer recovery checks
and assert every dispatched attempt remains accounted.

### P2 — Mixed defenses reject valid implementation citations

Requirement: ticket 02 preserves “citation policy”; parent decision8 preserves
existing citation eligibility. The legacy research generator explicitly allows
every reviewer to cite either paper or implementation in mixed mode.

`backend/openrouter_questions.py:317` instead uses `_eligible_ids`, which limits
Methodology, Ethics and Impact to research files even in mixed mode. That helper
belongs to a different existing role policy. A correctly cited implementation
line therefore fails after both new stages have run.

Reproduction: research paper plus `queue.py`, Methodology planner chooses an
eligible opening topic, reviewer cites exact `queue.py` line1. The funded route
raises `InvalidQuestionResponse: The AI cited an invalid project file` after two
mock HTTP requests, despite that citation being permitted by the prior mixed
research route.

Correction: preserve the legacy research/mixed eligibility selection; test code
citations through funded Methodology/Ethics/Impact as well as Critical.

### P2 — Established conversation and probe safeguards omitted

Requirement: parent story20 retains the “agreed conversational style”; decision8
preserves probe behavior and conversation rules.

`backend/openrouter_questions.py:278` constructs reviewer messages without
`CONVERSATION_GUIDANCE` or `SCENARIO_GUIDANCE`, both included by the old research
generator. The independent shorter instructions omit explicit rules for reading
resolved probe replies, avoiding repeated gaps/reactions, not treating omissions
as proof of absence, addressing the team, and keeping hypothetical scenarios
grounded/nonconsecutive.

Reproduction: inspect the actual funded reviewer's mocked outgoing system
message. All four checked shared-policy fragments are absent, including “If it
resolves the requested detail” and “Never use scenarios in consecutive questions.”
This establishes lost request instructions, not measured live wording quality.

Correction: reuse the shared conversation/scenario policy and add funded request
contract checks, preserving the shorter-question objective and role-specific
instructions. Actual language/conversation quality still needs live evidence.

## Verification and limits

- Created an isolated `git archive bbc7a11` under
  `.local/openrouter-02-recheck/artifact`; supplied the unchanged local client
  build needed for FastAPI's static mount. An initial import-only launch failed
  because that ignored build was absent; no application failure was inferred.
- Independently reran the six previously reported focused modules:
  `tests.test_openrouter_questions`, `tests.test_openrouter_mapping`,
  `tests.test_provider_allowance`, `tests.test_research_coverage`,
  `tests.test_panelist_probe`, `tests.test_adaptive_research_integration`.
  **86 tests pass**, external providers mocked, real temporary SQLite. Log:
  `.local/openrouter-02-recheck/logs/focused.log`.
- Three additional isolated review probes all reproduce the missing behavior:
  **two assertion failures and one invalid-citation exception**. Probe source:
  `.local/openrouter-02-recheck/artifact/tests/ticket02_review_probes.py`;
  command from that artifact: absolute repository `.venv/bin/python -m
  tests.ticket02_review_probes`. Log:
  `.local/openrouter-02-recheck/logs/regressions.log`.
- No canonical tests or runtime files edited. No paid inference, secrets/private
  papers, browser/live AI claim, new full-suite or fresh PostgreSQL claim. The
  prior agent's646Python/393React/build/185PostgreSQL evidence remains recorded
  separately; it does not cover these three additional probes.
- Read public OpenRouter model/routing pages to check the proposed rate-cap
  concern. Current listed Haiku/GLM/Qwen rates fit the configured cap; that
  hypothesis is not a finding. No model-price/configuration change was made.

Final counts: **Standards0 hard violations, one optional duplication concern;
Spec3 P2 findings**, including automatic-recovery and mixed-citation regressions.
Ticket02 requires fixes/recheck; tickets03–04 should wait for its corrected gate.
No commit, push or deployment was performed by this review.

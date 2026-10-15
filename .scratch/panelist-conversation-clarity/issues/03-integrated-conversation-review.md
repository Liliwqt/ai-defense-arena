# 03 — Integrated defenses and local conversation review

**What to build:** demonstrate the complete concise-dialogue and final-closing
experience through full mocked defenses, responsive local previews and a
separately documented live before/after comparison. Present the complete local
flow and evidence for review, completing checkpoint 2's handoff.

**Blocked by:** 02 — Safe final closing before coaching.

**Status:** ready-for-human

- [x] Run the full existing Python and React suites and production build; record check names and explicitly identify mocked AI/auth/payment evidence.
- [x] Complete authenticated mocked two-client code and twelve-question research/mixed defenses, preserving distinct code-only and coverage-driven policies.
- [x] Integrated runs cover vote, adequate/vague/contradictory answer outcomes, same-question clarification, probe/reply, timeout, normal/coverage/budget/host completion, generation retry and reconnect, without duplicate turns or lost accepted answers.
- [x] Both clients agree on exact citations, transcript, research coverage/gaps, coaching and the final closing. The closing has correct server-owned attribution, consumes no question and introduces no extra vote or answer clock.
- [x] Demonstrate valid, missing, empty and unusable optional closing with valid core coaching, genuine coaching failure/retry, repeated ready state, reconnect during/after the interval and stale completion after restart/closure using the approved existing seams.
- [x] Existing once-only charge, successful settlement, coaching-error recovery and credit-return regression evidence remains valid. Closing display cannot defer completion, cause refunds or revive a settled run.
- [x] Desktop, portrait and landscape local browser checks confirm readable reaction/closing content, correct speaking/completion labels, visible focus, keyboard navigation, usable source/transcript/controls and no clipped content or unintended horizontal overflow.
- [x] Present screenshots and the actual local preview for human review. Verify legacy snapshots/reports and inline Streamlit closing; do not infer user approval from an automated browser check.
- [ ] Separately inspect live before/after conversations with the same synthetic papers/code and scripted defender answers, recording the compared revisions and safe model/configuration information. Use a controlled starting-version comparison rather than unmatched historical transcripts.
- [ ] Live review covers English and modern Bisaya, code, empirical/theoretical research and mixed integration; examine strong, vague, contradictory and clarification responses, concise wording, necessary qualifications, specific reactions, useful probing, evidence boundaries, closing and coaching.
- [x] Retain factual live samples/findings and distinguish them from mocked checks. Missing credentials or other unavailable live evidence stays explicitly pending; do not mark the live criterion complete from offline output or claim universal correctness/native-language quality.
- [x] Update README/project handoff after each logical checkpoint and the final review with changes, evidence, risks and remaining review. Keep hosted, physical/native-device and native-speaker/user approval separate from local browser/live-AI evidence.
- [x] Preserve unrelated local files/deletions and keep frozen main/current production unchanged. No remote push or deployment occurs without a later request.

## Context and handoff

Originating specification: **Panelist conversation clarity and final closing**,
confirmed 2026-10-15. Ticket 01 supplies shared dialogue refinements; ticket 02
supplies the safe complete closing experience. Both already include relevant
slice checks; this ticket proves the integrated behavior and presents local
evidence without moving core safety testing into a final-only QA step.

Use the existing authenticated room/provider-mocked fake-clock boundary,
generation/coaching contracts, Streamlit checks and whole-room React/browser
seams confirmed by the user. No separate evaluator, model migration, price or
layout redesign is included. The user must actually review presented evidence
before any human approval is recorded.

## Comments

2026-10-15: User approved integrated handoff after ticket 02; ticket 01 is a
transitive prerequisite, so it is not a redundant direct blocking edge.

2026-10-16: Offline integration/browser handoff complete; 550 working-tree and
542 selected Python tests (providers mocked), 278 React tests and production build
pass. See docs/PANELIST_CONVERSATION_CLARITY_REVIEW.md for test boundaries,
screenshots and the actual static preview. User explicitly chose “Skip live
checks for now”; live before/after and native-language quality criteria above
remain unchecked/deferred. Ready-for-human means local evidence is presented,
not user approval or all live checks completed. No push/deploy.

Independent final Standards/Spec review of immutable candidate 52d054a against
approved baseline 9314379 found zero actionable findings on each axis. Local
reviewed commit only; publication still requires a later request.

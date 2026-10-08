# 06 — Run-wide and owner-shared AI allowances

**Blocked by:** 04 — Bounded clarification and explicit direct answers.

**What it delivers:** Host and guest AI work share predictable run/owner limits, long research sessions have proportionate allowances and resource rejections preserve transcripts and existing financial recovery.

**Status:** ready-for-human

Acceptance criteria:

- [ ] Apply the proposed 12 outbound attempts per owner per rolling minute across paid, voucher and sandbox modes, including guest submissions and all existing host AI actions. Derive owner identity server-side.
- [ ] Reuse actual-attempt accounting from 04. Enforce three question-generation attempts per turn, three preparation attempts per uploaded-project version, three coaching attempts per run and the 9 × B + 6 run envelope, where B is approved research budget or eight for code-only.
- [ ] Track preparation before a run and guard restarts/settings changes with the same owner burst allowance. Reset budgets only at the correct genuinely new run/project boundary; stale work cannot consume or reset a replacement run's allowance.
- [ ] Do not dispatch over-limit requests. Preserve pending text, accepted answers, coverage and current run; show retry timing or exhausted-allowance recovery without falsely claiming a provider failure.
- [ ] Preserve opening reservation release/retry, once-only charge and existing question/coaching provider-error credit return. Rate rejection alone never makes a run refundable. Explicit direct answers remain recordable without an interpretation allowance.
- [ ] Reconnect restores current allowances/capabilities without an AI call; shared fields reveal no account/financial details. Shared generation entry points and Streamlit remain compatible without adding multiplayer controls to the fallback.
- [ ] Mocked tests cover owner/guest concurrency, paid/voucher parity, opening and later failures, retries, restart/stale work, twelve-turn research behavior and the approved 100-question boundary, without extra charges.

## Comments

2026-10-08: Implemented locally; required review against dd037d5 and selected-release gate follow. See docs/SECURITY_ADMISSION_REVIEW.md for checks and remaining hosted/native/user review boundaries. The Implement skill authorizes a local commit despite the earlier planning-only no-commit wording; no push/deploy. Checklists are retained for reviewer assessment rather than asserting unrun cases.

# 06 — Progressive coaching with safe completion and recovery

**What to build:** Long research reports arrive automatically in finite admitted
sections, with a single closing, immediate access to ready cards and honest
completion/recovery that does not settle or return credits twice.

**Blocked by:** 05 — Grounded per-answer text coaching.

**Status:** ready-for-human

## Acceptance criteria

- [x] Freeze required membership from the accepted transcript and generate overview/every required section automatically in bounded sequential/admitted groups. Stable run/section/job identities and finite attempts deduplicate work and fence stale success/failure.
- [x] After the overview, show a valid optional last-reviewer closing once using its remaining interval, then open progressive Results. Bad/empty optional closing skips safely; reconnect restores time/progress; section retry never replays closing or interrupts Account/payment tasks.
- [x] Show ready cards and completed/required progress with pending/failed states. A required failure preserves ready sections exactly; admitted host retry targets failed sections only, continues valid pending work and charges no new defense. Exhausted recovery identifies permitted actions clearly.
- [x] Partial Results remain financially unfinished until the overview and every required section validate and durable completion succeeds. Completion-write failure remains recoverable. Update room retention/stage logic so partial Results are not expired or treated as successful settlement.
- [x] Preserve existing eligible end-unavailable credit return, interruption recovery and abandonment policy. Paid compensation is once-only; free/voucher runs cannot mint credits. A return/restart/close/replacement fences late work so it cannot reverse a return, overwrite another report or settle twice. Speech failure alone does not grant a refund for an otherwise available typed defense.
- [x] Partial/failed/complete export retains accepted originals, speaker/probe/provenance/evidence and ready sections. Streamlit keeps ready research text work and truthful failed-section recovery without pretending to support live-store compensation. No audio or durable Results archive is added.
- [x] Protocol/store/App checks cover closing/progress/retry and races among final-section completion, persistence failure, end-unavailable and restart; compare ledger outcomes and unchanged ready cards. Exercise twelve-question and large supported-budget reports with providers mocked, plus code-only regression.

## Verification

Fail one section after overview/closing, review ready cards,
retry just the failed section and finish once. In another run, return eligible
charged credits then deliver a late success and show it cannot settle/reverse
the return. This is part of checkpoint 3, which also requires 07.

## Comments

- 2026-10-17 — User approved the ten-ticket breakdown as drafted; published locally with its agreed blocking edges and acceptance criteria. Specification stories: 75–98, 106, 108.
- Parent: [research-defense practice specification](../spec.md). The parent remains the source of full scope, test boundaries and accepted ADRs; it is not changed by publication. Selected UI: B — Speaker desk, captured on prototype/research-practice (source f0d74a7, verdict a3046c4).
- Each ticket includes its own verification and leaves the app runnable. Record provider-mocked, actual speech, local database, native-build/device and hosted evidence separately. Ticket approval does not start implementation, authorize external-model sharing, push or deploy.

- 2026-10-18 — Implemented locally in f679c8f/caa0671; independent Standards 0 / Spec 0 remaining against user-confirmed 3f340ca after fixing Streamlit ready-card visibility. Final isolated gate: 598 Python (AI/speech/identity/payments mocked), 378 React, production build; 19 real local PostgreSQL funding/handoff checks with providers mocked. Synthetic Chromium desktop/portrait/landscape retry/export/refresh/Account checks pass. [Review and screenshots](../reviews/06.md). User visual, actual coaching/voice quality, hosted and installed devices remain pending. Checkpoint 3 still requires 07. No push/deploy/main change.

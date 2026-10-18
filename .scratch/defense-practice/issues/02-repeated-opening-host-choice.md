# 02 — Host choice when an opening repeats

**What to build:** If bounded variation still repeats, the host can explicitly
retry or accept the validated repeated candidate while the team waits.

**Blocked by:** 01 — Research-first practice with varied openings.

**Status:** ready-for-human

## Acceptance criteria

- [x] After the admitted duplicate regeneration, expose a clear host-only candidate/limitation with Retry and Accept repeated question; candidate preview is explicitly not an active defense question. Guests see waiting guidance rather than host controls.
- [x] Bind choice to the current host, room, run, map, candidate and generation. Old acceptance, changed-map, changed-run, guest and racing duplicate commands cannot activate or charge an obsolete candidate.
- [x] Retry stays within existing finite admission, preserves accepted paper/history and does not create asked-question history or charges for discarded candidates.
- [x] Accept revalidates source/ownership/current history and performs the once-only commit from 01; voting/deadline starts only after commit. Explicitly accepted repetition is a real committed opening and is retained idempotently.
- [x] Two-client mocked and whole-App checks cover failure/retry/accept/reconnect and role-specific mobile and keyboard actions. Real local transaction tests cover acceptance races and persistence failures without double charging.

## Verification

Force two recent duplicate candidates, inspect waiting views,
accept once, then replay an old choice after changing the run/map. Complete
checkpoint 1 with the app runnable and code-only unaffected.

## Comments

- 2026-10-17 — User approved the ten-ticket breakdown as drafted; published locally with its agreed blocking edges and acceptance criteria. Specification stories: 20–25.
- Parent: [research-defense practice specification](../spec.md). The parent remains the source of full scope, test boundaries and accepted ADRs; it is not changed by publication. Selected UI: B — Speaker desk, captured on prototype/research-practice (source f0d74a7, verdict a3046c4).
- Each ticket includes its own verification and leaves the app runnable. Record provider-mocked, actual speech, local database, native-build/device and hosted evidence separately. Ticket approval does not start implementation, authorize external-model sharing, push or deploy.

- 2026-10-18 — Implemented locally through 1fcdbc2 and independently reviewed against user-confirmed e68f149. Final Standards 0 / Spec 0; 560 Python (providers mocked),365 React,175 real-local-PostgreSQL checks and build pass, with final layout-focused checks and synthetic responsive screenshots. See [review and evidence](../reviews/02.md). Checkpoint 1 implemented/locally verified; user visual/live-quality acceptance pending. No push/deployment.

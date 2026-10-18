# 10 — Complete defenses and local review handoff

**What to build:** Verify the feature as one research-practice experience and
present the local preview and evidence, without conflating mocks, hosted behavior
or actual recorded speech/native-device support.

**Blocked by:** 02 — Host choice when an opening repeats; 06 — Progressive coaching with safe completion and recovery; 07 — Evidence-based voice delivery feedback; 08 — Android microphone practice; 09 — iOS microphone practice.

**Status:** ready-for-human

## Acceptance criteria

- [x] Run the full Python and React suites/build, real local database history/migration/expiry/concurrency/restart checks, and complete mocked two-client research/mixed runs including twelve questions and supported large report membership. Code-only, typed-only, existing access/price/citations/PDF and Streamlit remain compatible.
- [x] Cover duplicate/stale openings, voice/typed/probe/clarification, send/finalization/deadline/cap, interpretation/reconnect/navigation recovery, every-turn grounded cards, once-only closing, partial/failed retry/export, completion persistence and credit-return/stale-work races. Do not merely repeat unit helper assertions.
- [x] Review Speaker desk and focused coaching at desktop/portrait/landscape with keyboard/focus, long papers/reports, readable read-only words, unobscured next actions and unchanged live-timer/account-task behavior. Present local preview/screenshots before any publication.
- [ ] Record actual speech quality, supported language/code-switching, observed fillers/measures, maintained provider access/protocol/cost/retention, hosted relay behavior and installed Android/iOS capture as separate evidence. No paid call/audio upload/deployment is implied; unavailable evidence keeps the relevant capability/readiness claim pending.
- [x] Keep the prototype source/verdict as a reference; do not promote fake transcripts, scenario controls or prototype switchers. Finish the integration review and handoff against the implementation baseline selected at implementation time, without changing the parent spec or merging/pushing/deploying under this ticket-writing request.

## Verification

Present the full mocked research/mixed flow, the selected layout
and a clear passed/pending evidence record. This completes checkpoint 4's local
handoff; it cannot certify devices/providers that were not actually checked.

## Comments

- 2026-10-17 — User approved the ten-ticket breakdown as drafted; published locally with its agreed blocking edges and acceptance criteria. Specification stories: 108 and integrated acceptance of 1–107.
- Parent: [research-defense practice specification](../spec.md). The parent remains the source of full scope, test boundaries and accepted ADRs; it is not changed by publication. Selected UI: B — Speaker desk, captured on prototype/research-practice (source f0d74a7, verdict a3046c4).
- Each ticket includes its own verification and leaves the app runnable. Record provider-mocked, actual speech, local database, native-build/device and hosted evidence separately. Ticket approval does not start implementation, authorize external-model sharing, push or deploy.
- 2026-10-19 — Implemented on request against baseline **b1727e7** in an isolated `git archive` artifact, so unrelated uncommitted QR/backend/research-plan work was excluded by construction and stays untouched; no source change was needed. Verified (all offline, AI/speech/payment providers mocked): Python 604 OK, React 391/391 in 36 files, production build OK; real PostgreSQL 16.15 gate 177 OK plus a real `pg_ctl` stop/start reread (funding survived, interrupted-run credit returned exactly once); complete twelve-question two-client research/mixed runs pass. Responsive review in real Chromium at 1440×960/390×844/844×390 with mocked account/WebSocket snapshots: live timer ticks, Speaker desk with long question/citation readable and non-editable, keyboard/focus incl. compact-only "Go to answer" shortcut, unobscured submit, account "Return to defense" preserved, 12-question coaching membership with keyboard navigation, read-only transcript and mocked summary export; zero page errors. Screenshots in `reviews/evidence/10-*.png`, gallery `http://127.0.0.1:8871/practice-review.html`, full record `reviews/10.md`. Prototype stays reference-only (no switcher in built assets); parent spec unchanged; nothing pushed/deployed/merged. Criterion 4 deliberately left open: actual speech quality, languages/code-switching, filler measures, provider access/cost/retention, hosted relay and installed Android/iOS capture (incl. iOS build/XCTest, no macOS toolchain here) are recorded as separate pending evidence and are not claimed. Awaits user review.

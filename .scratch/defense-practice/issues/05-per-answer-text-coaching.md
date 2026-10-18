# 05 — Grounded per-answer text coaching

**What to build:** A short completed research/mixed defense produces a complete
validated report with detailed guidance for every recorded answer, shown in B's
question-selector/detail layout and shared as typed research coaching in Streamlit.

**Blocked by:** None — can start immediately.

**Status:** ready-for-human

## Acceptance criteria

- [x] Expand report/recipient/client contracts additively before migrating research consumers, preserving legacy and code-only reports. Introduce only the narrow report ownership seam needed by this slice; no broad mechanical refactor or temporary broken callers.
- [x] Every recorded turn in a validated complete report includes original answer, actual speaker/probe exchanges, specific strengths/gaps, supported stronger wording and practice task. Preserve originals; missing facts are labeled conditional/scaffolds, not invented methods/results. Advice uses confirmed research field, approach, stage, setting and evidence.
- [x] Unanswered turns get factual guidance without fabricated answers/strengths; empty sessions retain a factual no-unnecessary-AI summary. No unasked future question receives a card. Missing/invalid required cards cannot produce ready or successful settlement.
- [x] Results uses an accessible question selector and focused expandable details rather than a wall of text; retain original-versus-improved comparison and truthful voice/text evidence labels. Typed input has no invented audio statistics; observed wording/filler examples can be discussed without asserting uncaptured spoken measures.
- [x] Share richer research text coaching and originals in typed Streamlit without adding voice or fictitious financial compensation. Transcript/export includes completed cards, provenance where already available and truthful status; code-only data/output remains compatible.
- [x] Keep the existing complete-report request/closing/retry path runnable for bounded short reports. Do not introduce partial financial success or claim long-report batching here; 06 expands generation/recovery to admitted sections. Truncated, oversized or incomplete output fails recoverably rather than appearing fully coached.
- [x] Existing report contracts plus full room/App/fallback tests demonstrate end-to-end typed short defenses, grounded instructions, every-recorded-turn membership, speaker/probe attribution, no-answer cases and desktop/phone keyboard/detail navigation. Mocked text is not evidence of real coaching quality.

## Verification

Complete a short mocked research defense with an answer, probe and
missed turn; compare each original with supported wording and a practice task.
Reject a missing card instead of showing a complete report. Keep the app runnable
while 06 adds long-run batching/progressive Results.

## Comments

- 2026-10-17 — User approved the ten-ticket breakdown as drafted; published locally with its agreed blocking edges and acceptance criteria. Specification stories: 5–6, 10, 69–85, 95, 97, 104–106.
- Parent: [research-defense practice specification](../spec.md). The parent remains the source of full scope, test boundaries and accepted ADRs; it is not changed by publication. Selected UI: B — Speaker desk, captured on prototype/research-practice (source f0d74a7, verdict a3046c4).
- Each ticket includes its own verification and leaves the app runnable. Record provider-mocked, actual speech, local database, native-build/device and hosted evidence separately. Ticket approval does not start implementation, authorize external-model sharing, push or deploy.

- 2026-10-18 — Source 2d637cc implemented and independently reviewed against actual starting commit 6581ffe (async baseline confirmation pending). Standards 0 / Spec 0. Isolated 587 Python tests (AI/speech/Google/payments mocked), 374 React tests, production build and synthetic Chromium selector/keyboard/export checks at desktop/portrait/landscape pass. [Review and screenshots](../reviews/05.md). Bounded complete reports support up to twelve recorded turns; 06 adds long-report batching/progressive recovery. User visual and actual coaching quality remain pending. No real provider call, push/deploy or main change.

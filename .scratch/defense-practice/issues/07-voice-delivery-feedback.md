# 07 — Evidence-based voice delivery feedback

**What to build:** Coaching distinguishes what was actually said, reliable
recording-derived measures and AI suggestions for each accepted voice answer or
probe reply, including stronger structure and captured filler examples.

**Blocked by:** 04 — Voice probe replies and recovery across screens; 05 — Grounded per-answer text coaching.

**Status:** ready-for-human

## Acceptance criteria

- [x] Associate server-validated capture evidence with the accepted original answer/probe and actual speaker. Discarded, provisional, wrong-text and obsolete attempts supply no coaching performance evidence; their forwarded usage still counts against voice allowance.
- [x] Show captured filler/repetition examples and supported clearer structure/wording. Distinguish transcript observation, measured evidence and suggestion. A cleaned transcript cannot prove no fillers or complete filler totals; typed answers cannot receive invented spoken measures.
- [x] Compute/display approximate rate or pauses only from sufficient reliable capture/timing evidence for submitted material. Explain missing/insufficient/uncertain measurements without zero placeholders, accent grades, psychological confidence or transcript-only pronunciation/tone claims.
- [x] English-first voice remains independent of typed language support. Tagalog/Bisaya/code-switching are offered individually only after support/representative quality evidence; preserve natural wording without forced translation or automatically labeling normal particles as fillers. Unsupported recognition leads to typing, not a poor-delivery judgment.
- [x] Per-turn cards, overview and export retain evidence provenance and speaker/probe attribution without an audio archive. Finite buffering, log privacy and app/provider retention disclosure stay intact.
- [x] Fake-audio/report/App tests demonstrate reliable and unavailable evidence, observed uhm/structure advice, distinct speakers/probes, typed comparison and malicious client-measure claims. Record real recognition/filler/measurement/language checks separately; unavailable real checks stay pending. Complete checkpoint 3 together with 06.

## Verification

Compare an accepted voice answer with reliable synthetic timing,
a typed answer and an uncertain-recognition sample. Show supported examples and
honest unavailable evidence, not fabricated statistics or study decisions.

## Comments

- 2026-10-17 — User approved the ten-ticket breakdown as drafted; published locally with its agreed blocking edges and acceptance criteria. Specification stories: 64–74, 79–85, 97, 107–108.
- Parent: [research-defense practice specification](../spec.md). The parent remains the source of full scope, test boundaries and accepted ADRs; it is not changed by publication. Selected UI: B — Speaker desk, captured on prototype/research-practice (source f0d74a7, verdict a3046c4).
- Each ticket includes its own verification and leaves the app runnable. Record provider-mocked, actual speech, local database, native-build/device and hosted evidence separately. Ticket approval does not start implementation, authorize external-model sharing, push or deploy.

- 2026-10-18 — Local source6284f99/5c05207 implemented accepted-only capture facts, exact bounded transcript observations and separate original/probe speaker coaching/export. Speaking rate and linguistic pauses remain unavailable because the checked pilot model provides no word timing/confidence; recording duration is measurable and excludes padding. Standards0/Spec0 after fixing missing overview restrictions, baseline64db4a7 user-confirmed. Isolated604Python/381React/build and synthetic desktop/portrait/landscape keyboard/evidence/export checks pass (providers mocked). [Review](../reviews/07.md). Checkpoint3 locally implemented with06; user visual and actual recognition/filler/measurement/language/provider/native evidence remain pending. Default-off voice; no actual recording/provider call, push/deployment or main change.

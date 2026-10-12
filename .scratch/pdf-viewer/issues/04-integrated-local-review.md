# 04 — Integrated defenses and local visual handoff

**What to build:** The complete PDF viewer works in multi-client research and
mixed defenses and is presented as a running local preview with screenshots,
verification evidence and a clear review guide before publication.

**Blocked by:** 03 — Confident citation highlighting and truthful fallback.

**Status:** ready-for-human

- [x] Run the full Python suite with AI/Google/PayMongo mocked, React suite and production build, fixing regressions within the approved scope.
- [x] Complete mocked two-client research and mixed defenses, including a twelve-question run, personal document/page browsing, voting, clarification, answer probe, timeout, reconnect, transcript and coaching.
- [x] Confirm exact citations, retained answer drafts, synchronized question/reaction/clarification states and unchanged votes, deadlines, accepted answers, coverage and charges while clients use the viewer.
- [x] Complete integrated authorization, snapshot-privacy, storage-quota, failed/cancelled creation, lifecycle cleanup, run restart and stale-document/render checks; ordinary security and cleanup checks must already pass in the preceding tickets.
- [x] Inspect actual fixture PDFs through the production PDF.js worker: document/page switching, selectable text, unique highlights and ambiguous fallback, zoom/Fit width, long questions/source lines and column/repeated-text layouts.
- [x] Check desktop, portrait and landscape phone layouts and keyboard-only use for readable questions, labelled controls, visible focus, internal scrolling, tabs, expanded reading/focus return, accessible timer/dock and no clipped controls.
- [x] Update user documentation and shared handoff records with implemented behavior, configured retention limits and cleanup lifetime, rendering/AI scope, local preview and screenshots. Describe remaining live/hosted/installed-device checks separately.
- [x] Present the local screen and screenshots for user review; do not mark user visual review complete until it occurs. Distinguish provider-mocked defenses from actual browser PDF rendering and from any installed Android/iOS evidence.
- [x] Preserve unrelated files, parent specification, frozen main and current live release. No PDF downloads, Git push, deployment, payment changes, AI figure interpretation or new question policies are introduced by this ticket.


## Implementation handoff

Implemented locally; see [PDF_VIEWER_REVIEW.md](../../../docs/PDF_VIEWER_REVIEW.md) for the preview and evidence. User visual approval and publication remain pending.

# 03 — Confident citation highlighting and truthful fallback

**What to build:** A confidently and uniquely matched exact citation is
highlighted at its actual location on the original physical PDF page, including
after zoom and Fit width. Ambiguous or absent matches retain the page and exact
quote with a truthful precision-unavailable message.

**Blocked by:** 02 — Personal paper browsing and reading controls.

**Status:** ready-for-human

- [x] Match only the server-owned exact extracted quotation on its cited physical page, without changing the quotation or trusting client-supplied source locations.
- [x] Highlight only a confident unique occurrence mapped to actual rendered text geometry; permitted whitespace handling cannot invent a match or infer coordinates from extracted line numbers.
- [x] Repeated, ambiguous, absent or unmappable text displays the unchanged exact quote and “Precise highlight unavailable” rather than a guessed visual location.
- [x] Highlight geometry stays aligned after zoom, Fit width and viewport changes; wrapping, columns, repeated passages and extraction-order differences are handled conservatively.
- [x] Citation/document changes and navigation away from the cited page clear obsolete highlights; late loads/renders/matches cannot restore stale geometry. Return to citation recalculates against the correct page.
- [x] Keep filenames, physical page and extracted-line labels visible and distinguish extracted lines from visual PDF line numbers; a source match does not certify the AI's interpretation.
- [x] Preserve personal browsing and phone-tab behavior, exact quote fallback, keyboard use, answer drafts and existing defense flow. Highlighting adds no AI request or charge.
- [x] Verify observable unique/absent/ambiguous matching outcomes and actual fixture-PDF highlight geometry at multiple zooms and desktop/portrait/landscape sizes; mocked text geometry alone is not accepted as real-rendering evidence.


## Implementation handoff

Implemented locally; see [PDF_VIEWER_REVIEW.md](../../../docs/PDF_VIEWER_REVIEW.md) for the preview and evidence. User visual approval and publication remain pending.

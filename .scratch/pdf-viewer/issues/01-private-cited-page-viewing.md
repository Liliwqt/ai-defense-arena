# 01 — Private cited-page viewing

**What to build:** Joined defenders can see the original cited PDF page in the
central room card through private, bounded, room-owned storage. The question and
exact extracted quote remain readable during loading or rendering failure;
desktop shows the question above the PDF and phones have a basic Question/Paper
switch without losing the timer and bottom dock.

**Blocked by:** None — can start immediately.

**Status:** ready-for-human

- [x] Retain only validated original PDFs in private temporary disk storage, separate from AI-facing extracted text and outside static/public assets; preserve existing format, file-size, page, extracted-context, file-count and HTTP upload limits.
- [x] Default operator-configurable original-byte quotas to 110,000,000 bytes per room and 500,000,000 bytes server-wide; atomic reservations prevent concurrent overbooking and capacity failures are reported before room publication.
- [x] Rejected, failed or cancelled parsing/creation/publication releases reserved bytes and temporary files; room closure, expiry and reclamation release retained originals and capacity.
- [x] Restarting a defense run in the same room keeps its originals; shutdown/startup orphan cleanup respects existing service ownership and cannot remove another active service's files during deployment handoff.
- [x] A read-only same-origin document resource returns original PDF bytes only to valid joined player identities; hosts additionally require their verified owner account. Missing/invalid credentials, room-code-only requests, wrong-room/guessed document IDs and closed/expired access return no paper bytes.
- [x] Document requests use header credentials, opaque identifiers, correct PDF media type and no-store responses; URLs, logs and shared metadata expose no player tokens or private storage paths. Cleanup/read races fail safely.
- [x] Initial and reconnect snapshots expose safe document identity, accepted name, physical page count and server-resolved citation association without originals or private credentials; rooms without PDF metadata remain compatible.
- [x] Lazy-load PDF.js and its bundled worker; render the current cited physical page as a canvas with selectable text in the existing grayscale room. A new PDF-cited turn selects its server-owned document and page.
- [x] Loading and readable viewer errors leave the question and exact extracted quote usable. A local renderer/document retry invokes no AI, consumes no credits, restarts no defense and preserves answer drafts; obsolete loads/renders cannot publish after switching or teardown.
- [x] Desktop keeps the question above the page; a basic accessible phone Question/Paper switch and internal scrolling keep the header, timer, compact seats and answer/chat dock accessible. Code and non-PDF excerpts retain their existing presentation.
- [x] Keep exact extracted citation text, filename, physical page and extracted-line labels; do not fabricate visual highlights or imply that AI interprets newly visible figures. Visual highlighting is delivered by ticket 03.
- [x] Verify byte fidelity, host/guest/wrong-room access, snapshot privacy, concurrent quotas, rollback, lifecycle cleanup/restart/handoff and basic viewer loading/failure behavior through existing app boundaries; render an actual fixture PDF with the production worker. Keep providers mocked and report real rendering evidence separately.


## Implementation handoff

Implemented locally; see [PDF_VIEWER_REVIEW.md](../../../docs/PDF_VIEWER_REVIEW.md) for the preview and evidence. User visual approval and publication remain pending.

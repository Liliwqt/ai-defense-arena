# 02 — Personal paper browsing and reading controls

**What to build:** Defenders can browse any accepted PDF independently with page,
zoom and document controls, return to the grounded citation, and expand the
reading area. Their reading position survives same-question updates and
reconnect while phone tabs and room participation remain usable.

**Blocked by:** 01 — Private cited-page viewing.

**Status:** ready-for-human

- [x] Provide labelled previous/next page controls and current-page/total-page information, disabling unavailable page actions at document boundaries.
- [x] Provide zoom, Fit width, Return to citation and a document selector for all retained PDFs in the joined room; selection always uses the authenticated delivery established by ticket 01.
- [x] A new PDF-cited defense turn selects its server-owned document and physical page; a reconnect to a newer turn follows that citation, including after a defense-run restart.
- [x] Same-turn clarification, answer probes, voting, chat updates and reconnect preserve the defender's own page and zoom. One client's browsing never changes another client's reading position.
- [x] New-turn citation navigation does not force a phone user out of the Question tab. Switching Question/Paper tabs preserves reading position and keeps the timer, seat strips and answer/chat dock accessible.
- [x] Code-cited turns keep their code excerpt prominent with manual paper browsing available; DOCX/TXT/Markdown retain extracted-text display and code-only rooms retain their existing layout.
- [x] Expanded reading has a labelled exit, accessible timer and answering controls; keyboard operation and exit restore focus to the trigger without trapping navigation.
- [x] Navigation, zoom, document changes, expansion and local retry preserve answer drafts and the existing reaction/clarification/probe display; they add no AI requests or changes to votes, timers, accepted answers, charges or coverage.
- [x] Document/page switching retires obsolete loads and renders; the page count, displayed document and page cannot be overwritten by a late result from an earlier selection.
- [x] Verify whole-room controls, independent two-client browsing/reconnect and new-turn transitions using actual multi-page/multi-document fixtures, including desktop/portrait/landscape internal scrolling and keyboard focus checks. Record provider-mocked flow and actual PDF rendering separately.


## Implementation handoff

Implemented locally; see [PDF_VIEWER_REVIEW.md](../../../docs/PDF_VIEWER_REVIEW.md) for the preview and evidence. User visual approval and publication remain pending.

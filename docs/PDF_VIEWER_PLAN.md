# Central PDF viewer — confirmed plan

Date: 2026-10-13. Work branch: `feature/question-first-room`.
The user resumed this feature after publishing the web logo.
This document distinguishes source facts from proposed choices; it is not an
implementation specification or publication instruction. The three decision
rounds and final shared-understanding confirmation were accepted by the user
on 2026-10-13. Planning is complete; implementation has not started.

## Intended outcome

Defenders can inspect the uploaded PDF visually in the center of the room,
including the cited page and surrounding paper, while retaining a readable
question, authoritative timer and answer controls.

## Current source facts

- `backend/research_files.py` extracts accepted PDF text into `ProjectFile`.
  Its location labels include the one-based physical PDF page and extracted
  line. It does not retain original PDF bytes or citation rectangles.
- `game/src/components/PageCitation.tsx` presents extracted text, with optional
  neighbouring context. Its fidelity note explicitly says that figures,
  tables and equations are not shown. This is not an original-PDF renderer.
- The current question and exact citation share the central scrolling card.
  Compact phone layouts preserve their header, seat strips and bottom dock.
- Rooms and uploaded context remain in memory and disappear on restart. A
  new original-document access path must respect room membership, host account
  checks and cleanup rather than expose uploads under public assets.
- AI requests currently use accepted extracted text. Rendering the PDF for
  defenders does not make the AI understand its figures or equations.

## Retention and access findings

The current limits permit a 10 MB PDF, 100 PDF pages, a 110 MB upload request
and 20 retained/inflight rooms. Retaining all original uploads in application
RAM could therefore add roughly 2.2 GB before parser/rendering overhead. The
600 KB extracted-context limit does not bound compressed PDF bytes.

A separate, bounded original-document store is needed. The user selected private
ephemeral disk storage, creation reservations, cleanup of failed uploads, room
expiry/close cleanup and startup removal of orphan files. Original documents
live only as long as their room, across successive defense runs in that room.

Current guests authenticate with a private player token, while host access also
checks the verified owner account. A proposed same-origin document endpoint
would apply those checks, accept authorization in a header rather than a URL,
and return no-store responses. Room codes alone would not grant document access.
Snapshots would contain document metadata and citation page IDs, not bytes or
private tokens. No such endpoint exists yet.

Native Android/iOS download bridges currently handle bounded text transcript
exports only. PDF viewing through the existing React website is a candidate;
PDF downloads would need a separate decision and installed-device verification.

These findings come from read-only inspection of backend/game_server.py,
backend/project_files.py, backend/research_files.py, backend/rooms/model.py,
backend/rooms/lifecycle.py, backend/rooms/coordinator.py,
game/src/hooks/useRoomSocket.ts and mobile/README.md. No provider calls or
runtime tests were used to establish them.

## Proposed viewer approach

Use Mozilla PDF.js with a small app-specific toolbar, loading the renderer only
when needed and rendering the current page rather than the entire document at
once. The original uploaded PDF supplies the appearance; server-owned extracted
text remains the authority for citations.

The PDF.js display API supports fetching a document/page and rendering a scaled
page to a canvas. Its text layer can supply selectable text; it does not establish
that a pypdf extracted line maps uniquely to a rectangle. Whitespace, columns,
hyphenation and repeated passages need a tested matching/fallback policy.

Primary sources:

- [PDF.js rendering examples](https://mozilla.github.io/pdf.js/examples/index.html)
- [PDF.js layers and setup](https://mozilla.github.io/pdf.js/getting_started/)
- [PDF.js document/text API](https://mozilla.github.io/pdf.js/api/draft/api.js.html)

## Confirmed decisions

| Decision | Recommendation | Status |
| --- | --- | --- |
| Center layout | Question above PDF on desktop; Question/Paper tabs on narrow phones; retain visible timer/dock | User confirmed |
| Navigation | New questions open the cited page; zoom/browsing are local, with Return to citation | User confirmed |
| Formats | Original PDF viewer first; DOCX/TXT/Markdown keep extracted-text display | User confirmed |
| Access/lifetime | Joined room members may browse the whole PDF; private retention only while the room exists | User confirmed |
| Highlight certainty | Highlight only a confidently matched citation; otherwise show page and exact quote with a written fallback | User confirmed |
| Controls | Page navigation, zoom, Fit width, Return to citation and expanded reading; defer PDF downloads | User confirmed |
| Storage | Private temporary disk; configurable 110 MB per-room/500 MB global original-byte caps; reject capacity failures during creation and clean up with room lifecycle/startup | User confirmed |
| Browsing continuity | Keep page/zoom through same-question updates and reconnect; new questions follow PDF citations; code citations retain code display; document selector for multiple PDFs | User confirmed |
| Verification/delivery | Full offline gates, authenticated file/cleanup and mocked two-client tests, responsive/keyboard local preview; installed-device checks reported separately; no publication yet | User confirmed |

## Consolidated behavior

The central desktop card keeps the question above the original PDF. Narrow phone
layouts use Question/Paper tabs while the existing header timer, compact seat
strips and answer/chat dock remain accessible. The expanded reading view retains
a clear exit and access to the timer and answering controls. Follow the existing
black-and-white theme with visible keyboard focus and labelled controls.

Each new defense turn with a PDF citation selects its document and one-based
physical page. Individual defenders may browse, zoom and choose another PDF;
Return to citation restores the grounded page. Same-turn clarifications, answer
probes, vote/chat updates and reconnect preserve that personal reading position.
New-turn navigation does not force a phone user out of the Question tab. Code
citations remain the current code excerpt, with paper browsing available
manually. DOCX/TXT/Markdown keep their existing extracted-text presentation.

The server-owned exact extracted quote stays available with filename, PDF page
and extracted-line label. The extracted line number is not presented as a visual
PDF line number. Highlight only a confident, unambiguous match on the cited
page; ambiguous or absent matches show “Precise highlight unavailable” beside
the unchanged quote. Clear old highlights when the citation changes. A visual
match establishes where an excerpt appears, not whether the AI interpretation
is correct. Figures and equations become visible to defenders; the AI still
receives the existing extracted-text context.

Retain only validated original PDFs in private temporary storage, outside static
assets. Count actual original bytes with per-room and global reservations so
concurrent creations cannot exceed the caps. Defaults are 110,000,000 bytes per
room and 500,000,000 bytes server-wide, configurable by the operator. Existing
10 MB/file, 100-page, extracted-text, file-count and HTTP upload bounds remain.
Report retention-capacity errors before a room is published. Release reserved
bytes and temporary files on invalid, cancelled or failed creation; release
retained files with room closure/expiry. Server restart invalidates rooms and
removes orphan originals; startup cleanup must not remove another active service
instance's files during deployment handoff. Restarting a defense within the same
room retains that room's original PDFs.

Only authenticated joined room members may retrieve originals. Hosts also need
the existing verified owner account. Use opaque document IDs, header-based
authorization, same-origin delivery and no-store responses. Never put player
tokens in document URLs or grant access using a room code alone. Metadata in
snapshots supports citation/document selection and reconnect; binary contents,
storage paths and private authentication values stay out of shared snapshots.

Load PDF.js when required, render the current page with selectable text, and
cancel obsolete loads/renders on document changes or unmount. Provide a visible
loading state, readable rendering errors and a retry that does not restart the
defense or lose answer drafts. PDF viewing adds no AI request. PDF downloading,
DOCX visual rendering, OCR and AI figure interpretation are deferred.

## Proposed local implementation checkpoints

1. Retain validated originals with bounded storage and authenticated delivery.
   Wire metadata and lifecycle cleanup without changing AI or defense flow.
2. Add the PDF.js center viewer, navigation/zoom/document controls, confidence
   matching and quote fallback; integrate existing phone tabs and reading view.
3. Complete verification, documentation and screenshots; present a working local
   preview before any requested source publication or deployment.

These checkpoints are planning guidance, not implementation tickets.

## Verification contract

- Backend offline checks: retain original bytes correctly; PDF/document IDs and
  page mappings; guest/host authorization, wrong-room and expired/closed access;
  no tokens/paths in snapshots; concurrent quota reservations; rejected/cancelled
  creation cleanup; room expiry/close, restart and orphan cleanup; reconnect.
- Frontend checks: PDF loading/error retry, current-page rendering, unique versus
  absent/ambiguous quote matching, citation changes, multiple documents, personal
  page/zoom continuity, code/non-PDF fallbacks, tabs and keyboard focus. Verify
  that answer drafts, reaction/clarification/probe display and timers retain their
  current behavior.
- Run the full Python suite with AI/Google/PayMongo mocked, React suite and
  production build. Complete mocked two-client research and mixed defenses,
  including a longer twelve-question run, reconnect, clarification, timeout,
  transcript and coaching. Distinguish mocks from actual PDF rendering evidence.
- Inspect actual fixture PDF rendering and screenshots at desktop, portrait and
  landscape sizes, including long questions, source lines, columns/repeated
  text, zoom, switching tabs and keyboard access. Use the existing room theme.
- Report live AI/provider, hosted and installed Android/iOS checks separately.
  They are not established by browser viewport tests. No deployment is part of
  this local checkpoint; frozen main and existing live service remain unchanged.

## Planning handoff

The canonical local specification is
[Central PDF viewer for research defenses](../.scratch/pdf-viewer/spec.md),
marked ready-for-agent. It preserves this confirmed plan and the accepted test
boundaries; implementation and ticket publication have not started.

The user confirmed that this consolidated scope matches the intended feature.
No original-file storage, PDF API or renderer has been implemented, and no user
visual review is claimed. The specification is ready; next workflow: To Tickets
and Implement when requested. The user's Q9 acceptance supplies the verification-scope
agreement; Q10 supplies final scope confirmation. Publication remains separate.

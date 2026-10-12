# Central PDF viewer for research defenses

Status: ready-for-agent

Created: 2026-10-13. Work branch: feature/question-first-room.

The user confirmed the consolidated plan and verification scope. This is a local
Markdown tracker specification. Implementation, user visual review, source
publication and deployment are separate steps.

## Problem Statement

Defenders can currently see an exact extracted quotation and its page location,
but cannot see the original uploaded PDF inside the defense room. They cannot
inspect the surrounding page, original layout, tables or figures while discussing
the panelist's question. Extracted reading order may differ from the visible
paper, especially with columns, so the text card alone can make citations hard
to locate and understand.

Simply embedding a PDF also risks crowding the question and answer controls on
phones. Defenders need readable questions, visible timers and convenient access
to the cited page without losing their own browsing position on every room update.
Original papers must remain private to joined room members, with bounded server
storage and cleanup matching the room's lifetime.

## Solution

Add an original-PDF viewer to the center of the existing flat web room. Keep the
question above the viewer on desktop; use Question/Paper tabs on narrow phones
while preserving the header, compact seat strips, timer and answer/chat dock.
Open the PDF's cited physical page for each new defense turn. Browsing, document
selection and zoom are personal, with a Return to citation action.

Show the existing server-resolved exact extracted quotation and location. Add a
visual highlight only when its occurrence can be matched confidently and
unambiguously on the cited page; otherwise display the page, quote and a clear
"Precise highlight unavailable" message. Keep other document formats and code
citations readable using their current extracted-text and code presentations.

Retain validated original PDFs privately in bounded temporary disk storage for
the room's lifetime. Deliver them only to authenticated joined defenders, with
the existing additional owner-account requirement for hosts. Verify the feature
locally, then present the working preview and screenshots before publication.

## User Stories

1. As a defender, I want to see the original uploaded PDF in the room, so that I can inspect the paper's actual appearance while answering.
2. As a defender, I want the question above the PDF on desktop, so that the panelist's request remains the main focus.
3. As a phone defender, I want Question/Paper tabs, so that each view has enough readable space.
4. As a phone defender, I want the timer, compact seat strips and bottom dock to remain accessible, so that reading does not prevent participation.
5. As a defender, I want each new PDF-grounded question to open its cited page automatically, so that I can locate the source quickly.
6. As a defender, I want physical page numbering distinguished from printed page labels, so that the displayed location is accurate.
7. As a defender, I want the exact extracted quotation beside the source location, so that I can compare it with the visible paper.
8. As a defender, I want extracted line numbers labelled as extracted lines, so that I do not mistake them for visible PDF line numbers.
9. As a defender, I want a highlight when the citation has a confident unique match, so that I can locate the passage precisely.
10. As a defender, I want a clear fallback when a match is absent or ambiguous, so that the app does not imply false precision.
11. As a defender, I want obsolete highlights cleared when the citation changes, so that a previous passage is not mistaken for the current source.
12. As a defender, I want previous/next page controls and a current-page count, so that I can examine surrounding material.
13. As a defender, I want zoom controls, so that small source text is readable.
14. As a defender, I want Fit width, so that a page can fit the available reading space.
15. As a defender, I want Return to citation, so that I can recover the grounded page after browsing.
16. As a defender, I want an expanded reading view with a clear exit, so that I can inspect a detailed page without getting stuck.
17. As a defender, I want the timer and answering controls accessible in expanded reading, so that I can still respond before the deadline.
18. As a defender, I want selectable PDF text, so that I can inspect wording directly.
19. As a defender, I want a document selector when multiple PDFs were uploaded, so that I can inspect all accepted papers.
20. As a defender, I want my page and zoom independent of other defenders, so that my browsing does not interrupt their reading.
21. As a defender, I want voting and chat updates to preserve my reading position, so that ordinary synchronization does not move the paper.
22. As a defender, I want same-question clarifications and answer probes to preserve my reading position, so that I can continue examining the same evidence.
23. As a defender, I want reconnect to restore my current reading state within the same room and turn, so that a network interruption does not erase my place.
24. As a phone defender, I want a new question to update the cited page without forcing me out of the Question tab, so that navigation remains predictable.
25. As a defender in a mixed defense, I want code citations to keep their existing code view, so that implementation evidence remains clear.
26. As a defender in a mixed defense, I want to browse accepted PDFs manually while a code citation is active, so that I can compare the implementation with the paper.
27. As a defender using DOCX, TXT or Markdown, I want the existing extracted-text view retained, so that the first PDF release does not reduce support for other papers.
28. As a defender, I want a visible document-loading state, so that I know why the paper has not appeared yet.
29. As a defender, I want a readable rendering error and local retry, so that a viewer failure does not require restarting the defense.
30. As a chosen defender, I want viewer navigation and retry to preserve my answer draft, so that I do not lose work while reading.
31. As a defender, I want viewing the paper to leave votes, deadlines and answer rules unchanged, so that the defense remains fair and synchronized.
32. As a defender, I want reactions, clarification display and answer probes preserved, so that the existing conversation flow continues to work.
33. As a keyboard user, I want labelled controls, visible focus and usable tab navigation, so that I can operate the viewer without a pointer.
34. As a keyboard user, I want expanded-view focus to return to its trigger on exit, so that I can resume navigating the room.
35. As a host, I want only joined defenders to retrieve original PDFs, so that a shared room code alone cannot expose the paper.
36. As a host, I want my owner account checked for original-document access, so that host access follows the existing authentication model.
37. As a guest defender, I want original-document access through my existing player identity, so that I do not need a Google account to participate.
38. As a host, I want files unavailable after room closure or expiry, so that access follows the room's lifetime.
39. As a host, I want restarting a defense run in the same room to retain its papers, so that I do not need to upload them again.
40. As a host, I want storage-capacity failures reported before a room is published, so that I can understand why creation failed.
41. As an operator, I want configurable 110 MB per-room and 500 MB server-wide original-byte limits, so that retained papers cannot grow without a bound.
42. As an operator, I want concurrent room creation to respect those limits, so that simultaneous uploads cannot overbook storage.
43. As an operator, I want failed or cancelled creation to remove temporary originals and reservations, so that unsuccessful uploads do not consume capacity.
44. As an operator, I want closure and expiry to clean up retained originals, so that finished rooms release their storage.
45. As an operator, I want server startup to remove orphaned originals safely, so that papers from lost rooms do not accumulate.
46. As an operator, I want deployment handoff cleanup to leave the active service's files intact, so that a replacement process does not destroy ongoing access.
47. As a defender, I want citation metadata without server paths or private tokens, so that shared room state does not disclose file storage or credentials.
48. As a defender, I want private document requests to avoid reusable public links, so that authorization is checked when originals are fetched.
49. As a defender, I want the viewer to render the current page rather than every page at once, so that long papers remain practical on phones.
50. As a defender, I want obsolete document loads and page renders cancelled, so that rapidly switching documents cannot display an old page as the current one.
51. As a host, I want figures visible to people without implying that the AI interprets them, so that the viewer's scope is understood correctly.
52. As a maintainer, I want existing upload, extracted-text and research policies preserved, so that the viewer does not silently change defense eligibility or cost.
53. As a maintainer, I want authenticated room and whole-room UI tests to verify the feature, so that internal refactoring does not invalidate behavior checks.
54. As a reviewer, I want local screenshots and a working preview before publication, so that I can assess real PDF readability rather than only mock output.

## Implementation Decisions

- Reuse the existing room coordination, extraction, citation resolution,
  recipient-specific snapshots, account checks and player-token model. Keep
  the document store separate from AI-facing extracted project-file records.
  Do not move lifecycle ownership back into transport handlers.
- Add a bounded private original-document store using temporary disk storage
  outside public/static assets. Retain only validated original PDFs associated
  with an accepted room; use generated identifiers and storage names rather
  than uploaded filenames as filesystem paths.
- Preserve the current 10,000,000-byte research-file limit, 100-page PDF limit,
  combined 600 KB extracted context and 100-file bounds, and aggregate HTTP
  upload limits. Encrypted, invalid, scanned-only and unreadable-page PDF
  rejection remains unchanged. The viewer does not expand accepted formats.
- Default retained-original quotas to 110,000,000 bytes per room and 500,000,000
  bytes across the server. Make them operator configurable. Reserve actual
  original bytes atomically across concurrent creations; reject exceeded
  limits clearly before publication. Roll back reservations and temporary
  files when parsing, room creation or publication fails or is cancelled.
- Tie retention to the room, not the defense run. Run restart keeps originals;
  room closure, expiry and reclamation remove them and release quota. Service
  shutdown and startup orphan removal respect the existing exclusive service
  ownership/handoff mechanism; a new process must not purge another active
  service's files. No permanent document store or database migration is needed.
- Add a read-only, same-origin HTTP original-document delivery interface scoped
  to room and opaque document identity. Require a valid joined player token in
  a request header. Hosts additionally require the verified owner account.
  Missing/invalid credentials, wrong-room documents, expired or closed rooms
  must not return bytes. Room codes and guessed document IDs are insufficient.
- Return PDF content with correct media type and no-store caching semantics.
  Keep player tokens out of URLs, links, logs and shared metadata. Recheck room
  lifetime for retrieval and handle a cleanup/read race without exposing a
  document from another room or returning a misleading success.
- Add safe PDF metadata to existing room snapshots: opaque document ID, accepted
  filename, physical page count and source association needed for citation
  resolution. Resolve citation-to-document/page on the server from accepted
  extraction locations. Include metadata in reconnect views without a new AI
  call; never include original bytes, storage paths or private credentials.
  Preserve compatibility with rooms and fixtures lacking PDF metadata.
- Use Mozilla PDF.js for browser rendering, with a bundled worker and lazy
  loading. Render the selected page with a selectable text layer, rather than
  rendering an entire document eagerly. Handle document/page changes and
  component teardown by retiring obsolete loads and renders.
- Integrate the renderer into the existing central question area and grayscale
  theme. Desktop keeps the question above the PDF. Narrow phones use accessible
  Question/Paper tabs and internal scrolling, keeping the header, seat strips
  and answer/chat dock accessible. Expanded reading has a clear exit and keeps
  timer and answering access; keyboard exit restores focus to its trigger.
- Supply previous/next page, page count, zoom, Fit width, Return to citation,
  document selection and expanded reading controls. Disable unavailable page
  actions at document boundaries and expose meaningful accessible labels.
- Store navigation as personal viewer state. For a new defense turn with a PDF
  citation, select its document and one-based physical page. Preserve page and
  zoom through same-turn clarification, probe, voting, chat and reconnect;
  reconnect to a newer turn follows the new citation. Do not synchronize
  personal navigation to other clients or force a phone tab switch.
- Keep code excerpts prominent for code citations, with manual paper browsing
  available in mixed rooms. DOCX/TXT/Markdown retain their current extracted-text
  display. Viewer navigation does not replace question or transcript content.
- Preserve the server-owned exact quote and extracted-line label. A highlight
  requires a confident, unique occurrence on the cited physical page, mapped
  to the rendered text geometry. Whitespace normalization must not invent an
  occurrence. Repeated, ambiguous or missing text uses the unchanged quote and
  "Precise highlight unavailable" fallback; never guess coordinates from an
  extracted line number. Clear stale highlights on citation/document changes.
- Expose loading, failure and document retry states. Retry only document loading
  or rendering; it must not create a new question, invoke AI, restart the defense,
  consume credits or clear an answer draft. A failed viewer leaves the grounded
  quote and question usable. Reject obsolete load completions after navigation.
- Preserve existing reaction timing, clarification presentation, probes, role
  policies, coverage, voting, timers, charging, chat privacy, retries, transcript,
  coaching and socket reconnect behavior. No original PDF bytes are sent to AI;
  visual availability does not imply AI understanding of figures or equations.
- Deliver local runnable checkpoints for original retention/delivery, central
  rendering/controls and integrated verification/review. Preserve unrelated
  files and work. Source publication and deployment require later instructions;
  frozen main and the current live release remain untouched.

## Testing Decisions

- The user accepted these boundaries in planning Q9 and confirmed the complete
  scope in Q10. Prefer the existing authenticated HTTP/WebSocket room flow as
  the highest backend seam, and existing whole-room React behavior as the UI
  seam. The new original-document HTTP resource extends that same app boundary;
  it does not require a new test-only production control surface.
- Good tests assert externally visible behavior: received PDF bytes, denied
  access, unchanged citations, capacity/error outcomes, restored navigation,
  visible controls, retained drafts and synchronized defense state. Avoid
  asserting private store layouts, internal render-call counts or implementation
  details that can change without affecting users.
- Prior art includes authenticated room-creation/guest/host checks, fake-clock
  room-coordination and lifecycle races, upload admission and extraction tests,
  mocked multi-client protocol defenses, and room/question/citation React tests.
  Reuse their account fixtures and controlled AI/provider completions.
- Exercise original-byte retention and authenticated retrieval through the app:
  host with correct/expired account, valid guest, missing/invalid player token,
  wrong room/document, guessed IDs, closed/expired room and reconnect. Assert
  media type, no-store delivery and that snapshots omit paths/tokens/bytes.
- Use temporary storage and small configured quotas to verify boundary acceptance,
  concurrent reservations, clear creation errors, failed/cancelled parsing and
  creation rollback, closure/expiry cleanup, same-room run restart retention,
  startup orphan cleanup and active-service handoff protection. Test cleanup
  races through observable access/capacity outcomes.
- Use real readable synthetic PDFs for original-byte/page mapping, multiple
  documents and unchanged invalid/encrypted/scanned/unreadable/size rejection.
  Keep AI, Google and PayMongo mocked for all offline backend defenses.
- Verify room UI behavior for citation navigation, boundaries, zoom/Fit width,
  Return to citation, document selection, tabs, expansion/focus return, loading,
  rendering errors/retry and stale-result suppression. Assert page/zoom survive
  same-turn updates and reconnect while a new turn follows its PDF citation.
- Test matching with unique quotes, repeated text, absent text, line wrapping,
  columns and extracted text differing from visual order. Assert exact quote
  preservation and truthful fallback; a passing mocked text-layer test is not
  proof of real PDF geometry.
- Combine behavior tests with actual PDF.js rendering in a browser using fixture
  PDFs and the production worker build. Inspect selectable text, highlight
  position, current-page rendering and worker loading. Capture desktop,
  portrait and landscape screenshots with short/long questions and documents.
- Complete mocked two-client research and mixed defenses, including a
  twelve-question run, distinct personal browsing, voting, clarification,
  probe, timeout, reconnect, transcript and coaching. Confirm the viewer does
  not alter synchronization, deadlines, accepted answers or charges.
- Run the full Python suite with providers mocked, React suite and production
  build. Check keyboard-only operation, visible focus, readable contrast,
  internal scrolling and no clipped controls in desktop and phone layouts.
- Present screenshots and the working local screen before publication. Record
  offline tests, actual browser rendering, user visual review, live AI/provider,
  hosted and installed Android/iOS evidence separately. Browser viewport checks
  alone cannot establish installed WebView behavior.

## Out of Scope

- PDF downloading, generic native file export and native launcher changes.
- Original DOCX rendering, OCR, scanned-document acceptance, AI figure vision,
  reliable equation interpretation or examination of every paper sentence.
- Guaranteed visual highlighting where extraction cannot be matched reliably.
- Shared/synchronized browsing, room-code-only access, public PDF links or stored
  defense/document history beyond the room's existing lifetime.
- Cloud/object storage, permanent paper retention, payment/schema changes,
  upload-limit expansion, new AI requests or new question-generation policies.
- Broad visual redesign, reinstating a 3D room, changing conversation timing,
  voting/answer deadlines, turn budgets, credits, prices or guest sign-in rules.
- Git push, production deployment, frozen-main modifications or claims of actual
  hosted/provider/installed-device success based on mocks.

## Further Notes

The confirmed planning record is
[Central PDF viewer](../../docs/PDF_VIEWER_PLAN.md). It supplies decisions rather
than prototype code; no throwaway viewer was implemented. The existing document
card is an extracted-text presentation, so a successful visual review requires
real fixture PDF rendering as well as mocked room flow.

A room may contain successive defense runs. Original-document lifetime follows
the room; a server restart still loses in-memory rooms. Existing ephemeral-room
behavior is not converted into durable room storage by this feature.

A grounded citation confirms an excerpt's source. A confident highlight adds
visual location, not proof that the AI interpreted the research correctly.
Retain that distinction in UI copy and the verification handoff.

The next step is a dependency-ordered local ticket breakdown. Implementation
must leave the application runnable at each checkpoint and preserve unrelated
local files and the frozen main branch.

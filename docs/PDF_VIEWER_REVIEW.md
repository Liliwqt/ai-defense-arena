# Central PDF viewer local review

Implemented locally on `feature/question-first-room`, against the user-approved
review baseline `ea4c671`. Publication and deployment require a later request.
The approved plan and canonical specification remain under
`docs/PDF_VIEWER_PLAN.md` and `.scratch/pdf-viewer/spec.md`.

## Open the local screen

The isolated fixture server is running at
[http://127.0.0.1:8842/__fixture/login](http://127.0.0.1:8842/__fixture/login).
If it has stopped, run these commands from the repository root:

```bash
(cd game && npm run build)
.venv/bin/python -m tests.pdf_viewer_preview
```

The wrapper binds only to loopback, uses disposable synthetic accounts and two
original PDFs, and removes external-provider credentials from its own process.
Its login route is absent from the production app. It creates a fresh room on
each visit; keep that host tab open and join from another browser using its room
code. The synthetic clock freezes server progression for reading review; the
browser countdown is illustrative. Do not submit answers in this visual fixture.

Use `?case=repeated` for repeated text in two columns and `?case=long` for a longer
question. Other app states are available through the existing `/?preview=1`
fixtures, which use synthetic room snapshots rather than an original PDF.

## Review the experience

- Check the question, unchanged extracted quote and filename, then open Paper on
  a phone. The PDF uses physical pages; extracted line numbers are separate.
- Browse pages/documents and change zoom. Return to citation restores the current
  question's PDF page. Refresh/reconnect retains personal page and zoom; another
  client's browsing is independent. A new defense turn follows its new citation.
- Try expanded reading and Escape. Focus returns to its trigger; timer, seats and
  answer dock stay available. On short landscape screens the smaller central
  region scrolls internally; paper controls and the full page are reachable by
  scrolling that region.
- A unique mapped text run gets a real geometry highlight. Repeated, rotated,
  split or unmappable text keeps the exact quotation with **Precise highlight
  unavailable**. This conservative first release does not guess cross-run text
  coordinates or claim that a citation proves the AI's interpretation.
- Only joined identities can read originals. Host access also requires the owner
  account. Closing/expiring the room or stopping the service removes its private
  files. Restarting a defense inside the room retains them. Local paper retry
  does not generate a question, spend credits or clear an answer draft.

## Evidence

Provider-mocked protocol checks complete twelve-question research and mixed
PDF defenses, preserving exact citations, original bytes, voting, reactions,
timeouts, retry, clarification, same-question probes, reconnect and coaching.
Existing mocked code four/eight-turn checks remain in the Python gate. Private
HTTP/storage checks cover guest/owner access, expiry, wrong-room identifiers,
concurrent byte reservations, cancelled parsers, invalid uploads, failed
publication, retained originals on run restart and exclusive startup cleanup.
React checks mock the PDF API; they cover navigation, stale loads, precision,
retry and keyboard focus alongside the existing room behavior.

Actual local Chromium rendering uses the production PDF.js worker, not a mocked
PDF API. Two independent browser contexts joined the same room: the guest browsed
page 3 at 125% while the host stayed on page 2; reload retained the guest position
and Return to citation restored page 2. An intentionally aborted document request
showed local recovery and retained the answer draft through retry, with no page
exception. Unique highlight left edges matched rendered text; width differences
were under 0.02 CSS pixels at 100%, 125% and Fit width. A two-column repeated quote
produced zero markers and the written precision fallback. Desktop 1440×900,
portrait 390×844 and landscape 844×390 checks had no horizontal body overflow;
keyboard tabs, expanded-exit focus and internal long-question scrolling worked.

Actual AI conversation quality, hosted/provider verification, physical second
devices and installed Android/iOS WebViews were not tested by this checkpoint.
No user visual approval is recorded. All screenshots contain synthetic fixture
content only.

## Screenshots

| View | Screenshot |
| --- | --- |
| Desktop question and paper | [Desktop](review/pdf-viewer/pdf-viewer-desktop.png) |
| Expanded reading | [Expanded](review/pdf-viewer/pdf-viewer-desktop-expanded.png) |
| Portrait question | [Question tab](review/pdf-viewer/pdf-viewer-portrait-question.png) |
| Portrait paper | [Paper tab](review/pdf-viewer/pdf-viewer-portrait-paper.png) |
| Landscape question | [Landscape question](review/pdf-viewer/pdf-viewer-landscape-question.png) |
| Landscape paper | [Landscape paper](review/pdf-viewer/pdf-viewer-landscape-paper.png) |
| Repeated-text fallback | [Ambiguous match](review/pdf-viewer/pdf-viewer-ambiguous.png) |
| Long question on desktop | [Long desktop](review/pdf-viewer/pdf-viewer-long-desktop.png) |
| Long question on phone | [Long portrait](review/pdf-viewer/pdf-viewer-long-portrait.png) |

The PDF library is lazy-loaded, so its approximately 542 KB JavaScript chunk and
1.32 MB worker do not join the initial approximately 284 KB application chunk.
Local font/CMap/WASM support adds static build assets. Vite reports the expected
large lazy-chunk warning; it is not a failed build. Downloading original PDFs,
OCR, AI figure interpretation and faithful DOCX rendering remain outside scope.

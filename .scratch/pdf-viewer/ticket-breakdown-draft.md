# PDF viewer ticket breakdown — approved

Date: 2026-10-13. Branch: feature/question-first-room.

Source: the confirmed Central PDF viewer specification. The user approved this
four-ticket breakdown on 2026-10-13; separate ready-for-agent tickets are now
published in the local tracker. Approval did not start implementation or
authorize source publication. The parent specification remains unchanged.

## Approved sequence

1. **Private cited-page viewing**
   - **Blocked by:** None — can start immediately after ticket publication.
   - **Delivers:** A joined defender sees the original cited PDF page in the
     central room card through authenticated, bounded room-owned storage.
     Desktop keeps the question above the page; a basic phone Question/Paper
     switch preserves the timer and dock. The exact extracted quote remains
     usable while loading or when rendering fails.
   - **Acceptance scope:** Validated PDF retention; configurable 110 MB/room and
     500 MB/server byte reservations; creation rollback; safe closure/expiry,
     shutdown and startup orphan cleanup; run restart retains room files.
     Host-owner and guest-token document access, opaque IDs and safe reconnect
     metadata; no public paths, token URLs or cached private originals.
     Lazy PDF.js/worker loading, current-page canvas plus selectable text,
     local rendering retry and cancellation of obsolete results. Preserve
     existing code/non-PDF excerpts, citations, answer drafts and AI flow.
   - **Verification:** Authenticated app flows, capacity/lifecycle races,
     quote/failure UI checks and actual fixture-PDF page rendering. This slice
     includes its safe storage seam rather than an isolated backend-only
     prefactor. Browsing controls and visual highlighting follow later.

2. **Personal paper browsing and reading controls**
   - **Blocked by:** 01 — Private cited-page viewing.
   - **Delivers:** Defenders browse any accepted PDF independently with previous/
     next page, page count, zoom, Fit width, Return to citation, document
     selection and expanded reading. Phone tabs and expanded reading remain
     usable while the question timer and answering controls are accessible.
   - **Acceptance scope:** All reading controls are labelled and keyboard
     accessible; page actions respect boundaries; expanded-view exit restores
     focus. Same-turn clarifications/probes, voting/chat updates and reconnect
     preserve personal page/zoom. New PDF-cited turns follow the server-owned
     document/page without forcing a phone tab switch. Code-cited turns retain
     code presentation with manual paper browsing. Viewer retry, navigation
     and expansion do not clear drafts, spend credits or invoke AI.
   - **Verification:** Whole-room UI interactions plus two distinct clients'
     independent navigation and reconnect, actual multi-page/multi-document
     fixtures, desktop/portrait/landscape scrolling and keyboard checks.
     Builds on the authenticated delivery and page rendering completed in 01.

3. **Confident citation highlighting and truthful fallback**
   - **Blocked by:** 02 — Personal paper browsing and reading controls.
   - **Delivers:** A uniquely matched server-owned citation is highlighted on
     the rendered physical page, including after zoom/Fit width. Ambiguous or
     missing matches keep the page and unchanged quote visible with
     “Precise highlight unavailable”.
   - **Acceptance scope:** Match only on the cited page, map text to its actual
     rendered geometry and never infer coordinates from extracted line numbers.
     Check repeated text, wrapping, columns and extraction-order differences;
     retain exact quoted text and extracted-line labels. Clear stale highlights
     on citation/document changes and suppress late render/match results.
     Browsing another document/page must not show a highlight from the prior
     citation. A source match does not imply the AI interpretation is correct.
   - **Verification:** Observable unique/absent/ambiguous outcomes and real
     fixture-PDF highlight geometry at multiple zooms and screen sizes.
     Depends on 02 because highlights must follow the completed reading
     controls and viewport changes, not an interim fixed-scale renderer.

4. **Integrated defenses and local visual handoff**
   - **Blocked by:** 03 — Confident citation highlighting and truthful fallback.
   - **Delivers:** The complete viewer is verified in running multi-client
     research/mixed defenses and presented locally with screenshots and a
     clear review guide before any publication.
   - **Acceptance scope:** Full Python/React gates and production build; mocked
     two-client research/mixed defenses including a twelve-question run,
     personal browsing, voting, clarification, probe, timeout, reconnect,
     transcript and coaching. Check retained drafts, exact citations,
     authorization/lifecycle/quota behavior and unchanged timers/charges.
     Inspect real fixture-PDF production rendering, worker loading,
     selectable text/highlight geometry and responsive keyboard behavior
     with short/long questions. Update user documentation and handoff evidence.
   - **Verification:** Name each check, distinguish provider-mocked flow from
     actual local PDF rendering, and present desktop/portrait/landscape captures
     plus the local preview. Installed Android/iOS, live providers and hosted
     checks remain separate evidence. User visual review remains pending until
     performed. No push, deployment, downloads or frozen-main changes.

## Dependency rationale

The graph is **01 → 02 → 03 → 04**. Only 01 is initially unblocked. Original
retention is useful only when a room member can actually view it, so 01 spans
storage, authorization, metadata and a minimal real page UI. Later tickets
reuse the same delivery boundary and add complete user capabilities rather
than splitting layers. No database migration or broad expand–contract refactor
is required by the confirmed scope.

Each ticket includes behavior checks and leaves the app runnable. The last
ticket assembles cross-feature evidence; it does not defer authentication,
cleanup or ordinary regression testing until the end.

## Publication handoff

All four slices and their blocking edges were accepted without changes.
Separate issue files are published in dependency order; ticket 01 is the only
initially unblocked task. The parent specification remains unchanged.
Implementation, visual review, Git push and deployment are separate steps.

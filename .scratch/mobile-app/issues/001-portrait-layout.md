# Portrait defense room layout

Status: ready-for-agent

## Goal

Adapt the existing web room to portrait with compact panelist/defender strips
around the question and exact citation. Retain current components/theme and
support room creation/joining in phone browsers and Android/iOS WebView
wrappers that load the website URL.

## Primary sources

- Canonical specification: `.scratch/mobile-app/spec.md` (ready-for-agent).
- Discovery/history: `docs/MOBILE_APP_PLAN.md`.
- Prototype: local branch `prototype/mobile-portrait`, current commit `b18be90`
  (initial capture `4f70bc2`), based
  on feature release `48e3ff7` rather than frozen main.
- Worktree: `/tmp/arena-mobile-portrait`; run
  `npm --prefix /tmp/arena-mobile-portrait/game run prototype:mobile`.
- Preview: http://127.0.0.1:8775/?prototype=mobile&research=1&clarify=1&variant=A.
- Prototype usage/evidence: `game/src/components/prototypes/README.md` on that branch.

## Next step

The concrete spec is published. Use To Tickets to split website implementation
and verification from URL-loading wrappers, then Implement the website
checkpoint first. This existing pointer is not the complete multi-ticket set.
A/B/C selection is not required. The prototype remains historical evidence only
and does not establish native auth, synchronized rooms or keyboard behavior.

## Comments

2026-10-06: Three dev-only layouts captured locally. Existing 212 Python tests
(providers mocked), 156 React tests and build pass. Local browser checks cover
variant switching, typing/draft preservation, sheet focus/Escape, mock voting,
chosen-speaker waiting, chat and answer/transcript. Production assets are
unchanged. Rewrite the selected design as production code after confirmation;
do not promote throwaway code directly. Preserve unrelated changes and frozen
main. Publication and native integration remain separate work.

2026-10-06: User clarified that the portrait WebView should feel like the
current website. Updated all layouts to reuse its shared theme tokens and
refreshed the eight captures in `b18be90`; structures still differ for review.
Production build remains byte-identical. Local viewport/overflow checks passed;
no native-device or backend-connected mobile session is claimed.

2026-10-06: User corrected the scope explicitly: WebView loads the current
website URL. The next workflow is To Spec → To Tickets → Implement, starting
with responsive changes to the actual React page. Do not promote the prototype
or require a variant choice. Prior A recommendation is superseded.

2026-10-06: To Spec completed. Canonical spec and this pointer are ready-for-agent;
the user confirmed testing through the existing web room, mocked two-client
server flow and installed Android/iOS WebViews. No implementation or publication
occurred. Dependency-linked ticket breakdown remains the next workflow step.

# Mobile app discovery

Status: specification published locally as ready-for-agent; implementation not started.
Date: 2026-10-06. Working branch: `feature/question-first-room`.

The canonical specification is [Portrait website and downloadable WebView apps](../.scratch/mobile-app/spec.md).
This document retains discovery/history; use that spec for implementation.

## Settled requirements

- Target Android and iOS together, as selected by the user.
- Share portrait support between the installed apps and phone browsers, as
  selected by the user.
- Support both creating rooms and joining existing rooms.
- Use compact panelist and defender strips around the central reading card.
- Preserve the current website's theme; the mobile work rearranges the room
  for portrait rather than creating a separate visual identity.
- Adapt the existing React page for portrait. The user clarified that a WebView
  loads the website URL and should display that same app; a separate design or
  bundled replacement frontend is not the requested direction.
- Provide an embedded web experience with a portrait layout that prioritizes
  reading the question and exact citation.
- Retain the existing flat room direction. The central reading area is the
  question card; a literal 3D table is not part of the current app.

## Delivery direction

- First make the current website responsive in portrait, retaining its existing
  components, theme, backend, accounts and room protocol.
- Then add thin Android/iOS WebView wrappers loading the website URL. Wrapper
  tooling, native sign-in handoff and distribution still need a concrete spec;
  Capacitor is an earlier candidate, not a settled framework choice.
- Provide accessible voting, answer and team-chat controls below the reading
  card; keep the question visible while typing, with optional editor expansion.

Desktop behavior, AI question flow, server timers, citations and access rules
remain outside the portrait layout change.

## Next recommended workflow

1. To Spec completed: the local specification defines the existing-page
   portrait change, thin URL-loading shells and acceptance checks.
2. Next, To Tickets: separate responsive website, local/device verification and
   URL-loading wrappers with their authentication/file integration work.
3. Implement: start with portrait support in the existing web page, then review
   the real app locally before publication or native packaging.

Selecting A/B/C is no longer a prerequisite. The user rejected the premise of a
separate mobile design; those experiments stay historical reference only.
The user confirmed the existing-page, mocked two-client and installed-WebView
testing boundaries. Framework/setup speculation in these historical notes is
superseded by the specification's platform-native shell decisions.

## Technical facts and investigation

- The current app blocks narrow portrait screens using `RotatePrompt` and an
  orientation media query in `game/src/index.css`. The question body already
  scrolls internally, with code citations preserving exact source text.
- HTTP/account requests and WebSockets currently assume a shared app/server
  origin. A bundled native app needs an explicit transport and session design;
  installing a wrapper alone does not establish an authenticated host session.
- Google prohibits OAuth authorization in embedded user agents. Native or
  external-browser sign-in needs a verified return/session handoff; browser
  and WebView cookies must not be assumed to be shared.
  [Google OAuth policies](https://developers.google.com/identity/protocols/oauth2/policies).
- Capacitor supports Android, iOS and web. Local iOS builds require macOS and
  Xcode; Android needs Android Studio and the SDK. Tool availability in this
  workspace was checked separately.
  [Capacitor environment setup](https://capacitorjs.com/docs/getting-started/environment-setup).
- Read-only tooling inspection found Linux, Node 24/npm 11, JDK 17, `adb`,
  Android API 36 and build tools. Android SDK command-line tools, a standalone
  Gradle command and emulator were not available; no Xcode/iOS build tools were
  available. This is not evidence that a native build succeeds.
- No native project/configuration or Capacitor dependency exists yet. Current
  account requests/upload transport use relative URLs; host WebSocket checks
  also require the configured web origin. See `accounts.py:90`,
  `game_server.py:611` and `game/src/hooks/useRoomSocket.ts:36`.
- File picking, transcript downloads, external checkout return and app
  suspension/reconnect need native-device checks after the approach is settled.

## Boundaries and evidence

Executable prototype changes are isolated from the working app on local
`prototype/mobile-portrait`, current commit `b18be90` (initial capture `4f70bc2`),
based on feature release `48e3ff7`.
The worktree is `/tmp/arena-mobile-portrait`. No native packages, sign-in changes,
mobile builds or deployment. Existing Account UI/upload-progress edits,
unrelated files and screenshot deletions are preserved. Main remains frozen.

## Historical prototype reference

This experiment is preserved on its own branch; it is not the implementation
target or a visual-selection gate after the user's scope correction.

Open http://127.0.0.1:8775/?prototype=mobile&research=1&clarify=1&variant=A.
The floating arrows switch A (Reading deck), B (Document desk), and C
(Conversation). All reuse the current site's shared theme tokens following the
user's clarification. Controls shows full mock state and toggles long questions,
clarification, research/code evidence, voting and reduced keyboard space.
Local answering/chat/transcript interactions use memory only; there are no
backend calls or real room mutations. Static countdowns are labelled fixtures.

Start with one command if stopped:

```bash
npm --prefix /tmp/arena-mobile-portrait/game run prototype:mobile
```

Screenshots and detailed usage/evidence are captured on the prototype branch
under `screenshots/mobile-prototype-*` and
`game/src/components/prototypes/README.md`. The implementation pointer is
`.scratch/mobile-app/issues/001-portrait-layout.md` in the original workspace.

Verification: existing 212 Python tests (providers mocked), 156 React tests and
production build passed in the isolated worktree. Production JS/CSS assets are
identical to the published baseline, confirming the dev-only prototype is
excluded. Local browser layout/interactions were checked at 390x844, 320x568,
667x375 and 1365x900; no horizontal page overflow. Keyboard behavior is simulated,
not verified on physical devices or native WebViews. No user visual approval or
winning layout is claimed. The earlier A recommendation is superseded by the
direction to adapt the current website directly.


## Implementation checkpoint — 2026-10-06

User approved all eight tickets. The actual website portrait changes, native
URL-loading projects, one-time server-verified login handoff and native summary
integration are now implemented locally. Android debug APK builds and verifies;
iOS build/signing and installed-device/provider checks remain prerequisites.
See [mobile build and evidence guide](../mobile/README.md) and the current log.
Earlier tool discovery said no emulator; later inspection found its SDK binary,
but no configured AVD or connected device. No native installation is inferred.
This is not published or deployed, and no new mobile design is being selected.

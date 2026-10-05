# Mobile delivery ticket breakdown — draft for approval

Date: 2026-10-06
State: proposed; individual tickets have not been published.
Source: the canonical portrait website and downloadable WebView specification.

These are complete, verifiable increments, not separate frontend/backend/test
tasks. Each increment includes its own appropriate checks and documentation.
No broad prefactor is needed before starting: the existing page, room transport,
account boundaries and tests already provide the seams. Any small supporting
refactor stays with the behavior that requires it.

## 01 — Use the current website in portrait

**Blocked by:** None — can start immediately.

**What it delivers:** Hosts and defenders can use the actual existing website
upright, with compact seats, readable questions/citations and accessible voting,
answers, chat, setup, Account, Transcript and coaching. Desktop users retain the
same experience. This is the first local review checkpoint.

- [ ] Portrait is usable without a blocking rotate prompt; current theme and
  components are retained, with no replacement mobile page or prototype import.
- [ ] Four panelists and four defender positions remain identifiable around
  the question; complete role names, display names, status and chosen defender
  are available accessibly.
- [ ] Long questions, lead-ins and clarifications remain reachable in the
  internally scrolling reading area. Exact code/document citations retain
  their existing fidelity, indentation and appropriate horizontal scrolling.
- [ ] Vote/Answer and Team Chat remain in the bottom dock. Keyboard/visible-
  viewport adaptation keeps typing/submission reachable and preserves the draft
  through tab changes and orientation within the current turn.
- [ ] Current host setup/uploads/research map/budget and Account/Transcript
  drawers are usable by keyboard/touch without clipped essential controls.
- [ ] A mocked two-client code defense and research/mixed defense exercise
  voting, clarification, timeout, retry, answers, reconnect, transcript and
  coaching with one portrait and one desktop client. No rule/protocol changes.
- [ ] Existing offline Python/React gates and production build pass. Local
  desktop/portrait/landscape/enlarged-text captures are presented for review;
  actual physical keyboard checks remain explicitly distinct.

**Spec coverage:** website behavior in stories 1–34 and 39–42; native delivery
and integrations are completed below rather than claimed by browser checks.

## 02 — Join a shared room from an Android WebView app

**Blocked by:** 01 — Use the current website in portrait.

**What it delivers:** A test-installable Android shell loads the same configured
HTTPS website and lets a guest join, vote, answer and chat with browser teammates.
The shell provides page-load retry, safe navigation and resume/reconnect.

- [ ] Repeatable Android build and test APK use the configured website URL;
  no bundled React frontend or separate room service is introduced.
- [ ] Installed-shell guest participation is verified against the existing
  room/server boundary, with external providers mocked for automated checks.
- [ ] Initial loading/failure/retry are truthful and distinct from room/AI
  state. The room snapshot restores on resume without resetting deadlines or
  falsely preserving a disconnected chosen defender.
- [ ] Trusted-site navigation stays embedded; unrelated HTTPS links open
  externally, unsafe schemes/certificate errors are rejected and untrusted
  pages receive no native execution bridge.
- [ ] Back, keyboard, safe areas and orientation do not silently leave/restart
  the defense or discard same-turn drafts. Website storage/guest reconnect work.
- [ ] Build/install evidence and limitations are recorded. Host Google return,
  native upload/export and provider checkout are not claimed complete yet.

**Environment prerequisite:** compatible Android build tools and a test device
or emulator. This prerequisite does not gate ticket 01 or iOS work.

## 03 — Join a shared room from an iOS WebView app

**Blocked by:** 01 — Use the current website in portrait.

**What it delivers:** A test-installable iOS WKWebView shell loads the same
configured HTTPS website and lets a guest participate with browser teammates,
including safe navigation, page retry and resume/reconnect.

- [ ] Repeatable iOS project/build and installation guidance use supported
  signing/provisioning. Verify a signed installable test artifact when those
  facilities are available; source or an unsigned archive is not success.
- [ ] Installed-shell guest joining, vote/answer/chat and reconnect use the
  existing server and room snapshots; no alternate frontend/service is added.
- [ ] Truthful page loading/retry, allowlisted internal navigation, external
  links and rejection of unsafe schemes/certificate errors work.
- [ ] Safe areas, actual keyboard/orientation and lifecycle retain accessible
  controls and same-turn draft/state without changing server deadlines.
- [ ] Website storage persists appropriately for reconnect, and no unrelated
  site receives a native bridge. Build/device evidence is separate from browser
  captures or the Android artifact.
- [ ] Host sign-in and native document/checkout integrations remain explicit
  later increments rather than implied by a guest-only shell.

**Environment prerequisite:** macOS/Xcode, compatible device/simulator, and
signing/provisioning for the intended test install. Missing facilities are
reported as delivery prerequisites; they do not hold up Android or website work.

## 04 — Sign in and host from the Android app

**Blocked by:** 02 — Join a shared room from an Android WebView app.

**What it delivers:** An Android user completes external Google sign-in,
returns to a verified account in the embedded website, and uses account access
and host controls. This slice delivers the shared server-owned authentication
handoff that the iOS host slice will reuse.

- [ ] Sign-in leaves the embedded WebView for an appropriate registered
  platform/browser flow and returns to the originating app screen.
- [ ] Server-validated identity establishes the usual secure WebView account
  session through a short-lived, single-use, verifier-bound handoff. Browser
  cookies are not assumed shared, and a link cannot assert account ownership.
- [ ] Existing browser login remains compatible. Invalid verifier/flow,
  expiry, replay and nonallowlisted returns fail without creating a host session
  or changing the room. No reusable session/provider secret enters URLs/logs.
- [ ] The signed-in host can read existing private Account/voucher/test-credit
  state and perform legitimate host controls; another account and guests cannot.
  Existing CSRF/origin checks and private snapshot boundaries remain intact.
- [ ] Logout/session expiry revoke host access with a sign-in prompt while
  guest participation and current timers continue under existing rules.
- [ ] Mocked account/native integration tests exercise the complete return,
  session and room-owner boundary. Actual Google/device return is checked
  separately when callback/credential configuration is available.

**Environment prerequisite:** platform identity and OAuth/return-link
configuration for live checks, configured privately. No secret collection,
credential fabrication or public service deployment is implied by this ticket.

## 05 — Sign in and host from the iOS app

**Blocked by:** 03 — Join a shared room from an iOS WebView app; 04 — Sign in
and host from the Android app (shared verified handoff contract).

**What it delivers:** An iOS host completes the external authentication flow
and returns to the same server-verified account inside WKWebView, with account
access and host controls matching Android and the website.

- [ ] iOS browser/native authorization and allowlisted app return use the
  shared verified handoff without another account model or backend.
- [ ] WKWebView's website cookie store receives and verifies the session
  before host controls are enabled; no system-browser cookie-sharing assumption.
- [ ] Invalid/replayed/expired returns, changed accounts, logout and expiry
  are rejected through the shared server rules without losing accepted answers.
- [ ] Account privacy, guest joining and same-origin API/WSS/CSRF remain
  compatible. Existing voucher and sandbox run access behave the same.
- [ ] Installed-shell/mocked checks and separately configured actual Google
  return provide iOS-specific evidence, rather than reusing Android screenshots.

**Why 04 is a blocker:** it delivers the shared server/web handoff consumed by
this slice. The Android app itself is not a prerequisite for building the iOS
guest shell in 03; there is no artificial edge between 02 and 03.

## 06 — Prepare and save a defense from Android

**Blocked by:** 04 — Sign in and host from the Android app.

**What it delivers:** An Android host uses native document selection to create
code/research rooms, confirms the research map/budget, completes a defense and
saves/shares its transcript. Existing sandbox checkout opens externally and
returns to server-verified Account state. This slice establishes the narrow
trusted-site export/checkout-return contracts for both shells.

- [ ] System picking supports the existing multiple project files/ZIP and
  research-document inputs, cancellation and retry. Existing extraction/size
  limits, settings and measured progress remain visible and authoritative.
- [ ] Code and research/mixed preparation flows work from picked fixtures,
  with accepted metadata, extraction errors and research budget confirmation.
- [ ] Transcript export/save/share works for the existing summary, including
  browser Blob exports. Only trusted top-level site actions can invoke the
  narrow bridge; no general native execution or private-content logging.
- [ ] Sandbox checkout stays account-owned, opens appropriately outside the
  WebView and returns to refreshed Account state. Redirects cannot award
  credits; existing verified-webhook/deduplication/charging rules remain intact.
- [ ] Cancelled picker/share/checkout and interrupted app return are recoverable
  without losing the current room or causing duplicate paid runs/purchases.
- [ ] Fixture/mocked flow checks and device file/share checks are recorded;
  actual provider simulator checks are separate and never use a real wallet.

## 07 — Prepare and save a defense from iOS

**Blocked by:** 05 — Sign in and host from the iOS app; 06 — Prepare and save
a defense from Android (shared trusted-site export/checkout-return contracts).

**What it delivers:** An iOS host selects the accepted papers/source files,
creates/prepares the same defense and saves/shares the transcript, with sandbox
checkout return matching the shared website behavior.

- [ ] iOS document picking/cancellation/multiple selection works with the
  accepted website inputs, extraction limits, errors and upload progress.
- [ ] Code and research/mixed preparation, map review and budget confirmation
  are usable inside the current website in WKWebView.
- [ ] Existing transcript Blob export reaches a native save/share action using
  the trusted-site contract; private text is not emitted to logs or unrelated
  frames/sites. Cancelled actions preserve room state.
- [ ] External sandbox checkout return refreshes server-owned Account state
  without minting credits from a redirect or bypassing webhook/account checks.
- [ ] iOS integration/device evidence covers picking, actual keyboard/safe
  areas, export, interruption/reconnect and return. Android or browser success
  does not satisfy these platform-specific criteria.

**Why 06 is a blocker:** it supplies the shared website bridge/return contract,
not an iOS dependence on Android internals. The iOS host flow in 05 can proceed
independently of Android upload/export work once its own blockers are complete.

## 08 — Verify downloadable Android and iOS delivery

**Blocked by:** 06 — Prepare and save a defense from Android; 07 — Prepare and
save a defense from iOS.

**What it delivers:** Repeatable, installable test artifacts for both platforms,
with a verified same-room workflow, documented installation and honest evidence
for physical devices, providers and local release checks.

- [ ] Rebuild and install the Android test APK and correctly signed/provisioned
  iOS test artifact. Record build identity, supported test devices/OS versions
  and installation instructions; signing material stays outside Git.
- [ ] Both installed apps use the same configured website and existing backend;
  a desktop/browser teammate sees synchronized questions, citations, votes,
  answers, chat and the completed transcript/coaching.
- [ ] Exercise code and research/mixed flows with provider/AI fixtures, including
  clarification, timeout, retry, background/reconnect and session expiry.
- [ ] Physical Android and iOS checks cover actual keyboards/safe areas,
  uploads, export/share and external sign-in/return. Report simulator, browser,
  physical-device and user visual review evidence separately.
- [ ] Run existing offline Python/React suites and production build; separately
  verify actual Google and PayMongo simulator return when credentials/callbacks
  are configured, without real payments or paid AI tests by default.
- [ ] Provide local review screenshots and artifacts/evidence handoff. Frozen
  main, hosted deployments, public store submissions and paid infrastructure
  are unchanged unless separately requested. Missing build/signing/device or
  provider configuration is named; it is never reported as a passing check.

## Dependency frontier

Start with **01**. Then **02** and **03** can proceed independently. **04** follows
02; **05** follows 03 and the shared handoff from 04. **06** follows 04. **07**
follows 05 and the shared integration contracts from 06. **08** completes delivery
after both platforms' integration. Every ticket contains its own validation;
08 is final distribution/device verification, not the first time code is tested.

No automatic GitHub issues, publication, implementation or deployment has been
performed. The existing parent specification and historical portrait pointer
are not modified by this draft. After approval, publish eight separate numbered
local tickets with ready-for-agent status and their explicit blocking edges.

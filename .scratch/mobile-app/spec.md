# Portrait website and downloadable WebView apps

Status: ready-for-agent
Date: 2026-10-06
Working branch: feature/question-first-room

## Problem Statement

The defense room currently blocks portrait phones with a rotate prompt. Its
landscape layout gives too little usable reading and typing space on an upright
phone. The host and defenders need to read full panelist questions, inspect
grounded citations, vote and answer without rotating the phone.

The user also wants downloadable Android and iOS apps that open the existing
website in an embedded WebView. Separate mobile screens, a replacement frontend
and a separate backend would duplicate the product and are not the requested
solution. The earlier layout experiments are historical references, not a
design-selection requirement.

## Solution

Make the actual website responsive in portrait while keeping its current theme
and components. Four compact panelist positions sit above the central question
and citation; four compact defender positions sit below it. Voting, answers and
team chat remain in the bottom dock. Reading space, usable text and access to
controls take priority over decorative space.

Deliver thin Android and iOS shells that load the configured HTTPS website URL.
They display the same interface and use the same host accounts, rooms, defense
runs and backend as phone and desktop browsers. Website updates appear when
the hosted page reloads; changes to native integrations still need a new app
build. Provide test-installable artifacts and installation instructions before
any public store publication.

Deliver in sequence: existing-page portrait support and local review, then
URL-loading shells with mobile integration, then native-device/build evidence.
Publication is a separate user-requested step.

## User Stories

1. As a phone user, I want the current website to open in portrait, so that I can use it without rotating my phone.
2. As a returning user, I want the mobile room to retain the website's theme and familiar controls, so that I recognize the same product.
3. As a defender, I want the question to occupy the main reading area, so that I can understand what the panelist is asking.
4. As a defender, I want to read the full question and lead-in, so that a long question is never silently truncated.
5. As a defender, I want the active panelist clearly identified, so that I know who is speaking.
6. As a defender, I want all four panelist positions available in a compact strip, so that I can understand the panel without losing reading space.
7. As a defender, I want all four defender positions available below the question, so that I can see my team and the chosen defender.
8. As a teammate, I want my configured display name and online status shown accurately, so that I can recognize other defenders.
9. As a voter, I want readable vote counts and a clear chosen-defender indication, so that speaker selection is understandable without relying on color alone.
10. As a defender, I want the exact code excerpt with filename and line number, so that I can inspect what prompted the question.
11. As a research defender, I want the extracted passage, location and extraction label, so that I can distinguish document evidence from a faithful PDF render.
12. As a defender, I want preserved code indentation and horizontal source scrolling, so that long lines remain inspectable.
13. As a defender, I want internal question scrolling, so that long dialogue and evidence do not push the answer controls off-screen.
14. As a chosen defender, I want a usable answer composer above the keyboard, so that I can submit without dismissing the keyboard first.
15. As a chosen defender, I want part of the question reading area available while typing, so that I can refer back to the question.
16. As a chosen defender, I want my draft retained when I change dock tabs or rotate the phone, so that I do not lose work during the same turn.
17. As a chosen defender, I want visible sending and error states, so that I know whether my submission was accepted and can retry appropriately.
18. As a defender, I want same-question clarification exchanges readable on mobile, so that simplifying or translating a question does not advance the defense turn.
19. As a defender, I want the server-owned vote and answer deadlines shown, so that the mobile app follows the same timing rules as the website.
20. As a defender who is not chosen, I want to see who is answering and use team chat, so that I understand why I cannot submit the answer.
21. As a teammate, I want private team chat and its unread indication accessible from the dock, so that I can coordinate while the question stays available.
22. As a host, I want Controls, Account and Transcript reachable on a small screen, so that I can manage the room without clipped buttons.
23. As a keyboard or assistive-technology user, I want clear labels, visible focus and accessible drawer behavior, so that every essential action is usable.
24. As a host, I want Google sign-in to return me to the same app screen, so that I can create and manage my room.
25. As a host, I want existing voucher access and sandbox credits available in the mobile app, so that my account access is consistent across devices.
26. As a host, I want to upload accepted papers and code using the phone's file picker, so that I can prepare a defense without a desktop.
27. As a host, I want upload progress, extraction errors and retained selections on failure, so that room creation is understandable on mobile.
28. As a research host, I want to inspect the paper map and confirm the question budget, so that preparation remains available in portrait.
29. As a teammate, I want to join from a room code and display name without signing in, so that guest participation remains simple.
30. As a mobile defender, I want to share a room with desktop/browser teammates, so that mobile users are not placed in a separate system.
31. As a returning defender, I want the current room snapshot restored after reconnection, so that I see the actual phase, chosen defender and remaining time.
32. As a defender who backgrounds the app, I want reconnection to show what happened while I was away, so that I do not assume deadlines paused.
33. As a defender, I want transcript and coaching readable in portrait, so that I can review the same defense run on my phone.
34. As a defender, I want transcript download or native sharing to work, so that I can save the existing summary.
35. As an Android user, I want a downloadable test-installable app, so that I can open the website from an app icon.
36. As an iOS user, I want a properly signed test-installable app and installation guidance, so that I can open the same website from an app icon.
37. As an app user, I want a truthful loading/error screen and retry if the website cannot load, so that I can recover from a connection failure.
38. As an app user, I want external destinations to open appropriately outside the app, so that third-party pages do not take over the trusted WebView.
39. As a host, I want sign-out and session expiry respected inside the wrapper, so that room ownership remains tied to my verified host account.
40. As an app user, I want safe-area and keyboard spacing respected, so that essential text and buttons are not hidden by phone chrome.
41. As a desktop user, I want the existing desktop and landscape behavior retained, so that portrait support does not degrade my current experience.
42. As a project owner, I want website and native build verification reported separately, so that I know what is actually ready to download and test.

## Implementation Decisions

- The website remains the single frontend. Extend the current room layout,
  question card, seat rows, dock and drawers rather than creating a mobile
  route with replacement screens or promoting a prototype variant.
- Preserve existing visual tokens, typography, source presentation and
  presenter highlight. Use responsive sizing to reduce nonessential chrome
  before reducing question readability.
- Replace the portrait-blocking rotation prompt with usable portrait layout.
  Both portrait and landscape remain supported in mobile browsers and shells;
  orientation changes retain the same active page and turn.
- Keep four panelist and four defender positions identifiable. Compact labels
  can abbreviate roles visually while accessible names and the question header
  retain complete role names. Chosen defender, votes and connectivity use text
  or shape as well as the existing accent.
- Keep the question reading area internally scrollable. Preserve exact source
  text, code indentation and code-only horizontal scrolling. Keep document
  citations, surrounding passage and extracted-text explanation in their
  existing presentation; do not make research prose look like source code.
- Keep Vote/Answer and Team Chat in the current bottom dock. Do not move the
  answer composer back into the drawer or add a new defense navigation model.
- Use safe-area and visible-viewport sizing to keep the composer reachable
  when the keyboard opens. Compress nonessential header and seat detail on
  short screens while retaining a scrollable reading area and all positions.
  A mock keyboard block is not a substitute for real keyboard verification.
- Preserve draft, acknowledgment, rejection and turn-advance behavior. Resize,
  rotation and keyboard events must not remount room state or initiate a new
  connection/defense run solely because the layout changed.
- Use small platform-native shells: Android WebView and iOS WKWebView. Native
  code handles hosting, navigation, authentication return, file selection,
  download/sharing and lifecycle only. No bundled copy of the React app, second
  API service or wrapper framework is necessary for this URL-loading scope.
  [Android WebView guidance](https://developer.android.com/develop/ui/views/layout/webapps/webview),
  [Apple WKWebView documentation](https://developer.apple.com/documentation/webkit/wkwebview).
- Configure the allowed HTTPS website origin and app identity per build. The
  intended feature service is defense-simulator.onrender.com; frozen main's
  earlier service is not a deployment target. Configuration must not allow a
  room code or untrusted navigation to select an arbitrary app origin.
- The embedded page runs at the website origin and uses the existing relative
  API/socket URLs, host cookies and CSRF checks. Preserve same-origin WSS and
  account-derived ownership; do not disable origin checks or allow arbitrary
  credentialed cross-origin requests to accommodate the wrapper.
- Allow required JavaScript and website storage while restricting internal
  navigation to the configured site. Open unrelated HTTPS destinations through
  the system browser, reject unsafe schemes and certificate errors, and expose
  no general-purpose native execution bridge to uploaded content or other sites.
- Keep Google authorization outside the embedded WebView. Use an appropriate
  registered platform/browser flow with state/PKCE protection and an allowlisted
  app return. Preserve the existing validated Google identity and stable account
  subject; a deep link must never assert an account identity or authorize a host.
  [Google OAuth policies](https://developers.google.com/identity/protocols/oauth2/policies),
  [Native OAuth guidance](https://developers.google.com/identity/protocols/oauth2/native-app).
- Add the narrow server-owned authentication handoff needed by URL-loading
  shells. Bind each pending return/exchange to the initiating app flow using
  a verifier/challenge; use a short-lived, single-use opaque exchange code.
  Validate identity on the server before issuing the usual secure, HttpOnly
  host session into the WebView's website cookie store. Never place a reusable
  account session, provider token or secret in a return URL, transcript or log.
  Expired, replayed and unrelated handoffs fail without changing room state.
- Do not assume system-browser and WebView cookie stores are shared. Complete
  and verify session establishment before refreshing Account or attempting host
  controls. Sign-out/expiry use existing server revocation; guest tokens remain
  independent. Browser-only Google login remains compatible.
- Use system document picking for the existing accepted uploads, including
  multiple project files or project ZIP and direct research documents. Keep
  existing server extraction/size limits, defense settings and measured upload
  progress; add no new document format or extraction behavior.
- Support existing transcript download through a native save/share handoff
  where WebView blob downloads require it. Limit any bridge to the trusted
  top-level website and narrowly scoped actions, without logging document text.
- Keep current account/voucher and sandbox purchase behavior. Open provider
  checkout externally as needed, return to the app and refresh server-verified
  account state. A checkout redirect never grants credits. No real-money
  activation, price change or native purchasing system is introduced.
- Backgrounding does not reset server deadlines, change turn ownership or
  grant a new run. Resume/reconnect uses the existing snapshot and chosen-
  defender reassignment rules. Clarification clock behavior remains unchanged.
- Android Back dismisses the keyboard/drawer or uses safe in-site navigation
  before exiting; it must not silently submit or restart a defense. iOS uses
  native navigation conventions without adding a separate room toolbar.
- Show wrapper loading and main-page connection errors with retry, without
  presenting stale room state as connected. Preserve the existing expired-room
  recovery and keep app page-load status distinct from AI-generation status.
- Native outputs include repeatable Android and iOS projects/build instructions,
  an Android test APK and a signed iOS test artifact when signing/build facilities
  are available. iOS installation uses supported provisioning/distribution;
  an unsigned archive or repository link is not a downloadable working iOS app.
- App identifiers, signing material, OAuth registrations and return-link
  associations are build/deployment configuration. Keep secrets and signing keys
  out of Git; document prerequisites without inventing credentials or purchasing
  services. Local Linux is not evidence of a successful iOS build.
- Work on the feature branch, preserve unrelated Account/upload edits and files,
  and record each checkpoint in the shared log. Keep frozen main and hosted
  services unchanged until publication is explicitly requested.

## Testing Decisions

- Prefer the existing whole-room boundary: test the actual React room and its
  user-visible actions with mocked server/provider responses. Assert content,
  accessible controls, accepted/rejected actions and preserved state, not CSS
  class names, component internals or a second mock-only frontend.
- Use the existing room, question/citation, dock, drawer, upload and socket test
  patterns. Cover long question/lead-in, code indentation/horizontal overflow,
  PDF/DOCX extracted citations, clarification, presenter indication, setup,
  account, transcript and coaching through their public behavior.
- Browser layout checks cover 320x568 and 390x844 portrait, 667x375 landscape,
  normal desktop and enlarged text. Verify no page-level horizontal overflow,
  full reachable text, identifiable seats, visible focus, meaningful touch
  targets and an internal reading scroll region without clipped dock controls.
- Check keyboard opening/closing, draft retention, orientation changes and
  drawer focus/dismissal at the page boundary. Browser viewport simulation is
  a useful local check but cannot establish physical-keyboard correctness.
- Run a mocked two-client code defense and a research/mixed defense through
  preparation, voting, answers, clarification, timeout, retry, reconnect,
  transcript and coaching. Include one portrait client and one desktop client.
  Do not change AI quality requirements or use paid calls in offline tests.
- Use existing authenticated account/server tests for the added handoff. Test
  correct identity, wrong verifier/flow, bad return target, expiry, replay,
  once-only consumption, session establishment, logout/expiry and owner-only
  actions. Ensure guests can still join and private account details do not enter
  shared snapshots. Existing CSRF and payment protections must still pass.
- Test shell integration at its highest boundary: an installed app loading a
  controlled HTTPS fixture/server. Check allowlisted navigation, external links,
  failure/retry, upload selection/cancellation, native save/share and lifecycle.
  Avoid separate low-level tests that merely mirror platform delegates.
- Android and iOS physical-device checks verify actual keyboards/safe areas,
  external Google return and verified WebView session, file picking, transcript
  export, same-room interaction with a browser teammate, background/reconnect
  and expiry. A mobile-shaped browser screenshot does not satisfy these checks.
- Mock OAuth and PayMongo in automated runs. Once local credentials/callbacks
  are available, verify actual Google login and a provider sandbox return
  separately. Do not use a real bank/wallet payment as a test.
- Run the complete existing Python and React suites and production build after
  implementing website/server changes. Record native build/install checks per
  platform independently; unavailable signing/macOS facilities remain explicit
  prerequisites rather than inferred successes.
- Present the actual local website and desktop/portrait/landscape captures
  before publication. Record mocked, live-provider, hosted, physical-device and
  user-review evidence separately. No visual variant selection is required.

## Out of Scope

- A new visual identity, separate mobile React screens, A/B/C prototype
  promotion, 3D room or bundled replacement website.
- Changes to AI prompts, panelist roles, grounded-citation validation, question
  budgets, voting duration, answer duration or defense/coaching policy.
- New account/payment products, real-money enforcement, prices, subscriptions,
  credit quoting, native in-app purchases or store payment-policy rollout.
- Offline defenses, background timer suspension, push notifications, voice,
  movement, stored defense history or new upload/extraction capabilities.
- A Streamlit visual redesign, frozen-main changes, public app-store submission,
  unrequested deployment or paid build/distribution infrastructure.
- Guaranteed app-store acceptance, public unsigned iOS downloads or declaring
  an app complete from a browser preview alone.

## Further Notes

- The user has confirmed Android and iOS together, portrait in both wrappers
  and phone browsers, full host/guest functionality, compact seat positions and
  preservation of the current website. They explicitly clarified that the
  downloadable app embeds the website URL.
- The user confirmed the testing boundaries: existing web room at phone
  viewports, mocked two-client server flow, and installed Android/iOS WebViews
  for sign-in, uploads, downloads and reconnect. No additional discovery
  interview was needed.
- The local tracker is Markdown. Ready-for-agent means the specification is
  available for the next workflow, not that implementation, review, distribution
  credentials or publication has already happened. The next step is To Tickets
  with dependencies, then Implement beginning with website portrait support.
- The historical prototype is captured on local prototype/mobile-portrait at
  b18be90. Its tests/captures establish only earlier mocked visual exploration;
  it is not the source of an approved mobile design.
- Local inspection found Linux with Node/JDK and part of the Android SDK, but
  no emulator/SDK command-line tools or Xcode. Native tooling, signing and
  platform OAuth setup are separate prerequisites for executable app delivery.
- Rooms remain in memory on one process/instance. A later deployment/restart
  erases active rooms; hosted validation must use a fresh room. Nothing in this
  feature introduces a second room server or persistence for defenses.

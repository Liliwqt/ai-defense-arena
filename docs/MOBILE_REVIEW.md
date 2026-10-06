# Mobile implementation review

Fixed point approved by the user: `48e3ff7`. The review used
`git diff 48e3ff7...HEAD`, implementation commit `5a639df`, and the explicitly
selected mobile review fixes. Standards and Spec were reviewed independently by
read-only agents. Pre-existing Account/upload changes, payment documentation,
older captures, presentation files and screenshot deletions were excluded.

## Standards

No remaining documented-standard breaches or heuristic findings requiring work.
Three earlier findings were resolved: README no longer calls phone play
landscape-only; browser/native sign-in share session replacement and cookie
policy; verified Google identity uses named fields instead of a positional tuple.
The frozen-main, existing-theme, tracker and verification boundaries remain intact.

## Spec

No remaining code-level implementation finding or scope creep identified.
Two earlier defects were fixed and checked:

- Foregrounding keeps an OPEN socket. Only a closed socket reconnects, preserving
  the chosen defender, server deadline and same-turn draft on a healthy stream.
- Native sandbox checkout returns to a fixed HTTPS page with a Return to app
  link. Android/iOS callbacks resume the page; verified receipts/webhooks remain
  authoritative. Browser returns retain their existing behavior, and the public
  return page ignores claimed payment status and cannot award credits.

Three delivery/verification prerequisite groups remain open:

1. iOS compilation, signing and test installation require macOS/Xcode and the
   owner's provisioning. No signed iPhone artifact exists in this workspace.
2. Installed Android/iOS flows and physical keyboards/safe areas require devices
   or configured simulators. No adb device or Android AVD is currently available.
3. Actual Google sign-in and PayMongo simulator return need a controlled HTTPS
   deployment/callback configuration and installed apps. Offline mocks do not
   establish provider integration; user visual review is also still pending.

These are explicit incomplete delivery checks, not inferred passes or dismissed
requirements. The native tickets remain ready-for-human with unchecked criteria.

## Verification evidence

- Working tree: 219 Python tests (AI, Google and PayMongo mocked), 169 React tests,
  TypeScript/production build pass. Commands are the AGENTS offline gate.
- Isolated selected source: 219 Python tests (external providers mocked) and
  162 React tests/build, excluding unrelated pending Account/upload code. Different React counts reflect excluded pre-existing tests.
- Before review fixes: mocked two-browser code four/eight and mixed twelve-turn
  runs passed voting, clarification, timeout, retry, reconnect, exact citations,
  transcript and coaching. These are local fixtures, not live AI conversations.
- After review fixes: fresh desktop/portrait four-turn mock run kept exactly one
  socket, seat 1, unchanged answer deadline and draft after native-resume. Chat
  broadcast still arrived; both clients finished with identical cited turns and
  coaching, and reloading restored completion. Two helper errors (fixture routes
  after the static mount and a chat `message` instead of protocol `text`) were
  corrected in the temporary helper without changing production protocol.
- Android rebuild: Gradle `:app:assembleDebug` passes; apksigner verifies APK v2
  signature; package `com.defensearena.mobile`, min API 30, target 36.
  Debug APK SHA-256:
  `e47fdae60b7b4afea235e856109d9238cb7d416e6a7e1c74f6ecd2a81d423ec3`.
  Artifact is ignored at `mobile/artifacts/defense-arena-debug.apk`.
- iOS plist/scheme and Android manifest parse; build scripts pass shell syntax.
  This is source validation, not an iOS compile or native installation.

Local working preview: <http://127.0.0.1:8816/?preview=1&research=1&long=1>.
Preview is synthetic, with no paid calls. New captures:
[portrait](../screenshots/mobile-review-portrait.png) and
[chosen-speaker resume](../screenshots/mobile-resume-review-portrait.png).
Earlier desktop/portrait/landscape captures are named `screenshots/mobile-*`.

Main and hosted services are unchanged. Default native URL still receives the
older deployed website; a controlled HTTPS staging origin is needed to exercise
new native integrations before publication. No push/deployment or user visual
approval is claimed.

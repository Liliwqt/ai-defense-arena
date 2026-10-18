# Native microphone implementation review — 2026-10-19

Scope: ticket 08 Android and ticket 09 iOS, current source at commit 859b384
plus the owned uncommitted native/shared changes. Comparison starts at the
user-confirmed 1f760be. Unrelated reasoning/local-testing/planning/QR work is
excluded. Snapshot patch and SHA-256 manifest are in ignored
`.local/native-implementation-review-20261019/`. This review changes no runtime
source and does not authorize push, deployment or main changes.

## Standards

Independent Standards review: **0 actionable findings**. No documented-standard
violations or actionable baseline smells identified. Separate native platform
interfaces justify their different adapters. Evidence distinguishes source,
mocked tests, Android build and pending installed-device/iOS checks.

## Spec

Independent Spec review: **2 actionable findings**.

1. **P1 — iOS blocks its own background teardown navigation.**
   `mobile/ios/DefenseArena/ArenaViewController.swift:127` loads `about:blank`,
   while the navigation action policy at 141–152 cancels non-trusted URLs and
   the response policy at 155–156 does likewise. `trusted` requires HTTPS.
   `suspendAudio` has already cleared capture IDs and marked the document unloaded.
   Consequently the intended hard unload is blocked and cleanup depends on
   asynchronously delivered JavaScript. Ticket 09 requires stopping capture
   independently of teardown-message delivery. Permit only a narrowly authorized
   native teardown navigation or use a native media-stop API; do not broadly allow
   external pages. Validate the actual delegate sequence on iOS.
2. **P2 — Android foreground website retry leaves capture recovery broken.**
   `mobile/android/app/src/main/java/com/defensearena/mobile/ArenaActivity.java:164`
   calls `stopAudioDocument`, which suspends MicrophonePolicy and, after capture
   preparation, sets `audioDocumentUnloaded`. Retry at line 68 only calls
   `loadUrl`. It does not reset the flag or resume the policy. `onPageFinished`
   at 103 then suppresses audio/export-port installation and hiding the loading
   notice. Even before any capture preparation, the microphone policy remains
   suspended until another Activity resume. Ticket 08 requires clear recovery
   and preserved native callback boundaries. Use a foreground recovery transition
   that resets document state and resumes policy without starting the microphone.

No additional scope creep identified. Neither finding is fixed by this review.
The prior review 08 record is historical; its ready-for-human status does not
establish that these current native lifecycle paths are correct.

## Verification

- Fresh `npm test -- --run src/AppVoice.test.tsx`: **18/18 pass**, with native
  bridge, browser media, room and speech mocked. These tests do not execute Swift
  or Activity navigation/permission callbacks.
- Fresh `npx tsc -b --noEmit`: passes.
- A temporary Java diagnostic executes the real public MicrophonePolicy API:
  foreground resume → load → failure suspension → retry load → `arm` is **false**;
  an additional lifecycle resume makes it **true**. This confirms the Android
  policy recovery defect without a WebView/device or provider call.
- Python plist parsing confirms the iOS microphone disclosure is present.
- Reviewed source hashes still match the pinned manifest. No runtime edits made.
- Prior isolated ticket 08 gate remains separate evidence: 604 Python tests with
  external providers mocked, 387 React tests and production build passed.
  Later handoff records report 612/391 on the broader dirty working tree; these
  are not relabeled as fresh isolated verification in this review.
- No macOS/Xcode build or installed iOS/Android recording/background check ran.
  Source review and mocked green tests do not establish actual capture readiness.

Standards: **0 findings**. Spec: **2 findings**, worst P1 (iOS teardown blocked).

## Follow-up fixes — 2026-10-19 (session `native-lifecycle-fixes`)

Applied in the same working tree, without changing any other policy boundary.
This addendum records the fixes; it is not an independent re-review.

- P1 iOS: a one-shot `teardownNavigation` allowance in
  `ArenaViewController.swift` admits only the `about:blank` unload the shell
  starts and is cleared on finish, failure, retry, resume and process
  termination. All other untrusted main-frame/subframe navigation is still
  denied or externalized; the trusted origin is unchanged.
- P2 Android: `retryWebsite()` performs the foreground recovery transition the
  finding asked for — `pageFailed`, `resumeAfterCapture` and
  `audioDocumentUnloaded` are reset, `MicrophonePolicy.resume()` runs and a
  paused WebView is resumed before the reload — without arming the microphone.
- Also addressed in the same task: the ten-second arm uses the monotonic
  `ProcessInfo.processInfo.systemUptime` on iOS (Android already used
  `SystemClock.elapsedRealtime`); permission callbacks settle the requesting id
  exactly once and never clear a newer request; a late Android system result is
  applied only to the document generation that requested it; iOS capture also
  stops on inactive-without-background interruption while the app's own TCC
  prompt is exempt.
- Native tests: Android `MicrophonePolicyTest` grew from 4 to 6 cases
  (`foregroundFailureRecoveryRequiresTheResumeTransition`,
  `unloadedDocumentsAndTheTenSecondWindowStayBounded`) and passes via
  `:app:testDebugUnitTest`. iOS adds a hostless `DefenseArenaTests` target with
  `MicrophonePolicyTests.swift`; it cannot run on this Linux host (no
  macOS/Xcode/Swift toolchain), so its execution remains pending. The project
  file and scheme parse under the `pbxproj` Python library and an XML parser
  (structural checks only).
- Verification rerun after the fixes: `.venv/bin/python -m unittest discover`
  612 tests with AI/speech/Google/payments mocked; React 391 tests in 36 files
  (`NODE_OPTIONS=--max-old-space-size=1536 npm test -- --maxWorkers=2`);
  TypeScript and production build; Android `:app:testDebugUnitTest` 6/6 and
  `:app:assembleDebug` rebuilt APK (`versionCode=2`, `versionName=0.2.0`,
  `INTERNET`/`RECORD_AUDIO` only). Actual installed Android and iOS
  build/TCC/device evidence remains pending and is not implied by these checks.


# 09 — iOS microphone practice

**What to build:** A rebuilt iOS app supplies a microphone-purpose explanation
and trusted-origin capture for the same voice flow, retaining typed use when
capture or permission is unavailable.

**Blocked by:** 04 — Voice probe replies and recovery across screens.

**Status:** ready-for-human

## Acceptance criteria

- [x] Add microphone-purpose disclosure and platform-appropriate trusted-origin audio permission/capture handling without granting camera/external-origin capture or requesting a mic on page load.
- [x] Stop capture on denial/revocation/background/navigation/teardown and require explicit restart, with server-side deadline/cap/revocation protection independent of teardown-message delivery.
- [x] Preserve existing auth/payment/download allowlists and native callbacks; old/unsupported builds keep the current typed flow.
- [ ] Verify policy/lifecycle integration and build with macOS/Xcode/signing when available. Record actual installed capture/permission/background/reconnect and toolchain/device identity separately. Linux source checks do not establish an iOS build or recording; unavailable checks remain explicit pending evidence.

## Verification

Present checked source/policy and a build/device capture checklist;
where macOS and an installed build are available, record the actual results
separately. No broad permission grant is accepted as a shortcut.

## Comments

- 2026-10-17 — User approved the ten-ticket breakdown as drafted; published locally with its agreed blocking edges and acceptance criteria. Specification stories: 100–105, 108.
- Parent: [research-defense practice specification](../spec.md). The parent remains the source of full scope, test boundaries and accepted ADRs; it is not changed by publication. Selected UI: B — Speaker desk, captured on prototype/research-practice (source f0d74a7, verdict a3046c4).
- Each ticket includes its own verification and leaves the app runnable. Record provider-mocked, actual speech, local database, native-build/device and hosted evidence separately. Ticket approval does not start implementation, authorize external-model sharing, push or deploy.

- 2026-10-18 — Implemented locally (uncommitted working tree). `Info.plist` gains
  `NSMicrophoneUsageDescription` and version 0.2.0/code 2;
  `ArenaViewController.swift` adds a reply-capable `defenseAudio` handler, a
  microphone-only WebKit media-capture delegate (trusted HTTPS main frame, fresh
  ten-second single-use arm), a TCC mic request bound to explicit Start mic,
  background document unload/restore and navigation/teardown reset;
  `nativeCapture.ts` detects the iOS bridge and bounds prepare with a 30-second
  cancel, keeping the Android port path unchanged; `AppVoice.test.tsx` adds four
  iOS cases. Criteria 1–3 checked at source level; criterion 4 remains pending
  because this Linux host has no macOS/Xcode/signing. Offline gate: 612 Python
  (AI/speech/Google/payments mocked), 391 React in 36 files, TypeScript and
  production build pass; focused `AppVoice.test.tsx` 18/18. No push/deploy/main
  change; independent Standards/Spec review not yet recorded.

- 2026-10-19 — Review-fix pass (session `native-lifecycle-fixes`). The
  independent [native review](../reviews/native-check-2026-10-19.md) found P1:
  the `about:blank` teardown was cancelled by the shell's own HTTPS-only
  navigation delegate, so the hard unload depended on asynchronously delivered
  JavaScript. A one-shot `teardownNavigation` allowance now admits only the
  `about:blank` unload this controller starts (cleared on finish, failure,
  retry, resume and process termination); every other untrusted navigation stays
  blocked. Capture now also stops when the app becomes inactive without
  backgrounding (for example Control Center or a call), while the app's own TCC
  prompt and its outstanding request are exempt so the prompt cannot cancel
  itself. The permission state moved into shared pure policy structs
  (`MicrophonePolicies.swift`): the ten-second arm uses the monotonic
  `ProcessInfo.systemUptime`, and cancellation, navigation, timeout or a stale
  system callback settles the requesting id exactly once as denied without
  clearing a newer request. A hostless `DefenseArenaTests` target and shared
  scheme add XCTest coverage for the arm and settlement policies; this Linux
  host has no macOS/Xcode or Swift toolchain, so those tests, the iOS build,
  signing and device/TCC evidence remain pending. The project file and scheme
  were parsed by the `pbxproj` library and an XML parser (structural checks
  only). Offline evidence: Python 612 (mocked), React 391 in 36 files,
  TypeScript and production build pass; Android policy tests 6/6 and APK
  rebuilt separately. No push/deploy/main change.

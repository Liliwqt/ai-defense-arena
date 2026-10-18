# 08 — Android microphone practice

**What to build:** A rebuilt Android app captures audio only after the trusted
app's Start mic and system permission, sharing the working web answer/probe flow
with safe lifecycle stopping and typing fallback.

**Blocked by:** 04 — Voice probe replies and recovery across screens.

**Status:** ready-for-human

## Acceptance criteria

- [x] Add audio permission declaration/runtime handling and trusted-origin WebView capture policy. Permit only requested audio for the exact trusted application origin; deny external frames/pages, camera and broad wildcard grants.
- [x] Denial/revocation/backgrounding/navigation/destruction stops capture and upstream forwarding; resuming needs a fresh explicit action. Preserve sign-in/payment/download trust and callback boundaries.
- [x] Reuse the server's authorization, cap, manual-finalizing Send and current deadline. Older/unsupported builds retain typing rather than a misleading supported mic action.
- [x] Native policy/lifecycle checks and an available Android build verify source integration. Record actual installed permission denial/capture/background/reconnect separately with device/build identity; missing hardware/provider evidence remains pending, never a fabricated pass.

## Verification

Build the Android client where tooling exists, exercise policy
denial and lifecycle checks, and present a real-device capture checklist. Actual
capture is a separate claim from the source/build and mocked web checks.

## Comments

- 2026-10-17 — User approved the ten-ticket breakdown as drafted; published locally with its agreed blocking edges and acceptance criteria. Specification stories: 99, 101–105, 108.
- Parent: [research-defense practice specification](../spec.md). The parent remains the source of full scope, test boundaries and accepted ADRs; it is not changed by publication. Selected UI: B — Speaker desk, captured on prototype/research-practice (source f0d74a7, verdict a3046c4).
- Each ticket includes its own verification and leaves the app runnable. Record provider-mocked, actual speech, local database, native-build/device and hosted evidence separately. Ticket approval does not start implementation, authorize external-model sharing, push or deploy.

- 2026-10-18 — Implemented locally in 859b384; independent Standards/Spec review
  against user-confirmed 1f760be recorded in [review 08](../reviews/08.md). One
  Medium Spec finding fixed in the working tree: capture unload no longer
  destroys an outstanding file-picker callback. Two Medium and one Low Spec
  findings remain recorded, not fixed. Gate: 4/4 native policy tests, debug APK
  rebuilt and signature/metadata verified, 612 Python (providers mocked), 387
  React, TypeScript and production build. No connected device or AVD exists, so
  actual installed permission/capture/background/reconnect evidence remains
  pending. Checkpoint 3 still requires 09 and 10. No push/deploy/main change.

- 2026-10-19 — Review-fix pass (session `native-lifecycle-fixes`). The
  independent [native review](../reviews/native-check-2026-10-19.md) found the
  Retry path broken: `failPage` suspended `MicrophonePolicy` and, after capture
  preparation, set the unloaded-document latch, while Retry only reloaded the URL,
  leaving the audio/export ports and the loading notice suppressed and the policy
  suspended. `retryWebsite()` now performs a foreground recovery transition —
  clears `pageFailed`, `resumeAfterCapture` and `audioDocumentUnloaded`, resumes
  the policy and a paused WebView, and reloads — without arming the microphone;
  Start mic remains the only preparation path. In addition, a system permission
  result is now applied only to the document generation that requested it and
  always resolves the pending id exactly once (denied when stale), so a late or
  navigation-crossed result cannot arm an obsolete capture. Verification:
  `ANDROID_HOME=$HOME/Android/Sdk ./gradlew :app:testDebugUnitTest` passes 6/6
  `MicrophonePolicyTest` cases including the new failure-recovery and
  ten-second-window regressions; `:app:assembleDebug` rebuilt the APK
  (`versionCode=2`, `versionName=0.2.0`, only `INTERNET`/`RECORD_AUDIO`);
  offline `.venv/bin/python -m unittest discover` 612 tests with
  AI/speech/Google/payments mocked; React 391 tests in 36 files, TypeScript and
  the production build pass. Actual installed permission/capture/background
  evidence remains pending. No push/deploy/main change.

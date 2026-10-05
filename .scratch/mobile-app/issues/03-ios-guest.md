# 03 — Join a shared room from an iOS WebView app

**Status:** ready-for-human

**Blocked by:** 01 — Use the current website in portrait.

**What to build:** A test-installable iOS WKWebView shell loads the same
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

## Comments

2026-10-06: User approved this breakdown and requested implementation. Canonical specification: portrait website and downloadable WebView apps.

2026-10-06 implementation handoff: iOS WKWebView source/project/shared scheme implemented. Build/signing/installation require macOS/Xcode and the owner’s provisioning; no signed iOS artifact exists. Unchecked native criteria are not claimed complete.

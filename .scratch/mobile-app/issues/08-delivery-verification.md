# 08 — Verify downloadable Android and iOS delivery

**Status:** ready-for-human

**Blocked by:** 06 — Prepare and save a defense from Android; 07 — Prepare and
save a defense from iOS.

**What to build:** Repeatable, installable test artifacts for both platforms,
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

## Comments

2026-10-06: User approved this breakdown and requested implementation. Canonical specification: portrait website and downloadable WebView apps.

2026-10-06 implementation handoff: Offline gate passes 218 Python tests and 167 React tests/build. Mocked portrait/desktop code4/code8/mixed12 and layout checks pass. Android debug APK built; actual installations, signed iOS output and live providers remain blocked by explicit platform/device/configuration prerequisites. No push/deploy. Unchecked native criteria are not claimed complete.

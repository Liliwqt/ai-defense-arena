# 02 — Join a shared room from an Android WebView app

**Status:** ready-for-human

**Blocked by:** 01 — Use the current website in portrait.

**What to build:** A test-installable Android shell loads the same configured
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

## Comments

2026-10-06: User approved this breakdown and requested implementation. Canonical specification: portrait website and downloadable WebView apps.

2026-10-06 implementation handoff: Android URL-loading source and signed debug APK built locally. Installed-shell, physical keyboard and navigation/lifecycle checks await a device or configured emulator. Unchecked native criteria are not claimed complete.

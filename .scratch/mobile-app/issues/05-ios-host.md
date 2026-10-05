# 05 — Sign in and host from the iOS app

**Status:** ready-for-human

**Blocked by:** 03 — Join a shared room from an iOS WebView app; 04 — Sign in
and host from the Android app (shared verified handoff contract).

**What to build:** An iOS host completes the external authentication flow
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

## Comments

2026-10-06: User approved this breakdown and requested implementation. Canonical specification: portrait website and downloadable WebView apps.

2026-10-06 implementation handoff: iOS external ASWebAuthenticationSession and verified HttpOnly cookie-store return implemented against the shared contract. Xcode build and installed/live sign-in check pending. Unchecked native criteria are not claimed complete.

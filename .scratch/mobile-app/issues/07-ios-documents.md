# 07 — Prepare and save a defense from iOS

**Status:** ready-for-human

**Blocked by:** 05 — Sign in and host from the iOS app; 06 — Prepare and save
a defense from Android (shared trusted-site export/checkout-return contracts).

**What to build:** An iOS host selects the accepted papers/source files,
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

## Comments

2026-10-06: User approved this breakdown and requested implementation. Canonical specification: portrait website and downloadable WebView apps.

2026-10-06 implementation handoff: iOS built-in document picking, origin/main-frame-restricted save/share and checkout/resume source implemented. Browser return fixture passes; Xcode, installed picker/export and provider return checks pending. Unchecked native criteria are not claimed complete.

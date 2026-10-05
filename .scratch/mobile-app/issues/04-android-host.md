# 04 — Sign in and host from the Android app

**Status:** ready-for-human

**Blocked by:** 02 — Join a shared room from an Android WebView app.

**What to build:** An Android user completes external Google sign-in,
returns to a verified account in the embedded website, and uses account access
and host controls. This slice delivers the shared server-owned authentication
handoff that the iOS host slice will reuse.

- [ ] Sign-in leaves the embedded WebView for an appropriate registered
  platform/browser flow and returns to the originating app screen.
- [ ] Server-validated identity establishes the usual secure WebView account
  session through a short-lived, single-use, verifier-bound handoff. Browser
  cookies are not assumed shared, and a link cannot assert account ownership.
- [ ] Existing browser login remains compatible. Invalid verifier/flow,
  expiry, replay and nonallowlisted returns fail without creating a host session
  or changing the room. No reusable session/provider secret enters URLs/logs.
- [ ] The signed-in host can read existing private Account/voucher/test-credit
  state and perform legitimate host controls; another account and guests cannot.
  Existing CSRF/origin checks and private snapshot boundaries remain intact.
- [ ] Logout/session expiry revoke host access with a sign-in prompt while
  guest participation and current timers continue under existing rules.
- [ ] Mocked account/native integration tests exercise the complete return,
  session and room-owner boundary. Actual Google/device return is checked
  separately when callback/credential configuration is available.

**Environment prerequisite:** platform identity and OAuth/return-link
configuration for live checks, configured privately. No secret collection,
credential fabrication or public service deployment is implied by this ticket.

## Comments

2026-10-06: User approved this breakdown and requested implementation. Canonical specification: portrait website and downloadable WebView apps.

2026-10-06 implementation handoff: Shared server handoff passes mocked OIDC/HTTP/WebSocket identity, verifier, expiry, replay, concurrency, secure-cookie, CSRF/logout and ownership checks. Android return/cookie-store source compiles; actual Google/native check pending. Unchecked native criteria are not claimed complete.

# Website WebView apps

These are thin, native URL-loading shells for the **same website and backend**.
They do not contain a second React build or create separate rooms. Website
updates appear on page reload; native integration changes need a new app build.
The existing website now supports portrait and landscape in phone browsers too.

## Current evidence and limitations

Android debug APK built locally on Linux using JDK 17, SDK/build tools 36 and
Gradle 9.1.0/AGP 9.0.1. APK signature and package metadata were verified. The
artifact is `mobile/artifacts/defense-arena-debug.apk` (ignored by Git).
It is a test build, not a signed production/store release.

No connected Android device or configured emulator was found. The SDK contains
an emulator binary, but no AVD. Native navigation, file picking, external Google
return, actual keyboards, export and background/reconnect have **not** been
verified on an installed device.

The iOS project and shared scheme are provided, but this Linux workspace lacks
macOS/Xcode. No iOS build, signed artifact or installation is claimed. Use your
own Apple signing team/provisioning on a Mac. No paid distribution is assumed.

The default origin is `https://defense-simulator.onrender.com`. Source is now
published on `feature/question-first-room` with `[skip render]`; publication does
not request deployment. No hosted verification of the mobile changes is claimed.
An APK loading that URL receives the currently deployed website. To test the
new integration before publication, configure a controlled HTTPS staging server
with this branch. Do not point it at frozen main or disable certificate checks.

## Android build and test installation

Install JDK 17, Android SDK platform 36 and build tools 36.0.0. Set `ANDROID_HOME`
to that SDK. From the repository root:

```bash
./mobile/scripts/build-android.sh
# Optional controlled HTTPS origin:
./mobile/scripts/build-android.sh -ParenaUrl=https://your-staging.example
adb install -r mobile/artifacts/defense-arena-debug.apk
```

The app supports Android 11/API 30 or newer. Use Android Studio's SDK tools to
create an AVD, or connect your own USB-debugging-enabled device. Open AI Defense
Arena from the launcher. A real device must trust the server certificate normally.
For a manual APK install, Android may ask you to allow installation from your
chosen file manager. Use the debug APK only for private testing.

The wrapper pins its Gradle distribution and official SHA-256 checksum. Generated
builds, caches, local SDK configuration, artifacts and signing keys are ignored.
Debug signing is handled by the Android tools; no signing key belongs in Git.

## iOS build and installation

On a Mac with Xcode, open `mobile/ios/DefenseArena.xcodeproj`.
Copy `local.xcconfig.example` to ignored `local.xcconfig`, set your own
`DEVELOPMENT_TEAM` and, if needed, an HTTPS `ARENA_URL` and unique bundle ID.
Choose the shared DefenseArena scheme and your provisioned iPhone, then Run.
Or use `./mobile/scripts/build-ios.sh` to build for a generic iOS device.
Minimum iOS is 15.0. For an iOS simulator, Xcode can build with signing disabled;
that simulator build is not an installable iPhone app.

For a distributable test artifact, use Xcode Archive and your supported signing
and export method. Do not present an unsigned `.app` or source ZIP as an iPhone
download. TestFlight/public stores and their account/payment policies are a later
publication decision.

## Authentication and private account state

Google authorization runs outside WebView: Android opens the system browser;
iOS uses `ASWebAuthenticationSession`. The existing server OAuth client and its
HTTPS callback `/api/auth/google/callback` still validate identity, state, nonce,
signature and PKCE. Browser-only Google login stays compatible.

1. Native code creates a random verifier and sends its S256 challenge to
   `POST /api/auth/mobile/start`, with an allowlisted originating app screen.
2. Server returns a login URL for a bounded, five-minute handoff. It saves no
   provider tokens and admits at most 128 pending handoffs per process.
3. After verified Google return, the browser redirects to the fixed
   `defensearena://auth?flow=...&code=...` callback. The code is opaque, short-lived
   and once-only. It cannot assert an account or host ownership.
4. Native code matches its pending flow, then exchanges the code **and verifier**
   with `POST /api/auth/mobile/complete`. Expired, wrong and replayed proof fails.
5. Native code installs the usual Secure, HttpOnly site cookie in the WebView's
   cookie store and waits for completion before loading the originating screen.
   Account state is then read from the existing private `/api/auth/me` endpoint.

The custom scheme is registered in both native projects. Its interception cannot
redeem the code without the initiating verifier. Keep server credentials and
signing files private. No account session or Google token is put in a return URL
or JavaScript bridge. Handoffs are in memory and disappear on restart; accounts
and balances use the existing store. Host ownership, CSRF, vouchers and sandbox
credits retain their current server checks. Guests still use room tokens.

No additional Google native client secret is embedded in either app: this flow
uses the existing server web client. Register the server's exact HTTPS OAuth
callback in Google as before. Check real external-browser return on each platform
with configured credentials before claiming the integration works live.

## Navigation, documents and lifecycle

Internal navigation is restricted to the configured HTTPS origin. External
HTTPS pages, including provider checkout, open outside the trusted WebView.
Unsafe schemes and certificate errors are rejected. The native export capability
is unavailable to other origins or subframes. There is no general execution bridge.

Android uses the system document picker for HTML file inputs, including multiple
files; iOS keeps WKWebView's built-in document selection. Accepted types, extraction,
limits, validation errors and measured upload progress remain website/server-owned.
The picker does not add OCR or relax upload validation.

Download summary uses the existing summary text. Android transfers a narrow export
message port only to the trusted top-level site, then uses the system Save dialog.
iOS validates the top-level message origin and opens native save/share. Names and
text size are restricted; document contents are never logged. Browsers retain their
ordinary text-file download.

Foregrounding refreshes the private account and keeps a healthy WebSocket open.
A closed connection reconnects for the authoritative room snapshot. The same React
page remains mounted so same-turn drafts survive resize/reconnect. Server timers keep running; selection may change while a player
is offline. Native checkout uses a fixed HTTPS return page with a **Return to app** link
(`defensearena://payment-return`). It resumes the mounted page and refreshes
server-verified state; if the app was closed, open its payment screen to inspect
purchase history. Browser checkouts retain their normal website return. Neither
return path confirms payment or awards credits. Existing webhook verification remains authoritative.

## Verification checklist

- Website: actual page at 320x568/390x844, 667x375 and desktop; readable long code
  and extracted passages, clarification, setup/account/transcript/coaching,
  keyboard focus and simulated keyboard space. Physical keyboard is separate.
- Offline API: verified mocked OIDC return, wrong verifier/flow, expiry, replay,
  concurrent exchange, secure cookie, logout/CSRF and actual host/guest room access.
- Mocked two browsers: code four/eight and mixed twelve questions, votes, selected
  speaker, clarification, timeout, retry, reconnect, identical transcript/coaching.
- Installed Android/iOS: **pending**. Test initial load/failure/retry, hostile
  navigation/TLS, picker cancellation/multiple PDF/DOCX/ZIP, summary save/share,
  Google sign-in/out/expiry, sandbox checkout return, keyboard/rotation draft,
  chosen-speaker reassignment and same room with a browser teammate.
- Live Google/PayMongo, hosted deployment, physical second device and user visual
  approval are **not** established by offline tests or the APK build.

See the canonical spec `.scratch/mobile-app/spec.md`, eight tickets under
`.scratch/mobile-app/issues/`, and `PROJECT_LOG.md` for current evidence.

Implementation references: [Android WebView](https://developer.android.com/develop/ui/views/layout/webapps/webview),
[Android build compatibility](https://developer.android.com/build/releases/agp-9-0-0-release-notes),
[WKWebView](https://developer.apple.com/documentation/webkit/wkwebview),
[Google OAuth policies](https://developers.google.com/identity/protocols/oauth2/policies).

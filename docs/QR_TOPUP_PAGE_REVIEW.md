# QR-first top-up page

Implemented locally on `feature/question-first-room`, 2026-10-07, against
starting commit `9c13972`. Ticket 05 replaces the standalone hosted-checkout
screen. Ticket 06 will retire its creation endpoint; existing receipts remain.

## Local preview

The temporary synthetic fixture runs at
<http://127.0.0.1:8778/?payments=test>. It uses mock accounts, receipts and a
non-payable QR-shaped image, with no Google or PayMongo interaction. The fixture
server lives in `/tmp` and is not part of the application or commit.

To try the real local application, build `game/`, restart FastAPI with the
existing Google and PayMongo test settings, then open `/?payments=test` on that
configured origin. Never scan a sandbox QR using a real wallet.

Review captures:

- [Desktop QR](../screenshots/qr-topup-mock-desktop.png)
- [Portrait QR and actions](../screenshots/qr-topup-mock-portrait.png)
- [Landscape actions](../screenshots/qr-topup-mock-landscape.png)
- [Expired receipt](../screenshots/qr-topup-mock-expired.png)
- [Applied simulation](../screenshots/qr-topup-mock-paid.png)

These show synthetic browser fixtures, not live provider or device evidence.
User visual approval remains pending.

## Behavior

- Public config advertises existing server-owned packages additively. The
  chooser starts empty; explicitly selecting a package generates its QR. The
  default Generate action also supports the shipped package and retained retries.
  Creation sends only the package ID, account CSRF token and saved request key.
- The page displays a normalized PNG data image, package price, countdown based
  on server expiry, confirmation status, simulation, cancel and regenerate.
  It handles choosing, generating, pending, paid, failed, expired, cancelled,
  unverified creation and unconfigured payment states.
- Polling and resume/focus read stored server status only. They never award
  credits. Paid status refreshes account balance/history automatically. A failed
  balance refresh retains the paid receipt and explains how to retry.
- Simulate uses the authenticated test-key-gated route from ticket 04, showing
  explicit fixture copy. A simulated receipt continues checking until signed
  provider evidence replaces the flag and copy; no second award is made.
- Cancel hides the QR on this device, including after reload. It does not cancel
  a provider payment or refund credits. Cancel/expiry themselves award nothing;
  late verified payments remain authoritative. Regeneration starts a separate
  request. Prior receipts remain in server account history.
- Locally saved QR references are scoped to their account; the server enforces
  ownership. History can reopen an existing QR. Logout and version guards keep
  stale reads from restoring a signed-out account or an outdated receipt.
- New history labels cover QR creation, pending, failed, expired and simulation,
  retaining legacy checkout labels and actual `awarded_credits`. Existing
  checkout receipts use separate storage and are not mistaken for QR payments.

## Verification

All automated provider calls are mocked; no real transaction was made.

- Red-to-green slices reproduced missing package config/QR creation,
  regeneration and QR labels, stale account refresh after logout, suppressed
  balance-refresh errors, missing selection-triggered generation and stale
  simulated evidence. Final page/helper boundary has 34 passing rendered tests.
- `.venv/bin/python -m unittest discover -v`: 279 passing tests, including 72
  payment router tests. AI, Google and PayMongo are mocked; temporary SQLite is
  used. TestClient runs outside its known sandbox limitation.
- `(cd game && npm test && npm run build)`: 202 passing working-tree React tests,
  TypeScript checking and production build. Includes prior unrelated frontend
  changes, which are excluded from this checkpoint.
- An isolated HEAD snapshot with only the four selected frontend files passes
  195 React tests, TypeScript checking and production build.
- Playwright against the temporary synthetic server checked a real package
  selection, countdown, cancellation/reload, regeneration, expiry, simulation
  error/retry, balance and later provider evidence. A separate browser context
  restored a pending QR from account history and retained it after reload.
- Desktop 1366×900, portrait 390×844 and landscape 844×390 had no horizontal
  page overflow; QR/actions remain reachable by page scrolling. Actual
  Tab/Shift+Tab navigation produced a visible 2px focus ring. The initial
  programmatic-focus assertion was corrected to keyboard navigation.
- `git diff --check` passed. Live Google/PayMongo, real PostgreSQL, hosted and
  installed native/physical-device checks are separately unverified.

## Standards

Independent review found zero hard documented-rule violations. Two nonblocking
judgment calls concerned duplicate balance-refresh handling and unrestricted
lifecycle/provider types. Shared `refreshAfterPayment`, `TopupStatus` and the
provider union address them. Historical status strings retain the unknown-status
fallback intentionally. Follow-up review found zero remaining findings.

## Spec

Independent review found two P2 issues: selecting a package did not generate a
QR, and paid simulation stopped refreshing current receipt evidence. Rendered
regressions reproduced both. The chooser now begins with an empty placeholder,
and paid simulated receipts continue checking. A real browser selection and
simulation-to-provider resume confirm those paths with synthetic responses.
Follow-up review found zero remaining findings; checkout retirement stays in
ticket 06.

Review summary: Standards 0 remaining findings (2 suggestions addressed);
Spec 0 remaining findings (2 issues resolved). Review inspection is separate
from executed checks and user approval.

## Remaining

Ticket 06, user visual review and separate live provider/PostgreSQL/device
checks remain. This checkpoint is local only: no push or deployment. Frozen
`main`, hosted services and unrelated working changes/deletions are preserved.

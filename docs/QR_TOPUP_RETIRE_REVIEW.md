# Hosted-checkout retirement

Ticket 06 is implemented locally on `feature/question-first-room`, 2026-10-07,
against starting commit `839cbf0`. This completes the local QR migration;
publication, deployment and live integration are separate steps.

## Behavior

- QR top-up creation is the single active purchase path. The hosted-checkout
  creation route, request schema and provider creation call are removed.
  `POST /api/payments/test/checkout` returns 404 and is absent from OpenAPI.
- Existing purchases and credit awards are not rewritten or deleted. Legacy
  checkout receipts retain account ownership checks or the existing anonymous
  hashed bearer token. Valid signed legacy paid notifications still reconcile
  pending receipts, awarding eligible account credits once.
- Anonymous legacy receipts retain their zero-account-credit behavior.
  Invalid tokens, mismatched financial references and duplicate notifications
  retain the existing protections. Old mobile return URLs remain navigation
  only: redirects cannot confirm payment or award credits.
- Account and PostgreSQL test fixtures create QR top-ups through the active
  API. Legacy reconciliation tests seed receipts through the public purchase
  store boundary; a migration fixture represents an older anonymous row.
- Obsolete page copy/styles and run instructions now describe QR top-ups.
  No account schema, balance calculation, defense policy or live-money behavior
  changes. Sandbox simulation remains a separately labeled, test-key-gated
  fixture, not evidence of provider payment.

## Verification

All executed provider interactions below are mocked.

- A red-to-green FastAPI/TestClient regression reproduced the legacy endpoint
  returning 201 before retirement. It now returns 404 with no provider request
  or credit award, including anonymous and unconfigured requests.
- `.venv/bin/python -m unittest test_payment_sandbox test_accounts -v`:
  91 passing checks. New regressions cover pending/paid legacy preservation,
  later signed settlement, replay and token-protected anonymous reconciliation.
- `.venv/bin/python -m unittest discover -v`: 272 passing tests, temporary
  SQLite, AI/Google/PayMongo mocked. TestClient ran outside its known sandbox
  limitation. The count replaces ten obsolete checkout-creation tests with
  three retirement/compatibility regressions; QR equivalents retain creation
  authentication, CSRF, replay, concurrency, throttle and error coverage.
- `(cd game && npm test && npm run build)`: 202 working-tree React tests,
  TypeScript checking and production build passed. This includes unrelated
  prior frontend work, which is excluded from this checkpoint's commit.
- An isolated starting-HEAD frontend with only the three selected payment-page
  files passed 195 React tests, TypeScript checking and the production build.
- Playwright opened the newly built page in a separate synthetic browser
  context at portrait 390×844. QR generation and purchase history controls
  were present, the old checkout creation control was absent, and there was
  no horizontal page overflow. This is a mock UI smoke check, not a provider
  transaction or proof about the real router. Ticket 05 records the broader
  desktop/portrait/landscape walkthrough and review captures.
- Production-code search found no old creation-route caller in `game/` or
  `mobile/`; `git diff --check` and Python compilation passed.

## Standards

Independent read-only review found zero documented-standard violations.
One low-priority possible Duplicated Code concern remains: account and payment
tests separately construct the three-stage QR provider resource fixture and
mock response wrappers. A shared test-only fixture builder could reduce future
maintenance. Deferred because it is not a correctness blocker or needed for
retiring creation; it does not affect production behavior.

## Spec

Independent read-only review found zero missing, incorrect or extra behavior.
The removed creation path, single QR UI, legacy record reconciliation,
documentation and offline gate satisfy ticket 06. Review inspection is
distinct from executed checks and user approval.

Review summary: Standards 1 low-priority maintainability suggestion, 0 rule
violations; Spec 0 findings.

## Local review and remaining work

The temporary synthetic page is <http://127.0.0.1:8778/?payments=test>;
[ticket 05 captures](QR_TOPUP_PAGE_REVIEW.md#local-preview) remain available.
It uses synthetic accounts/receipts and a non-payable image, with no secrets or
external provider interaction. User visual approval is still pending.

Real PostgreSQL, Google/PayMongo, hosted and installed native/physical-device
checks remain separately unverified. The pre-existing untracked payment-flow
draft is preserved, not included in this migration commit; README and the
account deployment guide describe the active contract. No push or deployment
was performed. Frozen `main`, live services and unrelated edits/deletions are
unchanged.

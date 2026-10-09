# Spec: QR Ph sandbox top-up

Status: ready-for-agent
Created: 2026-10-06

Related: `docs/adr/0001-qr-ph-top-up.md`, `CONTEXT.md` (*Top-up*).

## Problem Statement

A host who has used up their test credits cannot add more without leaving the app
for a PayMongo-hosted page, and even then has to wait for a browser redirect and
a polled receipt to believe the payment went through. The provider page shows
PayMongo's own UI, not a code the host can scan on the screen in front of them,
and the outcome depends on the host staying on a redirect rather than on the
payment simply being confirmed.

## Solution

The account payment screen becomes a **Top-up**: the host picks a preset package
and a **dynamic QR Ph** code appears in the app. The host scans it with their
banking or e-wallet app and pays; the app confirms automatically from the signed
provider webhook and shows the new test-credit balance in place. QR codes expire
after 30 minutes, so the screen shows a countdown and can regenerate. Everything
runs in PayMongo test mode — no real money moves, and a test QR is never scanned
by a real wallet.

## User Stories

1. As a signed-in host, I want to open a Top-up screen from the account area, so
   that I can add test credits without leaving the app.
2. As a signed-in host, I want to choose a preset package, so that I know exactly
   how many credits I am adding and at what price.
3. As a signed-in host, I want a QR code to be generated automatically as soon as
   I choose a package, so that I do not have to interact with the provider.
4. As a signed-in host, I want to see the QR code prominently on the screen, so
   that I can scan it with a separate device's banking app.
5. As a signed-in host, I want the QR code to encode the exact amount, so that I
   do not have to enter the amount in my banking app.
6. As a signed-in host, I want to see a live countdown of how long the code is
   valid, so that I know whether it is still usable.
7. As a signed-in host, I want to regenerate an expired or cancelled code, so
   that I can try again without reloading the page.
8. As a signed-in host, I want to cancel a top-up I started by mistake, so that a
   stale code does not linger on screen.
9. As a signed-in host, I want the app to confirm the payment automatically once
   I have paid, so that I do not have to click anything to finish.
10. As a signed-in host, I want the credits to be added only after the server
    verifies the payment, so that a dropped connection or browser return cannot
    grant me credits I did not pay for.
11. As a signed-in host, I want the new balance shown immediately after the award,
    so that I can see the top-up worked.
12. As a signed-in host, I want a failed or expired payment to be shown plainly,
    so that I understand nothing was charged and can retry.
13. As a signed-in host, I want duplicate provider notifications to award credits
    exactly once, so that my balance cannot be inflated by a repeated event.
14. As a signed-in host, I want my top-up history to appear with my balance, so
    that I can see prior additions.
15. As a signed-in host, I want to be told when the server is not configured for
    sandbox payments, so that I do not attempt a top-up that cannot complete.
16. As a signed-in host, I want to be told a live-money mode is not enabled, so
    that I never expect a real peso charge.
17. As a signed-in host on a phone browser, I want the QR and countdown to fit the
    screen, so that I can complete a top-up on mobile.
18. As a signed-in host in the native Android/iOS shell, I want the top-up to work
    the same as in a phone browser, so that access is consistent across devices.
19. As a signed-in host opening a previously started top-up, I want to see its
    current state, so that I am not forced to start a new one.
20. As a signed-in host who lost the response to a create request, I want the same
    package request to reuse the same top-up, so that I am not charged twice for
    one intent.
21. As an operator running the sandbox, I want to simulate a paid top-up on one
    screen, so that the award-and-display loop is demonstrable without a second
    device.
22. As an operator running the sandbox, I want the simulate action to be
    impossible when a live key is configured, so that it can never fabricate a
    real award.
23. As an operator, I want to drive a genuine provider scenario through the
    provider's test URL, so that the real integration path is exercised, not just
    the simulate shortcut.
24. As an operator, I want to reject any non-test key, so that live charging
    cannot accidentally be turned on by configuration.
25. As a signed-in host, I want my existing voucher-free access to keep working
    unchanged, so that adding top-ups does not affect how runs are authorized.
26. As a signed-in host, I want run charging to stay ten test credits per defense
    run, so that the top-up only changes how credits arrive, not how they are
    spent.
27. As a signed-in host, I want the top-up to replace the old hosted-checkout page,
    so that there is exactly one place I add credits.

## Implementation Decisions

### Domain language

- **Top-up** replaces *Sandbox purchase* as the term for adding credits to an
  account balance (see `CONTEXT.md`). **Credit award**, **Run reservation**, and
  **Run charge** are unchanged.
- A **Credit award** remains once-only per verified payment, granted in the same
  transaction that marks the top-up paid.
- Balance stays **credit-denominated**. Peso is only the price of a package.

### QR generation and provider interaction

- Use the PayMongo **dynamic QR Ph** path, not Hosted Checkout:
  1. create a **Payment Intent** with `payment_method_allowed: ["qrph"]`, the
     package amount in centavos, PHP, and the top-up id as `description`/
     reference,
  2. create a **Payment Method** with `type: "qrph"`,
  3. **attach** the method, whose response carries
     `next_action.code.image_url` — a base64 QR image — and the intent status.
- Persist the QR image url (and the intent id) on the top-up row; the QR is
  rendered client-side as an `<img>`.
- A QR is single-use, amount-encoded, and expires after 30 minutes by default.
  The row stores an expiry; the UI derives the countdown from it.
- These three provider calls are wrapped behind the existing payments seam; no
  new module boundary is introduced. The wrapper is the only place that knows the
  provider's call shape.

### Confirmation

- Credits are awarded **only** by a verified, signed webhook for the payment
  intent, reusing the existing once-only ledger insert inside a transaction.
- Supported events: `payment.paid` (award), `payment.failed` (mark failed, no
  award), `qrph.expired` (mark expired, no award).
- Polling the top-up's status is allowed for **display only**; it must never
  grant credits. The webhook remains the sole grant path.
- The webhook validates: test mode only, signature freshness and HMAC, the
  amount and currency match the package, the reference maps to a known top-up,
  and the payment id is not already recorded against another top-up.

### Store and schema

- Extend the existing order/receipt/ledger shape rather than adding a parallel
  store. An order row gains a **provider discriminator** (`checkout_session` vs
  `payment_intent`) plus the intent id, QR image url, and expiry. New top-ups are
  `payment_intent`; the ledger table and its `ON CONFLICT(order_id) DO NOTHING`
  award are reused unchanged.
- `begin` reserves a top-up for an account against a request id (idempotent,
  account-scoped), keeping the existing per-window attempt limit. `register`
  records the intent id + QR url + expiry. `record_paid` is generalised to
  reconcile a payment-intent event as well as a checkout-session event.
- Store API (conceptual, not final names):
  - `begin(account_id, package, request_id) -> top-up row`
  - `register(order_id, intent_id, qr_image_url, expires_at) -> row`
  - `record_paid(order_id, intent_id, payment_ids) -> None` (once-only award)
  - `mark_failed(order_id) -> None`, `mark_expired(order_id) -> None`
  - `get(order_id) -> row | None`, `history(account_id) -> list[row]`

### HTTP surface (payments router)

- Reuse the existing `/api/payments/test/*` family and the `/?payments=test`
  route; the page becomes the QR-first top-up. Hosted Checkout creation is
  removed.
- Package selection is server-owned: the body may choose a **package id**, never
  an amount, currency, or credit count.
- Endpoints (conceptual): a config endpoint advertising test mode and the
  available packages; a create endpoint returning the top-up id + QR image +
  expiry; a status endpoint returning current state (display only); the existing
  signed webhook endpoint adapted to the payment-intent envelope; and a
  simulate endpoint that is **rejected unless a test key is configured**.
- All account-owned reads require the owner's account session; CSRF applies to
  state-changing calls as it does today.

### Packages

- Ship **one preset package**, PHP 100 → 100 test credits, matching today's
  fixture, held server-side and returned by the config endpoint. The shape allows
  additional presets later without a schema change.

### UI

- The top-up page shows: package selection, the QR image, the amount, a 30-minute
  countdown, a regenerate action, a cancel action, status/error copy, and the
  refreshed credit balance after award.
- States to render: choosing, generating, awaiting scan, paid-and-applied,
  failed, expired, cancelled, and provider-unconfigured.
- The standalone page replaces the hosted-checkout flow; there is **no in-room
  entry point** and the room keeps its current behavior.

### Sandbox boundaries

- Test mode only: an `sk_test_` key is required; any other key disables the
  feature. Live mode is a separate future config/go-live decision.
- A test QR must never be scanned by a real wallet. Sandbox exercises the flow
  via the provider's test URL and the test-key-gated simulate action.

## Testing Decisions

- Good tests assert **external behavior**: the store's observable row/award
  outcomes, the router's HTTP responses and side effects, and the page's rendered
  state — not private helpers or call sequences. Provider and network calls stay
  mocked; no live provider call is made in the suite.
- **Store seam** (`purchase_store`): new tests alongside `test_purchase_store.py`
  covering reserved-then-registered top-up state, the once-only award on a
  repeated paid event, failed/expired transitions awarding nothing, idempotent
  begin against a request id, and account scoping.
- **Router seam** (`payments`): new tests alongside `test_payment_sandbox.py`
  using the same `FastAPI` + `TestClient` + patched `httpx.AsyncClient` harness —
  create returns a QR payload in test mode; a live key disables the feature and
  never calls the provider; a signed `payment.paid` awards once; duplicate
  delivery awards once; amount/currency/reference mismatches are rejected;
  `payment.failed` and `qrph.expired` award nothing; the simulate endpoint works
  under a test key and is rejected otherwise.
- **Page seam** (`PaymentTestPage`): extend `PaymentTestPage.test.tsx` with
  mocked `fetch`, asserting the QR renders, the countdown and expired state
  render, regenerate re-requests, and the balance refreshes after a paid status.
- **Helper seam** (`lib/paymentHistory`): extend its tests for the new top-up
  statuses.
- Prior art: `test_purchase_store.py`, `test_payment_sandbox.py`, the existing
  React payment-page tests. Real-local-PostgreSQL coverage follows the existing
  `postgres_checks.py` pattern if the store change warrants it.

## Out of Scope

- Any real-money mode: live key, activated QR Ph capability, pricing, refunds,
  disputes, and KYC. This is a separate go-live decision.
- Static in-store QR codes.
- Free-form amounts (fixed preset packages only).
- An in-room entry point or any change to room behavior, run reservation, run
  charge, or voucher access semantics.
- Storing card data or any payment method other than QR Ph.
- Physical second-device payout confirmation and a live provider purchase.

## Further Notes

- The whole feature is a **sandbox fixture**. Documentation and UI copy must say
  so, and must warn that a test QR is never scanned by a real wallet.
- `main` is frozen during the review window; implementation stays on
  `feature/question-first-room`.
- Rooms are in memory and a redeploy erases them, but top-up records persist in
  the account store (SQLite local, PostgreSQL via `DATABASE_URL`).
- The QR path is derived from PayMongo's published QR Ph and QR Ph API docs;
  confirm test-mode QR simulation behavior during implementation.

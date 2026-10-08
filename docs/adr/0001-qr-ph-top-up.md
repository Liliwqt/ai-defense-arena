# QR Ph top-up with webhook-verified credit awards

Status: accepted, 2026-10-06. The webhook-only live settlement restriction is
partially superseded by [ADR 0004](0004-verified-live-payment-recovery.md),
accepted design on 2026-10-08 with implementation pending. Existing sandbox
rules and the historical decision below remain unchanged.

## Context

The sandbox top-up screen creates a PayMongo Hosted Checkout Session and awards
credits once from a signed webhook. The host asked for an in-app top-up: choose a
package, an auto-generated QR appears, scan and pay, then credits land back in
the account — confirmed automatically rather than by the payer clicking through a
provider page. QR Ph is the Philippine national QR standard; PayMongo offers a
dynamic variant that generates a per-transaction, amount-encoded, single-use code
inside the Payment Intent workflow.

## Decision

Top-ups use PayMongo **dynamic QR Ph**: create a Payment Intent with
`payment_method_allowed: ["qrph"]`, create a `type: "qrph"` Payment Method,
attach it, and render `next_action.code.image_url` (a base64 image) in the app.

- **Credits are awarded only by a verified signed webhook** (`payment.paid`),
  reusing the existing once-only `test_credit_ledger` insert. A browser return
  never awards credits. Polling the Payment Intent is allowed only to *display*
  status, never to grant credits.
- **Balance stays credit-denominated.** A top-up grants credits; peso is its
  price. Run reservation and run charge are unchanged.
- **`sk_test_` only for now.** A test-mode QR must never be scanned by a real
  wallet — doing so processes a real transaction. Sandbox testing drives the
  provider's `test_url`, plus an in-app simulate action that is hard-gated to a
  test key and impossible to reach with a live key. Going live (live key,
  activated QR Ph capability, pricing, refunds/disputes) is a separate config and
  go-live decision, not a rewrite.
- **Surface.** The top-up lives on the standalone account/payment page, has no
  in-room entry, and replaces the hosted-checkout page.
- **Packages.** Fixed preset packages (default PHP 100 → 100 credits), because a
  dynamic QR encodes an exact amount and is single-use.

## Considered options

- **Hosted Checkout (status quo).** Simplest, but shows PayMongo's page rather
  than our own QR, which does not satisfy "an auto-generated QR in the app".
- **Poll-only confirmation.** Rejected: `CONTEXT.md` requires a verified payment
  before credits are awarded, and a free-tier host restart makes polling fragile.
- **Static in-store QR.** Rejected: one reusable code with the payer entering the
  amount gives no per-transaction reconciliation.
- **Free-form amount.** Rejected: fixed packages reconcile cleanly against a
  single-use amount-encoded code.

## Consequences

- The store moves from a Checkout-Session-keyed order to a Payment-Intent-keyed
  top-up. The order/receipt/ledger shape is retained; a row gains a provider
  discriminator so both shapes share one *credit award* concept.
- Dynamic QR codes expire after 30 minutes by default (`qrph.expired`). The UI
  must show a countdown, offer regenerate, and handle expiry explicitly.
- The payer-hosted return and its browser-side receipt/attempt session keys give
  way to in-app QR state; the server remains the source of truth.

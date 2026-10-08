# Live tester release and operator checklist

This is a local release candidate on `feature/question-first-room`. Main and hosted
services are unchanged. Mocked evidence does not authorize real payments or cash refunds.

## Configuration

Use the existing Google account settings and stable HTTPS callback origin. Configure
these privately in the server environment; never put their values in source or screenshots:

| Setting | Purpose |
| --- | --- |
| `PAYMENTS_MODE=live` | Select the separate real-credit wallet; default remains test |
| `DATABASE_URL` | Durable PostgreSQL account/finance database; required on a hosted origin |
| `PAYMONGO_LIVE_SECRET_KEY` | Live provider credential, never the sandbox key |
| `PAYMONGO_LIVE_WEBHOOK_SECRET` | Signature secret for the live notification endpoint |
| `PAYMONGO_PUBLIC_BASE_URL` | Stable public HTTPS app origin |
| `LIVE_TOPUP_INVITED_EMAILS` | Comma-separated private verified-Google-email list for new purchases |
| `PAYMENT_SUPPORT_EMAIL` | Public support address; mandatory before new purchases |
| `LIVE_PAYMENTS_ENABLED=1` | Enable new purchases; unset to pause without stopping issued settlement |
| `LIVE_PAID_STARTS_ENABLED=1` | Enable new paid defenses; unset to pause paid starts |
| `FREE_ACCESS_VOUCHER` | Existing server-only free-access code; available to any signed-in account |
| `PAYMENT_OPERATOR_GOOGLE_SUB` | Stable Google subject authorized for refund review |
| `PAYMONGO_REFUND_RECONCILIATION_ENABLED=1` | Enable refund reads only after merchant capability/contract verification |

The payment notification route is `POST /api/payments/live/webhook`; subscribe to
`payment.paid`, `payment.failed` and `qrph.expired` in live mode. The sandbox route,
simulation and old receipts remain separate. Do not repoint a sandbox subscription.
Use exactly one worker and one instance. A database-backed service heartbeat prevents
overlapping room services and fences an old incarnation after takeover. Startup returns
only eligible unfinished runs from a recorded lost/stopped incarnation; unknown ownership
stays held for review. Provider recovery and the heartbeat run independently.

## What hosts see

Upload and guest joining are free. Research preparation requires access without spending
it. Every paid start/restart needs explicit 10-credit confirmation; one active defense per
host applies to voucher runs too. Opening failure releases the reservation, and retry
reserves again. Normal ending, timeouts, completed sessions and healthy-service-observed
ten-minute abandonment do not return credits. An unresolved question/coaching service
error allows free retry or End unavailable defense with a once-only credit return.

Private Account shows available/reserved/held credits, purchases, defense outcomes and
credit returns. Payment history restores original receipt terms, even after catalog changes.
The browser countdown cannot determine whether payment occurred. Signed notifications
are primary; a bounded server sweep independently checks exact bound payment intents
for missed paid notifications. Browser redirects, button clicks and customer screenshots
never award credits. Old invitations can be removed without stranding an issued receipt.

## Operator refund procedure

Customer support carries only a receipt reference and general category. Confirm receipt
ownership with the requester through support; inspect server-owned account/receipt data.
There is no customer refund button or general administrator dashboard.

1. With the configured operator Google session, send a same-origin CSRF-authenticated
   `POST /api/payments/live/operator/refunds` with `topup_id` and a short `reason`.
   A fully unused purchase enters `held`; duplicate review returns the same record.
   Reserved purchases must resolve their run first. Previously spent credits, including
   returned defense credits, require separate complaint review. Do not edit balances in SQL.
2. This application does **not** initiate a cash refund. Verify account capability and
   QR Ph claim/processing requirements before separately authorizing any dashboard action.
   Retain the app review ID, provider refund ID and reason. Uncertain provider submission
   keeps the hold; do not blindly repeat a refund.
3. After verifying the provider retrieval contract, the same operator may send
   `POST /api/payments/live/operator/refunds/{review_id}/reconcile` with `provider_id`.
   The server retrieves `https://api.paymongo.com/refunds/{id}` and requires the exact
   payment, full original amount, PHP, live mode and supported status. Partial/ambiguous
   refunds remain under review. Pending/processing retains the hold. Verified success
   removes held access once; verified failure releases it once. Subsequent paid events
   cannot re-award removed credits. Success means provider processing, not proof the
   customer has received money; verify QR claim completion separately where required.

PayMongo's [refund resource](https://docs.paymongo.com/reference/refund-resource) and
[retrieval endpoint](https://docs.paymongo.com/reference/retrieve-a-refund) document the
read contract. Its [refund guidance](https://docs.paymongo.com/docs/payment-acceptance-refunds)
describes method-specific behavior. Published event names differ between documentation
pages; this release does not guess refund-event payloads or enable them for settlement.

## Local and later hosted gates

Run `.venv/bin/python -m unittest discover -v`, then `npm test && npm run build` in `game/`.
Use `TEST_POSTGRES_URL` only for a disposable localhost database and run
`.venv/bin/python postgres_checks.py`. It creates/drops isolated databases and mocks
Google, AI and payment providers. Never supply a production database to this gate.

Before a separately approved hosted release, verify durable PostgreSQL backups/storage,
stable HTTPS Google destinations, live webhook/redelivery, actual merchant refund and
QR claim contracts, provider fees/minimums, support address and invitation list. Record
one authorized PHP 1 payment/10-credit award/run, missed-notification repair and hosted
restart recovery separately. Check actual Google sign-in, GCash and installed Android/iOS
WebViews; browser-sized previews do not prove those integrations. Pause switches must
leave issued receipts recoverable. No deployment or actual provider mutation occurs
merely by implementing or running the mocked local checks.

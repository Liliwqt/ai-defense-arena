# One-peso real-payment trial

Date: 2026-10-08. Branch: `feature/question-first-room`. Local only; no push or
deployment. Main and hosted services remain unchanged.

The user authorized one real-payment integration test at PHP 1.00 and privately
configured a live secret key. The trial uses a separate service, Google-owner
restriction, separate signing secret and local receipt database. The app's
existing PHP 100 sandbox pack, purchase amounts and 300 sandbox credits remain
unchanged. The trial awards 100 demo credits only within its own database.

## Implementation

- `payments_live_trial.py`: separate FastAPI app, fixed 100-centavo amount,
  explicit real-payment confirmation, account/CSRF validation and stable
  Google-subject ownership. No simulation or multiplayer room routes.
- `purchase_store.py`: one trial receipt per owner within a serialized
  transaction. Same-request replays reuse pending/paid receipts. Concurrent
  requests, ambiguous creation and settled receipts cannot open another QR.
- `payments.py`: shared QR and webhook helpers accept an explicit live mode;
  their default remains test mode. Legacy sandbox settings and checkout
  reconciliation remain unchanged.
- `game/live-trial.html`: isolated trial screen with real-money labels,
  confirmation checkbox, Google login, QR/status display, automatic refresh
  and demo-credit balance. Existing React payment UI is unchanged.
- `test_payments_live_trial.py`: twelve offline tests using provider fixtures.

Internal legacy table/receipt names retain their test terminology for schema
compatibility; response/UI mode is explicitly live. Database initialization
rejects existing accounts or receipts without the dedicated trial marker.
`DATABASE_URL` and other database filenames are rejected for this local trial.

## Offline verification

- Focused Python payment/store gate: 86 tests passed, providers mocked.
- Full Python gate: 284 tests passed, external providers mocked.
- Existing React gate: 202 tests passed; production Vite build passed.
- Mocked Playwright trial-page walkthrough: checkbox/create, pending QR,
  receipt restoration after reload, paid state and automatic balance refresh
  passed. No provider transaction was made by that walkthrough.
- Mocked desktop and 390-pixel portrait screenshots: real-money label and
  amount visible, no simulator button, no horizontal page overflow. Captures:
  `screenshots/one-peso-live-trial-mock-desktop.png` and
  `screenshots/one-peso-live-trial-mock-phone.png`.
- Live-trial tests cover fixed price, owner/CSRF rejection, wrong provider
  mode/amount, wrong receipt reference, live-vs-test signatures, duplicate
  awards, replay, concurrency, failed creation and isolated-store guards.

## Actual setup evidence (not a real payment)

- A separate live-mode PayMongo webhook was registered and its resource
  mode, URL, enabled status and signing-secret presence were checked.
- The temporary HTTPS tunnel was preserved. Only the dedicated local
  sandbox backend was stopped, and only its dedicated test webhook disabled.
  Original sandbox credentials, accounts and receipts are retained.
- The dedicated trial backend is on localhost 8791. Public health/page return
  200; unauthenticated trial configuration and unsigned webhook return 401;
  sandbox simulation route returns 404. Google login returns 302 with the
  existing correctly matched callback origin.
- Secrets and provider identifiers are in ignored mode-600 local records,
  never this document. The trial's live webhook must be disabled and the
  temporary backend/tunnel stopped after verification; retain receipts.

## Actual live payment verified

The operator reported completing the requested real-payment step. Read-only
verification through `/tmp/paymongo-one-peso-live-verify.py` then confirmed:

- PayMongo live-mode intent: **succeeded**, exact PHP 1.00 gross amount, PHP
  currency, and one live paid payment whose ID matches the stored receipt.
- Owner-linked local receipt: paid, paid timestamp present, amount 100
  centavos and 100 demo credits.
- Ledger: exactly one credit-award row for that receipt, totaling **100 demo
  credits**. The separate trial account has 100 demo credits.
- Original sandbox ledger remains **300 credits**. No local fixture
  simulation, direct ledger award or agent-authorized wallet payment was used.
- The API handler's live-signature-verifying notification path is the only
  settlement route exposed by the trial service. Browser redirects and
  status reads cannot award credits.

This establishes actual live QR creation/payment and automatic once-only
award for this receipt. Actual provider redelivery/races remain unexercised;
those are covered by mocked tests. Merchant payout, provider fees and bank
settlement were not inspected, and no hosted payment feature was deployed.

After verification, the agent fetched and matched the dedicated live webhook
by exact ID, callback URL and true mode, disabled only that webhook, and
confirmed its disabled status. The receipt service and temporary HTTPS tunnel
remain for review; stop them and remove only the temporary Google
origin/callback when finished. Private keys, setup records and receipt data
remain local. Public app pricing/balances and all other webhooks are unchanged.

PayMongo documents a [PHP 1 minimum and GCash support](https://docs.paymongo.com/docs/payment-acceptance-qr-ph).
Its [webhook guide](https://docs.paymongo.com/docs/developer-tools-webhook-setup-management)
specifies the live `li` signature and raw-body verification.

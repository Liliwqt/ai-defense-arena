# PayMongo QR sandbox verification

Local verification completed on `feature/question-first-room`, 2026-10-08.
This used actual Google sign-in and PayMongo test API/resources through a
temporary HTTPS tunnel to the separate localhost-8791 app. It is not a hosted
release, real-money transaction or physical-device check.

## Verified flow

- Operator saved credentials through hidden-input setup wizards into a
  Git-ignored, mode-600 file. A separate test webhook was registered; existing
  webhooks and hosted service settings were left unchanged.
- The Google callback initially failed with `redirect_uri_mismatch`. Operator
  registered the matching temporary callback. Actual sign-in produced a local
  account; account-owned QR creation used the authenticated application API.
- A read-only PayMongo intent query confirmed test mode, stored amount/currency
  and pending status. Its `next_action.code.test_url` opened the provider QRPH
  test page. API keys, account identifiers, payment references, simulator URLs
  and signing secrets are not included in this document.
- The first receipt was locally simulated by the operator. Provider test
  authorization subsequently replaced fixture evidence with the matching
  provider payment, retaining one 100-credit ledger award. This checked the
  transition from fixture to provider without another award.
- A new clean receipt was checked before authorization: pending, no payment
  reference and zero ledger rows/credits. Account ledger credits were 200.
  Agent used only **Authorize Test Payment** on its PayMongo-owned page.
- The first clean authorization attempt closed its browser before the async
  request completed. Read-only rechecks confirmed it remained pending with
  zero credits before retry. The next attempt waited for the provider POST to
  finish with HTTP 200; only then was the browser context closed.
- PayMongo then reported `succeeded`, with one matching test-mode paid payment.
  The local receipt became paid with a provider reference and paid timestamp.
  It had exactly one 100-credit ledger row; account credits increased from
  200 to 300. No app simulation action, direct store settlement or credit write
  was used for the clean receipt. Automatic settlement ran through the existing
  signature-validating webhook handler.
- An unsigned public webhook request was rejected with HTTP 401. Both local
  and temporary public health endpoints returned HTTP 200.

## Evidence boundaries

The provider API, browser test-page action and read-only receipt/ledger queries
are live **sandbox** evidence. Earlier 272 Python/202 React tests and builds use
mocked external providers; they remain a separate offline gate. No executable
application code changed during this sandbox walkthrough, so the full gate was
not repeated for these documentation updates.

The once-only claim here means one ledger award for each verified receipt,
including fixture-to-provider reconciliation. Actual provider redelivery of the
same event was not requested; concurrency and duplicate-event rejection retain
their offline test coverage. Live failure/expiry, PostgreSQL, native devices and
hosted QR deployment remain separate checks. A dashboard screenshot matched the
first actual provider receipt; it is not substituted for API/ledger evidence.

## Local handoff

The real sandbox on localhost 8791 and its temporary HTTPS tunnel remain
running for operator review. The port-8778 mock is a separate synthetic server.
Local test receipts/balances are isolated from the hosted database.

The shipped UI currently offers a separately labeled local simulation button;
it does not expose PayMongo's provider simulator URL. The temporary inspection
helper retrieved that link for this walkthrough. A validated provider-simulator
button is a possible follow-up, not implemented by this verification.

When review is finished, the temporary cleanup helper at
`/tmp/paymongo-qr-sandbox-cleanup.py` disables only this new test webhook and
stops the dedicated backend/tunnel. It retains private credentials and local
test receipts. Remove the temporary Google callback/origin from the appropriate
client manually when no longer needed, keeping hosted entries.

No push, deployment, change to frozen `main`, hosted behavior change or real
wallet/bank payment was performed.

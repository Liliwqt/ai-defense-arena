# QR top-up creation checkpoint

Implemented locally on `feature/question-first-room`, 2026-10-07, against
starting commit `eec5a88`. This is ticket 02, not the complete QR payment flow.

`POST /api/payments/test/topups` accepts a server-owned package ID and a
required request key. Google account authentication and Origin/CSRF checks
precede provider access. Success supplies the stored pending receipt, PNG QR,
amount, credits and display deadline. Request reuse is account/provider-scoped;
overlapping creation cannot start another provider attempt. Client financial
fields and non-test configuration are rejected. Hosted checkout is unchanged.

The requested QR lifetime is 1,800 seconds. Its conservative local display
deadline is measured immediately before attachment, rather than copied from a
provider expiry timestamp. It is not confirmation of expiry or payment.
Creation and elapsed time grant no credits. Incomplete creation is retained
and must not be silently recreated with the same request key.

## Verification

- Red-to-green FastAPI/TestClient tests reproduced the absent endpoint and
  rejection of a valid plain base64 QR; both pass with the implementation.
- `python -m unittest test_payment_sandbox -v`: 40 passing router tests with
  PayMongo mocked, including 16 new QR tests. These cover concurrency,
  ownership, CSRF, replay, checkout/QR request isolation, malformed/live
  resources, amount/currency validation, PNG normalization, sanitized failures
  at each provider step, throttling and no credit award at creation/expiry.
- `.venv/bin/python -m unittest discover -v`: 247 passing tests after final
  cleanup; AI, Google and PayMongo mocked. TestClient runs outside the
  filesystem sandbox because it stalls within that sandbox.
- `(cd game && npm test && npm run build)`: 186 React tests, TypeScript checking
  and production build passed. This verifies the broader working tree,
  including pre-existing account/upload frontend edits; no frontend changed
  in ticket 02.
- `git diff --check` passed. Temporary SQLite was exercised; PostgreSQL was
  not checked because `TEST_POSTGRES_URL` was unset.

## Standards

Independent review suggested sharing repeated intent-validation checks.
Shared validation now checks resource type/ID, test mode, amount and currency;
status, identity correspondence and client-key checks remain stage-specific.
Follow-up review confirms zero remaining Standards findings.

## Spec

Independent review confirms all ticket-02 criteria, including the additive
route and unchanged hosted checkout. Zero Spec findings before and after
cleanup. Reviews were read-only, not live tests.

Review summary: Standards 0 remaining findings; Spec 0 findings.

## Remaining work

Ticket 03 adds QR payment/status confirmation; 04 adds gated simulation; 05
builds the QR-first screen; 06 retires hosted-checkout creation. No provider
transaction, browser QR screen, hosted check, visual approval, publication or
deployment is claimed. Frozen `main` and current services remain unchanged.

Provider references: [QR Ph API](https://docs.paymongo.com/docs/payment-acceptance-qr-ph-api),
[Payment Method creation](https://docs.paymongo.com/reference/create-a-paymentmethod),
[Payment Intent resource](https://docs.paymongo.com/reference/the-payment-intent-object),
and [QR troubleshooting](https://docs.paymongo.com/docs/payment-acceptance-troubleshooting).

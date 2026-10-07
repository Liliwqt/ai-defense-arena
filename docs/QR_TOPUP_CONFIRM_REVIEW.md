# QR top-up confirmation checkpoint

Implemented locally on `feature/question-first-room`, 2026-10-07, against
starting commit `4f56918`. Ticket 03 adds signed QR notifications and an
owner-only stored-status read alongside the existing checkout flow.

## Behavior

- `POST /api/payments/test/webhook` verifies the raw-body signature and
  freshness before accepting test-only `payment.paid`, `payment.failed`, and
  `qrph.expired` resources. Current `data`, legacy `resource`, and flat event
  envelopes are supported; hosted-checkout notifications retain their path.
- Payment resources map to the server-owned Payment Intent ID. Amount,
  currency, payment ID, resource status and any supplied top-up metadata are
  checked. Unrelated intents are acknowledged without awards; conflicting
  references to a known receipt are rejected.
- A validated paid event settles and awards once under the existing serialized
  store transaction, including recovery after a failure, expiry, or lost
  attachment response. Duplicate payment identifiers cannot fund another
  receipt. Later failure/expiry events cannot reverse paid state.
- The validated intent ID is bound before attachment. An early event receives
  503 until registration finishes, allowing provider retry instead of loss.
  Binding collisions return a safe creation failure without changing the
  original receipt. No schema migration is required.
- `GET /api/payments/test/topups/{id}` requires the owner's account and returns
  the public stored receipt with `Cache-Control: no-store`. It never contacts
  PayMongo, infers expiry from time, or awards credits.

## Verification

All executable checks below are offline; AI, Google and PayMongo are mocked.

- FastAPI/TestClient red-to-green regressions reproduced absent awards and
  status reads, unsupported failure/expiry, an acknowledged early payment,
  conflicting references, duplicate binding errors and discarded delayed paid
  notifications. The final full gate includes 60 payment router tests (20 new
  ticket-03 tests), including concurrent paid/failure/expiry ordering.
- `.venv/bin/python -m unittest discover -v`: 267 passing tests after the final
  recovery changes. Router checks ran outside the known TestClient sandbox
  limitation. Temporary SQLite was exercised.
- `(cd game && npm test && npm run build)`: 186 passing React tests, TypeScript
  checking and production build. This covers the broader working tree with
  pre-existing frontend edits; ticket 03 changes no frontend.
- `git diff --check` passed. `TEST_POSTGRES_URL` was unset; real PostgreSQL was
  not checked. No live Google, provider transaction, hosted check, browser QR
  screen or visual approval is claimed.

## Standards

Independent review found no documented violations or actionable code-smell
findings, both before and after the final settlement recovery change.

## Spec

Independent review reproduced one P1: a valid paid event following
`creation_failed`, `failed`, or `expired` was acknowledged without an award.
QR-only settlement recovery now handles these states atomically. Follow-up
review confirmed resolution and independently checked the three paths with
temporary SQLite, duplicate delivery and unchanged legacy checkout behavior.
Zero remaining Spec findings.

Review summary: Standards 0 findings; Spec 0 remaining findings (1 resolved).

## Provider compatibility and remaining work

The public [event guide](https://docs.paymongo.com/docs/developer-tools-webhooks-events)
shows payment resources and the [quick start](https://docs.paymongo.com/docs/payment-acceptance-quick-start)
identifies `payment_intent_id` for matching. The [QR Ph guide](https://docs.paymongo.com/docs/payment-acceptance-qr-ph)
names the expiry event but does not show its complete payload. The conservative
parser accepts an expired intent resource (`awaiting_payment_method`) with
amount/currency, or a test QR resource with its intent ID; any financial fields
present in a QR expiry must match the receipt. Both variants are covered with
synthetic fixtures, not captured live events. Real sandbox expiry delivery must
still be inspected before claiming provider compatibility.

Tickets 04–06 remain: gated simulation, the QR-first screen, and retirement of
hosted-checkout creation. Frozen `main` and hosted services are unchanged. No
push or deployment is part of this checkpoint.

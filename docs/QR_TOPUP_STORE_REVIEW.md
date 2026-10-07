# QR top-up store: behavioral review fixes

Date: 2026-10-07. Branch: `feature/question-first-room`. Review baseline: latest commit `55a0228`.

## Scope and result

The user requested fixes for two reproduced ticket 01 defects before proceeding to tickets 02 and 03. Ticket 01 remains the store implementation; tickets 02–06 are still pending. This checkpoint does not create QR codes, add a QR webhook or replace the checkout UI.

1. **Registration cannot reopen a settled QR receipt.** `register_topup` updates only creating/pending purchases. A retry after payment leaves the paid status, intent, image, expiry, payment ID and paid timestamp intact. Later failure/expiry notifications and repeated paid reconciliation do not reverse the receipt or award credits again. The same guard preserves failed/expired states.
2. **Request reuse is provider-specific.** New hashed keys encode the provider, account and request as a structured tuple. A checkout and a QR top-up using the same request ID have separate records and reuse their own receipts. Compatibility lookup for the earlier hash format requires the same owner and provider; existing creating requests remain protected, and pending/paid requests remain reusable. Old hashes, purchases and credit awards do not need rewriting or a schema migration.

## Verification

- Red-to-green: the first regression reproduced paid-to-pending reset on registration retry. The second reproduced shared checkout/QR records in both creation orders. The third reproduced lost creating/pending/paid retry behavior when switching hash formats, then passed with the provider/owner-scoped compatibility lookup.
- `.venv/bin/python -m unittest test_purchase_store -v`: **9 tests passed** against temporary SQLite through public store methods. Historical hash rows are setup fixtures; assertions use store responses/history. No HTTP or provider calls.
- `.venv/bin/python -m unittest discover -v`: **231 tests passed**, external providers mocked. Python room checks ran outside the sandbox because FastAPI TestClient startup stalls inside this session's sandbox.
- `(cd game && npm test && npm run build)`: **186 React tests**, TypeScript checking and the production build passed. This includes unrelated existing account/upload tests; no frontend change is included in this checkpoint.
- `git diff --check` passed. No configured `TEST_POSTGRES_URL` was available, so real PostgreSQL and live PayMongo verification are not claimed. No new AI/provider requests, browser walkthrough or hosted check were needed for these store changes.

## Standards

Independent read-only review found **0 documented-standard violations and 0 actionable smell findings**. The changes stay at the existing transactional store boundary and preserve top-up/credit-award terminology. The compatibility tests make the two providers and legacy states explicit. No worst issue was identified.

## Spec

Independent read-only review found **0 missing requirements, incorrect implementations or scope additions** in this two-bug fix. Terminal paid receipt preservation, separate provider records and compatible existing retries are covered through public store tests. No worst issue was identified.

The earlier package-immutability and payment-verification-record suggestions remain nonblocking design opportunities; this checkpoint does not implement those refactors. Frozen `main`, hosted services, unrelated local changes and screenshot deletions remain unchanged. Publication is a later requested step.

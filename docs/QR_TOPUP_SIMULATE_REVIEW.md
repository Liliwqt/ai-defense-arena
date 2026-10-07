# QR top-up simulation checkpoint

Implemented locally on `feature/question-first-room`, 2026-10-07, against
starting commit `3e3cf69`. Ticket 04 adds a test-only router action; the screen
and simulation button belong to ticket 05.

## Behavior

- `POST /api/payments/test/topups/{id}/simulate` accepts `{}`. The owning Google
  account, Origin/CSRF checks and server test settings are required. Missing
  configuration or a live key disables the action. Extra financial or identity
  fields are rejected; no provider request is made.
- A fully created, pending, unexpired QR can be simulated. Failed, expired,
  incomplete, checkout and other accounts' receipts are rejected. Paid replays
  return the existing receipt without another award.
- The existing serialized ledger transaction awards credits once. Simulation
  and signed payment races cannot add a second award. A later validated signed
  payment may replace fixture evidence, retaining the original credit award.
  A provider payment identifier already used by another receipt is rejected
  transactionally without overwriting the simulated receipt.
- Responses explicitly say sandbox simulation and include `mode: "test"` and
  `simulated`. Private purchase history includes the same boolean, keeping
  payment identifiers private. The flag describes current receipt evidence;
  after verified provider confirmation it becomes false.
- This is the ticket's explicit sandbox fixture exception to normal signed
  webhook confirmation, not proof of payment. Existing checkout, run charges,
  account/voucher rules and schema are unchanged.

## Verification

All executable checks were offline, with AI, Google and PayMongo mocked.

- Three red-to-green router slices reproduced a missing endpoint, absent
  history label and rejection of subsequent signed payment after simulation.
- `.venv/bin/python -m unittest discover -v`: 278 passing tests, including 71
  payment router tests (11 new). Checks cover ownership, Origin/CSRF, live or
  missing settings, client fields, repeat/concurrent delivery, expiry and
  invalid states, private evidence labels and payment-identifier collisions.
  Temporary SQLite was exercised; TestClient ran outside its known sandbox
  limitation.
- `(cd game && npm test && npm run build)`: 186 passing React tests, TypeScript
  checking and production build. These checks include pre-existing unrelated
  frontend edits; ticket 04 changes no frontend.
- `git diff --check` passed. `TEST_POSTGRES_URL` was unset; PostgreSQL remains
  unverified. No real provider transaction, browser screen, hosted check,
  physical-device check or user visual approval is claimed.

## Standards

Independent read-only review found zero documented coding-rule violations or
actionable code smells. One documentation observation concerned the difference
between normal verified payments and the authorized sandbox simulation. README
and the selected `CONTEXT.md` paragraph now explicitly describe the exception.
Prior untracked ADR/planning changes are preserved separately.

## Spec

Independent read-only review found zero missing/incorrect requirements or
scope additions. Test-key gating, ownership, CSRF, once-only credit awards and
sandbox copy satisfy ticket 04. Restricting simulation to active registered QR
receipts and safely accepting later verified payment evidence preserve the
existing receipt rules. The screen remains ticket 05.

Review summary: Standards 0 code findings, 1 documentation observation resolved;
Spec 0 findings. Review inspection is separate from executed test evidence.

## Remaining work

Tickets 05–06 add the QR-first screen and retire hosted-checkout creation.
Real provider compatibility, PostgreSQL and manual screen review are separate
checks. Frozen `main` and hosted services are unchanged; no push or deployment.

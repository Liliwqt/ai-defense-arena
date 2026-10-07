# 04: Simulate a paid top-up (router, test-gated)

**What to build:** An operator can drive a paid top-up outcome from one screen
under a test key, so the award-and-display loop is demonstrable on a single
device without a second device or provider interaction. The action is impossible
when a live key is configured.

**Blocked by:** 02, 03

**Status:** ready-for-human

**Implemented:** 2026-10-07; local backend complete, manual review pending.

- [x] With a test key configured, an authenticated operator can simulate a paid
  outcome for a top-up they own and its credits are awarded once.
- [x] Simulating the same top-up twice does not award twice.
- [x] With a non-test key configured (or the feature unconfigured), the simulate
  action is rejected and awards nothing.
- [x] An unauthenticated or CSRF-less request is rejected.
- [x] The simulate path is clearly sandbox-only in copy and does not bypass the
  once-only award rule.
- [x] Router tests cover both the test-key success and the live-key rejection.

## Implementation notes

- Owner-only `POST /api/payments/test/topups/{id}/simulate` accepts `{}` and
  enforces Origin/CSRF plus test-only server configuration. No provider call.
- Active fully created QR receipts only; paid replays are harmless. One shared
  transaction awards credits once, including simulation/provider races.
- Receipt/history label fixture evidence explicitly. Later verified payment
  confirmation replaces the fixture identifier without another award.
- Offline gate: 278 Python tests (71 payment router tests, 11 new), 186 React
  tests and production build. External providers mocked; temporary SQLite.
- Independent Standards and Spec review: zero remaining findings. See
  `docs/QR_TOPUP_SIMULATE_REVIEW.md`; the screen/button belongs to ticket 05.
- No live provider/PostgreSQL/browser verification, push or deployment.

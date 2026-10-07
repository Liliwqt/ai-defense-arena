# 05: QR-first top-up page (UI) with labels and history

**What to build:** The account payment page becomes a QR-first top-up: the host
chooses a preset package, a QR image appears, and the page shows the amount, a
30-minute countdown, regenerate, and cancel, plus the refreshed credit balance.
It switches to the new top-up endpoint and renders every state — choosing,
generating, awaiting scan, paid-and-applied, failed, expired, cancelled, and
provider-unconfigured. Purchase history and its labels render the new top-up
statuses.

**Blocked by:** 02, 03

**Status:** ready-for-human

**Implemented:** 2026-10-07; local UI complete, user visual review pending.

- [x] A signed-in host can choose a preset package and see a QR image with its
  amount.
- [x] A live countdown shows the code's remaining validity, derived from the
  server expiry.
- [x] The host can regenerate an expired/cancelled code and cancel a top-up.
- [x] Once the server reports the top-up paid, the page shows the credits applied
  and the refreshed balance without a manual reload.
- [x] Failed, expired, cancelled, and provider-unconfigured states each render
  clear copy and award-nothing messaging; the never-scan-a-test-QR warning is
  present.
- [x] Package selection is the only input; the client never sends an amount,
  currency, or credit count.
- [x] Purchase history and its labels render the new top-up statuses.
- [x] Page tests extend the existing React payment-page suite with mocked fetch.

## Comments

- Public config now advertises the existing server-priced starter package.
  Explicit native package selection generates immediately; default/retry action
  is also available. Client creation sends only `package_id` and a saved request key.
- Cancel hides the QR locally, including on reload, without claiming provider
  cancellation. Expired/cancelled receipts continue watching for valid payment.
  Regenerate explicitly creates a new request; history retains old receipts.
- Simulate uses ticket 04's authenticated, CSRF-protected, test-gated route and
  labels fixture evidence. Balance refreshes automatically; later signed payment
  can replace the simulation label without another award.
- 279 Python tests, 202 working-tree React tests/build; isolated selected frontend
  195 tests/build. Providers mocked; temporary SQLite; 34 page/helper regressions.
- Synthetic desktop/portrait/landscape browser and separate-context history
  restoration passed. Five review screenshots and details are in
  `docs/QR_TOPUP_PAGE_REVIEW.md`. Independent Standards/Spec reviews: zero remaining
  findings. Live provider/PostgreSQL, user visual approval and native devices remain
  separate. Ticket 06 is pending; no push or deployment.

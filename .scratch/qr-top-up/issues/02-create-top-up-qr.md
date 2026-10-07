# 02: Create a top-up and get a QR (router, additive)

**What to build:** A signed-in host picks a preset package and receives a
top-up id, a base64 QR image to display, the amount, and an expiry. The new
endpoint is added **beside** the existing hosted-checkout endpoint so nothing
breaks; the old endpoint still works. The request may name a package but can
never choose an amount, currency, or credit count. A non-test key disables the
feature and no provider call is made.

**Blocked by:** 01

**Status:** ready-for-human
**Implemented locally:** 2026-10-07; live provider validation remains pending.

- [x] A signed-in host can create a top-up by package id and receives a top-up
  id, QR image, amount, and expiry.
- [x] The server owns the package amount and credits; a body attempting to set
  amount, currency, or credits is rejected.
- [x] Creating the same request id twice reuses the top-up without a second
  provider call.
- [x] When a non-test key is configured (or the feature is unconfigured), the
  endpoint is disabled and no provider request is made.
- [x] An unauthenticated or CSRF-less request is rejected.
- [x] The existing hosted-checkout endpoint is unchanged and still passes its
  current tests.
- [x] Router tests use the existing FastAPI/TestClient harness with the provider
  mocked.

## Comments

Ticket 02 implemented against `eec5a88`: additive authenticated QR creation,
server-owned starter package, required request key and safe provider validation.
Offline gate: 247 Python tests (providers mocked), 186 React tests and build.
Independent Standards/Spec review: zero remaining findings.
See `docs/QR_TOPUP_CREATE_REVIEW.md`; live integration, tickets 03–06,
publication and deployment are separate.

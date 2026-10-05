# Account/access deployment on the feature service

Target the existing `defense-simulator.onrender.com` service connected to
`feature/question-first-room`. Do not change frozen `main` or its
`ai-defense-arena.onrender.com` service. The root `render.yaml` is the older
free-service template; it does not provision account storage or Google settings.

The account release is prepared for manual deployment. Its commit uses
`[skip render]` until persistent storage and host authentication are configured.
Publishing the source is separate from completing the rollout.

## Storage: free now, paid when needed

The user selected Render Free with an external PostgreSQL database. The local
adapter uses `DATABASE_URL` for **all** identities, sessions, vouchers, purchases
and run-credit transactions. Without that setting, local development retains
SQLite at `PAYMONGO_TEST_DB_PATH` (default `.local/payments-test.sqlite3`). An
invalid or unavailable configured PostgreSQL database fails closed; it never
silently creates a replacement SQLite store.

Use a **Neon Free** PostgreSQL project for the initial hosted sandbox:

1. Sign in at [Neon](https://neon.com/) and create a Free project for this app.
   Choose a region near the existing Render service. Do not upgrade a plan yet.
2. In the project **Connect** dialog, select the database and role, enable the
   pooled connection, and copy the PostgreSQL connection URL privately.
3. In the **feature service** Render Environment, add `DATABASE_URL` with that
   entire URL, including its `sslmode=require` (or certificate-verification)
   option. Use **Save only** until the release is published and ready.
4. Keep the existing Render instance **Free**, with no disk and one worker/one
   instance. Do not use `PAYMONGO_TEST_DB_PATH` for hosted PostgreSQL; the URL
   takes precedence for both authentication and payments.
5. Deploy the PostgreSQL-enabled feature release after other settings below are
   ready. The server creates its additive tables transactionally on first use.
   Accounts and balances live in Neon; rooms and timers still live in Render
   memory and disappear on restarts.

[Neon connection guide](https://neon.com/docs/connect/connect-from-any-app),
[Neon plans](https://neon.com/pricing)

Neon Free has compute/storage limits and idle database compute can suspend; a
new connection can take longer to wake it. Check the current dashboard limits.
Render's own free PostgreSQL expires after **30 days**, so it is not the selected
long-term sandbox store. Free web instances still sleep and can suspend after
usage limits; upgrading hosting later does not require moving this PostgreSQL
database. Review provider backup/restore options before accepting real money.
[Render free limits](https://render.com/docs/free)

A later paid Render web instance can keep the same `DATABASE_URL` and Neon
project. A paid database tier can be chosen separately when usage warrants it.
An alternate SQLite-on-paid-disk deployment remains supported by removing
`DATABASE_URL`, attaching a persistent `/var/data` disk and setting
`PAYMONGO_TEST_DB_PATH=/var/data/payments-test.sqlite3`, but that is a different
store: switching backends does **not** copy accounts or balances. Do not switch
stores without an explicit private data migration. No paid resources are
approved or provisioned by this setup.

The initial hosted PostgreSQL store is empty. Existing local SQLite accounts,
purchases and awards are preserved locally, not automatically imported. Never
upload a database or connection URL to GitHub or share it in chat.

The sandbox deliberately serializes account transactions with a PostgreSQL
transaction advisory lock, preserving the SQLite ordering guarantee for
reservation/charge/release, voucher attempts and duplicate webhooks. It favors
correctness over high throughput. Before scaling to multiple app instances,
replace the global orphan-reservation startup cleanup and in-memory rooms with
an explicit multi-instance ownership/storage design; simply adding workers is
not safe.

### Verify the backend locally

The normal offline gate continues to use disposable SQLite databases with
AI/Google/PayMongo mocked. A separate real-PostgreSQL gate uses a disposable
**local** PostgreSQL server and creates/drops one test database per case:

```bash
TEST_POSTGRES_URL=postgresql://YOUR_LOCAL_ROLE@127.0.0.1:5432/postgres .venv/bin/python postgres_checks.py
```

The role needs local database-creation permissions. The script refuses remote
hosts. It exercises migrations, rollback, concurrent reservations, duplicate
signed webhook awards, authentication, voucher revocation and room charging
against PostgreSQL; external providers remain mocked. Never point it at the
hosted account database.

## Server environment

Enter secret values in Render's Environment settings, never in this file,
browser code, chat, or Git:

| Setting | Hosted value/purpose |
| --- | --- |
| `OPENAI_API_KEY` | Existing server-side AI credential |
| `OPENAI_MODEL` | Optional existing model override |
| `GOOGLE_CLIENT_ID` | Google Web application OAuth client |
| `GOOGLE_CLIENT_SECRET` | That client's private secret |
| `AUTH_SESSION_SECRET` | Stable random value, at least 32 characters |
| `AUTH_PUBLIC_BASE_URL` | `https://defense-simulator.onrender.com` |
| `FREE_ACCESS_VOUCHER` | Newly generated private voucher; use the local private file or a new random value |
| `DATABASE_URL` | Private Neon PostgreSQL connection URL with TLS; required for the chosen free-hosting path |
| `PAYMONGO_SECRET_KEY` | Secret **test** key; live keys are rejected |
| `PAYMONGO_WEBHOOK_SECRET` | Signing secret for the hosted test webhook |
| `PAYMONGO_PUBLIC_BASE_URL` | `https://defense-simulator.onrender.com` |

The former `GAME_HOST_PASSCODE` is unused by this release. Google configuration
is required to create or control a host room; missing settings intentionally
deny anonymous host access. PayMongo settings are needed for sandbox purchases;
configured Google plus voucher access can run defenses without checkout.

Register the exact Google redirect URI:

```text
https://defense-simulator.onrender.com/api/auth/google/callback
```

While the Google application is in Testing, add the intended host accounts as
test users. Login returns only to allowlisted same-app screens.
[Google OpenID Connect](https://developers.google.com/identity/openid-connect/openid-connect)

Register a **test-mode** PayMongo webhook for
`checkout_session.payment.paid` at:

```text
https://defense-simulator.onrender.com/api/payments/test/webhook
```

Use PayMongo's simulator for QRPh tests; do not pay a test QR code with a real
wallet or bank app. Redirects do not award credits; a verified matching webhook
does, once.
[PayMongo testing](https://docs.paymongo.com/docs/payment-acceptance-testing),
[webhook verification](https://docs.paymongo.com/docs/developer-tools-webhook-setup-management)

## Build, deploy, and verify

Use the existing commands:

```text
Build: pip install -r requirements.txt && cd game && npm ci && npm run build
Start: uvicorn game_server:app --host 0.0.0.0 --port $PORT --workers 1
Health: /health
```

After storage, settings, and callbacks are ready, deploy the selected release
with **Manual Deploy → Deploy latest commit**. A deploy erases in-memory rooms,
so create a fresh room for verification. The source commit's skip marker does
not prevent a manual deploy.
[Render manual deployments](https://render.com/docs/deploys#manual-deploys)

Confirm:

- Health returns ok and served JavaScript/CSS matches the tested release.
- Google sign-in/out returns to the main app; an anonymous visitor cannot host.
- Voucher redemption grants free runs and exposes no account details to guests.
- A simulator checkout awards 100 test credits once after its signed webhook.
- A paid opening failure releases its reservation; successful retry charges 10
  once. Later questions and coaching spend no additional credits.
- Guest joining, host reconnection, votes, answers, transcript, and coaching work
  in a fresh two-client code/research room.
- Accounts and balances survive a deliberate service restart; rooms do not.

Record actual provider, hosted, and physical-device results separately from
mocked tests in `PROJECT_LOG.md`. Do not claim deployment or persistent balances
until those checks produce evidence.

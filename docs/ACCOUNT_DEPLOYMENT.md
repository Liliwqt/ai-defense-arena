# Account/access deployment on the feature service

Target the existing `defense-simulator.onrender.com` service connected to
`feature/question-first-room`. Do not change frozen `main` or its
`ai-defense-arena.onrender.com` service. The root `render.yaml` is the older
free-service template; it does not provision account storage or Google settings.

The account release is prepared for manual deployment. Its commit uses
`[skip render]` until persistent storage and host authentication are configured.
Publishing the source is separate from completing the rollout.

## Storage decision

The current implementation uses SQLite. Render Free loses local SQLite data on
restart, redeploy, or spin-down and cannot attach a persistent disk.
[Render storage limitations](https://render.com/docs/free#local-files-lost-on-redeploy)

The smallest deployment change is a paid web-service instance with a persistent
disk. This preserves the tested SQLite implementation and requires explicit
approval for the new recurring cost. Render currently lists a $7/month smallest
paid instance and $0.25/GB/month disk storage: approximately $7.25/month for that
instance with a 1 GB disk, before additional usage/taxes.
[Render pricing](https://render.com/pricing),
[persistent disks](https://render.com/docs/disks)

For that path, configure the **feature service only**:

1. Select the smallest paid instance after its cost is approved.
2. Attach a 1 GB persistent disk mounted at `/var/data`.
3. Set `PAYMONGO_TEST_DB_PATH=/var/data/payments-test.sqlite3`.
4. Keep exactly one service instance and one Uvicorn worker.

Adding a disk triggers a deploy. Configure the account settings before switching
to the new release. The disk is available at runtime, not during the build.

An external PostgreSQL service can keep the web instance free, but this release
does not implement PostgreSQL. Setting `DATABASE_URL` alone is insufficient;
the account store and its transactional tests need an explicit migration first.
Choose that path before deployment if a paid web instance is unwanted. Render's
own free PostgreSQL databases expire after 30 days; they are not indefinite
balance storage.
[Free database limits](https://render.com/docs/free#free-postgres)

Local accounts and purchases are not automatically copied to the hosted disk.
The initial hosted store is empty unless an explicit migration is performed.
Do not upload a database containing private account data to GitHub.

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
| `PAYMONGO_TEST_DB_PATH` | `/var/data/payments-test.sqlite3` under the persistent mount |
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

# Local development

Run commands from the repository root. Python with virtual-environment support,
Node.js and npm are required. Keep API keys, OAuth secrets and database URLs in
private environment variables, never browser `VITE_` variables or Git.

## Install and start

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
./run_local.sh
```

Open <http://127.0.0.1:8000/>. The launcher installs frontend dependencies when
needed, builds React, prompts privately for a missing `OPENROUTER_API_KEY`, and
loads or creates the private `.local/free-access-voucher`. It does not load `.env`;
export configuration in its terminal. Restart after Python or prompt changes.

Hosting with this launcher requires Google sign-in configuration below.
Teammates join using the room code and a display name.

## Test without Google sign-in

```bash
./run_local_test.sh --port 8001
```

Open <http://127.0.0.1:8001/> to receive a disposable Local tester account. Create
a room, upload a paper, explicitly map it, confirm its profile/budget and start.
The launcher privately prompts for the OpenRouter key if needed. Standard
requests can spend real provider credit; opening the page does not request AI.

This opt-in runner binds to loopback, rejects forwarded/cross-origin requests,
disables OAuth/payment routes and uses disposable account/document storage.
Do not expose it through a tunnel or use it on Render. Uploaded originals and
test accounts disappear when it stops. Normal hosting keeps Google authentication.

## Google host sign-in

Create a Web application OAuth client in Google Cloud. Configure its audience
and test users as appropriate for your project, then register this exact callback:

```text
http://127.0.0.1:8000/api/auth/google/callback
```

In the launching terminal, configure `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`,
`AUTH_SESSION_SECRET` (at least 32 random characters), and
`AUTH_PUBLIC_BASE_URL=http://127.0.0.1:8000`. Keep the secret stable for the server
session. Restart `./run_local.sh`, open Account and sign in. Use `127.0.0.1`
consistently; another hostname or port needs its own matching callback.

Only hosts sign in. Guests retain room-player access, while host controls also
require the creator's account. Sign-out does not pause the room's timers.

## AI and payment configuration

[OpenRouter setup](OPENROUTER_SETUP.md) documents task models, captured reasoning
settings, provider limits and recovery. New runs use the temporary low-reasoning
trial; retained runs keep their saved policies. `OPENROUTER_MAPPING_REASONING_EFFORT`
can explicitly override mapping's low default. Model quality, speed and hosted
availability require separate live checks.

For payment/account administration, use [live tester payments](LIVE_TESTER_PAYMENTS.md)
and the [payment flow map](PAYMENT_FLOW.md). Sandbox and live money are separate.
Never enable live credentials merely to preview a screen; browser payment returns
do not award credits. The owner-only one-peso integration trial has its own
[historical review and setup](ONE_PESO_LIVE_TRIAL.md).

## Preview without AI calls

Build the frontend and start the normal server directly:

```bash
(cd game && npm ci && npm run build)
.venv/bin/uvicorn backend.game_server:app --host 127.0.0.1 --port 8000 --workers 1 --ws websockets --ws-max-size 20000 --ws-max-queue 4
```

Open <http://127.0.0.1:8000/?preview=1>. These static rooms do not call AI or accept
real actions. Add `&research=1`, `&vote=1`, `&review=1`, `&clarify=1`, `&probe=1`,
`&complete=1` or `&long=1` to inspect other states. Mock previews are not evidence
of real provider performance, payment success or device behavior.

For frontend development, run `npm run dev` in `game/` alongside FastAPI on port
8000. Vite proxies `/api`, `/ws` and `/health`. Test OAuth/payment callbacks on
the built app served by FastAPI so origin and cookie settings match.

## Streamlit fallback

Export `OPENROUTER_API_KEY`, then run:

```bash
.venv/bin/python -m streamlit run backend/app.py
```

See [Streamlit OpenRouter setup](STREAMLIT_OPENROUTER.md). The typed fallback
shares AI policy but has its own browser-session interface; voting, multiplayer
timers and team chat belong to the React room.

## Verification

```bash
.venv/bin/python -m unittest discover -v
(cd game && npm test && npm run build)
```

Python tests mock AI and external providers. Passing them does not establish live
question quality or latency. Read [PROJECT_LOG.md](../PROJECT_LOG.md) for measured
results and open checks. Real PostgreSQL, hosted providers and installed devices
are separate evidence.

## Hosting essentials

[render.yaml](../render.yaml) defines the build/start commands. Keep one worker
and one instance because rooms are in memory. Deployments, restarts and instance
spin-down erase active rooms. Durable accounts/balances need the configured
persistent database. Preserve the existing service/domain and configure secrets
privately; publication alone does not verify deployment or provider access.

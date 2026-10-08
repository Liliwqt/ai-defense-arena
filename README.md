# AI Defense Arena

Practice a code-project or research-paper defense with four AI panelists and up to four teammates. Questions cite exact uploaded source or extracted document text. Teammates vote for a speaker, answer under a timer, request clarification, and receive a shared coaching report.

The multiplayer app uses a flat, question-centered React interface served by FastAPI. Four panelist cards sit above the question, four defender cards below it, and a persistent bottom dock holds voting, answers, and team chat. A separate Streamlit app provides a single-browser fallback.

## Mobile website and WebView apps (feature-branch checkpoint)

The existing React room supports phone portrait and landscape, with compact seat
strips, internally scrolling questions/citations and a bottom answer/chat dock.
The same website is loaded by the new Android WebView and iOS WKWebView projects
under [mobile/](mobile/README.md); there is no separate mobile frontend or backend.

Android's local debug APK is built under `mobile/artifacts/`. The iOS project
requires macOS/Xcode and your own signing configuration; no iPhone artifact has
been built here. Installed-device, real Google return and sandbox provider checks
are still pending. The source and compact mobile header are published on
`feature/question-first-room`, and the website is deployed at
<https://defense-simulator.onrender.com>. See the mobile README for builds,
secure sign-in handoff and verification boundaries.


The compact mobile-header checkpoint is deployed: Settings and Account
icons flank a centered vote/answer timer or phase status. Room code, research
coverage and Transcript are available in Controls; question progress stays on
the question card. Desktop navigation is retained. Review the mock screen at
<http://127.0.0.1:8816/?preview=1> and the evidence in
[the header review](docs/MOBILE_HEADER_REVIEW.md). Publication and hosted verification are tracked in PROJECT_LOG.md;
website-only layout changes require no native app rebuild.

## Current branch and verification

This README describes `feature/question-first-room`: the flat room, research documents, same-question clarifications, summary downloads, answer-aware conversations, and Google host accounts with voucher or sandbox-credit access. Research and mixed defenses require a source-grounded paper map and a host-confirmed **4–100-question maximum**. Code-only defenses remain four to eight questions. The compact mobile header and existing architecture are served at [defense-simulator.onrender.com](https://defense-simulator.onrender.com), with shared timed-turn, purchase and progression modules and checkout UI compatible with account-owned receipts. Hosted health and asset hashes match the tested release; Google and test-payment configuration is enabled. A fresh signed-in defense and provider simulator purchase remain separate unverified checks. Separate Account UI and measured upload-progress work is still local. `main` stays frozen during the review window that began on October 1, 2026, and its earlier service remains unchanged.

The local account/access checkpoint, including the PostgreSQL adapter, passes **194 Python tests with AI, Google, and PayMongo mocked, 153 React tests, and a production build**. A separate **52-test gate against real local PostgreSQL**, with external providers still mocked, verifies migrations, rollback, concurrent reservations, duplicate webhooks and room charging. Two-browser mocked defenses completed all four combinations of code/research and voucher/test-credit access, including votes, clarification, answers, reconnect, transcript, and coaching. Mocked checkout/webhooks awarded 100 credits once, an opening failure released its reservation, and the subsequent code and research runs charged 10 credits each. Actual Google sign-in and a new account-linked PayMongo simulator purchase await configuration. Local desktop/landscape captures are linked in the account section below; user review is pending.

The isolated published research release passed **138 Python tests with AI mocked, 129 React tests, and a production build** using the committed lockfile. Its mocked two-browser twelve-question research and mixed defenses covered planning, budget confirmation, voting, timeout follow-up, clarification, retry, reconnect, exact PDF/code citations, export and coaching. Desktop, landscape, narrow landscape, portrait rotation and keyboard drawer controls were checked separately. These published-release checks are distinct from the newer local account/access tests.

Live evidence is separate: a local synthetic mixed/proposal defense completed twelve questions (eleven answers and one real timeout), English/Taglish adaptation, retries, clarifications, exact citations, reconnect, export and coaching. A fresh hosted synthetic mixed/proposal smoke check completed a deliberately selected four-question budget with two browser clients: planning, real voting, answers from both defenders, a same-question clarification, reconnect, transcript download and shared coaching. All 22 hosted map references and four question citations matched the uploads exactly; the session stopped at budget exhaustion with two of twelve topics addressed and the remaining gaps shown. Coaching used valid turn references and Q1-style question numbers. Hosted health and JavaScript/CSS bytes matched the tested release. These synthetic checks do not establish exhaustive coverage or consistently strong dialogue for arbitrary papers. User visual review and physical separate-device confirmation remain pending; the hosted four-question check does not replace the longer local checks.

See [PROJECT_LOG.md](PROJECT_LOG.md) for evidence and publication history. Agents and other session windows must also read [AGENTS.md](AGENTS.md) before editing.

## Architecture release checkpoint

The timed-turn, purchase persistence and shared progression modules are published
on the feature service, with checkout UI compatible with account-owned receipts. The isolated committed release passed **212 Python tests with external
providers mocked, 156 React tests, and the production build**. Separate Account
UI and upload-progress changes remain local. Hosted health and assets match the tested release. Evidence and limitations are
tracked in [PROJECT_LOG.md](PROJECT_LOG.md); main remains frozen.

## Run locally

Install Python with virtual-environment support, Node.js, and npm, then run from the repository root:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
./run_local.sh
```

Open <http://127.0.0.1:8000/>. The launcher installs frontend packages when needed, builds React, privately prompts for a missing OpenAI key, creates a private local voucher if needed, and starts FastAPI. Configure Google sign-in before hosting a room; an unconfigured server shows setup instructions and allows guest joining and visual previews. Restart it after changing Python code or prompt instructions.

| Setting | Purpose | Local configuration |
| --- | --- | --- |
| `OPENAI_API_KEY` | Server-side AI requests | Export in the launching terminal, or enter at the hidden prompt. The launcher does not save it. |
| `FREE_ACCESS_VOUCHER` | Shareable free-run voucher, redeemed by signed-in hosts | Export a new random value, or let the launcher load/create the Git-ignored `.local/free-access-voucher`. |
| `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `AUTH_SESSION_SECRET`, `AUTH_PUBLIC_BASE_URL` | Google host sign-in | Export in the launching terminal; follow the account setup below. |
| `OPENAI_MODEL` | Optional model override | Export before launching. The code defaults to `gpt-6-luna` with low reasoning effort. |

The launcher does not load `.env`. Export configuration in the launching terminal; keep secrets out of Git and `VITE_` variables. The former host passcode is no longer used by this local version. Only hosts sign in; teammates join with a room code and display name. The OpenAI key and voucher configuration stay on the server.

### Preview without AI calls

Build the frontend before starting FastAPI directly:

```bash
cd game
npm ci
npm run build
cd ..
.venv/bin/uvicorn game_server:app --host 127.0.0.1 --port 8000 --workers 1
```

Open <http://127.0.0.1:8000/?preview=1>. Preview mode uses static mock state, makes no AI calls, and does not accept room actions. Add flags to inspect different screens:

| Flag | Preview |
| --- | --- |
| `&research=1` | Research roles and document citation |
| `&plan=1` | Synthetic research map, with Controls open automatically |
| `&vote=1` | Speaker voting |
| `&coverage=1&research=1` | Longer-session progress (question 11 of 24) and topic coverage |
| `&review=1` | Reviewing an answer |
| `&clarify=1` | Same-question clarification |
| `&complete=1` | Transcript and coaching |
| `&long=1` | Long question and citation overflow |

For scope-preview variants, add `&budget=4` to view a smaller proposed budget, or `&planstatus=planning` / `&planstatus=failed` to inspect mapping status and failure copy. These fixtures make no AI requests and cannot confirm a real plan.

For frontend development, run `npm run dev` in `game/` alongside FastAPI on port 8000. Vite proxies `/api`, `/ws`, and `/health` to the backend. Check signed-in room and QR top-up flows on the built app served by FastAPI, where browser origin, OAuth callback, and CSRF settings match.

## Create and play a defense

1. Open **Account**, sign in with Google, and redeem the configured free-access voucher or obtain sandbox test credits. In **Controls**, keep or edit your prefilled display name, choose a defense type, and upload its materials. Uploading and creating the room are free. For a code demo, use [sample_project/README.md](sample_project/README.md) and [sample_project/queue.py](sample_project/queue.py).
2. Share the room code. Teammates open the same service URL and join with their own display names. The four defender seats include the host.
3. For research or mixed rooms, the host first chooses **Prepare defense**, reviews the map, edits the question maximum and selects **Confirm question budget**. Preparation requires free access or at least 10 available test credits, but deducts nothing. Start uses the voucher or reserves **10 test credits per run**, charged when the first validated question appears. The question count does not change this sandbox fixture charge. Each question appears with its panelist, optional reaction, and validated citation.
4. Every question, including follow-ups, begins with a **15-second speaker vote**. Online defenders may vote for themselves or another online defender and change their vote. The highest count wins; ties and no votes are resolved randomly among online defenders.
5. The chosen defender gets **120 seconds** to answer. Only that defender may submit. Disconnection assigns another online defender without resetting the clock. Expiry records an unanswered turn and advances the defense.
6. After completion (four to eight turns for code; coverage, budget, or host ending for research), open **Transcript** for the conversation and coaching. **Download summary** saves a text copy of questions, citations, clarifications, answers, timeouts, and coaching in your browser.

The server owns deadlines, votes, speaker selection, and accepted answers. Reconnecting in the same browser restores the current snapshot while the room exists. A host also needs a valid session for the room's creator account; guests keep their player-token access. Signing out or session expiry does not reset the room or stop teammates' timers. Signing back in with the same account restores host access while the room exists.

Restarting clears turns, votes, timers, chat, and coaching and starts a new run. Paid restarts require explicit 10-test-credit confirmation. Opening-generation failure releases the reservation; Retry reserves again without duplicate charging. After the first question, further questions, clarifications, retries, and coaching are included. Ending early after a question appears does not refund the flat charge. The budget is a question maximum, not a currency quote.

**Team Chat** is room-only defender conversation: the latest 100 messages, up to 500 characters each. Chat is excluded from panelist prompts, coaching, the transcript, and summary exports.

Phone play supports portrait and landscape in this local mobile checkpoint. The header, both seat rows, and bottom dock stay visible while question content scrolls. Controls and Transcript use a keyboard-accessible drawer.

## Defense types and panelists

| Defense type | Uploads | Speaking order |
| --- | --- | --- |
| Code project | Project source/documentation files or ZIP | Technical Architect → Security Reviewer → Product Judge → Critical Judge |
| Research paper | Direct PDF, DOCX, TXT, or Markdown documents | Methodology Reviewer → Ethics Reviewer → Impact Reviewer → Critical Reviewer |
| Research + code | Research documents and project sources in separate inputs | Same research panel; questions may connect claims and implementation |

Research modes offer **Proposal**, **Completed study**, or **Let AI infer**. Proposal guidance examines planned methods and feasibility; completed-study guidance examines reported results and limitations. When the stage is unclear, prompts instruct reviewers to ask for clarification rather than invent findings.

In code-only defenses each panelist asks one opening question and may ask **one immediate follow-up** for a material unresolved issue. All four roles must speak, producing four to eight resolved turns. A timeout counts as a resolved turn. Follow-ups are generated from the uploads and actual conversation, not a fixed second set of questions.

### Research scope, coverage and question budget

After creating a Research paper or Research + code room, open **Controls → Prepare defense**. This is an explicit, host-only AI request; uploading or joining does not automatically call the model. It receives all accepted materials and the selected research stage, maps substantive sections and important claims into ordered discussion topics, assigns reviewers, and identifies missing or unclear information. References-only material should be excluded and repetitive content grouped. These are model instructions: validate the proposed coverage during review rather than assuming every important claim was recognized.

Each topic includes its objective, assigned reviewer, gaps, and expandable source references. References resolve to the exact server-owned paper/code text, including PDF page or DOCX paragraph/table location. In mixed rooms a topic must include a paper reference and may also cite supporting code. A valid source location does not prove the model's interpretation.

The suggested maximum is **two questions per topic, bounded to 4–100**. The host can edit and **Confirm question budget**; teammates see the same map, confirmed value and evolving coverage after reconnect. If the budget is smaller than the topic count, the screen warns that some topics may remain unexplored. A failed map retains uploads and offers **Retry research map**, without creating a question. Repeated preparation invalidates confirmation of the older map. Research planning and its errors remain separate from defense/coaching state.

A research/mixed start requires the current validated map and confirmed maximum. All four research reviewers receive an opening turn in order, with one optional immediate follow-up per primary question. After the openings, the panel selects outstanding topics by reviewer expertise rather than stopping at eight turns. It prioritizes untouched topics, then useful revisits. Direct questions are the default; grounded what-if situations are occasional and prompts prohibit consecutive scenarios.

Each next-move AI request also assesses the preceding resolved turn's topic as **discussed**, **needs clarification**, or **addressed**, with a supporting question reference. Unasked topics are **pending**. The entire assessment and next move are validated before either is applied; an invalid result preserves the accepted answer and earlier coverage for host retry. “Addressed” means the topic was covered in discussion, not that the research is correct. A timeout consumes one generated question and cannot be assessed as addressed. Clarifications keep the question and do not consume another slot.

The session ends when every topic is addressed and all reviewers have participated, the approved maximum is reached, or the host chooses **End defense**. At the maximum, the next-move request may assess the final turn and complete but cannot generate another question. Early ending cancels clocks and discards stale AI results, preserves accepted answers, and marks an active unanswered turn **ended early**, separately from a timeout. With no resolved turns it shows a factual summary without requesting AI coaching. Controls and Transcript show coverage and ending reasons; text exports and coaching include remaining gaps. The question budget is not a payment quote and spends no test credits.

Streamlit mirrors preparation, confirmation, adaptive questions, coverage, early ending and research coaching. It remains a single-browser app without multiplayer voting or chat. Changing documents, defense type or research stage clears the map, confirmation and session.

Open the synthetic visual review at `/?preview=1&plan=1`. For a real AI map, start the updated local server with your own `OPENAI_API_KEY`; mock previews and offline tests do not demonstrate live map quality.

### Conversation and clarification

Technical traces operations, Security examines boundaries and safeguards, Product explores a person's workflow, and Critical tests assumptions and evidence. Research reviewers apply corresponding methodology, participant-safeguard, and impact perspectives.

The prompts encourage short questions, specific reactions to actual answers, occasional speaker-name attribution, and grounded hypothetical situations. They distinguish team claims from uploaded evidence. All substantive questions, reactions, clarification replies, and coaching are AI-generated; live quality still requires review.

Research and mixed reviewers can occasionally offer one conditional suggestion after hearing an accepted answer about a meaningful gap or tradeoff. Advice shares the existing two-sentence, 300-character lead-in limit and stays separate from the question and exact citation. Reviewers should respect constraints, accept a justified decision to retain the current approach, and defer longer advice to coaching. Openings and reactions to unanswered turns contain no suggestion. Clarification still explains the same question; advice is never credited as a team answer, strength, or proof of topic coverage. Code-only guidance is unchanged. These are prompt instructions, not a guarantee of recommendation quality; see the [local review evidence and pending live checks](docs/CONSTRUCTIVE_PANELIST_REVIEW.md).

The chosen defender can use the answer box to request simpler wording, translation, terminology, or an example. The AI interprets each submission. A clarification explains the **same question**, preserving its intent and citation without advancing, adding a turn, or starting another vote. Up to two clarifications are allowed per question. The answer clock pauses during interpretation and resumes with the remaining time.

Panelists start in English. Explicit clarification language requests carry forward until another request or a meaningful answer changes the language. Short, code-only, and timed-out answers preserve it. Taglish is supported through prompt guidance and language-context handling.

If interpretation fails, the chosen defender can retry or explicitly use the saved submission as an answer; the host may also retry interpretation. Question-generation failures retain accepted answers or timeouts for host retry. Coaching failures have a separate host retry. Accepted answers do not need to be submitted again.

## Uploads and citations

Each question request receives all accepted source files and extracted research text, plus resolved dialogue and original citations. Files, names, answers, and earlier AI messages are treated as data; private chat is excluded. The app does not execute uploaded code, search the original repository, or read files excluded by upload validation.

| Limit | Value |
| --- | --- |
| Accepted files, research and code combined | 100 |
| Combined UTF-8 source and extracted research text | 600 KB |
| Individual project text file | 200 KB |
| Compressed project ZIP | 25 MB; at most 2,000 entries |
| Individual research document | 10 MB |
| PDF length | 100 pages |

Project files must be supported UTF-8 source or documentation. ZIPs are read in memory, not extracted to disk. Hidden paths, generated/dependency directories, selected credential filenames, and unsupported ZIP entries are skipped. Upload a source-only archive rather than a checkout containing dependencies/build outputs. Review accepted names before starting; unsupported direct files and exceeded limits produce errors.

Research uploads are separate, direct files. PDFs must contain readable text on every page; encrypted, invalid, image-only, and partially unreadable documents are rejected. DOCX paragraphs and table cells are extracted in document order. OCR, figures, and reliable equation interpretation are not supported.

Every excerpt is resolved from server-owned text and validated before displaying a question:

- **Code:** filename, source line number, and exact line in a near-black monospaced panel with horizontal scrolling.
- **PDF:** filename, page, extracted line, and exact extracted text in a document-style panel.
- **DOCX:** filename and paragraph or table/row/cell location.
- **Research TXT/Markdown:** filename and text line location.

Research excerpts may include up to three surrounding lines on each side, with PDF context confined to the cited page. The cited line remains emphasized and unchanged. Code citations do not include neighbouring lines.

The document panel shows **extracted text**, not a rendered original PDF. Extraction order may differ from visual reading order, especially in columns or slide decks. Original layout and figures are not preserved. A validated excerpt establishes its location, not the correctness of the AI's interpretation.

## Architecture

| Component | Responsibility |
| --- | --- |
| `game/src/` | React account/setup drawers, flat room, question/citation UI, vote/answer/chat dock, transcript, and export |
| `game_server.py` | FastAPI HTTP/WebSocket service, authentication, room state, task scheduling, charging, and broadcasts |
| `timed_turn.py` | Synchronous voting, speaker selection, authoritative deadlines, interpretation, clarification and timeout transitions |
| `accounts.py`, `account_store.py` | Google sign-in, opaque sessions, voucher grants, private balances, atomic run reservations/charges, and additive SQLite migrations |
| `payments.py`, `game/src/payments/` | Account-authenticated sandbox QR top-ups, legacy receipt reconciliation, provider/signature validation and HTTP error translation |
| `purchase_store.py` | Transactional QR request reuse, legacy receipts, once-only credit awards and private purchase history |
| `defense_session.py` | Code/research policies, role order, optional follow-ups, coverage, resolved turns, and retained history |
| `defense_progression.py` | Shared isolated generation preparation and validated move application for FastAPI and Streamlit |
| `research_plan.py` | Structured research map, exact source references, suggested budget and scope-preview validation |
| `question_generator.py` | Shared prompts, Responses API structured output, submission interpretation, citation validation, and coaching |
| `project_files.py` / `research_files.py` | Upload validation and document extraction/location mapping |
| `app.py` | Streamlit single-browser fallback |

Endpoints: `POST /api/rooms` requires a verified account, matching origin, and CSRF token; `POST /api/rooms/{code}/join` admits guests; `WS /ws/{code}` authenticates player tokens and additionally checks the owner's account and origin for hosts. `GET /api/auth/me` returns private account/access/history data; `POST /api/auth/voucher` requires account authentication and CSRF. Research socket actions remain host-only `prepare_research_plan`, `retry_research_plan`, `approve_research_plan`, and `end_defense`. Approval and research `start` carry the current `plan_id` and integer `question_budget`; paid start/restart also requires `confirm_cost: true`. Shared snapshots carry research state, never email, account identifiers, balances, or voucher details. FastAPI serves the production React build from `game/dist`. There is no active 3D/Phaser scene.

Rooms, accepted text, chat, and coaching live in process memory. There is no stored defense-session history. Accounts and sandbox receipts use PostgreSQL when `DATABASE_URL` is set, otherwise the separate local SQLite database described below. A restart or instance shutdown loses active rooms; the downloaded summary is the team's own retained copy. Keep exactly **one worker and one instance**.

## Google host accounts, vouchers, and sandbox credits

The main app's **Account** drawer shows Google sign-in/sign-out, available and reserved test credits, voucher redemption, and purchase history. Hosts sign in; teammates do not. Account data stays private to the host. A voucher covers unlimited free runs; otherwise each defense costs **10 test credits**, regardless of its question budget. These are sandbox fixtures, not final pricing or a paper-cost estimate. Streamlit keeps its separate single-browser behavior without account charging.

The **Get sandbox test credits** link opens the QR-first `/?payments=test` page locally. The **PHP 100.00 → 100 test credits** package is a sandbox fixture. Verified matching test-mode PayMongo webhooks award once; the explicitly labeled, authenticated test-key-gated simulation is a separate fixture path. Browser redirects never award credits. No host passcode is required for top-ups or room creation.

### Step 1: view the local screen

Build React, then start a separate local server so an existing defense server does not need to be stopped:

```bash
(cd game && npm ci && npm run build)
.venv/bin/uvicorn game_server:app --host 127.0.0.1 --port 8790 --workers 1
```

Open <http://127.0.0.1:8790/?account=1> for the Account drawer, or <http://127.0.0.1:8790/?preview=1> for a mock room without AI. Without Google configuration, sign-in explains the required setup and anonymous room creation is disabled. No OpenAI key is required to inspect account/payment screens.

Local review captures: [account setup](screenshots/account-setup-desktop.png), [voucher account](screenshots/account-voucher-mock-desktop.png), [sandbox purchase/balance](screenshots/account-paid-mock-desktop.png), [completed research/coaching](screenshots/account-voucher-research-complete-mock.png), and [landscape account drawer](screenshots/account-paid-mock-landscape.png). Except the unconfigured setup screen, these use synthetic identities and mocked Google, PayMongo, and AI. They do not demonstrate actual provider sign-in or payment.

### Step 2: configure Google sign-in locally

1. Create or select a project in [Google Cloud Console](https://console.cloud.google.com/). Open **Google Auth Platform**, configure Branding with the app name and contact email, and select an External audience for personal Google accounts. Keep it in Testing; add your own Google email as a test user where requested.
2. Under **Clients**, create an OAuth client of type **Web application**. Add this exact **Authorized redirect URI**:

   ```text
   http://127.0.0.1:8790/api/auth/google/callback
   ```

   This server redirect flow does not require the browser JavaScript origins field. Use `127.0.0.1` consistently in your browser and configuration; `localhost`, another port, or another path is a different redirect URI.
3. Copy the client ID and secret privately into the **same terminal that starts FastAPI**. Do not put either secret into a `VITE_` variable or commit a downloaded client JSON. Request only the basic `openid email profile` scopes; this app does not access Drive or other Google APIs.

   ```bash
   read -r -p 'Google client ID: ' GOOGLE_CLIENT_ID
   read -r -s -p 'Google client secret: ' GOOGLE_CLIENT_SECRET
   printf '\n'
   export GOOGLE_CLIENT_ID GOOGLE_CLIENT_SECRET
   export AUTH_PUBLIC_BASE_URL=http://127.0.0.1:8790
   export AUTH_SESSION_SECRET="$(.venv/bin/python -c 'import secrets; print(secrets.token_urlsafe(48))')"
   .venv/bin/pip install -r requirements.txt
   .venv/bin/uvicorn game_server:app --host 127.0.0.1 --port 8790 --workers 1
   ```

   Stop the old port-8790 server with Ctrl+C before starting the updated one. Keep your existing PayMongo variables exported if you want to test QR top-ups too. Google-only sign-in works without PayMongo or OpenAI credentials. `run_local.sh` does not load Google values from `.env`; export them explicitly.
4. Open <http://127.0.0.1:8790/?account=1>, select **Sign in with Google**, and confirm your name, email, and initial **0 test credits** appear. The main app and payment page each return to their allowlisted originating screen after login. Signing out revokes this app's session; it does not sign you out of Google or delete your balance. Reconnecting as host requires the room creator's account as well as the saved room token.

`AUTH_SESSION_SECRET` must have at least 32 characters. It signs the ten-minute temporary OAuth state cookie; keep it private and stable for a server run. The application uses state, PKCE, nonce and verified ID-token checks through Authlib, then replaces provider credentials with an opaque eight-hour HttpOnly app cookie. Google access/refresh/ID tokens are not stored. HTTPS origins use Secure cookies; loopback HTTP is permitted for local testing. Google subject identifies an account even if its email or display name changes.

For a separate HTTPS sandbox check, set **both** `AUTH_PUBLIC_BASE_URL` and `PAYMONGO_PUBLIC_BASE_URL` to the exact public origin you browse. Register its `/api/auth/google/callback` URI in the same Google client, and its `/api/payments/test/webhook` in PayMongo. A changed tunnel hostname needs updated settings and a server restart. Auth state and app cookies must stay on the same origin throughout login and QR top-up. Keep this local checkpoint separate from both live services.

References: [Google web-server OAuth setup](https://developers.google.com/identity/protocols/oauth2/web-server) and [Google OpenID Connect](https://developers.google.com/identity/openid-connect/openid-connect).

### Step 3: configure and redeem the free-access voucher

`./run_local.sh` creates a new random voucher once at `.local/free-access-voucher`, with owner-only file permissions and a Git ignore rule. It exports that value as `FREE_ACCESS_VOUCHER` for its server; it never reuses the old host passcode. Open the file privately in your editor and redeem its value through **Account** after sign-in. For a server launched directly with Uvicorn, export the voucher in that server's terminal first:

```bash
read -r -s -p 'Free-access voucher: ' FREE_ACCESS_VOUCHER
printf '\n'
export FREE_ACCESS_VOUCHER
```

The same voucher may be shared with multiple signed-in accounts. Each gets a free-access grant; repeated redemption is harmless. The database stores its fingerprint, never the submitted plaintext. Grants have no expiry by default. Changing or removing the server environment value revokes matching grants for future runs; already authorized runs continue. A replacement voucher requires redemption again. Five failed attempts within five minutes trigger a temporary account-level throttle.

Rotating the launcher's stored voucher requires replacing its private file as well, or exporting a replacement before launch. Removing the environment variable alone is insufficient when the launcher will reload that file. To run without voucher access, start Uvicorn directly without `FREE_ACCESS_VOUCHER`.

### Step 4: configure PayMongo test credentials and a callback

In PayMongo's dashboard, switch to test mode and find your **secret test key** in the Developers settings. If your account cannot access test keys yet, finish the onboarding requested by PayMongo; an existing login does not establish API access. Do not use a live key or paste a key into chat.

For PayMongo to deliver webhooks to a local server, provide a public HTTPS development tunnel forwarding to port 8790. A loopback URL can display the UI but cannot receive PayMongo's remote notifications. Use the same public origin in your browser and `PAYMONGO_PUBLIC_BASE_URL` so the receipt remains available after redirect. Keep this separate from frozen production `main`.

Register a **test-mode** webhook at:

```text
https://YOUR-DEVELOPMENT-ORIGIN/api/payments/test/webhook
Events: payment.paid, payment.failed, qrph.expired
Legacy receipts: keep checkout_session.payment.paid
```

Copy its signing secret into the server environment. These are server settings, not React/Vite settings:

| Setting | Value |
| --- | --- |
| `PAYMONGO_SECRET_KEY` | Your `sk_test_...` secret key; live keys are rejected |
| `PAYMONGO_WEBHOOK_SECRET` | The signing secret of this test webhook endpoint |
| `PAYMONGO_PUBLIC_BASE_URL` | Your public HTTPS origin, with no path/query |
| `DATABASE_URL` | Optional server-only PostgreSQL URL; takes precedence for accounts and payments. Remote connections require TLS. |
| `PAYMONGO_TEST_DB_PATH` | Local SQLite path when `DATABASE_URL` is absent; defaults to `.local/payments-test.sqlite3` |

Enter secret values without saving them in shell history:

```bash
read -r -s -p 'PayMongo test secret key: ' PAYMONGO_SECRET_KEY
printf '\n'
read -r -s -p 'Test webhook signing secret: ' PAYMONGO_WEBHOOK_SECRET
printf '\n'
export PAYMONGO_SECRET_KEY PAYMONGO_WEBHOOK_SECRET
export PAYMONGO_PUBLIC_BASE_URL=https://YOUR-DEVELOPMENT-ORIGIN
.venv/bin/uvicorn game_server:app --host 127.0.0.1 --port 8790 --workers 1
```

Stop the earlier server on 8790 before restarting it with these settings. The regular `run_local.sh` does not load PayMongo values from `.env`; explicitly exported values are inherited. No secret value belongs in Git, browser code, screenshots, or the handoff log.

### Step 5: try the QR sandbox top-up

1. Rebuild React (`cd game && npm run build`) and restart FastAPI to load the
   new payment config. Open `/?payments=test` on the same origin used for
   Google sign-in and sign in to your account.
2. Choose **100 test credits · ₱100.00** to generate the QR immediately. The
   **Generate test QR** button also chooses that default package and retries
   a retained request after a lost response. The browser sends only its package
   ID; prices and awards are server-owned.
3. **Do not scan the test QR with a real wallet.** For a single-device fixture
   check, use **Simulate paid top-up**. It uses the authenticated test-only
   server route and explicitly labels the award as simulation. Testing actual
   provider notifications through PayMongo's test tools is a separate check.
4. Watch the server-derived countdown and automatic receipt/balance refresh.
   Expiry hides the QR without awarding credits. **Cancel top-up** hides it on
   this device, including after reload; it does not cancel a provider payment.
   Both states still monitor the receipt for later verified payment. Regenerate
   explicitly creates a separate QR; earlier receipts remain in account history.
5. Confirm the refreshed balance and actual credits added in history. A later
   signed provider payment can replace simulated evidence without adding more
   credits. Use **View top-up** to reopen an existing QR from your history.
   Running a defense still uses the existing flat ten-credit sandbox charge.

The selected account store (PostgreSQL, or a Git-ignored SQLite file locally) stores a basic Google profile (subject, name, email), hashed app sessions, minimal sandbox receipts, the once-only test-credit ledger, voucher fingerprints, and unique run reservation/charge records. Additive migrations preserve existing accounts, purchases, and awards. A signed matching paid event updates receipt and credits in one transaction. Reservations serialize concurrent starts; first-question charges and repeated messages are idempotent. Server startup releases orphaned reservations because active rooms do not survive a restart. Published questions remain charged.

Private account endpoints expose only the current user's access/balance and latest 20 purchases; mutations validate origin and session CSRF. WebSocket host controls recheck account ownership and origin. Uploaded files, room dialogue, and team chat are not stored in this database. Existing anonymous paid receipts stay separate and receive no retroactive credits. Local SQLite accounts/balances survive a Python restart. For hosted Render Free, use a Neon Free PostgreSQL project through `DATABASE_URL`; configuring a URL never migrates existing SQLite data. The PostgreSQL adapter serializes account transactions and never falls back to SQLite on connection failure. See the [deployment guide](docs/ACCOUNT_DEPLOYMENT.md) for setup and the separate real-local-PostgreSQL verification gate. Hosting and database paid tiers can be upgraded later while keeping the same store. Upload-based quotes, real credit pricing/spending, and real-money enforcement remain separate checkpoints.

Integration references: [PayMongo Hosted Checkout](https://docs.paymongo.com/docs/payment-channels-hosted-checkout), [test checkout quick start](https://docs.paymongo.com/docs/payment-channels-hosted-checkout-quick-start), [QRPh simulator guidance](https://docs.paymongo.com/docs/payment-acceptance-testing), and [webhook signatures](https://docs.paymongo.com/docs/developer-tools-webhook-setup-management).

### QR top-up creation checkpoint (local backend)

Ticket 02 adds `POST /api/payments/test/topups`; ticket 06 has now removed
hosted-checkout creation. Existing checkout receipts remain supported.
It requires a signed-in Google account, the existing Origin/CSRF headers,
and an `Idempotency-Key` containing 16–128 letters, digits, underscores or
hyphens. Send only `{"package_id":"starter"}`. The server fixes this sandbox
package at PHP 100 (`10000` centavos) for 100 test credits; client amounts,
currencies and credit counts are rejected.

The response contains `topup` with its ID, amount, currency, credits, pending
status, PNG `qr_image_url`, creation time and `expires_at`. A first creation
returns 201; a replay returns 200 with the stored receipt and makes no further
provider requests. Concurrent/incomplete requests return 409 instead of
creating another QR. Creation errors are retained for inspection and cannot
be automatically recreated using the same request ID.

Reuse the server-only PayMongo test settings above. Missing settings or a live
key disable creation. The backend creates a Payment Intent, a QR Ph Payment
Method and an attachment; it keeps provider credentials out of the response.
The requested QR lifetime is 1800 seconds. `expires_at` is a conservative local
display deadline measured before attachment, not confirmation of provider
expiry or payment. Creation and deadline passage award no credits.

This creation checkpoint is backend-only. Tickets 03–04 below add QR
confirmation/status and test simulation; ticket 05 adds the QR-first screen.
Hosted-checkout creation is now retired; existing receipts still reconcile.
No live PayMongo integration is claimed; do not scan a sandbox QR with a real
wallet. Provider details: [QR Ph API](https://docs.paymongo.com/docs/payment-acceptance-qr-ph-api),
[Payment Method creation](https://docs.paymongo.com/reference/create-a-paymentmethod),
and [QR troubleshooting](https://docs.paymongo.com/docs/payment-acceptance-troubleshooting).

### QR top-up confirmation checkpoint (local backend)

Ticket 03 handles `payment.paid`, `payment.failed` and `qrph.expired` on the
existing `POST /api/payments/test/webhook`. Keep the earlier
`checkout_session.payment.paid` subscription and add these three test events
to your test webhook when exercising QR top-ups. No additional secret setting
is required. Configure the server with that endpoint's signing secret.

The server verifies the raw-body HMAC and its five-minute timestamp window
before parsing. QR events and resources must explicitly be in test mode.
Payments are matched by their stored Payment Intent ID; supplied top-up
metadata must agree. Paid and failed payments require an integer amount and
currency matching the receipt. A valid paid event marks the receipt paid and
awards its credits once, in one transaction. A later valid payment may recover
an earlier failure, expiry or lost creation response; later failure/expiry
events cannot reverse a paid receipt. Duplicate or concurrent deliveries
cannot add a second award, and a payment ID cannot fund another receipt.

The intent ID is saved before QR attachment. Events arriving while creation
is incomplete receive 503 for retry. Valid unrelated intents are acknowledged
without changing local accounts; conflicting references to a known receipt
are rejected. Failure and expiry events alone award nothing.

`GET /api/payments/test/topups/{id}` returns `topup` with the same public receipt
fields as creation, restricted to its owning signed-in account. It reads stored
state only: no provider request, time-based expiry transition or credit award.
No CSRF token is needed for this read. A query parameter or browser return
cannot mark a receipt paid. Responses are not cached.

Offline tests cover signed payment resources and intent/QR-resource expiry
variants. PayMongo's public guides describe the expiry event but do not show
its complete resource payload; real sandbox delivery compatibility is still
unverified. Test simulation is implemented below; the QR screen is implemented below.
See [the confirmation review](docs/QR_TOPUP_CONFIRM_REVIEW.md).
Provider references: [webhook event structure](https://docs.paymongo.com/docs/developer-tools-webhooks-events),
[QR Ph events](https://docs.paymongo.com/docs/payment-acceptance-qr-ph),
and [signature verification](https://docs.paymongo.com/docs/developer-tools-webhook-setup-management).

### QR top-up simulation checkpoint (local backend)

Ticket 04 adds `POST /api/payments/test/topups/{id}/simulate` with an empty
JSON body `{}`. It requires the owning Google account, the existing Origin/CSRF
headers, and configured server-only PayMongo test settings. Live keys and
missing settings disable the action. Client-supplied amounts, credits, account
IDs and payment IDs are rejected.

Simulation awards the server-priced credits once using the same transactional
ledger as payment confirmation. It requires a fully created, pending QR whose
stored deadline has not passed. Failed, expired, incomplete and checkout
receipts cannot be simulated. Repeating an already paid top-up returns its
receipt without another award.

This is an explicitly labeled sandbox fixture exception to ordinary signed
webhook confirmation: no provider request or real payment is made. The response
includes `mode: "test"`, a written sandbox message and `topup.simulated`.
Private purchase history also includes that flag; provider payment identifiers
remain private. A later validated signed payment can replace the fixture's
payment evidence without adding credits, changing `simulated` to false.

The QR-first screen and its simulation button are implemented in ticket 05
below; hosted-checkout creation is now retired. Ticket 04 itself adds no UI. All verification used mocked providers and temporary SQLite, not a live payment. See
[the simulation review](docs/QR_TOPUP_SIMULATE_REVIEW.md).

### QR-first top-up screen checkpoint (local)

Ticket 05 connects `/?payments=test` to the QR endpoints above. The public
config advertises server-owned packages; the page lets a signed-in host choose
one and immediately generate its QR. It shows the amount, countdown,
simulation, cancellation and regeneration, plus account balance and history.
The existing **Get sandbox test credits** link opens this screen.

Creation, checking and confirmation are distinct. The request key is saved
before creation and reused after a lost response. Pending, failed, expired and
locally cancelled receipts remain monitored for later authoritative payment.
A paid receipt refreshes the balance automatically; simulated evidence keeps
refreshing until replaced by provider confirmation. A balance-refresh failure
retains the paid receipt and provides a manual retry. QR receipt references are
account-scoped locally; the server still enforces ownership on every request.
Only normalized PNG data images are displayed. Native resume and browser focus
refresh receipt/account data without trusting a redirect.

Cancel is a local display action, not provider cancellation or refund. Local
expiry and cancellation award nothing; history reflects server states and
actual `awarded_credits`, with explicit simulation labels. Regeneration starts
a new request; earlier receipts remain in the account's bounded history.

Local checks: 279 Python tests (external providers mocked), 202 working-tree
React tests and build; the isolated selected frontend passes 195 tests and
build. A synthetic browser walkthrough checked desktop, portrait and landscape,
keyboard focus, QR lifecycle/retry, automatic balance and later provider evidence.
See [the page review](docs/QR_TOPUP_PAGE_REVIEW.md) and
[desktop](screenshots/qr-topup-mock-desktop.png),
[portrait](screenshots/qr-topup-mock-portrait.png), and
[landscape](screenshots/qr-topup-mock-landscape.png) captures.
These are mock fixtures, not live payments or physical-device checks. Ticket 06
is complete locally below; real provider verification remains pending. No push or deployment.

### QR top-up migration complete locally

Ticket 06 removes `POST /api/payments/test/checkout`, its request schema and
provider-creation code. The QR-first `/?payments=test` page is the only new
purchase flow: `POST /api/payments/test/topups` creates a server-priced QR,
owner-only reads display its status, signed notifications confirm payment,
and the explicit test-gated simulation provides a sandbox fixture path.
No live-money mode is enabled. The ten-credit defense charge is unchanged.

Existing checkout rows, history and awards are preserved. Keep the legacy
`checkout_session.payment.paid` webhook subscription alongside QR events so
outstanding older purchases can still settle exactly once. Account-owned
legacy receipts remain readable at `/api/payments/test/orders/{id}`; anonymous
legacy receipts retain hashed-token access and gain no account credits.
The fixed mobile return page remains available for older links and awards
nothing. Neither it nor the receipt lookup creates a new checkout.

Current gate: 272 Python tests with external providers mocked, 202 working-tree
React tests and production build. Account/credit integration now exercises QR
creation and signed QR payments; separate legacy fixtures verify existing
checkout reconciliation, ownership and migration. The prior QR page's synthetic
layout checks remain applicable. User screen review, real provider/Google,
real PostgreSQL, native devices and hosted verification remain separate.
See [the retirement review](docs/QR_TOPUP_RETIRE_REVIEW.md). No push or deployment.

## Streamlit fallback

Configure `OPENAI_API_KEY` in the launching terminal, optionally set `OPENAI_MODEL`, then run:

```bash
.venv/bin/streamlit run app.py
```

The fallback supports all three defense types, the corresponding four-role sequence, validated citations, conversational lead-ins, and same-question clarifications. It keeps its separate appearance and browser-session state. Voting, answer deadlines, and team chat belong to the multiplayer room.

## Render configuration

The account/access release has a separate [feature-service deployment guide](docs/ACCOUNT_DEPLOYMENT.md), including persistent storage, hosted Google callbacks, voucher settings and test webhooks. Its publication uses `[skip render]` until those prerequisites are configured; no paid resources are provisioned automatically.

[render.yaml](render.yaml) defines the single-service deployment:

```text
Build: pip install -r requirements.txt && cd game && npm ci && npm run build
Start: uvicorn game_server:app --host 0.0.0.0 --port $PORT --workers 1
Health: /health
```

The currently published research release uses `OPENAI_API_KEY` and `GAME_HOST_PASSCODE`, plus optional `OPENAI_MODEL`, in its own service environment. This local account/access update replaces the passcode with Google authentication and voucher/test-credit eligibility; it is not deployed. Keep both existing services unchanged during review. Select durable hosted account/payment storage and configure exact HTTPS Google/PayMongo callbacks before a later account rollout. A feature service's configuration is independent of frozen `main`.

The service hosts UI, API, and WebSocket on one origin. HTTPS pages use `wss://` automatically. Teammates on other devices need a hosted URL; `127.0.0.1` refers to their own device. Restarts and redeploys require fresh rooms.

## Checks and troubleshooting

```bash
.venv/bin/python -m unittest discover -v
(cd game && npm test && npm run build)
```

AI, Google, and PayMongo calls are mocked in the Python suite. Tests confirm behavior and validation, not live dialogue quality, real provider integration, or deployment. Record live dialogue, browser layout, hosted operation, and physical separate-device checks separately in the handoff log.

- **Google sign-in unconfigured:** export the four account settings in the terminal starting the server. The callback port and `AUTH_PUBLIC_BASE_URL` must match the origin opened in your browser. Anonymous host access stays disabled.
- **Host session expired:** sign in with the room creator's Google account. Guests and timers continue; the saved room token alone cannot grant host controls.
- **Insufficient test credits:** redeem the server's voucher or obtain the sandbox credit pack. Uploading and joining are free; research preparation requires eligibility but does not deduct credits.
- **Missing frontend build:** run `npm ci && npm run build` in `game/` before starting FastAPI directly.
- **AI failure:** check the displayed safe error category and retry. A rejected key, unavailable model, rate/credit limit, or connection failure may require different fixes. `OPENAI_MODEL` overrides the default.
- **Citation rejected:** the model supplied an invalid file or line. Validation blocks it; the host can retry with the prior answer retained.
- **Room missing:** a process restart erased it. Create a fresh room and share its new code.

Coaching is qualitative practice guidance: strengths, improvements, and a next step tied to actual resolved turns. It supplies no numeric score and must not treat missed answers as responses.

## Live tester payments (local release candidate)

The normal live flow is `/?payments=live`: PHP 1/5/10 purchases provide 10/50/100 credits;
starting a defense reserves 10 credits and its first validated question finalizes the
charge. Later questions, clarifications, retries and coaching are included. A valid
voucher takes precedence and spends zero credits. Demo credits remain separate and
visible in Earlier test history. This implementation has not enabled hosted payments.

Read [the local release and operator checklist](docs/LIVE_TESTER_PAYMENTS.md) before
configuring live credentials. The purchase invitation list controls only new top-ups;
non-invited signed-in accounts can still redeem a voucher, join, or use existing credits.
Financial records use the existing durable account database. Rooms still disappear on
restart; unfinished eligible charges receive one recorded credit return, not a money refund.

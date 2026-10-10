# AI Defense Arena

Practice a code-project or research-paper defense with four AI panelists and up to four teammates. Questions cite exact uploaded source or extracted document text. Teammates vote for a speaker, answer under a timer, request clarification, and receive a shared coaching report.

The multiplayer app uses a flat, question-centered React interface served by FastAPI. Four panelist cards sit above the question, four defender cards below it, and a persistent bottom dock holds voting, answers, and team chat. A separate Streamlit app provides a single-browser fallback.

## Panelist conversation

The prompts give each panelist a distinct conversational habit: Technical follows
how a concrete operation works; Security calmly examines safeguards; Product
follows a user's everyday workflow; Methodology patiently examines research
choices; Ethics considers the participant's experience; Impact explores realistic
benefits; Critical tests assumptions fairly and accepts a sound justification.

Reactions are tied to an actual decision, reason or constraint in the defender's
answer. Panelists are instructed to vary their wording, use brief introductions,
explain confusing terms patiently and move on from details a probe reply has
already resolved. Their personality comes through their perspective and phrasing,
without invented personal stories, credentials, gestures or scripted questions.
Questions, reactions, optional advice and clarification replies remain AI-generated;
exact citations and existing language preferences still apply. The opening has no
fabricated reaction, and a missed turn is acknowledged without inventing an answer.

In the feature-branch multiplayer room, a generated reaction appears briefly on its own
after the previous turn, with the panelist marked **Speaking**. It stays for
4–12 seconds according to its length, then the next question and exact citation
appear and the full 15-second vote begins. The reaction is retained in Transcript
instead of remaining above the question. Empty reactions skip this moment;
reconnecting clients resume the server's current phase without replaying it.
The Streamlit fallback retains its existing inline dialogue display. Review the
mock transition at <http://127.0.0.1:8820/?preview=1&research=1&reaction=1>.

After a same-question clarification, the defender's request appears above the
panelist's latest explanation, which replaces the large question text. The
question number and exact citation remain unchanged. The original wording and
all clarification exchanges stay in Transcript; the next turn displays its new
question normally. Preview: <http://127.0.0.1:8820/?preview=1&research=1&clarify=1>.

The role-voice refinements are published on `feature/question-first-room`;
the reaction and clarification display updates are also published but have not
been deployed. Offline tests check
context and response contracts; a separate live conversation is needed to assess
how natural the generated dialogue actually sounds.

The published feature-branch language update adds everyday conversational Cebuano for Bisaya/Cebuano
requests, with natural English research terms such as “pag-check.” Ask a panelist
“Please use modern Bisaya” or “Bisaya lang” to set the language for the ongoing
conversation, including reactions, clarifications and coaching. Brief replies,
code-only replies and timeouts retain the preference; a later explicit request or
substantive answer in another language can change it. Shared words such as “ang”
and “sa” alone no longer identify an answer as Taglish. All dialogue remains
AI-generated. This language update has not been deployed; live native-speaker
review is still needed to verify the wording.

## Room status and replies (feature-branch checkpoint)

The question, header, seat strips, bottom dock and Controls use one read-only
room presentation model. Voting says **Choose a speaker**; the selected defender
sees **Your turn**, and teammates see who is answering. A same-question probe
uses **Reply to panelist**, a Reply timer and a **Replying** seat. It retains the
original answer, question number and citation. A new follow-up gets a new number.

During submission interpretation, **Reviewing submission · Timer paused/running**
explains the clock and the defender is **Selected**. Recovery guidance names the
existing permitted actions and respects remaining attempts; pending sends disable
repeat recovery actions. Drafts, reconnect, server timers and answer rules retain
their existing owners. Research mapping, first-question preparation, missed-turn
review and coaching each show their own status. Exhausted retries are described
in the dock, Controls and coaching report rather than suggesting an available retry.

Review the running [local reply preview](http://127.0.0.1:8832/?preview=1&research=1&probe=1).
Add `&submission=paused`, `&submission=running` or `&submission=retry` for review
states; use `?preview=1&complete=1&coaching=failed` for exhausted coaching recovery.
These are synthetic layout fixtures with no AI or payment calls. The preview
server uses an isolated temporary database and no provider credentials.
The [review record](docs/ROOM_PRESENTATION_REVIEW.md) links desktop, portrait and
landscape screenshots and records mocked two-client verification. This checkpoint
is published on `feature/question-first-room`; user visual review remains pending
and deployment is held with `[skip render]`.

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

This README describes `feature/question-first-room`: the flat room, research documents, same-question clarifications, summary downloads, answer-aware conversations, and Google host accounts with voucher or sandbox-credit access. Research and mixed defenses require a source-grounded paper map and a host-confirmed **4–100-question maximum**. Code-only defenses remain four to eight questions. The compact mobile header and existing architecture are served at [defense-simulator.onrender.com](https://defense-simulator.onrender.com), with shared timed-turn, purchase and progression modules and checkout UI compatible with account-owned receipts. Hosted health and asset hashes match the tested release; Google and test-payment configuration is enabled. A fresh signed-in defense and provider simulator purchase remain separate unverified checks. Account/upload-progress changes and availability fixes are now included in the feature-branch source. The latest publication has not been redeployed or hosted-verified. `main` stays frozen during the review window that began on October 1, 2026, and its earlier service remains unchanged.

The previous account/PostgreSQL checkpoint passed **194 Python tests with AI, Google, and PayMongo mocked, 153 React tests, and a production build**, plus a **52-test gate against real local PostgreSQL** with external providers mocked. Two-browser mocked defenses completed all four combinations of code/research and voucher/test-credit access, including votes, clarification, answers, reconnect, transcript and coaching. Mocked signed webhooks awarded 100 credits once, an opening failure released its reservation, and the subsequent code/research runs charged ten credits each. The cleanup gate passes **204 Python tests, 62 real-local-PostgreSQL tests with external providers mocked, 157 React tests and a production build**. A synthetic browser checkout processed duplicate signed notifications into exactly one 100-credit award and displayed run reservation/charge/release records; it is not a live provider purchase. An actual account-linked hosted PayMongo simulator purchase, fresh hosted defense charge, and deliberate restart persistence check remain pending. Local account captures use synthetic fixtures, and user visual review is separate.

The isolated published research release passed **138 Python tests with AI mocked, 129 React tests, and a production build** using the committed lockfile. Its mocked two-browser twelve-question research and mixed defenses covered planning, budget confirmation, voting, timeout follow-up, clarification, retry, reconnect, exact PDF/code citations, export and coaching. Desktop, landscape, narrow landscape, portrait rotation and keyboard drawer controls were checked separately. These published-release checks are distinct from the newer local account/access tests.

Live evidence is separate: a local synthetic mixed/proposal defense completed twelve questions (eleven answers and one real timeout), English/Taglish adaptation, retries, clarifications, exact citations, reconnect, export and coaching. A fresh hosted synthetic mixed/proposal smoke check completed a deliberately selected four-question budget with two browser clients: planning, real voting, answers from both defenders, a same-question clarification, reconnect, transcript download and shared coaching. All 22 hosted map references and four question citations matched the uploads exactly; the session stopped at budget exhaustion with two of twelve topics addressed and the remaining gaps shown. Coaching used valid turn references and Q1-style question numbers. Hosted health and JavaScript/CSS bytes matched the tested release. These synthetic checks do not establish exhaustive coverage or consistently strong dialogue for arbitrary papers. User visual review and physical separate-device confirmation remain pending; the hosted four-question check does not replace the longer local checks.

See [PROJECT_LOG.md](PROJECT_LOG.md) for evidence and publication history. Agents and other session windows must also read [AGENTS.md](AGENTS.md) before editing.

## Architecture release checkpoint

The timed-turn, purchase persistence and shared progression modules are published
on the feature service, with checkout UI compatible with account-owned receipts. The isolated committed release passed **212 Python tests with external
providers mocked, 156 React tests, and the production build**. Account UI and upload-progress changes are now included in feature-branch source; the hosted verification below describes the earlier deployed release. Hosted health and assets match the tested release. Evidence and limitations are
tracked in [PROJECT_LOG.md](PROJECT_LOG.md); main remains frozen.

## Local security admission checkpoint

The feature branch now limits each signed-in host to two retained rooms and three
creation attempts per minute, before upload parsing. In Controls, **Manage my
rooms** lists only your rooms and lets you resume host access or close an unused
room. Idle lobbies and settled completed rooms expire after 30 minutes; the room
shows a warning in the final two minutes. Active or unsettled defenses are protected.

Mobile login reuses an unexpired attempt without extending its five-minute lifetime.
New allocations are limited per client network; an already-open attempt must finish
in its existing browser window. Interpretation is limited to two successful
clarifications and six attempts per question. The chosen defender can explicitly
submit an answer without interpretation when clarification/retry capacity is used,
or write a new answer during recovery. AI-related clock pauses total at most four
minutes per question; the saved answer clock then resumes even while recovery is
pending. Host and guest requests share owner/run AI budgets. SDK automatic retries
are disabled. Existing access, pricing, citations and billing rules stay in force.

This checkpoint is **local, not deployed**. See [limits and verification](docs/SECURITY_ADMISSION_REVIEW.md)
for configuration, mocked browser screenshots and remaining hosted/native checks.
Do not configure trusted forwarding headers until the actual proxy path is verified.

Additional local availability safeguards bound anonymous join bodies to 4 KB,
with a 10-second deadline, 32 in-flight requests globally and eight per network.
WebSockets are limited to two tabs per defender, eight per room, 256 globally and
32 per network, including clients awaiting authentication. Connection attempts
and messages have shared network/player/room limits; reconnecting does not reset
them. Slow snapshot recipients are disconnected after one second. The launch
commands explicitly select the declared websockets backend, capping frames at
20 KB and inbound queues at four messages; do not substitute the auto backend,
whose queue behavior depends on the installed Uvicorn version.

DOCX extraction runs in a credential-free Linux child process with a 128 MiB
memory ceiling, 10 CPU seconds and a 20-second wall deadline. It rejects packages
with more than 512 entries, parts above 8 MB, total expansion above 32 MB, or an
expansion ratio above 1000. Request cancellation terminates and reaps the child
before releasing its parser slot. Non-Linux local servers reject DOCX safely;
use Linux/WSL or upload TXT/Markdown instead. PDF processing is unchanged.

## Run locally

### One-peso real-payment trial (local only)

`payments_live_trial.py` is a separate, owner-only service for one **PHP 1.00
real QR Ph payment**, adding 100 demo credits to an isolated trial account.
It does not change the multiplayer app's PHP 100 sandbox pack or its balances.
This is an integration check, not final pricing or a public live-money launch.

Configure `PAYMONGO_LIVE_TRIAL_ENABLED=1`, `PAYMONGO_LIVE_SECRET_KEY`,
`PAYMONGO_LIVE_WEBHOOK_SECRET`, and `PAYMONGO_LIVE_TRIAL_OWNER_SUB` on that
process only. The owner is the server-verified Google subject, not an email
or browser-supplied ID. Use the existing Google settings, a matching HTTPS
`AUTH_PUBLIC_BASE_URL` / `PAYMONGO_PUBLIC_BASE_URL`, and a separate
`PAYMONGO_TEST_DB_PATH` ending in `qr-one-peso-live.sqlite3`. Do not set
`DATABASE_URL` for the trial. Keep credentials in an ignored private file;
the operator's setup wizard writes `.env.paymongo-live-trial` with mode 600.

With those settings loaded into a separate process, run:

```bash
.venv/bin/uvicorn payments_live_trial:app --host 127.0.0.1 --port 8791 --workers 1 --no-access-log
```

Register a **live-mode** webhook at `/api/payments/live-trial/webhook` for
`payment.paid`, `payment.failed`, and `qrph.expired`. The service verifies the
live `li` signature, event mode, intent, amount, currency and receipt before a
once-only award. It does not expose sandbox simulation or defense endpoints.
One trial receipt per owner is enforced transactionally; failed or ambiguous
creation blocks another payment attempt until reviewed. Refreshing restores
the existing receipt, without generating another QR.

The owner signs in, confirms the real-payment label, generates the QR, and
checks **PHP 1.00** in GCash before approving. A paid browser redirect never
awards credits. Only the verified provider notification does. Trial credits
remain separate from usable app/sandbox credits. The dedicated temporary
HTTPS service is running locally. One operator-paid live PHP 1.00 transaction
was confirmed by PayMongo and awarded exactly 100 demo credits through the
signed webhook. The temporary live webhook is now disabled; its paid receipt
remains available. See [the trial review](docs/ONE_PESO_LIVE_TRIAL.md) for evidence.

### Multiplayer app

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

### Owner dashboard

Open **Account → Owner dashboard**, or `/?manager=1`, to manage top-up
invitations, search/page through registered Google accounts, and add or remove
live credits with a required reason. The dashboard shows available, reserved,
held and test balances separately, plus recent audited changes. It lists accounts
that have signed in; room-only guests do not create account records. You may
invite a Google email before its first sign-in.

Configure `PAYMENT_OPERATOR_GOOGLE_SUB` to your server-verified Google subject
on the server. This is the existing payment-operator identity, not an email,
display name or browser-selected account. Missing configuration disables owner
access. Every management endpoint checks ownership; changes also require the
existing authenticated session and same-origin CSRF token. No owner identifier
or user list is sent to teammates' room snapshots.

Invitations are stored in the account database and take effect without a
redeploy. `LIVE_TOPUP_INVITED_EMAILS` remains an optional seed list; a dashboard
disable overrides a seeded invitation. Removing an invitation blocks new top-ups
without deleting purchased credits or changing public signed-in voucher access.

Credit edits are signed adjustments to available **live** credits. They cannot
remove reserved/held credits or produce a negative available balance. Grants
are separate from payment receipts and test balances, fund defenses before
purchased credits, and participate in existing once-only reservations, charges
and service-failure returns. Purchased receipts retain their original terms;
manual edits do not mark a payment paid, trigger money refunds, or award test
credits. The audit records the owner account, target account, reason and change.

For a synthetic local preview, use
<http://127.0.0.1:8768/__fixture/login> while the private preview process is
running. Its users, identity and balances are fixtures, not real accounts or
payments. Hosted availability requires deploying this feature-branch release and configuring the owner identity.

### Preview without AI calls

Build the frontend before starting FastAPI directly:

```bash
cd game
npm ci
npm run build
cd ..
.venv/bin/uvicorn game_server:app --host 127.0.0.1 --port 8000 --workers 1 --ws websockets --ws-max-size 20000 --ws-max-queue 4
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
| `&probe=1` | Synthetic same-question panelist probe (combine with `&research=1`) |
| `&complete=1` | Transcript and coaching |
| `&long=1` | Long question and citation overflow |

For scope-preview variants, add `&budget=4` to view a smaller proposed budget, or `&planstatus=planning` / `&planstatus=failed` to inspect mapping status and failure copy. These fixtures make no AI requests and cannot confirm a real plan.

For frontend development, run `npm run dev` in `game/` alongside FastAPI on port 8000. Vite proxies `/api`, `/ws`, and `/health` to the backend. Check signed-in room and QR top-up flows on the built app served by FastAPI, where browser origin, OAuth callback, and CSRF settings match.

## Create and play a defense

1. Open **Account**, sign in with Google, and redeem the configured free-access voucher or obtain sandbox test credits. In **Controls**, keep or edit your prefilled display name, choose a defense type, and upload its materials. Uploading and creating the room are free. For a code demo, use [sample_project/README.md](sample_project/README.md) and [sample_project/queue.py](sample_project/queue.py).
2. Share the room code. Teammates open the same service URL and join with their own display names. The four defender seats include the host.
3. For research or mixed rooms, the host first chooses **Prepare defense**, reviews the map, edits the question maximum and selects **Confirm question budget**. Preparation requires free access or at least 10 available test credits, but deducts nothing. Start uses the voucher or reserves **10 test credits per run**, charged when the first validated question appears. The question count does not change this sandbox fixture charge. Each question appears with its panelist, optional reaction, and validated citation.
4. Every question, including follow-ups, begins with a **15-second speaker vote**. Online defenders may vote for themselves or another online defender and change their vote. The highest count wins; ties and no votes are resolved randomly among online defenders.
5. The chosen defender gets **120 seconds** to answer. The room shows **Your turn** to that defender and **[name] is answering** to teammates; voting says **Choose a speaker**. The question, seats, progress and timer share a read-only presentation model. Only that defender may submit. Disconnection assigns another online defender without resetting the clock. Expiry records an unanswered turn and advances the defense.
6. A panelist may ask for **one missing detail** after reading an answer. This optional probe keeps the original answer, question, source citation and chosen defender. It has its own **30-second reply window**, with no additional vote, question-budget slot or run charge. A clarification explains the probe without replacing it. If the probe expires, the original answer is retained and only the missed probe is marked. Direct-answer recovery bypasses this AI decision.
7. After completion (four to eight turns for code; coverage, budget, or host ending for research), open **Transcript** for the conversation and coaching. **Download summary** saves a text copy of questions, citations, clarifications, original answers, separate probe exchanges, timeouts, and coaching in your browser.

After selecting **Create defense room**, the loading bar shows **0–100% of the upload**, measured from browser upload events, plus elapsed time. At 100%, **Processing files and creating room** stays visible until the server validates the files and returns the room. Upload completion does not mean extraction or room creation has finished; elapsed time is not an estimate of time remaining. If the browser cannot report upload size, the bar shows activity without a percentage. The form is locked against repeat submissions, and a failed request keeps your name and selected files for retry.

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
.venv/bin/uvicorn game_server:app --host 127.0.0.1 --port 8790 --workers 1 --ws websockets --ws-max-size 20000 --ws-max-queue 4
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
   .venv/bin/uvicorn game_server:app --host 127.0.0.1 --port 8790 --workers 1 --ws websockets --ws-max-size 20000 --ws-max-queue 4
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
.venv/bin/uvicorn game_server:app --host 127.0.0.1 --port 8790 --workers 1 --ws websockets --ws-max-size 20000 --ws-max-queue 4
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

Synthetic review screens: [verified checkout](screenshots/payment-cleanup-checkout-mock-desktop.png), [account charge history](screenshots/payment-cleanup-account-mock-desktop.png), and [landscape charge history](screenshots/payment-cleanup-account-mock-landscape.png). They contain synthetic account/billing fixtures, not a live Google or PayMongo transaction.

The [account and payment flow map](docs/PAYMENT_FLOW.md) explains checkout request reuse, verified awards, run charges and recovery. New checkouts accept an account-bound `Idempotency-Key`; the web app preserves it before sending and reuses it after a lost response. In-flight/unverified attempts are not automatically recreated, and new checkout attempts are limited to five per account in ten minutes. New browser receipts store only an order ID and require the owning account, while legacy anonymous receipts keep their earlier access. Account history shows actual `awarded_credits` and the latest 20 run records. The server-only `.venv/bin/python -m payment_audit` checks aggregate financial-record consistency without contacting the provider or repairing data.

Private account endpoints expose only the current user's access/balance and latest 20 purchases/runs; mutations validate origin and session CSRF. WebSocket host controls recheck account ownership and origin. Uploaded files, room dialogue, and team chat are not stored in this database. Existing anonymous paid receipts stay separate and receive no retroactive credits. Local SQLite accounts/balances survive a Python restart. For hosted Render Free, use a Neon Free PostgreSQL project through `DATABASE_URL`; configuring a URL never migrates existing SQLite data. The PostgreSQL adapter serializes account transactions and never falls back to SQLite on connection failure. See the [deployment guide](docs/ACCOUNT_DEPLOYMENT.md) for setup and the separate real-local-PostgreSQL verification gate. Hosting and database paid tiers can be upgraded later while keeping the same store. Upload-based quotes, real credit pricing/spending, and real-money enforcement remain separate checkpoints.

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
layout checks remain applicable. The user accepted the mock payment screen.
A separate local Google/PayMongo sandbox walkthrough on 2026-10-08 verified
account-owned QR creation, provider authorization, automatic webhook settlement
and one 100-credit award for a clean receipt, plus fixture-to-provider
reconciliation without another award. This used an isolated local SQLite store
and temporary HTTPS callback; it does not verify the hosted release. See
[the provider sandbox evidence](docs/QR_TOPUP_PROVIDER_SANDBOX_REVIEW.md).
Actual provider redelivery, live failure/expiry, real PostgreSQL, native devices
and hosted QR verification remain separate.
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
Start: uvicorn game_server:app --host 0.0.0.0 --port $PORT --workers 1 --ws websockets --ws-max-size 20000 --ws-max-queue 4
Health: /health
```

The currently published research release uses `OPENAI_API_KEY` and `GAME_HOST_PASSCODE`, plus optional `OPENAI_MODEL`, in its own service environment. The hosted account/access update replaces that passcode with Google authentication and voucher/test-credit eligibility. New payment cleanup remains local pending publication. The user selected Neon PostgreSQL with Render Free. Keep the current services unchanged during local cleanup; verify payment callbacks and persistent balances separately. A feature service's configuration is independent of frozen `main`.

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

## Live tester payments

The normal live flow is `/?payments=live`: PHP 1/5/10 purchases provide 10/50/100 credits;
starting a defense reserves 10 credits and its first validated question finalizes the
charge. Later questions, clarifications, retries and coaching are included. A valid
voucher takes precedence and spends zero credits. Demo credits remain separate and
visible in Earlier test history. Hosted configuration and verification are recorded
in `PROJECT_LOG.md`; environment switches control live availability.

The refreshed `/?payments=live` page provides a balance summary,
selectable credit packages, and recent purchases with amount, credits, date, status,
and a **View receipt** action. An active, unexpired payment offers **Download QR code**
to save the exact server-issued PNG. Saving or hiding the QR does not confirm or
cancel payment; server verification still controls credit awards. QR downloads are
hidden once paid, failed, or expired. Installed Android/iOS WebView PNG downloads
remain a separate device check.

Read [the local release and operator checklist](docs/LIVE_TESTER_PAYMENTS.md) before
configuring live credentials. The purchase invitation list controls only new top-ups;
non-invited signed-in accounts can still redeem a voucher, join, or use existing credits.
Financial records use the existing durable account database. Rooms still disappear on
restart; unfinished eligible charges receive one recorded credit return, not a money refund.

On Render, a live-mode replacement can briefly report
`{"status":"ok","room_service":"starting"}` at `/health` while its predecessor
shuts down. The website, sign-in and payment callbacks stay available, but room
requests return a retry message until the exclusive lease is acquired. This avoids
Render's rolling-deploy startup conflict without allowing two room services to
charge defenses. Normal readiness returns `{"status":"ok"}`. Keep one worker
and one instance; do not delete lease or financial records to unblock a deploy.

Review: [independent implementation review](docs/LIVE_TESTER_REVIEW.md), with local
mocked payment/account/defense screenshots under `screenshots/live-tester-*`. User visual
acceptance and actual provider/hosted/native verification remain separate rollout gates.

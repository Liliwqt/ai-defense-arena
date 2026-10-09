# Security Policy

## System and Scope

This policy describes AI Defense Arena on `feature/question-first-room`: a FastAPI server serving a React multiplayer room, with a Streamlit fallback and Android/iOS WebView wrappers. HTTP, WebSocket, OAuth callback and payment webhook routes are potentially internet-facing. Assess the actual selected revision and deployment; documentation and branch publication do not establish hosted configuration.

Scope includes application source, upload and extraction code, AI integrations, account/session stores, purchases and credit ledgers, operator tools, browser/native clients, dependency integration and deployment configuration. Important paths include `game_server.py`, `accounts.py`, `mobile_auth.py`, `project_files.py`, `research_files.py`, `question_generator.py`, `resource_limits.py`, payment/store modules, `game/src/`, and `mobile/`. Separate trial services and legacy compatibility paths require their own exposure assessment.

## Threat Model and Trust Boundaries

Protect account identities and sessions, room participation tokens, uploaded private material, room-only conversations, operator privileges, financial records, purchased credits and shared server/AI capacity.

Potential attackers include anonymous visitors, authenticated hosts, room guests and malicious uploaders. Names, filenames, documents, answers, chat, HTTP/WebSocket messages, browser redirects and AI output are untrusted. Authentication does not make a host's document safe.

Google identity becomes trusted only after server-side verification. Account ownership uses the stable Google subject; browser-supplied account identifiers, email addresses, balances or role flags cannot confer authority. PayMongo notifications and retrieval responses require validation before changing financial state. Room tokens grant only their assigned participation rights.

The app server, configured operator and database are privileged boundaries, not proof that credential handling or configuration is safe. Native navigation, export bridges and browser-to-WebView sign-in cross additional trust boundaries. Provider services are dependencies; relevant integration failures remain within scope.

## Security Invariants

These are required properties, not claims that all current code or hosted controls satisfy them.

- Require server-verified ownership for room creation, host reconnection and every host action. Owner management, invitations, credit adjustments and refund operations require the configured operator identity.
- Protect account mutations with authenticated sessions and same-origin CSRF checks. Validate OAuth state, identity and nonce; restrict return destinations. Mobile completion requires an unexpired, once-only handoff and its matching proof.
- Isolate rooms and accounts. Shared snapshots must not expose account email, balances, voucher details, session credentials, player tokens or another participant's pending private submission. Team chat stays within its room and outside AI context, coaching and exports.
- Enforce selected-speaker permissions, authoritative deadlines, valid turn identifiers and once-only answer acceptance on the server. Reconnects and competing requests cannot override those checks.
- Bound admission before allocating shared capacity or dispatching costly work. Limits must account for accounts, client networks, concurrent sockets, message rates, upload parsing and AI attempts; four seats do not by themselves bound connections.
- Bound document expansion, parsing memory and execution as well as compressed upload size and final text size. Cancelled requests must not publish rooms or leave unbounded background work. Uploaded paths cannot escape their intended boundary, and uploaded code must not execute.
- Treat uploaded text and earlier dialogue as data. AI output cannot authorize operations, select billing terms, access other rooms or override server validation. Validate citations and resolve displayed excerpts from server-owned accepted text.
- Render untrusted text safely. Restrict native bridges and navigation to the intended origin and validate export destinations, names and sizes. Untrusted documents or external pages must not acquire application privileges.
- Price purchases on the server. Verify payment signature/authenticity, mode, receipt association, amount, currency, provider identifiers and successful status before a credit award. A QR download, browser redirect or client claim never proves payment.
- Award payments, reserve funds, charge runs, release reservations and return eligible credits transactionally and at most once. Replays, concurrent starts, stale AI results and service replacement cannot double-award, overspend or charge an unauthorized run.
- Separate live purchased credits from sandbox/demo balances. Test simulation cannot operate under live credentials or create spendable live credits. Preserve settled payment records against later failure/expiry events and request-key collisions.
- Enforce voucher revocation for future runs and top-up invitations independently. Credit edits and refunds require authorization, audit records and consistent holds; neither can falsify payment settlement.
- Fail closed when required identity, payment or configured database validation fails. Do not silently replace a configured unavailable persistent store with an empty local database.
- Keep secret keys, signing secrets and credentials out of public assets, responses, logs, exports and version control. Forwarding headers may affect limits only through an explicitly trusted and verified proxy path.

## Reportable Findings and Severity Context

Report a demonstrated violation with a realistic entry point, attacker capabilities, prerequisites, affected boundary and concrete impact. Relevant impacts include account/host/operator impersonation, cross-room disclosure, unauthorized credit changes, payment fraud, credential exposure, shared service exhaustion and uncontrolled AI spending.

Calibrate severity to evidence. Distinguish an anonymous visitor, ordinary signed-in host, invited payer and privileged operator. Explain whether impact reaches other users or only the attacker's own room, whether required configuration is present, and what mitigation is actually enforced.

A filename resembling a secret, a dependency advisory, a failed test or poor AI wording alone does not establish an exploitable path. Conversely, ignored files, local permissions, login requirements, low pricing and small-instance deployment do not automatically disprove one. Do not assert production exposure, valid credentials or effective proxy throttling without evidence.

## Exclusions and Accepted Risk

No owner-confirmed finding-class exclusions or new accepted risks are established by this policy draft. Do not use generated files, dependency folders, fixtures or prototype status as blanket suppression grounds. Their relevance depends on whether they ship, are exposed or affect a reachable application path.

Room contents and timers currently live in one process and disappear on restart. Whether ordinary room loss is an accepted availability limitation remains unresolved. It does not excuse unauthorized charges, missing eligible credit returns, duplicate compensation or cross-instance billing conflicts.

## Known Limitations and Verification Boundaries

Deployment requires one room worker and one instance; durable accounts and financial records are distinct from in-memory rooms. Exclusive service ownership and recovery require assessment across restart and replacement. Simply adding workers is not a safe scaling assumption.

Compressed-file limits, post-extraction text limits, parser concurrency and HTTP timeouts are different controls. Inspect where each applies; none alone establishes a bound on DOCX/PDF expansion or a running parser's memory use.

Offline tests with AI, Google and PayMongo mocked demonstrate only the exercised application behavior. Actual provider callbacks, hosted proxy configuration, production persistence and installed native sign-in/downloads need separate evidence. Prior incomplete or canceled scans are not a complete security assessment.

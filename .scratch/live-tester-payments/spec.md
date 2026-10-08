# Live tester payments and reliable paid defenses

Status: ready-for-agent
Created: 2026-10-08
Branch: feature/question-first-room
Publication: local Markdown tracker only; implementation and hosted release remain later checkpoints.

## Problem Statement

A host wants to pay a small, clear amount for credits and practice a defense
without developer instructions, manual payment authorization or uncertainty
about whether their balance is correct. The main app currently offers sandbox
credits, while the successful real PHP 1 trial is an isolated owner-only service
that awards demo credits. Neither is the integrated live storefront requested.

The existing room is erased by a service restart. Its financial records do not
distinguish a successfully delivered defense from an unfinished charged run.
A lost payment notification can also leave a paid receipt pending indefinitely.
Hosts need purchased access to survive those failures, and the operator needs
records that distinguish purchases, defense charges, credit returns and money
refunds without converting old demo balances into spendable live credits.

## Solution

Integrate live PayMongo dynamic QR Ph top-ups into the existing Account/payment
experience. The temporary packages are PHP 1 for 10 credits, PHP 5 for 50 credits,
and PHP 10 for 100 credits. Each paid defense costs 10 credits, regardless of
question count, and includes questions, clarifications and coaching. Purchased
credits never expire or change their count when package prices later change.

Only accounts on a private verified-Google-email invitation list can create new
live top-ups. Every signed-in account may still redeem the configured voucher
for free defenses. Voucher access takes precedence over spending credits;
teammates continue joining as guests. Invitation removal stops new purchases,
not use of existing credits or settlement of already-issued paid receipts.

The server confirms payments automatically through verified webhooks, with
independent provider verification to repair missed notifications. Reserve the
run cost on Start, finalize it on the first validated question, and return it
once for a verified server interruption that loses an unfinished run. Included
retries remain free. During an unresolved server-recorded question or coaching
failure, the host may explicitly end the unavailable run and recover its charge.
Normal voluntary ending, timeouts and abandonment do not produce a return.

Keep one active defense per host account. Show clear amounts, balances, receipts
and actionable statuses, with an email support link. Money refunds are reviewed
by the operator: fully unused top-ups are the ordinary eligible category;
complaints involving spent credits receive separate review. This is a local
implementation specification, not authority to deploy, configure live payments,
make a purchase or refund money.

## User Stories

1. As a host, I want to sign in with my Google account, so that my purchases and defense access belong to a verified identity.
2. As a host, I want my editable display name separate from account identity, so that changing it cannot change financial ownership.
3. As an invited host, I want to open Top up credits from Account, so that I can buy access without finding a developer page.
4. As an invited host, I want PHP 1, PHP 5 and PHP 10 packages, so that I can choose a small purchase with a clear credit amount.
5. As a host, I want the temporary PHP 1 = 10 credits rate and ten-credit defense cost stated clearly, so that I understand what I am buying.
6. As a host, I want to review the exact amount and credit count before generating a QR, so that a deliberate package selection starts the correct payment attempt.
7. As a host, I want a dynamic QR for the selected amount, so that I can pay through GCash or another supported QR Ph wallet.
8. As a host, I want a readable QR and one short payment instruction, so that I can pay without setup guides cluttering the page.
9. As a host, I want to see the QR deadline, so that I know whether the code is still usable.
10. As a host, I want local hiding of a QR distinguished from cancelling a provider payment, so that I do not assume an issued QR became unpayable.
11. As a host, I want explicit regeneration after a verified failure or expiry, so that I can make another deliberate attempt.
12. As a host, I want uncertain QR creation to retain its attempt, so that a lost response does not silently create a second payable QR.
13. As a host, I want repeated submission of the same purchase request to reuse it, so that double clicking cannot create duplicate payment attempts.
14. As a host, I want automatic confirmation after payment, so that I never have to press an authorization or simulation button.
15. As a host, I want payment confirmation backed by provider evidence, so that redirects or browser claims cannot invent credits.
16. As a host, I want missed payment notifications repaired automatically, so that a genuinely paid receipt does not remain pending forever.
17. As a host, I want duplicate or delayed notifications to award my purchase once, so that webhook retries cannot inflate my balance.
18. As a host, I want pending, failed, expired and uncertain receipts described accurately, so that I know whether to wait, retry or contact support.
19. As a host, I want a paid receipt retained if balance refresh fails, so that a temporary UI error does not make my payment appear lost.
20. As a host, I want my receipt restored after reload or sign-in on another device, so that I do not need to create a new QR to inspect a purchase.
21. As a host, I want purchased credits to have no expiry, so that unused access remains available.
22. As a host, I want existing credits and receipt amounts unchanged after new pricing, so that a later catalog update cannot rewrite my purchase.
23. As a host, I want live credits and old sandbox/demo history kept separate, so that simulated awards cannot fund real paid runs.
24. As a non-invited host, I want a short top-up-unavailable message, so that I understand purchasing is temporarily restricted.
25. As a non-invited host, I want voucher redemption available, so that top-up invitations do not block free access.
26. As a host removed from the invitation list, I want my bought credits and already-issued paid receipts honored, so that removal does not confiscate access.
27. As a voucher holder, I want free access used before purchased credits, so that a free run leaves my balance intact.
28. As a voucher holder, I want already-authorized runs preserved when the voucher rotates, so that a configuration change does not disrupt the current defense.
29. As a guest defender, I want to join using a room code and display name, so that I do not need to purchase or sign in.
30. As a host, I want uploading and room creation to remain free, so that I can inspect accepted material before starting a paid run.
31. As a research host, I want preparation to check access without deducting credits, so that making a paper map does not spend the run price.
32. As a host, I want one flat ten-credit run cost, so that a longer research defense does not create unexpected per-question charges.
33. As a host, I want to see available credits separately from reservations, so that I understand what I can spend while an opening question is generated.
34. As a host, I want the opening failure to release its reservation, so that a defense with no validated question does not consume credits.
35. As a host, I want an opening retry to reserve access again without duplicating a charge, so that recovery is fair and predictable.
36. As a host, I want one active defense across my rooms and browsers, so that accidental parallel starts cannot overspend or start duplicate runs.
37. As a voucher holder, I want the same active-run limit, so that unlimited free access is not confused with unlimited concurrent AI requests.
38. As a host, I want later questions, clarifications and coaching included, so that using the conversation does not add charges.
39. As a host, I want a paid restart to require explicit ten-credit confirmation, so that replacing a run cannot silently spend again.
40. As a host, I want an unauthorized or insufficient-credit action to leave the room intact, so that rejected actions do not erase accepted answers.
41. As a host, I want expired sign-in to prompt reauthentication, so that teammates and existing clocks continue while I recover access.
42. As a defender, I want voting, answer timing, citations, chat and clarifications unchanged, so that payment work does not change the defense rules.
43. As a host, I want a lost unfinished charged run to return ten credits automatically, so that a server crash does not charge for unavailable service.
44. As a host, I want an opening reservation orphaned by a crash released, so that reserved access does not remain locked after the room disappears.
45. As a host, I want free retries after a later question failure, so that an included recovery does not require another purchase.
46. As a host, I want to end an unavailable run during an unresolved question error and recover ten credits, so that I am not trapped waiting indefinitely.
47. As a host, I want free coaching retries or explicit ending with a credit return during an unresolved coaching error, so that failed included coaching has the same recovery.
48. As a host, I want repeated recovery actions to return credits once, so that reconnects and retries cannot multiply compensation.
49. As a host, I want normal ending and completed runs distinguished from service failure, so that ordinary use is not misreported as refundable interruption.
50. As a host, I want brief disconnections to permit reconnection, so that mobile connectivity changes do not abandon my defense.
51. As a host, I want abandonment after every defender is absent for ten operating-service minutes, so that a forgotten run releases the active-run slot.
52. As a host, I want server downtime excluded from abandonment, so that a crash cannot be attributed to my inactivity.
53. As a host, I want receipts, balances and credit returns to survive server restarts, so that financial history remains available even when rooms do not.
54. As a host, I want a support email link carrying my receipt reference, so that I can report a payment issue without an in-app support form.
55. As a host, I want to request operator review of a fully unused top-up refund, so that an eligible purchase can be assessed safely.
56. As a host with a complaint involving used credits, I want separate review, so that my complaint is not mistaken for an automatic unused-purchase refund.
57. As a host, I want pending, completed and failed money refunds distinguished, so that requesting a refund is not presented as money already received.
58. As a host, I want defense credit returns distinguished from cash refunds, so that I know whether access or money was restored.
59. As an operator, I want refunded credits prevented from being spent or re-awarded, so that refund and defense races cannot give both the money and access.
60. As an operator, I want payment/refund references and reasoned adjustments recorded once, so that I can investigate failures without directly editing balances.
61. As an operator, I want live and sandbox modes to reject mismatched credentials and events, so that a fixture cannot award live credits.
62. As an operator, I want new purchases or paid starts pausable without blocking issued receipts, so that an outage does not strand customers who already paid.
63. As an operator, I want durable hosted storage verified before rollout, so that account and payment records are not left on ephemeral disk.
64. As an operator, I want safe payment errors and bounded recovery requests, so that neither customer data nor secrets are exposed during diagnosis.
65. As an operator, I want staged local review and separate actual-provider evidence, so that passing mocked tests is not described as a production payment launch.
66. As a mobile host, I want portrait, landscape and WebView payment/account controls to remain usable, so that buying access does not require a desktop layout.
67. As a host, I want my balances, email, voucher and invitation details private, so that teammates see room state without my financial information.
68. As an operator, I want existing accounts and legacy purchases preserved by migrations, so that adding live payments does not erase sandbox evidence or ownership.

## Implementation Decisions

### Boundaries and delivery

- Extend the existing account, transactional purchase, payment-provider and room
  progression boundaries. Keep provider networking outside database transactions
  and room locks; apply validated results through existing concurrency guards.
  The small real-payment trial is evidence and reusable validation only, not the
  production account service or a second balance for normal users.
- Deliver four reviewable checkpoints: live wallet/access/run lifecycle;
  automatic top-ups and payment recovery; customer UI and operator refund/support
  workflow; hosted readiness and an explicitly requested rollout. Every local
  checkpoint stays on the feature branch and preserves unrelated work.
- This invocation advances the completed fifteen-decision interview into a
  specification. It does not authorize implementation, publication or deployment.
  Legacy sandbox contracts remain test-mode compatible until explicit retirement.

### Identity, invitations and configuration

- Use validated Google subject as stable account identity and the identity
  provider's verified email for the private server invitation list. Never trust
  browser-supplied ownership, email, prices, balances or refund eligibility.
- The top-up invitation check applies only to new purchases. Owner receipt reads,
  settlement, existing credit use, guest joining and voucher redemption are not
  invitation-gated. A request replay may recover an already-authorized attempt;
  it may not create a new one after removal.
- Preserve existing account authentication, host ownership, origin validation,
  CSRF checks on account mutations, guest room tokens and safe OAuth destinations.
  Unconfigured identity rejects anonymous hosting; expired host sessions do not
  reset rooms or stop teammates' timers.
- Preserve voucher fingerprint grants, throttled redemption and configuration
  revocation for future runs. Voucher runs consume zero credits and count toward
  the active-run limit. No invitation dashboard, general admin role or owner-only
  unlimited-concurrency exemption is introduced.
- Introduce an explicit live/sandbox mode and independently configured purchase
  and paid-start availability. Live mode requires coherent live credentials,
  webhook validation and durable storage; reject absent/mismatched setup without
  silently falling back to sandbox, simulation or an ephemeral hosted wallet.
  Pausing starts still allows voucher-authorized runs subject to operational AI
  availability; the controls distinguish paid-start pause from AI-service outage.
- API keys, signing secrets, invitation lists and voucher values remain server-only.
  Public responses disclose eligibility/status, not the invitation list or provider
  credentials. Use no-store responses for private financial/account reads.

### Packages, history and wallet records

- Server packages use integer centavos and integer credits: 100/500/1000 centavos
  purchase 10/50/100 credits in PHP. Clients submit only package choice and a
  stable account-scoped attempt key. Store package version, amount, currency,
  credits, account and payment environment immutably on each receipt.
- Historical receipts are validated against their frozen terms, never the current
  package list. The frontend must restore older receipts after catalog changes;
  today's package catalog is used to create new purchases, not reinterpret old ones.
- Additive migrations preserve accounts, sessions, legacy anonymous and account
  receipts, sandbox awards and run charges. Existing sandbox and isolated trial
  balances remain demo history; neither is promoted to a live award.
- Add a distinct live ledger, reservation/allocation representation, run outcomes
  and adjustment records. A purchase awards once; a run returns once; a verified
  refund/reversal adjusts once. Enforce uniqueness and account/environment binding
  transactionally, not through process-local flags alone.
- Track credit lots by originating purchase. Allocate ordinary paid reservations
  deterministically from eligible lots in purchase order; final charge records
  their spend. Release restores the same unspent lots and credit returns restore
  the original run allocations. No renewal, expiry or cash value is attached to
  restored credits. A refund hold prevents allocation of the affected lot.
- For normal refund eligibility, a fully unused top-up has no finalized spend;
  a released opening reservation is not a spend. Past spent-credit cases, including
  returned run allocations, are visible for operator review instead of being
  silently relabeled as an untouched purchase. Do not imply this review policy
  overrides applicable customer rights.
- Private account overview returns coherent live available/reserved credits,
  free-access eligibility, top-up eligibility, catalog/run cost and receipt/run/
  adjustment history. Legacy test history remains explicitly labeled separately.
  Shared room snapshots contain no balances, account IDs, email, invitations,
  voucher values or refund details.

### Run reservation, completion and compensation

- Validate host authority, room phase, research plan/budget and action legality
  before any financial mutation. Atomically acquire the account's active-run claim
  and reserve ten credits, or authorize zero-cost voucher access. One claim spans
  opening generation, voting, answers, question/clarification work and included
  coaching. Duplicate starts reuse the authorized run; a competing room is rejected
  without erasing answers or moving credits.
- Finalize a paid charge only when a first question has passed all grounding and
  progression checks. Record its validated publication commitment durably with the
  charge before broadcasting; handle the database-commit/in-memory-commit crash gap
  as an unfinished interrupted run. Do not claim receipt by a browser can be made
  atomic with the database, or wait for browser acknowledgment to decide charging.
- Opening failure releases its reservation with no charge. Opening retry reacquires
  authorization/reservation and an active claim without duplicate charge; it cannot
  bypass a newer active run. Later retries, clarification and coaching are included.
- Restart is a new run with new explicit paid-cost confirmation. Validate replacement
  and reserve its access safely before replacing the old room state; rejection must
  preserve it. A replaced charged run is an ordinary voluntary ending, not automatic
  compensation. Replacement updates active claims and run outcomes transactionally.
- Persist financial run identity, funding mode, room/service ownership, generation
  epoch, reservation/charge timestamps, service outcomes, unresolved error category
  and minimal lifecycle evidence. Do not persist uploaded text, chat, answers or
  coaching as a financial audit record. Rooms and transcripts remain ephemeral.
- Distinguish financial state from service state. Service outcomes include opening,
  active dialogue, coaching pending, completed, ordinarily ended, abandoned and
  interrupted/ended unavailable. Successfully delivered coaching completes the
  service; exhausted questions with failed coaching do not count as successful
  completion for compensation. Existing room completion presentation must not
  falsely mark the financial service finished before its included report is ready.
- During an unresolved server-recorded question or coaching error, offer free retry
  and an explicit host action to end unavailable service and return the charged ten
  credits once. Extend this recovery to code as well as research runs without
  changing ordinary code question order or adding general early-ending gameplay.
- The server revalidates the unresolved error and run epoch when applying recovery.
  Ending cancels/invalidate clocks and pending AI results, records a terminal outcome,
  releases the active claim and returns paid allocations atomically. A repeated
  action or stale successful result cannot restore the run, charge again or return
  again. A voucher run ends safely with no fabricated ten-credit award.
- A new service incarnation recovers only runs belonging to a verifiably lost
  incarnation: release orphan reservations and return charges for unfinished lost
  runs once. Do not blanket-refund historical charged runs or a healthy overlapping
  process's runs. Persist terminal outcomes before relinquishing ownership; if
  ownership/liveness cannot be established safely, retain records for review.
  Historical rows with no outcome evidence remain legacy, not presumed interrupted.
- Observe all-defender absence for ten minutes while a healthy service owns the run.
  Any connected defender resets that absence interval. Only one browser tab closing
  is insufficient while another connection remains. On observed abandonment, cancel
  timers/generation, persist the noncompensable outcome and release the active claim.
  Service downtime or expired host sign-in is not evidence of user abandonment.
- Ordinary answer timeouts, voluntary ending, completed service and healthy-service
  abandonment do not receive automatic credit returns. Durable recovery is financial
  compensation, not transcript restoration or a money refund.

### Automatic top-ups and payment recovery

- Reuse dynamic QR creation with a durable attempt reserved before networking and
  exact provider intent bound as soon as it is known. Account, provider, environment
  and attempt identity must prevent QR/legacy collisions and cross-user reuse.
- A lost/uncertain creation response retains its attempt and any known provider
  reference. Replay does not automatically create a second payable intent. Resolve
  the known intent when possible; otherwise show uncertainty/history/support before
  an explicit new attempt. Backend financial ambiguity survives a page reload.
- Validate provider resource types, exact intent/payment identifiers, live flags,
  PHP amount/currency, receipt metadata where present, and acceptable payment states
  at each stage. Store only a validated QR image; never expose secret/client keys.
- The normal live surface contains no simulation action or test-provider simulator.
  Sandbox fixtures and historical receipt routes remain mode-isolated, unable to
  award live credits or use a live key to manufacture a fixture award.
- Webhooks verify signatures over the exact raw body and the configured environment,
  then validate the bound receipt/payment before shared once-only settlement. Handle
  duplicate, early, delayed and out-of-order delivery. Failure/expiry awards nothing;
  verified later payment can recover the matching receipt once. Paid settlement is
  not overwritten by registration retries, failure/expiry or duplicate notices.
- Independent authenticated server reads recover eligible bound receipts that were
  paid externally but missed delivery. Validate the same amount/currency/mode/
  ownership/payment identity as a webhook and use the same atomic award operation.
  Browser receipt reads remain display-only and cannot supply provider evidence.
  Schedule bounded startup/periodic recovery from durable pending or uncertain
  attempts; browser presence is not necessary for a legitimately paid award.
- Use per-receipt concurrency control, bounded batch sizes, network deadlines and
  persisted backoff. Repeated status polling cannot cause unbounded provider requests.
  An outage or unknown status is pending/uncertain, never assumed paid or expired.
- Record minimum safe event/recovery audit evidence with unique provider references.
  A webhook is acknowledged only after settlement or durable retryable event intake;
  never drop a paid event by acknowledging before any durable commitment. Existing
  synchronous durable settlement is acceptable if timely; do not add a queue solely
  to mirror provider advice. Early unbound receipt events remain retryable.

### Customer interfaces and refund/support operations

- Reuse the account drawer and QR-first page with live-specific labels and the
  current theme. Show package amounts, credit counts, pending/paid/failed/expired/
  uncertain state, countdown, retry, history and return-to-room navigation. Remove
  developer setup prose and simulation controls only from the live customer surface;
  retain operator setup in documentation and safe test tooling in sandbox mode.
- Provide a deliberate package/payment action, a disabled busy state and immediate
  readable feedback. QR generation is creation, not payment confirmation. The browser
  deadline is a display cue, not settlement authority or proof of nonpayment.
- Refresh private balances automatically after a paid receipt and on focus/native
  resume. Preserve the receipt if refresh fails. Ignore outstanding responses after
  sign-out or account change; never show another account's cached QR/history.
- Support email links carry only the receipt reference and general issue category,
  never identity tokens, full email/balance dumps, uploaded research or voucher codes.
  Require a configured public support address before inviting paying testers.
- Handle ordinary refunds by authenticated operator procedure, with no customer
  refund button or new administrative web dashboard. Verify receipt ownership and
  provider capability; use unique refund references, amount limits, reason/actor audit
  and a transactional hold on the eligible credit lot before initiating or recording
  a provider refund. No ad hoc balance edits or browser claims authorize adjustments.
- A refund request/processing state is not successful cash delivery. Once independently
  verified successful, finalize the matching debit once and show truthful history.
  Confirmed failure releases a hold once; uncertain provider submission retains it
  for investigation instead of repeatedly issuing refunds. Spent-credit complaints
  use operator review and a recorded decision, not an automatic entitlement or an
  unverified negative adjustment. Provider reversals must be validated and audited;
  unsupported/ambiguous schemas go to review rather than being invented in code.
- Preserve keyboard access, visible focus, readable QR/citations and unobscured controls
  at desktop, phone portrait/landscape and WebView sizes. Native return links navigate
  only; they never settle or award. No different mobile theme or wrapper rebuild is
  needed for website-only changes, though actual installed-wrapper behavior still
  needs separate verification.

## Testing Decisions

- Test observable behavior at the highest existing seams: authenticated FastAPI HTTP
  requests and room WebSockets, supported transactional store operations, and rendered
  account/payment/room flows. Mock external Google, PayMongo and AI calls for offline
  tests; use a controlled clock and fault injection to reproduce races/crash boundaries.
  Avoid SQL-layout snapshots, implementation-mirroring mocks or isolated getter tests.
- Prior art: current account tests validate real OIDC library behavior against fixtures,
  ownership, CSRF, voucher grants and private history; payment tests exercise signed raw
  webhook bodies, provider response validation and once-only awards; purchase tests
  reproduce concurrent settlement/replay and paid-registration regressions. Extend
  those contracts rather than introducing alternate fake production entry points.
- Current room/access tests cover authenticated host controls, two-client voting,
  clarification, timeout, retry, restart, reconnect and coaching. Extend them with
  private live funding and terminal outcomes while preserving code/research progression.
- Use the existing disposable-local-PostgreSQL gate for additive migration, concurrent
  awards/reservations, rollback, durable adjustments, active-run exclusivity, refund
  holds and restart recovery. Do not run destructive test setup against hosted accounts.
  SQLite mock passes or mocked adapter calls are not evidence of PostgreSQL correctness.
- Payment boundary cases: all three packages; unauthorized/non-invited/CSRF rejection
  before provider work; subject-based ownership; removed invitations and issued receipts;
  cross-user/mode/provider attempt collision; catalog changes and historical receipt
  restoration; duplicate paid events; wrong prices/currency/metadata/intent/payment;
  webhook/recovery concurrency; delayed paid after failure/expiry; unknown creation;
  early webhook; network error/backoff; simulation rejection in live mode.
- Wallet/run cases: separate old balances; voucher precedence/revocation; concurrent
  starts in different rooms with and without vouchers; insufficient credits; opening
  release/retry; charge at first validated question; repeated restart confirmations;
  later question and coaching retry; unresolved-error ending racing success; stale
  generations; exactly-once compensation; restart repeated across incarnations;
  crash before/after first-question commitment; healthy overlapping process not
  refunded; terminal completed/ended/abandoned runs excluded; legacy uncertainty
  retained for review; all-player absence and reconnect around the ten-minute deadline.
- Refund/support cases: fully unused versus previously spent lots; reservation release
  versus finalized spend; hold racing a run start; duplicate operator/provider updates;
  delayed payment notification after refund; confirmed success versus processing,
  failure and unknown outcomes; wrong-account/reference/mode/amount evidence; support
  link contains receipt only. Test these with provider fixtures, never actual refunds.
- React boundary tests extend existing QR-first, Account and Controls tests: eligibility,
  three live packages, separate test history, retained attempts/receipt, price revisions,
  safe sign-out races, balance refresh, failure-recovery actions and confirmations.
  Confirm that live copy has no developer setup/simulation text and sandbox remains
  truthfully labeled. Assert visible labels, interactions and network contracts.
- Mocked browser walkthroughs complete code and research defenses through voucher
  and live-credit fixtures, using two independent contexts. Cover payment restoration,
  host expiry, timers, clarification, error recovery, coaching and reconnect. Capture
  desktop/portrait/short-landscape account/payment/recovery screens and verify keyboard
  reachability, focus, scrolling and no clipped controls. Mark screenshots mocked.
- Run the full Python and React suites and production build before local checkpoint
  handoffs. Record provider-mocked, actual PostgreSQL, browser, live AI, hosted and
  installed physical-device results separately; no one replaces another.
- Separate explicitly authorized rollout checks cover real Google sign-in, one actual
  PHP 1 purchase through GCash, verified provider/receipt/once-only ten-credit award,
  a ten-credit paid run, two-client reconnect and deliberate hosted service restart
  compensation with retained balances. Check actual provider redelivery and refund
  capability independently; no money refund is authorized by writing this spec.
- On 2026-10-08 the user confirmed these test boundaries: existing authenticated
  HTTP/WebSocket flows with external providers mocked, real local PostgreSQL
  migration/concurrency/recovery checks, and desktop/portrait/landscape/WebView
  browser checks. Actual Google/GCash/provider-refund and hosted-restart evidence
  remain separate. This confirmation is not a claim of completed verification.

## Out of Scope

- Public unrestricted top-ups, a general paid public launch, subscriptions, custom
  payment amounts, currency exchange or automatic credit pricing by paper length.
- A host invitation dashboard, new admin web UI, stored customer support form or
  automatic customer-triggered money refunds.
- Promotion of sandbox/demo credits into live credits, credit expiry, balance
  confiscation on invitation removal or revaluation of existing purchases.
- New AI behavior, scoring, panelists, voice, chat features, upload limits, research
  question policy or ordinary code-defense early-ending gameplay changes.
- Durable uploaded documents, private chat, transcripts, stored defense history,
  room restoration after restart or multi-instance room synchronization.
- A new native design, rebuilding wrappers for website-only UI changes, or claiming
  installed Android/iOS compatibility solely from viewport tests.
- Automatic adjudication of disputes, tax/business-registration guidance, promises
  about provider fees/merchant payouts, or unverified provider refund event handling.
- Live credential setup, payment/refund execution, remote push, deployment or any
  modification of frozen main as part of this specification step.

## Further Notes

- The fifteen interview answers define the product scope. Invoking To Spec advances
  that completed discovery into a local specification; it is not visual approval or
  publication authorization. Related accepted-design ADRs distinguish interruption
  compensation, balance isolation and verified live recovery from historical sandbox
  behavior; implementation is pending.
- PayMongo's [webhook retry guidance](https://docs.paymongo.com/docs/developer-tools-retry-logic)
  documents finite retries and missed events that are not automatically replayed after
  exhaustion. This supports an independent verified-recovery path; it does not justify
  accepting a browser claim as payment evidence.
- [Payment Intent retrieval](https://docs.paymongo.com/reference/retrieve-a-paymentintent)
  supports authenticated provider reads. Their use for live settlement is the explicit
  ADR 0004 change; historical sandbox receipt reads keep their existing contract.
- [QR Ph refund guidance](https://docs.paymongo.com/docs/qrph-refunds) describes an
  operator/dashboard procedure and a customer-claimed transfer link. The link is valid
  for three days; a pending refund may fail if it expires or is declined. Exact account
  capability, fees, minimum amount and event compatibility need actual verification
  before release. These provider facts were rechecked on 2026-10-08; no refund was made.
- The previous operator-paid PHP 1 trial confirmed one live payment and a once-only
  isolated 100-demo-credit award. It does not prove this release's ten-credit package,
  durable financial recovery, refund capability or hosted integration. Preserve its
  historical receipts and describe its evidence accurately.
- Rooms remain in memory with exactly one worker/instance. Durable service ownership
  exists to prevent mistaken compensation during restarts/overlap, not to introduce
  horizontal room scaling. Hosted money uses existing PostgreSQL/Neon persistence;
  database connection failure must never create a silent local live-wallet fallback.
- Before a later hosted rollout, configure stable HTTPS/Google callbacks, live keys
  and webhook, a private invitation list and public support email; verify additive
  migrations against real PostgreSQL. Present the local integrated flow first. Any
  inability to establish once-only charging/recovery, balance isolation or provider
  refund handling is a rollout blocker rather than a reason to weaken these checks.

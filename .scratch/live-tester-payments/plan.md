# Live tester payments

Status: completed discovery; specification published locally in [spec.md](spec.md).
This discovery record is not implementation or deployment approval.
Date: 2026-10-08.
Branch: `feature/question-first-room`. Frozen `main` remains unchanged.

## Confirmed scope

Move real QR Ph payments into the existing React/FastAPI app. Hosts use
server-verified Google accounts; teammates continue joining as guests by room
code and display name. Only invited accounts may purchase top-ups; top-ups are temporarily disabled
for other accounts. Any signed-in account may redeem the configured voucher
for free access. Invitations do not gate voucher redemption or guest joining.
Purchased credits do not expire or lose their credit count after pricing changes.

Temporary rate: **PHP 1.00 = 10 credits**. A defense costs **10 credits**,
regardless of question count. Uploading/joining stay free; research preparation
requires sufficient access without deducting credits. Clarifications, later
questions and coaching are included. Restart starts another paid run.

The previous operator-only PHP 1 trial awarded 100 isolated demo credits. Its
receipt is preserved as evidence. It is not a reusable storefront, transferable
balance, or pricing definition for this release.

## Ask Matt workflow

All fifteen Grill with Docs decisions are recorded below. The user invoked
To Spec on 2026-10-08 to advance this settled design, then confirmed the existing
HTTP/WebSocket, PostgreSQL and browser test boundaries. The canonical
specification is [spec.md](spec.md), marked ready-for-agent in the local tracker.
No runtime or deployment approval is inferred from this workflow advancement.

To Spec is complete. Next use `/to-tickets`, then `/implement` for each
dependency-ordered ticket.
Implement uses test-first slices and Standards/Spec code review. This crosses
storage, provider integration, run charging, customer UI and hosted setup, so
it should be split into checkpoints rather than edited as a package constant.

Use `/wizard` only for Google/Render/PayMongo steps the operator must perform.
The currently successful isolated trial does not prove hosted payment durability
or paid defense recovery. No runtime or live provider changes are authorized
by this planning document.

## Checkpoint 1: live wallet, pricing and host access

- Add live/test environment discrimination to purchases, awards and run
  debits using additive migrations. Preserve all existing accounts, receipts,
  sandbox awards and historical package amounts. Do not reset or promote test
  balances into spendable live credits.
- Use the existing durable PostgreSQL/Neon store for hosted payments. SQLite
  remains a local test option, never hosted financial storage. Verify against
  actual PostgreSQL before rollout, including failure and restart behavior.
- Enforce top-up invitations on the server using verified account identity.
  Any signed-in account may redeem a voucher. The invitation gate applies to
  new purchases, not voucher access or guest joining. Keep balances, invitation
  details and voucher information out of shared room snapshots.
  The invitation list is private server configuration, using Google-verified
  email and stable account identity. No owner invitation dashboard is in scope.
- Derive all purchase values from a versioned server package catalog. Freeze
  amount, currency and awarded credits in each receipt. Never recalculate an
  old receipt from today's price or accept client-supplied amounts/credits.
- Confirmed packages: **PHP 1 → 10 credits**, **PHP 5 → 50 credits**, and
  **PHP 10 → 100 credits**. No larger purchase is needed for release testing.
- Preserve reserve-then-charge semantics: reserve 10 atomically on Start,
  charge when the first validated question is published, release on opening
  failure. Retry, reconnect and concurrent starts cannot charge twice or
  overspend. Paid restart shows its 10-credit cost before starting.
- Define recovery for a charged defense lost to a server restart. Rooms remain
  in memory. Confirmed: return the 10 credits once for a verifiably interrupted
  unfinished run, with durable run outcome and adjustment records. Completion,
  user-requested early ending and interruption must be distinguishable; do not
  refund successfully completed runs or invent stored transcripts. Resolve
  process-overlap/ownership before automatic recovery. The payment release
  must not silently leave a tester charged for a lost room.
- Allow only one active defense per host account, including voucher runs;
  enforce this atomically across rooms and repeated starts. Pending generation
  and unavailable coaching retain the run until it is completed or ended.
  Also bound repeated AI requests without adding per-question charges.
- Keep the existing voucher lifecycle: rotating/removing its configuration
  revokes future grants, not already authorized runs. Valid voucher access
  takes precedence over spending purchased credits.

Review: account balances and migration/recovery tests, with no real charge.

## Checkpoint 2: automatic live top-ups

- Introduce an explicit server payment mode and a normal top-up API used by
  the main app. Live configuration requires the live key and live signing
  secret; mismatched or missing configuration fails closed. No automatic
  fallback to sandbox or local fixture settlement.
- Reuse validated dynamic QR creation and owner/CSRF/idempotency boundaries.
  Multiple legitimate top-ups are allowed; concurrent/repeated creation of the
  same attempt must create only one receipt. An uncertain provider response
  retains its attempt for review rather than creating another chargeable QR.
- Verify the raw-body live `li` signature, event/resource mode, exact bound
  intent, PHP amount, currency and payment identity before settlement.
- Atomically mark paid and award the receipt's frozen credit count once. Guard
  duplicate/out-of-order notifications, early notifications, wrong owners,
  wrong prices, failures, expiry and delayed paid recovery.
- Live deployments do not expose local simulation actions. Existing sandbox
  routes/legacy receipts remain supported only under their proper environment;
  a test notification or demo award must never fund a live wallet.
- Persist minimal verified payment-event processing/audit metadata, protect
  retries, and monitor pending receipts/failed delivery. Never log keys, raw
  personal payment payloads or signatures. Browser status reads do not award.
- Recover externally paid/local-pending live receipts through independent
  authenticated server retrieval of the exact bound provider intent/payment.
  Validate live mode, account/receipt binding, amount, currency and payment
  identity with the same once-only award boundary used by signed webhooks.
  Webhooks remain primary; browser claims and redirects never settle a receipt.
  ADR 0004 explicitly revises the older webhook-only restriction for live
  recovery. Bound recovery retries and retain uncertain attempts for review.

Review: duplicate/race/mode checks and one mocked account-linked payment-to-run
flow, including 10-credit award and exactly one defense charge.

## Checkpoint 3: clean customer payment experience

Use the existing app and styling, with Account linking to **Top up credits**.
Suggested customer flow:

1. Select **10 credits · PHP 1.00** (temporary tester rate).
2. Tap **Pay PHP 1.00**.
3. Display the live QR, exact amount, credit count, expiry countdown and one
   short instruction: **Scan with GCash or a QR Ph wallet**.
4. Show **Waiting for payment** while checking the server-owned receipt.
5. Show **Payment received · 10 credits added**, refresh the private balance
   automatically, and offer **Return to your room**.

Remove developer setup steps, long method explanations, sandbox fixtures,
simulation buttons and “test credits” labels from the live customer experience.
Non-invited accounts see a brief top-up-unavailable message and can still
redeem vouchers; invited accounts see the three packages. Keep the actual price
and credit count clear before payment; keep expiry,
failure and retry messages actionable. Offer an email support link with the
receipt reference; configure the public support address during setup. Operator configuration belongs
in README/deployment docs. A disabled service shows a short unavailable message.

Preserve receipt history, account-owned restoration on another device,
Google sign-out/expiry, request replay, QR reload and status refresh. Local
cancellation only hides a QR; it must not falsely promise provider cancellation.
Before regeneration, distinguish verified failed/expired attempts from
uncertain creation so a user cannot accidentally pay two attempts.

Verify portrait/landscape, keyboard access, readable QR/copy, busy/error states
and WebView return/reconnect. No native rebuild is needed for website-only UI
changes, but installed-device payment navigation still needs verification.

## Checkpoint 4: hosted tester rollout

- Present the local integrated preview first. Publish/deploy only after the
  requested release step; do not merge or deploy frozen `main`.
- Configure the feature service's durable store, stable HTTPS origin, Google
  callbacks, live secret and a separate live webhook. The temporary trial
  callback is disabled and must not be repurposed as hosted infrastructure.
- Apply the confirmed host-access policy and show the temporary tester rate. Have a server-side
  switch to pause new top-ups/paid starts while preserving receipts and the
  ability to settle already-issued QRs, even if an invitation is later removed.
- Use operator-reviewed money refunds through PayMongo. Normal refund
  requests cover fully unused top-ups; complaints about spent credits receive
  individual review, subject to applicable rights. Track purchase-credit usage
  and prevent refunded credits being spent or awarded again. Refunds/provider
  reversals require once-only durable adjustments and truthful pending/failed
  outcomes, distinct from automatic defense credit returns. Verify actual
  account refund capability and event schemas before rollout; do not assume
  that initiating a refund means money has reached the customer.
- Complete one operator-approved **PHP 1 → 10 credit** purchase through GCash
  on the hosted app. Confirm exact provider/receipt/award identity, start one
  fresh defense, check 10-credit reservation/charge and reconnect two clients.
- Verify durable balance/receipt retention and interrupted-run recovery across
  a deliberate service restart. Actual refunds, provider redelivery, fees,
  payout settlement and physical-device results must be reported separately.

## Verification gates

- Mocked Python tests: host access/auth/CSRF; mode isolation; price/version
  preservation; ledger idempotency; concurrent starts/top-ups; opening failure;
  delayed notifications; reload/reconnect; run recovery and support adjustments.
- Real PostgreSQL tests with external providers mocked: migrations, historical
  purchases, transactional once-only awards/reservations and restart recovery.
- React tests/build plus mocked two-client code/research defenses: payment
  states, balance refresh, cost confirmation, transcript/coaching and guest join.
- Desktop/portrait/landscape and WebView browser checks, with mock provider data.
- Separate actual Google/hosted PHP 1 payment and stored-credit/run evidence.

Do not claim production readiness from the previous single successful QR alone.
Stop rollout if host authorization, data separation, once-only settlement or charged-run
recovery fail. Keep old test data and unrelated local changes/deletions intact.

## Implementation and rollout facts still pending

The product decision frontier is closed and the user has advanced to To Spec. Concrete server boundaries, concurrency/recovery algorithms and
purchase-credit attribution belong in the specification and tests, not another
product interview. Setup must provide a public support email and the private
invitation list. Provider refund capability, event schemas, fees and hosted
persistence must be verified before rollout. No live refund is authorized here.

Removing a top-up invitation blocks new purchases only: purchased credits and
settlement of already-issued paid receipts remain valid. A valid voucher takes
precedence over spending credits. Completed defense dialogue with failed
included coaching is an unfinished purchased service for recovery purposes;
an unresolved server-recorded coaching error permits included retry or explicit
ending with the ten-credit return. Ordinary ending after successful service
is not refundable under the run compensation rule.

## Grill with Docs discovery

### Settled decisions after all five rounds

- Temporary PHP 1 = 10 live credits; 10 credits per paid defense run.
- Packages: PHP 1 / 5 / 10 for 10 / 50 / 100 credits.
- Top-up invitations use a private server Google-email list matched to verified
  stable accounts; an invitation dashboard is deferred.
- Top-ups are available to invited accounts only; all signed-in accounts may
  redeem vouchers for free access. This replaces the earlier assumption that
  invitations gate hosting itself.
- Purchased credits have no expiry and preserve their credit count after
  temporary pricing changes; only new purchases use a new price.
- Automatically return ten credits once for verified server loss of an
  unfinished charged run. Also allow included retries or explicit ending with
  credit return while a later question-generation or final coaching error is
  unresolved. Successfully completed runs, ordinary End defense and temporary disconnection do not qualify.
  Recorded in ADR 0002.
- Sandbox/demo balances stay separate from the live wallet; preserve their
  history without promotional conversion (ADR 0003).
- All-defender disconnection for ten minutes is abandonment, without automatic
  credit return; shorter disconnections allow reconnect (ADR 0002).
- Webhooks remain the primary award path; automatic, independently verified
  server recovery repairs externally paid/local-pending live receipts once.
  Browser claims never award (ADR 0004).
- Money refunds are operator-reviewed. Normal requests cover fully unused
  top-ups; complaints involving spent credits are reviewed separately.
- Provide email support with the receipt reference; the address is configured
  later, not assumed from the host's personal account.
- One active defense per Google host, including voucher users, with bounded
  repeated AI requests. Account invitations gate new top-ups only.
- Simplify the existing main app's payment UI, preserving truthful price/status
  information and moving developer setup material into documentation.

### Round one answers

- Q1: user selected PHP 1, PHP 5 and PHP 10 packages.
- Q2: user said “keep vouchers for all testers, not invited.”
- Q3: user selected automatic credit return.

### Round two answers

- Q4: user clarified that invitations gate the top-up method only. Top-ups for
  non-invited users are temporarily disabled; voucher free access is for all.
- Q5: user confirmed no expiry and retaining purchased credits after price changes.
- Q6: user selected included retries or explicit End with credit return during
  an unresolved server-recorded later question-generation error. This ends the
  failed run and restores its ten charged credits once; ordinary ending, answer
  timeout and completed defenses do not qualify.

### Round three answers

- Q7: user selected a private server list of Google emails, matched to verified
  stable accounts. Owner invitation UI is deferred; email is not trusted from
  a browser field or used instead of the Google subject as account identity.

- Q8: user selected separate sandbox/demo balances, preserving test history;
  no automatic promotional transfer into the live wallet. Recorded in ADR 0003.
- Q9: user selected abandonment after all defenders disconnect for ten minutes,
  without an automatic credit return. Brief disconnections allow reconnect.
  Abandonment must be observed by a healthy service, never inferred from its
  downtime after a crash.

### Round four answers

- Q10: operator-reviewed money-refund requests, rather than self-service money
  refunds. Provider/account capability remains a rollout verification gate.
- Q11: automatic verified server recovery for externally paid/local-pending
  receipts. This explicitly revises the old webhook-only live award restriction
  (ADR 0004); browser status alone remains untrusted.
- Q12: email support link with receipt reference rather than an in-app form.

### Round five answers

- Q13: normal money-refund requests cover fully unused top-ups; complaints about
  already-used credits are reviewed separately. Track purchase-credit use;
  provider capability and applicable consumer rights still apply.
- Q14: included coaching retries or explicit ending with a ten-credit return
  during an unresolved server-recorded coaching error, as for question failure.
- Q15: one active defense per Google host, plus repeated-AI-request limits.
  Teammates still join normally; voucher runs are included in the active limit.

### Design tree closure

- Access → private verified-email top-up invitations; public signed-in voucher
  redemption; invitation removal leaves existing purchased credits/receipts valid.
- Pricing/history → three packages; flat ten-credit run; permanent credit counts;
  separate sandbox/demo history and live wallet.
- Run recovery → once-only server-interruption return; explicit failure ending
  for unresolved question/coaching errors; ten-minute healthy-service-observed
  abandonment without automatic return; one active run per host.
- Refund/support → operator review; fully unused top-ups ordinarily eligible;
  spent-credit complaints separate; public email plus receipt reference.
- Settlement → signed webhooks primary; independent verified provider recovery;
  once-only shared award; browser claims never settle.
- Rollout → local checkpoints and review; provider/storage verification; later
  publication request. The user advanced the settled design into To Spec.

### Facts checked on 2026-10-08

Read-only exploration by `live_payment_facts`; no external calls or tests:

- Vouchers currently grant unlimited future free runs while their fingerprint
  remains valid (`account_store.py:138`, `account_store.py:204`). This can
  bypass the proposed tester payment flow unless explicitly changed.
- Ten credits are reserved before opening generation, charged before the
  validated question is committed to room memory, and released on opening
  failure (`game_server.py:335`, `game_server.py:352`). Later retries retain
  the charge.
- Startup releases reserved runs only. Rooms are lost and charged runs remain
  charged (`game_server.py:195`, `account_store.py:239`). No durable completion
  or interruption field distinguishes a completed run from a lost one.
- There is no credit-adjustment/refund representation or payment-event inbox
  in the inspected application. Receipt reads never fetch provider status;
  the audit cannot detect an externally paid/local-pending receipt
  (`account_store.py:59`, `payments.py:219`, `payment_audit.py:13`).
- Existing once-only settlement checks and PostgreSQL transaction serialization
  are reusable (`purchase_store.py:168`, `postgres_store.py:84`).

The glossary now distinguishes testers from guest defenders, live credits
from sandbox/demo units, and credit returns from real-money payment refunds. Policy choices, migrations
and executable behavior are not implemented by these definitions. Keep each
answer in this discovery record as it arrives; record an ADR only for a settled
decision with a meaningful trade-off and reversal cost. ADR 0002 records the
confirmed server-interruption compensation policy; its implementation is pending.

`CONTEXT.md` currently defines sandbox credit awards/reservations, and
`docs/adr/0001-qr-ph-top-up.md` is test-key-only. The implementation must record
the explicit live-mode/pricing decision and update these terms while preserving
the old sandbox records. ADR 0004 explicitly revises live settlement only;
sandbox webhook rules remain unchanged.

## Sources

- [PayMongo QR Ph](https://docs.paymongo.com/docs/payment-acceptance-qr-ph):
  PHP 1 minimum, participating wallets including GCash, dynamic amount and
  paid/failed/expiry events.
- [PayMongo webhook setup and verification](https://docs.paymongo.com/docs/developer-tools-webhook-setup-management):
  separate live/test keys, live `li` signature and raw-body HMAC verification.

Local baseline inspected: HEAD `03e00d6`, local trial code and reports,
`payments.py`, `purchase_store.py`, `account_store.py`, React Account/payment
components, README, PROJECT_LOG, domain glossary and QR ADR. No implementation
or new paid transaction occurred while preparing this plan.

## Additional source facts for recovery/refunds

Read-only exploration by `live_payment_facts`, 2026-10-08; no private settings,
provider API requests or live refund tests:

- Google callback requires verified email and subject; accounts are keyed by
  Google subject and update email/name on later sign-in (`accounts.py:173`,
  `account_store.py:107`). The main app has no general operator invitation or
  refund role; room ownership is not administrative permission.
- [QR Ph refunds](https://docs.paymongo.com/docs/qrph-refunds) describes full/partial
  refunds through a separate refund API and a customer-claimed transfer link
  valid for three days, subject to available merchant wallet balance. Exact
  account capability, minimum/refund fees and PHP 1 refund behavior are not
  verified. Official refund event names differ between reference pages; do not
  implement an assumed event schema.
- [Webhook retry logic](https://docs.paymongo.com/docs/developer-tools-retry-logic)
  documents retry exhaustion. Re-enabling an endpoint does not replay missed
  events. [Delivery resend](https://docs.paymongo.com/docs/retry-a-webhook-delivery)
  and [intent retrieval](https://docs.paymongo.com/reference/retrieve-a-paymentintent)
  provide recovery facilities; neither is integrated in the current app.
- Paid-QR receipt reads and the aggregate audit currently cannot repair an
  externally paid/local-pending receipt. The existing ledger cannot represent
  cash-refund holds/adjustments or independent run compensation.

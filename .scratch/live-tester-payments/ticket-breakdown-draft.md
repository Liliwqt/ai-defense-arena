# Live tester payments — proposed ticket breakdown

Status: approved by explicit Implement invocation, 2026-10-08; twelve individual local tickets published.
Created: 2026-10-08
Source: [approved-scope specification](spec.md), with 68 user stories and confirmed test seams.
Branch: feature/question-first-room. Frozen main and current hosted services stay unchanged.

## Slicing rules and shared constraints

- This draft is the To Tickets quiz artifact, not a combined implementation ticket.
  After approval, publish one numbered ready-for-agent file per slice in the local
  tracker. Do not change or close the parent specification.
- Ticket 01 is an expand-first compatibility prefactor. It preserves working
  sandbox contracts while making mode and frozen purchase terms explicit;
  no blanket table rename, old-contract deletion or forced contract phase is needed.
- Tickets 02–11 expose independently observable account, purchase, defense or
  operator behavior across persistence, interfaces, presentation and tests.
  Ticket 12 is the final integration/review gate, not a layer-only cleanup ticket.
- Keep live purchasing/paid starts unavailable to paying testers until integration,
  local review and separately authorized rollout. Implementing a slice does not
  authorize a provider mutation, payment, refund, push or deployment.
- Preserve existing Google identity, CSRF/origin and guest-token boundaries,
  private balances, voucher lifecycle, citations, voting, timers, clarification,
  research budgets, Streamlit fallback and unrelated local changes/deletions.
- Use supported transactional operations and authenticated HTTP/WebSocket tests,
  real disposable-local-PostgreSQL checks, and rendered browser behavior.
  Mock providers offline. Record actual provider/hosted/device evidence separately.
- Each ticket includes relevant documentation/log changes and the normal regression
  gate for its touched behavior. Full final suites/build and whole-flow checks are
  also required by ticket 12. Do not defer race invariants until final integration.

## Proposed slices

### 01 — Expand financial contracts without changing sandbox behavior

Blocked by: None — can start immediately.

Delivers: existing hosts can still inspect and use their sandbox purchases while
purchase mode, frozen receipt terms and new live configuration can be represented
safely through storage, API responses and receipt presentation.

Acceptance outline:
- Add explicit environment and immutable purchase-term representation beside
  existing contracts; legacy receipts keep original amount/credits and test status.
- Read old receipts independently of today's package catalog, including in the UI.
- Preserve sandbox creation, simulation, legacy receipt reads and verified settlement.
- Unknown/mismatched live configuration cannot enable a live payment or silently
  select local hosted storage; no live purchase/award is exposed by this slice.
- Prove additive migration/history retention and compatible HTTP/React behavior;
  include actual local PostgreSQL migration evidence with providers mocked.

### 02 — Show a separate live wallet and top-up eligibility

Blocked by: 01 — Expand financial contracts.

Delivers: a signed-in host sees live available/reserved credits and separate demo
history; invited accounts see the three live packages while all signed-in accounts
retain voucher redemption and guests retain joining.

Acceptance outline:
- Add live wallet/credit-lot representation without transferring existing test/demo
  awards; normal migrated accounts initially have no purchased live credits.
- Derive identity from Google subject and invitation eligibility from verified email
  matched against the private server list, never client-submitted values.
- Display PHP 1/5/10 → 10/50/100 credits and ten-credit run cost; hide purchase actions
  for non-invited accounts with a brief explanation and visible voucher access.
- Voucher precedence/lifecycle, private account data and free uploads/joining remain
  intact; new-purchase and paid-start switches report truthful availability.
- Test identities, invitation removal, privacy, missing setup and migration balances
  through account/room boundaries, React and disposable local PostgreSQL.

### 03 — Create and restore a live QR purchase

Blocked by: 02 — Live wallet and eligibility.

Delivers: an invited host deliberately chooses a package, receives its verified
amount-specific live QR, and restores the same owned attempt after reload.

Acceptance outline:
- Account/CSRF/origin/eligibility checks precede provider work; freeze terms on a
  durable receipt and bind the known provider intent as soon as possible.
- Replays reuse an account/provider/environment-scoped attempt; ambiguous responses
  preserve it instead of automatically creating another payable QR.
- Show exact amount/credits, generating/pending/uncertain state, expiry cue and a
  readable QR with short payment copy; no simulation or developer setup prose.
- Owner history and restoration work across clients/account changes, including an
  issued receipt whose owner later loses their top-up invitation.
- Creation awards no credits. Browser countdown/hiding/redirect cannot settle or
  promise cancellation. Test provider-response validation, replay/races, sign-out,
  privacy and desktop/phone QR readability with providers mocked.

### 04 — Confirm live payments and award credits once

Blocked by: 03 — Live QR purchase.

Delivers: after a matching signed paid event, the host sees Payment received and
exactly the frozen credit award, without manually authorizing the app.

Acceptance outline:
- Validate raw live signature, event/resource environment, bound intent/payment,
  account receipt, amount, currency and available metadata before settlement.
- Atomically record paid receipt and once-only live credit award; preserve payment
  identity uniqueness and paid terminality under registration or event retries.
- Early, delayed, duplicate and out-of-order delivery are safe; verified paid after
  failed/expired receipt can recover once, while failure/expiry itself awards nothing.
- Paid status refreshes the private balance; a refresh error preserves the confirmed
  receipt. Sandbox notifications/fixtures cannot fund the live wallet.
- Prove races, rollback and price/version preservation at HTTP/store boundaries and
  real local PostgreSQL; test the visible paid/history/balance flow with mock events.

### 05 — Run one paid or voucher defense per host

Blocked by: 04 — Verified live awards.

Delivers: a host starts a code or research defense with live credits or a voucher,
sees reservation/charge history, and cannot accidentally run competing paid sessions.

Acceptance outline:
- Validate room/host/research budget before mutation; atomically acquire one active
  host claim and reserve ten credits, or authorize a zero-credit voucher run.
- Allocate paid reservations to purchased lots deterministically; release the same
  allocations on opening failure and reacquire safely on opening retry.
- Commit a once-only charge with validated first-question publication commitment;
  later questions, clarification and coaching add no cost.
- Persist service ownership/generation and minimal outcomes; completion includes
  successful coaching, without storing papers, answers, private chat or transcripts.
- Restart confirms a new cost and replaces outcomes/claims safely; denial preserves
  the current room. Current code/research flow, guest participation and clocks remain.
- Show live cost/reservation/charge/restart/active-run messages in Account/Controls;
  prove concurrent starts, duplicates, opening failure, voucher rotation, logout and
  two-client progression with mocked AI and real local PostgreSQL transactions.

### 06 — Repair paid receipts that missed notifications

Blocked by: 04 — Verified live awards.

Delivers: a genuinely paid receipt becomes paid and credits appear automatically
when its webhook was missed, even if the host closed the browser.

Acceptance outline:
- Bounded startup/periodic server recovery retrieves the exact stored provider intent
  and validates the same binding/mode/amount/currency/payment evidence as settlement.
- Share the existing transactional once-only award with webhooks; their race cannot
  award twice. Browser status reads and redirects remain display-only.
- Persist retry/backoff and retain uncertainty on outage or unknown payment state;
  polling cannot create unlimited provider work or a new purchase.
- Recovery still honors issued receipts after invitation removal/purchase pause;
  current receipt/history/balance UI reveals its verified result.
- Test unknown/partial creation, missed/delayed notification, worker restart,
  wrong-evidence rejection and concurrent webhook/recovery against real local
  PostgreSQL with provider fixtures.

### 07 — End unavailable AI service with a once-only credit return

Blocked by: 05 — Paid/voucher defense lifecycle.

Delivers: a host can retry a failed question/coaching report free or explicitly end
an unresolved unavailable run, restoring its ten credits once.

Acceptance outline:
- Only server-recorded unresolved question/coaching failure enables the recovery
  action; ordinary ending, timeouts and successful service do not qualify.
- Persist the error and run epoch; atomically end service, release the active claim
  and restore original paid allocations once. An uncharged opening releases only
  its reservation; voucher runs never manufacture a credit award.
- Revalidate under concurrency with retry success; invalidate timers/pending AI
  results so stale completion cannot revive or recharge the ended run.
- Provide host-only recovery controls for code and research, private adjustment
  history and clear distinction between credits returned and a cash refund.
- Test repeated actions/reconnect, coaching failure, accepted-answer preservation,
  unauthorized recovery and race outcomes at WebSocket/React/PostgreSQL boundaries.

### 08 — Abandon a defense after ten minutes with nobody connected

Blocked by: 05 — Paid/voucher defense lifecycle.

Delivers: healthy-service-observed all-defender absence ends an abandoned run,
releases its active slot and permits a later run without refunding the old charge.

Acceptance outline:
- All defenders and their multiple connections are considered; any connected defender
  resets absence, and brief disconnects permit normal reconnect.
- Ten minutes must elapse while the owning service operates; expired host sign-in,
  one closed tab or server downtime does not prove abandonment.
- Persist the terminal noncompensable outcome, cancel generation/timers and release
  the active claim; stale results cannot reopen the abandoned run.
- Reconnection/account history explains abandonment; no invented transcript restore
  or ten-credit return. Voucher outcomes remain zero-cost.
- Fake-clock tests cover the boundary, reconnect/disconnect races, idle AI/report
  work, multi-tab presence and PostgreSQL outcome/claim persistence.

### 09 — Restore access after a verified server interruption

Blocked by: 07 — Unavailable-service credit return; 08 — Abandonment outcomes.

Delivers: after a service restart loses an unfinished room, the host's orphaned
reservation is released or its ten-credit charge returned once, visibly in Account.

Acceptance outline:
- Reuse run-return semantics and durable lifecycle evidence to recover only a
  verifiably lost service incarnation, never a healthy overlapping process.
- Exclude completed, ordinary-ended and observed-abandoned outcomes; legacy rows
  without evidence stay reviewable rather than presumed interrupted.
- Crash windows before/after charge/publication and during coaching are handled;
  repeated startup cannot produce duplicate compensation or credits for vouchers.
- Treat downtime as server interruption, not disconnected-user abandonment. Retain
  financial records while the UI acknowledges that in-memory room data is gone.
- Verify durable receipts/balances/history and active-slot cleanup through a real
  local PostgreSQL process/restart check, with external providers mocked.

### 10 — Review unused top-up refunds and protect their credits

Blocked by: 05 — Purchased-credit allocation and run lifecycle.

Delivers: a customer can contact support with a receipt, and the operator can review
unused-purchase eligibility and place an auditable hold without racing a defense.

Acceptance outline:
- Provide the configured email support link using receipt/category only, plus a
  private receipt's refundable/review/held state; no public admin/support form.
- Supported authenticated operator procedure verifies ownership and purchase use;
  normal unused requests differ from complaints about previously spent credits.
- A transactional hold protects the purchase lot from spending. An active reservation
  prevents that same lot entering refund processing until resolved; duplicate requests
  cannot multiply holds, and a held lot cannot fund a run.
- Record actor/reason/reference safely; historical spending and credit returns remain
  traceable. No manual SQL edits or customer claim grants/adjusts a balance.
- No cash refund is initiated by this ticket. Test email privacy, review states,
  lot/hold/reservation races and account UI against real local PostgreSQL.

### 11 — Reconcile operator-reviewed money refund outcomes

Blocked by: 10 — Refund review and credit holds.

Delivers: independently verified successful refund removes the matching held access
once; confirmed failure releases it, and uncertain processing stays visibly pending.

Acceptance outline:
- Extend the operator procedure with verified provider refund binding, amount limits,
  environment, actor/reason/reference and once-only outcomes; no customer refund button.
- Distinguish processing/claim pending from money received; uncertain submission or
  unverified reversal retains review/hold instead of retrying a cash refund blindly.
- Success finalizes the correct purchase debit once; failure releases the hold once;
  later paid webhook/recovery cannot re-award refunded credits.
- Show truthful private receipt/refund/credit history. Already-used-credit complaints
  remain operator-reviewed, not automatically approved or silently adjusted.
- Verify provider account capability/event contracts before enabling actual refund
  processing; unsupported evidence blocks it. Offline fixtures validate duplicate,
  wrong-identity/mode/amount, hold/charge and delayed-event races through PostgreSQL.
- Writing or implementing this ticket does not authorize an actual money refund.

### 12 — Review the integrated flow and prepare hosted readiness

Blocked by: 06 — Missed-payment recovery; 09 — Server-interruption recovery;
11 — Verified refund outcomes. These inherit all other implementation prerequisites.

Delivers: a locally reviewed release candidate and clear operator checklist for a
later separately requested hosted tester release; paying users are not enabled yet.

Acceptance outline:
- Run full Python/React suites/build and real disposable-local-PostgreSQL migration,
  concurrency and financial-recovery gates with external providers mocked.
- Complete mocked two-client code/research through voucher and live-credit paths,
  including purchase restoration, failure returns, timeout/clarification, coaching,
  reconnect, invitation removal and one-active-host behavior.
- Review desktop/portrait/landscape/WebView browser layouts, busy/errors, keyboard,
  support, history and clean live copy; installed devices remain separate evidence.
- Document setup/preflight for durable hosted storage, stable HTTPS/Google callbacks,
  live mode/webhook, invitations, public support email and independent pause controls.
- Present local screenshots/screen. Preserve explicit unresolved provider refund,
  fees/redelivery, actual Google/GCash and physical-device checks as rollout gates.
- Include a later operator-authorized PHP 1 purchase/ten-credit award/run, hosted
  restart recovery and deployment checklist; execute none until separately requested.
- Frozen main and current hosted service remain unchanged during this local gate.

## Dependency graph and frontier

- 01 → 02 → 03 → 04 → 05.
- 04 also unlocks 06.
- 05 unlocks 07, 08 and 10.
- 07 + 08 unlock 09; 10 unlocks 11.
- 06 + 09 + 11 unlock 12.

Only 01 is initially unblocked. An unlocked frontier means eligibility to start,
not a requirement to run simultaneous agents on overlapping files. Keep each
slice verified and reviewed before dependents rely on it. Any publication or
real-provider task needs its own later explicit authorization.

## Approval quiz

- Is this granularity right, or should a specific ticket be merged/split?
- Do these blocking edges reflect genuine prerequisites?
- Approve this draft to publish twelve individual local tracker tickets, not to
  implement or deploy them. Until then this draft remains unpublished as tickets.

# Security admission ticket breakdown

Status: ready-for-human
Created: 2026-10-08
Source: [Fair room access, mobile sign-in and bounded AI work](spec.md)

This is a proposed breakdown, not a published set of implementation tickets. The specification's numeric policies remain proposed defaults. Approval of granularity/dependencies must not be recorded as separate interview approval of those values. Each eventual ticket carries its own acceptance criteria and the source specification's preservation boundaries.

No wide prefactoring is necessary. Make only narrow prerequisite seams inside the first slice that needs them; keep existing HTTP/WebSocket, timed-turn and account test seams. The attempt accounting introduced by 04 is reused by 06, rather than creating a standalone infrastructure-only ticket.

## 01 — Fair room creation and owner-managed closing

**Blocked by:** None — can start immediately.

**What it delivers:** A host can retain two rooms, inspect their own rooms and close an unused or settled room to make space. Excess or repeated creation is rejected before expensive parsing, with clear recovery controls.

Acceptance scope:

- Enforce the proposed two-room account ceiling, three admitted creation attempts per minute and existing 20-room global ceiling, including concurrent in-flight creations.
- Reserve capacity atomically before reading/parsing uploads; preserve authentication, CSRF and validation. Release reservations on error, cancellation or the proposed 120-second processing timeout; late results cannot publish a room. Bound concurrent parsing to two workers.
- Expose owner-only room summaries and close controls. Nonowners cannot enumerate or close another account's rooms; guests retain their current join behavior. Do not expose account IDs, balances, voucher metadata or uploads in summaries.
- A host can close a lobby or settled terminal room, receiving a clear final room notice on all clients. Active/unsettled runs must use their established ending/recovery path first.
- Closing invalidates pending identities/tasks before releasing registry capacity. Neither rejected creation nor closing initiates a charge or credit return.
- Demo the two-room ceiling, successful close-and-create recovery and blocked third/concurrent upload through existing authenticated HTTP/WebSocket and React tests, with external providers mocked.

## 02 — Safe room expiry and reconnect recovery

**Blocked by:** 01 — Fair room creation and owner-managed closing.

**What it delivers:** Unused and finished rooms release shared capacity automatically, while active runs remain protected and teams receive readable expiry warnings instead of endless reconnect attempts.

Acceptance scope:

- Add the proposed 30-minute meaningful-inactivity lobby expiry and 30-minute settled-terminal retention. Keepalive, polling, chat, denied actions and terminal reconnect do not extend the applicable retention.
- Expose server-owned expiry timing and two-minute warnings; preserve transcript download during retention. Expired-room handling stops reconnect loops without leaking prior membership.
- Use both periodic and admission-time cleanup, reusing the safe close/removal behavior from 01 and a consistent lock order.
- Never evict unsettled billing or pending timers, interpretation, preparation, generation or coaching. Authorized successful restart cancels terminal expiry; unauthorized/failed restart does not.
- Preserve ten-minute observed absence and financial compensation semantics. Check whether unresolved error states can settle under existing abandonment rules; resolve any required lifecycle gap explicitly before claiming those rooms are reclaimable. Never substitute forced deletion or a synthetic refund for settlement.
- Delete only in-memory room data; preserve durable receipts and run ledger. Stale asynchronous results cannot recreate rooms or duplicate financial writes.
- Fake-clock tests cover exact deadlines, meaningful activity, warning, terminal read retention, expiry/start/restart races, offline absence and settlement protection. UI tests cover expiry messaging and room-list recovery.

## 03 — Fair and retry-safe mobile sign-in

**Blocked by:** None — can start immediately.

**What it delivers:** Legitimate mobile sign-in retries reuse an attempt, while a single network cannot fill the shared queue without bounds. Users get a retry delay and existing verified attempts can still finish.

Acceptance scope:

- Deduplicate a live challenge plus allowlisted destination without refreshing its five-minute expiry, resetting its opened state or replacing identity/code information.
- Apply the proposed 12 new flows per network/minute, 16 outstanding flows per network and 60 total start requests per network/minute, retaining the existing 128-flow process ceiling. Limiter state remains bounded and expiry/consumption releases capacity.
- Derive network identity only from the connection peer or a documented configured trusted proxy chain; spoofed forwarding headers and arbitrary installation IDs cannot bypass admission. Document IPv6 grouping and shared-network limits.
- Return safe HTTP 429 messages and bounded Retry-After. New-allocation throttling does not block existing OAuth return or proof-verified completion.
- Preserve verifier binding, random flow/code, one-time locked consume and session-store failure retry. An already-open reused flow must resume safely rather than reopen OAuth.
- Preserve Android/iOS compatibility, or include the minimal native change with mocked contract tests if a server-only safe resume is impossible. State clearly when installed-device evidence is unavailable.
- HTTP fake-clock/concurrency tests demonstrate deduplication, multiple legitimate users on one network, independent-network admission, forged-header rejection, expiry, store failure and one-time session issuance. No real Google call or production exhaustion test.

## 04 — Bounded clarification and explicit direct answers

**Blocked by:** None — can start immediately.

**What it delivers:** A chosen defender can clarify twice, retry within a bounded interpretation allowance and still submit an explicit answer after the allowance is used, without triggering another interpretation request.

Acceptance scope:

- Enforce two successful clarifications and the proposed six outbound interpretation attempts per turn before provider dispatch and before pausing the clock. Failed/invalid dispatched calls count; invalid authorization, local rejection and duplicate in-flight messages do not.
- Account for actual SDK outbound attempts; disable hidden automatic retries or prove each attempt is admitted. Introduce only the minimal reusable public attempt-accounting seam needed by 06.
- Add direct answer submission with current-turn, selected-defender, deadline, answer length and first-valid-answer validation. It records the server-owned name and bypasses interpretation, while later question generation remains normal.
- At exhausted clarification/interpretation allowance, reject ambiguous combined submissions with no interpretation call and offer the direct-answer action. Never record a request for simpler wording as an answer without explicit intent.
- Retain pending failed text and existing submitter-only use-as-answer recovery. The chosen defender can instead write a new direct answer. Host or another guest cannot convert someone else's pending text into an answer.
- Publish needed allowance/capability fields, preserve drafts on rejection, restore them and counters on reconnect, and clear drafts only after acknowledged turn resolution.
- Mocked WebSocket/React tests show exactly two clarifications, zero provider calls after rejection, bounded failure/retry, direct answer recovery, correct attribution, duplicate suppression and unchanged citation/coverage.

## 05 — Bounded answer-clock pauses

**Blocked by:** 04 — Bounded clarification and explicit direct answers.

**What it delivers:** Clarification and recovery cannot keep a question paused indefinitely; the chosen defender sees the authoritative remaining time and can answer directly before the effective deadline.

Acceptance scope:

- Track the proposed 240-second cumulative pause allowance per turn, including failed-interpretation waiting and retries. Rejected requests grant no pause; reconnect and new submissions do not reset the allowance.
- Once the allowance is consumed, resume saved answer time on the server even in interpretation/recovery state, publish the effective deadline and maintain expiry scheduling.
- Preserve 15-second voting and 120 seconds of active answer time. Show readable pause/exhaustion/recovery status on desktop and phone layouts.
- Apply only current provider results before the effective deadline. Timeout, direct acceptance, restart and ending invalidate late results; pending text remains distinct from an accepted answer.
- Fake-clock and two-client tests cover boundary races, successful clarification, failed wait, retry, direct answer, timeout during interpretation/recovery, reassignment, reconnect and stale results without duplicate turns or invented answers.

## 06 — Run-wide and owner-shared AI allowances

**Blocked by:** 04 — Bounded clarification and explicit direct answers.

**What it delivers:** Host and guest AI work share predictable run/owner limits, long research sessions have proportionate allowances and resource rejections preserve transcripts and existing financial recovery.

Acceptance scope:

- Apply the proposed 12 outbound attempts per owner per rolling minute across paid, voucher and sandbox modes, including guest submissions and all existing host AI actions. Derive owner identity server-side.
- Reuse actual-attempt accounting from 04. Enforce three question-generation attempts per turn, three preparation attempts per uploaded-project version, three coaching attempts per run and the 9 × B + 6 run envelope, where B is approved research budget or eight for code-only.
- Track preparation before a run and guard restarts/settings changes with the same owner burst allowance. Reset budgets only at the correct genuinely new run/project boundary; stale work cannot consume or reset a replacement run's allowance.
- Do not dispatch over-limit requests. Preserve pending text, accepted answers, coverage and current run; show retry timing or exhausted-allowance recovery without falsely claiming a provider failure.
- Preserve opening reservation release/retry, once-only charge and existing question/coaching provider-error credit return. Rate rejection alone never makes a run refundable. Explicit direct answers remain recordable without an interpretation allowance.
- Reconnect restores current allowances/capabilities without an AI call; shared fields reveal no account/financial details. Shared generation entry points and Streamlit remain compatible without adding multiplayer controls to the fallback.
- Mocked tests cover owner/guest concurrency, paid/voucher parity, opening and later failures, retries, restart/stale work, twelve-turn research behavior and the approved 100-question boundary, without extra charges.

## 07 — Combined defenses and remediation evidence

**Blocked by:** 02 — Safe room expiry and reconnect recovery; 03 — Fair and retry-safe mobile sign-in; 05 — Bounded answer-clock pauses; 06 — Run-wide and owner-shared AI allowances.

**What it delivers:** A locally reviewable release that demonstrates the protections together without breaking code/research defenses, mobile recovery or financial invariants.

Acceptance scope:

- Complete mocked two-client code and twelve-turn research defenses with voting, clarification, direct-answer recovery, timeout, AI failure/retry, reconnect, transcript and coaching. Include paid and voucher access, plus safe room close/expiry recovery.
- Verify desktop, portrait and landscape drafts, keyboard focus, expiry/countdown/status text, disabled retries and recovery actions. Record synthetic screenshots and preview evidence.
- Verify mobile HTTP/native-contract behavior, including reused already-open login flow and completion under admission pressure. Keep actual installed Android/iOS and hosted proxy checks explicitly pending unless separately evidenced.
- Run full Python tests with AI/Google/PayMongo mocked, full React tests and production build. Regression evidence must address each original source-validated finding and any remaining protected error-state lifecycle gap.
- Update README and the shared handoff log with final configurable limits, private data boundaries and results separated into offline, mocked browser, live and hosted evidence. Preserve unrelated files and deletions.
- Record residual many-account/distributed-network abuse risks. No production saturation, payment, credit adjustment, commit/push/deploy or frozen-main alteration is authorized by this ticket set.

## Dependency graph and frontier

```text
01 → 02 ───────────────────────────────┐
03 ────────────────────────────────────┤
04 → 05 ───────────────────────────────┤→ 07
  └→ 06 ───────────────────────────────┘
```

Initially unblocked: 01, 03 and 04. They address different protections; no dependency on another domain is invented. Separate execution contexts should still coordinate shared server, AI and UI edits. Approval of this graph does not authorize concurrent agents automatically.

## Review requested

Does the granularity fit a fresh implementation context per ticket? Are the dependency edges genuine? Should any slices merge or split? Wait for user approval before publishing one ready-for-agent file per ticket.

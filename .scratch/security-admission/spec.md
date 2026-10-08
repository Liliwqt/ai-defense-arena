# Fair room access, mobile sign-in and bounded AI work

Status: ready-for-human
Created: 2026-10-08

Basis: the completed Codex Security functional review at feature HEAD dd037d5 and the local security-admission design note. The user requested To Spec before answering the three policy questions. The limits below are explicit proposed defaults synthesized for implementation, not approved interview answers. The user confirmed the proposed test boundaries on 2026-10-08. This specification authorizes no publication, deployment, provider attack test, or financial mutation.

## Problem Statement

A legitimate host can be unable to create a room because another account filled all room slots with unused uploads. A student signing in through a mobile app can be blocked because anonymous requests occupied the shared sign-in queue. A chosen defender can repeatedly request clarification after the allowance is exhausted, causing additional paid AI calls and extending the question's paused time.

Students need fair access and recoverable errors. Hosts need a predictable flat-cost defense whose infrastructure spending cannot be amplified by guest submissions. Limits must preserve ordinary answers, campus networks, legitimate sign-in retries, long research defenses, reconnect and purchased-service recovery.

The findings are source-validated medium resource-exhaustion issues. They are not evidence of credit theft, account takeover, or successful attacks against the hosted service.

## Solution

Limit each host to two retained rooms, reclaim inactive and finished rooms safely, and reject excess creation before expensive upload work. Preserve the existing one-active-defense-per-host rule separately.

Keep mobile sign-in anonymous until Google verification, but reuse legitimate pending attempts and bound new allocations per network. Preserve proof binding, one-time exchange and expiry. Give busy users a clear retry delay without penalizing an existing attempt.

Enforce AI allowances before provider calls. Keep two successful clarifications per question and offer an explicit direct answer path after they are used up or interpretation capacity is exhausted. Bound retries and cumulative clock pauses, retain submitted text, and apply the same run-owned limits to hosts and guests. Keep the ten-credit defense charge unchanged.

## User Stories

1. As a host, I want another account unable to occupy every room slot, so that I can prepare a defense.
2. As a host, I want one room for my active defense and one for preparation, so that preparation need not interrupt my team.
3. As a host, I want my room allowance explained before uploading, so that I do not waste time sending a large project.
4. As a host, I want unsuccessful uploads to release their temporary slot, so that validation failures do not consume my allowance.
5. As a host, I want simultaneous creation requests counted together, so that duplicate clicks cannot bypass limits.
6. As a host, I want a list of my retained rooms without exposing their uploads to other accounts, so that I can resume or close an unused room.
7. As a host, I want an unused room closed without spending credits, so that cleanup does not create a charge.
8. As a host, I want active runs protected from automatic idle-room deletion, so that accepted answers and charged service are not lost.
9. As a defender, I want advance notice of room expiry, so that I can save the existing transcript when available.
10. As a reconnecting defender, I want an expired-room message instead of an endless reconnect loop, so that I know to request a fresh room.
11. As a team, I want a finished transcript available for a stated retention period, so that we have time to download it.
12. As a host, I want closing or expiry unable to refund or charge a run twice, so that cleanup preserves financial records.
13. As a mobile user, I want a retried sign-in allocation to reuse the same pending attempt, so that a lost response does not consume another slot.
14. As a mobile user, I want existing sign-in attempts able to complete while new admissions are throttled, so that a busy queue does not invalidate my login.
15. As a student on shared Wi-Fi, I want several people able to sign in concurrently, so that one network is not treated as one person.
16. As a mobile user, I want a clear retry delay when sign-in is busy, so that I avoid repeatedly tapping the button.
17. As a mobile user, I want a failed session-store operation recoverable with the same proof, so that I do not have to repeat Google sign-in unnecessarily.
18. As an account owner, I want copied return links unable to establish my session without the initiating verifier, so that fairness changes do not weaken login security.
19. As a chosen defender, I want two useful clarifications of the existing question, so that confusing wording does not become an extra defense turn.
20. As a chosen defender, I want an explicit Submit answer action when clarification is exhausted, so that my answer can still be accepted without another interpretation call.
21. As a chosen defender, I want clarification requests never silently treated as my answer, so that the transcript records what I intended to defend.
22. As a chosen defender, I want a failed submission retained, so that I can retry within the allowance or explicitly use it as my answer.
23. As a chosen defender, I want rejected requests to leave my draft intact, so that a limit does not erase work.
24. As a defender, I want the actual countdown and pause status visible, so that server-owned deadlines remain understandable.
25. As a teammate, I want the same clarification allowance and phase on every client, so that reconnect or another browser cannot reset limits.
26. As a host, I want guest-triggered AI calls included in the run's limits, so that free guest participation cannot bypass spending protection.
27. As a research host, I want limits to scale with my approved question budget, so that a hundred-question defense is not capped like an eight-question code defense.
28. As a host, I want rate-limited retries to preserve accepted answers and coverage, so that waiting does not duplicate or reset a turn.
29. As a host, I want legitimate provider failures recoverable without another run charge, so that bounded retries still honor included service.
30. As a paying host, I want the existing unavailable-run credit-return option retained, so that question or coaching failure has its established recovery path.
31. As a voucher host, I want identical resource limits without credit deductions, so that free access remains usable and fair.
32. As an operator, I want bounded limiter state and non-sensitive diagnostics, so that the protections cannot themselves consume unlimited memory or expose private text.
33. As an operator, I want trustworthy client-network identification, so that forged forwarding headers cannot evade sign-in limits.
34. As a phone or WebView user, I want readable limit messages and keyboard-accessible actions, so that recovery works on the same website and native shell.
35. As a user, I want existing payment receipts, balances and private account details unaffected, so that resource protection does not change purchasing or disclose my identity to teammates.

## Implementation Decisions

### Policy status and invariants

- All new numeric limits below are proposed defaults. Keep them centrally defined, bounded and operator-configurable with documented units; invalid configuration fails clearly rather than disabling protection.
- Implement locally on the feature branch. Keep frozen main and the live service unchanged. Preserve unrelated payment/account/upload changes and deletions.
- Preserve upload limits, accepted full-text context, role voices, citations, 15-second voting, 120-second answer time, four-to-eight code questions, and approved research budgets of 4–100. Private chat stays outside AI context.
- Resource rejection does not deduct credits, invalidate a voucher, change ownership, reset a run, or count as an AI/provider failure eligible for a credit return.
- The existing paid-run settlement and compensation policy remains authoritative. Cleanup never deletes an unsettled run or creates a financial write without its existing authorized lifecycle transition.

### Room admission and retention

- Default retained-room allowance: two per server-verified host account, counting lobby, active, failed and retained terminal rooms. The existing one-active-run rule is independent. Preserve the global 20-room ceiling as a final backstop; this does not guarantee protection against many independently authenticated abusive accounts.
- Default creation admission: three new attempts per account per rolling minute. Apply authentication, CSRF and creation admission before reading/parsing uploads. Malformed admitted uploads consume the short rate allowance but release their reserved capacity.
- Reserve capacity atomically under the registry lock before parsing. Count in-flight admissions toward both account and global ceilings. Release on failure/cancellation; publish only after validated uploads and ownership are available. A bounded processing timeout defaults to 120 seconds; late parser results cannot publish a released reservation. Bound concurrent parsing with a small worker limit, initially two, so cancelled work cannot create unlimited outstanding parser tasks.
- Provide authenticated host-only retained-room listing and closing. Lists reveal only that account's room code, phase and expiry; no guest/account financial details or uploaded text. Closing requires CSRF and owner verification. Closing is permitted for lobbies and terminal rooms; an active run must use its established End/recovery path first.
- Default lobby expiry: 30 minutes without a successful host preparation/settings action or a defender joining. Transport keepalives, polling, rejected requests and chat do not extend retention. Host preparation in flight suspends lobby eviction until its bounded result or failure. Room creation initializes this timestamp.
- Default terminal retention: 30 minutes from settled completion, explicit ending or abandonment. Reconnect, chat and repeated reads do not extend it. Successful authorized restart before expiry begins the next run; failed authorization leaves the terminal record unchanged.
- Expiry removes uploads, player tokens, chat, transcript and room state from process memory. Durable payment/run records remain intact. After expiry the ordinary unavailable-room response must stop client reconnect attempts; do not reveal former membership to an unauthenticated caller.
- Publish server-owned expiry timestamps and warnings two minutes before scheduled deletion. Room closing/expiry broadcasts a final notice before disconnecting clients. Retained-room listing and warnings expose no balance or voucher metadata.
- Run a bounded periodic cleanup plus admission-time cleanup. Recheck eligibility under the room/registry locks in one consistent lock order. Never delete a room with unsettled billing, active timers, pending interpretation, generation, research preparation or coaching work. Existing ten-minute observed absence first settles an active run under the established abandonment policy; it is not itself room deletion. If current abandonment coverage leaves an unsettled error state protected, resolve that lifecycle gap explicitly under the existing compensation policy before claiming that state is reclaimable.
- Remove owned timers/tasks only after invalidating their generation/interpretation identifiers. Late results cannot recreate a room, publish a turn, or settle billing again. Record expiration/close notices separately from defense answers.

### Mobile sign-in admission

- Reuse an unexpired handoff for the same challenge and allowlisted return destination instead of allocating again. Reuse does not extend its original five-minute expiry, reopen an already-open OAuth transaction, or replace verified identity/code data. It does not weaken the requirement for the initiating verifier during completion.
- Default allocation limits: 12 new flows per client network per rolling minute and 16 outstanding flows per client network. Preserve the process-wide 128 outstanding cap. Reused starts do not consume another allocation allowance; separately bound all start requests at 60 per network per minute to protect repeated lookups.
- These are network safeguards plus attempt deduplication, not trusted installation identity. A random client-supplied installation ID is not an admission bypass. Shared-NAT users may still encounter a clear temporary busy response; no promise of unlimited campus concurrency is made.
- Derive network identity from the trusted connection peer or explicitly configured trusted proxy chain. Ignore caller-controlled forwarding headers when no such trust is configured. Do not assume the current hosting proxy is trustworthy without a separate configuration check. Prefer the nearest verifiably untrusted client hop; normalize IPv4 and group IPv6 by a documented subnet policy so address rotation cannot trivially bypass limits.
- Keep limiter and deduplication maps bounded with fixed expiries. Store no verifier, provider token, email or unnecessary raw network address in diagnostics. Distinct destinations/challenges must not share the same handoff accidentally. Expired/consumed flows cease occupying pending capacity.
- Reject new allocations with HTTP 429 and a bounded Retry-After value. Existing open, verified-return and complete operations remain available during admission pressure and retain their proof, one-time and expiry checks. They still validate input and cannot allocate new handoffs.
- Preserve the existing native request/return contract where possible. An already-open reused attempt needs a safe resume response/behavior, not an OAuth reopening loop. If a backward-compatible server response cannot support that behavior, document the minimal Android/iOS compatibility change and test it before release; do not claim website-only delivery of a native-required change.

### Interpretation allowances and direct answers

- Keep at most two successful clarification exchanges per turn. Check this allowance before any new interpretation request. At zero, reject ambiguous legacy combined submissions without an AI call and show an explicit direct-answer action. Never automatically reinterpret a request such as “repeat it” as an answer.
- Add an additive authenticated room action for direct answer submission. It shares current-turn, chosen-defender, first-valid-submission, answer length and deadline validation. It records the server-owned speaker name and does not invoke the interpretation provider. Other AI generation/coaching requests still occur normally after an accepted answer.
- Default interpretation budget: six outbound provider attempts per turn, counting initial submissions and interpretation retries together. Admission occurs atomically before pausing the clock or dispatching provider work. A failed response, invalid response, cancellation after dispatch or transport error consumes an attempt; authorization rejection, stale turn, deduplicated in-flight action and local throttling do not.
- Count actual outbound SDK attempts. Disable hidden SDK retrying for budgeted operations and schedule retries through the shared allowance, or otherwise demonstrably account for each provider attempt before dispatch. A logical-call counter that leaves automatic paid retries uncounted is insufficient.
- Use a shared owner-account burst limit across host and guest AI actions, initially the existing 12 outbound attempts per rolling minute. Enforce it in paid, voucher and sandbox modes, and for interpretation/retry as well as existing host actions. Host identity derives from room ownership, never a guest-supplied account ID. Direct answers require no AI allowance to be recorded; subsequent generation can wait or remain retryable.
- Preserve one in-flight interpretation per turn. Reconnect, duplicate messages and another guest token cannot reset or duplicate the budget. Only the accepted submitter may explicitly use retained pending text as their answer under the existing chosen-defender checks; the host cannot silently convert another defender's request into an answer.
- When interpretation capacity is exhausted, retain pending text and offer direct answer/recovery without another interpretation call. Keep permission for the chosen defender to submit a newly written direct answer. An exhausted clarification allowance does not consume a defense turn or mark its topic addressed.
- Default total AI clock-pause allowance: 240 seconds per turn, shared across interpretation and retry. Pausing starts at the accepted request; failed-wait/retry time also counts. Once exhausted, the saved remaining answer time runs on the server, including in recovery state. Publish its authoritative deadline and expire the turn normally. Do not grant another pause through a new submission or retry.
- A provider result received before the effective deadline may apply if its identity is still current. Expiry, explicit answer acceptance, restart or ending invalidates late interpretation results. Retained failed/pending text is not an accepted answer; a timeout transcript and coaching must not present it as a successful response.

### Whole-run AI budget and recovery

- Let B be the approved research question maximum, or eight for code-only. Default per-turn question generation allowance: three outbound attempts. Default research preparation allowance: three per uploaded-project version; default coaching allowance: three per run. Preparation retries belong to the same allowance until uploads/settings genuinely change.
- Default whole-run attempt envelope: 9 × B + 6, covering up to three question-generation attempts and six interpretation attempts per question, plus preparation and coaching overhead. Separately track preparation before a run, so resetting or changing uploads cannot evade the owner burst limit. Research cannot generate questions beyond its approved budget, regardless of spare AI capacity.
- Account/run/turn limits are all enforced, not substitutes. A cancelled run cannot transfer unused turn allowance to an unrelated run. Starting a genuinely new run reinitializes its budgets through the existing access and charge contract; it cannot bypass owner burst limits or pending unsettled work.
- On generation/coaching attempt exhaustion, preserve transcript/coverage and enter the existing retry/recovery UI with a clear “retry allowance used” status. Do not launch another provider call. Existing provider-error credit-return eligibility remains available if its conditions actually hold; a rate-limit rejection alone never fabricates that eligibility.
- Opening generation failure continues releasing the reservation as established. A retry can reserve again without duplicate charge and remains bounded by the same opening question allowance. Later attempts remain included in the existing flat charge.
- Shared snapshots expose remaining turn allowances, effective timing/pause status and recovery capabilities, not owner identifiers, balance, raw provider errors or network counters. Restore them on reconnect with no provider call. Publish only fields needed for the team's current actions; private preparation/account details remain host-only where applicable.
- React and WebView screens preserve drafts, offer accessible limit/retry/direct-answer states, avoid duplicate sends and clear drafts only after an acknowledged resolved turn. Keep ordinary transcript/coaching attribution unchanged. Streamlit retains its single-browser behavior; reuse pre-provider safeguards where shared generation functions require them without introducing multiplayer UI.

## Testing Decisions

- Prefer the highest existing behavior seams: authenticated FastAPI HTTP/WebSocket room/account tests, the public timed-turn/session interfaces with a fake clock, and whole-room React interaction tests. Add a small focused public allowance-policy seam only where existing tests cannot control clocks or concurrent admission cleanly; avoid tests of private dictionaries or implementation layout.
- Existing room-access, timed-room, timed-turn and clarification tests provide prior art for host ownership, chosen-speaker enforcement, saved text, first submission, deadline races and stale results. Existing account/mobile tests already cover verifier exchange, expiry, concurrent one-time session issuance and store-failure recovery. Existing live-run/access tests supply once-only charge, opening release, abandonment and error-return fixtures.
- Test concurrent creation at account/global limits, parser failure/cancellation/timeout, admission before parser work, list/close ownership and CSRF, exact retention deadlines, warnings, reconnect after eviction, cleanup races with start/restart/generation, and protected unsettled runs. Verify creation/cleanup never mutates balances by itself.
- Test mobile retry reuse without refreshed expiry, different challenges/destinations, same-network threshold and recovery, multiple users on shared networks, second-network fairness, bounded global exhaustion, forged forwarding headers, trusted-proxy configuration and IPv6 grouping. Preserve successful completion during admission pressure, missing/wrong verifier rejection, replay rejection and retry after session-store failure.
- With AI mocked, assert zero outbound calls for over-cap clarification, exhausted attempts, unauthorized/stale messages and burst rejection. Exercise repeated ordinary clarification requests after two exchanges, all retry paths, guest/host shared ownership and actual attempt accounting including SDK retry settings.
- Test direct answers before/after allowance exhaustion, pending-text ownership, disconnect reassignment, exact deadline races, duplicate acceptance, cumulative pause exhaustion, timeout during recovery, late provider results, and retained draft/transcript/coverage on rejection. Test long research budgets through at least twelve turns and the 100-question budget boundary.
- Test paid and voucher recovery, opening reservation release/retry, unchanged charge amount, no synthetic refund on throttling, and existing provider-error compensation. Use existing store fixtures; no new durable financial schema is required by this specification.
- Complete mocked two-client code and research defenses with clarifications, a timeout, retry, reconnect, direct answers, transcript and coaching. Check desktop, portrait and landscape recovery controls, keyboard focus and retained drafts. Add a mocked HTTP/native-contract walkthrough for start reuse and completion; installed-device sign-in remains separate evidence.
- Run full Python tests with AI/Google/PayMongo mocked, full React tests and production build. Separately record hosted trusted-proxy configuration, legitimate shared-network behavior and installed Android/iOS OAuth return only when a later release is authorized. Do not exercise exhaustion against production or initiate payments to prove this feature.
- The user confirmed these test boundaries on 2026-10-08. This confirmation concerns verification expectations, not independent approval of proposed numeric policies or deployment.

## Out of Scope

- Payment pricing, package changes, money refunds, a new credit ledger, account registration restrictions, durable room/history storage, distributed workers or multi-instance coordination.
- A universal DDoS solution, guarantees against distributed attackers or many independent Google accounts, a new installation identity system, CAPTCHA or separate mobile frontend.
- New questions, panelists, prompt personalities, retrieval, voice, chat semantics, research coverage rules or extra chargeable turns.
- Broad dependency cleanup, unrelated active work, frozen main changes, publishing tickets remotely, pushing or deploying this specification.
- Treating a passing mocked suite as live provider, installed-device, hosted proxy or security-remediation evidence.

## Further Notes

The previous interview was superseded by the user's specification request, not completed by approval. Numeric defaults may be revised at review without altering the core requirements: reject before expensive allocation/calls, reuse legitimate attempts safely, preserve ordinary answers and settle runs before reclaiming them.

Use domain terms consistently: a room may contain successive defense runs; clarification is not a new turn; a credit return is not a payment refund. Existing compensation decisions take precedence over cleanup shortcuts. Clarification/spending limits apply equally to voucher and paid runs.

Implementation should deliver three independently reviewable protections with a final integration gate. Use the local ticket workflow for a later breakdown. After fixes, explicitly verify the original security findings and report residual distributed-abuse and hosted-configuration limitations. No fixes, tests, live walkthrough or deployment are claimed by writing this spec.

## Implementation handoff

2026-10-09: Implemented locally and code-reviewed against dd037d5. See docs/SECURITY_ADMISSION_REVIEW.md and PROJECT_LOG.md for fixes, isolated-release gates and remaining user/hosted/native verification. No push or deployment.

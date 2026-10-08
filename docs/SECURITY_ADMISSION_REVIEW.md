# Security admission implementation review

Local implementation on `feature/question-first-room`, reviewed against `dd037d5`.
The Implement request authorizes the synthesized policy defaults and a local commit;
no push, deployment or frozen-main change is part of this checkpoint. The spec and
seven tickets live under [.scratch/security-admission](../.scratch/security-admission/spec.md).
User visual review is pending. The final isolated selected release passed **384 Python
tests (external providers mocked), 226 React tests and the production build**. The
full working-tree counts below also include preserved unrelated local tests.

## Behavior

Room creation authenticates the account and CSRF token, then atomically reserves
both account and process capacity before multipart parsing. Validation failure or
request cancellation releases the reservation. Two parser workers remain occupied
until their actual work finishes, even if the request times out. A late result cannot
publish without its reservation. Owner-only list, close and resume actions keep
uploads, balances, account identifiers and credentials private to the owner.

Idle lobbies and opening-failure rooms expire after their idle period; settled
completed, ended or abandoned rooms have terminal retention. Active timers, pending
interpretation, planning, generation and unsettled service/compensation states are
protected. Observed all-offline abandonment settles the run using existing financial
policy before retention starts. Expiry invalidates late results and tokens, removes
room memory, and sends an unavailable-room notice that stops reconnect attempts.
It does not modify purchased credit history. Rooms remain in memory on one worker.

Mobile starts deduplicate by proof challenge and allowlisted destination. Reuse
preserves original expiry; an already-open flow returns a safe conflict rather than
reopening OAuth. Existing proof, one-time completion and session-store retry rules
remain. Admission pressure applies to starts, not completion of existing attempts.

Interpretation admission precedes pausing/provider work. Only two successful
clarifications are permitted. Six interpretation attempts include retries. A chosen
defender can explicitly accept saved text or write a new direct answer during
recovery; clarification requests are never silently converted into answers. The
server validates the chosen seat, current turn, length and deadline on direct answers.
After at most 240 seconds of cumulative AI/retry waiting, saved answer time runs
again. Deadline expiry invalidates late provider results. Pending text is not a
recorded answer, and reconnect does not reset budgets.

Question, interpretation, planning and coaching requests share the verified room
owner's burst allowance, including guest-triggered requests and free/voucher runs.
Each question position, preparation and coaching has a retry cap. With approved
question budget B (eight for code), run requests have a 9B+6 backstop; preparation
is separately counted before the run and retained across restarts. SDK automatic
retries are disabled. Provider failures retain existing included retry and eligible
credit-return behavior; local throttling alone does not create refund eligibility.

## Configuration

All values are server-only positive integers. Invalid values fail startup. Caps in
the last column constrain operator overrides; they are not recommended settings.

| Variable | Default | Unit | Maximum |
| --- | ---: | --- | ---: |
| `ROOM_HOST_LIMIT` | 2 | retained + in-flight rooms/account | 20 |
| `ROOM_CREATE_PER_MINUTE` | 3 | admitted new requests/account/rolling minute | 10000 |
| `ROOM_PROCESS_SECONDS` | 120 | upload/processing timeout | 600 |
| `ROOM_IDLE_SECONDS` | 1800 | lobby idle period | 86400 |
| `ROOM_RETENTION_SECONDS` | 1800 | settled terminal retention | 86400 |
| `MOBILE_START_PER_MINUTE` | 60 | all starts/network/rolling minute | 10000 |
| `MOBILE_NEW_PER_MINUTE` | 12 | new flows/network/rolling minute | 10000 |
| `MOBILE_PENDING_PER_NETWORK` | 16 | outstanding flows/network | 128 |
| `AI_OWNER_PER_MINUTE` | 12 | admitted provider attempts/owner/rolling minute | 10000 |
| `AI_INTERPRETATION_ATTEMPTS` | 6 | attempts/turn | 20 |
| `AI_QUESTION_ATTEMPTS` | 3 | attempts/question position | 10 |
| `AI_PLAN_ATTEMPTS` | 3 | attempts/uploaded project | 10 |
| `AI_COACHING_ATTEMPTS` | 3 | attempts/run | 10 |
| `AI_PAUSE_SECONDS` | 240 | cumulative pause/turn | 600 |

Process backstops remain 20 rooms, two parsing workers, 128 pending handoffs and
4096 live rate-limiter keys. IPv4 uses the normalized address; IPv6 is grouped by
/64. Limiter state expires, contains no verifier/provider token and is not exposed
in room snapshots.

`TRUSTED_PROXY_NETWORKS` is an optional comma-separated list of actual proxy CIDRs.
Without it, caller-supplied X-Forwarded-For is ignored. With it, the chain is walked
from the connection peer toward the nearest untrusted hop. Preserve the transport
peer (for example Uvicorn `--no-proxy-headers`) when using this explicit policy;
a separate server proxy middleware must not first trust arbitrary forwarded data.
Do not use a wildcard or guess the Render topology. Hosted proxy behavior is not
verified in this checkpoint. Shared campus NAT still shares a budget; distributed
networks or many authenticated accounts remain residual abuse risks.

## Evidence

- Full working-tree Python suite: 396 passing tests, offline with AI, Google and
  PayMongo mocked. Full React suite: 232 tests and production build passed. Pre-existing local
  tests are distinguished from the selected release in the final handoff.
- New authenticated HTTP/WS and fake-clock cases exercise account quotas before
  extraction, concurrent creation, validation recovery, owner controls, exact idle
  expiry, protected active rooms, bounded question calls, mobile start deduplication,
  network admission, spoofed headers, trusted chain/IPv6 grouping, clarification
  rejection before AI calls, direct answers and bounded retry pause timeout.
- Existing account/native-contract tests cover verifier rejection, one-time exchange,
  expiry and session-store failure recovery. Existing financial suites remain the
  mocked evidence for paid reservation/charge/provider-error behavior; no money was moved.
- Browser walkthroughs use a disposable loopback FastAPI process with synthetic
  Google accounts, voucher access, mocked AI and an accelerated clock. Two separate
  browser contexts completed four- and eight-turn code defenses, including one/two
  clarifications, direct answer, interpretation failure/retry, votes, reconnect,
  synchronized transcript and coaching. Twelve-turn research and mixed runs each
  completed eleven answers plus one timeout, clarification/reconnect, exact citations,
  synchronized progress/transcript and coaching. Desktop, 844×390 landscape and
  390×844 portrait checks reported no horizontal overflow. These are not actual
  provider, installed WebView or physical-device checks.

Screenshots, all synthetic:

- [Code desktop](../screenshots/security-admission-code-mock-desktop.png)
- [Code landscape](../screenshots/security-admission-code-mock-landscape.png)
- [Direct answer desktop](../screenshots/security-admission-direct-answer-mock-desktop.png)
- [Direct answer portrait](../screenshots/security-admission-direct-answer-mock-portrait.png)
- [Research transcript](../screenshots/security-admission-research-mock-transcript.png)
- [Mixed transcript](../screenshots/security-admission-mixed-mock-transcript.png)
- [Recovery clock running, portrait](../screenshots/security-admission-running-clock-mock-portrait.png)
- [Burst rejection/direct answer](../screenshots/security-admission-burst-recovery-mock-desktop.png)
- [Unavailable-room notice](../screenshots/security-admission-expiry-notice-mock-portrait.png)
- [Test-credit run completed](../screenshots/security-admission-test-credit-complete-mock-desktop.png)

A final synthetic test-credit two-browser code defense completed four answers,
reconnect and shared coaching. Its available balance changed from 100 to 90 test
credits, reservations returned to zero, and exactly one charged run was recorded.
This fixture seeded an isolated local ledger; it made no PayMongo call or payment.

The portrait recovery browser check also exhausted the four-minute pause, displayed
the running answer clock, accepted a newly written direct answer and keyboard-resumed
the owned room. Its active Close action remained disabled. An extra recovery row
was removed after it crowded the mobile Submit button.

An initial mixed-run mock had an invalid source identifier. The server retained the
resolved answers and rejected the citation; correcting the synthetic fixture allowed
the complete rerun. No production citation validation was weakened.

Pending: user visual review, actual hosted proxy configuration/shared-network checks,
installed Android/iOS OAuth recovery, a separately requested formal security fix
verification, and any future publication. Passing mocked tests is not a guarantee of
security or live AI quality. Production remains on its existing release.

## Spec review

Independent committed-diff review of `742ca0a`, using `git diff dd037d5...HEAD`,
found four issues; all have subsequent fixes and regression evidence:

1. Timed-out creation cancelled only Starlette's response waiter, leaving the
   downstream upload/parser queue alive. Admission now owns the downstream ASGI
   task, cancels it on timeout, and checks admission/deadline before extraction.
   A blocked-parser reproduction failed before the fix and passes afterward;
   queued-worker and cancelled-body regressions show no late publication/work.
2. Owner burst rejection left an ordinary question with no visible AI-free answer
   path. The composer retains its draft and presents **Submit answer directly**
   after an interpretation allowance rejection. It still requires an explicit click.
3. Expiry cleared its own explanation while stopping reconnect. The hook now
   retains the unavailable-room notice while clearing credentials/room state.
4. Cancellation, timeout, global-cap and cleanup/start-race evidence was missing.
   Added authenticated/global concurrent admission, body cancellation, worker
   timeout, queued-worker cancellation and cleanup/start/restart race cases.

Further regressions verify terminal eviction's final notice and memory cleanup,
and completing an existing proof-bound mobile login while new starts are throttled.
These are offline/mocked tests, not hosted attack or native-device evidence.

## Standards review

Independent committed-diff review found **zero hard documented-standard violations**.
Two low-priority heuristic suggestions remain:

- Possible duplicated policy/guard logic: named policy accessors and a shared retry
  validation method would reduce repeated defaults and interpretation checks.
- Possible repeated recovery-phase selectors across timer, status and composer:
  shared selectors could reduce future drift.

A follow-up also identified message-text coupling in AI recovery. That heuristic
was resolved with the additive `ai_admission` WebSocket error reason, passed through
the socket hook and room dock. All interpretation-admission rejections, including
the full limiter-map backstop, now enable explicit direct answers without parsing
user-facing wording. The two remaining maintenance suggestions do not block the behavioral fixes. No broad refactor
was included. Final review follow-up and selected-release results are recorded in
PROJECT_LOG.md; neither axis claims complete hosted security or live provider proof.

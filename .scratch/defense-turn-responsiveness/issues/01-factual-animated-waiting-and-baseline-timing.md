# 01 — Factual animated waiting and baseline timing

**What to build:** defenders see useful waiting feedback on existing research/mixed
flows while operators can measure the current pipeline without private content.
The initial operation/stage contract is introduced through this visible behavior.

**Blocked by:** None — can start immediately.

**Status:** ready-for-human

Source: [confirmed specification](../spec.md). Breakdown approved on 2026-10-21.

- [x] Show truthful stage/elapsed status near question/submission, mapping and Results
  work; distinguish retained input from accepted answers and retry wait from work.
- [x] Add subtle dots/pulse and known-operation labels for question generation,
  interpretation, identifiable clarification/probe work, mapping/validation,
  overview/cards and recovery. Generic Thinking/Preparing wording is allowed
  when the actual stage is less specific; no timer-driven fictional sequence.
- [x] Keep genuine mapping/coaching progress and ready answers/cards visible; stop
  animation on result, failure, cancellation, end/restart or stale operation.
- [x] Shared web/WebView presentation covers Standard/Free; Streamlit uses native
  waiting indicators and matching factual text. No model or voice change.
- [x] Respect reduced motion, stable focus/layout and polite stage announcements;
  decorative animation and elapsed ticks are not repeatedly read aloud.
- [x] Expose authoritative operation identity/timing through compatible snapshots
  where needed; reconnect/navigation reflect the existing operation, not a reset.
- [x] Capture complete/stage elapsed time, failure class and available supplied usage
  without papers, answers, keys or hidden reasoning; unavailable data is not zero.
- [x] Establish the comparable baseline/replay harness with synthetic sources/answers.
  Mocked timings test instrumentation, not a real speed result. Actual inference
  and quality remain the separate gate owned by 08.
- [x] Verify room/browser and native-fallback status lifecycle, including no artificial
  delay, narrow layouts and existing permitted recovery controls.

## Comments

2026-10-21 implementation handoff: operation/stage/timing contract, shared React
WaitingIndicator integrations, Streamlit spinner wording, backend/frontend tests,
and the synthetic timing comparison/replay harness are implemented locally.
Python 742 and React 408 pass offline with AI mocked, and the production build
passes. Layout/reduced-motion evidence is synthetic and labeled; native Streamlit
and real-room visual review remain pending, so the web/WebView/Streamlit criterion
and the browser/native lifecycle criterion remain unchecked. No paid inference,
push, or deployment.

2026-10-21 independent review against user-approved baseline 4af094c: returned to
ready-for-agent. [Review findings](../reviews/01.md) record six P2 Spec issues:
unpublished operation starts, default timing logging disabled, supplied usage not
connected, active-generation presentation during retry sleep, incomplete coaching
duration/failure capture, and a JSONL summarizer without synthetic-case replay.
Four previously checked criteria are reopened (elapsed/status, published timing,
measurement capture and baseline replay); the two prior app/fallback verification
criteria remain open. Three of nine criteria remain checked. Standards found no
hard breaches and one nonblocking duplication suggestion. Fresh 16 Python / 71 React
checks pass offline with AI mocked but do not cover those failing requirements.
No runtime fixes or publication occurred. Ticket 02 remains blocked by this ticket.

2026-10-21 corrections handoff: all six review findings are addressed locally.
Operation starts now bump the revision and publish before AI work; the retry wait
is a static "Waiting to retry…" stage with its own timing record; the default
timing sink is configured independently of Uvicorn and records provider-supplied
usage; coaching samples completion after durable storage and keeps section failure
classes; and the harness runs bounded synthetic source/answer defenses with
case/condition/run identity and case-aware comparison. Provider usage is also
forwarded on the mapping path. Added/updated focused tests for each behavior.
Full offline gates pass: 751 Python tests, 409 React tests and the production
build, with AI/Google/payments mocked. Synthetic layout/timing evidence was
regenerated from the current production stylesheet and harness. Independent
re-review, real-room/browser lifecycle, native Streamlit and human visual review
remain open, so those two criteria remain unchecked. No paid inference, commit,
push or deployment.

2026-10-21 independent re-review: [corrected-patch findings](../reviews/01-rereview.md)
confirm operation publication, default logging, retry-wait presentation and
post-storage completion timing are fixed. Standards: zero findings. Spec: three
P2 findings remain—cross-room supplied-usage collisions, failed coaching stages
logged as successful, and a baseline runner that bypasses research/mixed flows.
Reopened measurement capture and baseline criteria; 5/9 remain checked and status
returns to ready-for-agent. Ticket 02 remains blocked. Fresh 19 selected Python
and 72 React checks pass offline with providers mocked; a broader Python run
stalled and was interrupted. Full reported 751/409/build gates were not rerun.
The two existing interface/lifecycle checks and human visual review remain open.
No runtime fixes, commit, push or deployment occurred in this re-review.

2026-10-21 correction verification: [final fix review](../reviews/01-fixes.md)
closes all three P2 findings. Opaque usage lifetimes isolate concurrent rooms and
late callbacks; coaching records actual section outcomes and truthful retry
stages; bounded research/mixed replay now exercises real coordinator commands,
funded clients with mocked HTTP, temporary SQLite and complete progressive cards.
Comparison rejects changed source/answer fingerprints. Final independent
Standards0/Spec0; restored measurement/baseline criteria, 7/9 checked and
ready-for-human. The original two interface/lifecycle evidence checks remain open
and ticket02 stays blocked pending acceptance. Fresh final offline gate:
757 Python, 409 React and build pass, providers mocked. No live inference,
human visual approval, commit, push or deployment.

2026-10-21 local interface continuation: [browser/fallback evidence](../reviews/01-interface.md)
closes the two remaining local checks: real two-context HTTP/WebSocket waiting,
clarification/probe/recovery, reconnect/navigation, progressive coaching, keyboard,
desktop/portrait/landscape and Free mixed WebView-shaped presentation; actual
Streamlit spinners plus three failure/recovery AppTests. Providers mocked and
temporary databases only; installed-device and human visual evidence are not
claimed. All 9/9 implementation checks are checked, still ready-for-human.
User explicitly requested proceeding to ticket02 while away; that continuation
is authorized without claiming visual approval. Runtime source unchanged here.

# Research defense practice — proposed ticket breakdown

Date: 2026-10-17. Approved as drafted by the user; the ten separate
ready-for-agent tickets are published in the [local ticket index](README.md). Parent: [approved specification](spec.md).
Prototype B — Speaker desk is the selected layout. No implementation starts here.

## Proposed order and blocking edges

| Ticket | Title | Blocked by | End-to-end result |
| --- | --- | --- | --- |
| 01 | Research-first practice with varied openings | None | Research setup and guide lead to a grounded opening informed by private durable history, with one history/charge commit. |
| 02 | Host choice when an opening repeats | 01 | A repeated candidate stays out of play until the host retries or explicitly accepts the current validated candidate. |
| 03 | Live voice answers in Speaker desk | None | A chosen defender can explicitly capture, review read-only words and manually finalize/send an answer through a bounded authorized pilot. |
| 04 | Voice probe replies and recovery across screens | 03 | Same-question replies, interpretation recovery and valid unsent voice drafts work across navigation/reconnect without replay or stale speech. |
| 05 | Grounded per-answer text coaching | None | A complete short research/mixed defense receives original-versus-improved coaching for every recorded answer in focused Results and typed Streamlit. |
| 06 | Progressive coaching with safe completion and recovery | 05 | Long reports arrive in admitted sections; one closing, retained cards, failed-only retry and once-only financial recovery remain consistent. |
| 07 | Evidence-based voice delivery feedback | 04, 05 | Submitted speech supplies attributable filler/structure feedback and reliable measures, with honest language and evidence limits. |
| 08 | Android microphone practice | 04 | A rebuilt Android app uses the trusted web voice flow with explicit permission and lifecycle-safe capture; typing remains available. |
| 09 | iOS microphone practice | 04 | A rebuilt iOS app uses the same flow with purpose disclosure, trusted-origin permission and lifecycle-safe capture. |
| 10 | Complete defenses and local review handoff | 02, 06, 07, 08, 09 | Integrated mocked defenses, suites/build, responsive review and separately identified live/native/provider evidence complete the feature handoff. |

01, 03 and 05 have no functional prerequisites on each other. The agreed delivery
order still favors checkpoint 1 before checkpoint 2 before checkpoint 3; it is
not represented as an artificial code dependency. Shared code edits should be
serialized/coordinated even for logically independent tickets. This draft does
not request parallel agents or external-model sharing.

## Slice details

### 01 — Research-first practice with varied openings

**What to build:** Fresh research setup offers the brief answer guide and starts
Q1 using the host's recent openings for the accepted paper, across fresh rooms
and restarts, without losing grounding or once-only financial behavior.

**Blocked by:** None — can start immediately.

**Acceptance criteria:**

- [ ] Fresh setup defaults to Research paper; mixed remains available; code-only is labeled Experimental and explicit/restored selections and code behavior remain intact. The general guide recommends voice when available without promising capture before its pilot is enabled or revealing upcoming answers. Mirror relevant labels/defaults/guide in typed Streamlit.
- [ ] Server-computed accepted-paper content identity survives renamed copies, distinguishes changed accepted content and isolates host accounts. Mixed code alone does not replace the paper's identity. Store only bounded opening metadata, not papers/answers/audio.
- [ ] Latest five committed openings per host/content for 30 days survive store/process restart; local SQLite and real local PostgreSQL checks cover migration, expiry, pruning, isolation and concurrent access.
- [ ] Existing opening generation sees recent context while retaining the current reviewer, eligible topics and validated citations. Exact/normalized duplicates receive one admitted regeneration; another duplicate remains a recoverable uncharged preparation failure until ticket 02 adds acceptance. A prompt/lexical comparison does not claim universal semantic novelty.
- [ ] Authoritative history append and run charge/access transition commit once under one transaction, including race/replay/rollback behavior and free/voucher runs. History lookup/write failure cannot publish or charge a new opening; stale proposals cannot commit.
- [ ] Authenticated room/API and whole-App checks demonstrate repeated fresh-room practice, visible recovery and unchanged code-only/typed behavior. Opening failure retains existing reservation release and bounded host retry; no unrelated room/account/payment refactor is required.

**Demo/check:** Run two mocked research starts with the same host/paper, then a
rename and store restart; observe history-aware requests, one active validated
opening and one charge/history entry per accepted run. Force a duplicate/storage
failure and show recoverable preparation with no rejected question in play.

**Primary stories:** 1–19, 21–24, 26, 106.

### 02 — Host choice when an opening repeats

**What to build:** If bounded variation still repeats, the host can explicitly
retry or accept the validated repeated candidate while the team waits.

**Blocked by:** 01 — Research-first practice with varied openings.

**Acceptance criteria:**

- [ ] After the admitted duplicate regeneration, expose a clear host-only candidate/limitation with Retry and Accept repeated question; candidate preview is explicitly not an active defense question. Guests see waiting guidance rather than host controls.
- [ ] Bind choice to the current host, room, run, map, candidate and generation. Old acceptance, changed-map, changed-run, guest and racing duplicate commands cannot activate or charge an obsolete candidate.
- [ ] Retry stays within existing finite admission, preserves accepted paper/history and does not create asked-question history or charges for discarded candidates.
- [ ] Accept revalidates source/ownership/current history and performs the once-only commit from 01; voting/deadline starts only after commit. Explicitly accepted repetition is a real committed opening and is retained idempotently.
- [ ] Two-client mocked and whole-App checks cover failure/retry/accept/reconnect and role-specific mobile and keyboard actions. Real local transaction tests cover acceptance races and persistence failures without double charging.

**Demo/check:** Force two recent duplicate candidates, inspect waiting views,
accept once, then replay an old choice after changing the run/map. Complete
checkpoint 1 with the app runnable and code-only unaffected.

**Primary stories:** 20–25.

### 03 — Live voice answers in Speaker desk

**What to build:** In an operator-enabled research/mixed web pilot, the chosen
defender can explicitly start a mic, see recognized words read-only and Send a
finalized answer before the current deadline, with ten shared minutes/run and a
usable typing fallback.

**Blocked by:** None — can start immediately.

**Acceptance criteria:**

- [ ] Implement selected B context/workspace layout and narrow-screen stacking/answer shortcut while retaining citations/PDF, seats, timer, chat and typed drafts. Starting voice must resolve rather than silently overwrite a typed draft; Switch to typing opens a fresh editable answer.
- [ ] Configure maintained OpenAI live speech independently from text AI, disabled unless explicitly enabled/configured. Before capture, show provider/retention disclosure and support limitations; revalidate model/protocol/account access. Standard keys stay server-only; no real audio/API call is necessary for offline verification.
- [ ] Explicit capture authorizes only the online chosen defender in the current research/mixed answer window, with server-issued attempt scope. Other seats, stale runs/turns and code-only voice are rejected. Until 04, probe input remains typed. No page visit, vote, silence or reconnect starts capture.
- [ ] A bounded server-controlled relay enforces current authorization, one active stream, finite frame/buffer/duration/attempt limits, actual forwarded-audio accounting and ten shared minutes/run. Deadline, cap, disconnect, selection/run change, leave/end/restart, navigation/page teardown and lost authorization stop forwarding and invalidate stale callbacks from the first usable release.
- [ ] Show readable provisional versus finalized words in a read-only field. Manual Send, including keyboard submission, stops capture, finalizes ordered/deduplicated segment identities and uses the normal submission/acknowledgment path once. Finalization does not extend the deadline; silence/final events/cap do not submit.
- [ ] Server validates final transcript/provenance and current attempt, nonempty/size limits and deadline; client claims cannot fabricate verified voice text or measures. Wrong/late/obsolete data never enters another question. Capture denial/provider failure/overflow/finalization failure gives truthful unsent/rejected status and typing recovery.
- [ ] Forwarded retries/discards consume shared allowance; reconnect/refresh cannot reset it. At the cap stop new audio and finalize if possible without sending. Retain only submitted provenance and supported evidence, discard bounded audio buffers, and keep sensitive content out of logs/browser storage. Current price/voucher rules and code-only controls remain unchanged.
- [ ] Authenticated fake-audio and whole-App/browser checks cover normal capture/send, forged actor/provenance, duplicate/out-of-order finals, cap/deadline races, no auto-send, no extra forwarding after revocation, typing recovery, readable grey words and desktop/phone keyboard use. Essential lifecycle safety is not deferred to 04.

**Demo/check:** Two mocked clients select one defender, stream fake speech, manually
finalize/send and observe one normal accepted answer. Repeat with a nonselected
client, reached cap and deadline during finalization. Actual speech quality is
separate evidence and must not be claimed from this demo.

**Primary stories:** 27–34, 36–47, 49–52, 54–65, 103–105, 107.

### 04 — Voice probe replies and recovery across screens

**What to build:** Extend the working answer flow to same-question probe replies
and the app's navigation/reconnect/interpretation recovery, retaining explicit
manual submission and correct speaker/probe identity.

**Blocked by:** 03 — Live voice answers in Speaker desk.

**Acceptance criteria:**

- [ ] Enable authorized voice for the current probe reply with independent attempt/probe identity, original-answer attribution and unchanged question number, reply length and deadline. Team chat and explicit clarification remain typed.
- [ ] Preserve existing interpretation/direct-answer/probe recovery. Recognized clarification is not falsely recorded as a successful answer; saved/direct acceptance attaches provenance only to the matching server-finalized text.
- [ ] A disconnect or navigation away stops capture without pausing time; a still-valid finalized unsent draft can be reviewed on return and submitted only by a fresh manual action. Obsolete/provisional material cannot be restored as an editable typed answer or auto-sent; refresh carries no new voice-draft durability promise.
- [ ] Selection/probe/turn/run changes, recovery, timeout, restart and room closure invalidate outstanding finals. Reconnect never restarts the mic or replays Send, and repeated recovery events cannot replace an accepted original/probe answer.
- [ ] Allowance is shared across original answers, probe replies, speakers and retries. Existing tab-scoped typed drafts, Back/refresh/task returns and input-mode changes do not reset usage or silently replace unrelated unsent work.
- [ ] Two-client fake-audio tests cover probes, interpretation failure/retry/direct recovery, disconnection with selection change and navigation away/return. Responsive keyboard walkthroughs retain timer context, safe typing and correct accepted transcript attribution; complete checkpoint 2.

**Demo/check:** Answer by voice, receive a probe, record a reply, interrupt/reconnect
and submit a valid finalized draft manually. Reject a delayed old-probe segment
after the turn advances. Show typing still works after the shared cap.

**Primary stories:** 35, 37, 48–54, 57, 61, 64, 79, 102–105.

### 05 — Grounded per-answer text coaching

**What to build:** A short completed research/mixed defense produces a complete
validated report with detailed guidance for every recorded answer, shown in B's
question-selector/detail layout and shared as typed research coaching in Streamlit.

**Blocked by:** None — can start immediately.

**Acceptance criteria:**

- [ ] Expand report/recipient/client contracts additively before migrating research consumers, preserving legacy and code-only reports. Introduce only the narrow report ownership seam needed by this slice; no broad mechanical refactor or temporary broken callers.
- [ ] Every recorded turn in a validated complete report includes original answer, actual speaker/probe exchanges, specific strengths/gaps, supported stronger wording and practice task. Preserve originals; missing facts are labeled conditional/scaffolds, not invented methods/results. Advice uses confirmed research field, approach, stage, setting and evidence.
- [ ] Unanswered turns get factual guidance without fabricated answers/strengths; empty sessions retain a factual no-unnecessary-AI summary. No unasked future question receives a card. Missing/invalid required cards cannot produce ready or successful settlement.
- [ ] Results uses an accessible question selector and focused expandable details rather than a wall of text; retain original-versus-improved comparison and truthful voice/text evidence labels. Typed input has no invented audio statistics; observed wording/filler examples can be discussed without asserting uncaptured spoken measures.
- [ ] Share richer research text coaching and originals in typed Streamlit without adding voice or fictitious financial compensation. Transcript/export includes completed cards, provenance where already available and truthful status; code-only data/output remains compatible.
- [ ] Keep the existing complete-report request/closing/retry path runnable for bounded short reports. Do not introduce partial financial success or claim long-report batching here; 06 expands generation/recovery to admitted sections. Truncated, oversized or incomplete output fails recoverably rather than appearing fully coached.
- [ ] Existing report contracts plus full room/App/fallback tests demonstrate end-to-end typed short defenses, grounded instructions, every-recorded-turn membership, speaker/probe attribution, no-answer cases and desktop/phone keyboard/detail navigation. Mocked text is not evidence of real coaching quality.

**Demo/check:** Complete a short mocked research defense with an answer, probe and
missed turn; compare each original with supported wording and a practice task.
Reject a missing card instead of showing a complete report. Keep the app runnable
while 06 adds long-run batching/progressive Results.

**Primary stories:** 5–6, 10, 69–85, 95, 97, 104–106.

### 06 — Progressive coaching with safe completion and recovery

**What to build:** Long research reports arrive automatically in finite admitted
sections, with a single closing, immediate access to ready cards and honest
completion/recovery that does not settle or return credits twice.

**Blocked by:** 05 — Grounded per-answer text coaching.

**Acceptance criteria:**

- [ ] Freeze required membership from the accepted transcript and generate overview/every required section automatically in bounded sequential/admitted groups. Stable run/section/job identities and finite attempts deduplicate work and fence stale success/failure.
- [ ] After the overview, show a valid optional last-reviewer closing once using its remaining interval, then open progressive Results. Bad/empty optional closing skips safely; reconnect restores time/progress; section retry never replays closing or interrupts Account/payment tasks.
- [ ] Show ready cards and completed/required progress with pending/failed states. A required failure preserves ready sections exactly; admitted host retry targets failed sections only, continues valid pending work and charges no new defense. Exhausted recovery identifies permitted actions clearly.
- [ ] Partial Results remain financially unfinished until the overview and every required section validate and durable completion succeeds. Completion-write failure remains recoverable. Update room retention/stage logic so partial Results are not expired or treated as successful settlement.
- [ ] Preserve existing eligible end-unavailable credit return, interruption recovery and abandonment policy. Paid compensation is once-only; free/voucher runs cannot mint credits. A return/restart/close/replacement fences late work so it cannot reverse a return, overwrite another report or settle twice. Speech failure alone does not grant a refund for an otherwise available typed defense.
- [ ] Partial/failed/complete export retains accepted originals, speaker/probe/provenance/evidence and ready sections. Streamlit keeps ready research text work and truthful failed-section recovery without pretending to support live-store compensation. No audio or durable Results archive is added.
- [ ] Protocol/store/App checks cover closing/progress/retry and races among final-section completion, persistence failure, end-unavailable and restart; compare ledger outcomes and unchanged ready cards. Exercise twelve-question and large supported-budget reports with providers mocked, plus code-only regression.

**Demo/check:** Fail one section after overview/closing, review ready cards,
retry just the failed section and finish once. In another run, return eligible
charged credits then deliver a late success and show it cannot settle/reverse
the return. This is part of checkpoint 3, which also requires 07.

**Primary stories:** 75–98, 106, 108.

### 07 — Evidence-based voice delivery feedback

**What to build:** Coaching distinguishes what was actually said, reliable
recording-derived measures and AI suggestions for each accepted voice answer or
probe reply, including stronger structure and captured filler examples.

**Blocked by:** 04 — Voice probe replies and recovery across screens; 05 — Grounded per-answer text coaching.

**Acceptance criteria:**

- [ ] Associate server-validated capture evidence with the accepted original answer/probe and actual speaker. Discarded, provisional, wrong-text and obsolete attempts supply no coaching performance evidence; their forwarded usage still counts against voice allowance.
- [ ] Show captured filler/repetition examples and supported clearer structure/wording. Distinguish transcript observation, measured evidence and suggestion. A cleaned transcript cannot prove no fillers or complete filler totals; typed answers cannot receive invented spoken measures.
- [ ] Compute/display approximate rate or pauses only from sufficient reliable capture/timing evidence for submitted material. Explain missing/insufficient/uncertain measurements without zero placeholders, accent grades, psychological confidence or transcript-only pronunciation/tone claims.
- [ ] English-first voice remains independent of typed language support. Tagalog/Bisaya/code-switching are offered individually only after support/representative quality evidence; preserve natural wording without forced translation or automatically labeling normal particles as fillers. Unsupported recognition leads to typing, not a poor-delivery judgment.
- [ ] Per-turn cards, overview and export retain evidence provenance and speaker/probe attribution without an audio archive. Finite buffering, log privacy and app/provider retention disclosure stay intact.
- [ ] Fake-audio/report/App tests demonstrate reliable and unavailable evidence, observed uhm/structure advice, distinct speakers/probes, typed comparison and malicious client-measure claims. Record real recognition/filler/measurement/language checks separately; unavailable real checks stay pending. Complete checkpoint 3 together with 06.

**Demo/check:** Compare an accepted voice answer with reliable synthetic timing,
a typed answer and an uncertain-recognition sample. Show supported examples and
honest unavailable evidence, not fabricated statistics or study decisions.

**Primary stories:** 64–74, 79–85, 97, 107–108.

### 08 — Android microphone practice

**What to build:** A rebuilt Android app captures audio only after the trusted
app's Start mic and system permission, sharing the working web answer/probe flow
with safe lifecycle stopping and typing fallback.

**Blocked by:** 04 — Voice probe replies and recovery across screens.

**Acceptance criteria:**

- [ ] Add audio permission declaration/runtime handling and trusted-origin WebView capture policy. Permit only requested audio for the exact trusted application origin; deny external frames/pages, camera and broad wildcard grants.
- [ ] Denial/revocation/backgrounding/navigation/destruction stops capture and upstream forwarding; resuming needs a fresh explicit action. Preserve sign-in/payment/download trust and callback boundaries.
- [ ] Reuse the server's authorization, cap, manual-finalizing Send and current deadline. Older/unsupported builds retain typing rather than a misleading supported mic action.
- [ ] Native policy/lifecycle checks and an available Android build verify source integration. Record actual installed permission denial/capture/background/reconnect separately with device/build identity; missing hardware/provider evidence remains pending, never a fabricated pass.

**Demo/check:** Build the Android client where tooling exists, exercise policy
denial and lifecycle checks, and present a real-device capture checklist. Actual
capture is a separate claim from the source/build and mocked web checks.

**Primary stories:** 99, 101–105, 108.

### 09 — iOS microphone practice

**What to build:** A rebuilt iOS app supplies a microphone-purpose explanation
and trusted-origin capture for the same voice flow, retaining typed use when
capture or permission is unavailable.

**Blocked by:** 04 — Voice probe replies and recovery across screens.

**Acceptance criteria:**

- [ ] Add microphone-purpose disclosure and platform-appropriate trusted-origin audio permission/capture handling without granting camera/external-origin capture or requesting a mic on page load.
- [ ] Stop capture on denial/revocation/background/navigation/teardown and require explicit restart, with server-side deadline/cap/revocation protection independent of teardown-message delivery.
- [ ] Preserve existing auth/payment/download allowlists and native callbacks; old/unsupported builds keep the current typed flow.
- [ ] Verify policy/lifecycle integration and build with macOS/Xcode/signing when available. Record actual installed capture/permission/background/reconnect and toolchain/device identity separately. Linux source checks do not establish an iOS build or recording; unavailable checks remain explicit pending evidence.

**Demo/check:** Present checked source/policy and a build/device capture checklist;
where macOS and an installed build are available, record the actual results
separately. No broad permission grant is accepted as a shortcut.

**Primary stories:** 100–105, 108.

### 10 — Complete defenses and local review handoff

**What to build:** Verify the feature as one research-practice experience and
present the local preview and evidence, without conflating mocks, hosted behavior
or actual recorded speech/native-device support.

**Blocked by:** 02 — Host choice when an opening repeats; 06 — Progressive coaching with safe completion and recovery; 07 — Evidence-based voice delivery feedback; 08 — Android microphone practice; 09 — iOS microphone practice.

**Acceptance criteria:**

- [ ] Run the full Python and React suites/build, real local database history/migration/expiry/concurrency/restart checks, and complete mocked two-client research/mixed runs including twelve questions and supported large report membership. Code-only, typed-only, existing access/price/citations/PDF and Streamlit remain compatible.
- [ ] Cover duplicate/stale openings, voice/typed/probe/clarification, send/finalization/deadline/cap, interpretation/reconnect/navigation recovery, every-turn grounded cards, once-only closing, partial/failed retry/export, completion persistence and credit-return/stale-work races. Do not merely repeat unit helper assertions.
- [ ] Review Speaker desk and focused coaching at desktop/portrait/landscape with keyboard/focus, long papers/reports, readable read-only words, unobscured next actions and unchanged live-timer/account-task behavior. Present local preview/screenshots before any publication.
- [ ] Record actual speech quality, supported language/code-switching, observed fillers/measures, maintained provider access/protocol/cost/retention, hosted relay behavior and installed Android/iOS capture as separate evidence. No paid call/audio upload/deployment is implied; unavailable evidence keeps the relevant capability/readiness claim pending.
- [ ] Keep the prototype source/verdict as a reference; do not promote fake transcripts, scenario controls or prototype switchers. Finish the integration review and handoff against the implementation baseline selected at implementation time, without changing the parent spec or merging/pushing/deploying under this ticket-writing request.

**Demo/check:** Present the full mocked research/mixed flow, the selected layout
and a clear passed/pending evidence record. This completes checkpoint 4's local
handoff; it cannot certify devices/providers that were not actually checked.

**Primary stories:** 108 and integrated acceptance of 1–107.

## Checkpoints, implementation frontier and scope boundaries

| Agreed checkpoint | Required tickets | Runnable outcome |
| --- | --- | --- |
| 1 — Opening history | 01, 02 | Research-first setup and varied Q1 with safe host repetition choice. |
| 2 — Live web voice | 03, 04 | B's live answer/probe voice, bounded allowance and explicit recovery; native clients can type. |
| 3 — Complete answer coaching | 05, 06, 07 | Grounded every-turn text/voice feedback, progressive reports and safe financial recovery; typed Streamlit shared. |
| 4 — Native and integration | 08, 09, 10 | Native source/build integration and full local handoff, with real provider/device gaps explicitly recorded. |

Initial functional frontier: 01, 03 and 05; recommended first work: 01 to follow
the agreed checkpoint order. Blockers express actual producer/consumer gates,
not every other ticket in an earlier numbered checkpoint. 10 lists only terminal
prerequisites; its other prerequisites are transitive. 08 and 09 do not need
coaching generation before microphone integration because they reuse the shared
web flow. 07 needs accepted voice/probe data and per-answer coaching, but does not
depend on the separate section scheduler in 06.

No standalone broad prefactor is required by current code inspection. Introduce
additive store/report/transport contracts inside their first complete slice,
before migrating callers. Each ticket includes its own relevant tests and local
verification; 10 does not defer safety or sole correctness testing until the end.
Every numbered slice leaves the app runnable. Intermediate scope is explicit:
01 may fail safely on repeated Q1 until 02; 03 keeps probes typed until 04; 05
proves complete short reports and fails closed on incomplete output until 06
adds long-run bounded sections. These are checkpoint boundaries, not changes to
the final specification.

## Approval record

On 2026-10-17 the user selected “Approve as drafted (Recommended)” for this exact
ten-ticket breakdown. All ten numbered tickets are now published locally with
ready-for-agent status; see the [ticket index](README.md). Approval does not start
implementation, authorize external-model sharing, push source or deploy. The
parent specification remains unchanged.

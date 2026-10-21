# Ticket 03 — checkpoint 1 local presentation

Date: 2026-10-21. Local implementation evidence complete; user review separate.
Preview: http://127.0.0.1:8866/checkpoint-review

The gallery presents captured states and a runnable synthetic mixed-room link.
It uses the actual production React build, reviewed isolated FastAPI runtime,
HTTP/WebSocket, temporary SQLite accounts and mocked provider HTTP. Synthetic
papers, answers and receipts only; no real sign-in, payment or AI request.
Fixture/control routes remain under `.local/turn03-preview/`, never in production.
The walkthrough releases its test gates and simulates one short provider429 so
users can inspect the countdown without configuring accounts or keys.

## Observed workflow

- Actual explicit mapping, profile confirmation and four-question budget approval.
- Standard policy snapshot:45000ms window, one automatic transient retry and
  provider-directed retry enabled. A short Retry-After produced a static countdown.
  Opening calls were PlanDraft, failed QuestionDraft, then only QuestionDraft.
- Refresh during gated generation kept operation ID, started_at and authoritative
  deadline unchanged. Active/failed/retry stages came from actual room snapshots.
- Two browser contexts joined through real room actions and shared the next
  question after recovery. An earlier programmatic guest restore fixture failed
  to connect; the verified run used the actual Join room tab and Join team flow.
- Answer review and following question shared the same processing deadline.
  Controlled-clock expiry retained the accepted original answer, cleared the
  active operation and showed the45-second recovery message. Keyboard retry
  continued to question2; no repeated answer interpretation was dispatched.
- A full four-question mixed defense finished4/4answer coaching and settled once.
  The unchanged normal transitions used SubmissionDraft→PlanDraft→QuestionDraft:
  still three requests. Completion used submission/planning plus protected coaching.
- Desktop1440×960, portrait390×844 and landscape844×390 captures show readable
  retry/countdown controls without horizontal overflow. Narrow Results and keyboard
  question-card navigation pass; reduced-motion media was enabled for Results.
  Representative portrait retry, expiry recovery and portrait Results images
  were inspected. No installed Android/iOS or physical-device claim is made.

## Preview-discovered wording correction

The first capture exposed a misleading dock/header: an opening retry claimed that
there was a saved resolved turn. `roomPresentation.ts` now uses the existing
isResolved predicate to distinguish first-question/uploads-retained guidance from
resolved-turn guidance. Existing accepted-answer wording remains unchanged.
A new presentation regression failed before the fix, then passed. Independent
Standards0/Spec0 for this two-file delta; existing nonblocking duplication notes
remain separate. Full frontend gate:414React tests and production build pass.
Final captures use this corrected build.

## Measurement capability

The current Standard research/mixed synthetic runner completed identical baseline
and repeat conditions:108content-free stage/total records across44operations.
Input fingerprints match; records contain no paper/answer/question/prompt fields.
The comparison reports matching cases and zero differences for the fixed synthetic
latency inputs. These are controlled-clock measurements demonstrating export,
aggregation and replay, not proof of faster models or lower cost.

The actual browser mixed run additionally recorded31stage/total events including
an admitted automatic retry, a failed45-second question stage, manual recovery,
accepted answers and progressive coaching. Durations include deliberately held
fixture gates and an advanced test clock, so they are not live-provider latency.
Usage is synthetic; missing measurements remain unavailable rather than zero.

Evidence and scripts: `.local/turn03-preview/`, including browser-verification.txt,
browser-timings.jsonl, baseline.jsonl, baseline-summary.json and evidence/ captures.
Final isolated `.venv/bin/python -m unittest discover -v`:789tests passed
in140.728s, AI/Google/payments mocked; foreign-only coverage excluded. Full frontend:
414React tests and build pass. The earlier correction recheck's60focusedPython/
16real-local-PostgreSQL checks remain valid for unchanged backend source.
The reviewed source checkpoint is being committed locally; no push or deployment. Checkpoint1 remains the current three-call pipeline; combined
planning, focused context and measured provider tuning are later tickets.

The final presentation criterion is satisfied locally:03has9/9implementation
checks. Human visual approval, actual provider speed/quality/cost, hosted and
installed-device checks remain separate. No push or deployment is authorized.

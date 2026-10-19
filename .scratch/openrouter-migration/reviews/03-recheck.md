# Ticket 03 — independent implementation recheck

**Superseding verified fix (2026-10-20):** source **c4d838d** closes the delayed-
retry time restoration issue. All four independent probes, Python 673,
React 393/build and Standards 0 / Spec 0 pass. See [the final fix handoff](03-retry-fix.md).
Earlier findings/verdicts below are historical. Actual-provider/user review
remains separate; no push/deployment.

**Latest independent follow-up (2026-10-20):** the original four-minute pause is
fixed and its two probes pass, but delayed retries refund already-consumed
answer time. One P2 remains; see [the timer follow-up](03-timer-followup.md).
Earlier complete/ready-for-human verdicts are superseded for timer recovery.

Date: **2026-10-20**. User requested checking the other agent's implementation.
Fixed diff: `git diff 889a8e2...84b5542`.
Commits: **b5e6244** (implementation), **84b5542** (handoff).
Unrelated dirty reasoning/local-testing/QR/planning changes were excluded.
Runtime and canonical tests were not edited during this review.

**One P2 Spec finding remains. Ticket 03 needs a timer correction.**

## Standards

Independent review found **one P3 documentation violation**, with no runtime
hard-rule violations or actionable baseline smells. `AGENTS.md`, “After each
logical change,” rule 3 requires current-status updates when a checkpoint ends,
but the implementation only appended Changes: `PROJECT_LOG.md` still said
03–04 were not started. The current-status update in this review handoff closes
that documentation issue with the accurate recheck outcome.

The Responses-shaped adapter preserves existing prompt/validation ownership.
Its placement, capture fields and cancellation hint follow the established funded
question workflow; no additional architecture work is needed for this ticket.

## Spec

### P2 — Resume the answer clock after failed interaction work

Ticket requirement: **“Do not freeze authoritative answer timers on provider or
budget failure.”**

`backend/rooms/submissions.py:83` introduces funded requests whose allowance
refusal/provider failure reaches the existing failure path at lines122–124.
`TimedTurn.interpretation_failed()` (`backend/timed_turn.py:306`) changes only
the phase/error. It leaves the unused AI pause and extended answer deadline
intact. Failure is therefore still presented as a paused clock until the
remaining AI-pause budget ends (default **240 seconds**).

Two independent controlled-clock, two-client room probes reproduce the missing
requirement with an immediate budget refusal and an HTTP503. Both produce:

- Original answer deadline **1135001**; failed-work deadline **1375001** — an
  additional **240000ms** despite no elapsed processing time.
- `clock_paused=true`, `pause_deadline_ms=1255001`.
- `CatchUpDeadline` at the original deadline plus1 leaves
  `phase=interpretation_retry`, `timed_out=false`.
- Correct provider request counts remain intact: **2** for allowance refusal
  (opening planner/reviewer only), **3** including the failed HTTP503 request.

This is a missing requirement in a pre-existing mechanism, not an allegation
that this diff introduced the pause implementation. The new test named
`test_failed_interaction_resumes_the_answer_clock` checks only that an extended
deadline exists and eventually expires. It does not establish immediate clock
resumption after failure. The handoff's “failure-clock resume” claim is therefore
not supported by that test.

Correction: end the unused processing pause on failure while preserving pending
text, account for legitimately elapsed allowed processing time, restore the
remaining authoritative answer/probe clock and schedule it consistently. Cover
instant allowance refusal/provider failure, elapsed processing time, retry,
probe replies and stale failures. Preserve direct-answer and recovery rules.

No other concrete defect found in reviewer routing, fixed lower reasoning,
allowance reservations/coaching protection, duplicate guards, stale-result
fencing or preserved prompt/source/language handling.

## Verification

- Exact committed source isolated with `git archive 84b5542` under
  `.local/openrouter-03-recheck/artifact`; unchanged built frontend supplied for
  FastAPI static mounting. No unrelated dirty source/tests are included.
- New canonical interaction module independently passes **10/10 in2.140s**.
  Log: `.local/openrouter-03-recheck/logs/interactions.log`.
- Full committed-source unittest discovery passes **666 tests in125.639s**,
  offline with external providers mocked, temporary real SQLite and controlled
  clocks. Diagnostic stack dumps were enabled; dedicated temporary paper storage
  prevented cross-process lease contention. Log `python-full.log` in that logs
  directory. This excludes the untracked foreign local-dev tests mentioned in
  the original handoff; no failure is attributed to those tests here.
- Unchanged production frontend plus the committed phone test extension passes
  **393 React tests in36files** and `npm run build`. Logs `react.log` and
  `react-build.log`. This is mocked DOM/build evidence, not physical phone review.
- New independent timer probes both **fail** against committed source. Source:
  `.local/ticket03-spec-probes/ticket03_timer_probes.py`. Parent independently
  confirmed both failures in **0.592s**, log
  `.local/openrouter-03-recheck/logs/timer-probes.log`. Run from the artifact:

```bash
ROOM_DOCUMENT_DIR=/tmp/ibm-bob-ticket03-review-timer \
/home/jhonryl-pamaybay/IBM-BOB/.venv/bin/python -c \
"import sys, unittest; sys.path.insert(0, '/home/jhonryl-pamaybay/IBM-BOB/.local/ticket03-spec-probes'); unittest.main(module='ticket03_timer_probes', argv=['unittest', 'Ticket03TimerProbes.test_budget_refusal_resumes_answer_clock', 'Ticket03TimerProbes.test_provider_failure_resumes_answer_clock'], verbosity=2)"
```

No paid inference, actual-provider schema/cost check, fresh PostgreSQL,
hosted/browser/native review, credential access or private-paper access.

Final review counts: **Standards1 P3 (current-status record corrected by this
handoff); Spec1 P2 (timer recovery remains open)**. Reopened only ticket03's
timer criterion/statusready-for-agent. Ticket04 remains independently unblocked;
ticket05 still requires both03and04. No runtime/canonical test edit, commit,
push or deployment.

## Correction (2026-10-20)

The P2 timer correction is implemented, verified offline with providers mocked
and a controlled clock, and committed locally (source hash recorded in
`PROJECT_LOG.md`).

- `TimedTurn.interpretation_failed` now settles the processing pause (charging
  only elapsed time beyond the AI-pause budget), clears the pause fields,
  restores the remaining answer/probe deadline and bumps the clock id; the
  funded failure path schedules that restored clock, and `retry_interpretation`
  re-arms the pause for the new request.
- Both independent probes now **pass** against the fixed source: for both
  provider503 and budget refusal, `failure_deadline` **1135001** equals
  `original_deadline` **1135001**, `failure_pause_deadline` is null,
  `failure_clock_paused` is false, `CatchUpDeadline` at the original deadline
  plus1 reaches `phase=generating`/`timed_out=true`, and request counts remain
  **3** and **2**.
- Canonical coverage added in `tests/test_openrouter_interactions.py`: immediate
  failure equality for 503 and allowance refusal, retry re-pausing only for
  elapsed processing time, a failed probe reply restoring the probe deadline,
  and a stale failure that cannot touch a timed-out clock.
  `tests/test_clarification.py` now asserts the resumed clock instead of the
  retained pause.
- Offline full `unittest discover` passes **677** with only the two pre-existing
  foreign `tests/test_local_dev.py` failures; unchanged frontend passes
  **393** React tests in36files plus `npm run build`.

Standards P3 stays closed by the current-status update; Spec P2 is closed with
this correction. The ticket's timer criterion is re-checked and ticket03 is
ready-for-human again. User visual review, actual-provider quality/cost, fresh
PostgreSQL, hosted and native evidence remain separate pending gates; no paid
inference, push or deployment.

# Ticket 03 independent recheck

Date: 2026-10-21. Outcome: corrections required; runtime unchanged by this review.
Comparison: `git diff c31cf8f...d7e8181`.
Commits: `00db48d` (source) and `d7e8181` (receipt).
The committed artifact is frozen in `.local/turn03-recheck/checkpoint`; unrelated
working-tree edits are excluded. This supersedes the zero-remaining correctness
conclusion in [the implementation handoff](03.md).

## Standards

Independent review: **0 documented violations, 2 low-priority judgment calls**.

- Duplicated Code: questions.py:118–132 and submissions.py:131–145 repeat remaining
  window calculation, expiry rejection, bounded await and timeout translation.
  A shared bounded-request helper would reduce the chance of divergence.
- Primitive Obsession: questions.py:186,215 and submissions.py:163 inspect the
  literal `legacy` version. Explicit policy capabilities would avoid workflows
  interpreting version identifiers while preserving old semantics.

These are nonblocking maintainability suggestions. Documented Python/package
navigation and domain vocabulary are respected; no later combined-planning scope
was introduced. The reviewer's initial comments were independent of the Spec axis.

## Spec

**Three confirmed correctness findings remain.**

1. **P1 — Funded writer dispatch can occur at the expired deadline.** Ticket:
   “one 45-second authoritative window spanning stages” and respect remaining time
   and current-work checks. questions.py:113 supplies a stopped predicate checking
   only generation/run/phase. The synchronous funded client does not receive the
   captured processing deadline; its own timeout is 90 seconds per stage. An outer
   `wait_for` rejects eventual publication but cannot forcibly stop its thread.
   A deterministic real-adapter/mocked-HTTP probe completed PlanDraft at the exact
   45-second deadline, then dispatched QuestionDraft at that deadline. Both fake
   receipts consumed the synthetic run allowance; the late question was correctly
   withheld. Include the authoritative deadline in provider current checks before
   further reservations/dispatch and preserve conservative holds for prior work.
2. **P2 — Opening-history preflight is outside the cap.** Ticket: at expiry, stop
   accepting results and expose recovery. questions.py:103 awaits recent_openings
   before the bounded request at lines128–130. A blocked history read kept the
   question generating with a visible operation after its processing window had
   elapsed. The probe used a 30ms policy window, advanced its controlled clock to
   expiry, waited80ms and observed the task still pending. Bound preflight against
   the same remaining deadline, without resetting it or authorizing stale work.
3. **P2 — Exhausted-credit 429 can auto-retry.** Ticket explicitly requires exhausted
   funds to use manual/operator recovery. processing_policy.py:123–128 accepts an
   SDK429 with short Retry-After regardless of quota classification; the HTTP/SSE
   classifier at openrouter_stream.py:86–99 handles daily messages but not depleted
   credits/quota. Direct HTTP, stream-envelope and SDK probes using insufficient
   credits/insufficient_quota plus Retry-After1 all returned allowed=True with a
   1000ms delay. Preserve machine-readable quota/credit classification and deny
   automatic recovery consistently without exposing raw provider messages.

No scope creep found. Existing validation retries remain distinct from transient
classification; their preservation alone is not a correctness finding.

## Independent verification

- **57 Python tests passed** in20.659s: processing policy, OpenRouter stream,
  retained-stage recovery and funded interactions, from the committed artifact;
  AI/provider HTTP mocked. No full Python suite rerun. The implementation's786
  isolated/791worktree report remains historical evidence, not a new review claim.
- **22 React tests passed** across waiting presentation, WaitingIndicator and
  whole-App stages; the isolated production build passed. Root game sources match
  the committed target. Initial symlinked-node_modules test execution was blocked
  by Vite's filesystem rule for the PDF worker; the final run used the unchanged
  root frontend and passed. An initial Python import lacked built static assets;
  the subsequent built-artifact run passed.
- **15 real-local PostgreSQL16.15 checks passed** in23.566s: existing defense
  allowances, protected coaching allowances, opening history and integrated text
  checkpoint suites, including twelve-question research/mixed runs and partial
  coaching. All providers mocked; every test created/dropped a synthetic database.
  This closes the prior lack of baseline PostgreSQL evidence, but does not prove
  corrected deadline/fund-retry behavior. Disposable fixture stopped.
- Two deadline probes and three quota-classification probes confirm the failures
  above. Scripts/logs remain `.local/turn03-recheck/`; no production/test file was
  edited to make them pass. No paid inference or real account/database contacted.

Ticket03 returns to ready-for-agent; authoritative window, exhausted-funds handling
and expiry-recovery checks are reopened (4/9 remain checked). The boundary-test/
financial criterion remains open because failing cases need regressions/fixes,
despite passing baseline PostgreSQL. Checkpoint1 runnable preview remains open.
Ticket04 waits for corrected03. No push/deployment, hosted/native check or human
visual sign-off. Runtime and canonical tests remain unchanged by this review.

Follow-up, 2026-10-21: the three findings were corrected locally and covered by
new regressions; see [the correction pass](03-fixes.md). This review remains the
historical failing baseline. The correction pass has not itself been independently
rechecked, and corrected real-local-PostgreSQL boundary/spending evidence and the
checkpoint-1 preview remain open.

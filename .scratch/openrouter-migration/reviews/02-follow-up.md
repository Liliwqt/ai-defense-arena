# Ticket 02 — follow-up check of the recheck fixes

**Superseding verified correction (2026-10-19):** all original findings and the
remaining SSE retry issue are now closed in **1efb1a1**. Full Python 656,
React 393/build and independent Standards 0 / Spec 0 pass. See
[the final fix handoff](02-sse-fix.md). Evidence and earlier verdicts below are
historical; actual-provider/user review remains separate.

Date: 2026-10-19. User requested checking the corrected implementation.
Original baseline: **bd10cc3**. Reviewed final source **c6ca8ac**, focusing
`git diff bbc7a11...c6ca8ac` (fix commit **2d15a16**, handoff **c6ca8ac**).
Unrelated dirty reasoning/local-testing/QR/docs changes were excluded.

**All three original findings are fixed. One P2 streamed-error classification
gap remains.** Runtime source and canonical tests were not changed in this check.

## Standards

Independent Standards review: **zero hard repository-rule violations**. Mixed
eligibility mirrors the legacy research route; shared conversation/scenario
guidance is restored. Reusing the shared constants resolves the prior policy
drift; remaining prompt-assembly duplication needs no additional architecture
work for ticket02. The streamed-error issue below is an actionable behavior
finding, not an additional independent coding-standard violation.

## Spec

Independent follow-up confirms the original fixes:

- Every research reviewer can again cite implementation in mixed mode;
  research-only mode remains paper-only.
- HTTP503/network/invalid structured output now reaches the existing bounded
  post-answer automatic retry. Ordinary HTTP4xx and plain configuration/budget/
  cancellation failures remain outside that automatic path.
- Reviewer requests reuse the conversation/scenario policy, including resolved
  probes and grounded hypothetical guidance.

### P2 — Streamed rate-limit errors are incorrectly retried

Requirement: retain existing retry/recovery policy. Existing
`tests/test_question_recovery.py:96` explicitly classifies400/401/403/404/429
provider failures as nonretryable.

`backend/openrouter_stream.py:84` converts **every** SSE `error` envelope to
`ValueError`, then line104 turns it into `InvalidQuestionResponse`. The room
automatically retries that exception at `backend/rooms/questions.py:128`, so a
valid rate-limit event bypasses the new `ProviderStatusError.retryable=False`
classification. The same error sent as ordinary HTTP429is handled correctly.

This is a documented wire format. OpenRouter commits HTTP200when streaming
headers are sent; later provider failures appear inside SSE, including
`error.code=429` with `metadata.error_type=rate_limit_exceeded`.
[Official OpenRouter error documentation](https://github.com/OpenRouterTeam/docs/blob/main/api_reference/errors-and-debugging.mdx).

Room-level reproduction: accept Q1and its answer, then return the documented
HTTP200SSE rate-limit envelope from the next planner. Valid success responses
are queued only to reveal whether a second attempt occurs. Expected: manual
`phase=retry` after three total requests (Q1planner/reviewer plus rate-limited
planner). Actual: automatic planner/reviewer dispatches reach `phase=voting`
with **five** total requests. The accepted answer is retained. This is retry
classification and extra dispatch, not duplicate defense-credit charging.

Correction: distinguish validated provider SSE error status/type from malformed
model output. Preserve sanitized classification and redact provider messages;
known rate/quota/auth/configuration failures stay manual, supported server
failures may retry once, and unknown dispatched costs remain conservatively
reserved. Add paired HTTP-versus-SSE recovery checks, including429and503.

## Independent verification

- Isolated `git archive c6ca8ac`:
  `.local/openrouter-02-final-check/artifact`. The unchanged client build was
  copied only for FastAPI static mounting. Original three review probes copied
  unchanged from the prior review artifact.
- Original three reproductions now **pass3/3** against committed code: mixed
  implementation citation, shared request guidance and post-answer503recovery.
  Command: repository `.venv/bin/python -m tests.ticket02_review_probes` from that
  artifact. Log: `.local/openrouter-02-final-check/logs/original-probes.log`.
- Six updated focused unittest modules independently **pass90tests** in16.225s
  (external providers mocked, real temporary SQLite). Log:
  `.local/openrouter-02-final-check/logs/focused.log`.
- Additional documented SSE429room probe **fails as described** in1.317s.
  Source: artifact `tests/ticket02_stream_limit_probe.py`; command:
  `.venv/bin/python -m unittest
  tests.ticket02_stream_limit_probe.Recovery.test_streamed_rate_limit_stays_manual -v`.
  Log: `.local/openrouter-02-final-check/logs/sse-rate-limit.log`.
- Prior agent's650Python/393React/build/185PostgreSQL logs remain separate
  recorded evidence. This follow-up claims no fresh full-suite, PostgreSQL,
  browser, actual inference/cost or hosted/native verification.

Final counts: **Standards0 hard violations; Spec1 P2** (streamed nonretryable
errors incorrectly retried). Three original findings closed. Only recovery
remains reopened;03–04wait for correction. No commit, push, deployment, runtime
edit or private-paper/credential access in this review.

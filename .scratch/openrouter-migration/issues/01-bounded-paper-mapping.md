# 01 — Bounded OpenRouter paper mapping

**What to build:** A host explicitly maps/remaps a research or mixed paper
through DeepSeek high, sees grounded progress and safe recovery, and cannot start
the temporarily unavailable code-only or voice workflows.

**Blocked by:** None — can start immediately.

**Status:** ready-for-human

- [x] Expand the shared server integration before migrating mapping; use the exact
  assigned model, supported schema/reasoning/context limits and redacted errors.
- [x] Give preparation fixed settings and a separate finite allowance with atomic
  request reservation, known-usage settlement and conservative unknown usage.
  Refresh, remapping and retry cannot reset that allowance or dispatch unpaid work.
- [x] Keep profile corrections, current budget/profile confirmation, source checks,
  streamed progress, stale-work cancellation and retained valid preparation.
- [x] Enforce code-only creation/start/restart disablement on server and both setup
  interfaces, explaining restored selections and preserving existing results.
  Research + code remains available. Voice stays off server-side and in clients.
- [x] Verify the complete mapping path, accounting failures/races and real local
  PostgreSQL reservation/settlement behavior, plus mocked room/contract and setup
  browser checks. Choose bounded initial mapping settings from synthetic evidence.

## Comments

- 2026-10-19 final local handoff: implemented in161ac1e/3a2ffff; independent Standards0/Spec0 remaining againsta185680 after fixing both saved-results findings. Isolated621Python (external providers mocked),393React/build and desktop/portrait/landscape synthetic browser checks pass; earlier3real-localPostgreSQL allowance checks are separate evidence. See [final review](../reviews/01.md). Ready for human review locally; actual provider/model quality/schema/billing and hosted/native evidence remain later gates. No push/deployment/main change. This supersedes pending-verification comments below.
- 2026-10-19 continuation: full isolated frontend gate passes 393 React tests/build; 14 focused Python generation/HTTP/SQLite contracts pass in shared and isolated trees, including Unicode context and conflicting streamed cost evidence. Full ASGI Python gate, browser review, two-axis review and commit remain pending. Approval service still fails before launch with “Selected model is at capacity”; no bypass or completion claim.
- 2026-10-19: implementation is in progress; see [interim verification handoff](../reviews/01.md). Baseline a185680 confirmed. Mapping/allowance and code/voice gates are implemented locally; final Python/browser checks, two-axis review and commit are pending because automatic approval review is unavailable. No completion/ready-for-human claim.
- Approved as drafted on 2026-10-19. Parent: [OpenRouter migration specification](../spec.md).
- Read the [approved dependency index](../README.md) for checkpoint boundaries and evidence gates. This ticket does not authorize a push, deployment or change to main.

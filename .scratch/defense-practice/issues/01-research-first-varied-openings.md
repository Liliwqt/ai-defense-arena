# 01 — Research-first practice with varied openings

**What to build:** Fresh research setup offers the brief answer guide and starts
Q1 using the host's recent openings for the accepted paper, across fresh rooms
and restarts, without losing grounding or once-only financial behavior.

**Blocked by:** None — can start immediately.

**Status:** ready-for-human

## Acceptance criteria

- [x] Fresh setup defaults to Research paper; mixed remains available; code-only is labeled Experimental and explicit/restored selections and code behavior remain intact. The general guide recommends voice when available without promising capture before its pilot is enabled or revealing upcoming answers. Mirror relevant labels/defaults/guide in typed Streamlit.
- [x] Server-computed accepted-paper content identity survives renamed copies, distinguishes changed accepted content and isolates host accounts. Mixed code alone does not replace the paper's identity. Store only bounded opening metadata, not papers/answers/audio.
- [x] Latest five committed openings per host/content for 30 days survive store/process restart; local SQLite and real local PostgreSQL checks cover migration, expiry, pruning, isolation and concurrent access.
- [x] Existing opening generation sees recent context while retaining the current reviewer, eligible topics and validated citations. Exact/normalized duplicates receive one admitted regeneration; another duplicate remains a recoverable uncharged preparation failure until ticket 02 adds acceptance. A prompt/lexical comparison does not claim universal semantic novelty.
- [x] Authoritative history append and run charge/access transition commit once under one transaction, including race/replay/rollback behavior and free/voucher runs. History lookup/write failure cannot publish or charge a new opening; stale proposals cannot commit.
- [x] Authenticated room/API and whole-App checks demonstrate repeated fresh-room practice, visible recovery and unchanged code-only/typed behavior. Opening failure retains existing reservation release and bounded host retry; no unrelated room/account/payment refactor is required.

## Verification

Run two mocked research starts with the same host/paper, then a
rename and store restart; observe history-aware requests, one active validated
opening and one charge/history entry per accepted run. Force a duplicate/storage
failure and show recoverable preparation with no rejected question in play.

## Comments

- 2026-10-17 — User approved the ten-ticket breakdown as drafted; published locally with its agreed blocking edges and acceptance criteria. Specification stories: 1–19, 21–24, 26, 106.
- Parent: [research-defense practice specification](../spec.md). The parent remains the source of full scope, test boundaries and accepted ADRs; it is not changed by publication. Selected UI: B — Speaker desk, captured on prototype/research-practice (source f0d74a7, verdict a3046c4).
- Each ticket includes its own verification and leaves the app runnable. Record provider-mocked, actual speech, local database, native-build/device and hosted evidence separately. Ticket approval does not start implementation, authorize external-model sharing, push or deploy.

- 2026-10-17 — Implemented locally in 5326361 and responsiveness fix 2a99d9c; independently code-reviewed against user-confirmed baseline f15e756 with Standards0 and Spec0 actionable findings. Selected-source verification:555Python tests (AI/Google/PayMongo mocked),361React tests,174real-local-PostgreSQL checks with external providers mocked, and TypeScript/Vite build pass. Actual local Chromium synthetic desktop/portrait/landscape checks confirm research default, visible guide, no width overflow and restored explicit code selection after refresh. Review/evidence: [ticket01 handoff](../reviews/01.md). User visual and live-AI/hosted checks remain pending; no push/deploy. Ticket02 repetition acceptance is not implemented.

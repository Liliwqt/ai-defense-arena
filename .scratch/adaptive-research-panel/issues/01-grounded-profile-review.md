# 01 — Grounded profile review and confirmation

**What to build:** Preparing a research or mixed defense presents a grounded, multi-field/multi-approach suggested profile alongside the existing map. The host can inspect and confirm the profile, uncertainty and question budget; teammates can inspect the same state. React and Streamlit both support this read/confirm path. Starting captures the confirmed profile without changing existing reviewer dialogue yet.

**Blocked by:** None — can start immediately.

**Status:** ready-for-human

- [x] The existing single structured mapping request returns validated fields, approach choices, optional setting, source explanation, grounded paper references and explicit uncertainty. No extra classification request is made.
- [x] Multiple fields/approaches are supported; an explicitly confirmed Unclear profile is permitted without inventing a method. Stage remains separate.
- [x] Server-owned profile excerpts use existing citation/location validation. Invalid references, unsupported choices, excessive values or incomplete final output fail preparation safely.
- [x] Existing streamed topics remain Draft until final validation; neither streamed nor final-but-unconfirmed profiles appear host-confirmed.
- [x] React and Streamlit show the suggested profile and cited basis; only the host can confirm the current map/profile/budget. Guests see read-only profile and confirmation state.
- [x] Start requires current confirmation; older research maps without a validated profile require preparing again. A run captures a fixed profile and reconnect restores it without another AI call.
- [x] Code-only defenses and existing account, timer, coverage and run-charge behavior remain unchanged. Existing tests/fixtures stay compatible through explicit profile-aware research fixtures rather than an anonymous approval bypass.
- [x] Mocked normal HTTP/WebSocket and mapping-request checks demonstrate host/guest authority, uncertainty acknowledgment, invalid output rejection, legacy-map handling and restored snapshots. React tests and the Streamlit read/confirm path are checked.

## Working boundary

Use the approved Adaptive research panel specification as the implementation contract. Work locally on `feature/question-first-room`; preserve existing reasoning/local-access work and unrelated files. This ticket does not authorize a push or deployment. Record implementation and verification in the shared handoff log, distinguishing offline mocks from live evidence.

## Local handoff

Implemented and independently reviewed against `c498598`. Verification and synthetic preview: [ticket 01 review](../../../docs/ADAPTIVE_RESEARCH_PANEL_REVIEW.md). User visual review remains pending. Tickets 02–04 remain ready-for-agent; no push or deployment.

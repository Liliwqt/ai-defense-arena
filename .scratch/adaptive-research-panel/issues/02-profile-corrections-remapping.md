# 02 — Profile corrections, remapping and safe recovery

**What to build:** The host corrects fields, approaches or setting, prepares a new map and reconfirms the resulting profile/budget in React or Streamlit. Corrections remain attributed host descriptions, survive failure/retry and cannot be mistaken for source evidence or silently reset by the next map.

**Blocked by:** 01 — Grounded profile review and confirmation.

**Status:** ready-for-agent

- [ ] Edits are host-only and limited to preparation; active-run edits are rejected without resetting answers or other valid state.
- [ ] Unsaved changes prevent the host UI from presenting old approval as ready to start. Accepted changes invalidate old map approval and Start eligibility.
- [ ] Remapping receives immutable correction input as data, retains host-selected descriptions, and keeps its citation-grounded explanation and uncertainties distinct. The model may flag supported conflicts rather than overwrite the correction or claim it is paper evidence.
- [ ] The host receives a fresh map identity and must confirm the updated profile and budget. Stale approval or results cannot re-enable Start or replace a newer correction/map.
- [ ] Failed mapping retains uploads and corrections; retry uses the same saved input. Duplicate preparation, edits during pending work and late callbacks are handled consistently with existing coordinator fences, without duplicate AI work or silent state loss.
- [ ] Reconnect restores saved correction and approval state. Streamlit correction changes invalidate its old map/session/coaching scope. An unchanged restart retains the confirmed profile under existing cost/access rules; changing profile cannot bypass preparation or rewrite a prior run.
- [ ] Mocked public room/AI boundaries verify host edits, unchanged guest state, remap/retry, uncertainty and host/source conflict, invalid commands, stale work, reconnect, active-run rejection and preserved access/credit rules. Relevant frontend and fallback checks pass.
- [ ] Finish checkpoint 1: run the full offline suites/build and present profile/map review on desktop, portrait and landscape. Record screenshots and factual implementation/verification notes; adaptive dialogue remains the next checkpoint.

## Working boundary

Use the approved Adaptive research panel specification as the implementation contract. Work locally on `feature/question-first-room`; preserve existing reasoning/local-access work and unrelated files. This ticket does not authorize a push or deployment. Record implementation and verification in the shared handoff log, distinguishing offline mocks from live evidence.

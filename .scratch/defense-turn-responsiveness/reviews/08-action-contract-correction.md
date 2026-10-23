# Exclusive action response contract — 2026-10-24

Local correction following the [contradictory action/probe retest](08-coherent-selection-results.md).
Ticket 08 remains **4/7**. No new provider request, key read, model promotion,
push or deployment occurred.

## Contract

The existing lookup envelope now advertises a union of strict result shapes:

| Action | Required fields | Meaning |
| --- | --- | --- |
| `answer` | `action`, `assessment`, `next_move` | Assess the submitted answer and select a complete candidate; null selection still requires permitted completion. |
| `clarify` | `action`, `clarification` | Explain the existing question without accepting an answer or planning another turn. |
| `probe` | `action`, `probe` | Request one detail about the current answer; unavailable for a pending probe reply. |

Each variant forbids the others' fields. Answer assessment retains its exact
server turn/topic and bounded reason; selection retains the request's candidate
ID mapping. The wrapper converts a validated variant to the original domain
model, then all existing action, citation, coverage, eligibility and completion
guards still execute. A null candidate cannot bypass the completion guard.

Compatibility removes only unused **null** slots from older flat responses.
Contradictory non-null data, mixed selection formats, half selections and unknown
candidates are rejected. It does not repair a bad action or fill a missing field.
Malformed action tags reach strict validation without an unhashable-tag error.

Shared generation guidance now asks for only the selected action's fields.
Separate/noncombined planning retains its contract. No model, reasoning, provider,
timer, price, retry or spending-policy setting changed. Per-request candidate
maps remain isolated. The existing diagnostic captures the actual result class,
including its new RootModel union inside the normal lookup envelope.

## Standards

Independent review: **0 hard violations; 0 new optional smells**. Strict variants,
null-only compatibility, per-request binding, lookup separation and unchanged
domain validation were confirmed. This is source review, not human acceptance.

## Spec

Independent review: **0 confirmed findings**. Action shapes are exclusive,
pending-probe replies exclude another probe, and original semantics and policy
settings remain. Actual provider acceptance and full-defense reliability remain
open; the review did not authorize inference.

## Verification

- Red funded HTTP regression reproduced the old typed-contract gap in **0.100s**;
  its corrected version passed in **0.100s**.
- Full isolated `.venv/bin/python -m unittest discover -v`: **892 passed in
  209.358 seconds**, offline, AI/Google/payment providers mocked.
- `npm test`: **414 passed**; `npm run build`: passed.
- Targeted provider, room, diagnostic, typed Streamlit and complete-defense
  checks: **66 passed in 51.545 seconds**, providers mocked.
- Coverage includes non-probe/probe conflicts, cross-action fields, required
  payloads, malformed tags, exact advertised variants, valid legacy responses,
  candidate mapping, original completion rejection and retained pending-probe
  state when a second probe is rejected. Existing diagnostics now expect earlier
  `response_schema_invalid` for contradictions; pending-input/privacy assertions
  remain.
- **24 frozen source hashes**, scoped runtime delta and credential-free
  root/isolated plans match. Foreign reasoning/budget hunks were excluded from
  the checkpoint and preserved in the shared tree. All earlier paid checkpoints,
  artifacts and ledgers remain unchanged. Scoped whitespace checks passed.

Review baseline remains user-approved `8465a88`; new pre-change snapshots and
scoped patch are retained under ignored `.local/action-contract/`. Its isolated
checkpoint starts at `4a6be54` plus previously reviewed local corrections and
this change. Scoped work remains local and uncommitted. Existing PostgreSQL,
browser, hosted and installed-device evidence is separate and was not rerun.

## Separate live gate

The [new two-request plan](08-action-contract-plan.json) is prepared with the
same synthetic Critical-only state, GLM/low/6144, 45-second diagnostic window
and privacy/price controls. Its conservative bound is **US$0.0511776**, fitting
a proposed fresh **US$0.06 total campaign cap**. The compiled ignored launcher
checks source, plan and absent output before any key read, and pins a new ledger.
It is **not authorized or executed**; prior paid approvals are finished.

Offline passing checks do not prove provider schema enforcement, fewer invalid
generations, faster complete turns, all-role dialogue quality or a full defense.
DeepInfra shared-pool capacity remains a separate unresolved gate.


Subsequent separately authorized execution is recorded in
[the live results](08-action-contract-results.md). Both isolated outcomes passed
application validation (one answer/plan, one probe); review latency and wider
readiness remain unresolved. The earlier preparation-only statement above is
historical; that separate two-request approval is now finished.

# Assessment response constraints — 2026-10-24

Local correction following the [completed Critical replay](08-critical-replay-results.md).
Ticket 08 remains **4/7**, with actual provider and full-defense gates open.
No additional inference, model promotion, push or deployment occurred.

## Problem and change

The replay identified `plan_invalid_assessment` without retaining its precise
invalid field. It did not establish the earlier full-run failure's cause.
An HTTP-mocked regression reproduced a wrong turn passing response parsing and
failing the later prospective-plan guard, in 0.071 seconds.

Combined submission responses now advertise and enforce the prospective server
context's exact zero-based turn and topic. Reasons must contain non-whitespace
text within the existing 600-character limit. Strict integer behavior rejects
boolean/string turns. Clarification and probe assessments remain nullable.

The original submission and prospective-plan checks remain intact. There is no
repair of rejected decisions, nor a change to models, reasoning, routing, prices,
timers, retry rules or spending policy. Separate legacy planning retains its
existing schema. React and typed Streamlit use the shared response builder.

The replay captures the actual response-schema class from the funded request
and uses it for parsing, including its evidence-lookup envelope. It no longer
parses against a generic, weaker combined schema. Existing paid campaign source,
plans, outputs and ledgers were preserved; current `--plan` output describes
the new contract and does not authorize execution.

## Standards

Independent review: **0 hard violations; 0 new judgement-call smells**.
Strict metadata checks, original semantic guards and captured-schema fidelity
were confirmed. The earlier optional probe-orchestration duplication is unchanged.

## Spec

Independent review: **0 confirmed findings**. Known metadata and bounded reasons
are constrained without changing action semantics or making a live-readiness
claim. The initial review's verification caveat was resolved by the completed
offline gate below, rather than treating intermediate failed commands as passes.

## Verification

- Full isolated `.venv/bin/python -m unittest discover -v`: **884 passed in
  213.890 seconds**, offline, AI/Google/payment providers mocked.
- `npm test`: **414 passed**; `npm run build`: passed, unchanged frontend.
- Targeted provider contracts, diagnostics, combined room submissions and typed
  Streamlit checks: **38 passed in 41.535 seconds**, providers mocked.
- Wrong topic/turn, boolean/string turns, empty/whitespace/oversized reasons,
  valid answer/clarification/probe and replay schema fidelity covered.
- Frozen source hashes, scoped runtime delta and root/isolated credential-free
  plans match. Scoped whitespace check passed. No key was read for this change.

The isolated checkpoint starts at `4a6be54` plus previously reviewed diagnostic
changes and this correction. The ticket's approved review baseline remains
`8465a88`; the narrow new patch and pre-change snapshots are retained under
ignored `.local/assessment-schema/`. Foreign reasoning/budget edits were excluded
from that checkpoint and preserved in the shared working tree. All work remains
local and uncommitted.

Actual provider support for the narrower contract, improved acceptance rate,
all-role speed/quality, hosted behavior and native evidence remain unverified.
No existing campaign approval covers another request.

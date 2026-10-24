# Panelist activity prototype review

Status: user selected A — Editor notes, 2026-10-24. Design direction confirmed; production implementation remains subsequent work.

## Question and source

Which inline layout makes factual task/context information readable during AI
waits, then disappears completely as soon as the result appears?

The [confirmed plan](PANELIST_VISIBILITY_PLAN.md) supplies the requirements.
The source is captured separately from main on local branch
`prototype/panelist-activity`, commit
`ef445a249750d177b90074660887ee3e82b6588a`, based on `13870e2`.
No prototype code has been merged into main or pushed. Carry this branch/commit
pointer into subsequent specification and implementation tickets as the primary
visual source. The prototype must be rewritten against actual operation state;
its simulation is not production code.

## Preview

Open <http://127.0.0.1:8865/?preview=1&research=1&prototype=panelist-activity&variant=A>.
Use the bottom arrows or Left/Right outside controls to compare:

| Variant | Structure |
| --- | --- |
| A — Editor notes | Compact task line, vertical editor-style gutter, highlighted context |
| B — Focus words | Large task sentence with a prominent highlighted context phrase |
| C — Context ledger | Task/status column beside structured context/material rows |

Prototype controls are below the room; its Controls button scrolls there.
Choose an AI task, explicitly simulate a stage update, or press Result ready.
Fast result simulates completion in 120 ms. Both completion actions remove all
activity markup without a reading delay. Recovery/accessibility controls show
failure, retry, cancel, restart, current-only simulated reconnect, no-context
fallback, reduced motion and Standard/Free labels.

The temporary source is at
`.local/panelist-activity-prototype/game/src/prototypes/panelist-activity/`.
To restart the preview, run `npm run prototype:activity` from
`.local/panelist-activity-prototype/game/`.

## Verification

- TypeScript and Vite production build passed in the isolated prototype worktree.
  Output excludes the prototype module/switcher. Existing large-PDF-chunk warning
  remains. Initial dev-server binding required sandbox escalation; it now listens
  on localhost only. An initial build invoked from the repository root had no
  build script; the successful command ran from `game/`.
- Local browser interaction checks: all three layouts remove activity for normal
  and 120 ms completion. Six synthetic task cases show explicit stage changes,
  current-only reconnect simulation, clearing on failure/cancel, retry wording,
  no-context fallback, reduced motion and completion. Finished coaching remains
  visible alongside pending work.
- A/B/C inspected at 1440×1000, 390×844 and 844×390 without horizontal document or
  activity overflow. Mobile paper/activity switching, keyboard variant switching,
  focused-control arrow protection, reload-stable variant and system reduced
  motion checked. Screenshots are under the branch's prototype `evidence/` folder.
- Six-task browser observations recorded zero application `/api/` or `/ws/`
  requests. No AI calls, keys, Google or payments were used.

These are synthetic local prototype checks. Simulated reconnect is not evidence
of actual socket authorization, two-client synchronization, server lifecycle or
provider correctness. No full Python/React production suites, installed-device,
hosted or live-AI check is claimed. The later layout selection below is an
explicit user decision, not evidence that every device/scenario was reviewed.

## Decision

Decision captured on the same local prototype branch at
`f98d50d7f3692c3f0e64c523a39c35f7c349ffd9`.

User explicitly selected **A — Editor notes** in response to the prototype
comparison question. Use A's compact task line, vertical editor-style gutter and
highlighted context as the visual reference. No additional reason or preference
for a hybrid was supplied; do not infer one.

Preserve the confirmed behavior: open activity for every AI wait, complete
disappearance when a result appears, no reading delay, validated context only,
and no extra provider call. Keep B/C and the switcher on the prototype branch as
comparison evidence. Production implementation must use authoritative operation
state rather than copying the synthetic scenario controls.

Next: specification and implementation workflow. No production-code merge, push
or deployment is authorized by selecting the layout.

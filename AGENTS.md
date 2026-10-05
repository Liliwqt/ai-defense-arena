# Agent handoff rules

This project is a small FastAPI/React multiplayer hackathon prototype with a Streamlit fallback. `README.md` explains how to run it. `PROJECT_LOG.md` is the shared handoff record for agents and separate session windows.

`main` is frozen for a hackathon review window of roughly three weeks from 2026-10-01. Do not merge into it, redeploy it, or alter its behavior until the user says the review is over. Work on `feature/question-first-room`; `main` still serves the earlier 3D room, and that difference is expected for now.

Before working:

1. Read `README.md` and `PROJECT_LOG.md`, then inspect the files relevant to your task. The code is the source of truth if the log is stale.
2. Check `PROJECT_LOG.md` for active work. If another session is changing the same files, coordinate before editing them. Entries can be historical: before relying on one, confirm it is still live by running `git log --oneline` against the files it names. An entry whose work is already recorded as a commit or as a dated entry lower in this log is stale, and you should expire or annotate it rather than stall on it.
3. For work that may overlap another session, add a short active-work entry with your session label, intended files, start date, and how the work ends (the commit hash or dated log entry that will close it).

After each logical change to project files:

1. Reread the end of `PROJECT_LOG.md` so you do not erase another session's entry.
2. Append a dated change entry: what changed, which files changed, what you verified, and what remains. Group related edits into one entry; do not log every keystroke.
3. Update the current-status and active-work sections when a checkpoint starts, finishes, or becomes blocked. Remove your own active-work entry when it is done. You may also expire or annotate another session's entry when you can point at the commit or dated log entry that finished it; name what you expired in your own change entry. Do not silently delete a claim you cannot prove is finished.
4. Report the same outcome to the user. The log does not replace a clear handoff in the conversation.

Never put API keys, secrets, full environment values, or uploaded private project text in the log. Keep entries factual; distinguish implemented work from mocked or live verification. Do not mark a checkpoint reviewed until the user has actually reviewed it.

## Legacy, not wired into the app

The room is a flat React layout. `game/src/App.tsx` renders `FlatRoom.tsx` (`PanelistSeats` / `DefenderSeats`) with `QuestionCard.tsx` and `RoomDock.tsx`. The earlier 3D/Phaser room (`ThreeDefenseScene.tsx`, `PhaserScene.tsx`, `phaser/DefenseScene.ts`, `JudgePanelOverlay.tsx`, `judgeConfig.ts`) was removed on 2026-10-01 along with the `three` and `phaser` dependencies; it had not been imported by the app since the flat redesign, and neither library reached the production bundle. Do not reintroduce it, and do not describe the room as 3D. `main` still serves that older room, so the two branches genuinely differ; the flat room is the intended direction.

## Verifying a change

A change entry's Verification line must name the check that produced the evidence, and must say whether it was mocked or live. The offline gate is:

```bash
.venv/bin/python -m unittest discover -v
(cd game && npm test && npm run build)
```

Python tests need `.venv`; the React tests and build need Node.js and npm. AI calls in the Python tests are mocked, so a passing suite is not evidence of question quality — say "offline, AI mocked" rather than implying a live defense ran.

For layout review with no AI call, use the mock rooms: `http://127.0.0.1:8000/?preview=1`, adding `&research=1`, `&vote=1`, `&review=1`, `&clarify=1`, `&complete=1`, or `&long=1` as needed. A live defense, a hosted check, and a physical second device are three separate claims; never let evidence for one stand in for another.

Current status and deployed commits are recorded in `PROJECT_LOG.md`: see its **Current status** section for the present state and its **Changes** entries for history. Do not copy deployment status into this file; it goes stale and this file is read first.

Two things stay true regardless of the log's state:

- Rooms are in memory. A Render restart, redeploy, or Free-instance spin-down erases active rooms, so keep exactly one worker and one instance, and create a fresh room shortly before a demo.
- Do not mark visual review, hosted verification, or physical separate-device confirmation complete without evidence.


## Agent skills

### Issue tracker

For skill-driven planning or review, read [local Markdown tracker conventions](docs/agents/issue-tracker.md).

### Triage labels

For task status changes, use [local triage labels](docs/agents/triage-labels.md).

### Domain docs

For architecture exploration, follow [single-context domain guidance](docs/agents/domain.md).

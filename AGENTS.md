# Agent handoff rules

This project is a small FastAPI/Phaser multiplayer hackathon prototype with a Streamlit fallback. `README.md` explains how to run it. `PROJECT_LOG.md` is the shared handoff record for agents and separate session windows.

Before working:

1. Read `README.md` and `PROJECT_LOG.md`, then inspect the files relevant to your task. The code is the source of truth if the log is stale.
2. Check `PROJECT_LOG.md` for active work. If another session is changing the same files, coordinate before editing them.
3. For work that may overlap another session, add a short active-work entry with your session label, intended files, and start date.

After each logical change to project files:

1. Reread the end of `PROJECT_LOG.md` so you do not erase another session's entry.
2. Append a dated change entry: what changed, which files changed, what you verified, and what remains. Group related edits into one entry; do not log every keystroke.
3. Update the current-status and active-work sections when a checkpoint starts, finishes, or becomes blocked. Only remove your own active-work entry.
4. Report the same outcome to the user. The log does not replace a clear handoff in the conversation.

Never put API keys, secrets, full environment values, or uploaded private project text in the log. Keep entries factual; distinguish implemented work from mocked or live verification. Do not mark a checkpoint reviewed until the user has actually reviewed it.

The multiplayer 2D room is the current checkpoint. Keep the Streamlit fallback available. A live API walkthrough, hosted two-device check, and user review are pending. Do not add feedback or more panelists before that review.

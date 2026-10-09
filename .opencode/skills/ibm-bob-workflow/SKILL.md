---
name: ibm-bob-workflow
description: Use when working on the AI Defense Arena repo (IBM-BOB) — running or writing tests, verifying a change, planning feature tickets in .scratch, setting triage status, or updating PROJECT_LOG.md before handing work back.
---

# IBM-BOB workflow

`AGENTS.md` is the source of truth. Read it first, every session. This skill only
routes you to it; it does not restate its rules.

## Always

1. Read `AGENTS.md`, `README.md`, and the **Current status** section of
   `PROJECT_LOG.md` before editing anything.
2. Read root `CONTEXT.md` for domain or architecture exploration, plus relevant
   ADRs under `docs/adr/` if present. Use the glossary's terms (room, defense run,
   defense turn, grounded citation, clarification).
3. Work on `feature/question-first-room`. `main` is frozen for a review window —
   no merges, redeploys, or behavior changes there.
4. Never put API keys, secrets, environment values, or private project text in
   `PROJECT_LOG.md`.

## Verifying a change

Offline gate:

```bash
.venv/bin/python -m unittest discover -v
(cd game && npm test && npm run build)
```

Say "offline, AI mocked" when that is the evidence. A passing Python suite is not
evidence of question quality. A live defense, a hosted check, and a physical
second device are three separate claims — never let one stand in for another.

Layout review without an AI call: `http://127.0.0.1:8000/?preview=1` plus
`&research=1`, `&vote=1`, `&review=1`, `&clarify=1`, `&complete=1`, `&long=1`.

## Planning and review

- Tickets: [local Markdown tracker conventions](docs/agents/issue-tracker.md).
  New ticket sets live in `.scratch/<feature>/spec.md` and
  `.scratch/<feature>/issues/`, with a `Status:` line.
- Status values: [triage labels](docs/agents/triage-labels.md)
  (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`).
- Domain exploration: [single-context domain guidance](docs/agents/domain.md).

## Handoff

After each logical change, append one dated entry to `PROJECT_LOG.md`: what
changed, which files, what you verified and how (mocked or live), what remains.
Reread the end of the log first so another session's entry is not erased. Remove
your own active-work entry when done; annotate an expired one rather than
deleting it silently. Then report the same outcome in the conversation.

Do not mark visual review, hosted verification, or physical separate-device
confirmation complete without evidence.

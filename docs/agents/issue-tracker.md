# Issue tracker: Local Markdown

Specs and tasks are local Markdown, not automatically published to GitHub.
The current architecture spec is [ARCHITECTURE_PLAN.md](../ARCHITECTURE_PLAN.md).
Read a user-supplied spec directly; preserve its existing path rather than duplicating it.

For new ticket sets, use `.scratch/<feature>/spec.md` and numbered files under
`.scratch/<feature>/issues/`. Each ticket has a `Status:` line using the
[triage labels](triage-labels.md); append discussion under `## Comments`.
When a skill says publish or fetch a ticket, write or read those local files.

`PROJECT_LOG.md` remains the shared session and verification handoff, separate
from task specifications. Remote publication requires the user's request.

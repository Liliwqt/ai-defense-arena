# 04 — Voice probe replies and recovery across screens

**What to build:** Extend the working answer flow to same-question probe replies
and the app's navigation/reconnect/interpretation recovery, retaining explicit
manual submission and correct speaker/probe identity.

**Blocked by:** 03 — Live voice answers in Speaker desk.

**Status:** ready-for-human

## Acceptance criteria

- [x] Enable authorized voice for the current probe reply with independent attempt/probe identity, original-answer attribution and unchanged question number, reply length and deadline. Team chat and explicit clarification remain typed.
- [x] Preserve existing interpretation/direct-answer/probe recovery. Recognized clarification is not falsely recorded as a successful answer; saved/direct acceptance attaches provenance only to the matching server-finalized text.
- [x] A disconnect or navigation away stops capture without pausing time; a still-valid finalized unsent draft can be reviewed on return and submitted only by a fresh manual action. Obsolete/provisional material cannot be restored as an editable typed answer or auto-sent; refresh carries no new voice-draft durability promise.
- [x] Selection/probe/turn/run changes, recovery, timeout, restart and room closure invalidate outstanding finals. Reconnect never restarts the mic or replays Send, and repeated recovery events cannot replace an accepted original/probe answer.
- [x] Allowance is shared across original answers, probe replies, speakers and retries. Existing tab-scoped typed drafts, Back/refresh/task returns and input-mode changes do not reset usage or silently replace unrelated unsent work.
- [x] Two-client fake-audio tests cover probes, interpretation failure/retry/direct recovery, disconnection with selection change and navigation away/return. Responsive keyboard walkthroughs retain timer context, safe typing and correct accepted transcript attribution; complete checkpoint 2.

## Verification

Answer by voice, receive a probe, record a reply, interrupt/reconnect
and submit a valid finalized draft manually. Reject a delayed old-probe segment
after the turn advances. Show typing still works after the shared cap.

## Comments

- 2026-10-17 — User approved the ten-ticket breakdown as drafted; published locally with its agreed blocking edges and acceptance criteria. Specification stories: 35, 37, 48–54, 57, 61, 64, 79, 102–105.
- Parent: [research-defense practice specification](../spec.md). The parent remains the source of full scope, test boundaries and accepted ADRs; it is not changed by publication. Selected UI: B — Speaker desk, captured on prototype/research-practice (source f0d74a7, verdict a3046c4).
- Each ticket includes its own verification and leaves the app runnable. Record provider-mocked, actual speech, local database, native-build/device and hosted evidence separately. Ticket approval does not start implementation, authorize external-model sharing, push or deploy.

- 2026-10-18 — Implemented source daf9cd7; independent Standards 0 / Spec 0 against user-confirmed 0b9893b. Isolated 580 Python tests (AI/speech/Google/payments mocked), 373 React tests, production build and synthetic-audio Chromium desktop/portrait/landscape keyboard/navigation checks pass. [Review and screenshots](../reviews/04.md). Checkpoint 2 is implemented locally; user visual and actual provider/account/speech/hosted/native evidence remain pending, pilot default-off. No real recording/provider call, push/deploy or main change.

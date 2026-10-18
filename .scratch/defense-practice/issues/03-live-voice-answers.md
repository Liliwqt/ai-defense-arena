# 03 — Live voice answers in Speaker desk

**What to build:** In an operator-enabled research/mixed web pilot, the chosen
defender can explicitly start a mic, see recognized words read-only and Send a
finalized answer before the current deadline, with ten shared minutes/run and a
usable typing fallback.

**Blocked by:** None — can start immediately.

**Status:** ready-for-human

## Acceptance criteria

- [x] Implement selected B context/workspace layout and narrow-screen stacking/answer shortcut while retaining citations/PDF, seats, timer, chat and typed drafts. Starting voice must resolve rather than silently overwrite a typed draft; Switch to typing opens a fresh editable answer.
- [ ] Configure maintained OpenAI live speech independently from text AI, disabled unless explicitly enabled/configured. Before capture, show provider/retention disclosure and support limitations; revalidate model/protocol/account access. Standard keys stay server-only; no real audio/API call is necessary for offline verification.
- [x] Explicit capture authorizes only the online chosen defender in the current research/mixed answer window, with server-issued attempt scope. Other seats, stale runs/turns and code-only voice are rejected. Until 04, probe input remains typed. No page visit, vote, silence or reconnect starts capture.
- [x] A bounded server-controlled relay enforces current authorization, one active stream, finite frame/buffer/duration/attempt limits, actual forwarded-audio accounting and ten shared minutes/run. Deadline, cap, disconnect, selection/run change, leave/end/restart, navigation/page teardown and lost authorization stop forwarding and invalidate stale callbacks from the first usable release.
- [x] Show readable provisional versus finalized words in a read-only field. Manual Send, including keyboard submission, stops capture, finalizes ordered/deduplicated segment identities and uses the normal submission/acknowledgment path once. Finalization does not extend the deadline; silence/final events/cap do not submit.
- [x] Server validates final transcript/provenance and current attempt, nonempty/size limits and deadline; client claims cannot fabricate verified voice text or measures. Wrong/late/obsolete data never enters another question. Capture denial/provider failure/overflow/finalization failure gives truthful unsent/rejected status and typing recovery.
- [x] Forwarded retries/discards consume shared allowance; reconnect/refresh cannot reset it. At the cap stop new audio and finalize if possible without sending. Retain only submitted provenance and supported evidence, discard bounded audio buffers, and keep sensitive content out of logs/browser storage. Current price/voucher rules and code-only controls remain unchanged.
- [x] Authenticated fake-audio and whole-App/browser checks cover normal capture/send, forged actor/provenance, duplicate/out-of-order finals, cap/deadline races, no auto-send, no extra forwarding after revocation, typing recovery, readable grey words and desktop/phone keyboard use. Essential lifecycle safety is not deferred to 04.

## Verification

Two mocked clients select one defender, stream fake speech, manually
finalize/send and observe one normal accepted answer. Repeat with a nonselected
client, reached cap and deadline during finalization. Actual speech quality is
separate evidence and must not be claimed from this demo.

## Comments

- 2026-10-17 — User approved the ten-ticket breakdown as drafted; published locally with its agreed blocking edges and acceptance criteria. Specification stories: 27–34, 36–47, 49–52, 54–65, 103–105, 107.
- Parent: [research-defense practice specification](../spec.md). The parent remains the source of full scope, test boundaries and accepted ADRs; it is not changed by publication. Selected UI: B — Speaker desk, captured on prototype/research-practice (source f0d74a7, verdict a3046c4).
- Each ticket includes its own verification and leaves the app runnable. Record provider-mocked, actual speech, local database, native-build/device and hosted evidence separately. Ticket approval does not start implementation, authorize external-model sharing, push or deploy.

- 2026-10-18 — Local implementation through 5a86d49 passes 573 Python tests (AI/speech/Google/payments mocked), 370 React tests, production build and synthetic-audio Chromium desktop/phone checks. Independent Standards 0 / Spec 0 against user-confirmed 5489a87. [Review and preview](../reviews/03.md). Configuration/disclosure and mocked protocol checks are implemented; criterion 2 remains unchecked because actual account/model/transport validation is still required before enabling the default-off pilot. User visual acceptance remains pending. Probe voice is ticket 04; checkpoint 2 remains incomplete. No real audio/provider call, push/deploy or main change.

# Adaptive research panel — local implementation review

Implemented locally on `feature/question-first-room`; review baseline `c498598`.
Tickets 01–03 are implemented and independently reviewed locally. Complete checkpoint-2 review (04) remains pending; user visual review is not implied.

## What changed

The existing paper-mapping request now also suggests multiple fields and study approaches, an optional setting, a short grounded explanation and uncertainties. Profile references are resolved from accepted paper text; code-only evidence cannot establish a research profile, even in mixed rooms. Streamed topic drafts remain unconfirmed until the complete output passes validation.

React and Streamlit show the profile and exact paper citations. The host explicitly reviews it and acknowledges uncertainty before confirming the current profile/map/budget. Guests can inspect the same confirmed state. Legacy maps without a profile cannot start or reserve a run. The research session captures the immutable plan/profile, which reconnect restores without classification. Code-only dialogue and payment/timer rules retain their existing behavior.

## Ticket 01 verification (earlier)

- Working tree: 528 Python tests, AI/Google/PayMongo mocked; 273 React tests and production build passed. Separate pending reasoning/local-test work is included in that working-tree count.
- Selected ticket artifact: 520 Python tests (external providers mocked), 273 React tests and production build passed in an isolated extracted tree with its own frontend build. Its JS/CSS hashes match the working-tree build. This excludes the pending task-specific reasoning and quick-local-access implementation.
- Focused mocked tests cover invalid/missing/oversized profiles, paper-only profile references in mixed rooms, server-owned quotes, explicit confirmation, uncertain acknowledgment, host/guest authority, legacy-map rejection before reservation, frozen run context and reconnect. Streamlit AppTest covers ordinary and uncertain profiles plus existing long-defense/probe paths.
- Full offline protocol tests include code four/eight-turn and research/mixed twelve-question defenses, voting, clarification, timeout, saved-answer retry, reconnect, private PDF citations, transcript and coaching.
- Synthetic Chromium checks at desktop 1440×900, portrait 390×844 and landscape 844×390: readable profile, internal drawer scroll, no horizontal page overflow, 44-pixel checkbox labels and visible keyboard focus. Space, Tab and Enter confirmed the profile over the actual local WebSocket; Start enabled only after acknowledgment. These checks use a synthetic account, PDF and paced mapping, with no external AI/provider requests.
- Independent Standards and Spec reviews cleared ticket 01. One optional type-consistency suggestion was applied; stale Streamlit fixture labels were corrected and focused tests passed. Final review has zero remaining findings on either axis.

Live classification quality, actual Google/provider checks, installed Android/iOS verification and user visual review are separate pending evidence. This checkpoint does not publish or deploy.

## Preview

Open [the read-only profile preview](http://127.0.0.1:8845/?preview=1&plan=1).
For the interactive synthetic read/confirm path, open [the mapping fixture](http://127.0.0.1:8845/__fixture/login?case=mapping), choose Controls → Prepare defense, wait for the map, then review and acknowledge its profile before confirming. A synthetic opening question is not supplied by this fixture; use it for mapping/confirmation review only.

The preview is a separate loopback-only process with temporary storage and provider credentials removed. The user's normal server is unchanged.

- [Desktop suggested profile](../screenshots/adaptive-profile-desktop.png)
- [Portrait suggested profile](../screenshots/adaptive-profile-portrait.png)
- [Landscape confirmation controls](../screenshots/adaptive-profile-landscape.png)
- [Confirmed profile and exact PDF citation](../screenshots/adaptive-profile-confirmed.png)


## Checkpoint 1 correction/remapping verification

The host edits the practice fields, approaches or setting, then chooses **Apply profile and remap**. Unsaved edits disable Start and confirmation. The accepted description is saved separately from the paper-based suggestion, explanation and server-owned citations. It invalidates the old approval and requires a fresh map identity and renewed profile/budget confirmation. Retry reuses the saved description; guest viewing and reconnect retain the same state. Mapping and active-run edits are rejected, and an unchanged restart keeps the confirmed profile under existing cost/access rules.

Streamlit mirrors the flow. Accepted corrections invalidate its previous completed session/coaching scope; changing materials or stage clears saved descriptions. Approach choices derive from the shared backend type. Mapping remains one ordinary request, with no new evaluator/classifier or run charge.

- Full working-tree gate: `python -m unittest discover -v` using `.venv` passed **534 tests**, AI/Google/PayMongo mocked; **275 React tests** and production build passed. The working tree includes separate pending reasoning/local-access work. Final focused AppTest also verifies completed-session/coaching invalidation without modifying the detached old answer, and material-change clearing.
- Exact selected checkpoint: isolated Python unittest discovery passed **526 tests** with external providers mocked, plus **275 React tests** and production build. The selected JS/CSS bytes match the working-tree build. This excludes prior reasoning/local-access code.
- Normal authenticated HTTP/WebSocket tests exercise invalid corrections, guest authority, revoked access without scope loss, duplicate preparation, pending edits, late progress/results after restart, saved-description failure/retry/reconnect, stale map approval, active-run accepted-answer preservation and unchanged restart. The full gate retains mocked code four/eight-turn and research/mixed twelve-question flows with voting, clarification, timeouts, retries, reconnect, transcript/coaching and financial regressions.
- Synthetic Chromium at 1440×900, 390×844 and 844×390 showed readable host/source descriptions, internal Controls scrolling, no horizontal page overflow and 44-pixel approach labels. An actual local WebSocket demo confirmed the original map, edited fields/approaches, blocked unsaved Start, failed the second synthetic map, retained inputs, retried with those inputs and required fresh confirmation. Space/Tab/Enter with a visible focus ring confirmed the updated scope and enabled Start. Reload restored the host description and approval.
- Independent Standards and Spec reviews against **c498598** cleared tickets 01–02. Applied the optional shared-vocabulary suggestion; reviewers verified the final code delta. **0 Standards findings / 0 Spec findings remain.**

These are offline/mocked and synthetic browser checks. Live classification/dialogue quality, actual Google/payment providers, hosted behavior, installed devices and user visual review remain separate pending evidence. No push or deployment; frozen main and hosted service are unchanged.

## Checkpoint 1 preview

Open [the read-only profile layout](http://127.0.0.1:8845/?preview=1&plan=1).
For a fresh interactive demo, use [the correction/failure/retry fixture](http://127.0.0.1:8845/__fixture/login?case=corrections): Controls → Prepare defense, review the profile, edit its fields or approaches, then Apply profile and remap. The second preparation intentionally fails; Retry research map retains your saved input. The third map requires fresh confirmation. Ordinary mapping limits remain in effect; this demo does not generate a defense question.

The preview uses a separate loopback-only server, disposable storage, synthetic Google identity and synthetic PDFs; external provider keys are removed. It does not restart the user's normal server or measure real AI quality/latency.

- [Desktop unsaved correction](../screenshots/adaptive-profile-correction-desktop.png)
- [Saved input after synthetic mapping failure](../screenshots/adaptive-profile-correction-failure.png)
- [Portrait host description and paper-based suggestion](../screenshots/adaptive-profile-correction-portrait.png)
- [Landscape correction controls](../screenshots/adaptive-profile-correction-landscape.png)


## Ticket 03 — consistent subject-aware conversations

A shared research-panel boundary supplies topic-sensitive role guidance and profile serialization to the existing mapping, question, interpretation and coaching requests. Research and mixed submission interpretation captures detached scope and the current topic while holding the room lock. Streamlit forwards the same session context. Code-only requests remain unchanged; no classifier, evaluator, additional dialogue call, AI schema, timer, budget or financial rule was added.

Methodology covers empirical, qualitative, theoretical and computational/design reasoning where relevant. Ethics does not assume human participants; Impact includes contributions to knowledge; Critical considers topic-specific theory, evidence and alternatives. Multiple approach labels do not establish mixed-methods design. Confirmed uncertainty and material host/source discrepancies invite grounded inquiry rather than invented methods or findings. Existing role voices, natural reactions, occasional scenarios, conditional advice, language continuity and same-question reply rules remain in force. Prompt instructions are not evidence of live answer quality.

- Full working-tree gate: `.venv/bin/python -m unittest discover -v` passed **538 Python tests**, AI/Google/PayMongo mocked; `game` **275 React tests** and production build passed. Separate pending reasoning/local-access work accounts for eight additional Python tests.
- Exact selected runtime/test artifact: isolated `.venv` unittest discovery passed **530 Python tests** with external providers mocked. The frontend source and lockfile are unchanged from the independently built checkpoint 1; its current React tests/build also pass.
- Four new mocked test methods cover request contracts and qualitative, quantitative, theoretical, computational/design, unclear and interdisciplinary research/mixed contexts across proposal/completed/inferred stages. A two-client HTTP/WebSocket flow carries one fixed profile through clarification, an accepted answer, a same-question probe/reply, the next reaction/question, transcript and coaching, excluding private chat/account context. Streamlit AppTest mirrors that flow. Forty-eight existing conversation/clarification/probe tests passed separately.
- A one-off provider-mocked comparison against **6737586** confirmed exact equality of seven code-only request payloads and response schemas: four role openings, next question, submission interpretation and coaching.
- Independent Standards and Spec reviews of the isolated candidate against **c498598** report **0 actionable findings on either axis** for tickets 01–03. Reviewers performed static/read-only checks; the parent ran the suites above.

Ticket 03 is ready-for-human. Ticket 04 remains pending for complete integrated defenses, responsive handoff and separate live conversation-quality evidence. No new UI screenshots or live/provider checks are claimed for this dialogue-only change; the checkpoint-1 screenshots above show profile controls, not generated conversation quality. No push or deployment; frozen main, the hosted service and unrelated pending files remain unchanged.

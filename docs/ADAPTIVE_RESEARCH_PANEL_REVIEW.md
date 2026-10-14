# Adaptive research panel — local implementation review

Implemented locally on `feature/question-first-room`; review baseline `c498598`.
Tickets 01–03 and ticket 04's offline integration/responsive review are complete locally and independently code-reviewed. Separate live empirical, theoretical and mixed samples are now recorded; two resulting prompt refinements await a post-restart live check. User visual/native-language review and publication readiness remain pending.

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


## Ticket 04 — integrated local review

The offline implementation and responsive review are complete. Live conversation quality, user visual approval and publication readiness remain pending. The two checkpoints are locally runnable; no push or deployment was performed.

### Integrated defense evidence

Two new authenticated HTTP/WebSocket checks complete **twelve-question Research paper and Research + code defenses**. Each prepares an unclear source-grounded profile, saves a conflicting host description, experiences a synthetic remapping failure, retries with the saved description, rejects stale/guest/unacknowledged approval, and confirms the fresh scope before starting. A timeout leaves its topic unresolved; a clarification stays on the same question; a probe retains the original answer and accepts a reply. A synthetic invalid next-question citation exercises automatic retry without duplicating the answer or turn. Reconnection during the probe and after completion restores the same profile, transcript and coverage without another generation. Every published paper/code excerpt is checked against the original synthetic source. Both defenses stop at twelve questions, preserve outstanding topic 12 and report budget exhaustion in coaching.

These are provider-mocked runs, not live conversations. Each records three map attempts, fourteen next-move attempts (including the final assessment and one retry), and one coaching request. The same fixed profile reaches generation, submission interpretation and coaching; private chat and account data do not. Existing full-suite checks retain stale-result fences, failed map recovery, legacy-map guidance, unchanged code-only flows and once-only paid-run charging/recovery.

- Full working tree: `.venv/bin/python -m unittest discover -v` passed **540 Python tests** (AI/Google/PayMongo mocked); `game` `npm test` passed **275 React tests**; `npm run build` passed. The existing large PDF chunk warning remains; no dependency change is part of this ticket.
- Isolated selected artifact: absolute `.venv` Python unittest discovery passed **532 mocked Python tests**, excluding the eight pending reasoning/local-access tests. Runtime/frontend source is unchanged by ticket 04; the current frontend gate above uses the already committed feature source.
- Independent parallel Standards and Spec reviews of the full feature against **c498598** report **0 actionable findings on either axis**. Reviewers used static/read-only evidence; the parent ran the tests and browser checks.

### Responsive and keyboard evidence

Actual local Chromium checked desktop **1440×900**, portrait **390×844** and landscape **844×390**. Eighteen synthetic conversation views covered long answers/questions, clarification, same-question probes, voting, submission recovery and completion. All retained the header, both seat strips and answer dock in the viewport without horizontal page overflow. Long question/reply content scrolls internally; timer labels accurately represent the supplied Answer, Reply, Vote and Paused fixtures.

A separate synthetic-account/PDF fixture exercised real local WebSocket mapping, profile correction, deliberately failed remapping, saved-input retry and renewed confirmation. Keyboard Space toggled both acknowledgments with a visible 3-pixel focus outline; Enter confirmed the profile/budget and enabled Start. Reload restored the host/source descriptions and confirmation. Controls scroll internally on both phone orientations. An actual rendered synthetic PDF displayed the exact page-2 quotation and one visible citation highlight. Arrow keys switched the phone Question/Paper tabs while the timer, seats and dock stayed visible. These are synthetic local browser checks, not hosted, installed-device or live-AI evidence.

### Local preview and screenshots

The review server binds only to loopback on **8846**, removes provider credentials and uses disposable accounts, voucher and document storage. The user's normal server is unchanged. The links work while this review process remains running.

- [Interactive correction/failure/retry review](http://127.0.0.1:8846/__fixture/login?case=corrections): Controls → Prepare defense; edit the profile; Apply profile and remap. The second mapping intentionally fails. Retry preserves the description; acknowledge the profile and uncertainty and confirm the fresh budget. This fixture does not generate a defense question.
- [Real synthetic PDF with a long question](http://127.0.0.1:8846/__fixture/login?case=long): close Controls, use Question/Paper on phones and browse the cited page. The prebuilt question and fixed server clock are for layout review only.
- [Question 11 with coverage](http://127.0.0.1:8846/?preview=1&research=1&coverage=1), [same-question reply](http://127.0.0.1:8846/?preview=1&research=1&probe=1), and [clarification](http://127.0.0.1:8846/?preview=1&research=1&clarify=1) are display-only fixtures.

| Capture | Evidence |
| --- | --- |
| [Desktop confirmed profile](../screenshots/adaptive-panel-review-desktop.png) | Separate host/source provenance and exact PDF reference |
| [Portrait profile](../screenshots/adaptive-panel-review-portrait.png) | Readable source explanation in scrolling Controls |
| [Landscape profile](../screenshots/adaptive-panel-review-landscape.png) | Bounded drawer with internal scrolling |
| [Desktop question and paper](../screenshots/adaptive-panel-question-desktop.png) | Long question with actual cited PDF page |
| [Portrait question](../screenshots/adaptive-panel-question-portrait.png) | Visible timer, seats and answer dock |
| [Portrait paper highlight](../screenshots/adaptive-panel-paper-portrait.png) | Complete page browsing and visible verified highlight |
| [Landscape panelist reply](../screenshots/adaptive-panel-reply-landscape.png) | Same-question reply labels and scrolling content |

### Separate live evidence

The original offline handoff did not make real AI, Google or PayMongo requests. The user subsequently configured a local server on port 8001, and three live AI samples were inspected. See [the live review](ADAPTIVE_RESEARCH_PANEL_LIVE_REVIEW.md) for synthetic sources, actual generated transcripts, safe mapping recovery and two discovered wording issues. Those issues led to research-only prompt refinements whose post-restart live check remains pending. Samples do not certify specialist accuracy or native-language quality. User review, hosted behavior and installed Android/iOS checks remain separate; no publication readiness is implied.

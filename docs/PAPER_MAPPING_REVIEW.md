# Live paper-mapping review

Local checkpoint on `feature/question-first-room`, 2026-10-13. Publication and deployment are not requested; frozen main stays unchanged.

## Behavior

The multiplayer preparation request streams structured output from the existing configured model. Completed topic objects are validated against role, text, count and server-owned source-reference rules before appearing as **Draft** cards. Each shows a title, reviewer, objective and expandable exact source excerpts. No partial JSON, private reasoning, invented page-reading narration, percentage or time estimate is exposed.

Stages reflect actual boundaries: accepted documents are prepared, topic output is received, then the complete response is validated. The final map must agree with the streamed topics and pass all existing map checks before becoming ready. Draft cards do not constitute approval or evidence that the research interpretation is correct. The existing one-request policy, AI attempt limits, budget confirmation, timers and charging are retained. Streamlit uses the existing non-streaming preparation path.

Progress is immutable snapshot data, fenced by the coordinator's run/generation/lobby identity. Both clients see the same prefix, reconnect restores it without another AI call, and failure/retry/cancel clears obsolete drafts. Start defense is absent before/during failed or unfinished research mapping. It appears after a ready map and remains disabled until budget confirmation and the existing account/connection checks pass. Code-only Start behavior is unchanged.

SDK implementation follows [official structured-output streaming guidance](https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=responses). The installed Python SDK was inspected for `responses.stream`, output-text deltas and `get_final_response`. One bounded incremental decoder reads complete topic objects; the SDK still parses and validates the final response.

## Verification

- Full offline Python gate: 512 tests pass in 62.443 seconds, AI/Google/PayMongo mocked, private document storage isolated in a disposable directory. The first full run found callback identity being included in request equality; corrected by excluding that transport callback from value comparison. A preliminary transport invocation used already-owned default paper storage; the final transport fixture owns a private directory.
- React: 271 tests pass; production build passes with the existing lazy PDF.js chunk-size warning. Tests cover draft/reference display, validating/failure transitions, hidden Start before readiness and required budget confirmation. Existing code/research defenses and deadline/payment/retry suites run in the full gates.
- Seven new backend tests cover token-sized partial/escaped JSON, bounded decoding, one-request streaming with ignored reasoning events, invalid citations, final-response disagreement, unresolved map validation, two-client publication/reconnect, premature Start rejection, stale progress and fresh retry.
- Actual Chromium layout checks with synthetic fixtures: 1440x900 desktop, 390x844 portrait and 844x390 landscape have no horizontal body overflow; the question card scrolls internally. Progress and draft cards also appear in Controls. Reduced-motion behavior was verified separately in the preceding progress-bar checkpoint.
- Actual two-browser local transport walkthrough, AI mocked: desktop host and isolated portrait guest received drafts while mapping was unfinished; guest reload restored the same current draft. Both reached ready. Host Start was absent before and during mapping, visible but disabled after ready, and enabled only after server-acknowledged budget confirmation. No defense was started or charged in this walkthrough.

## Local review

Open <http://127.0.0.1:8842/__fixture/login?case=mapping>, then choose **Prepare defense** in Controls. The loopback fixture uses synthetic identity, temporary storage and deliberately paced mock topic events; it does not measure AI speed or quality. Invite a second browser with the shown room code to see synchronization. After mapping finishes, confirm the question budget to enable Start. Do not start a real defense from this provider-free demo.

For a stable three-topic layout preview use <http://127.0.0.1:8842/?preview=1&plan=1&planstatus=planning>.

| Capture | Evidence |
| --- | --- |
| [Desktop feed](review/paper-mapping/desktop.png) | Server-delivered first draft during the mocked two-client walkthrough |
| [Portrait feed](review/paper-mapping/portrait.png) | Independent guest after reload, still receiving draft progress |
| [Ready Controls](review/paper-mapping/ready-controls.png) | Final map and budget confirmation with Start available |

Live OpenAI streaming/quality, hosted behavior, physical separate-device and installed Android/iOS checks remain unverified. User visual approval remains pending.

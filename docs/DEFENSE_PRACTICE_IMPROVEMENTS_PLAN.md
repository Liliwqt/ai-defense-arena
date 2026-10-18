# Research defense practice: consolidated plan

Date: 2026-10-17. Status: planning complete; the user confirmed Q1–Q20 and the consolidated scope in Q21 on 2026-10-17.
Branch: feature/question-first-room. Design/specification only; the reviewed prototype is isolated on prototype/research-practice. No production implementation, push or deployment.

## Purpose and supported modes

Prepare defenders to explain research clearly across different fields. Questions, answer examples and coaching use the existing host-confirmed research profile, study approach, stage, setting and uploaded evidence. Keep the four established reviewer perspectives; do not invent examiner credentials, institutional requirements or one universal experimental/statistical method.

- **Research paper** becomes the default for fresh setup.
- **Research + code** remains available for studies with software and receives the same research-first improvements.
- **Code project · Experimental** remains available with its current flow; new live voice and detailed delivery coaching do not apply to code-only defenses. Preserve explicit/restored code selections and existing code behavior.
- Shared web/Android/iOS research/mixed defenses receive live voice and expanded coaching. Streamlit shares richer research text coaching and research-first labels/defaults while retaining typed input.

## Before, during and after

Before starting, show a short general guide: answer directly, explain the reason, support it with evidence, and acknowledge a relevant limitation. Recommend the microphone for rehearsing spoken explanation while retaining typing. Do not reveal a suggested answer to an upcoming question.

During a defense, only the selected defender can use voice for an answer or same-question probe reply. Words appear live in a readable grey-styled, read-only field. Distinguish provisional recognition from finalized words. Team chat and clarification requests remain typed; explicit clarification controls must keep existing same-question behavior.

Afterward, generate a team overview and an expandable card for every question/answer, including probe exchanges where relevant. Cards retain the original submitted words and actual speaker, explain strengths/gaps, suggest stronger supported wording, offer a practice task, and show available delivery evidence. Unanswered turns receive factual notes and a scaffold/practice task rather than invented answers or strengths. AI suggestions never replace the original answer, change coverage, or count as team performance.

## Fresh openings for the same paper

Retain the latest five committed opening questions for one host and the same accepted paper content for30days. History is private to the host and survives fresh rooms, repeated runs and service restarts; it does not persist the room itself. Identify paper content rather than filename, so renaming the same material shares history; changed accepted paper content starts fresh context. Keep full papers, recordings and answer transcripts out of this history store.

Use the existing research opening reviewer and eligible mapped topics. Include recent openings in the existing question request to seek a different grounded angle. Reject exact/normalized duplicate candidates deterministically; recent questions/topics also guide semantic variation. A prompt or lexical check alone is not proof that every paraphrase explores a different idea.

On a recent duplicate, allow one bounded regeneration within existing admission limits. If still repetitive, explain the limitation and let the host retry or explicitly accept a validated repeated candidate. Do not present a rejected candidate as the active team question or charge for it. A host acceptance must still match the current room/run/map/generation and pass source validation.

Write history idempotently at the authoritative opening commit, with once-only financial behavior. Stale/failed/rejected proposals do not become asked questions. If required history lookup/write cannot be completed, expose recoverable preparation failure before committing/charging the opening, rather than falsely claiming prior history was checked. A retry must not duplicate a committed opening or charge. Enforce expiry/caps in the server store.

Decision record: [bounded opening history](adr/0006-bounded-opening-question-history.md).

## Live voice controls and recovery

- **Start mic** is explicit and discloses live transcription. Never begin capture when merely visiting a page or selecting a speaker.
- **Send** stops capture, finalizes the last segment, then submits the finalized text once. Show **Finishing transcript…** while waiting. Silence, transcript-final events and a reached voice cap never submit automatically.
- Current answer/reply deadlines and text-size limits remain authoritative. Finalization does not pause or extend the timer. If the deadline passes first, reject late submission and clearly report the outcome; late speech must not enter the next question.
- Provide **Discard and record again** and **Switch to typing**, which clears the voice draft and opens a fresh typed answer. Recognized voice text remains uneditable. Preserve the existing typed-draft navigation/recovery contract and avoid silently replacing unrelated unsent work.
- Stop/revoke capture and invalidate callbacks on turn/run/probe/selection changes, leave/end/restart, lost authorization, disconnection or page teardown. Scope every event so another speaker's or previous question's late transcript cannot populate the current answer. Reconnect does not replay Send or automatically restart the mic.
- Keep finalized unsent text visibly separate from accepted answers. Only the normal validated submission/acknowledgment path records an answer. Raw capture and provisional recognition are not accepted answers or coaching strengths.

## Shared allowance, provider and privacy

Use an operator-enabled tester pilot with **10 voice minutes per defense run**, shared across defenders, with visible remaining time. Keep the current10credit defense price and voucher rules; no extra user charge. The app covers added provider costs. Forwarded audio from retries/discarded recordings still consumes this allowance; refresh/reconnect does not reset it. Retain only measurements associated with the actually submitted voice material for coaching.

At exhaustion, stop further audio forwarding, finalize what is available without auto-sending, explain the cap and keep typing available. Enforce duration, concurrent streams, attempts, payload sizes, deadlines and owner/server limits independently on the server. Provider failure, unavailable configuration or denied mic access must offer a clear typed path rather than block an otherwise valid typed defense. Once-only charge/return rules stay intact.

Start with a maintained **OpenAI live-transcription** model, configured separately from the question/coaching AI. The verified candidate is gpt-live-transcribe; do not make a deprecated model the default. Use a server-controlled relay/lifecycle boundary to enforce room/run/turn/probe/selected-defender authorization and stop forwarding at deadlines/allowance limits. Standard API keys stay server-only. Browser ephemeral-token expiry alone is not a sufficient time/spending boundary.

There is no application audio archive. Process bounded audio buffers, compute supported measurements, then discard the application's audio copy. Keep submitted transcript and available measurements with current in-memory room/results; do not imply restart durability for those results. Clear obsolete/unsubmitted capture on discard/leave/expiry. Voice allowance accounting is separate from delivery measurements and the credit wallet.

Disclose the selected provider's separate retention before capture: the checked OpenAI Realtime policy lists30day abuse-monitoring retention and no application-state retention. App deletion is not a promise of provider deletion. No personal recording or API key was used during planning.

## Languages and truthful feedback

Voice launches **English-first**. Include Tagalog and modern Bisaya individually only where the selected service supports them and representative checks pass, including natural code-switching. Preserve what was said without forced translation. Existing typed-language preferences remain; unsupported/unreliable voice recognition gets a clear explanation and typing fallback rather than a poor-delivery judgment.

Coaching covers wording, organization, relevance, reasoning and evidence. It also addresses observed fillers such as uhm, repetition and ways to keep a clear structure, using the defender's language preference. Quote captured examples and show a clearer supported formulation; do not invent study decisions, safeguards, results or evidence. Label missing facts or conditional scaffolds explicitly.

Voice cards can include approximate speaking rate and pause observations only where reliable recording-derived measurements exist. Distinguish transcript observations, computed measurements and AI suggestions; explain unavailable evidence. A cleaned transcript may omit fillers, so absent tokens do not prove filler-free speech. Do not count normal Bisaya/Tagalog usage as filler without contextual evidence, grade accents, infer psychological confidence, or claim transcript-only pronunciation/tone assessment.

## Progressive coaching, closing and completion

Generate the overview and every required per-question card automatically in bounded, sequential/admitted batches, with visible progress. This is application request grouping, not a claim of discounted provider Batch API pricing. Preserve successful sections and retry only failed sections under bounded admission, without another defense charge or duplicating accepted work.

Once the overview is ready, show the existing optional closing once, then open Results with ready cards and progress for outstanding cards. Empty/invalid optional closing is skipped without discarding valid coaching. Reconnect resumes the current closing/progress, and section retry never replays closing. Account/payment tasks remain uninterrupted by room transitions.

The full report and run remain incomplete until the overview and every required coaching section are valid. Visible partial Results do not financially settle the run. A required error retains successful sections, free retry and the existing eligible end-unavailable credit-return path. Free/voucher runs cannot receive credits they were never charged. Late completion must be fenced after recovery, restart or run replacement so it cannot reverse a return, settle twice or overwrite a newer report.

Transcript/export retains original answers, speaker/probe attribution, accepted voice/text provenance, available measurements, completed coaching and a truthful partial/failed status. No audio download/archive is introduced. Room loss/expiry remains explicit; opening history is the only new persistent practice-history capability in this scope.

Decision record: [progressive coaching and settlement](adr/0007-progressive-coaching-before-settlement.md).

## Native work and existing boundaries

Include Android microphone declaration/runtime permission and trusted-origin WebView capture handling, plus iOS microphone usage/capture integration and necessary build changes. Request only audio capture for the trusted application origin; preserve exact sign-in/payment trust allowlists and keep external pages from receiving microphone access. Denied/revoked permission, app backgrounding and lifecycle teardown stop capture and provide honest recovery.

New installed builds and actual permission/recording checks are required. Responsive web evidence cannot establish Android/iOS microphone support; a Linux source check cannot establish an iOS build or device result. Unsupported/older native builds keep typed use available.

Retain the current four research reviewers, confirmed profile rules, citations, question budgets/coverage, speaker voting, answer/reply lengths, account access, payment verification and financial policy except the explicitly expanded required-coaching readiness above. Keep coordination and stale-work fencing inside existing room ownership; do not refactor unrelated auth/payment/document extraction or alter AI research claims as part of this feature.

## Local delivery and verification

First review a clearly marked, isolated local prototype of the mic/read-only transcript/finalizing-Send flow and expandable coaching cards. Use simulated recognition and report progression so this UI review does not need an API key, real microphone upload or paid provider call. Retain the existing visual identity and provide desktop/portrait/landscape walkthroughs.

Then implement four runnable local checkpoints:

1. **Opening history:** content-based private bounded history, duplicate handling/host acceptance and research-first/default/Experimental presentation. Existing code flow remains runnable.
2. **Live web voice:** authorized bounded streaming, read-only drafts, explicit finalizing Send, shared allowance, recovery and supported measurements; native clients can still type.
3. **Complete per-answer coaching:** stronger supported formulations, measured/observed evidence, admitted batches, progressive Results/closing, export and eligible financial recovery; shared Streamlit research text coaching.
4. **Native and integration:** Android/iOS microphone source/build work, lifecycle/trust handling and complete supported-surface/regression review.

Required local evidence: full Python/React suites and production build; real local database history/migration/concurrency/restart checks; authenticated two-client research/mixed room flows with AI/payment/speech mocked, controlled clock and fake audio; duplicate/stale/cap/finalization/deadline/reconnect/probe/retry/partial-coaching/settlement/return checks; code-only compatibility and Streamlit contracts; desktop/portrait/landscape keyboard/accessibility layouts.

Separate evidence before claiming readiness: actual English recognition and filler/measurement quality, supported Tagalog/Bisaya/code-switch quality, provider access/usage/retention verification, hosted transport and actual installed Android/iOS capture/permission/background/reconnect. Record unavailable toolchains/devices/checks as pending rather than passed. Present local previews before publication. User confirmation of the plan does not authorize a push/deployment or imply these checks already ran.

## Confirmed interview choices

| Decision | Confirmed choice |
| --- | --- |
| Q1 | Brief guide before; personalized coaching after. |
| Q2 | Recorded speaking practice included now. |
| Q3 | Five host/paper openings for30days across rooms/restarts. |
| Q4 | Live read-only transcript during defense; manual Send; recommend voice for practice. |
| Q5 | Detailed coaching for every answer. |
| Q6 | Temporary app audio; retain submitted transcript and available measurements. |
| Q7 | Voice for selected defender answers/probe replies; typed chat/clarification and typed fallback. |
| Q8 | Rerecord or switch to fresh typing; timer continues. |
| Q9 | Automatic batches, overview, expandable cards, progress and failed-section retry. |
| Q10 | Send stops, finalizes, submits once; unchanged deadline. |
| Q11 | Evidence-based text/delivery feedback plus captured fillers and answer structure. |
| Q12 | Native microphone changes in this release, with separate build/device evidence. |
| Q13 | English first; include supported/tested Tagalog and modern Bisaya. |
| Q14 revised | Research paper default; mixed available; code Experimental/current flow; Streamlit research text coaching only. |
| Q15 | Ten shared voice minutes/run; current10credit/voucher rules; app covers added cost. |
| Q16 | Partial cards preserved, free failed-section retry, existing eligible credit-return recovery. |
| Q17 | One duplicate regeneration, then host retry/accept; content-based identity; no rejected-draft charge. |
| Q18 | Maintained OpenAI live transcription for pilot, separate from text AI. |
| Q19 | Closing once after overview, then progressive Results; settle only after required coaching is ready. |
| Q20 | Local prototype, four checkpoints and agreed local/separate-live checks. |

## Checked implementation and primary-source facts

Current backend uses only the current run's answered history. Opening reviewer order is fixed, but the model selects among eligible assigned topics in map order; it is not hardcoded to map topic zero. Existing coaching is one shared report with turn-linked strengths/improvements, next step and optional closing. Existing room state is in memory, selected-speaker submission/acknowledgment is bounded, and current Android/iOS shells have no microphone setup. Relevant seams: backend/defense_session.py, defense_progression.py, rooms/questions.py, rooms/coaching.py; game/src/components/AnswerComposer.tsx and CoachingReport.tsx; mobile Android manifest/activity and iOS Info.plist/controller. These are source facts, not live question-quality evidence.

Browser microphone capture needs HTTPS/localhost and permission; recorder formats require feature detection. Native browser SpeechRecognition is limited-availability and may use a separate vendor service, so it does not establish universal WebView or Bisaya support. [Capture](https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia), [recording formats](https://developer.mozilla.org/en-US/docs/Web/API/MediaRecorder/isTypeSupported_static), [SpeechRecognition](https://developer.mozilla.org/en-US/docs/Web/API/SpeechRecognition).

Official live guidance distinguishes partial delta and final item events; final items may complete out of order, so reconcile by identity. The checked live model needs explicit commits rather than relying on server VAD. Completed-file transcription alone cannot satisfy live captions, and file prompting about fillers does not establish complete live disfluency capture. [Realtime transcription](https://developers.openai.com/api/docs/guides/realtime-transcription), [file-transcription prompting](https://developers.openai.com/api/docs/guides/speech-to-text#prompting).

Current provider client-secret rules allow multiple sessions before expiry and sessions that outlive it; TTL is not a hard room/deadline/spend bound. Standard keys stay server-only and the application needs independently enforced lifecycle controls. App audio deletion and endpoint retention differ; do not apply file-transcription retention rules to Realtime. [WebRTC authentication](https://developers.openai.com/api/docs/guides/voice-webrtc?voice-api=realtime), [secret constraints](https://developers.openai.com/api/reference/resources/realtime/subresources/client_secrets/methods/create), [endpoint retention](https://developers.openai.com/api/docs/guides/your-data).

As checked on2026-10-17, gpt-live-transcribe is USD0.017/minute of realtime audio duration:10minutes is USD0.17 before text coaching, question/mapping calls and hosting. Rounding/silence/account access/actual use are unverified; this is not a complete price estimate. A cheaper supported candidate was investigated but is deprecated for shutdown2027-02-26 and was not selected as default. [Model pricing](https://developers.openai.com/api/docs/models/gpt-live-transcribe), [pricing table](https://developers.openai.com/api/docs/pricing), [deprecations](https://developers.openai.com/api/docs/deprecations#2026-08-26-transcription-models). Language/recognition quality requires representative evaluation, not an inferred guarantee. [Transcription testing](https://developers.openai.com/api/docs/guides/transcription).

## Next step

The local prototype is complete and the user selected **B — Speaker desk** on 2026-10-17: question/research context beside the speaking workspace, stacked on phones, with a question selector and focused coaching detail. See [the prototype review](DEFENSE_PRACTICE_PROTOTYPE_REVIEW.md); source f0d74a7 and verdict a3046c4 are on prototype/research-practice. The [local implementation specification](../.scratch/defense-practice/spec.md) is ready-for-agent, with 108 user stories and user-confirmed test boundaries. Next is To Tickets, followed by the four agreed implementation checkpoints. Layout/specification confirmation does not authorize implementation or publication; prototype speech, coaching and financial recovery remain synthetic.

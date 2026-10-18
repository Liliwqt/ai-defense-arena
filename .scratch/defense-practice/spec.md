# Research defense practice: varied openings, live voice and answer-delivery coaching

Status: ready-for-agent

Date: 2026-10-17. The user confirmed the complete research-practice plan in Q21,
selected prototype **B — Speaker desk**, and confirmed this specification's test
boundaries. This is a local specification in the project's Markdown issue tracker.
Implementation tickets, production implementation and publication are separate.

## Problem Statement

Defenders want to prepare for a real research defense by explaining their own
work clearly. Repeated defenses of the same paper can begin with the same
question because a new defense run does not remember earlier openings. That
encourages memorizing one answer instead of rehearsing different supported angles.

The existing typed-answer flow and shared coaching report provide useful
discussion practice, but they do not offer live speaking practice or detailed
delivery guidance for every answer. Defenders want to see what they said, learn
where wording or structure obscured their reasoning, and practice a stronger
explanation without having the AI invent research decisions or results.

This should work across research fields. A theoretical paper, interview study and
software-supported research study must not all be treated as statistical
experiments. Voice should help practice, while typing remains usable when a mic,
speech service, supported language or device is unavailable.

## Solution

Make Research paper the default, retain Research + code, and label code-only
practice Experimental while keeping its existing defense flow. Before starting,
offer a brief guide: answer directly, explain why, support the explanation with
evidence, and acknowledge a relevant limitation. Recommend voice for spoken
practice without requiring it or revealing answers to upcoming questions.

For research and mixed defenses, remember five recent opening questions per host
and accepted paper content for 30 days. Seek another grounded angle using the
existing opening reviewer and eligible topics. When a recent duplicate persists
after one bounded regeneration, let the host retry or explicitly accept a
validated repeated opening. A rejected draft never becomes the active question
or incurs a run charge.

Use the selected **Speaker desk** layout: research/question context beside a
dedicated speaking workspace on desktop, stacked on phones. The chosen defender
can start a microphone explicitly for an answer or answer-probe reply. Recognized
words appear read-only; Send stops capture, finishes the transcript and submits
through the normal server-validated answer flow. The answer deadline continues.
Typing, rerecording and clear failure recovery remain available. A tester pilot
provides ten shared voice minutes per defense run at the current defense price.

After the defense, show a team overview and optional closing once, then open
Results with progressive coaching for every recorded turn. A question selector
opens focused details with expandable sections for original answers, probe
exchanges, supported improvements, stronger wording and a practice task. Use
captured filler examples and reliable delivery measurements where available.
Keep completed cards when another section fails, allow free bounded retry of
failed work, and retain eligible end-unavailable credit-return recovery. Partial
Results are visibly incomplete and do not financially complete the defense run.

## User Stories

### Preparation and research scope

1. As a host, I want fresh setup to default to Research paper, so that the app starts with its principal practice use case.
2. As a host, I want Research + code to remain available, so that a study with software can receive research-focused practice.
3. As a host, I want Code project labeled Experimental while preserving its current behavior, so that its maturity and scope are clear.
4. As a returning host, I want explicit or restored mode selections preserved, so that a new default does not silently change my work.
5. As a researcher, I want questions and coaching to use the confirmed research profile, stage, setting and paper, so that practice fits my field and approach.
6. As a researcher, I want host descriptions distinguished from source evidence, so that a selected profile cannot manufacture facts about my study.
7. As a defender, I want a short general answer guide before starting, so that I can organize an explanation without seeing answers to future questions.
8. As a defender, I want voice recommended and typing retained, so that I can choose a usable practice method.
9. As a defender, I want the existing preparation, profile confirmation and Start workflow retained, so that the speaking feature does not bypass readiness requirements.
10. As a researcher in a nonexperimental field, I want method-appropriate advice, so that I am not told to invent participants, statistical tests or results my work does not require.

### Fresh opening questions

11. As a host repeating a paper, I want recent openings considered, so that a fresh defense can explore another grounded angle.
12. As a host, I want the latest five openings retained for 30 days, so that practice varies without building an indefinite archive.
13. As a host, I want history to work across fresh rooms, repeated runs and server restarts, so that recreating a room does not erase opening context.
14. As a host, I want renamed copies of the same accepted paper to share history, so that renaming does not reset practice context.
15. As a host, I want changed accepted paper content to start fresh history, so that an earlier version does not constrain a materially different upload.
16. As a host, I want my history private to my account, so that another host cannot inspect or influence it as their own history.
17. As a defender, I want a different opening to retain the established reviewer, valid topic eligibility and exact citations, so that novelty does not weaken grounding.
18. As a host, I want an exact or normalized recent duplicate detected, so that a superficial formatting change is not treated as a fresh question.
19. As a host, I want one bounded regeneration after a duplicate, so that the app tries another supported angle without looping indefinitely.
20. As a host, I want to retry or explicitly accept a validated repeated candidate if variation fails, so that the limitation does not force an invisible choice.
21. As a teammate, I want a rejected candidate kept out of the active defense, so that voting and answer time begin only for an accepted question.
22. As a paying host, I want rejected or stale proposals to incur no run charge, so that I pay for an accepted defense opening.
23. As a host, I want an accepted opening recorded and charged at most once, so that duplicate clicks, retries and racing requests do not duplicate history or charges.
24. As a host, I want history-storage failure reported before an opening is committed or charged, so that the app does not falsely claim it checked my history.
25. As a host, I want repeat acceptance to expire when the run or map changes, so that an obsolete choice cannot start another defense.
26. As an operator, I want history expiry and size bounds enforced in storage, so that the feature cannot grow into an unbounded paper or answer archive.

### Speaker desk and live capture

27. As a chosen defender, I want the question and research context beside the speaking workspace, so that I can answer while referring to the evidence.
28. As a phone user, I want the Speaker desk stacked with a clear way to reach its answer controls, so that a long question does not bury Start mic or Send.
29. As a defender, I want the existing paper viewer, citations, seats, timer and team chat to remain usable, so that speaking practice retains the room context.
30. As a chosen defender, I want Start mic to be an explicit action, so that entering a room or winning a vote never begins recording.
31. As a defender, I want the transcription provider and separate retention disclosed before capture, so that I understand where live audio goes.
32. As a chosen defender, I want recognized words to appear while I speak, so that I can follow the captured explanation.
33. As a chosen defender, I want provisional words distinguished from finalized words, so that I do not mistake unstable recognition for the final transcript.
34. As a chosen defender, I want voice text read-only and legible, so that it preserves what was recognized without looking like an unusable disabled control.
35. As a chosen defender, I want voice in both the answer and answer-probe reply boxes, so that I can rehearse the whole same-question exchange.
36. As a teammate, I want only the chosen defender authorized to stream an answer, so that another seat cannot consume allowance or answer on their behalf.
37. As a defender, I want Team chat and clarification controls to retain typing, so that voice does not change those interactions.
38. As a defender, I want silence to leave a draft unsent, so that thinking or pausing does not submit an unfinished answer.
39. As a defender, I want Send to stop the mic and finalize the last segment, so that the end of my explanation is included.
40. As a defender, I want Finishing transcript shown while Send waits, so that I understand the delay and cannot send the same answer repeatedly.
41. As a defender, I want the normal answer acknowledgment to confirm acceptance, so that visible words or a speech-service event are not mistaken for a recorded answer.
42. As a defender, I want my existing answer or reply deadline to continue during finalization, so that speaking does not extend the turn unfairly.
43. As a defender, I want a clear late-submission outcome if finalization crosses the deadline, so that I know the speech was not accepted.
44. As a defender, I want Discard and record again, so that I can replace inaccurate recognition without editing voice text.
45. As a defender, I want Switch to typing to open a fresh typed answer, so that unreliable recognition does not trap me in an uneditable draft.
46. As a defender, I want unrelated typed work protected when changing input methods, so that starting voice does not silently overwrite an unsent answer.
47. As a defender, I want mic denial, unsupported capture and speech-service errors to explain how to type, so that a valid defense can continue.
48. As a defender, I want unchanged direct-answer, clarification and probe recovery rules, so that voice provenance does not silently alter answer interpretation.

### Capture lifecycle and allowance

49. As a defender, I want capture stopped when selection, turn or probe changes, so that my speech cannot enter another person's answer.
50. As a defender, I want capture stopped on leaving, ending, restarting, losing authorization or closing the page, so that obsolete work cannot keep recording.
51. As a defender, I want navigating away from the speaking workspace to stop capture without pausing the defense, so that microphone state and server time remain clear.
52. As a defender, I want disconnection to stop capture without replaying Send, so that reconnection cannot submit something I did not choose to send.
53. As a defender, I want a still-valid finalized unsent draft distinguished from accepted answers after reconnect, so that I can make a fresh manual submission when time permits.
54. As a defender, I want delayed speech events ignored after my attempt becomes obsolete, so that old text cannot populate a new question or run.
55. As a team, I want ten shared voice minutes per defense run displayed, so that we can allocate speaking practice across defenders.
56. As a team, I want forwarded audio from discarded and retried attempts to count, so that displayed usage reflects consumed transcription allowance.
57. As a team, I want refresh and reconnect to preserve server allowance usage, so that the cap is consistent for all defenders.
58. As a defender, I want the cap to stop further forwarding and finalize available text without sending, so that I retain control of submission.
59. As a defender, I want typing available after the cap, so that reaching the voice limit does not end an otherwise valid defense.
60. As a host, I want the current ten-credit or voucher defense rules unchanged, so that the pilot does not introduce a hidden voice charge.
61. As an operator, I want finite server limits for streams, durations, attempts and payloads, so that client behavior cannot bypass the pilot budget.
62. As an operator, I want standard provider keys kept on the server, so that browser and native clients cannot use them independently.
63. As a defender, I want the app to discard audio after bounded processing, so that it does not create an audio archive.
64. As a defender, I want only submitted transcript and supported measurements retained with current results, so that discarded speech is not treated as accepted performance.

### Languages and delivery evidence

65. As an English-speaking defender, I want English voice to be the first supported pilot language, so that its quality can be checked before broader claims.
66. As a Tagalog or Bisaya speaker, I want my language offered only when supported and tested, so that an advertised option is usable.
67. As a multilingual defender, I want supported natural code-switching preserved without forced translation, so that the transcript reflects my explanation.
68. As a defender, I want unreliable recognition explained separately from delivery feedback, so that transcription mistakes are not graded as poor speaking.
69. As a defender, I want captured filler examples such as uhm discussed with clearer wording, so that I can practice a more direct explanation.
70. As a defender, I want normal language particles distinguished from fillers, so that Bisaya or Tagalog usage is not automatically criticized.
71. As a defender, I want speaking rate and pauses shown only with reliable measurements, so that the app does not manufacture delivery statistics.
72. As a defender, I want missing evidence explained, so that a cleaned transcript is not presented as proof that I used no fillers.
73. As a typed-answer defender, I want wording and reasoning coaching without invented audio measures, so that my feedback stays appropriate to my input.
74. As a defender, I want no accent grade or unsupported confidence, pronunciation or tone judgment, so that feedback stays within the evidence.

### Detailed coaching and Results

75. As a team, I want a grounded overview followed by detailed coaching for every recorded turn, so that useful feedback is not limited to a few examples.
76. As a defender, I want a question selector and focused coaching details, so that I can review a long defense without one wall of text.
77. As a defender, I want expandable original-answer and improvement sections, so that I can compare the explanation with the advice at my own pace.
78. As a defender, I want original submitted words preserved, so that suggested wording never rewrites the record of my performance.
79. As a defender, I want original answers and probe replies attributed to their actual speakers, so that each person can identify their contribution.
80. As a defender, I want a specific explanation of what worked and what needs improvement, so that coaching is useful rather than generic praise.
81. As a defender, I want stronger wording grounded in the paper and my answer, so that the example does not invent research choices, safeguards or findings.
82. As a defender, I want missing facts labeled as questions or conditional scaffolds, so that I do not repeat an AI suggestion as an established fact.
83. As a defender, I want a practice task for each recorded turn, so that I can rehearse a concrete improvement.
84. As a defender, I want a missed answer represented factually, so that the app does not invent strengths or pretend I supplied a response.
85. As a researcher, I want coaching adapted to the confirmed field and approach, so that stronger answers remain suitable for my study.
86. As a team, I want progress as required sections finish, so that I can begin reviewing useful coaching while remaining work continues.
87. As a defender, I want the optional final panelist closing once after the overview is ready, so that the conversation ends naturally before Results.
88. As a defender, I want an absent or invalid optional closing skipped safely, so that it cannot discard valid coaching.
89. As a reconnecting defender, I want the remaining closing interval and current progress restored, so that earlier stages are not replayed.
90. As a host on Account or a payment task, I want a clear return-to-results action without forced interruption, so that shared room transitions preserve my task.
91. As a team, I want a required failure to retain completed cards, so that one failed section does not erase useful feedback.
92. As a host, I want retry to target only failed sections within existing limits, so that successful work is not regenerated or charged again.
93. As a paying host, I want an unresolved required coaching failure to retain eligible end-unavailable credit return, so that partial Results do not waive the purchased service.
94. As a voucher or free-access host, I want recovery without credits I never spent, so that credit compensation stays correct.
95. As a host, I want full completion only after every required section succeeds, so that report status and financial outcome agree.
96. As a host, I want late completions ignored after recovery or restart, so that they cannot reverse a credit return or replace a newer report.
97. As a defender, I want transcript and summary exports to retain original answers, speakers, input provenance, available evidence and coaching status, so that the record remains truthful outside the app.
98. As a defender, I want restart or room loss described honestly, so that persistent opening history is not mistaken for durable result or audio storage.

### Native, fallback and accessibility

99. As an Android user, I want a rebuilt app to request microphone permission only for the trusted app's explicit capture action, so that unrelated content cannot record me.
100. As an iOS user, I want a microphone purpose explanation and trusted-origin capture handling, so that live practice respects platform permission rules.
101. As a native user, I want denial, revocation and backgrounding to stop capture with clear recovery, so that capture cannot continue invisibly.
102. As a native user, I want sign-in, payment returns and existing origin restrictions preserved, so that voice does not widen those access rules.
103. As a user of an older or unsupported native build, I want typing retained, so that a missing capture capability does not break the defense.
104. As a keyboard or assistive-technology user, I want labeled controls, visible focus and readable capture/progress status, so that I can complete the flow without relying on color or pointer use.
105. As a phone or landscape user, I want visible next actions without overlapping controls, so that I can reach mic, Send and retry while retaining timer context.
106. As a Streamlit user, I want research-first labels and richer research text coaching while keeping typed input, so that the fallback shares useful guidance without pretending to support live voice.
107. As an operator, I want voice pilot enablement and provider configuration separate from text AI, so that switching the question model does not accidentally reroute audio.
108. As an operator, I want local mocked evidence separated from real speech, hosted and installed-device evidence, so that pilot readiness claims reflect checks that actually ran.

## Implementation Decisions

### Scope, navigation and the selected prototype

- Apply persistent opening variation and research-specific voice/coaching to Research paper and Research + code. Preserve code-only generation, report and timer behavior. Label code-only Experimental without implying it is removed. Fresh setup defaults to research; explicit and restored choices win over the default.
- Keep the four research reviewer perspectives and the current host-confirmed research profile, remapping/confirmation, coverage, citations, question budgets, voting, answer/probe limits and account access. Adapt advice by field, approach, setting and research stage; no invented institutional or country-specific requirements.
- Use the existing persistent app shell and bookmarkable preparation/room/Controls/Results screens. Navigating does not create a room, map a paper, start a defense, pause time or leave. Preserve account/payment task-return and private-member PDF behavior.
- Prototype B resolves the layout question: question/research context beside a dedicated speaker workspace on wide screens; stacked on narrow screens with an accessible answer shortcut and visible next actions. Keep panel/team context and the existing paper-viewer controls accessible. Results use a question selector and focused detail with expandable content for every turn. The fixed prototype footer, scenario switches, fake timers and synthetic reports are throwaway material, not production UI or contracts.
- Preparation adds a short general guide and voice recommendation. It must not expose stronger sample answers for upcoming questions. Typing remains an equal functional fallback.

### Durable private opening-question history

- Extend the existing account database/store boundary rather than adding a separate hosted service. Support its local SQLite and configured PostgreSQL paths. Add an account-scoped opening-history record with accepted-paper fingerprint, defense-run/commit identity, bounded opening text, relevant reviewer/topic identity and server commit time. Enforce unique authoritative commit identity, indexed account/content lookup and bounded retrieval/cleanup. Do not store full papers, answer transcripts or audio in this history.
- Compute identity on the server from a versioned deterministic representation of accepted research content, with document boundaries represented. Renaming the same accepted content must preserve identity; changed accepted research content starts another key. Do not let client filenames, uploaded fingerprint claims, room codes or display names define ownership. Mixed-defense code alone is not a replacement for paper identity. This fingerprint is a lookup key, not a promise that source content is anonymous.
- Read the most recent five unexpired committed openings for the host/content key, across rooms and runs, using server time and deterministic commit ordering. Enforce 30-day expiry on reads and deletion and a five-record bound per key; perform bounded cleanup so expired keys do not accumulate indefinitely. Another host's records never enter the request or recipient snapshot.
- Include recent opening context in the existing grounded opening request. Preserve the current research opening reviewer and mapped-topic eligibility, rather than hardcoding map topic zero or bypassing coverage. Seek a different supported angle; do not promise that every paraphrase is semantically novel.
- Deterministically reject exact/normalized recent duplicates using a defined, tested normalization of question comparison text. Do not normalize or rewrite the validated source citation. Recent topic/wording context guides semantic variation, but a lexical detector is not an independent semantic evaluator.
- Allow one automatic duplicate regeneration, subject to existing AI admission and finite attempt limits. If another validated candidate repeats, expose a host-only retry or accept-repetition choice. Any candidate preview is explicitly not the active defense question; teammates wait for the host. Host retry is still admitted and cannot reset quotas.
- Bind the proposed candidate and acceptance to the current room, owner, defense run, map version and question-generation identity. Revalidate currency of the proposal and citation before commit. Concurrent duplicate submissions or old acceptance commands have no effect on a replacement run.
- Put the authoritative opening-history append and once-only run charge/access transition under the same transactional store operation for the relevant run. Extend the existing store interface where required; independent history and charging transactions are insufficient. A required lookup/write or commit failure must not publish/charge a new opening. Preserve release/retry recovery and free/voucher behavior. Recheck the relevant history under the commit's concurrency boundary so racing starts cannot silently bypass duplicate policy.
- Commit at most one history entry per accepted opening/run; no entry for a stale, rejected or failed draft. Once committed, publish through the existing room owner and ordered snapshot path. Durable history survives a process restart; the in-memory room does not. A commit followed by process loss must remain financially idempotent and follow existing interruption recovery.

### Authorized speech relay and capture state

- Add one bounded room-scoped speech transport boundary, authenticated by existing room membership and the verified defender identity. Keep binary/media handling separate from ordinary JSON room commands where necessary, but make the room coordinator the owner of authorization, attempt identity and lifecycle. No parallel controller may mutate the defense independently.
- The transport contract covers explicit start, bounded audio frames, stop/finalize, cancel, provisional text, finalized text, allowance/status and structured errors. Server-issued attempt identity binds room, run, turn, selected defender and optional probe. Sequence/item identity prevents duplicate or out-of-order transcript completion from producing duplicate or reordered text. Provider callbacks are data, not room commands.
- Start is permitted only for the current online chosen defender in a valid research/mixed answer or probe-reply window, with pilot enabled, configured provider and remaining allowance. A room code, host role without selection, old attempt or forged speaker/turn claim is insufficient. Limit concurrent active speech attempts to the currently authorized answer opportunity; starting another cannot leave an untracked old stream.
- Browser/native clients capture only after Start mic and successful permission. The UI distinguishes idle, starting, listening, finalizing, ready-unsent and failed/stopped states, with clear typing recovery. It never requests microphone access on page load, seat selection, navigation return or reconnect.
- Recognized words are read-only, visibly provisional or final, and readable with adequate contrast. The grey styling must not hide text or depend on a disabled field to express state. Provisional recognition is never an accepted answer or a coaching strength.
- Start mic does not silently overwrite a typed draft. An explicit input-mode change resolves the existing unsent draft; switching from voice to typing discards the voice draft and provides fresh editable text. Preserve existing tab-scoped typed draft/navigation behavior. Do not persist audio or provisional recognition in browser storage. Voice drafts carry no new restart/refresh durability guarantee.
- Send stops capture, requests final completion of submitted segments, assembles finalized items by identity and calls the existing submission/acknowledgment path once. The action is disabled while finalizing/sending. No silence, segment-final, quota exhaustion, reconnect or provider-close event may submit on its own. Ctrl/Command+Enter must obey the same finalization and once-only rules as the visible Send action.
- Finalization cannot pause or extend the server deadline. Keep the existing answer/reply size and nonempty-text validation; do not silently truncate overflow into a different answer. A finalization failure or late final text produces an honest unsent/rejected outcome with available recovery. Late data cannot spill into another turn.
- Use server-finalized text and server-associated provenance/measurements for voice submissions; client read-only styling does not establish authenticity. Validate that the submitted attempt belongs to this defender/opportunity and that its finalized text matches. Never trust client-supplied delivery scores or arbitrary text labeled as verified voice.
- Preserve ordinary interpretation/direct-answer/probe/clarification and recovery rules. Submission acknowledgment and the accepted defense record determine acceptance, not speech readiness. A recognized request treated as clarification by the existing rules is not relabeled as a successful defense answer. Keep original-answer and probe-reply provenance separate.
- Stop local capture, stop server forwarding and invalidate obsolete callbacks on selection, turn/probe/run change, authorization loss, disconnect, leave, end, restart, room expiry, screen/page teardown or native backgrounding. Navigating away from the speaking workspace stops capture without pausing the room. Provider failure is surfaced without blocking typing.
- Reconnection never restarts the mic or replays Send. A finalized unsent draft may remain recoverable only while its server attempt and current opportunity are still valid; require manual submission before the current deadline. Provisional/obsolete capture is discarded. Obsolete callbacks cannot refill a cleared draft or overwrite accepted text.

### Pilot allowance, provider configuration and privacy

- Use an operator-enabled tester pilot with ten voice minutes shared across all defenders in one defense run. The current ten-credit defense price, voucher access and once-only charge/credit-return rules stay; no voice surcharge or new credit unit is introduced. The operator covers added speech and coaching provider costs.
- Account for audio forwarded to the provider, including discarded recordings and retries, in the server's authoritative per-run allowance. Refresh, speaker change or reconnect cannot reset it. Do not use a browser stopwatch or declared media duration as the authority. Bound and validate the media representation and reserve/account for forwarding under the room's concurrency boundary so competing streams cannot overspend the same remainder.
- Enforce finite payload, buffering, audio duration, stream concurrency, start/attempt frequency, finalization timeout and operator/account/server resource limits. Hard-stop forwarding at deadline, revocation or cap even if a client ignores the UI. At the cap, finalize available text when possible without submitting; offer typing. The cap is a product allowance, not a promise about provider billing granularity or total cost.
- Configure maintained OpenAI live transcription separately from text generation. The approved plan records a candidate model and point-in-time pricing research; verify the maintained model, session protocol, account access, regional availability and actual usage before enabling the pilot. Do not make a deprecated model the default or assume a text-model/OpenRouter configuration also configures speech.
- Use a server-controlled relay/lifecycle boundary; standard speech keys remain server-only. Provider ephemeral-token expiry alone cannot enforce room access, a turn deadline or the spending cap. Stop/close upstream work when application authorization ends.
- Retain only bounded application audio buffers needed for forwarding/validated measurements; discard them after processing. No audio archive, audio file download, recording replay service or audio browser cache is introduced. Telemetry/error logs must not retain raw audio, full transcripts, credentials or uploaded private source.
- Submitted transcripts and supported measurements remain with the existing in-memory room/results. Measurement evidence belongs only to the actually submitted voice material; usage accounting still includes discarded/failed attempts. Clear obsolete unsent capture. Opening history is the only new persistent practice-history feature in this scope.
- Disclose provider identity and its separately applicable retention before capture. The plan's checked Realtime policy described 30-day abuse-monitoring retention; reverify and disclose the applicable policy before launch. Application deletion does not imply provider deletion. No recordings or provider calls are authorized merely by writing or reviewing this spec.

### Truthful language and delivery coaching

- Launch English first. Offer Tagalog and modern Bisaya individually only after selected-service support and representative recognition/code-switch checks pass. Retain typed-language preferences and natural terms; do not force translation or infer supported speech languages from existing text-prompt support.
- Separate captured transcript observations, reliable computed measurements and AI suggestions. Use captured filler/repetition examples, including uhm when present, to explain clearer wording and organization. Missing fillers in a cleaned transcript do not establish filler-free audio. Avoid unsupported total counts or treating ordinary Bisaya/Tagalog particles as filler by default.
- Report approximate speaking rate or pauses only when supported by reliable audio/timing evidence for the submitted material. Explain missing/insufficient measurements; do not generate placeholder numbers. Typed submissions receive text-based feedback with audio evidence unavailable. Recognition uncertainty cannot be scored as a speaking fault.
- Coach relevance, directness, reasoning, structure and evidence. Stronger wording must preserve the defender's intended claim and the paper's established facts, marking any missing information or conditional scaffold. Never manufacture a sample size, result, ethical safeguard or method to make an answer sound better. No accent grade, psychological confidence inference or transcript-only pronunciation/tone assessment.
- Use the confirmed research profile and accepted evidence across the overview and per-turn sections, with support for theoretical, qualitative, quantitative, computational and interdisciplinary research. Suggested answers are practice aids; they do not revise the transcript, score, research coverage or source evidence.

### Per-turn report, progressive Results and financial completion

- Extend the shared research coaching contract with an overview and a required section for every recorded defense turn, including its original answer, probe exchanges, actual speakers, input provenance, available delivery evidence, specific feedback, supported stronger wording and practice task. Associate data with stable run/turn/probe identities, not array arrival order or an editable display name. Do not require one global suggestion to cover multiple speakers' distinct contributions.
- Freeze required report membership from the accepted transcript when defense discussion ends. Generate no cards for unasked future questions. A recorded unanswered outcome receives a factual note and labeled scaffold/practice guidance, never an invented answer or strength. Empty sessions retain a factual summary and make no unnecessary coaching calls.
- Generate the overview and required sections automatically in finite, sequential/admitted groups. Capture immutable source/transcript/profile input and use the existing coordinator's duplicate-work, cancellation and stale-result protections. Validate report structure, section identity and bounds before publishing. Batching is application request grouping, not discounted provider Batch API pricing or a claim of lower total cost.
- Represent overview status, each required section's status, aggregate progress/error and complete-report readiness separately. Add compatible fields to room snapshots, shared report data and client types; legacy/code-only report data remains readable. A whole-report ready flag may not be set while any required section is pending, invalid or failed.
- After a valid overview, publish any valid optional last-reviewer closing using the existing reading interval, then show progressive Results. Missing/invalid optional closing is skipped without discarding valid core data. Persist the current closing identity/deadline in the live room so reconnect resumes only remaining time. Section retry never replays closing. Account/payment tasks receive a return-to-results indication rather than forced navigation.
- In Results, show completed sections immediately, an honest completed/required count and clear pending/failed states. The selected B question/detail layout makes every recorded turn reachable and retains expandable original-versus-improved comparisons. Do not show fake percentages based on elapsed time or suggest a pending section has evaluated an answer.
- Preserve successful sections exactly across recovery. Host retry targets failed required work only, with finite admission and no further defense charge; it does not silently regenerate ready sections or retry an unlimited number of times. Continue queued/pending work under the same bounded job ownership. Controls/Results explain who may retry and when limits are exhausted.
- Financial completion occurs only after the overview and all required sections are valid and the durable outcome can be committed. Viewing partial Results, ending the closing interval or recording the final answer is insufficient. A durable completion-write failure must remain recoverable rather than claiming successful settlement. This deliberately replaces the previous research behavior that settled on a single overview/report before a closing display.
- A server-recorded unresolved required-coaching failure retains the existing eligible end-unavailable credit-return operation. Once-only returns are limited to credits actually charged; free/voucher runs cannot mint credits. Speech unavailability alone does not create a money refund or automatic credit return when typing and the purchased defense remain available.
- Fence every result and completion/return against current run and job/section identity. A return, restart, closure, abandonment or replacement invalidates old work; a late result cannot reverse a return, settle twice, charge again or overwrite another report. Keep existing interruption compensation, abandonment observation and terminal-outcome policy. Partial work remains unfinished for existing restart recovery purposes.
- Keep room retention and lifecycle logic aware that progressive Results can still represent unfinished work. Do not expire it as a successfully settled report merely because the UI is on Results. This adds no durable room/report recovery service.
- Transcript/summary export retains accepted original words, original/probe speaker attribution, voice/text provenance, available measurements, ready coaching and a truthful partial/failed/complete state. No audio export is added. Retain current access checks for room results and downloads.

### Native and Streamlit integration

- Add Android audio permission declarations and runtime handling, plus trusted-origin WebView audio-capture permission handling. Add iOS microphone-purpose disclosure and trusted-origin media-capture/lifecycle integration. Grant only requested audio capture for the configured trusted application origin, never camera access or capture for an external page/subframe through a broad wildcard grant.
- Preserve exact origin, sign-in, payment and download trust boundaries. Permission denial/revocation, navigation away, backgrounding and destruction stop capture and recover through explicit user action. Provider-side stopping cannot depend solely on a native page successfully sending a teardown message.
- New native builds and actual installed capture/permission checks are required before voice is advertised as supported there. Source inspection or responsive web checks do not establish Android/iOS capture. Older/unsupported builds retain typing; a missing toolchain/device must be documented as pending evidence, not silently claimed as completion.
- Streamlit shares research-first mode presentation, the general guide and richer research text-coaching contracts. It remains typed and single-browser: no live voice, native capture or multiplayer Speaker desk is added there. Its coaching must preserve partial work/retry truthfulness without pretending to grant live-store compensation that the fallback does not support. Code-only fallback behavior stays compatible.

### Delivery checkpoints

- Checkpoint 1: durable bounded opening history, duplicate recovery/acceptance and research-first/default/Experimental presentation, with the app runnable.
- Checkpoint 2: live web voice, bounded authenticated relay, manual finalizing Send, allowance and evidence/recovery, while native clients can still type.
- Checkpoint 3: complete research per-turn coaching, progressive Results/closing, export, safe financial recovery and typed Streamlit integration.
- Checkpoint 4: native source/build work and integrated supported-surface verification. Record actual device/provider gaps separately before making readiness claims.
- Present local previews before publication. These are runnable checkpoints, not the final implementation-ticket breakdown. Rewrite validated prototype decisions under production contracts and tests; do not merge the throwaway implementation.

## Testing Decisions

- The user confirmed these boundaries on 2026-10-17: whole-App React/browser behavior; authenticated FastAPI HTTP/WebSocket flows with AI, speech and payments mocked and a controlled clock; real local database history/migration/concurrency checks; native permission/lifecycle checks; and separately recorded real speech/provider/hosted/installed-device evidence.
- Prefer the highest existing boundary: drive room creation, preparation, voting, answering, probes, recovery and Results through authenticated public room HTTP/WebSocket contracts, asserting recipient snapshots, acknowledgments, transcript and ledger outcomes. Fake external speech at the relay boundary with deterministic audio/transcript events, rather than unit-testing private task registries or reproducing the implementation. Ordinary room commands must remain compatible.
- A good test demonstrates a user-visible or security/financial contract: a wrong speaker cannot stream; no final event autosends; finalization across a deadline records no answer; a failed section retains a ready one; a returned run cannot later settle. Avoid tests that merely mirror helpers, CSS classes, implementation call order or private state layout.
- Existing protocol, timed-room, room-access, live-room and coordination tests are prior art for two-client authentication, controlled deadlines, stale-result rejection, AI admission, retained answers and once-only charges/returns. Keep focused generator/report contract checks where external structured data validation cannot be exercised economically only through a full defense.
- Use the existing real-local-PostgreSQL runner and isolated database setup for migrations, two-account isolation, content identity across renamed uploads, changed-content separation, five-entry pruning, 30-day expiry, concurrent append/duplicate acceptance, idempotent replay, commit rollback and history survival across a process/store restart. Run local SQLite contract coverage too. Provider mocks do not substitute for these real transaction checks.
- Exercise opening history through accepted-question/ledger behavior: rejected proposals are not active or charged; exactly one duplicate regeneration is admitted; host acceptance is bound to the current candidate/map/run; lookup/write failure leaves recoverable uncharged preparation; retry does not duplicate history or charge. Include adversarial interleavings at the store commit boundary.
- Through the speech transport and room interfaces, test unauthorized/nonselected/stale attempts, one current stream, bounded media, forged provenance/metrics, out-of-order/duplicate final segments, finalizing Send once, explicit clarification/probe compatibility, oversized/empty transcript rejection and no auto-send on silence/final event/cap.
- Use fake audio and a controlled clock for deadline/cap races, shared usage across defenders, discarded/retried forwarded usage, navigation/teardown, disconnect/reconnect, run/selection/probe changes, provider failure and late callbacks. Assert no additional forwarding after revocation/deadline/cap and no usage reset on reconnect. No raw audio/transcript retention in error logs or browser storage is expected.
- Verify accepted-only evidence attribution, typed versus voice feedback, absent measurement handling, observed filler examples, unanswered turns and grounded/conditional suggested wording through report contract and end-to-end fixtures. Mocked model wording establishes data handling and instructions, not genuine speech recognition or coaching quality.
- Reuse whole-App and real-browser navigation/draft/stage checks for Speaker desk, Back/refresh, read-only versus fresh typing, explicit mode changes, focus, keyboard Send, disabled finalization, paper/citation availability, selected coaching detail, partial progress and Account/payment task preservation. Add fake capture/transport only at the browser platform/service boundary. Test accessible behavior rather than a screenshot-only claim.
- Through complete two-client research and mixed defenses, cover clarification, probe reply, timeouts, finalization, repeated opening, late/retried events, one closing, progressive cards, free failed-only retry, exhausted recovery, reconnect, transcript/export and successful versus returned settlement. Include twelve-question runs and large synthetic report membership covering the supported question budget. Code-only and typed-only users remain regression cases.
- Extend existing coaching-closing and live-store tests to distinguish a visible closing/partial Results from full financial completion. Test completion-write failure and races among last-section success, end-unavailable recovery, restart and stale callbacks. Assert a paid run charges/returns/completes at most once and a free/voucher run creates no credit award. Keep ready cards unchanged and never replay closing during retry.
- Verify Streamlit's shared research report/typed behavior and code-only compatibility using existing fallback contract patterns. Do not claim that single-browser checks establish multiplayer synchronization or live microphone behavior.
- Run the project's full Python suite, full React suite and production build at the required checkpoints and final gate. Python providers are mocked offline. Scope tests to behavior and risks rather than creating tests for status-document changes or throwaway prototype controls.
- Review desktop, phone portrait and landscape with keyboard/focus and long content. Confirm no control overlap, readable grey transcript, stable timer context, clear next action, full cited-page access and usable question/detail coaching. Synthetic browser screenshots are local visual evidence, not hosted or physical-device evidence.
- Native verification includes permission/origin/lifecycle policy checks and builds where toolchains exist, followed by actual installed Android/iOS denial, recording, backgrounding, reconnect and typed fallback checks. Record platform/build/device/version and failures; unavailable iOS tooling on Linux remains pending.
- Separately evaluate actual English recognition, delayed final segments, fillers, rate/pause evidence and grounded coaching with consented synthetic practice material; evaluate Tagalog/Bisaya/code-switching before enabling each language. Independently verify provider access, usage cost, applicable retention and hosted transport/resource behavior. No real audio upload, paid call, deployment or readiness claim follows from offline tests or this specification.

## Out of Scope

- Replacing the four research reviewer roles, inventing examiner credentials, institution-specific rubrics or country-specific compliance certification.
- New live voice or detailed per-answer delivery coaching for code-only defenses; removing the current code-only flow.
- Voice chat, voiced clarification input, panelist text-to-speech, automatic submission after silence, transcript editing in voice mode or background recording.
- Audio archives, audio replay/download services, durable room/transcript/report storage or a general account practice-history dashboard. Only bounded opening-question history is newly durable.
- Pronunciation, accent, emotional/psychological confidence or tone grading without supporting evidence; invented filler totals, speaking measures, research facts or model answers treated as actual team performance.
- A guarantee that every new opening is semantically unique, an extra independent AI novelty evaluator, or random questions that bypass mapped topics/source validation.
- Additional user charges, new payment/refund workflows or changes to current voucher rules, question prices, research question budgets, voting or answer/reply deadlines. Required-coaching readiness changes are explicitly included.
- Unrelated architecture/authentication/payment/document-extraction refactors, wholesale navigation redesign or merging the prototype variants into production.
- Streamlit live audio/multiplayer, broad camera/storage permissions, external-origin microphone grants or automatic support claims for untested native builds/languages.
- Automatic source publication, merging into main, deployment, recording upload or paid provider usage under this specification-writing request.

## Further Notes

- Scope source: [confirmed research-practice plan](../../docs/DEFENSE_PRACTICE_IMPROVEMENTS_PLAN.md), including Q1–Q20 and Q21 confirmation. Do not reopen settled choices as a discovery interview.
- Selected UI source: [prototype review and layout verdict](../../docs/DEFENSE_PRACTICE_PROTOTYPE_REVIEW.md). Throwaway branch **prototype/research-practice** contains source **f0d74a7** and selection record **a3046c4**. Layout B was chosen by the user; simulated transcript/report/financial behavior is not production evidence.
- Respect [bounded opening history](../../docs/adr/0006-bounded-opening-question-history.md), [partial coaching before settlement](../../docs/adr/0007-progressive-coaching-before-settlement.md), [existing credit compensation](../../docs/adr/0002-live-run-credit-compensation.md), [bookmarkable app screens](../../docs/adr/0005-bookmarkable-app-screens.md) and the [domain glossary](../../CONTEXT.md). Existing code settles its single report before closing; research partial coaching intentionally changes that boundary under the accepted ADR, while code-only remains compatible.
- The current app uses in-memory rooms with one worker and one instance. Persistent opening history does not make active rooms, voice drafts or Results survive a restart. Preserve existing verified-interruption compensation and truthful room-loss messaging.
- Model names, protocol features, language support, prices and retention in the plan are dated research inputs, not perpetual promises. Revalidate operational configuration during implementation/launch and keep actual billed usage separate from the product's voice allowance.
- Local status ready-for-agent means this spec can feed the To Tickets workflow; no implementation tickets have been published by this action. User review of a layout and confirmation of test boundaries do not authorize push or deployment.

# Voice delivery evidence — English pilot

Research/mixed Results separates captured words, measured recording facts and AI
practice suggestions for each accepted answer and actual probe reply speaker.
Only a current, server-finalized draft whose words match the accepted submission
supplies voice provenance. Typed replacements, clarifications, discarded,
provisional and stale attempts supply no accepted voice-performance evidence;
forwarded usage still counts against the shared allowance.

The server records received PCM duration at the configured 24 kHz sample clock,
excluding synthetic finalization padding. This measures recording duration, not
speaking time, accuracy or delivery quality. No raw audio is retained. Client
measurements are ignored. English configuration must be acknowledged before audio
forwarding. The UI retains the existing English-only pilot/typing fallback and
pre-capture app/provider retention disclosure. Tagalog, Bisaya and code-switch
recognition are not advertised as verified; typed language support is independent.

The selected gpt-live-transcribe model supplies no word timestamps or transcription
confidence and does not support server/semantic VAD, according to the
[official realtime transcription guide](https://developers.openai.com/api/docs/guides/realtime-transcription),
checked 2026-10-18. Therefore this pilot does **not** calculate speaking rate or
linguistic pause counts. Full recording duration divided by recognized words
would not establish a reliable speaking measure. Short recordings and missing or
invalid legacy evidence have explicit unavailable reasons, without zero statistics
or recognition uncertainty being graded as a speaking fault. Future numeric
speech measures require a separately validated source and representative evidence.
No model substitution or extra evaluator was introduced for this ticket.

Bounded hesitation-like and repeated phrase examples are copied verbatim from
accepted text. They are observations to review, not asserted spoken totals or an
automatic error judgment. Ordinary Bisaya/Tagalog particles are not in the pilot's
hesitation matcher. Recognition may omit fillers or introduce repetition; an empty
example list never proves filler-free speech. Suggestions must preserve the
intended meaning and paper evidence, with missing facts labeled conditional.
Neither accent, tone, pronunciation nor psychological confidence is inferred.

Cards and summary exports retain original/probe attribution, available capture
facts, observations and explicit unavailable states, independently of AI wording.
The coaching request receives accepted provenance and instructions to distinguish
it from suggestions. Existing required-card validation, batching, prices,
completion/credit recovery and empty-session rules remain in force. No audio or
durable Results archive is added; Streamlit stays typed and single-browser.

Offline fake-audio/report/App and synthetic browser evidence establishes data
handling and presentation only. Actual recognition accuracy, captured fillers,
measurement usefulness, each additional speech language, provider account/protocol,
usage cost/retention controls, hosted transport and installed devices remain
separate pending evidence. Voice remains disabled by default before enablement.

# Live voice pilot — local implementation

Ticket 03 adds research/mixed web voice; code-only and Streamlit keep typed input.
Voice is disabled by default. No real microphone, speech account, hosted relay or
installed-device verification is implied by the offline tests.

## Operator configuration

Set `VOICE_PILOT_ENABLED=1`, a private `OPENAI_SPEECH_API_KEY`, and optionally
`OPENAI_SPEECH_MODEL=gpt-live-transcribe`. Never place keys in the client, logs,
tracked files or chat. This is separate from `OPENAI_API_KEY`, `OPENAI_MODEL` and
any text-model/OpenRouter base URL. The speech endpoint is fixed to OpenAI.
Unsupported models keep voice disabled; no automatic deprecated-model fallback.
Before enabling for testers, verify account/region access, actual transport,
representative English audio and applicable retention/cost controls. Each capture
also waits for provider confirmation of the expected transcription configuration.

The default allowance is600seconds of PCM forwarded per run, shared by defenders.
`VOICE_ALLOWANCE_SECONDS` can lower it (1–600) for a smaller pilot; it cannot raise
the ten-minute ceiling. `VOICE_ATTEMPTS_PER_RUN` defaults40(max80);
`VOICE_MAX_STREAMS` defaults16(max64), with one per owner and one per room.
Starts are limited to12per owner/minute. Attempts last at most125seconds and still
end at the room's earlier answer deadline. Finalization has an8second limit;
setup and socket IO have separate finite bounds. No voice surcharge is added.

Media is raw mono PCM16 at24kHz, captured explicitly by an AudioWorklet. Frames
are at most9600bytes, at most60frames/second with bounded startup buffering, and
may not arrive faster than real audio duration. Actual forwarded sample counts
are authoritative. Reserved writes with uncertain network failure count
conservatively against the allowance; reconnect/discard never restore usage.
Raw audio is not archived, written to disk or browser storage. Temporary frames,
provider queues and transcript/segment identities are bounded. Text overflow is
rejected, never truncated into another answer. Client controls cannot inject
provider events or arbitrary verified voice text.

## User flow and limitations

Use voice resolves a typed draft explicitly. Start mic requests browser permission
and starts a room-authorized relay. Provisional/final words are read-only and
readable. Send stops capture, finishes the last segment and submits server-final
text through existing interpretation/direct-answer and acknowledgment rules.
Silence, provider finals and the shared cap never submit automatically. The
server rechecks current speaker/run/turn and deadline. Navigation, background,
disconnect, selection/run change and lifecycle invalidation stop capture/relay.
No automatic mic restart or Send replay occurs on reconnect.

The Speaker desk places paper/question context beside the workspace on desktop,
stacks it on phones, and includes an answer shortcut, existing citations/PDF,
seats, chat and authoritative timer. Switching to typing discards the voice draft
and opens an empty editable answer. Submitted provenance records OpenAI/model and
forwarded audio duration with the original answer; duration is not speaking pace.
Typed claims cannot fabricate that provenance. Original-answer and later typed
probe content remain distinct. Probe voice/reconnect refinements are ticket04;
native microphone releases are08/09. English is the initial pilot; Tagalog/Bisaya
are not advertised as verified. Provider recognition errors are not delivery grades.

## Primary documentation checked 2026-10-18

[Live transcription](https://developers.openai.com/api/docs/guides/realtime-transcription)
documents24kHz PCM, manual commits, partial/final item events and model-specific
turn detection. [Server events](https://developers.openai.com/api/reference/resources/realtime/server-events)
define committed-item ordering and final identities; completion arrival order is
not trusted. [Realtime connection](https://developers.openai.com/api/reference/resources/realtime/methods/connect)
uses server Bearer authentication. The adapter's exact connection/session setup
still requires an actual account/hosted check before pilot launch.

[GPT-Live-Transcribe](https://developers.openai.com/api/docs/models/gpt-live-transcribe)
is the maintained candidate checked for this implementation; live account access
and billed usage have not been tested here. [OpenAI data controls](https://developers.openai.com/api/docs/guides/your-data)
list separate default abuse-monitoring retention up to30days (with controls and
exceptions). App audio deletion does not imply provider deletion. The UI discloses
this before capture. [Representative transcription checks](https://developers.openai.com/api/docs/guides/transcription)
are needed for language, noise, names, numbers and microphone quality.

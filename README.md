# AI Defense Arena

Practice your research defense with four AI reviewers and up to four teammates.
Upload your paper, review its research map, then answer questions grounded in
cited passages from your materials.

## How it works

1. Sign in to host, choose Research paper or Research + code, and upload your materials.
2. Map the paper, review the suggested research profile, and confirm the question budget.
3. Share the room code. Teammates join with a name, without signing in.
4. Vote for a speaker, answer the panel, and request clarification when needed.
5. Review the transcript and personalized coaching, including stronger supported wording and practice tasks.

## Features

- **Four perspectives:** Methodology, Ethics, Impact and Critical reviewers, adapted to your research field and study approach.
- **Paper beside the question:** PDF page navigation and matched citation highlighting, with an exact-quote fallback.
- **Team practice:** server-owned voting and answer timers, private team chat, reconnect and saved-answer recovery.
- **Focused feedback:** short questions, optional reactions, same-question probes and coaching for each answer.
- **Flexible access:** Free practice with usage limits, or Standard practice with credits or a voucher.
- **Desktop and mobile:** responsive web interface, Android/iOS WebView projects and a typed Streamlit fallback.

Code-only defense is experimental and temporarily disabled. Voice is disabled
pending its separate provider/integration checks. AI feedback is practice guidance,
not a certification of research quality.

## Project

FastAPI serves the React/TypeScript app and authenticated HTTP/WebSocket room
flows. OpenRouter handles research mapping, reviewer conversations and coaching.
Accounts and financial records support SQLite or PostgreSQL; active rooms live
in memory and disappear after a restart. Run one worker and one instance.

Uploaded material is sent to the configured AI providers for processing. Team
chat is excluded from AI prompts and coaching. Keep credentials and private
papers out of Git.

## Documentation

- [Development guide](docs/LOCAL_DEVELOPMENT.md)
- [AI models, reasoning and spending limits](docs/OPENROUTER_SETUP.md)
- [Free practice](docs/FREE_PRACTICE.md)
- [Payment operations](docs/LIVE_TESTER_PAYMENTS.md)
- [Mobile apps](mobile/README.md)
- [Render service definition](render.yaml)
- [Current status and verification history](PROJECT_LOG.md)

Contributors and coding agents should read [AGENTS.md](AGENTS.md) first.

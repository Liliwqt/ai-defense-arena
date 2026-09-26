# AI Defense Arena

A browser-based, four-question project defense for up to four teammates. Two AI panelists sit across from the team in a fixed-seat Phaser scene. The Technical Architect and Security Reviewer alternate questions, then each asks one follow-up. Every question cites an exact line in the uploaded project.

For work across agents or session windows, read [AGENTS.md](AGENTS.md) and [PROJECT_LOG.md](PROJECT_LOG.md) before making changes.

## Run the multiplayer game locally

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
read -rsp 'OpenAI API key: ' OPENAI_API_KEY; echo
export OPENAI_API_KEY
read -rsp 'Room host passcode: ' GAME_HOST_PASSCODE; echo
export GAME_HOST_PASSCODE
.venv/bin/uvicorn game_server:app --host 127.0.0.1 --port 8000
```

Open <http://127.0.0.1:8000>. The room fills the browser viewport. The setup drawer opens automatically: the host enters the passcode, a display name, and source files or a ZIP, then shares the room code with teammates. Teammates join from the same service URL in separate browsers or devices. The host starts the defense from **Controls**. The active panelist shows a speech-bubble cue; the card below the seats shows the complete question and exact cited source line. Use **Answer** to submit a response and **Transcript** to review the four turns. On a portrait phone, rotate to landscape for the room. Any teammate can answer; the first valid answer received for a turn counts. If a question fails, the previous answer stays saved and the host can retry. Reconnecting with the same browser restores the room snapshot while the server process is still running. Use <http://127.0.0.1:8000/?preview=1> to review the layout with mock data and no API call.

For a quick project upload, select `sample_project/README.md` and `sample_project/queue.py`. If your account cannot use the default `gpt-6-luna` model, set `OPENAI_MODEL` to one your account can access. The key and host passcode are read only by the Python server, never put in the browser bundle or repository. The commands above do not echo or save either value in shell history. Restart the service after changing them.

For teammates on other devices, use the deployed HTTPS URL. The browser selects `wss://` automatically for its room connection. Local `127.0.0.1` is reachable only on the host computer.

## Deploy to Render

`render.yaml` describes one Free Python web service with one worker, a health check, and prompts for `OPENAI_API_KEY` and `GAME_HOST_PASSCODE`. From a **private** GitHub repository, create a Render Blueprint or configure one Web Service with the same build and start commands. Set both secrets in Render's dashboard; never commit them. If needed, add `OPENAI_MODEL` in the dashboard. Check `/health`, open the service URL on two devices, and create a fresh room shortly before the demo. The service serves the game, HTTP API, and WebSocket from one origin.

Rooms are in memory. A Render restart, redeploy, or Free-instance idle spin-down erases active rooms; connected browsers will need a new room code after that. Keep only one worker and one instance for this prototype.

## Streamlit fallback

The earlier single-browser app is still available:

```bash
.venv/bin/streamlit run app.py
```

It supports the same four AI questions and validated source lines, but no shared multiplayer room.

## Limits and troubleshooting

Uploads accept up to 60 supported UTF-8 text files, 100 KB per file, and 300 KB total text. A ZIP can be up to 10 MB compressed. Generated folders, hidden files, and unsupported ZIP entries are skipped; files are read in memory and not extracted. The game server displays the accepted filenames in room state. Each question sends the accepted project text and earlier answers to OpenAI.

If generation fails, the app shows a safe error category and lets the host retry. HTTP 401 means the key was rejected; HTTP 404 often means the model is unavailable to the API project; HTTP 429 can mean a rate limit or insufficient credit. Missing API key is reported before a paid request. Rooms and transcripts are not persisted or exported.

Run offline checks with `.venv/bin/python -m unittest discover -v`; AI calls in the tests are mocked.

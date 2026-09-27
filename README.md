# AI Defense Arena

A browser-based project defense for up to four teammates. A React, TypeScript, and code-built Three.js room shows four AI panelists facing the team: Technical Architect, Security Reviewer, Product Judge, and Critical Judge. Each asks at least one question and may ask one immediate follow-up, for four to eight resolved turns in total. Every question cites an exact line in the uploaded project. At the end, the team receives a shared coaching report with strengths, areas to improve, and a next step.

For work across agents or session windows, read [AGENTS.md](AGENTS.md) and [PROJECT_LOG.md](PROJECT_LOG.md) before making changes.

## Run the multiplayer game locally

For real AI questions, run `./run_local.sh` in a terminal after installing the Python dependencies below. It builds the current React app, prompts privately for your API key and a **local** room host passcode, and starts FastAPI at <http://127.0.0.1:8000/>. The key and passcode stay in that terminal process and are not saved in the repository. The temporary test server at port `8770`, when running, uses prewritten mock questions and does not analyze uploaded files with AI.

Questions arrive one at a time: the Technical Architect starts, and an answer or timeout triggers the next question or a follow-up. All four judges speak at least once, so a defense has four to eight resolved turns. The room shows “Preparing the next question…” while a real API request is pending.

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
./run_local.sh
```

Open <http://127.0.0.1:8000>. The setup drawer opens automatically: the host enters a local passcode, a display name, and source files or a ZIP, then shares the room code. Teammates join from the same service URL. The host starts the defense from **Controls**.

Each new question is visible during a **15-second speaker vote**. Every online defender, including the host, can vote for an online teammate or change their vote. The server randomly resolves ties or no votes among online defenders. Then the selected teammate has a fresh **two minutes** to answer in the bottom **Vote/Answer** bar; only that teammate can submit. The clock and winner come from the server, so a late vote or answer is rejected even if a browser timer lags. If the selected teammate disconnects, another online teammate is chosen without resetting the deadline. An expired question is recorded as unanswered and the defense continues. If AI question generation fails, the saved answer or timeout remains and the host can retry from **Controls**.

The complete question and exact cited line stay in a scrollable card above the bottom bar. The citation includes a filename, line number, preserved indentation, and horizontal scrolling for long lines. **Team Chat** in the bottom bar is private to the room's defenders, holds the latest 100 messages of up to 500 characters each, and is excluded from AI prompts, the transcript, and coaching. The Transcript drawer shows answered and missed turns plus the shared coaching report; coaching never treats a timeout as an answer. Reconnecting with the same browser restores the room, vote, deadline, chat, transcript, and coaching while this server process is running. On portrait phones, rotate to landscape. Use <http://127.0.0.1:8000/?preview=1> for a static mock question, add `&vote=1` for a mock voting phase, or `&long=1` to inspect card and citation scrolling. Preview mode makes no AI call and does not accept answers or chat messages.

For a quick project upload, select `sample_project/README.md` and `sample_project/queue.py`. If your account cannot use the default `gpt-6-luna` model, set `OPENAI_MODEL` to one your account can access. The key and host passcode are read only by the Python server, never put in the browser bundle or repository. The launcher does not echo or save either value in shell history. Restart the service after changing them.

For teammates on other devices, use the deployed HTTPS URL. The browser selects `wss://` automatically for its room connection. Local `127.0.0.1` is reachable only on the host computer.

## Deploy to Render

`render.yaml` describes one Free Python web service with one worker, a health check, a frontend build (`npm ci && npm run build`), and prompts for `OPENAI_API_KEY` and `GAME_HOST_PASSCODE`. From a **private** GitHub repository, create a Render Blueprint or configure one Web Service with the same build and start commands. Set both secrets in Render's dashboard; never commit them. If needed, add `OPENAI_MODEL` in the dashboard. Check `/health`, open the service URL on two devices, and create a fresh room shortly before the demo. The service serves the game, HTTP API, and WebSocket from one origin.

Rooms are in memory. A Render restart, redeploy, or Free-instance idle spin-down erases active rooms; connected browsers will need a new room code after that. Keep only one worker and one instance for this prototype.

## Streamlit fallback

The earlier single-browser app is still available:

```bash
.venv/bin/streamlit run app.py
```

It supports the same four panelists, adaptive follow-ups, and validated source lines. Voting, timers, and team chat are multiplayer web-room features only.

## Limits and troubleshooting

Uploads accept up to 100 supported UTF-8 text files, 200 KB per file, and 600 KB total text. A ZIP can be up to 25 MB compressed. For this repository, upload a source-only ZIP; the full checkout contains large dependency and build folders. Generated folders, hidden files, and unsupported ZIP entries are skipped; files are read in memory and not extracted. The game server displays the accepted filenames in room state. Each question sends the accepted project text and earlier answers to OpenAI.

If generation fails, the app shows a safe error category and lets the host retry. HTTP 401 means the key was rejected; HTTP 404 often means the model is unavailable to the API project; HTTP 429 can mean a rate limit or insufficient credit. Missing API key is reported before a paid request. Rooms, chat, transcripts, and coaching reports are not persisted or exported. The coaching report is practice guidance, not a numeric grade.

Run offline checks with `.venv/bin/python -m unittest discover -v`, then `(cd game && npm test && npm run build)`; AI calls in the tests are mocked. The frontend build requires Node.js and npm.

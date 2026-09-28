# AI Defense Arena

A browser-based code and research defense for up to four teammates. The local React room places four panelist cards above the question and four defender cards below it, with a persistent vote, answer, and chat dock. Code projects use Technical Architect, Security Reviewer, Product Judge, and Critical Judge; research defenses use a research-focused panel. Each asks at least one question and may ask one immediate follow-up, for four to eight resolved turns in total. Every question cites exact uploaded source or extracted document text. At the end, the team receives a shared coaching report with strengths, areas to improve, and a next step.

The flat room redesign is on `feature/question-first-room` and has not been deployed; the hosted `main` release still uses the earlier 3D room.

For work across agents or session windows, read [AGENTS.md](AGENTS.md) and [PROJECT_LOG.md](PROJECT_LOG.md) before making changes.

## Run the multiplayer game locally

For real AI questions, run `./run_local.sh` in a terminal after installing the Python dependencies below. It builds the current React app, prompts privately for your API key, and starts FastAPI at <http://127.0.0.1:8000/>. The key stays in that terminal process and is not saved in the repository. The `?preview=1` pages use mock room state for layout review and make no AI call. Ordinary rooms use the configured API key.

Questions arrive one at a time: the first panelist for the selected defense type starts, and an answer or timeout triggers the next question or a follow-up. All four judges speak at least once, so a defense has four to eight resolved turns. After the first question, each panelist can briefly react to a specific point in the latest answer before asking one focused question. The four roles use distinct professional, friendly voices and can match the language of a substantive answer, including Taglish.

While the AI reviews an answer, the room keeps the resolved question, team answer or timeout, and citation visible with a “Reviewing your answer…” status. The reaction and question arrive together in one validated response; every question still cites an exact uploaded source line.

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
./run_local.sh
```

Open <http://127.0.0.1:8000>. The setup drawer opens automatically: the host enters a display name, selects **Code project**, **Research paper**, or **Research + code**, and uploads the required materials. Project sources accept individual text files or a ZIP; research documents accept text-based PDF, DOCX, TXT, and Markdown files directly. The host shares the room code. Teammates join from the same service URL. The host starts the defense from **Controls**.

Research and mixed defenses use Methodology Reviewer, Ethics Reviewer, Impact Reviewer, and Critical Reviewer. The host can mark a paper as a proposal or completed study, or let the AI infer its stage. Methodology questions cover the study design and feasibility; ethics questions address participants and research integrity; impact questions concern practical value; critical questions challenge assumptions and evidence. Mixed defenses can connect claims in the paper to the implementation. The panel cites extracted document text with its PDF page and extracted line or DOCX paragraph/table location. The excerpt is exact extracted text, not a claim that its interpretation is proven. The 4–8-question structure and one optional follow-up per reviewer also apply to research defenses. Use <http://127.0.0.1:8000/?preview=1&research=1> to inspect the local research room without an AI call.

Each new question is visible during a **15-second speaker vote**. Every online defender, including the host, can vote for an online teammate or change their vote. The server randomly resolves ties or no votes among online defenders. Then the selected teammate has a fresh **two minutes** to answer in the bottom **Vote/Answer** bar; only that teammate can submit. The clock and winner come from the server, so a late vote or answer is rejected even if a browser timer lags. If the selected teammate disconnects, another online teammate is chosen without resetting the deadline. An expired question is recorded as unanswered and the defense continues. The chosen defender may also type a request such as “Can you repeat that in simple English?” or “Can you give an example?” in the same answer box. The AI interprets each submission; a clarification explains the existing question without advancing, starting a new vote, or counting as an answer. Up to two clarifications are allowed per question. The answer clock pauses while the AI interprets the text and resumes with its remaining time. If interpretation fails, the submission and time remain saved: the chosen defender can retry or explicitly use the pending text as an answer, and the host can retry. If AI question generation fails, the saved answer or timeout remains and the host can retry from **Controls**.

The complete question and exact cited line stay in a scrollable card between the two seat rows. The citation uses a near-black source panel with a filename, location, preserved indentation, and horizontal scrolling for long lines. The header, seat rows, and bottom dock remain visible on short landscape screens while the question card scrolls. **Team Chat** in the bottom bar is private to the room's defenders, holds the latest 100 messages of up to 500 characters each, and is excluded from AI prompts, the transcript, and coaching. The Transcript drawer shows answers, missed turns, clarification exchanges, and the shared coaching report; coaching never treats a timeout as an answer. Reconnecting with the same browser restores the room, vote, deadline, chat, transcript, and coaching while this server process is running. On portrait phones, rotate to landscape. Use <http://127.0.0.1:8000/?preview=1> for a static mock question, add `&vote=1` for a mock voting phase, `&review=1` for the answer-review state, or `&long=1` to inspect card and citation scrolling. Add `&clarify=1` to preview a same-turn explanation or `&complete=1` for transcript and coaching. Preview mode makes no AI call and does not accept answers or chat messages.

For a quick project upload, select `sample_project/README.md` and `sample_project/queue.py`. If your account cannot use the default `gpt-6-luna` model, set `OPENAI_MODEL` to one your account can access. The API key is read only by the Python server, never put in the browser bundle or repository. The launcher does not echo or save it in shell history. Restart the service after changing it.

For teammates on other devices, use the deployed HTTPS URL. The browser selects `wss://` automatically for its room connection. Local `127.0.0.1` is reachable only on the host computer.

## Deploy to Render

`render.yaml` describes one Free Python web service with one worker, a health check, a frontend build (`npm ci && npm run build`), and prompts for `OPENAI_API_KEY`. From a **private** GitHub repository, create a Render Blueprint or configure one Web Service with the same build and start commands. Set the API key in Render's dashboard; never commit it. If needed, add `OPENAI_MODEL` in the dashboard. Check `/health`, open the service URL on two devices, and create a fresh room shortly before the demo. The service serves the game, HTTP API, and WebSocket from one origin.

Anyone with the public service URL can now create a room without a passcode. Starting a defense uses the server's OpenAI API key, so monitor API usage during the demo.

Rooms are in memory. A Render restart, redeploy, or Free-instance idle spin-down erases active rooms; connected browsers will need a new room code after that. Keep only one worker and one instance for this prototype.

## Streamlit fallback

The earlier single-browser app is still available:

```bash
.venv/bin/streamlit run app.py
```

It supports all three defense types, the corresponding panelists, adaptive follow-ups, and validated source or extracted-document citations. Voting, timers, and team chat are multiplayer web-room features only. The fallback supports two same-turn clarification requests per question without a timer.

## Limits and troubleshooting

Combined code and extracted research text is limited to 100 files and 600 KB. Source uploads allow 200 KB per text file and a 25 MB compressed ZIP. Direct research documents allow 10 MB each; PDFs allow up to 100 pages. Every PDF page must contain extractable text. Encrypted, unreadable, image-only, and partially unreadable PDFs receive a clear error; provide a text-based copy. DOCX paragraphs and table cells are extracted in document order. OCR, figures, and equations are not interpreted reliably.

Uploads accept up to 100 supported UTF-8 text files, 200 KB per file, and 600 KB total text. A ZIP can be up to 25 MB compressed. For this repository, upload a source-only ZIP; the full checkout contains large dependency and build folders. Generated folders, hidden files, and unsupported ZIP entries are skipped; files are read in memory and not extracted. The game server displays the accepted filenames in room state. Each question sends the accepted project text and earlier answers to OpenAI.

If generation fails, the app shows a safe error category and lets the host retry. HTTP 401 means the key was rejected; HTTP 404 often means the model is unavailable to the API project; HTTP 429 can mean a rate limit or insufficient credit. Missing API key is reported before a paid request. Rooms, chat, transcripts, and coaching reports are not persisted or exported. The coaching report is practice guidance, not a numeric grade.

Run offline checks with `.venv/bin/python -m unittest discover -v`, then `(cd game && npm test && npm run build)`; AI calls in the tests are mocked. The frontend build requires Node.js and npm.

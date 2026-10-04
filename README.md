# AI Defense Arena

Practice a code-project or research-paper defense with four AI panelists and up to four teammates. Questions cite exact uploaded source or extracted document text. Teammates vote for a speaker, answer under a timer, request clarification, and receive a shared coaching report.

The multiplayer app uses a flat, question-centered React interface served by FastAPI. Four panelist cards sit above the question, four defender cards below it, and a persistent bottom dock holds voting, answers, and team chat. A separate Streamlit app provides a single-browser fallback.

## Current branch and verification

This README describes `feature/question-first-room`: the flat room, research documents, same-question clarifications, summary downloads, and answer-aware panelist conversations. Research and mixed defenses require a source-grounded paper map and a host-confirmed **4–100-question maximum**. Code-only defenses remain four to eight questions. The research release is live at [defense-simulator.onrender.com](https://defense-simulator.onrender.com). Google sign-in and PayMongo account/test-credit work remain separate local work and are excluded from this release. `main` stays frozen during the review window that began on October 1, 2026, and its earlier service remains unchanged.

The isolated published release passed **138 Python tests with AI mocked, 129 React tests, and a production build** using the committed lockfile. Mocked two-browser twelve-question research and mixed defenses covered planning, budget confirmation, voting, timeout follow-up, clarification, retry, reconnect, exact PDF/code citations, export and coaching. Desktop, landscape, narrow landscape, portrait rotation and keyboard drawer controls were checked separately. The larger local workspace's 170 Python/142 React totals include unpublished account/payment tests.

Live evidence is separate: a local synthetic mixed/proposal defense completed twelve questions (eleven answers and one real timeout), English/Taglish adaptation, retries, clarifications, exact citations, reconnect, export and coaching. A fresh hosted synthetic mixed/proposal smoke check completed a deliberately selected four-question budget with two browser clients: planning, real voting, answers from both defenders, a same-question clarification, reconnect, transcript download and shared coaching. All 22 hosted map references and four question citations matched the uploads exactly; the session stopped at budget exhaustion with two of twelve topics addressed and the remaining gaps shown. Coaching used valid turn references and Q1-style question numbers. Hosted health and JavaScript/CSS bytes matched the tested release. These synthetic checks do not establish exhaustive coverage or consistently strong dialogue for arbitrary papers. User visual review and physical separate-device confirmation remain pending; the hosted four-question check does not replace the longer local checks.

See [PROJECT_LOG.md](PROJECT_LOG.md) for evidence and publication history. Agents and other session windows must also read [AGENTS.md](AGENTS.md) before editing.

## Run locally

Install Python with virtual-environment support, Node.js, and npm, then run from the repository root:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
./run_local.sh
```

Open <http://127.0.0.1:8000/>. The launcher installs frontend packages when needed, builds React, privately prompts for missing credentials, and starts FastAPI. Restart it after changing Python code or prompt instructions.

| Setting | Purpose | Local configuration |
| --- | --- | --- |
| `OPENAI_API_KEY` | Server-side AI requests | Export in the launching terminal, or enter at the hidden prompt. The launcher does not save it. |
| `GAME_HOST_PASSCODE` | Creating rooms only | Export in the terminal, set in the Git-ignored `.env`, or enter at the hidden prompt. |
| `OPENAI_MODEL` | Optional model override | Export before launching. The code defaults to `gpt-6-luna` with low reasoning effort. |

The launcher reads only `GAME_HOST_PASSCODE` from `.env`; it does not load an API key or model override from that file. Do not commit secrets. Teammates join using the room code without the host passcode; the OpenAI API key stays on the server.

### Preview without AI calls

Build the frontend before starting FastAPI directly:

```bash
cd game
npm ci
npm run build
cd ..
.venv/bin/uvicorn game_server:app --host 127.0.0.1 --port 8000 --workers 1
```

Open <http://127.0.0.1:8000/?preview=1>. Preview mode uses static mock state, makes no AI calls, and does not accept room actions. Add flags to inspect different screens:

| Flag | Preview |
| --- | --- |
| `&research=1` | Research roles and document citation |
| `&plan=1` | Synthetic research map, with Controls open automatically |
| `&vote=1` | Speaker voting |
| `&coverage=1&research=1` | Longer-session progress (question 11 of 24) and topic coverage |
| `&review=1` | Reviewing an answer |
| `&clarify=1` | Same-question clarification |
| `&complete=1` | Transcript and coaching |
| `&long=1` | Long question and citation overflow |

For scope-preview variants, add `&budget=4` to view a smaller proposed budget, or `&planstatus=planning` / `&planstatus=failed` to inspect mapping status and failure copy. These fixtures make no AI requests and cannot confirm a real plan.

For frontend development, run `npm run dev` in `game/` alongside FastAPI on port 8000. Vite proxies `/api`, `/ws`, and `/health` to the backend. Real rooms still require the backend credentials.

## Create and play a defense

1. In **Controls**, enter your display name and host passcode, choose a defense type, and upload its materials. For a code demo, use [sample_project/README.md](sample_project/README.md) and [sample_project/queue.py](sample_project/queue.py).
2. Share the room code. Teammates open the same service URL and join with their own display names. The four defender seats include the host.
3. For research or mixed rooms, the host first chooses **Prepare defense**, reviews the map, edits the question maximum and selects **Confirm question budget**. Then the host starts the defense. Each question appears with its panelist, optional reaction, and validated citation.
4. Every question, including follow-ups, begins with a **15-second speaker vote**. Online defenders may vote for themselves or another online defender and change their vote. The highest count wins; ties and no votes are resolved randomly among online defenders.
5. The chosen defender gets **120 seconds** to answer. Only that defender may submit. Disconnection assigns another online defender without resetting the clock. Expiry records an unanswered turn and advances the defense.
6. After completion (four to eight turns for code; coverage, budget, or host ending for research), open **Transcript** for the conversation and coaching. **Download summary** saves a text copy of questions, citations, clarifications, answers, timeouts, and coaching in your browser.

The server owns deadlines, votes, speaker selection, and accepted answers. Reconnecting in the same browser restores the current snapshot while the room exists. Restarting a defense clears its turns, votes, timers, chat, and coaching.

**Team Chat** is room-only defender conversation: the latest 100 messages, up to 500 characters each. Chat is excluded from panelist prompts, coaching, the transcript, and summary exports.

Phone play is landscape-only. The header, both seat rows, and bottom dock stay visible while question content scrolls. Controls and Transcript use a keyboard-accessible drawer.

## Defense types and panelists

| Defense type | Uploads | Speaking order |
| --- | --- | --- |
| Code project | Project source/documentation files or ZIP | Technical Architect → Security Reviewer → Product Judge → Critical Judge |
| Research paper | Direct PDF, DOCX, TXT, or Markdown documents | Methodology Reviewer → Ethics Reviewer → Impact Reviewer → Critical Reviewer |
| Research + code | Research documents and project sources in separate inputs | Same research panel; questions may connect claims and implementation |

Research modes offer **Proposal**, **Completed study**, or **Let AI infer**. Proposal guidance examines planned methods and feasibility; completed-study guidance examines reported results and limitations. When the stage is unclear, prompts instruct reviewers to ask for clarification rather than invent findings.

In code-only defenses each panelist asks one opening question and may ask **one immediate follow-up** for a material unresolved issue. All four roles must speak, producing four to eight resolved turns. A timeout counts as a resolved turn. Follow-ups are generated from the uploads and actual conversation, not a fixed second set of questions.

### Research scope, coverage and question budget

After creating a Research paper or Research + code room, open **Controls → Prepare defense**. This is an explicit, host-only AI request; uploading or joining does not automatically call the model. It receives all accepted materials and the selected research stage, maps substantive sections and important claims into ordered discussion topics, assigns reviewers, and identifies missing or unclear information. References-only material should be excluded and repetitive content grouped. These are model instructions: validate the proposed coverage during review rather than assuming every important claim was recognized.

Each topic includes its objective, assigned reviewer, gaps, and expandable source references. References resolve to the exact server-owned paper/code text, including PDF page or DOCX paragraph/table location. In mixed rooms a topic must include a paper reference and may also cite supporting code. A valid source location does not prove the model's interpretation.

The suggested maximum is **two questions per topic, bounded to 4–100**. The host can edit and **Confirm question budget**; teammates see the same map, confirmed value and evolving coverage after reconnect. If the budget is smaller than the topic count, the screen warns that some topics may remain unexplored. A failed map retains uploads and offers **Retry research map**, without creating a question. Repeated preparation invalidates confirmation of the older map. Research planning and its errors remain separate from defense/coaching state.

A research/mixed start requires the current validated map and confirmed maximum. All four research reviewers receive an opening turn in order, with one optional immediate follow-up per primary question. After the openings, the panel selects outstanding topics by reviewer expertise rather than stopping at eight turns. It prioritizes untouched topics, then useful revisits. Direct questions are the default; grounded what-if situations are occasional and prompts prohibit consecutive scenarios.

Each next-move AI request also assesses the preceding resolved turn's topic as **discussed**, **needs clarification**, or **addressed**, with a supporting question reference. Unasked topics are **pending**. The entire assessment and next move are validated before either is applied; an invalid result preserves the accepted answer and earlier coverage for host retry. “Addressed” means the topic was covered in discussion, not that the research is correct. A timeout consumes one generated question and cannot be assessed as addressed. Clarifications keep the question and do not consume another slot.

The session ends when every topic is addressed and all reviewers have participated, the approved maximum is reached, or the host chooses **End defense**. At the maximum, the next-move request may assess the final turn and complete but cannot generate another question. Early ending cancels clocks and discards stale AI results, preserves accepted answers, and marks an active unanswered turn **ended early**, separately from a timeout. With no resolved turns it shows a factual summary without requesting AI coaching. Controls and Transcript show coverage and ending reasons; text exports and coaching include remaining gaps. The question budget is not a payment quote and spends no test credits.

Streamlit mirrors preparation, confirmation, adaptive questions, coverage, early ending and research coaching. It remains a single-browser app without multiplayer voting or chat. Changing documents, defense type or research stage clears the map, confirmation and session.

Open the synthetic visual review at `/?preview=1&plan=1`. For a real AI map, start the updated local server with your own `OPENAI_API_KEY`; mock previews and offline tests do not demonstrate live map quality.

### Conversation and clarification

Technical traces operations, Security examines boundaries and safeguards, Product explores a person's workflow, and Critical tests assumptions and evidence. Research reviewers apply corresponding methodology, participant-safeguard, and impact perspectives.

The prompts encourage short questions, specific reactions to actual answers, occasional speaker-name attribution, and grounded hypothetical situations. They distinguish team claims from uploaded evidence. All substantive questions, reactions, clarification replies, and coaching are AI-generated; live quality still requires review.

The chosen defender can use the answer box to request simpler wording, translation, terminology, or an example. The AI interprets each submission. A clarification explains the **same question**, preserving its intent and citation without advancing, adding a turn, or starting another vote. Up to two clarifications are allowed per question. The answer clock pauses during interpretation and resumes with the remaining time.

Panelists start in English. Explicit clarification language requests carry forward until another request or a meaningful answer changes the language. Short, code-only, and timed-out answers preserve it. Taglish is supported through prompt guidance and language-context handling.

If interpretation fails, the chosen defender can retry or explicitly use the saved submission as an answer; the host may also retry interpretation. Question-generation failures retain accepted answers or timeouts for host retry. Coaching failures have a separate host retry. Accepted answers do not need to be submitted again.

## Uploads and citations

Each question request receives all accepted source files and extracted research text, plus resolved dialogue and original citations. Files, names, answers, and earlier AI messages are treated as data; private chat is excluded. The app does not execute uploaded code, search the original repository, or read files excluded by upload validation.

| Limit | Value |
| --- | --- |
| Accepted files, research and code combined | 100 |
| Combined UTF-8 source and extracted research text | 600 KB |
| Individual project text file | 200 KB |
| Compressed project ZIP | 25 MB; at most 2,000 entries |
| Individual research document | 10 MB |
| PDF length | 100 pages |

Project files must be supported UTF-8 source or documentation. ZIPs are read in memory, not extracted to disk. Hidden paths, generated/dependency directories, selected credential filenames, and unsupported ZIP entries are skipped. Upload a source-only archive rather than a checkout containing dependencies/build outputs. Review accepted names before starting; unsupported direct files and exceeded limits produce errors.

Research uploads are separate, direct files. PDFs must contain readable text on every page; encrypted, invalid, image-only, and partially unreadable documents are rejected. DOCX paragraphs and table cells are extracted in document order. OCR, figures, and reliable equation interpretation are not supported.

Every excerpt is resolved from server-owned text and validated before displaying a question:

- **Code:** filename, source line number, and exact line in a near-black monospaced panel with horizontal scrolling.
- **PDF:** filename, page, extracted line, and exact extracted text in a document-style panel.
- **DOCX:** filename and paragraph or table/row/cell location.
- **Research TXT/Markdown:** filename and text line location.

Research excerpts may include up to three surrounding lines on each side, with PDF context confined to the cited page. The cited line remains emphasized and unchanged. Code citations do not include neighbouring lines.

The document panel shows **extracted text**, not a rendered original PDF. Extraction order may differ from visual reading order, especially in columns or slide decks. Original layout and figures are not preserved. A validated excerpt establishes its location, not the correctness of the AI's interpretation.

## Architecture

| Component | Responsibility |
| --- | --- |
| `game/src/` | React setup, flat room, question/citation UI, vote/answer/chat dock, transcript, and export |
| `game_server.py` | FastAPI HTTP/WebSocket service, authentication, room state, timers, and broadcasts |
| `defense_session.py` | Role order, optional follow-ups, resolved turns, and retained history |
| `research_plan.py` | Structured research map, exact source references, suggested budget and scope-preview validation |
| `question_generator.py` | Shared prompts, Responses API structured output, submission interpretation, citation validation, and coaching |
| `project_files.py` / `research_files.py` | Upload validation and document extraction/location mapping |
| `app.py` | Streamlit single-browser fallback |

Endpoints: `POST /api/rooms` for passcode-protected host creation/uploads, `POST /api/rooms/{code}/join` for teammates, `WS /ws/{code}` for player-token-authenticated events, and `GET /health`. Research actions on the authenticated room socket are host-only `prepare_research_plan`, `retry_research_plan`, `approve_research_plan`, and `end_defense`. Approval and research `start` carry the current `plan_id` and an integer `question_budget`. Snapshots carry planning status, map, safe planning error, confirmed budget, topic coverage, current topic and completion reason. FastAPI serves the production React build from `game/dist`. There is no active 3D/Phaser scene.

Rooms, accepted text, chat, and coaching live in process memory. There is no stored defense-session history. A restart or instance shutdown loses active rooms; the downloaded summary is the team's own retained copy. Keep exactly **one worker and one instance**.

## Streamlit fallback

Configure `OPENAI_API_KEY` in the launching terminal, optionally set `OPENAI_MODEL`, then run:

```bash
.venv/bin/streamlit run app.py
```

The fallback supports all three defense types, the corresponding four-role sequence, validated citations, conversational lead-ins, and same-question clarifications. It keeps its separate appearance and browser-session state. Voting, answer deadlines, and team chat belong to the multiplayer room.

## Render configuration

[render.yaml](render.yaml) defines the single-service deployment:

```text
Build: pip install -r requirements.txt && cd game && npm ci && npm run build
Start: uvicorn game_server:app --host 0.0.0.0 --port $PORT --workers 1
Health: /health
```

Set `OPENAI_API_KEY` and `GAME_HOST_PASSCODE` in the service's environment settings, plus `OPENAI_MODEL` if needed. Select the intended branch explicitly; production `main` stays frozen until its review window is released. A separate feature-branch service needs its own environment configuration.

The service hosts UI, API, and WebSocket on one origin. HTTPS pages use `wss://` automatically. Teammates on other devices need a hosted URL; `127.0.0.1` refers to their own device. Restarts and redeploys require fresh rooms.

## Checks and troubleshooting

```bash
.venv/bin/python -m unittest discover -v
(cd game && npm test && npm run build)
```

AI calls are mocked in the Python suite. Tests confirm behavior and validation, not live dialogue quality or deployment. Record live dialogue, browser layout, hosted operation, and physical separate-device checks separately in the handoff log.

- **Invalid host passcode:** use the value configured for that server. Local and hosted settings are independent. Missing `GAME_HOST_PASSCODE` disables room creation.
- **Missing frontend build:** run `npm ci && npm run build` in `game/` before starting FastAPI directly.
- **AI failure:** check the displayed safe error category and retry. A rejected key, unavailable model, rate/credit limit, or connection failure may require different fixes. `OPENAI_MODEL` overrides the default.
- **Citation rejected:** the model supplied an invalid file or line. Validation blocks it; the host can retry with the prior answer retained.
- **Room missing:** a process restart erased it. Create a fresh room and share its new code.

Coaching is qualitative practice guidance: strengths, improvements, and a next step tied to actual resolved turns. It supplies no numeric score and must not treat missed answers as responses.

# Project handoff log

Use this file to track completed updates across agents and session windows. See `AGENTS.md` for the update rules. Older entries below are reconstructed from the current files and conversation; new entries should be written as work happens.

## Current status

- The React/Phaser multiplayer room and shared coaching report are deployed to Render from commit `a1bd90c`. A hosted four-answer coaching walkthrough passed; physical separate-device confirmation remains unverified.
- Locally, Technical Architect, Security Reviewer, Product Judge, and Critical Judge each ask at least one source-grounded question. Each may ask one immediate AI-selected follow-up, for four to eight answers. The Streamlit fallback supports the same adaptive sequence.
- The adaptive four-panelist release and larger source ZIP limits are deployed from commit `afad667`. Hosted health, assets, and desktop/landscape mock previews pass. A fresh hosted live AI defense has not yet been completed, and the user has not reported a personal visual review.
- The local React room now uses a code-built Three.js isometric scene, a bottom question card, and an answer drawer. Accepted answers trigger a brief presenter focus using the responder's seat; this redesign has not been pushed or deployed.
- The four judge roles are printed on dark plaques on their desk panels in the local Three.js preview.
- The four teammate characters now stand without chairs; their live name tags sit near their feet.

## Active work

- Root session, 2026-09-27: redesigning the React room question/citation and bottom answer composer, then testing and deploying directly as requested. Files: React App, QuestionCard, ControlsPanel, Phaser scene, socket hook, CSS, tests, README, AGENTS, PROJECT_LOG, and new review screenshots. Preserve unrelated local screenshots and draft plan.
- Root session, 2026-09-27: deploying the adaptive four-panelist release and larger ZIP limits to Render from private `main`, then verifying hosted health, assets, and room flow. Files: selected feature code, tests, docs, new review screenshots, and this log. Preserve unrelated local screenshots and draft plan.
- Root session, 2026-09-27: preparing the adaptive four-panelist checkpoint for user review, then deployment after approval. Files: Python defense/generation/server/fallback and tests, React scene/components and tests, README, AGENTS, PROJECT_LOG, and new four-panel review screenshots. Preserve unrelated screenshots and `react-migration-plan.md`.

## Pending verification and next step

- The earlier release was deployed directly. The new Three.js redesign is local for visual review first; its live AI room flow has not been run or deployed. A fresh hosted live AI room check of the earlier adaptive release still awaits a host-created room code.
- Physical separate-device confirmation remains separate from two-browser local verification.

## Change entry template

Append new entries to the **end** of this file in date order:

### YYYY-MM-DD — Brief change title

- Session: name or label, if several agents are working at once.
- Files: paths changed.
- Changed: user-visible behavior or key implementation detail.
- Verification: tests or manual checks run, with results.
- Remaining: open issue, review gate, or `None`.

## Changes

### 2026-09-26 — Project intake (reconstructed)

- Files: `project_files.py`, `app.py`, `test_project_files.py`, `README.md`.
- Changed: added ZIP and multiple-file upload, accepted-file preview, and file size/type limits. Files are read in memory.
- Verification: offline project-file tests cover accepted and rejected uploads.

### 2026-09-26 — First grounded question (reconstructed)

- Files: `question_generator.py`, `app.py`, `test_question_generator.py`, `README.md`.
- Changed: added a Technical Architect question using all accepted project files, structured output, and validated code file/line citations. Added clear API error messages and an `OPENAI_MODEL` override.
- Verification: offline tests cover valid and invalid citations, missing key, and API error mapping.

### 2026-09-26 — Four-question defense chat (reconstructed)

- Files: `app.py`, `defense_session.py`, `question_generator.py`, `README.md`, `test_app.py`, `test_defense_session.py`.
- Changed: added alternating Technical Architect and Security Reviewer questions, two follow-ups, session-only answers, exact source-line display, restart/reset behavior, and retry without losing an answer.
- Verification: 33 offline tests passed, including a mocked four-answer Streamlit walkthrough and retry. A live OpenAI check was not run because the API key was unavailable to that execution shell.
- Remaining: complete the live walkthrough and user review before feedback.

### 2026-09-26 — Agent handoff record

- Files: `AGENTS.md`, `PROJECT_LOG.md`, `README.md`.
- Changed: added shared rules and a chronological handoff log, with a README pointer so future sessions can find them.
- Verification: checked the entries against the current project files and prior checkpoint status. Documentation-only change; no code tests needed.
- Remaining: future agents must update this log manually after their changes.

### 2026-09-26 — Multiplayer 2D defense room

- Session: root server/integration work and frontend agent scene work.
- Files: `game_server.py`, `test_game_server.py`, `game/index.html`, `game/game.js`, `game/style.css`, `requirements.txt`, `render.yaml`, `README.md`, `AGENTS.md`, `.gitignore`, `screenshots/`.
- Changed: added a FastAPI room server with authenticated host creation, four defender seats, WebSocket snapshots, first-valid-answer-wins turns, retry and reconnect behavior; added the fixed-seat Phaser interface and Render Free service configuration. Streamlit remains available.
- Verification: 36 offline unit tests passed; JavaScript syntax passed; local HTTP assets and health endpoint returned 200. A headless browser screenshot confirmed the mock scene. Two independent browser contexts completed four answers against a mocked AI server, including AI failure, retry, and reconnect; both showed a complete transcript and no page errors. `screenshots/` contains review images.
- Remaining: live AI and hosted separate-device walkthrough require runtime secrets and Render setup; user review pending. No feedback feature started.

### 2026-09-26 — Private repository prepared

- Session: root.
- Files: `PROJECT_LOG.md` and the committed project files.
- Changed: initialized the repository, committed the complete local checkpoint, and pushed `main` to the private repository `https://github.com/Liliwqt/ai-defense-arena`. The `render.yaml` Blueprint is ready for connection to Render.
- Verification: GitHub reports `isPrivate: true` and `main` as the default branch; working tree was clean after the initial push. Source files were scanned for common API-key and private-key patterns before publishing, with no matches.
- Remaining: this environment has no Render authentication or runtime `OPENAI_API_KEY` / `GAME_HOST_PASSCODE`; Render deploy and live AI/device checks await access. Do not mark user review complete.

### 2026-09-26 — Recovery from expired rooms

- Session: root.
- Files: `game_server.py`, `game/game.js`, `test_game_server.py`, `PROJECT_LOG.md`.
- Changed: handle a WebSocket peer that disconnects during authentication without an ASGI exception. If a stored room or token is invalid after a server restart, the browser clears it and returns to create/join instead of reconnecting forever.
- Verification: 37 offline tests passed, JavaScript syntax passed, and a headless browser with a stored expired room returned to the create/join form and cleared its stored code.
- Remaining: hosted live AI/device verification and user review pending.

### 2026-09-26 — Hosted live four-question walkthrough

- Session: root and the user-hosted browser.
- Files: `PROJECT_LOG.md`, `screenshots/hosted-live-defense.png` (local review artifact).
- Changed: Render Blueprint deployment is live at `https://ai-defense-arena.onrender.com`; no application code changed. A host created a room with sample project files and a second browser client joined as a defender over HTTPS/WSS.
- Verification: `/health`, HTML, CSS, and JavaScript returned HTTP 200; desktop and mobile Phaser previews rendered without page errors or mobile overflow. The guest browser completed four real AI-generated questions and answers. All four citations matched the exact `sample_project/queue.py` source line; the two follow-ups explicitly referred to the corresponding panelist's earlier answer. Both players appeared online in the complete room snapshot. The screenshot captures the completed hosted transcript.
- Remaining: user visual review and confirmation from a physical second device, if desired. Do not add feedback or panelists before review. The log and live screenshot are kept local for now so a GitHub push does not redeploy and erase the active in-memory room.

### 2026-09-26 — Fullscreen defense room local preview

- Session: root.
- Files: `game/index.html`, `game/style.css`, `game/game.js`, `README.md`, `AGENTS.md`, `PROJECT_LOG.md`, new `screenshots/fullscreen-*.png` review images. Existing local screenshot changes were preserved.
- Changed: the Phaser room fills the browser viewport, with four panel positions and four defender seats above a docked question card. The active panelist has a speech-bubble cue; the card shows the complete question and exact citation in scrollable areas. Create/join, upload, host actions, answer entry, and transcript are in a keyboard-accessible drawer. Portrait phones show a rotation prompt. The room protocol and Streamlit fallback are unchanged.
- Verification: 37 offline Python tests, JavaScript syntax, and `git diff --check` passed. Headless desktop and phone-landscape previews showed no page errors or horizontal overflow; a portrait phone showed the rotation prompt. Long question and source text remained readable. Drawer keyboard focus trapping, Escape close, and focus restoration passed. Two browser contexts completed a mocked four-turn defense including first-answer submission, one simulated AI failure and host retry, reconnect, exact citation matching, and completed transcript. No paid calls were made for this layout check.
- Remaining: user visual review of the local preview. No push or Render redeploy has happened for this change; after approval, deploy and smoke-test the hosted layout. Physical separate-device confirmation remains pending. No feedback or additional panelists were added.

### 2026-09-26 — Fullscreen deployment readiness check

- Session: root.
- Files: `PROJECT_LOG.md` only.
- Changed: confirmed the local fullscreen build is ready for visual review; no commit, push, or Render redeploy was performed.
- Verification: 37 offline tests, JavaScript syntax, and `git diff --check` passed again. Desktop, landscape, portrait, and long-question browser previews passed with no page errors or horizontal overflow. The local server returned HTTP 200 for the preview and JavaScript asset. The private GitHub `main` ref was reachable. A predeployment hosted `/health` request timed out from this environment; hosted status was not inferred from that timeout.
- Remaining: explicit user visual approval, then push and hosted checks with a fresh room. Existing unrelated screenshot changes remain untouched.

### 2026-09-26 — Fullscreen Render deployment

- Session: root.
- Files: selected fullscreen UI, docs, log, and new preview screenshots in commit `18a7d1c`; `PROJECT_LOG.md` and two hosted screenshots updated locally after deployment. Existing `screenshots/fixed-seat-preview.png` changes and `screenshots/hosted-live-defense.png` remained untouched.
- Changed: pushed the fullscreen update to private `main`; Render now serves the same HTML, CSS, and JavaScript bytes as that commit. The user explicitly authorized deployment before personal visual review.
- Verification: `/health` returned HTTP 200. Hosted headless desktop and phone-landscape previews had no page errors or horizontal overflow; portrait showed the rotation prompt; the long question remained scrollable. The hosted create/join drawer passed keyboard focus, Escape, and focus-restoration checks.
- Remaining: a fresh hosted room walkthrough with multiple clients and exact citation checks, physical separate-device confirmation, and user visual review. No feedback or additional panelists were added.

### 2026-09-26 — Hosted fullscreen four-answer walkthrough

- Session: root, with the user hosting a fresh room.
- Files: `PROJECT_LOG.md`; `screenshots/hosted-fullscreen-completed.png` and two hosted layout screenshots kept locally for review.
- Changed: confirmed the deployed fullscreen room through a complete live session; no application code changed.
- Verification: the user-hosted room accepted two independent browser clients. All four real AI questions appeared in Technical Architect, Security Reviewer, Technical Architect, Security Reviewer order. Every displayed citation and final transcript citation matched the exact uploaded `sample_project/queue.py` line. Answers from alternating clients reached both clients. The phone-sized browser reconnected during question two and recovered the current snapshot. A fresh fourth-seat browser received all four answers and the visible transcript, then retained them after reload. No page errors were recorded. The completion script's extra click on an already-open transcript drawer timed out; a separate fresh-client check confirmed this was a test-script mistake, not an app failure.
- Remaining: the user’s personal visual review and physical separate-device confirmation. Hosted screenshots remain local so the completed room is not reset by another deploy. No feedback or additional panelists were added.

### 2026-09-26 — Shared coaching report after fourth answer

- Session: root.
- Files: `question_generator.py`, `game_server.py`, `game/index.html`, `game/game.js`, `game/style.css`, `test_question_generator.py`, `test_game_server.py`, `PROJECT_LOG.md`.
- Changed: after the fourth answer is accepted the server makes one Responses API call (gpt-6-luna, low reasoning, structured output, store:false) and produces a shared `CoachingReport` with a summary, 1–3 strengths, 1–3 improvements (each referencing a turn 0–3), and one next step. No numeric score. The report is validated (non-empty text, valid turn references 0–3) before broadcasting. `feedback_status` (`none`/`generating`/`ready`/`failed`) and `feedback` are included in every WebSocket snapshot so reconnecting clients receive the full report. The room stays in `complete` phase throughout; a `retry_coaching` action (host-only) is available when `feedback_status` is `failed`. Restarting a defense clears feedback and bumps `feedback_generation_id` so any stale in-flight result is discarded. The question card shows "Preparing coaching report" while generating and adapts its message for ready/failed states. The Transcript drawer opens automatically when coaching becomes ready (or when the host should retry on failure). The coaching report appears at the top of the Transcript panel above the four turn cards. A "Retry coaching report" button appears in the host controls drawer when the report has failed.
- Verification: 51 offline tests pass (14 up from 37 in game_server, 10 new in question_generator.CoachingReportTests). New tests cover: valid report returned with correct fields and prompt contents; invalid/empty turn reference, text, summary, and next_step rejections; wrong turn count; missing/whitespace API key; one coaching call per completed defense; failure and host retry; reconnect delivers report; restart clears coaching and stale result does not arrive. JavaScript syntax check passed. No paid AI calls were made for this change.
- Remaining: present the combined local screen to the user for review. After approval, push and deploy to Render; complete one live sample-project defense and confirm the coaching refers to answers actually given on both clients. Record in this log.

### 2026-09-26 — React + TypeScript + Vite + Tailwind frontend migration

- Session: root.
- Files: `game/src/` (all new TypeScript/React source files), `game/package.json`, `game/vite.config.ts`, `game/vitest.config.ts`, `game/tsconfig.json`, `game/tailwind.config.js`, `game/postcss.config.js`, `game/index.html`, `game/src/index.css`, `game/_legacy/` (backed-up vanilla JS files), `game_server.py` (GAME_DIR → `game/dist`), `render.yaml` (build command extended), `.gitignore` (node_modules + dist excluded), `PROJECT_LOG.md`.
- Changed: replaced the vanilla JS/HTML/CSS frontend with a Vite 6 + React 18 + TypeScript 5 + Tailwind CSS 3 + Phaser 3 application. The Phaser DefenseScene is ported to TypeScript and wrapped in a PhaserScene React component using useEffect. All WebSocket logic lives in the useRoomSocket hook. Components: App, HUD, QuestionCard, RotatePrompt, Drawer, ControlsPanel, TranscriptPanel, CoachingReport, TurnCard. FastAPI backend, WebSocket protocol, room logic, and all Python files are unchanged except GAME_DIR now points to `game/dist`. The Render build command now runs `npm ci && npm run build` after pip install. Legacy vanilla files are preserved in `game/_legacy/` for reference.
- Verification: 51 Python backend tests pass. 39 frontend component/hook tests pass (vitest + React Testing Library): useRoomSocket (5), HUD (5), QuestionCard (7), CoachingReport (6), TranscriptPanel (4), ControlsPanel (7), Drawer (5). `npm run build` produces `game/dist/` with no TypeScript errors. JavaScript syntax clean. No paid AI calls were made.
- Remaining: push to private GitHub `main` and trigger a Render redeploy; run `npm ci && npm run build` in the Render build environment; smoke-test `/health`, preview URL, and a fresh live room on two devices. Record hosted verification here. Render deploy and separate-device check require Render access not available in this environment.

### 2026-09-27 — React coaching room local integration review

- Session: root.
- Files: `README.md`, `AGENTS.md`, `.gitignore`, `PROJECT_LOG.md`, `game/src/App.tsx`, `game/src/components/Drawer.tsx`, `game/src/components/Drawer.test.tsx`, `game/src/hooks/useRoomSocket.test.ts`, `game/src/index.css`, `game/src/phaser/DefenseScene.ts`, and new `screenshots/react-coaching-*.png` review artifacts.
- Changed: documented the required npm build before FastAPI starts, clarified that coaching and React are local while the earlier fullscreen version is hosted, and ignored generated TypeScript build info. Fixed answer-field focus and keyboard focus restoration in the drawer. Rebalanced the short-landscape dock and compact Phaser cue so the question, long citation, and eight seats remain visible without overlap; removed an unwrapped mock socket callback from the frontend tests.
- Verification: 51 Python unittest tests and 40 frontend Vitest tests passed; `npm ci --offline && npm run build`, local `/health`, and React asset serving passed; npm reported zero vulnerabilities. Two independent browser contexts completed all four mocked cited questions and answers; they verified answer synchronization, one question-generation failure and host retry, reconnect, one coaching failure and host retry, a shared coaching report tied to those answers, transcript, exact source-line matches, keyboard drawer actions, desktop/phone-landscape rendering, and portrait rotation. No browser page errors or paid AI calls. A long question and source line remained independently scrollable on phone landscape.
- Remaining: user review of the combined local screen. After approval, commit the selected migration/coaching/docs files, push, verify Render's build and assets, and complete a fresh live hosted defense with coaching. Physical second-device confirmation remains separate. The older unrelated screenshots and draft migration plan were preserved.

### 2026-09-27 — Combined screen approved for deployment

- Session: root, with user review.
- Files: `PROJECT_LOG.md`.
- Changed: the user reviewed the local preview/screenshots and approved committing and deploying the React/coaching room.
- Verification: approval was explicitly received in the review prompt; hosted verification has not yet happened.
- Remaining: push the selected code and docs, verify the Render deployment, then run a fresh live coaching defense.

### 2026-09-27 — React coaching deployment smoke check

- Session: root.
- Files: commit `a1bd90c` (selected React/coaching code, tests, lockfile, and docs); `PROJECT_LOG.md` updated locally after deployment. Older screenshots and draft migration plan remain local and were not included in the commit.
- Changed: pushed the approved build to private `main`; Render now serves its new React JavaScript and CSS asset hashes.
- Verification: hosted `/health`, React HTML, and both new assets returned HTTP 200. Headless desktop and phone-landscape browsers rendered the Phaser canvas and cited mock preview with no page errors or horizontal overflow; portrait showed the rotate prompt. The landscape question area stayed readable and drawer keyboard focus, Tab, Escape, and focus restoration passed. The React asset hashes matched the local build. This was a mock preview, not a live AI walkthrough.
- Remaining: run one fresh live four-answer defense and confirm both clients receive coaching grounded in the actual answers. Physical separate-device confirmation remains separate. Keep this post-deploy log local until it can be recorded without an unnecessary Render redeploy.

### 2026-09-27 — Hosted live React coaching walkthrough

- Session: root, with the user hosting a fresh Render room.
- Files: `PROJECT_LOG.md` and new `screenshots/hosted-react-*.png` review captures, kept local to avoid another redeploy. No application code changed.
- Changed: completed the four-question defense on the deployed React release and confirmed the shared coaching report after the fourth answer.
- Verification: two browser clients joined the user-hosted room and saw all four real AI questions and synchronized answers. The Technical Architect and Security Reviewer follow-ups referred to their earlier answers; each question citation matched the exact uploaded `sample_project/queue.py` line. Answers covered `BEGIN IMMEDIATE`, staff role checks, bounded lock retries, and an opaque reservation code. One walkthrough harness assertion incorrectly expected `4 / 4 answered` after the last answer, but the app correctly switched directly to `COMPLETE`. Rejoining through the remaining seat in two browser windows confirmed the four saved answers, identical ready coaching text, and report recovery after reload. The report cited Q1, Q2, Q3, and Q4 and specifically discussed those answers, including the distinction between proposed protections and the current prototype. No page errors were recorded. The two report-check windows shared the same authenticated seat; this was a browser-client check, not a physical second-device check.
- Remaining: physical separate-device confirmation, if desired. User visual approval was received before deployment. No further feature work is in this checkpoint. Keep this post-deploy log local to avoid an unnecessary Render redeploy.

### 2026-09-27 — Adaptive four-panelist local checkpoint

- Session: root.
- Files: `question_generator.py`, `defense_session.py`, `game_server.py`, `app.py`, related Python tests, React room components/scene/preview and related tests, `README.md`, `AGENTS.md`, `PROJECT_LOG.md`, and new `screenshots/four-panel-*.png` review images. Unrelated local screenshots and `react-migration-plan.md` were preserved.
- Changed: filled the outer panel seats with Product Judge and Critical Judge. Technical Architect, Security Reviewer, Product Judge, and Critical Judge each ask an opening question in order. After each first answer, structured AI output may choose one immediate source-grounded follow-up or advance. The server rejects skipped roles, early completion, invalid citations, and extra follow-ups while retaining the saved answer for host retry. The shared coaching report validates references against the actual four-to-eight-answer transcript. React and Streamlit display variable-turn progress; Streamlit remains a fallback.
- Verification: 59 Python tests, 42 frontend tests, and a Vite build passed. Two mocked two-browser FastAPI defenses completed four and eight answers, including exact source-line checks, synchronized questions and answers, reconnect, transcript, shared coaching, and a forced generation failure with host retry. Headless desktop and phone-landscape previews rendered four occupied panel seats; portrait showed the rotation prompt. No browser page errors or paid API calls. New local screenshots capture the screen and both completion lengths.
- Remaining: user visual review of the local checkpoint before any push. After approval, deploy and run a fresh live hosted room with real AI, checking both new judges and citations. Physical second-device confirmation remains separate.

### 2026-09-27 — Larger local source ZIP upload

- Session: root.
- Files: `project_files.py`, `game_server.py`, `question_generator.py`, `test_project_files.py`, `test_question_generator.py`, `README.md`, `.gitignore`, and `PROJECT_LOG.md`. Local ignored artifact: `ai-defense-arena-source.zip`.
- Changed: raised upload limits to 100 UTF-8 source files, 200 KB per file, 600 KB total text, and 25 MB compressed ZIP; raised the room request limit accordingly and kept the question generator's analysis limit aligned. Prepared a source-only ZIP from tracked project files, excluding dependencies, build outputs, hidden files, and binary assets.
- Verification: the local ZIP contains 53 accepted files and 415,285 text bytes, compresses to 120,274 bytes, and passes upload validation. All 60 Python tests pass. After restarting the local mock server, an HTTP room creation using that exact ZIP returned 201, and a browser upload reached the room controls with no page errors. No API calls or Render deployment were made.
- Remaining: user can try the local ZIP. The adaptive panelist screen still awaits user review before pushing; live AI handling of this larger project is untested.

### 2026-09-27 — Real local defense launch clarified

- Session: root.
- Files: `run_local.sh`, `README.md`, `game/src/components/QuestionCard.tsx`, `PROJECT_LOG.md`. Temporary mock servers on ports 8770 and 8771 were stopped; no production question prompts were replaced with canned text.
- Changed: added a local launcher that builds the current React app, securely prompts for the user's own API key and a local host passcode when absent, and starts the normal FastAPI server on port 8000. The question card now says that submitting an answer triggers the next question. Documented that the prior port-8770 test harness used prewritten questions and never analyzed uploads with AI. The normal server continues to use OpenAI for the first question and adaptive next moves.
- Verification: shell syntax passed, 42 frontend tests and React build passed. The launcher started the normal service with temporary placeholder credentials for a startup-only check; `/health` returned 200, then that process was stopped. No live API call was made, because no local key is configured in this environment. The ignored source-only ZIP was refreshed with the current launcher: 54 accepted files, 419,121 text bytes, and 121,888 compressed bytes.
- Remaining: user must run `./run_local.sh` in their terminal and enter their key privately to see real AI questions. The adaptive four-panelist checkpoint still awaits visual review before deployment.

### 2026-09-27 — Direct deployment requested

- Session: root, with user direction.
- Files: `AGENTS.md`, `PROJECT_LOG.md`.
- Changed: the user asked to deploy the adaptive four-panelist build directly to the web, overriding the earlier plan to wait for visual review before pushing. The user also clarified that actual defense questions must be generated by AI, not prewritten; the temporary local mock servers were stopped. Static preview fixtures remain marked as mock and are outside live defenses.
- Verification: the direct deployment request was explicit. Push and hosted verification follow this entry; visual approval and live AI validation are not inferred.
- Remaining: commit and push selected files, check Render, then test a fresh live room.

### 2026-09-27 — Adaptive panelists deployed to Render

- Session: root.
- Files: selected feature code, tests, docs, launcher, and four review screenshots in commit `3dce219`; merge commit `afad667`; local-only `PROJECT_LOG.md` and `screenshots/hosted-four-panel-*.png` after deployment. Unrelated screenshots and draft plan remain untouched.
- Changed: pushed adaptive Technical, Security, Product, and Critical panelists with source-grounded optional follow-ups, dynamic four-to-eight-turn coaching, and larger source ZIP limits to private `main`. A newer remote commit had raised only the single-file cap to 5 MB while leaving the total cap at 300 KB; the merge retained the tested 200 KB per-file and 600 KB total limits, which accept this repository's source ZIP and keep complete project prompts bounded. Render rebuilt the React app.
- Verification: 60 Python tests, 42 frontend tests, React build, and staged secret-pattern scan passed before push; 43 upload/question-generator tests passed after merging. Hosted `/health` returned 200, and the hosted JavaScript/CSS hashes matched the local build byte for byte. Headless desktop and phone-landscape mock previews showed the four panel seats and cited question card with no page errors; root showed create-room controls. The mock preview is explicitly labeled and is not a live AI check.
- Remaining: complete a fresh hosted AI defense with the user as host, checking generated questions, all four roles, citations, answer progression, and coaching. Physical second-device confirmation and personal visual review remain unconfirmed. Keep this post-deploy log local to avoid another Render redeploy.

### 2026-09-27 — Centered question and bottom answer composer, local verification

- Session: root.
- Files: `game/src/App.tsx`, `game/src/components/{QuestionCard,AnswerComposer,ControlsPanel,Drawer,HUD}*`, `game/src/hooks/useRoomSocket*`, `game/src/phaser/DefenseScene.ts`, `game/src/index.css`, `README.md`, `AGENTS.md`, `PROJECT_LOG.md`, and four new `screenshots/centered-*.png` captures. Existing unrelated screenshots and draft plan remain untouched.
- Changed: moved the complete question and exact citation into a scrollable card between the seat rows; the cited line uses a dark code panel with a filename header, gutter, preserved indentation, and horizontal scrolling. Replaced the large Phaser speech bubble with a small active-speaker cue. Moved answer entry from the drawer into a persistent bottom composer with pending, send-error, retry, and completion states; the drawer retains Controls and Transcript.
- Verification: 60 Python tests, 51 frontend tests, Vite build, and `git diff --check` passed. Two browser clients completed mocked four- and eight-answer defenses with exact citation matches, synchronized answers, transcript, coaching, reconnect, and a forced question-generation failure with host retry in the four-answer run. Desktop and 844×390 / 667×375 landscape screenshots show fixed seats and bottom bar with no browser errors or page overflow. A long question scrolls within the middle card; a long source line scrolls horizontally with the keyboard. Portrait shows the rotation prompt. These were mocked AI checks, with no paid calls.
- Remaining: push the selected UI/docs/tests/screenshots to private `main`, verify Render health/assets and a fresh live AI room. Personal visual review and physical separate-device confirmation remain unverified.

### 2026-09-27 — Judge character animation system

- Session: root.
- Files: `game/src/components/judgeConfig.ts` (new), `game/src/components/JudgePanelOverlay.tsx` (new), `game/src/components/JudgePanelOverlay.test.tsx` (new), `game/src/App.tsx`, `game/src/index.css`, `game/src/phaser/DefenseScene.ts`, `PROJECT_LOG.md`.
- Changed: added a CSS-only character animation system for the four judges — Product Judge, Technical Architect, Security Reviewer, and Critical Judge. A new `JudgePanelOverlay` React component renders animated HTML/CSS avatar figures over the Phaser panelist row. Animations are driven by real session state: the active judge pulses with a glow ring and bouncing speaking animation while their question is shown; while the user is composing, all non-active judges play distinct personality-specific idle animations (composed micro-breathe, analytical head-tilt, watchful lean-in, skeptical sway) including CSS eye blinks; after an answer is submitted a shared 1.8-second "discussing" state plays staggered thinking-dot cues and a panel-wide discussion animation; in lobby/complete/generating phases all judges show a calm waiting breathe. Judge personality config is centralized in `judgeConfig.ts`. The Phaser panelist circles, labels, and speaker dot are hidden (replaced by the React overlay). All existing functionality — upload, AI questions, multi-judge turns, answer submission, transcript, coaching — is preserved.
- Verification: 56 frontend tests pass (5 new JudgePanelOverlay tests), Vite TypeScript build passes with no errors. Pre-existing `test_app` Streamlit file-uploader API error is unrelated and was present before this change.
- Remaining: visual review in browser. Push to private main and verify Render.


### 2026-09-27 — Judge animation bug fixes and test coverage

- Session: root.
- Files: `game/src/App.tsx`, `game/src/components/judgeConfig.ts`, `game/src/components/JudgePanelOverlay.test.tsx`, `game/src/index.css`, `game/src/phaser/DefenseScene.ts`, `PROJECT_LOG.md`.
- Changed:
  - **Bug fix (reconnect):** `prevAnsweredRef` now initialises from the first snapshot's answered count (sentinel -1 → N on first arrival) so reconnecting mid-session no longer spuriously triggers the discussing animation. `handleUseRoom` and `handleLeaveRoom` also reset the baseline and cancel any in-flight discussing timer when entering or leaving a room.
  - **Dead code removed:** Unused `initials` field removed from `JudgeConfig`; exported `getJudgeConfig` helper (never imported) removed from `judgeConfig.ts`.
  - **CSS bug fix (eye blink stagger):** `judge-discussing` state now separately targets `.judge-eye-left` and `.judge-eye-right` with a 0.06 s offset so both eyes don't blink simultaneously during the discussion sequence, matching the idle-state approach.
  - **CSS bug fix (animation-delay shorthand conflict):** `.judge-waiting` previously used both an `animation:` shorthand (which implicitly sets delay to 0) and a separate `animation-delay:` override. Merged into a single shorthand with the delay embedded.
  - **Perf fix:** `DefenseScene.makeTextures()` no longer generates the unused "panelist" texture (panelist avatars are fully replaced by the React overlay).
  - **Test coverage:** Added 4 new `JudgePanelOverlay` tests — lobby shows no active judge, non-active judges do not get the asking label, complete phase shows no active judge, retry phase shows no active judge.
- Verification: 60 frontend tests pass (was 56), TypeScript clean, Vite build passes.
- Remaining: visual review in browser; push to Render when ready.

### 2026-09-27 — Code-built illustrated room local preview

- Session: root.
- Files: `game/src/App.tsx`, new `game/src/components/ThreeDefenseScene.tsx`, React room components and CSS, `game_server.py`, `game/src/types.ts`, related tests, package files, `README.md`, `AGENTS.md`, and this log.
- Changed: replaced the active room canvas with a fully code-built Three.js isometric office, four panelist and four teammate characters, live nameplates, active-judge cue, and a podium. Restyled the HUD, question card, Controls, Transcript, and answer entry. The card now opens a focused answer drawer. An accepted answer broadcasts `answered_by_seat` and briefly focuses on the correct teammate standing and gesturing at the podium; reduced-motion users get a stationary highlight. The final Transcript waits for that moment. Static mock preview includes an answer panel and a repeatable presenter action. No AI-generated image asset was added; Streamlit and defense/AI rules are unchanged.
- Verification: 60 Python tests, 64 frontend tests, TypeScript/Vite production build, and `git diff --check` passed. Local browser preview rendered the room and answer panel with no console errors. Desktop, 844×390, 667×375, and portrait viewport checks showed no page overflow; the answer panel focused its textarea and the mock presenter action activated the podium moment. No paid AI call was made.
- Remaining: user visual review and a live multi-client walkthrough of this redesign. The redesign remains local; no GitHub push or Render deployment was performed.

### 2026-09-27 — Judge roles on desk panels

- Session: root.
- Files: `game/src/components/ThreeDefenseScene.tsx`, `PROJECT_LOG.md`.
- Changed: replaced the four floating judge role badges with code-drawn, two-line dark plaques fixed to the front of the corresponding desk panels. The active speaking cue remains above the judge.
- Verification: TypeScript/Vite production build and `git diff --check` passed. The local preview showed all four roles on their desk panels with no browser console errors.
- Remaining: user visual review of the local redesign; no GitHub push or Render deployment was performed.

### 2026-09-27 — Standing teammates in local room

- Session: root.
- Files: `game/src/components/ThreeDefenseScene.tsx`, `PROJECT_LOG.md`.
- Changed: removed teammate chairs and rendered all four teammates in standing poses. Moved their live name tags near their feet and gave them dark backgrounds so they remain visible against the light floor. Updated the scene description.
- Verification: local preview showed all four teammates standing with no chairs and no browser console errors. TypeScript/Vite production build and `git diff --check` passed. Frontend dependencies were restored with `npm install` after `npm ci` could not remove an esbuild executable held open by the running dev server.
- Remaining: user visual review of the local redesign; no GitHub push or Render deployment was performed.


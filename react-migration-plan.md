# React Migration Plan

## Overview

Replace the hand-written vanilla JS/HTML/CSS frontend (`game/`) with a Vite + React 18 + TypeScript + Tailwind CSS application while keeping the Phaser 3 scene, the FastAPI backend, and the WebSocket protocol completely unchanged.

**Stack:**  Vite 5 · React 18 · TypeScript 5 · Tailwind CSS 3 · Phaser 3.86 · Vitest + React Testing Library

**Build target:**  `game/dist/` — FastAPI's existing `StaticFiles` mount at `GAME_DIR` is updated to point there.

**Non-goals:**  No changes to any Python file except the two-line `GAME_DIR` update in `game_server.py`. No new server features. No Phaser replacement.

---

## Architecture

```
game/                        ← Vite project root
  src/
    types.ts                 ← RoomState, Turn, Player, CoachingReport interfaces
    hooks/
      useRoomSocket.ts       ← WebSocket, reconnect, sendEvent, roomState
    components/
      PhaserScene.tsx        ← mounts Phaser.Game, forwards roomState to scene
      HUD.tsx                ← room pill, progress pill, Controls/Transcript buttons
      QuestionCard.tsx       ← docked bottom panel
      Drawer.tsx             ← aria-modal slide-in, focus trap, Escape close
      ControlsPanel.tsx      ← create/join forms, host actions, answer form
      TranscriptPanel.tsx    ← CoachingReport + TurnCard list
      CoachingReport.tsx     ← coaching summary/strengths/improvements/next step
      TurnCard.tsx           ← single question + citation + answer
      RotatePrompt.tsx       ← portrait lock overlay
    App.tsx                  ← top-level layout, drawer state
    main.tsx                 ← ReactDOM.createRoot
    index.css                ← Tailwind directives + custom Phaser overrides
  index.html                 ← Vite entry shell
  package.json
  vite.config.ts             ← proxy /api and /ws to localhost:8000 in dev
  tailwind.config.ts
  tsconfig.json
  dist/                      ← Vite build output (served by FastAPI)
```

---

## Sub-Tasks

---

### Sub-task 1 — Scaffold the Vite + React + TypeScript + Tailwind project

**Intent**\
Set up the Vite project inside `game/`, install all dependencies, configure TypeScript, Tailwind, and a dev-server proxy so the React app can talk to the running FastAPI server without CORS issues during development.

**Expected Outcomes**
- `game/package.json` exists with all dependencies declared.
- `npm run dev` starts on port 5173, proxies `/api` and `/ws` to `http://localhost:8000`.
- `npm run build` produces `game/dist/index.html` and hashed JS/CSS assets.
- `npm run test` runs Vitest and exits 0 on an empty test suite.
- `game/vite.config.ts` has the proxy and sets `outDir: "dist"`.
- `game/tailwind.config.ts` scans `src/**/*.{ts,tsx}`.
- `game/tsconfig.json` targets ES2022, strict mode on.

**Todo List**
- [ ] Remove the existing `game/index.html`, `game/game.js`, `game/style.css` (back them up as `game/_legacy/` for reference during migration).
- [ ] Run `npm create vite@latest . -- --template react-ts` inside `game/`.
- [ ] Install Tailwind: `npm install -D tailwindcss postcss autoprefixer` and `npx tailwindcss init -p`.
- [ ] Install Phaser: `npm install phaser`.
- [ ] Install test tooling: `npm install -D vitest @vitest/ui jsdom @testing-library/react @testing-library/user-event @testing-library/jest-dom`.
- [ ] Configure `vite.config.ts` with the `/api` and `/ws` proxy and `outDir: "dist"`.
- [ ] Configure `tailwind.config.ts` with content paths.
- [ ] Add Tailwind directives to `src/index.css`.
- [ ] Add `"test": "vitest run"` and `"test:ui": "vitest --ui"` to `package.json` scripts.
- [ ] Verify `npm run dev`, `npm run build`, and `npm run test` all succeed.

**Relevant Context**
- [`render.yaml`](render.yaml) — build command will be updated in Sub-task 9.
- Vite dev server proxy: `{ "/api": { target: "http://localhost:8000" }, "/ws": { target: "ws://localhost:8000", ws: true } }`.

**Status:** `[ ] pending`

---

### Sub-task 2 — Define TypeScript types from the server snapshot contract

**Intent**\
Create a single `src/types.ts` that precisely mirrors every field in `game_server.py`'s `snapshot()` return value. All components and the WebSocket hook import from here — no inline `any`.

**Expected Outcomes**
- `src/types.ts` exports `RoomState`, `Turn`, `Player`, `CoachingFeedback`, `FeedbackStatus`, `Phase`.
- Every field in the server `snapshot()` dict has a typed counterpart.
- TypeScript compiles with zero errors.

**Todo List**
- [ ] Create `src/types.ts`.
- [ ] Define `Phase` as a string union: `"lobby" | "generating" | "question" | "retry" | "complete"`.
- [ ] Define `FeedbackStatus` as `"none" | "generating" | "ready" | "failed"`.
- [ ] Define `Player`: `{ seat: number; name: string; online: boolean; is_host: boolean }`.
- [ ] Define `Turn`: `{ panelist: string; question: string; filename: string; evidence_line: number; evidence_text: string; answer: string | null; answered_by: string | null }`.
- [ ] Define `CoachingPoint`: `{ turn: number; text: string }`.
- [ ] Define `CoachingFeedback`: `{ summary: string; strengths: CoachingPoint[]; improvements: CoachingPoint[]; next_step: string }`.
- [ ] Define `RoomState`: all fields from snapshot including `room_code`, `self_seat`, `self_is_host`, `phase`, `players`, `turns`, `active_panelist`, `error`, `revision`, `files`, `feedback_status`, `feedback`.
- [ ] Run `npx tsc --noEmit` and confirm zero errors.

**Relevant Context**
- [`game_server.py`](game_server.py) `snapshot()` return dict — the exact field names and types are the contract.
- Current vanilla JS reads: `state?.phase`, `state?.feedback_status`, `state?.feedback`, `state?.turns`, `state?.players`, `state?.active_panelist`, `state?.error`, `state?.room_code`, `state?.self_is_host`, `state?.self_seat`, `state?.revision`.

**Status:** `[ ] pending`

---

### Sub-task 3 — Implement the `useRoomSocket` hook

**Intent**\
Extract all WebSocket logic (connect, reconnect, send, snapshot handling, connection version guard, localStorage) into a single custom hook. This is the most critical piece — it replaces the ~150 lines of imperative WebSocket code in the current `game.js`.

**Expected Outcomes**
- `src/hooks/useRoomSocket.ts` exports `useRoomSocket()` returning `{ roomState, connected, roomCode, playerToken, knownHost, waitingForAnswerAck, sendEvent, useRoom, leaveRoom }`.
- Reconnect uses the connection-version guard (stale reconnect is cancelled when version changes).
- `localStorage` helpers (`safeStore`, `clearStoredRoom`, `readStoredRoom`) are internal to the hook.
- Auto-reconnect on close with 1800 ms delay.
- `wsUrl` switches `ws://`/`wss://` based on `window.location.protocol`.
- Hook cleans up the socket and timer on unmount.

**Todo List**
- [ ] Create `src/hooks/useRoomSocket.ts`.
- [ ] Implement `connectionVersion` as a `useRef<number>` (not state — must not trigger re-renders).
- [ ] Implement `useRoom(code, token, host)` — sets roomCode, playerToken, calls `safeStore`, opens socket.
- [ ] Implement `leaveRoom()` — increments connectionVersion, closes socket, clears storage, resets all state.
- [ ] Implement `connectSocket()` — creates WebSocket, attaches listeners, guards all callbacks with version check.
- [ ] On `snapshot` message: update `roomState`, clear `waitingForAnswerAck`.
- [ ] On `error` message: handle `"Room not found"` / `"no longer valid"` by calling `leaveRoom`.
- [ ] On `close`: set `connected = false`, schedule reconnect.
- [ ] Implement `sendEvent(payload)` — returns false and logs if socket not open.
- [ ] On mount, read `localStorage` and auto-reconnect if a stored room exists.
- [ ] Write unit tests in `src/hooks/useRoomSocket.test.ts` using `vi.useFakeTimers()` and a mock WebSocket class.
- [ ] Tests must cover: initial connect sends hello, snapshot updates roomState, error triggers leaveRoom for invalid room, reconnect fires after 1800 ms, version guard prevents stale reconnect.

**Relevant Context**
- Current vanilla JS equivalent: `connectSocket()`, `scheduleReconnect()`, `sendEvent()`, `useRoom()`, `leaveRoom()`, `safeStore()`, `clearStoredRoom()`, `readStoredRoom()` in [`game/game.js`](game/_legacy/game.js).
- `connectionVersion` pattern: incremented on `leaveRoom` and new connects; every async callback checks `version !== connectionVersion` and returns early if stale.

**Status:** `[ ] pending`

---

### Sub-task 4 — Implement the `PhaserScene` component

**Intent**\
Wrap the existing `DefenseScene` Phaser class in a React component. Phaser is imperative — the component mounts the game in a `useEffect`, passes `roomState` updates to the scene via a separate `useEffect`, and destroys the game on unmount.

**Expected Outcomes**
- `src/components/PhaserScene.tsx` renders a `<div ref={containerRef}>` that Phaser mounts into.
- The `DefenseScene` class is ported to TypeScript in `src/phaser/DefenseScene.ts` with no logic changes.
- `roomState` prop changes call `scene.renderState(state)` without re-mounting Phaser.
- Phaser `scale.mode` is `RESIZE` — the canvas fills the container div exactly.
- Component cleans up via `game.destroy(true)` on unmount.

**Todo List**
- [ ] Copy `DefenseScene` class (the `create`, `makeTextures`, `layout`, `renderCue`, `renderState` methods) into `src/phaser/DefenseScene.ts` and add TypeScript types.
- [ ] Import `Phaser` from the npm package (not CDN).
- [ ] Create `src/components/PhaserScene.tsx` with `containerRef = useRef<HTMLDivElement>(null)`.
- [ ] In `useEffect([], [])`: create `new Phaser.Game({ ..., parent: containerRef.current, scene: DefenseScene })`, store in a `gameRef`. Return cleanup `() => gameRef.current?.destroy(true)`.
- [ ] In `useEffect([roomState])`: call `gameRef.current?.scene.getScene("DefenseScene")?.renderState(roomState)`.
- [ ] The container div must be `position: absolute; inset: 0` to fill the stage.
- [ ] Verify no Phaser logic is changed — only TypeScript types and the React wrapper added.

**Relevant Context**
- Current `DefenseScene` source: [`game/_legacy/game.js`](game/_legacy/game.js) lines 457–570.
- `panelNames` constant (`["Technical Architect", "Security Reviewer"]`) is used inside `renderCue` — move it to `src/phaser/DefenseScene.ts` or a shared constants file.
- Phaser `scale.on("resize", this.layout, this)` is already present — keep it.

**Status:** `[ ] pending`

---

### Sub-task 5 — Implement `HUD`, `QuestionCard`, and `RotatePrompt` components

**Intent**\
Build the three always-visible layout regions: the top HUD overlay, the docked bottom question card, and the portrait rotation prompt. These are pure presentational components driven by `roomState` props.

**Expected Outcomes**
- `<HUD>` renders the brand, room pill, progress pill, Controls button, and Transcript button. Buttons call `onOpenDrawer("controls")` / `onOpenDrawer("transcript")`.
- `<QuestionCard>` renders the panelist name, question number badge, question text (scrollable), source-block (hidden when no citation), arena status, and "Answer question" CTA. CTA calls `onOpenDrawer("controls", true)`.
- `<RotatePrompt>` is hidden except on `(max-width: 700px) and (orientation: portrait)` — Tailwind `hidden portrait:grid` with a custom breakpoint, or a CSS media query override in `index.css`.
- `<QuestionCard>` handles all `phase` + `feedbackStatus` combinations for its text content (same logic as current `renderQuestionCard()`).
- All three components have Vitest tests covering key render states.

**Todo List**
- [ ] Create `src/components/HUD.tsx` with props: `roomState: RoomState | null`, `roomCode: string | null`, `onOpenDrawer: (mode: DrawerMode) => void`.
- [ ] Create `src/components/QuestionCard.tsx` with props: `roomState: RoomState | null`, `connected: boolean`, `previewMode: boolean`, `onOpenDrawer: (mode: DrawerMode, focusAnswer?: boolean) => void`.
- [ ] Port `renderQuestionCard()` logic into `QuestionCard` as derived values from props (no imperative DOM).
- [ ] Create `src/components/RotatePrompt.tsx` as a static overlay.
- [ ] Style all three with Tailwind utility classes, matching the current visual design (dark blue palette).
- [ ] Write `QuestionCard.test.tsx`: test that each phase renders the correct heading text and that the source block is hidden/shown correctly.
- [ ] Write `HUD.test.tsx`: test that the room pill text updates and that the drawer-open callbacks are invoked.

**Relevant Context**
- Current CSS classes to replicate: `.hud`, `.brand`, `.eyebrow`, `.hud-button`, `.room-pill`, `.progress-pill`, `.question-card`, `.question-heading`, `.question-number`, `.question-content`, `.question-text`, `.source-block`, `.source-ref`, `.arena-status`, `.card-action`, `.rotate-prompt`.
- Phase/feedbackStatus logic: [`game/_legacy/game.js`](game/_legacy/game.js) `renderQuestionCard()` function.

**Status:** `[ ] pending`

---

### Sub-task 6 — Implement `TurnCard`, `CoachingReport`, and `TranscriptPanel` components

**Intent**\
Build the transcript drawer body: the coaching report block at the top, followed by four turn cards. Both are pure presentational components; `TranscriptPanel` composes them.

**Expected Outcomes**
- `<TurnCard>` renders panelist label, question text, citation line, and answer (with answerer name).
- `<CoachingReport>` renders four states: hidden (`none`), preparing (spinner text), failed (error message), ready (summary + strengths + improvements + next step with `Q{n}·` prefix).
- `<TranscriptPanel>` renders `<CoachingReport>` above the `<TurnCard>` list; shows empty state when no turns and no feedback.
- Strength items have green left border, improvement items have amber — matching current CSS.
- All three have Vitest tests covering the key render states.

**Todo List**
- [ ] Create `src/components/TurnCard.tsx` with props: `turn: Turn`, `index: number`.
- [ ] Create `src/components/CoachingReport.tsx` with props: `feedbackStatus: FeedbackStatus`, `feedback: CoachingFeedback | null`.
- [ ] Create `src/components/TranscriptPanel.tsx` with props: `roomState: RoomState | null`.
- [ ] Port `renderCoachingReport()` and `renderTranscript()` logic declaratively into the above components.
- [ ] Style `CoachingReport` with Tailwind — golden title, green strength border, amber improvement border, `::before` Q-prefix via a Tailwind `before:content-[...]` or a small wrapper span.
- [ ] Write `CoachingReport.test.tsx`: test generating, failed, and ready states; assert strength/improvement text and turn prefix rendering.
- [ ] Write `TranscriptPanel.test.tsx`: test empty state, turns-only state, and full state with ready coaching report.

**Relevant Context**
- Current CSS classes: `.coaching-report`, `.coaching-title`, `.coaching-summary`, `.coaching-section`, `.coaching-item`, `.coaching-strength`, `.coaching-improve`, `.turn-card`, `.citation`, `.answer`.
- Turn Q-prefix: `data-turn` attribute + `::before { content: "Q" attr(data-turn) " · " }` — replicate as a span or Tailwind `before:` variant.

**Status:** `[ ] pending`

---

### Sub-task 7 — Implement `ControlsPanel` and `Drawer` components

**Intent**\
Build the slide-in drawer with two panels (Controls and Transcript). `ControlsPanel` handles all forms and host actions. `Drawer` wraps both panels with the `aria-modal` role, Escape-key close, and Tab focus trap.

**Expected Outcomes**
- `<Drawer>` is a fixed right-side panel with `role="dialog"`, `aria-modal="true"`, backdrop scrim, Escape-key listener, and Tab-trap.
- `<ControlsPanel>` renders the create/join tab switcher, create form, join form, room details, connection status, host control buttons (start, retry, retry coaching, restart), answer form, wait message, and leave button.
- Host-only buttons are hidden for non-host players.
- "Retry coaching report" button is shown only when `phase === "complete"` and `feedbackStatus === "failed"`.
- All form submissions call the appropriate API or `sendEvent` via props.
- Focus is returned to the trigger element when the drawer closes.
- Vitest tests cover: Tab trap cycles, Escape closes, correct buttons visible for host vs non-host, form submission calls the right handler.

**Todo List**
- [ ] Create `src/components/Drawer.tsx` with props: `open: boolean`, `mode: DrawerMode`, `onClose: () => void`, `children: React.ReactNode`. Attach `keydown` listener for Escape and Tab trap via `useEffect`.
- [ ] Create `src/components/ControlsPanel.tsx` with props: all room state fields + callbacks for `onCreate`, `onJoin`, `onStart`, `onRetry`, `onRetryCoaching`, `onRestart`, `onSubmitAnswer`, `onLeave`.
- [ ] Implement create form: `POST /api/rooms` with `FormData`, call `useRoom` on success, clear passcode field on completion.
- [ ] Implement join form: `POST /api/rooms/{code}/join` with JSON body.
- [ ] Implement `DrawerMode` type: `"controls" | "transcript"`.
- [ ] Write `Drawer.test.tsx`: Escape closes drawer; Tab trap cycles to first/last focusable element.
- [ ] Write `ControlsPanel.test.tsx`: host sees start/retry/retry-coaching/restart buttons; non-host does not; retry-coaching only visible when feedback_status is "failed".

**Relevant Context**
- Current drawer logic: `openDrawer()`, `closeDrawer()`, keyboard listener in [`game/_legacy/game.js`](game/_legacy/game.js).
- CSS: `.drawer`, `.drawer-header`, `.drawer-close`, `.drawer-body`, `.drawer-scrim`, `.tabs`, `.tab`, `.form-stack`, `.field-hint`, `.host-controls`, `.room-details`, `.connection`, `.message`.
- Auto-open rules from `connectSocket()`: open Transcript when `feedback_status` transitions to `"ready"`; open Controls for host when transitions to `"failed"`; open Controls for host when phase transitions to `"retry"`; open Transcript when phase transitions to `"complete"`.

**Status:** `[ ] pending`

---

### Sub-task 8 — Assemble `App.tsx` and verify full local preview

**Intent**\
Wire all components together in `App.tsx`. Run `npm run dev` against the live FastAPI server and verify `?preview=1` renders the mock scene correctly, then confirm a full mocked two-browser walkthrough with no page errors.

**Expected Outcomes**
- `App.tsx` composes: `<Stage>` (contains `<PhaserScene>` + `<HUD>`), `<QuestionCard>`, `<Drawer>`, `<RotatePrompt>`.
- `useRoomSocket` is called once in `App`; all state and callbacks flow down as props.
- Preview mode (`?preview=1`) works: `previewState` is loaded, forms hidden, no API calls.
- `npm run dev` + `uvicorn game_server:app` allows full local two-browser walkthrough.
- `npm run build` produces `game/dist/` with no TypeScript errors and no Vite build warnings.
- All existing 51 Python tests still pass after the `GAME_DIR` update.

**Todo List**
- [ ] Create `src/App.tsx` — call `useRoomSocket`, manage `drawerOpen` and `drawerMode` state, manage `waitingForAnswerAck` state.
- [ ] Implement auto-open drawer rules in `App.tsx` via `useEffect` watching `roomState.phase` and `roomState.feedback_status`.
- [ ] Create `src/main.tsx` — `ReactDOM.createRoot(document.getElementById("root")!).render(<App />)`.
- [ ] Update `game/index.html` to a minimal Vite shell with `<div id="root">`.
- [ ] Update `GAME_DIR` in [`game_server.py`](game_server.py): `GAME_DIR = Path(__file__).resolve().parent / "game" / "dist"`.
- [ ] Run `npm run build` and verify `game/dist/index.html` exists.
- [ ] Run `.venv/bin/python -m unittest discover -v` — all 51 tests must still pass.
- [ ] Manually test `?preview=1` in a browser.
- [ ] Run a mocked two-browser walkthrough (four answers, retry, reconnect) locally.

**Relevant Context**
- Current `GAME_DIR` in [`game_server.py`](game_server.py) line 33: `GAME_DIR = Path(__file__).resolve().parent / "game"`.
- Preview mode state object: `previewState` from current [`game/_legacy/game.js`](game/_legacy/game.js) lines 6–28 — port to `src/previewState.ts`.
- Auto-open rules are triggered from `connectSocket` message handler in current code.

**Status:** `[ ] pending`

---

### Sub-task 9 — Update `render.yaml` and deploy to Render

**Intent**\
Add the Node.js build step to the Render build command so `game/dist/` is produced before FastAPI starts. Verify the hosted deployment serves the React app correctly.

**Expected Outcomes**
- `render.yaml` `buildCommand` installs both Python and Node dependencies and runs the Vite build.
- Hosted `/health` returns 200.
- Hosted `/?preview=1` renders the React app with the Phaser scene.
- A fresh hosted room completes four questions with coaching report on two devices.

**Todo List**
- [ ] Update `render.yaml` `buildCommand` to: `pip install -r requirements.txt && cd game && npm ci && npm run build`.
- [ ] Confirm `game/package-lock.json` is committed (required for `npm ci`).
- [ ] Push to the private GitHub repository `main` branch.
- [ ] Monitor Render build logs; confirm both pip install and Vite build succeed.
- [ ] Check `/health` returns `{"status": "ok"}`.
- [ ] Open the service URL on two devices; create a fresh room with `sample_project/README.md` and `sample_project/queue.py`; complete all four questions.
- [ ] Confirm the coaching report appears in Transcript on both devices.
- [ ] Record the result in `PROJECT_LOG.md`.

**Relevant Context**
- Current [`render.yaml`](render.yaml) `buildCommand`: `pip install -r requirements.txt`.
- Render Free plan has a 512 MB build RAM limit — Vite + Phaser build should be well within that.
- `game/node_modules/` must be in `.gitignore`.

**Status:** `[ ] pending`

---

## Dependency Order

```
Sub-task 1 (scaffold)
    └── Sub-task 2 (types)
            └── Sub-task 3 (useRoomSocket hook)
            └── Sub-task 4 (PhaserScene component)
            └── Sub-task 5 (HUD, QuestionCard, RotatePrompt)
                    └── Sub-task 6 (TurnCard, CoachingReport, TranscriptPanel)
                            └── Sub-task 7 (ControlsPanel, Drawer)
                                    └── Sub-task 8 (App.tsx + local verify)
                                                └── Sub-task 9 (Render deploy)
```

Sub-tasks 3, 4, and 5 can be worked in parallel once Sub-task 2 is complete.
Sub-tasks 6 and 7 can be worked in parallel once Sub-tasks 2 and 5 are complete.

---

## Files changed per sub-task

| Sub-task | Files created | Files modified |
|---|---|---|
| 1 | `game/package.json`, `game/vite.config.ts`, `game/tailwind.config.ts`, `game/tsconfig.json`, `game/src/index.css`, `game/index.html` | — |
| 2 | `game/src/types.ts` | — |
| 3 | `game/src/hooks/useRoomSocket.ts`, `game/src/hooks/useRoomSocket.test.ts` | — |
| 4 | `game/src/phaser/DefenseScene.ts`, `game/src/components/PhaserScene.tsx` | — |
| 5 | `game/src/components/HUD.tsx`, `game/src/components/QuestionCard.tsx`, `game/src/components/RotatePrompt.tsx`, `game/src/components/HUD.test.tsx`, `game/src/components/QuestionCard.test.tsx` | — |
| 6 | `game/src/components/TurnCard.tsx`, `game/src/components/CoachingReport.tsx`, `game/src/components/TranscriptPanel.tsx`, `game/src/components/CoachingReport.test.tsx`, `game/src/components/TranscriptPanel.test.tsx` | — |
| 7 | `game/src/components/Drawer.tsx`, `game/src/components/ControlsPanel.tsx`, `game/src/components/Drawer.test.tsx`, `game/src/components/ControlsPanel.test.tsx` | — |
| 8 | `game/src/App.tsx`, `game/src/main.tsx`, `game/src/previewState.ts` | `game_server.py` (GAME_DIR only), `game/index.html` |
| 9 | — | `render.yaml`, `PROJECT_LOG.md` |

Python test files and all other backend files are untouched throughout.

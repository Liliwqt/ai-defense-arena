"use strict";

const previewMode = new URLSearchParams(window.location.search).get("preview") === "1";
const $ = (id) => document.getElementById(id);
const panelNames = ["Technical Architect", "Security Reviewer"];
const previewState = {
  room_code: "PREVIEW",
  phase: "question",
  self_seat: 0,
  self_is_host: true,
  players: [
    {seat: 0, name: "You", online: true, is_host: true},
    {seat: 1, name: "Teammate A", online: true, is_host: false},
    {seat: 2, name: "Teammate B", online: true, is_host: false},
    {seat: 3, name: "Teammate C", online: false, is_host: false},
  ],
  turns: [{
    panelist: "Technical Architect",
    question: "Why does reserve() open a new SQLite connection for every reservation, and how will that choice behave when several students reserve at once?",
    filename: "sample_project/queue.py",
    evidence_line: 9,
    evidence_text: "    with sqlite3.connect(DATABASE) as connection:",
    answer: null,
    answered_by: null,
  }],
  active_panelist: "Technical Architect",
  error: null,
};

let roomCode = null;
let playerToken = null;
let roomState = null;
let websocket = null;
let reconnectTimer = null;
let connectionVersion = 0;
let connected = false;
let knownHost = false;
let waitingForAnswerAck = false;
let drawerMode = "controls";
let drawerReturnFocus = null;
let scene = null;

function safeStore(code, token) {
  try {
    localStorage.setItem("defense_room_code", code);
    localStorage.setItem("defense_player_token", token);
  } catch (_) {
    // The active page can still work when private browsing disables storage.
  }
}

function clearStoredRoom() {
  try {
    localStorage.removeItem("defense_room_code");
    localStorage.removeItem("defense_player_token");
  } catch (_) { /* Storage may be disabled. */ }
}

function readStoredRoom() {
  try {
    const code = localStorage.getItem("defense_room_code");
    const token = localStorage.getItem("defense_player_token");
    return code && token ? {code, token} : null;
  } catch (_) {
    return null;
  }
}

function openDrawer(mode = "controls", focusAnswer = false) {
  const drawer = $("drawer");
  if (drawer.hidden) drawerReturnFocus = document.activeElement;
  drawerMode = mode;
  $("controls-panel").hidden = mode !== "controls";
  $("transcript-panel").hidden = mode !== "transcript";
  $("drawer-title").textContent = mode === "transcript" ? "Transcript" : "Controls";
  drawer.hidden = false;
  $("drawer-scrim").hidden = false;
  $("controls-toggle").setAttribute("aria-expanded", String(mode === "controls"));
  $("transcript-toggle").setAttribute("aria-expanded", String(mode === "transcript"));
  if (focusAnswer && !$("answer-form").hidden) $("answer-form").elements.answer.focus();
  else $("drawer-close").focus();
}

function closeDrawer() {
  $("drawer").hidden = true;
  $("drawer-scrim").hidden = true;
  $("controls-toggle").setAttribute("aria-expanded", "false");
  $("transcript-toggle").setAttribute("aria-expanded", "false");
  if (drawerReturnFocus && document.contains(drawerReturnFocus)) drawerReturnFocus.focus();
  drawerReturnFocus = null;
}

function showMessage(message) {
  $("message").textContent = message;
  $("message").hidden = !message;
  if (message && $("drawer").hidden) openDrawer("controls");
}

function setButtonBusy(form, busy) {
  const button = form.querySelector("button[type=submit]");
  if (button) button.disabled = busy;
}

function selectTab(which) {
  const create = which === "create";
  $("create-form").hidden = !create;
  $("join-form").hidden = create;
  $("create-tab").classList.toggle("active", create);
  $("join-tab").classList.toggle("active", !create);
  $("create-tab").setAttribute("aria-selected", String(create));
  $("join-tab").setAttribute("aria-selected", String(!create));
}

async function responseJson(response) {
  let body;
  try { body = await response.json(); } catch (_) { body = {}; }
  if (!response.ok) {
    const detail = body.detail;
    const message = typeof detail === "string" ? detail : (body.message || `Request failed (${response.status}).`);
    throw new Error(message);
  }
  return body;
}

function useRoom(code, token, host) {
  if (!code || !token) throw new Error("The server did not provide room credentials.");
  roomCode = String(code).toUpperCase();
  playerToken = String(token);
  knownHost = host;
  roomState = null;
  waitingForAnswerAck = false;
  safeStore(roomCode, playerToken);
  $("connect-forms").hidden = true;
  $("room-controls").hidden = false;
  $("room-code").textContent = roomCode;
  $("room-pill").textContent = `Room ${roomCode}`;
  showMessage("");
  render();
  if (host) openDrawer("controls");
  else closeDrawer();
  connectSocket();
}

function leaveRoom() {
  connectionVersion++;
  if (reconnectTimer) clearTimeout(reconnectTimer);
  reconnectTimer = null;
  if (websocket) websocket.close();
  websocket = null;
  connected = false;
  roomCode = null;
  playerToken = null;
  roomState = null;
  knownHost = false;
  waitingForAnswerAck = false;
  clearStoredRoom();
  $("room-controls").hidden = true;
  $("connect-forms").hidden = false;
  $("answer-form").elements.answer.value = "";
  showMessage("");
  render();
  openDrawer("controls");
}

function socketUrl(code) {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${protocol}//${window.location.host}/ws/${encodeURIComponent(code)}`;
}

function connectSocket() {
  if (previewMode || !roomCode || !playerToken) return;
  const version = ++connectionVersion;
  if (reconnectTimer) clearTimeout(reconnectTimer);
  if (websocket) websocket.close();
  connected = false;
  $("connection-status").textContent = "Connecting to room…";
  let socket;
  try { socket = new WebSocket(socketUrl(roomCode)); }
  catch (_) { scheduleReconnect(version); return; }
  websocket = socket;
  socket.addEventListener("open", () => {
    if (version !== connectionVersion) return;
    connected = true;
    $("connection-status").textContent = "Connected · team state is live";
    socket.send(JSON.stringify({type: "hello", token: playerToken}));
    render();
  });
  socket.addEventListener("message", (event) => {
    if (version !== connectionVersion) return;
    let message;
    try { message = JSON.parse(event.data); } catch (_) { return; }
    if (message.type === "snapshot" && message.state) {
      const previousCurrent = findCurrentTurn(roomState);
      const answeredPreviousTurn = previousCurrent && message.state.turns?.[previousCurrent.index]?.answer;
      const previousPhase = roomState?.phase;
      const previousFeedbackStatus = roomState?.feedback_status;
      if (answeredPreviousTurn) {
        $("answer-form").elements.answer.value = "";
        if (waitingForAnswerAck && drawerMode === "controls") closeDrawer();
      }
      roomState = message.state;
      waitingForAnswerAck = false;
      showMessage("");
      render();
      if (roomState.phase === "retry" && previousPhase !== "retry" && isHost(roomState)) openDrawer("controls");
      if (roomState.phase === "complete" && previousPhase !== "complete") openDrawer("transcript");
      if (roomState.feedback_status === "ready" && previousFeedbackStatus !== "ready") openDrawer("transcript");
      if (roomState.feedback_status === "failed" && previousFeedbackStatus !== "failed" && isHost(roomState)) openDrawer("controls");
    } else if (message.type === "error") {
      waitingForAnswerAck = false;
      const error = String(message.message || "Room action failed.");
      if (error.startsWith("Room not found.") || error.startsWith("This room link is no longer valid.")) {
        leaveRoom();
        showMessage("That room is no longer available. Create or join a new room.");
        return;
      }
      showMessage(error);
      render();
    }
  });
  socket.addEventListener("close", () => {
    if (version !== connectionVersion) return;
    connected = false;
    waitingForAnswerAck = false;
    $("connection-status").textContent = "Disconnected · reconnecting…";
    render();
    scheduleReconnect(version);
  });
  socket.addEventListener("error", () => {
    // The close event handles retry; browsers do not expose useful error details.
  });
}

function scheduleReconnect(version) {
  if (version !== connectionVersion) return;
  reconnectTimer = setTimeout(() => connectSocket(), 1800);
}

function sendEvent(payload) {
  if (!websocket || websocket.readyState !== WebSocket.OPEN) {
    showMessage("Room connection is unavailable. Reconnecting now; try again shortly.");
    return false;
  }
  websocket.send(JSON.stringify(payload));
  return true;
}

function findCurrentTurn(state) {
  const turns = Array.isArray(state?.turns) ? state.turns : [];
  for (let i = turns.length - 1; i >= 0; i--) {
    if (turns[i].question && !turns[i].answer) return {turn: turns[i], index: i};
  }
  return null;
}

function isHost(state) {
  if (state && typeof state.self_is_host === "boolean") return state.self_is_host;
  if (state && Number.isInteger(state.self_seat)) {
    const self = (state.players || []).find((player) => player.seat === state.self_seat);
    if (self) return Boolean(self.is_host);
  }
  return knownHost;
}

function textElement(tag, className, value) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  element.textContent = value == null ? "" : String(value);
  return element;
}

function renderCoachingReport(state, container) {
  const status = state?.feedback_status;
  const report = state?.feedback;
  if (!status || status === "none") return;
  const section = document.createElement("section");
  section.className = "coaching-report";
  const heading = textElement("h3", "coaching-title", "Coaching Report");
  section.appendChild(heading);
  if (status === "generating") {
    section.appendChild(textElement("p", "coaching-preparing", "Preparing your coaching report…"));
    container.appendChild(section);
    return;
  }
  if (status === "failed") {
    section.appendChild(textElement("p", "coaching-error", "The coaching report could not be generated. The host can retry from Controls."));
    container.appendChild(section);
    return;
  }
  if (status !== "ready" || !report) return;
  section.appendChild(textElement("p", "coaching-summary", report.summary));
  if (report.strengths && report.strengths.length) {
    const block = document.createElement("div");
    block.className = "coaching-section";
    block.appendChild(textElement("h4", "coaching-section-title coaching-strength-title", "Strengths"));
    report.strengths.forEach((item) => {
      const p = textElement("p", "coaching-item coaching-strength", item.text);
      p.dataset.turn = String(item.turn + 1);
      block.appendChild(p);
    });
    section.appendChild(block);
  }
  if (report.improvements && report.improvements.length) {
    const block = document.createElement("div");
    block.className = "coaching-section";
    block.appendChild(textElement("h4", "coaching-section-title coaching-improve-title", "Areas to Improve"));
    report.improvements.forEach((item) => {
      const p = textElement("p", "coaching-item coaching-improve", item.text);
      p.dataset.turn = String(item.turn + 1);
      block.appendChild(p);
    });
    section.appendChild(block);
  }
  if (report.next_step) {
    const block = document.createElement("div");
    block.className = "coaching-section";
    block.appendChild(textElement("h4", "coaching-section-title", "Next Step"));
    block.appendChild(textElement("p", "coaching-item", report.next_step));
    section.appendChild(block);
  }
  container.appendChild(section);
}

function renderTranscript(state) {
  const transcript = $("transcript");
  const turns = Array.isArray(state?.turns) ? state.turns : [];
  const answered = turns.filter((turn) => turn.answer).length;
  $("transcript-count").textContent = `${answered} / 4 answered`;
  transcript.replaceChildren();
  if (!turns.length && (!state?.feedback_status || state.feedback_status === "none")) {
    transcript.className = "transcript-empty";
    transcript.textContent = "Questions and team answers will appear here.";
    return;
  }
  transcript.className = "transcript-list";
  renderCoachingReport(state, transcript);
  turns.forEach((turn, index) => {
    const card = textElement("article", "turn-card", "");
    card.appendChild(textElement("h3", "", `QUESTION ${index + 1} · ${turn.panelist || "Panelist"}`));
    card.appendChild(textElement("p", "", turn.question || "Question being prepared…"));
    if (turn.filename && Number.isInteger(turn.evidence_line)) {
      card.appendChild(textElement("p", "citation", `${turn.filename}:${turn.evidence_line} — ${turn.evidence_text || ""}`));
    }
    if (turn.answer) {
      const answerer = turn.answered_by ? ` · ${turn.answered_by}` : "";
      card.appendChild(textElement("p", "answer", `Team answer${answerer}: ${turn.answer}`));
    }
    transcript.appendChild(card);
  });
}

function renderQuestionCard(state) {
  const current = findCurrentTurn(state);
  const phase = state?.phase || "none";
  const feedbackStatus = state?.feedback_status || "none";
  const answered = (state?.turns || []).filter((turn) => turn.answer).length;
  let name = "Your defense begins here";
  let question = "Create or join a room to begin your defense.";
  let number = "READY";
  let status = "Create or join a room to begin.";
  let source = null;
  let evidence = null;
  if (phase === "lobby") {
    name = "Your team is gathering";
    question = "The host starts the defense when everyone is ready.";
    status = isHost(state) ? "Open Controls to start the defense." : "Waiting for the host to start.";
  } else if (phase === "generating") {
    name = state.active_panelist || "The panel";
    question = "Preparing the next question…";
    number = `QUESTION ${Math.min(answered + 1, 4)} OF 4`;
    status = "Your team will see the same question when it is ready.";
  } else if (phase === "question" && current) {
    name = current.turn.panelist;
    question = current.turn.question;
    number = `QUESTION ${current.index + 1} OF 4`;
    source = `${current.turn.filename}:${current.turn.evidence_line}`;
    evidence = current.turn.evidence_text;
    status = "Any teammate can answer; the first valid submission counts.";
  } else if (phase === "retry") {
    name = state.active_panelist || "The panel";
    question = "The next question could not be generated.";
    number = `QUESTION ${Math.min(answered + 1, 4)} OF 4`;
    status = state.error || "The host can retry. Previous answers are saved.";
  } else if (phase === "complete") {
    if (feedbackStatus === "generating") {
      name = "Preparing coaching report";
      question = "Your team's coaching report is being prepared. It will appear in the Transcript.";
      number = "4 OF 4";
      status = "This may take a few seconds.";
    } else if (feedbackStatus === "failed") {
      name = "Defense complete";
      question = "All four questions have been answered. The coaching report could not be generated.";
      number = "4 OF 4";
      status = state.error || (isHost(state) ? "Open Controls to retry the coaching report." : "The host can retry the coaching report.");
    } else {
      name = "Defense complete";
      question = "All four questions have been answered. Open Transcript to review your coaching report.";
      number = "4 OF 4";
      status = "The complete transcript and coaching report remain in this room until the server restarts.";
    }
  }
  const questionChanged = $("question-text").textContent !== question;
  $("panelist-name").textContent = name;
  $("question-number").textContent = number;
  $("question-text").textContent = question;
  $("source-block").hidden = source === null;
  $("source-ref").textContent = source || "";
  $("evidence-text").textContent = evidence == null ? "" : String(evidence);
  $("arena-status").textContent = status;
  $("answer-open").hidden = previewMode || phase !== "question" || !current;
  $("answer-open").disabled = !connected;
  if (questionChanged) {
    $("question-content").scrollTop = 0;
    $("source-block").scrollTop = 0;
  }
}

function render() {
  const state = roomState;
  if (scene) scene.renderState(state);
  renderTranscript(state);
  renderQuestionCard(state);
  const turns = Array.isArray(state?.turns) ? state.turns : [];
  const answered = turns.filter((turn) => turn.answer).length;
  const current = findCurrentTurn(state);
  const host = isHost(state);
  const phase = state?.phase || "none";
  const feedbackStatus = state?.feedback_status || "none";
  $("room-pill").textContent = state ? `Room ${state.room_code || roomCode || "—"}` : "No room yet";
  $("round-indicator").textContent = phase === "complete" ? "COMPLETE" : state ? `${answered} / 4 ANSWERED` : "READY";
  if (!state) return;
  $("room-code").textContent = state.room_code || roomCode || "—";
  $("role-label").textContent = previewMode ? "Visual preview" : (host ? "Host · share the code with your team" : "Defender · waiting with your team");
  $("host-controls").hidden = previewMode || !host;
  $("leave-button").hidden = previewMode;
  $("start-button").hidden = phase !== "lobby";
  $("retry-button").hidden = phase !== "retry";
  $("retry-coaching-button").hidden = phase !== "complete" || feedbackStatus !== "failed";
  $("restart-button").hidden = phase === "lobby";
  $("start-button").disabled = !connected;
  $("retry-button").disabled = !connected;
  $("retry-coaching-button").disabled = !connected;
  $("restart-button").disabled = !connected;
  $("answer-form").hidden = previewMode || phase !== "question" || !current;
  $("answer-form").querySelector("button[type=submit]").disabled = !connected || waitingForAnswerAck;
  $("wait-message").textContent = previewMode ? "Preview mode does not send answers." :
    phase === "lobby" ? (host ? "Start when your team is ready." : "The host will start the defense.") :
    phase === "generating" ? "The panelist is preparing the next question…" :
    phase === "retry" ? (host ? "Question generation failed. Your team's previous answer was saved; retry when ready." : "The host can retry the next question. Previous answers are saved.") :
    phase === "complete" && feedbackStatus === "generating" ? "Preparing your team's coaching report…" :
    phase === "complete" && feedbackStatus === "failed" ? (host ? "Coaching report failed. Use Retry coaching report to try again." : "Coaching report failed. The host can retry.") :
    phase === "complete" ? "The four-question defense is complete. Open Transcript for your coaching report." : "";
}

class DefenseScene extends Phaser.Scene {
  constructor() { super("DefenseScene"); }

  create() {
    scene = this;
    this.makeTextures();
    this.background = this.add.graphics();
    this.panelSeats = Array.from({length: 4}, (_, index) => ({
      ring: this.add.circle(0, 0, 40, 0x5c2737, .62).setStrokeStyle(2, 0xe9747c, .8),
      glow: this.add.circle(0, 0, 46).setStrokeStyle(4, 0xffd26d, 1).setVisible(false),
      sprite: index === 1 || index === 2 ? this.add.sprite(0, 0, "panelist") : null,
      label: this.add.text(0, 0, index === 1 ? "Technical Architect" : index === 2 ? "Security Reviewer" : "Empty panel seat", {
        fontFamily: "Arial, sans-serif", color: index === 1 || index === 2 ? "#ffe0e0" : "#91a1b3", fontStyle: "bold", align: "center",
      }).setOrigin(.5),
    }));
    this.defenderSeats = Array.from({length: 4}, (_, index) => ({
      ring: this.add.circle(0, 0, 40, 0x1e527b, .55).setStrokeStyle(2, 0x55a9e6, .8),
      sprite: this.add.sprite(0, 0, "defender").setAlpha(.22),
      label: this.add.text(0, 0, `Open seat ${index + 1}`, {
        fontFamily: "Arial, sans-serif", color: "#9cb7d3", fontStyle: "bold", align: "center",
      }).setOrigin(.5),
    }));
    this.cue = this.add.graphics();
    this.cueText = this.add.text(0, 0, "", {
      fontFamily: "Arial, sans-serif", color: "#16324b", fontStyle: "bold", align: "center",
    }).setOrigin(.5);
    this.scale.on("resize", this.layout, this);
    this.layout();
    this.renderState(roomState);
  }

  makeTextures() {
    for (const [name, jacket, trim] of [["panelist", 0xe66572, 0xffced0], ["defender", 0x4baef2, 0xc3ebff]]) {
      const g = this.make.graphics({x: 0, y: 0}, false);
      g.fillStyle(0x071526, .25); g.fillEllipse(43, 78, 60, 10);
      g.fillStyle(jacket); g.fillRoundedRect(13, 37, 60, 42, 12);
      g.fillStyle(trim); g.fillTriangle(36, 38, 50, 38, 43, 57);
      g.fillStyle(0xe9ad82); g.fillCircle(43, 25, 21);
      g.fillStyle(0x19273d); g.fillEllipse(43, 13, 44, 19);
      g.fillCircle(37, 26, 2); g.fillCircle(49, 26, 2);
      g.lineStyle(2, 0x855545); g.lineBetween(37, 34, 49, 34);
      g.generateTexture(name, 86, 84);
      g.destroy();
    }
  }

  layout() {
    if (!this.panelSeats) return;
    const width = this.scale.width;
    const height = this.scale.height;
    const compact = height < 320;
    const radius = Phaser.Math.Clamp(height * .095, 24, 63);
    const panelY = compact ? Math.max(66, height * .31) : Math.max(130, height * .24);
    const defenderY = compact ? height - 53 : height * .73;
    const labelSize = compact ? "10px" : "15px";
    const labelWidth = width * .22;
    this.background.clear();
    this.background.fillStyle(0x0d2238, 1).fillRect(0, 0, width, height);
    this.background.fillStyle(0x183651, 1).fillRoundedRect(12, compact ? 39 : 72, width - 24, height - (compact ? 45 : 82), 15);
    this.background.lineStyle(2, 0x42688a, .75).strokeRoundedRect(12, compact ? 39 : 72, width - 24, height - (compact ? 45 : 82), 15);
    this.background.lineStyle(2, 0x3b6382, .8).lineBetween(30, (panelY + defenderY) / 2, width - 30, (panelY + defenderY) / 2);
    for (let index = 0; index < 4; index++) {
      const x = width * (.14 + index * .24);
      const panel = this.panelSeats[index];
      panel.ring.setPosition(x, panelY).setRadius(radius);
      panel.glow.setPosition(x, panelY).setRadius(radius + 6);
      if (panel.sprite) panel.sprite.setPosition(x, panelY + 3).setScale(radius * 1.55 / 86);
      panel.label.setPosition(x, panelY + radius + (compact ? 9 : 13)).setFontSize(labelSize).setWordWrapWidth(labelWidth);
      const defender = this.defenderSeats[index];
      defender.ring.setPosition(x, defenderY).setRadius(radius);
      defender.sprite.setPosition(x, defenderY + 3).setScale(radius * 1.55 / 86);
      defender.label.setPosition(x, defenderY + radius + (compact ? 9 : 13)).setFontSize(labelSize).setWordWrapWidth(labelWidth);
    }
    this.cueText.setFontSize(compact ? "12px" : "20px");
    this.renderCue(roomState);
  }

  renderCue(state) {
    const height = this.scale.height;
    const width = this.scale.width;
    const compact = height < 320;
    const panelY = compact ? Math.max(66, height * .31) : Math.max(130, height * .24);
    const defenderY = compact ? height - 53 : height * .73;
    const cueY = (panelY + defenderY) / 2 + (compact ? 8 : 0);
    const cueWidth = Math.min(width * .48, compact ? 370 : 530);
    const cueHeight = compact ? 29 : 68;
    const activeName = state?.active_panelist || findCurrentTurn(state)?.turn.panelist;
    const activeIndex = activeName === panelNames[0] ? 1 : activeName === panelNames[1] ? 2 : -1;
    let cue = "Create or join a room";
    if (state?.phase === "lobby") cue = "Your team is gathering";
    else if (state?.phase === "generating") cue = `${activeName || "The panel"} is preparing a question`;
    else if (state?.phase === "question") cue = `${activeName || "The panel"} is asking`;
    else if (state?.phase === "retry") cue = "Question paused · host can retry";
    else if (state?.phase === "complete") cue = "Defense complete";
    this.cue.clear();
    this.cue.fillStyle(0xe7f4ff, 1).fillRoundedRect(width / 2 - cueWidth / 2, cueY - cueHeight / 2, cueWidth, cueHeight, compact ? 9 : 15);
    this.cue.lineStyle(2, 0x8fc8e9, 1).strokeRoundedRect(width / 2 - cueWidth / 2, cueY - cueHeight / 2, cueWidth, cueHeight, compact ? 9 : 15);
    if (activeIndex >= 0 && !compact && state?.phase !== "complete") {
      const x = width * (.14 + activeIndex * .24);
      this.cue.fillStyle(0xe7f4ff, 1).fillTriangle(x - 11, cueY - cueHeight / 2 + 1, x + 11, cueY - cueHeight / 2 + 1, x, cueY - cueHeight / 2 - 12);
    }
    this.cueText.setPosition(width / 2, cueY).setWordWrapWidth(cueWidth - 20).setText(cue);
    this.panelSeats.forEach((seat, index) => seat.glow.setVisible(index === activeIndex && state?.phase !== "complete"));
  }

  renderState(state) {
    if (!this.panelSeats) return;
    const players = Array.isArray(state?.players) ? state.players : [];
    for (let index = 0; index < 4; index++) {
      const seat = this.defenderSeats[index];
      const player = players.find((person) => person.seat === index);
      seat.sprite.setAlpha(player ? (player.online ? 1 : .45) : .22);
      seat.label.setText(player ? `${player.name || "Defender"}${player.is_host ? " ★" : ""}${player.online ? "" : " (offline)"}` : `Open seat ${index + 1}`);
      seat.label.setColor(player ? "#cdeeff" : "#91a6bd");
    }
    this.renderCue(state);
  }
}

function startGame() {
  if (typeof Phaser === "undefined") {
    $("game").textContent = "The game could not load. Check the Phaser connection and refresh.";
    return;
  }
  new Phaser.Game({
    type: Phaser.AUTO,
    parent: "game",
    width: 960,
    height: 540,
    backgroundColor: "#0d2238",
    scale: {mode: Phaser.Scale.RESIZE},
    scene: DefenseScene,
  });
}

$("controls-toggle").addEventListener("click", () => openDrawer("controls"));
$("transcript-toggle").addEventListener("click", () => openDrawer("transcript"));
$("drawer-close").addEventListener("click", closeDrawer);
$("drawer-scrim").addEventListener("click", closeDrawer);
$("answer-open").addEventListener("click", () => openDrawer("controls", true));
document.addEventListener("keydown", (event) => {
  if ($("drawer").hidden) return;
  if (event.key === "Escape") { event.preventDefault(); closeDrawer(); return; }
  if (event.key !== "Tab") return;
  const focusable = [...$("drawer").querySelectorAll("button:not([disabled]), input:not([disabled]), textarea:not([disabled])")]
    .filter((element) => !element.closest("[hidden]") && element.getClientRects().length);
  if (!focusable.length) return;
  const first = focusable[0];
  const last = focusable[focusable.length - 1];
  if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
  else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
});
$("create-tab").addEventListener("click", () => selectTab("create"));
$("join-tab").addEventListener("click", () => selectTab("join"));

$("create-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  showMessage("");
  const form = event.currentTarget;
  setButtonBusy(form, true);
  try {
    const response = await fetch("/api/rooms", {method: "POST", body: new FormData(form)});
    const body = await responseJson(response);
    useRoom(body.room_code, body.player_token, true);
  } catch (error) {
    showMessage(error.message || "Could not create the room.");
  } finally {
    form.elements.host_passcode.value = "";
    setButtonBusy(form, false);
  }
});

$("join-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  showMessage("");
  const form = event.currentTarget;
  setButtonBusy(form, true);
  try {
    const code = form.elements.room_code.value.trim().toUpperCase();
    const name = form.elements.name.value.trim();
    const response = await fetch(`/api/rooms/${encodeURIComponent(code)}/join`, {
      method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({name}),
    });
    const body = await responseJson(response);
    useRoom(body.room_code, body.player_token, false);
  } catch (error) {
    showMessage(error.message || "Could not join the room.");
  } finally {
    setButtonBusy(form, false);
  }
});

$("leave-button").addEventListener("click", leaveRoom);
$("start-button").addEventListener("click", () => { if (sendEvent({type: "start"})) closeDrawer(); });
$("retry-button").addEventListener("click", () => { if (sendEvent({type: "retry"})) closeDrawer(); });
$("retry-coaching-button").addEventListener("click", () => { if (sendEvent({type: "retry_coaching"})) closeDrawer(); });
$("restart-button").addEventListener("click", () => {
  if (sendEvent({type: "restart"})) {
    $("answer-form").elements.answer.value = "";
    closeDrawer();
  }
});
$("answer-form").addEventListener("submit", (event) => {
  event.preventDefault();
  const current = findCurrentTurn(roomState);
  if (!current) return;
  const answer = event.currentTarget.elements.answer.value.trim();
  if (!answer) { showMessage("Write an answer before submitting."); return; }
  if (sendEvent({type: "submit_answer", turn: current.index, answer})) {
    waitingForAnswerAck = true;
    render();
  }
});

if (previewMode) {
  $("preview-banner").hidden = false;
  $("connect-forms").hidden = true;
  $("room-controls").hidden = false;
  $("connection-status").textContent = "Offline layout preview";
  roomState = previewState;
  roomCode = "PREVIEW";
  knownHost = true;
} else {
  const stored = readStoredRoom();
  if (stored) useRoom(stored.code, stored.token, false);
  else openDrawer("controls");
}
startGame();
render();

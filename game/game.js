"use strict";

const previewMode = new URLSearchParams(window.location.search).get("preview") === "1";
const $ = (id) => document.getElementById(id);
const panelNames = ["Technical Architect", "Security Reviewer"];
const seatX = [148, 370, 590, 812];
const previewState = {
  room_code: "PREVIEW",
  phase: "question",
  self_seat: 0,
  players: [
    {seat: 0, name: "You", online: true, is_host: true},
    {seat: 1, name: "Teammate A", online: true, is_host: false},
    {seat: 2, name: "Teammate B", online: true, is_host: false},
    {seat: 3, name: "Teammate C", online: false, is_host: false},
  ],
  turns: [{
    panelist: "Technical Architect",
    question: "Why does reserve() open a new SQLite connection for every reservation?",
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

function showMessage(message) {
  $("message").textContent = message;
  $("message").hidden = !message;
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
  $("room-pill").textContent = "No room yet";
  $("answer-form").elements.answer.value = "";
  showMessage("");
  render();
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
      const answeredPreviousTurn = previousCurrent &&
        message.state.turns?.[previousCurrent.index]?.answer;
      if (answeredPreviousTurn) $("answer-form").elements.answer.value = "";
      roomState = message.state;
      waitingForAnswerAck = false;
      showMessage("");
      render();
    } else if (message.type === "error") {
      waitingForAnswerAck = false;
      showMessage(String(message.message || "Room action failed."));
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

function renderTranscript(state) {
  const transcript = $("transcript");
  const turns = Array.isArray(state?.turns) ? state.turns : [];
  const answered = turns.filter((turn) => turn.answer).length;
  $("transcript-count").textContent = `${answered} / 4 answered`;
  transcript.replaceChildren();
  if (!turns.length) {
    transcript.className = "transcript-empty";
    transcript.textContent = "Questions and team answers will appear here.";
    return;
  }
  transcript.className = "transcript-list";
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

function render() {
  const state = roomState;
  if (scene) scene.renderState(state);
  renderTranscript(state);
  if (!state) {
    $("arena-status").textContent = previewMode ? "Mock room preview. Create a real room to play." : "Create or join a room to begin.";
    $("round-indicator").textContent = "Waiting for a room";
    return;
  }
  const turns = Array.isArray(state.turns) ? state.turns : [];
  const current = findCurrentTurn(state);
  const answered = turns.filter((turn) => turn.answer).length;
  const host = isHost(state);
  const phase = state.phase || "lobby";
  $("room-pill").textContent = `Room ${state.room_code || roomCode || "—"}`;
  $("room-code").textContent = state.room_code || roomCode || "—";
  $("role-label").textContent = previewMode ? "Visual preview" : (host ? "Host · share the code with your team" : "Defender · waiting with your team");
  $("host-controls").hidden = previewMode || !host;
  $("leave-button").hidden = previewMode;
  $("start-button").hidden = phase !== "lobby";
  $("retry-button").hidden = phase !== "retry";
  $("restart-button").hidden = phase === "lobby";
  $("start-button").disabled = !connected;
  $("retry-button").disabled = !connected;
  $("restart-button").disabled = !connected;
  $("answer-form").hidden = previewMode || phase !== "question" || !current;
  $("answer-form").querySelector("button[type=submit]").disabled = !connected || waitingForAnswerAck;
  $("wait-message").textContent = previewMode ? "Preview mode does not send answers." :
    phase === "lobby" ? (host ? "Start when your team is ready." : "The host will start the defense.") :
    phase === "generating" ? "The panelist is preparing the next question…" :
    phase === "retry" ? (host ? "Question generation failed. Your team's previous answer was saved; retry when ready." : "The host can retry the next question. Previous answers are saved.") :
    phase === "complete" ? "The four-question defense is complete." : "";
  $("arena-status").textContent = phase === "question" && current ?
    `Question ${current.index + 1} of 4 · ${current.turn.panelist} is asking.` :
    phase === "generating" ? "Preparing the next panel question…" :
    phase === "retry" ? "Generation paused. The host can retry without losing the previous answer." :
    phase === "complete" ? "Defense complete · all four questions answered." :
    "Waiting for the host to start the defense.";
  $("round-indicator").textContent = phase === "complete" ? "COMPLETE" : `${answered} / 4 ANSWERED`;
  if (state.error && phase === "retry") showMessage(String(state.error));
}

class DefenseScene extends Phaser.Scene {
  constructor() { super("DefenseScene"); }

  create() {
    scene = this;
    this.makeTextures();
    this.add.rectangle(480, 270, 960, 540, 0x12253d);
    this.add.rectangle(480, 270, 942, 522, 0x152b44).setStrokeStyle(2, 0x365674);
    this.add.rectangle(480, 270, 904, 478, 0x132840).setStrokeStyle(1, 0x2c4a69);
    this.add.text(480, 29, "THE PANEL", {fontFamily: "Arial, sans-serif", fontSize: "15px", color: "#fda8a8", fontStyle: "bold", letterSpacing: 4}).setOrigin(.5);
    this.add.text(480, 507, "YOUR TEAM", {fontFamily: "Arial, sans-serif", fontSize: "15px", color: "#8ccfff", fontStyle: "bold", letterSpacing: 4}).setOrigin(.5);
    this.add.rectangle(480, 359, 860, 2, 0x315371);

    this.panelSeats = seatX.map((x, index) => {
      const circle = this.add.circle(x, 110, 52, 0x783340, .24).setStrokeStyle(2, 0xe9747c, .55);
      const glow = this.add.circle(x, 110, 58).setStrokeStyle(4, 0xffcc69, 1).setVisible(false);
      const sprite = index === 1 || index === 2 ? this.add.sprite(x, 113, "panelist") : null;
      if (sprite) sprite.setScale(.9);
      const label = this.add.text(x, 170, index === 1 ? "Technical Architect" : index === 2 ? "Security Reviewer" : "Empty panel seat", {
        fontFamily: "Arial, sans-serif", fontSize: "14px", color: index === 1 || index === 2 ? "#ffe0e0" : "#8192a7", fontStyle: "bold", align: "center", wordWrap: {width: 200},
      }).setOrigin(.5);
      return {circle, glow, sprite, label};
    });

    this.defenderSeats = seatX.map((x, index) => {
      const circle = this.add.circle(x, 423, 52, 0x24547b, .3).setStrokeStyle(2, 0x55a9e6, .55);
      const sprite = this.add.sprite(x, 426, "defender").setScale(.9).setAlpha(.25);
      const label = this.add.text(x, 482, `Open seat ${index + 1}`, {
        fontFamily: "Arial, sans-serif", fontSize: "14px", color: "#9cb7d3", fontStyle: "bold", align: "center", wordWrap: {width: 200},
      }).setOrigin(.5);
      return {circle, sprite, label};
    });

    this.bubble = this.add.graphics();
    this.questionText = this.add.text(181, 216, "", {
      fontFamily: "Arial, sans-serif", fontSize: "21px", color: "#14243c", fontStyle: "bold", lineSpacing: 4, wordWrap: {width: 600},
    });
    this.questionText.setMaxLines(3);
    this.citationText = this.add.text(181, 310, "", {
      fontFamily: "Arial, sans-serif", fontSize: "14px", color: "#345d7b", wordWrap: {width: 600},
    });
    this.citationText.setMaxLines(2);
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

  renderState(state) {
    if (!this.panelSeats) return;
    const players = Array.isArray(state?.players) ? state.players : [];
    for (let index = 0; index < 4; index++) {
      const seat = this.defenderSeats[index];
      const player = players.find((person) => person.seat === index);
      seat.sprite.setAlpha(player ? (player.online ? 1 : .45) : .22);
      seat.label.setText(player ? `${player.name || "Defender"}${player.is_host ? " ★" : ""}${player.online ? "" : " (offline)"}` : `Open seat ${index + 1}`);
      seat.label.setColor(player ? "#cdeeff" : "#8299b3");
    }
    const current = findCurrentTurn(state);
    const activeName = state?.active_panelist || current?.turn.panelist;
    const activeIndex = activeName === panelNames[0] ? 1 : activeName === panelNames[1] ? 2 : -1;
    this.panelSeats.forEach((seat, index) => seat.glow.setVisible(index === activeIndex && state?.phase !== "complete"));
    this.bubble.clear();
    this.bubble.fillStyle(0xe8f4ff, 1);
    this.bubble.fillRoundedRect(155, 196, 650, 155, 15);
    this.bubble.lineStyle(3, 0x8fc8e9, 1);
    this.bubble.strokeRoundedRect(155, 196, 650, 155, 15);
    if (activeIndex > -1) {
      const x = seatX[activeIndex];
      this.bubble.fillStyle(0xe8f4ff, 1);
      this.bubble.fillTriangle(x - 16, 197, x + 16, 197, x, 178);
    }
    let title = "Create or join a room to start your defense.";
    let citation = "Panelists will ask code-grounded questions here.";
    if (state?.phase === "question" && current) {
      title = current.turn.question;
      citation = `${current.turn.filename}:${current.turn.evidence_line}  ${current.turn.evidence_text || ""}`;
    } else if (state?.phase === "generating") {
      title = `${activeName || "The panel"} is preparing a question…`;
      citation = "Your team will see the same question when it is ready.";
    } else if (state?.phase === "retry") {
      title = "The next question could not be generated.";
      citation = "The host can retry. Your previous answer is saved.";
    } else if (state?.phase === "complete") {
      title = "Defense complete. Well played, team.";
      citation = "Review the four questions and answers below.";
    } else if (state?.phase === "lobby") {
      title = "The team is gathering.";
      citation = "The host starts when everyone is ready.";
    }
    this.questionText.setText(String(title));
    this.citationText.setText(String(citation));
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
    backgroundColor: "#12253d",
    scale: {mode: Phaser.Scale.FIT, autoCenter: Phaser.Scale.CENTER_BOTH},
    scene: DefenseScene,
  });
}

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
$("start-button").addEventListener("click", () => sendEvent({type: "start"}));
$("retry-button").addEventListener("click", () => sendEvent({type: "retry"}));
$("restart-button").addEventListener("click", () => {
  if (sendEvent({type: "restart"})) $("answer-form").elements.answer.value = "";
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
}
startGame();
render();

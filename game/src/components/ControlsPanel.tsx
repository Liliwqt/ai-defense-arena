import { useState } from "react";
import type { RoomState } from "../types";

interface ControlsPanelProps {
  roomState: RoomState | null;
  connected: boolean;
  previewMode: boolean;
  onUseRoom: (code: string, token: string, host: boolean) => void;
  onLeaveRoom: () => void;
  onSendEvent: (payload: Record<string, unknown>) => boolean;
  onCloseDrawer: () => void;
  showMessage: (msg: string) => void;
}

async function responseJson(response: Response): Promise<Record<string, unknown>> {
  let body: Record<string, unknown> = {};
  try {
    body = (await response.json()) as Record<string, unknown>;
  } catch {
    body = {};
  }
  if (!response.ok) {
    const detail = body.detail;
    const message =
      typeof detail === "string"
        ? detail
        : (body.message as string | undefined) ??
          `Request failed (${response.status}).`;
    throw new Error(message);
  }
  return body;
}

export function ControlsPanel({
  roomState,
  connected,
  previewMode,
  onUseRoom,
  onLeaveRoom,
  onSendEvent,
  onCloseDrawer,
  showMessage,
}: ControlsPanelProps) {
  const [activeTab, setActiveTab] = useState<"create" | "join">("create");
  const [createBusy, setCreateBusy] = useState(false);
  const [joinBusy, setJoinBusy] = useState(false);
  const [defenseType, setDefenseType] = useState<"code" | "research" | "mixed">("code");

  const inRoom = roomState !== null || !!connected;
  const phase = roomState?.phase ?? "none";
  const feedbackStatus = roomState?.feedback_status ?? "none";
  const isHost = roomState?.self_is_host ?? false;
  const roomCode = roomState?.room_code ?? null;

  async function handleCreate(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    showMessage("");
    setCreateBusy(true);
    const form = e.currentTarget;
    try {
      const resp = await fetch("/api/rooms", {
        method: "POST",
        body: new FormData(form),
      });
      const body = await responseJson(resp);
      onUseRoom(body.room_code as string, body.player_token as string, true);
    } catch (err) {
      showMessage((err as Error).message ?? "Could not create the room.");
    } finally {
      setCreateBusy(false);
    }
  }

  async function handleJoin(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    showMessage("");
    setJoinBusy(true);
    const form = e.currentTarget;
    try {
      const code = (
        form.elements.namedItem("room_code") as HTMLInputElement
      ).value
        .trim()
        .toUpperCase();
      const name = (form.elements.namedItem("name") as HTMLInputElement).value.trim();
      const resp = await fetch(`/api/rooms/${encodeURIComponent(code)}/join`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name }),
      });
      const body = await responseJson(resp);
      onUseRoom(body.room_code as string, body.player_token as string, false);
    } catch (err) {
      showMessage((err as Error).message ?? "Could not join the room.");
    } finally {
      setJoinBusy(false);
    }
  }

  function handleStart() {
    if (onSendEvent({ type: "start" })) onCloseDrawer();
  }
  function handleRetry() {
    if (onSendEvent({ type: "retry" })) onCloseDrawer();
  }
  function handleRetryCoaching() {
    if (onSendEvent({ type: "retry_coaching" })) onCloseDrawer();
  }
  function handleRestart() {
    if (onSendEvent({ type: "restart" })) onCloseDrawer();
  }

  function handleSetupTabKey(event: React.KeyboardEvent<HTMLButtonElement>) {
    if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") return;
    event.preventDefault();
    const next = activeTab === "create" ? "join" : "create";
    setActiveTab(next);
    const tabs = event.currentTarget.parentElement?.querySelectorAll<HTMLButtonElement>("[role=tab]");
    tabs?.[next === "create" ? 0 : 1]?.focus();
  }

  const tabClass = (active: boolean) => `setup-tab${active ? " is-selected" : ""}`;
  const inputClass = "setup-input";
  const primaryBtn = "button-primary";
  const secondaryBtn = "button-secondary";

  const waitText =
    previewMode
      ? "Preview mode does not send answers."
      : phase === "lobby"
        ? isHost
          ? "Start when your team is ready."
          : "The host will start the defense."
        : phase === "generating"
          ? "The panelist is preparing the next question…"
          : phase === "retry"
            ? isHost
              ? "Question generation failed. Your team's previous answer was saved; retry when ready."
              : "The host can retry the next question. Previous answers are saved."
            : phase === "complete" && feedbackStatus === "generating"
              ? "Preparing your team's coaching report…"
              : phase === "complete" && feedbackStatus === "failed"
                ? isHost
                  ? "Coaching report failed. Use Retry coaching report to try again."
                  : "Coaching report failed. The host can retry."
                : phase === "complete"
                  ? "The defense is complete. Open Transcript for your coaching report."
                  : "";

  return (
    <div className="grid gap-[15px]">
      {/* Connect forms — shown before joining */}
      {!inRoom && !previewMode && (
        <div>
          {/* Tab switcher */}
          <div className="setup-tabs" role="tablist" aria-label="Room setup">
            <button
              type="button"
              className={tabClass(activeTab === "create")}
              role="tab" aria-controls="create-form" tabIndex={activeTab === "create" ? 0 : -1}
              onKeyDown={handleSetupTabKey}
              aria-selected={activeTab === "create"}
              onClick={() => setActiveTab("create")}
            >
              Create room
            </button>
            <button
              type="button"
              className={tabClass(activeTab === "join")}
              role="tab" aria-controls="join-form" tabIndex={activeTab === "join" ? 0 : -1}
              onKeyDown={handleSetupTabKey}
              aria-selected={activeTab === "join"}
              onClick={() => setActiveTab("join")}
            >
              Join room
            </button>
          </div>

          {activeTab === "create" && (
            <form id="create-form" role="tabpanel" onSubmit={handleCreate} className="grid gap-[15px]">
              <label className="setup-label">
                Your name
                <input name="host_name" maxLength={24} autoComplete="name" required placeholder="Your name" className={inputClass} />
              </label>
              <label className="setup-label">
                Host passcode
                <input name="host_passcode" type="password" autoComplete="off" required placeholder="Enter the host passcode" className={inputClass} />
              </label>
              <label className="setup-label">
                Defense type
                <select name="defense_type" value={defenseType} onChange={(event) => setDefenseType(event.target.value as typeof defenseType)} className={inputClass}>
                  <option value="code">Code project</option>
                  <option value="research">Research paper</option>
                  <option value="mixed">Research + code</option>
                </select>
              </label>
              {defenseType !== "code" && <label className="setup-label">
                Research stage
                <select name="research_stage" defaultValue="infer" className={inputClass}>
                  <option value="infer">Let AI infer</option>
                  <option value="proposal">Proposal</option>
                  <option value="completed">Completed study</option>
                </select>
              </label>}
              {defenseType !== "research" && <label className="setup-label">
                Project source files or ZIP
                <input name="files" type="file" multiple required accept=".zip,.md,.txt,.py,.js,.jsx,.ts,.tsx,.json,.html,.css,.java,.go,.rs,.sql,.yaml,.yml,.toml,.sh,.c,.cpp,.h,.hpp,.kt,.swift,.rb,.php,.vue,.svelte" className={`${inputClass} text-[0.77rem] leading-tight`} />
              </label>}
              {defenseType !== "code" && <label className="setup-label">
                Research documents
                <input name="research_files" type="file" multiple required accept=".pdf,.docx,.txt,.md" className={`${inputClass} text-[0.77rem] leading-tight`} />
              </label>}
              <p className="control-help">
                Research papers: text-based PDF, DOCX, TXT, or Markdown. PDF pages must contain readable text.
              </p>
              <button type="submit" disabled={createBusy} className={primaryBtn}>
                {createBusy ? "Creating…" : "Create defense room"}
              </button>
            </form>
          )}

          {activeTab === "join" && (
            <form id="join-form" role="tabpanel" onSubmit={handleJoin} className="grid gap-[15px]">
              <label className="setup-label">
                Room code
                <input name="room_code" maxLength={12} autoComplete="off" required placeholder="Enter room code" className={inputClass} />
              </label>
              <label className="setup-label">
                Your name
                <input name="name" maxLength={24} autoComplete="name" required placeholder="Your name" className={inputClass} />
              </label>
              <button type="submit" disabled={joinBusy} className={primaryBtn}>
                {joinBusy ? "Joining…" : "Join team"}
              </button>
            </form>
          )}
        </div>
      )}

      {/* In-room controls */}
      {(inRoom || previewMode) && (
        <div className="grid gap-[15px]">
            <div className="room-code-card">
            <span className="room-code-kicker">
              ROOM CODE
            </span>
            <strong className="room-code-value">
              {roomCode ?? "—"}
            </strong>
            <span className="room-code-hint">
              {previewMode
                ? "Visual preview"
                : isHost
                  ? "Host · share the code with your team"
                  : "Defender · waiting with your team"}
            </span>
          </div>

          {roomState?.phase === "lobby" && roomState.accepted_files && (
            <div className="accepted-files" aria-label="Accepted files">
              <strong>Accepted files · {roomState.defense_type === "code" ? "Code project" : roomState.defense_type === "mixed" ? "Research + code" : "Research paper"}</strong>
              <ul className="mt-2 pl-5">{roomState.accepted_files.map((file) => <li key={file.name}>{file.name}{file.detail ? ` · ${file.detail}` : ""}</li>)}</ul>
            </div>
          )}
          <p className="connection-status">
            {connected ? "Connected · team state is live" : "Disconnected · reconnecting…"}
          </p>

          {/* Host-only controls */}
          {!previewMode && isHost && (
            <div className="grid gap-[9px]">
              {phase === "lobby" && (
                <button
                  type="button"
                  disabled={!connected}
                  onClick={handleStart}
                  className={primaryBtn}
                >
                  Start defense
                </button>
              )}
              {phase === "retry" && (
                <button
                  type="button"
                  disabled={!connected}
                  onClick={handleRetry}
                  className={primaryBtn}
                >
                  Retry question
                </button>
              )}
              {phase === "complete" && feedbackStatus === "failed" && (
                <button
                  type="button"
                  disabled={!connected}
                  onClick={handleRetryCoaching}
                  className={primaryBtn}
                >
                  Retry coaching report
                </button>
              )}
              {phase !== "lobby" && (
                <button
                  type="button"
                  disabled={!connected}
                  onClick={handleRestart}
                  className={secondaryBtn}
                >
                  Restart defense
                </button>
              )}
            </div>
          )}

          {waitText && (
            <p className="control-help">
              {waitText}
            </p>
          )}

          {!previewMode && (
            <button
              type="button"
              onClick={onLeaveRoom}
              className={`${secondaryBtn} leave-room`}
            >
              Leave room
            </button>
          )}
        </div>
      )}
    </div>
  );
}

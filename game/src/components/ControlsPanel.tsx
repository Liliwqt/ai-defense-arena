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

  const tabClass = (active: boolean) =>
    `border-0 rounded-[7px] py-[10px] text-[0.84rem] font-[750] transition-colors ${
      active ? "bg-[#c5e3fc] text-[#173b65]" : "bg-transparent text-[#536b88]"
    }`;

  const inputClass =
    "w-full bg-white border border-[#b8cde1] rounded-[9px] text-[#1b2944] p-[11px_12px] outline-none focus:border-[#61b7ff] focus:shadow-[0_0_0_3px_#61b7ff25]";

  const primaryBtn =
    "w-full border-0 rounded-[9px] p-[11px_13px] font-[850] bg-[#3b8fe5] text-white hover:bg-[#68adf0] disabled:opacity-55 disabled:cursor-wait";

  const secondaryBtn =
    "w-full border border-[#b8cde1] rounded-[9px] p-[11px_13px] font-[850] bg-white text-[#2b4d72] hover:bg-[#e7f2fc] disabled:opacity-55 disabled:cursor-wait";

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
          <div className="grid grid-cols-2 gap-[5px] bg-[#e5eff9] rounded-[10px] p-1 mb-5">
            <button
              type="button"
              className={tabClass(activeTab === "create")}
              aria-selected={activeTab === "create"}
              onClick={() => setActiveTab("create")}
            >
              Create room
            </button>
            <button
              type="button"
              className={tabClass(activeTab === "join")}
              aria-selected={activeTab === "join"}
              onClick={() => setActiveTab("join")}
            >
              Join room
            </button>
          </div>

          {activeTab === "create" && (
            <form id="create-form" onSubmit={handleCreate} className="grid gap-[15px]">
              <label className="grid gap-[7px] text-[#d5e4f3] text-[0.84rem] font-bold">
                Your name
                <input name="host_name" maxLength={24} autoComplete="name" required placeholder="Your name" className={inputClass} />
              </label>
              <label className="grid gap-[7px] text-[#d5e4f3] text-[0.84rem] font-bold">
                Defense type
                <select name="defense_type" value={defenseType} onChange={(event) => setDefenseType(event.target.value as typeof defenseType)} className={inputClass}>
                  <option value="code">Code project</option>
                  <option value="research">Research paper</option>
                  <option value="mixed">Research + code</option>
                </select>
              </label>
              {defenseType !== "code" && <label className="grid gap-[7px] text-[#d5e4f3] text-[0.84rem] font-bold">
                Research stage
                <select name="research_stage" defaultValue="infer" className={inputClass}>
                  <option value="infer">Let AI infer</option>
                  <option value="proposal">Proposal</option>
                  <option value="completed">Completed study</option>
                </select>
              </label>}
              {defenseType !== "research" && <label className="grid gap-[7px] text-[#d5e4f3] text-[0.84rem] font-bold">
                Project source files or ZIP
                <input name="files" type="file" multiple required accept=".zip,.md,.txt,.py,.js,.jsx,.ts,.tsx,.json,.html,.css,.java,.go,.rs,.sql,.yaml,.yml,.toml,.sh,.c,.cpp,.h,.hpp,.kt,.swift,.rb,.php,.vue,.svelte" className={`${inputClass} text-[0.77rem] leading-tight`} />
              </label>}
              {defenseType !== "code" && <label className="grid gap-[7px] text-[#d5e4f3] text-[0.84rem] font-bold">
                Research documents
                <input name="research_files" type="file" multiple required accept=".pdf,.docx,.txt,.md" className={`${inputClass} text-[0.77rem] leading-tight`} />
              </label>}
              <p className="text-[0.78rem] leading-[1.45] text-[#9eb5ca] m-0">
                Research papers: text-based PDF, DOCX, TXT, or Markdown. PDF pages must contain readable text.
              </p>
              <button type="submit" disabled={createBusy} className={primaryBtn}>
                {createBusy ? "Creating…" : "Create defense room"}
              </button>
            </form>
          )}

          {activeTab === "join" && (
            <form id="join-form" onSubmit={handleJoin} className="grid gap-[15px]">
              <label className="grid gap-[7px] text-[#d5e4f3] text-[0.84rem] font-bold">
                Room code
                <input name="room_code" maxLength={12} autoComplete="off" required placeholder="Enter room code" className={inputClass} />
              </label>
              <label className="grid gap-[7px] text-[#d5e4f3] text-[0.84rem] font-bold">
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
            <div className="grid gap-1 bg-white border border-[#d2e0ee] rounded-[11px] p-[15px] mb-[14px]">
            <span className="text-[#4b7fad] text-[0.68rem] font-black tracking-[0.16em]">
              ROOM CODE
            </span>
            <strong className="text-[1.45rem] tracking-[0.15em] break-all text-[#1b2944]">
              {roomCode ?? "—"}
            </strong>
            <span className="text-[0.8rem] text-[#59718b]">
              {previewMode
                ? "Visual preview"
                : isHost
                  ? "Host · share the code with your team"
                  : "Defender · waiting with your team"}
            </span>
          </div>

          {roomState?.phase === "lobby" && roomState.accepted_files && (
            <div className="text-[0.78rem] text-[#d5e4f3]" aria-label="Accepted files">
              <strong>Accepted files · {roomState.defense_type === "code" ? "Code project" : roomState.defense_type === "mixed" ? "Research + code" : "Research paper"}</strong>
              <ul className="mt-2 pl-5">{roomState.accepted_files.map((file) => <li key={file.name}>{file.name}{file.detail ? ` · ${file.detail}` : ""}</li>)}</ul>
            </div>
          )}
          <p className="text-[0.8rem] text-[#8ed4f3] m-0">
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
            <p className="text-[0.78rem] leading-[1.45] text-[#9eb5ca] m-0">
              {waitText}
            </p>
          )}

          {!previewMode && (
            <button
              type="button"
              onClick={onLeaveRoom}
              className={`${secondaryBtn} mt-[17px]`}
            >
              Leave room
            </button>
          )}
        </div>
      )}
    </div>
  );
}

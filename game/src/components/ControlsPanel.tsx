import { useState } from "react";
import type { RoomState } from "../types";

interface ControlsPanelProps {
  roomState: RoomState | null;
  connected: boolean;
  previewMode: boolean;
  waitingForAnswerAck: boolean;
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
  waitingForAnswerAck,
  onUseRoom,
  onLeaveRoom,
  onSendEvent,
  onCloseDrawer,
  showMessage,
}: ControlsPanelProps) {
  const [activeTab, setActiveTab] = useState<"create" | "join">("create");
  const [createBusy, setCreateBusy] = useState(false);
  const [joinBusy, setJoinBusy] = useState(false);

  const inRoom = roomState !== null || !!connected;
  const phase = roomState?.phase ?? "none";
  const feedbackStatus = roomState?.feedback_status ?? "none";
  const isHost = roomState?.self_is_host ?? false;
  const roomCode = roomState?.room_code ?? null;

  // find current unanswered turn
  const turns = roomState?.turns ?? [];
  let currentTurnIndex = -1;
  for (let i = turns.length - 1; i >= 0; i--) {
    if (turns[i].question && !turns[i].answer) {
      currentTurnIndex = i;
      break;
    }
  }
  const hasCurrent = currentTurnIndex >= 0;

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
      // clear passcode
      (form.elements.namedItem("host_passcode") as HTMLInputElement).value = "";
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
      active ? "bg-[#285277] text-white" : "bg-transparent text-[#9bb4ce]"
    }`;

  const inputClass =
    "w-full bg-[#081a2b] border border-[#42617d] rounded-[9px] text-white p-[11px_12px] outline-none focus:border-[#61b7ff] focus:shadow-[0_0_0_3px_#61b7ff25]";

  const primaryBtn =
    "w-full border-0 rounded-[9px] p-[11px_13px] font-[850] bg-[#50b6ee] text-[#092039] hover:bg-[#83d2f8] disabled:opacity-55 disabled:cursor-wait";

  const secondaryBtn =
    "w-full border border-[#547595] rounded-[9px] p-[11px_13px] font-[850] bg-[#263f5b] text-[#dcecff] hover:bg-[#345675] disabled:opacity-55 disabled:cursor-wait";

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
                  ? "The four-question defense is complete. Open Transcript for your coaching report."
                  : "";

  return (
    <div className="grid gap-[15px]">
      {/* Connect forms — shown before joining */}
      {!inRoom && !previewMode && (
        <div>
          {/* Tab switcher */}
          <div className="grid grid-cols-2 gap-[5px] bg-[#071829] rounded-[10px] p-1 mb-5">
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
                Host passcode
                <input name="host_passcode" type="password" autoComplete="off" required placeholder="Server passcode" className={inputClass} />
              </label>
              <label className="grid gap-[7px] text-[#d5e4f3] text-[0.84rem] font-bold">
                Project files or ZIP
                <input name="files" type="file" multiple required className={`${inputClass} text-[0.77rem] leading-tight`} />
              </label>
              <p className="text-[0.78rem] leading-[1.45] text-[#9eb5ca] m-0">
                Select source files together, or one ZIP. The host passcode is sent only to the server.
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
          <div className="grid gap-1 bg-[#071a2b] border border-[#35546e] rounded-[11px] p-[15px] mb-[14px]">
            <span className="text-[#85acd4] text-[0.68rem] font-black tracking-[0.16em]">
              ROOM CODE
            </span>
            <strong className="text-[1.45rem] tracking-[0.15em] break-all text-[#eaf2ff]">
              {roomCode ?? "—"}
            </strong>
            <span className="text-[0.8rem] text-[#a9c7df]">
              {previewMode
                ? "Visual preview"
                : isHost
                  ? "Host · share the code with your team"
                  : "Defender · waiting with your team"}
            </span>
          </div>

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

          {/* Answer form */}
          {!previewMode && phase === "question" && hasCurrent && (
            <form
              id="answer-form"
              className="grid gap-[15px]"
              onSubmit={(e) => {
                e.preventDefault();
                const textarea = e.currentTarget.elements.namedItem("answer") as HTMLTextAreaElement;
                const answer = textarea.value.trim();
                if (!answer) { showMessage("Write an answer before submitting."); return; }
                if (onSendEvent({ type: "submit_answer", turn: currentTurnIndex, answer })) {
                  // waitingForAnswerAck will be set by the hook; clear field on ack
                }
              }}
            >
              <label className="grid gap-[7px] text-[#d5e4f3] text-[0.84rem] font-bold">
                Your answer
                <textarea
                  name="answer"
                  rows={5}
                  maxLength={4000}
                  required
                  placeholder="Explain your team's design choice…"
                  className={`${inputClass} resize-y min-h-[115px]`}
                />
              </label>
              <button
                type="submit"
                disabled={!connected || waitingForAnswerAck}
                className={primaryBtn}
              >
                Submit answer
              </button>
              <p className="text-[0.78rem] leading-[1.45] text-[#9eb5ca] m-0">
                Any teammate can answer. The first valid answer received by the server counts.
              </p>
            </form>
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

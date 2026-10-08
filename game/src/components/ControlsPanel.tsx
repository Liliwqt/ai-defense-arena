import { useEffect, useState } from "react";
import type { RoomState } from "../types";
import type { Account } from "../hooks/useAccount";
import { OwnedRooms } from "./OwnedRooms";
import { ResearchPlanPanel } from "./ResearchPlanPanel";

interface ControlsPanelProps {
  account?: Account | null;
  onOpenAccount?: () => void;
  onOpenTranscript?: () => void;
  onPreviewMoment?: () => void;
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
  account,
  onOpenAccount,
  onOpenTranscript,
  onPreviewMoment,
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
  const [budgetDirty, setBudgetDirty] = useState(false);
  const [defenseType, setDefenseType] = useState<"code" | "research" | "mixed">("code");

  const [hostName, setHostName] = useState("");
  const [nameEdited, setNameEdited] = useState(false);
  const [confirmRestart, setConfirmRestart] = useState(false);
  useEffect(() => { if (!nameEdited && account?.user?.name) setHostName(account.user.name.slice(0, 24)); }, [account?.user?.name, nameEdited]);
  const liveAccess = account?.payment_mode === "live";
  const creditLabel = liveAccess ? "credits" : "test credits";
  const availableCredits = liveAccess ? account?.live_credits : account?.test_credits;
  const canRun = !!account?.authenticated && (!liveAccess || account.ai_service_available !== false)
    && (!!account.free_access || ((!liveAccess || account.paid_starts_enabled !== false) && (availableCredits ?? 0) >= 10));

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
        headers: { "X-CSRF-Token": account?.csrf_token ?? "" },
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
    const payload = roomState?.defense_type && roomState.defense_type !== "code"
      ? { type: "start", confirm_cost: true, plan_id: roomState.research_plan?.id, question_budget: roomState.research_budget_preview }
      : { type: "start", confirm_cost: true };
    if (onSendEvent(payload)) onCloseDrawer();
  }
  function handleRetry() {
    if (onSendEvent({ type: "retry" })) onCloseDrawer();
  }
  function handleRetryCoaching() {
    if (onSendEvent({ type: "retry_coaching" })) onCloseDrawer();
  }
  function handleRestart() {
    if (!account?.free_access && !confirmRestart) { setConfirmRestart(true); return; }
    if (onSendEvent({ type: "restart", confirm_cost: true })) { setConfirmRestart(false); onCloseDrawer(); }
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
      {onOpenTranscript && <button type="button" className={secondaryBtn} onClick={onOpenTranscript}>Transcript</button>}
      {previewMode && onPreviewMoment && <button type="button" className={secondaryBtn} onClick={onPreviewMoment}>Preview presenter</button>}
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
              {!account?.authenticated && <div className="account-access-card"><p>Sign in with Google to create a room. Teammates can use Join room without an account.</p><button type="button" className={secondaryBtn} onClick={onOpenAccount}>Open Account</button></div>}
              <label className="setup-label">
                Your name
                <input name="host_name" maxLength={24} autoComplete="name" required placeholder="Your name" value={hostName} onChange={e => { setNameEdited(true); setHostName(e.target.value); }} className={inputClass} />
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
              <button type="submit" disabled={createBusy || !account?.authenticated} className={primaryBtn}>
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

      {!previewMode && account?.authenticated && account.csrf_token && <OwnedRooms csrf={account.csrf_token}
        onResume={(code, token) => { onUseRoom(code, token, true); onCloseDrawer(); }}
        onClosed={code => { if (code === roomCode) onLeaveRoom(); }} />}
      {roomState?.expires_at_ms && <p role="status" className="control-help">This room expires at {new Date(roomState.expires_at_ms).toLocaleTimeString()}. Save the transcript before expiry.</p>}
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
            {previewMode ? "Visual preview · no AI calls or room connection" : connected ? "Connected · team state is live" : "Disconnected · reconnecting…"}
          </p>

          {roomState?.defense_type && roomState.defense_type !== "code" && <ResearchPlanPanel
            roomState={roomState} connected={connected} previewMode={previewMode} onSendEvent={onSendEvent} onBudgetDraftChange={setBudgetDirty} />}

          {isHost && !previewMode && <div className="account-access-card"><strong>{account?.free_access ? "Free access active" : `10 ${creditLabel} per defense run`}</strong><p>{account?.authenticated ? `${availableCredits ?? 0} available · ${liveAccess ? account.live_reserved_credits ?? 0 : account.reserved_credits ?? 0} reserved ${creditLabel}` : "Sign in with the room owner’s Google account to use host controls."}</p><button type="button" className={secondaryBtn} onClick={onOpenAccount}>Open Account</button></div>}

          {/* Host-only controls */}
          {isHost && liveAccess && account?.ai_service_available === false && <p role="status">The defense service is temporarily unavailable. Your credits are retained.</p>}
          {isHost && liveAccess && account?.ai_service_available !== false && account?.paid_starts_enabled === false && !account.free_access && <p role="status">Paid starts are temporarily paused. Voucher access remains available.</p>}
          {!previewMode && isHost && (
            <div className="grid gap-[9px]">
              {phase === "lobby" && (
                <button
                  type="button"
                  disabled={!connected || !canRun || budgetDirty || (!!roomState?.defense_type && roomState.defense_type !== "code" && (!roomState.research_plan_approved || !roomState.research_plan || roomState.research_planning_status !== "ready"))}
                  onClick={handleStart}
                  className={primaryBtn}
                >
                  {account?.free_access ? "Start defense · free access" : `Start defense · 10 ${creditLabel}`}
                </button>
              )}
              {roomState?.defense_type && roomState.defense_type !== "code" && phase === "lobby" && !roomState.research_plan_approved && <p className="control-help">Prepare and confirm the research map and question budget to enable Start.</p>}
              {roomState?.defense_type && roomState.defense_type !== "code" && phase !== "lobby" && phase !== "complete" && <>
                <button type="button" disabled={!connected} className={secondaryBtn}
                  onClick={() => { if (onSendEvent({ type: "end_defense" })) onCloseDrawer(); }}>End defense</button>
                <p className="control-help">End now and keep accepted answers. An active unanswered question is marked ended early.</p>
              </>}
              {phase === "retry" && (
                <button
                  type="button"
                  disabled={!connected || roomState?.question_attempts_left === 0}
                  onClick={handleRetry}
                  className={primaryBtn}
                >
                  Retry question
                </button>
              )}
              {phase === "complete" && feedbackStatus === "failed" && (
                <button
                  type="button"
                  disabled={!connected || roomState?.coaching_attempts_left === 0}
                  onClick={handleRetryCoaching}
                  className={primaryBtn}
                >
                  Retry coaching report
                </button>
              )}
              {liveAccess && (phase === "retry" || (phase === "complete" && feedbackStatus === "failed")) && <button type="button" className={secondaryBtn} disabled={!connected} onClick={() => { if(onSendEvent({type:"end_unavailable"})) onCloseDrawer(); }}>End unavailable defense{account?.free_access ? "" : " · return credits"}</button>}
              {phase !== "lobby" && (
                <button
                  type="button"
                  disabled={!connected || !canRun}
                  onClick={handleRestart}
                  className={secondaryBtn}
                >
                  {confirmRestart ? `Confirm restart · 10 ${creditLabel}` : "Restart defense"}
                </button>
              )}
            </div>
          )}

          {confirmRestart && <p role="status" className="control-help">Restart begins a new run for 10 {creditLabel}. Your previous transcript will be replaced. <button type="button" className={secondaryBtn} onClick={() => setConfirmRestart(false)}>Cancel restart</button></p>}

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

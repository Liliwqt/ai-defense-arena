import { useEffect, useRef, useState, type ReactNode } from "react";
import type { RoomState } from "../types";
import type { Account } from "../hooks/useAccount";
import { OwnedRooms } from "./OwnedRooms";
import { ResearchPlanPanel } from "./ResearchPlanPanel";
import { createRoom, RoomCreationError, type RoomCreationProgress } from "../lib/createRoom";

import { deriveRoomPresentation, type RoomPresentation } from "../lib/roomPresentation";

interface ControlsPanelProps {
  presentation?: RoomPresentation;
  account?: Account | null;
  setupRequest?: { tab: "create" | "join"; id: number; fresh?: boolean };
  onOpenAccount?: () => void;
  onOpenTranscript?: () => void;
  onPreviewMoment?: () => void;
  roomState: RoomState | null;
  connected: boolean;
  previewMode: boolean;
  /** "page" renders inside the full-screen setup/preparation surface. */
  surface?: "drawer" | "page";
  pageContext?: ReactNode;
  actionError?: string | null;
  /** Show fresh create/join forms even inside an existing room ("Create another room"). */
  forceSetup?: boolean;
  /** On the setup page for an existing room: show its fixed accepted files, not a replacement form. */
  showExistingFiles?: boolean;
  activeRoomCode?: string | null;
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
  setupRequest,
  onOpenAccount,
  onOpenTranscript,
  onPreviewMoment,
  roomState,
  connected,
  previewMode,
  surface = "drawer",
  pageContext,
  actionError,
  forceSetup = false,
  showExistingFiles = false,
  activeRoomCode = null,
  onUseRoom,
  onLeaveRoom,
  onSendEvent,
  onCloseDrawer,
  showMessage,
  presentation = deriveRoomPresentation(roomState),
}: ControlsPanelProps) {
  const createFormRef = useRef<HTMLFormElement>(null);
  const [activeTab, setActiveTab] = useState<"create" | "join">(setupRequest?.tab ?? "create");
  // The panel stays mounted across drawer/screen changes. Each explicit Home entry
  // is a fresh request (new object with a new id), so a repeated choice reapplies;
  // manual tab clicks and keyboard arrows keep owning activeTab between requests.
  useEffect(() => {
    if (!setupRequest) return;
    setActiveTab(setupRequest.tab);
    if (setupRequest.fresh) {
      createFormRef.current?.querySelectorAll<HTMLInputElement>('input[type="file"]').forEach(input => { input.value = ""; });
      setCreateProgress(null);
      setCreateUncertain(false);
      setCreateElapsed(0);
    }
  }, [setupRequest]);
  const [createBusy, setCreateBusy] = useState(false);
  const [createProgress, setCreateProgress] = useState<RoomCreationProgress | null>(null);
  const [createElapsed, setCreateElapsed] = useState(0);
  // A lost create response may still have made a room; never silently retry it.
  const [createUncertain, setCreateUncertain] = useState(false);
  const createPending = useRef(false);
  const progressRef = useRef<HTMLDivElement>(null);
  const [joinBusy, setJoinBusy] = useState(false);
  const [scopeDirty, setScopeDirty] = useState(false);
  const startPending = useRef(false);
  const [starting, setStarting] = useState(false);
  const [researchActionContainer, setResearchActionContainer] = useState<HTMLDivElement | null>(null);
  const [defenseType, setDefenseType] = useState<"code" | "research" | "mixed">("code");

  const [hostName, setHostName] = useState("");
  const [nameEdited, setNameEdited] = useState(false);
  const [confirmRestart, setConfirmRestart] = useState(false);
  useEffect(() => {
    if (createBusy) progressRef.current?.scrollIntoView?.({ block: "nearest" });
  }, [createBusy]);
  useEffect(() => {
    if (!createBusy) return;
    const started = Date.now();
    const timer = window.setInterval(() => setCreateElapsed(Math.floor((Date.now() - started) / 1000)), 1000);
    return () => window.clearInterval(timer);
  }, [createBusy]);
  useEffect(() => { if (!nameEdited && account?.user?.name) setHostName(account.user.name.slice(0, 24)); }, [account?.user?.name, nameEdited]);
  const liveAccess = account?.payment_mode === "live";
  const creditLabel = liveAccess ? "credits" : "test credits";
  const availableCredits = liveAccess ? account?.live_credits : account?.test_credits;
  const canRun = !!account?.authenticated && (!liveAccess || account.ai_service_available !== false)
    && (!!account.free_access || ((!liveAccess || account.paid_starts_enabled !== false) && (availableCredits ?? 0) >= 10));

  const inRoom = roomState !== null || !!connected || !!activeRoomCode;
  const phase = roomState?.phase ?? "none";
  const feedbackStatus = roomState?.feedback_status ?? "none";
  const isHost = roomState?.self_is_host ?? false;
  const roomCode = roomState?.room_code ?? activeRoomCode;

  // Mode selection: fresh setup forms, the fixed files of an existing room, or the
  // live preparation/room controls. They never overlap, so a room cannot appear to
  // offer a replacement upload form.
  const showExisting = showExistingFiles && !forceSetup;
  const showSetupForms = forceSetup || (!inRoom && !previewMode);
  const showRoomControls = (inRoom || previewMode) && !showExisting && !forceSetup;

  const researchMode = !!roomState?.defense_type && roomState.defense_type !== "code";
  useEffect(() => { setScopeDirty(false); }, [roomCode, researchMode]);
  const accessReason = !account?.authenticated ? "Sign in with the room owner’s Google account."
    : liveAccess && account.ai_service_available === false ? "The defense service is temporarily unavailable. Your credits are retained."
    : liveAccess && account.paid_starts_enabled === false && !account.free_access ? "Paid starts are paused. Voucher access remains available."
    : !account.free_access && (availableCredits ?? 0) < 10 ? `Use a free-access voucher or obtain 10 ${creditLabel} in Account.` : "";
  const runReason = previewMode ? "Visual preview · preparation controls are read-only." : !connected ? "Reconnect before starting the defense." : accessReason || (starting ? "Starting the defense… Waiting for the server." : "");
  const startLabel = account?.free_access ? "Start defense · free access" : `Start defense · 10 ${creditLabel}`;
  useEffect(() => {
    startPending.current = false;
    setStarting(false);
  }, [phase, roomCode, roomState?.research_plan?.id, connected]);

  useEffect(() => {
    if (!actionError) return;
    startPending.current = false;
    setStarting(false);
  }, [actionError]);

  async function handleCreate(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (createPending.current || !account?.authenticated) return;
    createPending.current = true;
    showMessage("");
    setCreateUncertain(false);
    setCreateElapsed(0);
    setCreateProgress({ percent: 0, stage: "uploading" });
    setCreateBusy(true);
    const form = e.currentTarget;
    try {
      const body = await createRoom(new FormData(form), account?.csrf_token ?? "", setCreateProgress);
      onUseRoom(body.room_code, body.player_token, true);
    } catch (err) {
      setCreateProgress(null);
      setCreateUncertain(err instanceof RoomCreationError ? err.uncertain : true);
      showMessage((err as Error).message ?? "Could not create the room.");
    } finally {
      createPending.current = false;
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
    if (startPending.current || runReason || scopeDirty) return;
    const payload = roomState?.defense_type && roomState.defense_type !== "code"
      ? { type: "start", confirm_cost: true, plan_id: roomState.research_plan?.id, question_budget: roomState.research_budget_preview }
      : { type: "start", confirm_cost: true };
    startPending.current = true;
    if (onSendEvent(payload)) { setStarting(true); onCloseDrawer(); }
    else startPending.current = false;
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
    if (createBusy || joinBusy) return;
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
  const createLabel = createBusy ? "Creating…" : "Create defense room";
  const joinLabel = joinBusy ? "Joining…" : "Join team";
  const createDisabled = createBusy || !account?.authenticated;

  const waitText = previewMode ? "Preview mode does not send answers." : !connected && roomState
    ? "Reconnecting… Controls become available when connected." : presentation.guidance;

  return (
    <div className={surface === "page" ? "guided-controls" : "controls-content"}>
      <div className="controls-main grid gap-[15px]">
      {surface === "drawer" && onOpenTranscript && <button type="button" className={secondaryBtn} onClick={onOpenTranscript}>Transcript</button>}
      {previewMode && surface === "drawer" && onPreviewMoment && <button type="button" className={secondaryBtn} onClick={onPreviewMoment}>Preview presenter</button>}
      {/* Keep forms mounted so page and tab changes retain FileList and drafts. */}
        <div hidden={!showSetupForms}>
          {/* Tab switcher */}
          <div className="setup-tabs" role="tablist" aria-label="Room setup">
            <button
              type="button"
              disabled={createBusy || joinBusy}
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
              disabled={createBusy || joinBusy}
              className={tabClass(activeTab === "join")}
              role="tab" aria-controls="join-form" tabIndex={activeTab === "join" ? 0 : -1}
              onKeyDown={handleSetupTabKey}
              aria-selected={activeTab === "join"}
              onClick={() => setActiveTab("join")}
            >
              Join room
            </button>
          </div>

            <div hidden={activeTab !== "create"}>
            <form ref={createFormRef} id="create-form" role="tabpanel" aria-busy={createBusy} onSubmit={handleCreate}>
              <fieldset disabled={createBusy} className="setup-fieldset">
              {!account?.authenticated && <div className="account-access-card"><p>Sign in with Google to create a room. Teammates can use Join room without an account.</p><button type="button" className={secondaryBtn} onClick={onOpenAccount}>Open Account</button></div>}
              <section className="setup-card">
              <h2>What are you preparing?</h2>
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
              </section>
              <section className="setup-card">
              <h2>Your work</h2>
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
              </section>
              <button hidden={surface === "page"} type="submit" disabled={createDisabled} className={primaryBtn}>
                {createLabel}
              </button>
              </fieldset>
            </form>
            {createProgress && <div ref={progressRef} className="room-create-progress">
              <div className="room-create-progress-heading">
                <p role="status">{createProgress.stage === "ready" ? "Room ready" : createProgress.stage === "processing" ? "Processing files and creating room…" : "Uploading files…"}</p>
                <strong className="room-create-percent">{createProgress.percent === null ? "Uploading" : `${createProgress.percent}%`}</strong>
              </div>
              <div className="room-create-progress-track" role="progressbar" aria-label="File upload" aria-valuemin={0} aria-valuemax={100}
                aria-valuenow={createProgress.percent ?? undefined}
                aria-valuetext={createProgress.stage === "ready" ? "Upload complete. Room ready." : createProgress.stage === "processing" ? "Upload complete. Processing files and creating room." : undefined}>
                <span className={`room-create-progress-fill${createProgress.percent === null ? " is-indeterminate" : ""}`} style={createProgress.percent === null ? undefined : { width: `${createProgress.percent}%` }} />
              </div>
              <p className="control-help">{createProgress.stage === "ready" ? "Room created successfully." : createProgress.stage === "processing" ? "Upload complete. Keep this page open while your files are checked." : "Keep this page open. Percentage shows files uploaded."} <span className="room-create-elapsed">{createElapsed}s elapsed</span></p>
            </div>}
            </div>

            <form hidden={activeTab !== "join"} id="join-form" role="tabpanel" onSubmit={handleJoin} className="setup-card grid gap-[15px]">
              <h2>Meet your team.</h2>
              <p className="control-help">Enter your room code and the name your teammates will see. No Google account needed.</p>
              <label className="setup-label">
                Room code
                <input name="room_code" maxLength={12} autoComplete="off" required placeholder="Enter room code" className={inputClass} />
              </label>
              <label className="setup-label">
                Your name
                <input name="name" maxLength={24} autoComplete="name" required placeholder="Your name" className={inputClass} />
              </label>
              <button hidden={surface === "page"} type="submit" disabled={joinBusy} className={primaryBtn}>
                {joinLabel}
              </button>
            </form>
        </div>

      {/* Existing room on the setup page: fixed accepted files, never a replacement form */}
      {showExisting && (
        <div className="grid gap-[15px]">
          <p className="control-help">This room keeps its accepted uploads. To defend different files, use Create another room; this room stays open.</p>
          {roomState?.accepted_files?.length ? (
            <div className="accepted-files" role="group" aria-label="Accepted files">
              <strong>Accepted files · {roomState.defense_type === "code" ? "Code project" : roomState.defense_type === "mixed" ? "Research + code" : "Research paper"}</strong>
              <ul className="mt-2 pl-5">{roomState.accepted_files.map((file) => <li key={file.name}>{file.name}{file.detail ? ` · ${file.detail}` : ""}</li>)}</ul>
            </div>
          ) : <p role="status">Loading this room’s accepted uploads…</p>}
        </div>
      )}

      {/* A lost create response may still have made a room; offer recovery, never replay */}
      {createUncertain && (
        <div className="account-access-card" role="status">
          <strong>We couldn’t confirm whether the room was created.</strong>
          <p>Check your rooms before trying again — a room may already exist with your uploads.</p>
        </div>
      )}

      {roomState?.expires_at_ms && <p role="status" className="control-help">This room expires at {new Date(roomState.expires_at_ms).toLocaleTimeString()}. Save the transcript before expiry.</p>}
      {/* In-room controls */}
      {
        <div hidden={!showRoomControls} className="grid gap-[15px]">
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
            <details className="preparation-files" open={surface !== "page" || !researchMode}>
              <summary>Accepted files · {roomState.accepted_files.length} {roomState.accepted_files.length === 1 ? "file" : "files"}</summary>
              <ul>{roomState.accepted_files.map(file => <li key={file.name}>{file.name}{file.detail ? ` · ${file.detail}` : ""}</li>)}</ul>
            </details>
          )}
          {surface !== "page" && <p className="connection-status">
            {previewMode ? "Visual preview · no AI calls or room connection" : connected ? "Connected · team state is live" : "Disconnected · reconnecting…"}
          </p>}

          {roomState?.defense_type && roomState.defense_type !== "code" && <ResearchPlanPanel key={roomState.room_code}
            roomState={roomState} connected={connected} previewMode={previewMode} onSendEvent={onSendEvent} onScopeDraftChange={setScopeDirty}
            startControl={{ label: startLabel, reason: runReason, onStart: handleStart, onAccount: onOpenAccount,
              accessLabel: previewMode ? "Visual preview · no credits used" : account?.free_access ? "Free access active" : `${availableCredits ?? 0} available · ${liveAccess ? account?.live_reserved_credits ?? 0 : account?.reserved_credits ?? 0} reserved ${creditLabel} · 10 per defense` }}
            actionError={actionError} actionContainer={surface === "page" && showRoomControls ? researchActionContainer : null}
            accessReason={accessReason} />}

          {isHost && !previewMode && !researchMode && <div className="account-access-card"><strong>{account?.free_access ? "Free access active" : `10 ${creditLabel} per defense run`}</strong><p>{account?.authenticated ? `${availableCredits ?? 0} available · ${liveAccess ? account.live_reserved_credits ?? 0 : account.reserved_credits ?? 0} reserved ${creditLabel}` : "Sign in with the room owner’s Google account to use host controls."}</p><button type="button" className={secondaryBtn} onClick={onOpenAccount}>Open Account</button></div>}

          {/* Host-only controls */}
          {isHost && liveAccess && account?.ai_service_available === false && <p role="status">The defense service is temporarily unavailable. Your credits are retained.</p>}
          {isHost && liveAccess && account?.ai_service_available !== false && account?.paid_starts_enabled === false && !account.free_access && <p role="status">Paid starts are temporarily paused. Voucher access remains available.</p>}
          {!previewMode && isHost && (
            <div className="grid gap-[9px]">
              {phase === "lobby" && !researchMode && (
                <button
                  type="button"
                  disabled={!!runReason || scopeDirty}
                  onClick={handleStart}
                  className={primaryBtn}
                >
                  {startLabel}
                </button>
              )}
              {roomState?.defense_type && roomState.defense_type !== "code" && phase === "lobby" && !roomState.research_plan_approved && <p className="control-help">Prepare and confirm the research map and question budget to enable Start.</p>}
              {roomState?.defense_type && roomState.defense_type !== "code" && phase !== "lobby" && phase !== "complete" && <>
                <button type="button" disabled={!connected} className={secondaryBtn}
                  onClick={() => { if (onSendEvent({ type: "end_defense" })) onCloseDrawer(); }}>End defense</button>
                <p className="control-help">End now and keep accepted answers. An active unanswered question is marked ended early.</p>
              </>}
              {presentation.controls.questionRetry && (
                <button
                  type="button"
                  disabled={!connected || !presentation.controls.questionRetryAvailable}
                  onClick={handleRetry}
                  className={primaryBtn}
                >
                  Retry question
                </button>
              )}
              {presentation.controls.coachingRetry && (
                <button
                  type="button"
                  disabled={!connected || !presentation.controls.coachingRetryAvailable}
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
      }
      {!previewMode && account?.authenticated && account.csrf_token && <OwnedRooms csrf={account.csrf_token}
        onResume={(code, token) => onUseRoom(code, token, true)}
        onClosed={code => { if (code === roomCode) onLeaveRoom(); }} />}
      </div>
      {surface === "page" && <aside className="guided-sidebar" aria-label="Room and next step">
        {pageContext}
        {showRoomControls && roomState?.defense_type && roomState.defense_type !== "code" && <div className="guided-primary" ref={setResearchActionContainer} />}
        {showSetupForms && <div className="guided-primary">
          <p className="control-help">{activeTab === "create"
            ? createBusy ? "Keep this page open while your files are processed." : !account?.authenticated ? "Sign in to create a defense. Teammates can join directly." : "Create your room, then review the material before starting."
            : "Join your team at its current stage. You can join without signing in."}</p>
          <button type="submit" form={activeTab === "create" ? "create-form" : "join-form"}
            className={primaryBtn} disabled={activeTab === "create" ? createDisabled : joinBusy}>
            {activeTab === "create" ? createLabel : joinLabel}
          </button>
        </div>}
      </aside>}
    </div>
  );
}

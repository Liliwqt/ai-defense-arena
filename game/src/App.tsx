import { useCallback, useEffect, useRef, useState } from "react";
import { AccountScreen, AppPage, HomeScreen, PreparationSteps, SignInScreen } from "./components/AppScreens";
import { useAccount } from "./hooks/useAccount";
import { RoomDock } from "./components/RoomDock";
import { ControlsPanel } from "./components/ControlsPanel";
import { PreparationPage } from "./components/PreparationPage";
import { LiveRoomStatus } from "./components/LiveRoomStatus";
import { HUD } from "./components/HUD";
import { QuestionCard } from "./components/QuestionCard";
import { DraftSession, clearRoomDrafts } from "./hooks/useTabDraft";
import { useAppRoute } from "./hooks/useAppRoute";
import { internalAppHref, type AppScreen } from "./lib/appRoute";
import { roomDestination } from "./lib/roomDestination";
import { clearTaskIntent, rememberTask, rememberAuthTask, resolveTaskReturn, consumeTaskReturn, isFreshSetupReturn } from "./lib/taskIntent";
import { LivePaymentPage } from "./payments/LivePaymentPage";
import { PaymentTestPage } from "./payments/PaymentTestPage";
import { ManagerPage } from "./management/ManagerPage";
import { useRoomViewport } from "./hooks/useRoomViewport";
import "./mobile.css";
import { DefenderSeats, PanelistSeats, type PresenterMoment } from "./components/FlatRoom";
import { TranscriptPanel } from "./components/TranscriptPanel";
import { useRoomSocket } from "./hooks/useRoomSocket";
import { previewState } from "./previewState";
import type { RoomState } from "./types";

import { deriveRoomPresentation } from "./lib/roomPresentation";

const PRESENTER_MS = 2600;
const previewMode = new URLSearchParams(window.location.search).get("preview") === "1";

export function App() {
  const viewport = useRoomViewport();
  const { account, refresh: refreshAccount, error: accountError } = useAccount(previewMode);
  const { screen: routeScreen, freshSetup = false, invalid, navigate: moveTo, navigateHref } = useAppRoute();
  // The bare entry starts with sign-in while identity is loading. An existing
  // authenticated session can go straight Home; explicit routes keep their intent.
  const isEntry = !window.location.hash || window.location.hash === "#" || window.location.hash === "#/";
  const screen = routeScreen === "signin" && isEntry && account?.authenticated ? "home" : routeScreen;
  const {
    roomState: liveRoomState, connected, roomCode, waitingForAnswerAck,
    actionError, actionErrorReason, sendEvent, useRoom, leaveRoom, playerToken,
  } = useRoomSocket(previewMode);
  const [setupRequest, setSetupRequest] = useState<{ tab: "create" | "join"; id: number; fresh?: boolean }>({ tab: "create", id: 0 });
  // A distinct "Create another room" starts fresh setup without closing the current room.
  const [newRoomSetup, setNewRoomSetup] = useState(freshSetup);
  useEffect(() => { if (routeScreen === "setup") setNewRoomSetup(freshSetup); }, [routeScreen, freshSetup]);
  const previousTaskScreen = useRef(screen);
  useEffect(() => {
    const prior = previousTaskScreen.current;
    previousTaskScreen.current = screen;
    // Payment/manager components own their request state. Revalidate the shell's
    // private wallet on every return, including browser Back, without a mutation.
    if (prior !== screen && ["payments-live", "payments-test", "manager"].includes(prior)) void refreshAccount();
  }, [screen, refreshAccount]);
  useEffect(() => {
    const refresh = () => { void refreshAccount(); };
    window.addEventListener("defense-native-resume", refresh);
    return () => window.removeEventListener("defense-native-resume", refresh);
  }, [refreshAccount]);
  const [message, setMessage] = useState("");
  const [presenterMoment, setPresenterMoment] = useState<PresenterMoment | null>(null);
  const presenterTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const previousAnswered = useRef(-1);

  const sequence = useRef(0);
  const [mockRoomState, setMockRoomState] = useState(previewState);
  const roomState: RoomState | null = previewMode ? mockRoomState : liveRoomState;
  const presentation = deriveRoomPresentation(roomState);


  const isSetup = screen === "setup";
  const isPrepare = screen === "prepare";
  const isControls = screen === "controls";
  const pageScreen = isSetup || isPrepare || isControls;
  const [stageNotice, setStageNotice] = useState("");
  const activeRoomCode = previewMode ? (roomState?.room_code ?? null) : roomCode;
  const hasRoom = activeRoomCode !== null;
  const navigate = useCallback((target: AppScreen) => {
    if (["account", "signin", "payments-live", "payments-test", "manager"].includes(target) &&
        ["setup", "prepare", "room", "controls", "results"].includes(screen)) {
      rememberTask(screen, account, newRoomSetup ? null : activeRoomCode);
    }
    moveTo(target, target === "setup" && newRoomSetup);
  }, [moveTo, screen, account, activeRoomCode, newRoomSetup]);
  const callbackEntry = useRef(new URLSearchParams(window.location.search).get("account") === "1");
  const previousIdentity = useRef<string | null>(null);
  const previousAuth = useRef(account?.authenticated);
  useEffect(() => {
    const identity = account?.authenticated ? account.user?.id : null;
    if (identity && previousIdentity.current && identity !== previousIdentity.current) clearTaskIntent();
    if (identity) previousIdentity.current = identity;
    const signedIn = previousAuth.current === false && account?.authenticated;
    if (account) previousAuth.current = account.authenticated;
    if (!account?.authenticated || (!callbackEntry.current && !signedIn)) return;
    if (activeRoomCode && !roomState) return; // wait for authoritative membership
    callbackEntry.current = false;
    const target = resolveTaskReturn(account, roomState, !!presentation.reaction?.closing, true);
    if (target) {
      const fresh = target === "setup" && isFreshSetupReturn();
      if (fresh) setNewRoomSetup(true);
      consumeTaskReturn(account, true); moveTo(target, fresh);
    }
  }, [account, roomState, activeRoomCode, presentation.reaction?.closing, moveTo]);

  const priorRoomCode = useRef<string | null>(null);
  useEffect(() => {
    if (priorRoomCode.current && !activeRoomCode) { clearRoomDrafts(priorRoomCode.current); clearTaskIntent(); }
    priorRoomCode.current = activeRoomCode;
  }, [activeRoomCode]);

  useEffect(() => {
    if (!previewMode || mockRoomState.phase !== "reacting") return;
    const timer = setTimeout(() => {
      const now = Date.now();
      setMockRoomState(state => ({ ...state, phase: "voting", reaction_deadline_ms: null,
        server_now_ms: now, vote_deadline_ms: now + 15_000 }));
    }, Math.max(0, (mockRoomState.reaction_deadline_ms ?? Date.now()) - Date.now()));
    return () => clearTimeout(timer);
  }, [mockRoomState.phase, mockRoomState.reaction_deadline_ms]);

  useEffect(() => {
    if (!previewMode || mockRoomState.phase !== "complete" || !mockRoomState.closing_deadline_ms) return;
    const timer = setTimeout(() => {
      setMockRoomState(state => ({ ...state, closing_deadline_ms: null, server_now_ms: Date.now() }));
    }, Math.max(0, mockRoomState.closing_deadline_ms - Date.now()));
    return () => clearTimeout(timer);
  }, [mockRoomState.phase, mockRoomState.closing_deadline_ms]);

  const openControls = useCallback(() => navigate("controls"), [navigate]);
  const openSetup = useCallback((tab: "create" | "join") => {
    // A monotonic id makes every explicit Home choice reapply even when it repeats
    // the previous tab, since the persisted ControlsPanel cannot see a same-value change.
    setSetupRequest(previous => ({ tab, id: previous.id + 1 }));
    setMessage("");
    navigate("setup");
  }, [navigate]);
  const startAnotherRoom = useCallback(() => {
    setSetupRequest(previous => ({ tab: "create", id: previous.id + 1, fresh: true }));
    setNewRoomSetup(true);
    setMessage("");
    moveTo("setup", true);
  }, [moveTo]);

  const showMessage = useCallback((value: string) => {
    setMessage(value);
    if (value && screen === "room") openControls();
  }, [openControls, screen]);

  // Back is navigation only; leaving a room remains explicit.
  const handlePageBack = useCallback(() => {
    if (isControls) navigate("room");
    else if (isSetup) navigate(hasRoom ? "prepare" : "home");
    else if (isPrepare) navigate(hasRoom ? "room" : "home");
    else navigate("room");
  }, [isSetup, isPrepare, isControls, hasRoom, navigate]);
  // Finishing a preparation action on the page returns to the defense room.
  const finishControlAction = useCallback(() => navigate("room"), [navigate]);

  const endPresenter = useCallback(() => {
    if (presenterTimer.current) clearTimeout(presenterTimer.current);
    presenterTimer.current = null;
    setPresenterMoment(null);

  }, []);

  useEffect(() => {
    if (!roomState) return;
    const turns = roomState?.turns ?? [];
    const answered = presentation.acceptedCount;
    const firstSnapshot = previousAnswered.current === -1;
    const newAnswer = !firstSnapshot && answered > previousAnswered.current;

    if (newAnswer) {
      const seat = turns.filter((turn) => turn.answer).at(-1)?.answered_by_seat;
      if (typeof seat === "number" && seat >= 0 && seat < 4) {
        const reducedMotion = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches ?? false;
        setPresenterMoment({ seat, sequence: ++sequence.current, reducedMotion });
        if (presenterTimer.current) clearTimeout(presenterTimer.current);
        presenterTimer.current = setTimeout(endPresenter, PRESENTER_MS);
      }
    } else if (!firstSnapshot && answered < previousAnswered.current) {
      if (presenterTimer.current) clearTimeout(presenterTimer.current);
      presenterTimer.current = null;
      setPresenterMoment(null);
    }

    const closing = !!presentation.reaction?.closing;
    if (closing) {
      if (presenterTimer.current) clearTimeout(presenterTimer.current);
      presenterTimer.current = null;
      setPresenterMoment(null);
    }
    previousAnswered.current = answered;
  }, [roomState]);

  useEffect(() => () => { if (presenterTimer.current) clearTimeout(presenterTimer.current); }, []);

  // A mock focus moment is available for local visual review without sending an answer.
  useEffect(() => {
    if (!previewMode || new URLSearchParams(window.location.search).get("moment") !== "answer") return;
    const timer = setTimeout(() => {
      setPresenterMoment({ seat: 0, sequence: ++sequence.current, reducedMotion: false });
      presenterTimer.current = setTimeout(endPresenter, PRESENTER_MS);
    }, 700);
    return () => clearTimeout(timer);
  }, [endPresenter]);

  const resetMoment = useCallback(() => {
    previousAnswered.current = -1;
    if (presenterTimer.current) clearTimeout(presenterTimer.current);
    presenterTimer.current = null;
    setPresenterMoment(null);
  }, []);

  const previewPresenter = useCallback(() => {
    const reducedMotion = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches ?? false;
    setPresenterMoment({ seat: 0, sequence: ++sequence.current, reducedMotion });
    if (presenterTimer.current) clearTimeout(presenterTimer.current);
    presenterTimer.current = setTimeout(endPresenter, PRESENTER_MS);
  }, [endPresenter]);

  // A host lands on the shareable preparation screen; a guest enters the room itself.
  const handleUseRoom = useCallback((code: string, token: string, host: boolean) => {
    resetMoment();
    useRoom(code, token, host);
    setNewRoomSetup(false);
    setMessage("");
    navigate(host ? "prepare" : "room");
  }, [resetMoment, useRoom, navigate]);

  const handleLeaveRoom = useCallback(() => {
    resetMoment();
    if (activeRoomCode) clearRoomDrafts(activeRoomCode);
    clearTaskIntent();
    leaveRoom();
    setNewRoomSetup(false);
    setMessage("");
    navigate("home");
  }, [resetMoment, leaveRoom, navigate, activeRoomCode]);

  useEffect(() => { if (liveRoomState?.self_is_host) void refreshAccount(); }, [liveRoomState?.phase, refreshAccount]);
  // A socket sign-in error can persist for the life of the room. Redirect once per
  // newly received error so Back/Home/room stay usable while it is still present.
  const handledSignInError = useRef<string | null>(null);
  useEffect(() => {
    if (!actionError?.startsWith("Sign in") || handledSignInError.current === actionError) return;
    handledSignInError.current = actionError;
    if (screen !== "account") navigate("account");
    void refreshAccount();
  }, [actionError, screen, navigate, refreshAccount]);

  // Announce each screen change by focusing its heading; ordinary same-screen
  // updates (account refresh, snapshots, timers) leave focus where it is.
  const firstScreen = useRef(true);
  useEffect(() => {
    if (firstScreen.current) { firstScreen.current = false; return; }
    const mappingRoom = screen === "prepare" && roomState?.research_planning_status === "planning";
    document.getElementById(screen === "room" || mappingRoom ? "room-screen-title" : "app-screen-title")?.focus();
  }, [screen]);

  // Follow meaningful server stage changes once; snapshots never own manual navigation.
  const stageRef = useRef<{ room: string; stage: "prepare" | "room" | "results" } | null>(null);
  useEffect(() => {
    if (!roomState) return;
    const stage = roomDestination(roomState, !!presentation.reaction?.closing);
    const prior = stageRef.current;
    const initial = !prior || prior.room !== roomState.room_code;
    const changed = !initial && prior.stage !== stage;
    stageRef.current = { room: roomState.room_code, stage };
    if (!["room", "prepare", "controls", "results"].includes(screen)) return;
    if ((changed && stage !== "prepare") || (initial &&
      ((screen === "prepare" && stage !== "prepare") || (screen === "results" && stage === "prepare") ||
       (screen === "controls" && stage === "prepare") || (screen === "room" && stage === "results")))) {
      setStageNotice("Your room’s current stage has been restored.");
      navigate(stage);
    }
  }, [roomState, presentation.reaction?.closing, screen, navigate]);
  const returnScreen = roomDestination(roomState, !!presentation.reaction?.closing);
  const onAccountTask = ["signin", "account", "payments-live", "payments-test", "manager"].includes(screen);
  const savedReturn = onAccountTask && account?.authenticated && (!hasRoom || roomState) ? resolveTaskReturn(account, roomState, !!presentation.reaction?.closing) : null;
  const taskReturn = savedReturn ?? (hasRoom ? returnScreen : null);
  const returnAction = taskReturn ? <button type="button" className="button-secondary" onClick={() => {
    const fresh = taskReturn === "setup" && isFreshSetupReturn();
    if (fresh) setNewRoomSetup(true);
    if (account?.authenticated) consumeTaskReturn(account);
    if (fresh) moveTo("setup", true); else navigate(taskReturn);
  }}>
    {taskReturn === "results" ? "View defense results" : taskReturn === "setup" ? "Return to setup" : "Return to defense"}
  </button> : null;
  // A bare preparation address with no room falls back to setup rather than
  // showing preparation controls a route alone cannot authorize.
  const prepareReady = isPrepare && hasRoom;
  const mappingInRoom = prepareReady && roomState?.phase === "lobby"
    && roomState.defense_type !== "code" && roomState.research_planning_status === "planning";
  const pageTitle = isControls ? "Live controls" : prepareReady ? (roomState?.defense_type && roomState.defense_type !== "code" ? "Shape your defense." : "Prepare your defense")
    : hasRoom ? (newRoomSetup ? "Create another room" : "Your material")
    : setupRequest.tab === "join" ? "Join a room" : "Bring your work.";
  const pageKicker = isControls ? "YOUR DEFENSE · CONTROLS" : prepareReady ? "STEP 2 / PREPARE & REVIEW" : "STEP 1 / UPLOAD & SETUP";

  const pageSide = <section className="guided-room-context">
    <p className="app-page-kicker">{hasRoom ? "YOUR TEAM’S ROOM" : "YOUR PRACTICE"}</p>
    <strong>{activeRoomCode ?? "A space to prepare together"}</strong>
    <p>{hasRoom ? `${roomState?.self_is_host ? "Host" : "Teammate"} · ${roomState?.phase ?? "Connecting…"}` : "Four perspectives. Your research. Your reasoning."}</p>
    {hasRoom && <>
      <p>Share this code with your team. Your room stays connected while you prepare.</p>
      {!isControls && <button type="button" className="button-secondary" onClick={() => navigate(isPrepare ? "room" : "prepare")}>
        {isPrepare ? "Return to the defense room" : "Back to preparation"}
      </button>}
      {isPrepare && <button type="button" className="button-secondary" onClick={() => navigate("setup")}>Back to setup</button>}
      {!newRoomSetup && <button type="button" className="button-secondary" onClick={startAnotherRoom}>Create another room</button>}
    </>}
  </section>;

  return (
    <DraftSession account={account} token={playerToken} state={roomState} preview={previewMode}>
    <div className="app-root" onClick={event => {
      if (event.defaultPrevented || event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
      const anchor = (event.target as Element).closest<HTMLAnchorElement>("a[href]");
      if (!anchor || anchor.download || (anchor.target && anchor.target !== "_self")) return;
      const url = new URL(anchor.href, window.location.href);
      if (url.origin === window.location.origin && url.pathname === "/api/auth/google/login") rememberAuthTask(screen, account);
      const href = internalAppHref(anchor.href);
      if (href) { event.preventDefault(); navigateHref(href); }
    }}>
      {stageNotice && <p className="navigation-notice" role="status">{stageNotice}</p>}
      <div className="room-screen" hidden={screen !== "room" && !mappingInRoom}>
        <div className="arena-shell" data-research-mapping={roomState?.phase === "lobby" && roomState.research_planning_status === "planning"} data-speaker-desk={!!roomState?.voice?.enabled && roomState.defense_type !== "code"} data-compact-viewport={viewport.compact} style={{ "--room-viewport-height": `${viewport.height}px` } as React.CSSProperties}>
          <div id="stage" className="arena-stage">
            <HUD presentation={presentation} roomState={roomState} roomCode={roomCode} previewMode={previewMode} onOpenControls={openControls} onOpenTranscript={() => navigate("results")}
              onOpenAccount={() => navigate("account")} onOpenHome={() => navigate("home")} onPreviewMoment={previewPresenter} />
            <PanelistSeats presentation={presentation} roomState={roomState} />
            <QuestionCard presentation={presentation} roomState={roomState} playerToken={playerToken} />
            <DefenderSeats presentation={presentation} roomState={roomState} presenterMoment={presenterMoment} />
          </div>
          <RoomDock active={screen === "room"} playerToken={playerToken} presentation={presentation} roomState={roomState} connected={connected} previewMode={previewMode}
            waitingForAnswerAck={waitingForAnswerAck} actionError={actionError} actionErrorReason={actionErrorReason} onSendEvent={sendEvent} />
        </div>
      </div>
      {/* Keep preparation content mounted across screens to preserve FileList and drafts. */}
      <PreparationPage open={pageScreen && !mappingInRoom} title={pageTitle}
        kicker={pageKicker}
        introContent={isControls && <section className="live-controls-overview" aria-label="Current defense controls">
          <LiveRoomStatus state={roomState} presentation={presentation} />
          <div className="app-page-actions">{returnAction}<button type="button" className="button-secondary" onClick={() => navigate("results")}>Transcript</button></div>
        </section>}
        steps={pageScreen && !isControls ? <PreparationSteps current={prepareReady ? 2 : 1} hasRoom={hasRoom}
          onSelect={step => navigate(step === 1 ? "setup" : step === 2 ? "prepare" : "room")} /> : undefined}
        onHome={() => navigate("home")} onAccount={() => navigate("account")}
        description={isControls ? "Manage this run and return to your team. Room timers continue on every screen." : prepareReady ? "Make sure the panel understands your work. Confirm the profile and question budget before starting."
          : hasRoom && !newRoomSetup ? "These accepted files stay with your room. Use a new room for different material."
          : setupRequest.tab === "join" ? "Enter your room code and join your team."
          : "Choose the work you want to defend. You’ll prepare your room before anything starts."}
        onClose={handlePageBack}>
        {/* Controls and accepted files stay mounted while other tasks are open. */}
        <div>
          <ControlsPanel presentation={presentation} roomState={previewMode ? roomState : liveRoomState} connected={connected} previewMode={previewMode}
            actionError={actionError} setupRequest={setupRequest} surface="page" pageContext={pageSide}
            forceSetup={isSetup && newRoomSetup} showExistingFiles={isSetup && hasRoom && !newRoomSetup}
            activeRoomCode={activeRoomCode}
            onUseRoom={handleUseRoom} onLeaveRoom={handleLeaveRoom} onSendEvent={sendEvent}
            onActionComplete={finishControlAction} showMessage={showMessage} account={account}
            onOpenAccount={() => navigate("account")}
            />
          {(message || actionError) && <div role="alert" className="drawer-error">{message || actionError}</div>}
        </div>

      </PreparationPage>
      {screen === "results" && <AppPage kicker="SESSION HISTORY · YOUR TEAM" title="Defense results"
        actions={<><button type="button" className="button-secondary" onClick={() => navigate("room")}>Return to defense</button><button type="button" className="button-secondary" onClick={() => navigate("controls")}>Live controls</button><button type="button" className="button-secondary" onClick={() => navigate("home")}>Home</button></>}>
        <LiveRoomStatus state={roomState} presentation={presentation} />
        {!hasRoom ? <p role="alert">This room is no longer available. Results cannot be restored from this browser.</p> :
          <TranscriptPanel presentation={presentation} roomState={roomState} previewMode={previewMode} connected={connected} onSendEvent={sendEvent} />}
      </AppPage>}
      {["signin", "account", "payments-live", "payments-test", "manager"].includes(screen) && <div className="task-room-return">{returnAction}</div>}
      {screen === "payments-live" && <LivePaymentPage />}
      {screen === "payments-test" && <PaymentTestPage />}
      {screen === "manager" && <ManagerPage />}
      {screen === "account" && (
        <AccountScreen account={account} error={actionError?.startsWith("Sign in") ? actionError : accountError}
          refresh={refreshAccount} previewMode={previewMode} onBack={() => navigate("home")} />
      )}
      {screen === "signin" && <SignInScreen account={account} error={accountError} onRetry={() => { void refreshAccount(); }}
        onBack={() => navigate("home")} onAccount={() => navigate("account")} onJoin={() => openSetup("join")} />}
      {screen === "home" && <HomeScreen notice={invalid ? "We couldn’t open that screen. You’re on Home." : null}
        onCreate={() => { if (account?.authenticated) openSetup("create"); else { rememberTask("setup", account, null); navigate("signin"); } }}
        onJoin={() => openSetup("join")} roomCode={roomCode}
        onReturnToRoom={() => navigate("room")}
        ownerHref={account?.authenticated && account.manager_enabled ? "/?manager=1" : null} />}
    </div>
    </DraftSession>
  );
}

import { useCallback, useEffect, useRef, useState } from "react";
import { AccountScreen, AppPage, HomeScreen, PreparationSteps, SignInScreen } from "./components/AppScreens";
import { useAccount } from "./hooks/useAccount";
import { RoomDock } from "./components/RoomDock";
import { ControlsPanel } from "./components/ControlsPanel";
import { Drawer } from "./components/Drawer";
import { LiveRoomStatus } from "./components/LiveRoomStatus";
import { HUD } from "./components/HUD";
import { QuestionCard } from "./components/QuestionCard";
import { useAppRoute } from "./hooks/useAppRoute";
import { useRoomViewport } from "./hooks/useRoomViewport";
import "./mobile.css";
import { DefenderSeats, PanelistSeats, type PresenterMoment } from "./components/FlatRoom";
import { TranscriptPanel } from "./components/TranscriptPanel";
import { useRoomSocket } from "./hooks/useRoomSocket";
import { previewState } from "./previewState";
import type { DrawerMode, RoomState } from "./types";

import { deriveRoomPresentation } from "./lib/roomPresentation";

const PRESENTER_MS = 2600;
const previewMode = new URLSearchParams(window.location.search).get("preview") === "1";

export function App() {
  const viewport = useRoomViewport();
  const { account, refresh: refreshAccount, error: accountError } = useAccount(previewMode);
  const { screen: routeScreen, invalid, navigate } = useAppRoute();
  // The bare entry starts with sign-in while identity is loading. An existing
  // authenticated session can go straight Home; explicit routes keep their intent.
  const isEntry = !window.location.hash || window.location.hash === "#" || window.location.hash === "#/";
  const screen = routeScreen === "signin" && isEntry && account?.authenticated ? "home" : routeScreen;
  const {
    roomState: liveRoomState, connected, roomCode, waitingForAnswerAck,
    actionError, actionErrorReason, sendEvent, useRoom, leaveRoom, playerToken,
  } = useRoomSocket(previewMode);
  const [drawerMode, setDrawerMode] = useState<DrawerMode>("controls");
  const [setupRequest, setSetupRequest] = useState<{ tab: "create" | "join"; id: number; fresh?: boolean }>({ tab: "create", id: 0 });
  // A distinct "Create another room" starts fresh setup without closing the current room.
  const [newRoomSetup, setNewRoomSetup] = useState(false);
  useEffect(() => {
    const refresh = () => { void refreshAccount(); };
    window.addEventListener("defense-native-resume", refresh);
    return () => window.removeEventListener("defense-native-resume", refresh);
  }, [refreshAccount]);
  const [message, setMessage] = useState("");
  const [presenterMoment, setPresenterMoment] = useState<PresenterMoment | null>(null);
  const presenterTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const previousAnswered = useRef(-1);
  const previousPhase = useRef<string | undefined>();
  const previousFeedback = useRef<string | undefined>();
  const previousClosing = useRef(false);

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

  const openDrawer = useCallback((mode: DrawerMode) => {
    setDrawerMode(mode);
    navigate(mode === "transcript" ? "results" : "controls");
  }, [navigate]);
  const closeDrawer = useCallback(() => navigate("room"), [navigate]);
  const openSetup = useCallback((tab: "create" | "join") => {
    // A monotonic id makes every explicit Home choice reapply even when it repeats
    // the previous tab, since the persisted ControlsPanel cannot see a same-value change.
    setSetupRequest(previous => ({ tab, id: previous.id + 1 }));
    setDrawerMode("controls");
    setMessage("");
    navigate("setup");
  }, [navigate]);
  const startAnotherRoom = useCallback(() => {
    setSetupRequest(previous => ({ tab: "create", id: previous.id + 1, fresh: true }));
    setNewRoomSetup(true);
    setDrawerMode("controls");
    setMessage("");
    navigate("setup");
  }, [navigate]);

  const showMessage = useCallback((value: string) => {
    setMessage(value);
    if (value && screen === "room") openDrawer("controls");
  }, [openDrawer, screen]);

  // Header Back moves to the previous meaningful screen; the room overlay still closes.
  const handleDrawerBack = useCallback(() => {
    if (isControls) navigate("room");
    else if (isSetup) navigate(hasRoom ? "prepare" : "home");
    else if (isPrepare) navigate(hasRoom ? "room" : "home");
    else closeDrawer();
  }, [isSetup, isPrepare, isControls, hasRoom, navigate, closeDrawer]);
  // Finishing a preparation action on the page returns to the defense room.
  const closeControls = useCallback(() => {
    if (isPrepare || isControls) navigate("room");
    else closeDrawer();
  }, [isPrepare, isControls, navigate, closeDrawer]);

  const endPresenter = useCallback(() => {
    if (presenterTimer.current) clearTimeout(presenterTimer.current);
    presenterTimer.current = null;
    setPresenterMoment(null);

  }, []);

  useEffect(() => {
    if (!roomState) return;
    const phase = roomState?.phase;
    const feedback = roomState?.feedback_status;
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
    previousPhase.current = phase;
    previousFeedback.current = feedback;
    previousClosing.current = closing;
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
    previousPhase.current = undefined;
    previousFeedback.current = undefined;
    previousClosing.current = false;
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
    if (host) { openDrawer("controls"); navigate("prepare"); }
    else { closeDrawer(); navigate("room"); }
  }, [resetMoment, useRoom, openDrawer, closeDrawer, navigate]);

  const handleLeaveRoom = useCallback(() => {
    resetMoment();
    leaveRoom();
    setNewRoomSetup(false);
    setMessage("");
    navigate("home");
  }, [resetMoment, leaveRoom, navigate]);

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
    document.getElementById("app-screen-title")?.focus();
  }, [screen]);

  // Follow meaningful server stage changes once; snapshots never own manual navigation.
  const stageRef = useRef<{ room: string; stage: "prepare" | "room" | "results" } | null>(null);
  useEffect(() => {
    if (!roomState) return;
    const stage = roomState.phase === "lobby" ? "prepare"
      : roomState.phase === "complete" && !presentation.reaction?.closing ? "results" : "room";
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
  const returnScreen = roomState?.phase === "lobby" ? "prepare"
    : roomState?.phase === "complete" && !presentation.reaction?.closing ? "results" : "room";
  const returnAction = hasRoom ? <button type="button" className="button-secondary" onClick={() => navigate(returnScreen)}>
    {returnScreen === "results" ? "View defense results" : "Return to defense"}
  </button> : null;
  const title = "Controls";
  // A bare preparation address with no room falls back to setup rather than
  // showing preparation controls a route alone cannot authorize.
  const prepareReady = isPrepare && hasRoom;
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
      <button type="button" className="button-secondary" onClick={() => navigate(isPrepare ? "room" : "prepare")}>
        {isPrepare ? "Return to the defense room" : "Back to preparation"}
      </button>
      {isPrepare && <button type="button" className="button-secondary" onClick={() => navigate("setup")}>Back to setup</button>}
      {!newRoomSetup && <button type="button" className="button-secondary" onClick={startAnotherRoom}>Create another room</button>}
    </>}
  </section>;

  return (
    <div className="app-root">
      {stageNotice && <p className="navigation-notice" role="status">{stageNotice}</p>}
      <div className="room-screen" hidden={screen !== "room"}>
        <div className="arena-shell" data-compact-viewport={viewport.compact} style={{ "--room-viewport-height": `${viewport.height}px` } as React.CSSProperties}>
          <div id="stage" className="arena-stage">
            <HUD presentation={presentation} roomState={roomState} roomCode={roomCode} previewMode={previewMode} onOpenDrawer={openDrawer}
              onOpenAccount={() => navigate("account")} onOpenHome={() => navigate("home")} onPreviewMoment={previewPresenter} />
            <PanelistSeats presentation={presentation} roomState={roomState} />
            <QuestionCard presentation={presentation} roomState={roomState} playerToken={playerToken} />
            <DefenderSeats presentation={presentation} roomState={roomState} presenterMoment={presenterMoment} />
          </div>
          <RoomDock presentation={presentation} roomState={roomState} connected={connected} previewMode={previewMode}
            waitingForAnswerAck={waitingForAnswerAck} actionError={actionError} actionErrorReason={actionErrorReason} onSendEvent={sendEvent} />
        </div>
      </div>
      {/* One persistent panel: an in-room overlay on the room screen, a full-screen
          setup/preparation surface otherwise. Keeping it mounted preserves drafts. */}
      <Drawer open={pageScreen} mode={drawerMode} title={pageTitle || title}
        variant="page" kicker={pageScreen ? pageKicker : undefined}
        steps={pageScreen && !isControls ? <PreparationSteps current={prepareReady ? 2 : 1} hasRoom={hasRoom}
          onSelect={step => navigate(step === 1 ? "setup" : step === 2 ? "prepare" : "room")} /> : undefined}
        onHome={() => navigate("home")} onAccount={() => navigate("account")}
        description={prepareReady ? "Make sure the panel understands your work. Confirm the profile and question budget before starting."
          : hasRoom && !newRoomSetup ? "These accepted files stay with your room. Use a new room for different material."
          : setupRequest.tab === "join" ? "Enter your room code and join your team."
          : "Choose the work you want to defend. You’ll prepare your room before anything starts."}
        onClose={pageScreen ? handleDrawerBack : closeDrawer}>
        {/* Controls stay mounted while the transcript shows so unsent preparation
            drafts survive both drawer switching and screen navigation. */}
        <div>
          {isControls && <><LiveRoomStatus state={roomState} presentation={presentation} />{returnAction}<button type="button" className="button-secondary" onClick={() => navigate("results")}>Transcript</button></>}
          <ControlsPanel presentation={presentation} roomState={previewMode ? roomState : liveRoomState} connected={connected} previewMode={previewMode}
            actionError={actionError} setupRequest={setupRequest} surface={pageScreen ? "page" : "drawer"} pageContext={pageSide}
            forceSetup={isSetup && newRoomSetup} showExistingFiles={isSetup && hasRoom && !newRoomSetup}
            activeRoomCode={activeRoomCode}
            onUseRoom={handleUseRoom} onLeaveRoom={handleLeaveRoom} onSendEvent={sendEvent}
            onCloseDrawer={closeControls} showMessage={showMessage} account={account}
            onOpenAccount={() => navigate("account")} onOpenTranscript={() => openDrawer("transcript")}
            onPreviewMoment={previewPresenter} />
          {(message || actionError) && <div role="alert" className="drawer-error">{message || actionError}</div>}
        </div>

      </Drawer>
      {screen === "results" && <AppPage kicker="SESSION HISTORY · YOUR TEAM" title="Defense results"
        actions={<><button type="button" className="button-secondary" onClick={() => navigate("room")}>Return to defense</button><button type="button" className="button-secondary" onClick={() => navigate("controls")}>Live controls</button><button type="button" className="button-secondary" onClick={() => navigate("home")}>Home</button></>}>
        <LiveRoomStatus state={roomState} presentation={presentation} />
        {!hasRoom ? <p role="alert">This room is no longer available. Results cannot be restored from this browser.</p> :
          <TranscriptPanel presentation={presentation} roomState={roomState} previewMode={previewMode} />}
      </AppPage>}
      {screen === "account" && <div className="task-room-return">{returnAction}</div>}
      {screen === "account" && (
        <AccountScreen account={account} error={actionError?.startsWith("Sign in") ? actionError : accountError}
          refresh={refreshAccount} previewMode={previewMode} onBack={() => navigate("home")} />
      )}
      {screen === "signin" && <SignInScreen account={account} error={accountError} onRetry={() => { void refreshAccount(); }}
        onBack={() => navigate("home")} onAccount={() => navigate("account")} onJoin={() => openSetup("join")} />}
      {screen === "home" && <HomeScreen notice={invalid ? "We couldn’t open that screen. You’re on Home." : null}
        onCreate={() => { if (account?.authenticated) openSetup("create"); else navigate("signin"); }}
        onJoin={() => openSetup("join")} roomCode={roomCode}
        onReturnToRoom={() => navigate("room")}
        ownerHref={account?.authenticated && account.manager_enabled ? "/?manager=1" : null} />}
    </div>
  );
}

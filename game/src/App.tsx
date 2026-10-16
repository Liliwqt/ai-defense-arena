import { useCallback, useEffect, useRef, useState } from "react";
import { AccountScreen, HomeScreen, PreparationSteps, SignInScreen } from "./components/AppScreens";
import { useAccount } from "./hooks/useAccount";
import { RoomDock } from "./components/RoomDock";
import { ControlsPanel } from "./components/ControlsPanel";
import { Drawer } from "./components/Drawer";
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
  const { screen, invalid, navigate } = useAppRoute();
  const {
    roomState: liveRoomState, connected, roomCode, waitingForAnswerAck,
    actionError, actionErrorReason, sendEvent, useRoom, leaveRoom, playerToken,
  } = useRoomSocket(previewMode);
  const [drawerOpen, setDrawerOpen] = useState(() =>
    screen === "room" && (!previewMode || new URLSearchParams(window.location.search).get("plan") === "1"));
  const [drawerMode, setDrawerMode] = useState<DrawerMode>("controls");
  const [setupRequest, setSetupRequest] = useState<{ tab: "create" | "join"; id: number }>({ tab: "create", id: 0 });
  // A distinct "Create another room" starts fresh setup without closing the current room.
  const [newRoomSetup, setNewRoomSetup] = useState(false);
  const { account, refresh: refreshAccount, error: accountError } = useAccount(previewMode);
  useEffect(() => {
    const refresh = () => { void refreshAccount(); };
    window.addEventListener("defense-native-resume", refresh);
    return () => window.removeEventListener("defense-native-resume", refresh);
  }, [refreshAccount]);
  const [message, setMessage] = useState("");
  const [presenterMoment, setPresenterMoment] = useState<PresenterMoment | null>(null);
  const presenterTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const pendingTranscript = useRef(false);
  const previousAnswered = useRef(-1);
  const previousPhase = useRef<string | undefined>();
  const previousFeedback = useRef<string | undefined>();
  const previousClosing = useRef(false);
  const closingActive = useRef(false);
  const sequence = useRef(0);
  const [mockRoomState, setMockRoomState] = useState(previewState);
  const roomState: RoomState | null = previewMode ? mockRoomState : liveRoomState;
  const presentation = deriveRoomPresentation(roomState);
  closingActive.current = !!presentation.reaction?.closing;

  const isSetup = screen === "setup";
  const isPrepare = screen === "prepare";
  const pageScreen = isSetup || isPrepare;
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
    setDrawerOpen(true);
  }, []);
  const closeDrawer = useCallback(() => setDrawerOpen(false), []);
  const openSetup = useCallback((tab: "create" | "join") => {
    // A monotonic id makes every explicit Home choice reapply even when it repeats
    // the previous tab, since the persisted ControlsPanel cannot see a same-value change.
    setSetupRequest(previous => ({ tab, id: previous.id + 1 }));
    setNewRoomSetup(false);
    setDrawerMode("controls");
    setMessage("");
    navigate("setup");
  }, [navigate]);
  const startAnotherRoom = useCallback(() => {
    setSetupRequest(previous => ({ tab: "create", id: previous.id + 1 }));
    setNewRoomSetup(true);
    setDrawerMode("controls");
    setMessage("");
  }, []);
  useEffect(() => { if (screen !== "room") setDrawerOpen(false); }, [screen]);
  const showMessage = useCallback((value: string) => {
    setMessage(value);
    if (value) openDrawer("controls");
  }, [openDrawer]);

  // Header Back moves to the previous meaningful screen; the room overlay still closes.
  const handleDrawerBack = useCallback(() => {
    if (isSetup) navigate(hasRoom ? "prepare" : "home");
    else if (isPrepare) navigate(hasRoom ? "room" : "home");
    else closeDrawer();
  }, [isSetup, isPrepare, hasRoom, navigate, closeDrawer]);
  // Finishing a preparation action on the page returns to the defense room.
  const closeControls = useCallback(() => {
    if (isPrepare) navigate("room");
    else closeDrawer();
  }, [isPrepare, navigate, closeDrawer]);

  const endPresenter = useCallback(() => {
    if (presenterTimer.current) clearTimeout(presenterTimer.current);
    presenterTimer.current = null;
    setPresenterMoment(null);
    if (pendingTranscript.current && !closingActive.current) {
      pendingTranscript.current = false;
      openDrawer("transcript");
    }
  }, [openDrawer]);

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
      pendingTranscript.current = false;
      if (presenterTimer.current) clearTimeout(presenterTimer.current);
      presenterTimer.current = null;
      setPresenterMoment(null);
    }

    const justCompleted = phase === "complete" && previousPhase.current !== "complete";
    const reportReady = feedback === "ready" && previousFeedback.current !== "ready";
    const closing = !!presentation.reaction?.closing;
    const closingFinished = previousClosing.current && !closing && feedback === "ready";
    if (closing) {
      pendingTranscript.current = false;
      if (presenterTimer.current) clearTimeout(presenterTimer.current);
      presenterTimer.current = null;
      setPresenterMoment(null);
      if (firstSnapshot) closeDrawer();
    }
    if (!closing && feedback !== "generating" && (justCompleted || reportReady || closingFinished)) {
      if ((newAnswer && typeof turns.filter((turn) => turn.answer).at(-1)?.answered_by_seat === "number") || presenterTimer.current) {
        pendingTranscript.current = true;
      } else {
        openDrawer("transcript");
      }
    }
    if (phase === "retry" && previousPhase.current !== "retry" && roomState?.self_is_host) openDrawer("controls");
    if (feedback === "failed" && previousFeedback.current !== "failed" && roomState?.self_is_host) openDrawer("controls");
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
    pendingTranscript.current = false;
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
    setMessage("");
    if (host) { openDrawer("controls"); navigate("prepare"); }
    else { closeDrawer(); navigate("room"); }
  }, [resetMoment, useRoom, openDrawer, closeDrawer, navigate]);

  const handleLeaveRoom = useCallback(() => {
    resetMoment();
    leaveRoom();
    setNewRoomSetup(false);
    setMessage("");
    openDrawer("controls");
  }, [resetMoment, leaveRoom, openDrawer]);

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

  const title = drawerMode === "transcript" ? "Transcript" : "Controls";
  // A bare preparation address with no room falls back to setup rather than
  // showing preparation controls a route alone cannot authorize.
  const prepareReady = isPrepare && hasRoom;
  const pageTitle = prepareReady ? "Prepare your defense"
    : hasRoom ? (newRoomSetup ? "Create another room" : "Your material")
    : setupRequest.tab === "join" ? "Join a room" : "Create a defense";
  const pageKicker = prepareReady ? "DEFENSE PREPARATION" : "HOST SETUP";

  const pageSide = prepareReady ? (
    <>
      <h2 className="app-surface-side-title">Room actions</h2>
      <p>Your room stays connected while you prepare. Share its code so your team can join.</p>
      <button type="button" className="button-secondary" onClick={startAnotherRoom}>Create another room</button>
      <button type="button" className="button-secondary" onClick={() => navigate("setup")}>Back to setup</button>
      <button type="button" className="button-secondary" onClick={() => navigate("room")}>Return to the defense room</button>
    </>
  ) : hasRoom ? (
    <>
      <h2 className="app-surface-side-title">Room actions</h2>
      <p>This room keeps its accepted files. Creating another room does not close or change it.</p>
      {!newRoomSetup && <button type="button" className="button-secondary" onClick={startAnotherRoom}>Create another room</button>}
      <button type="button" className="button-secondary" onClick={() => navigate("prepare")}>Back to preparation</button>
    </>
  ) : (
    <>
      <h2 className="app-surface-side-title">About this step</h2>
      <p>Upload your material once. Nothing is sent until you explicitly create the room.</p>
      {isPrepare && <p>No room is open yet. Create or join one to prepare.</p>}
    </>
  );

  return (
    <div className="app-root">
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
      <Drawer open={pageScreen || drawerOpen} mode={drawerMode} title={pageScreen ? pageTitle : title}
        variant={pageScreen ? "page" : "overlay"} kicker={pageScreen ? pageKicker : undefined}
        steps={pageScreen ? <PreparationSteps current={prepareReady ? 2 : 1} /> : undefined}
        side={pageScreen ? pageSide : undefined}
        onClose={pageScreen ? handleDrawerBack : closeDrawer}>
        {/* Controls stay mounted while the transcript shows so unsent preparation
            drafts survive both drawer switching and screen navigation. */}
        <div hidden={!pageScreen && drawerMode !== "controls"}>
          <ControlsPanel presentation={presentation} roomState={previewMode ? roomState : liveRoomState} connected={connected} previewMode={previewMode}
            setupRequest={setupRequest} surface={pageScreen ? "page" : "drawer"}
            forceSetup={isSetup && newRoomSetup} showExistingFiles={isSetup && hasRoom && !newRoomSetup}
            activeRoomCode={activeRoomCode}
            onUseRoom={handleUseRoom} onLeaveRoom={handleLeaveRoom} onSendEvent={sendEvent}
            onCloseDrawer={closeControls} showMessage={showMessage} account={account}
            onOpenAccount={() => navigate("account")} onOpenTranscript={() => openDrawer("transcript")}
            onPreviewMoment={previewPresenter} />
          {(message || actionError) && <div role="alert" className="drawer-error">{message || actionError}</div>}
        </div>
        {!pageScreen && drawerOpen && drawerMode === "transcript" && <TranscriptPanel presentation={presentation} roomState={roomState} previewMode={previewMode} />}
      </Drawer>
      {screen === "account" && (
        <AccountScreen account={account} error={actionError?.startsWith("Sign in") ? actionError : accountError}
          refresh={refreshAccount} previewMode={previewMode} onBack={() => navigate("home")} />
      )}
      {screen === "signin" && <SignInScreen account={account}
        onBack={() => navigate("home")} onAccount={() => navigate("account")} />}
      {screen === "home" && <HomeScreen notice={invalid ? "We couldn’t open that screen. You’re on Home." : null}
        onCreate={() => { if (account?.authenticated) openSetup("create"); else navigate("signin"); }}
        onJoin={() => openSetup("join")} roomCode={roomCode}
        onReturnToRoom={() => navigate("room")}
        ownerHref={account?.authenticated && account.manager_enabled ? "/?manager=1" : null} />}
    </div>
  );
}

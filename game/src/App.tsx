import { useCallback, useEffect, useRef, useState } from "react";
import { AccountPanel } from "./components/AccountPanel";
import { useAccount } from "./hooks/useAccount";
import { RoomDock } from "./components/RoomDock";
import { ControlsPanel } from "./components/ControlsPanel";
import { Drawer } from "./components/Drawer";
import { HUD } from "./components/HUD";
import { QuestionCard } from "./components/QuestionCard";
import { RotatePrompt } from "./components/RotatePrompt";
import { DefenderSeats, PanelistSeats, type PresenterMoment } from "./components/FlatRoom";
import { TranscriptPanel } from "./components/TranscriptPanel";
import { useRoomSocket } from "./hooks/useRoomSocket";
import { previewState } from "./previewState";
import type { DrawerMode, RoomState } from "./types";

const PRESENTER_MS = 2600;
const previewMode = new URLSearchParams(window.location.search).get("preview") === "1";

export function App() {
  const {
    roomState: liveRoomState, connected, roomCode, waitingForAnswerAck,
    actionError, sendEvent, useRoom, leaveRoom,
  } = useRoomSocket(previewMode);
  const [drawerOpen, setDrawerOpen] = useState(!previewMode || new URLSearchParams(window.location.search).get("plan") === "1");
  const [drawerMode, setDrawerMode] = useState<DrawerMode>(new URLSearchParams(location.search).get("account") === "1" ? "account" : "controls");
  const { account, refresh: refreshAccount, error: accountError } = useAccount(previewMode);
  const [message, setMessage] = useState("");
  const [presenterMoment, setPresenterMoment] = useState<PresenterMoment | null>(null);
  const presenterTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const pendingTranscript = useRef(false);
  const previousAnswered = useRef(-1);
  const previousPhase = useRef<string | undefined>();
  const previousFeedback = useRef<string | undefined>();
  const sequence = useRef(0);
  const roomState: RoomState | null = previewMode ? previewState : liveRoomState;

  const openDrawer = useCallback((mode: DrawerMode) => {
    setDrawerMode(mode);
    setDrawerOpen(true);
  }, []);
  const closeDrawer = useCallback(() => setDrawerOpen(false), []);
  const showMessage = useCallback((value: string) => {
    setMessage(value);
    if (value) openDrawer("controls");
  }, [openDrawer]);

  const endPresenter = useCallback(() => {
    if (presenterTimer.current) clearTimeout(presenterTimer.current);
    presenterTimer.current = null;
    setPresenterMoment(null);
    if (pendingTranscript.current) {
      pendingTranscript.current = false;
      openDrawer("transcript");
    }
  }, [openDrawer]);

  useEffect(() => {
    if (!roomState) return;
    const phase = roomState?.phase;
    const feedback = roomState?.feedback_status;
    const turns = roomState?.turns ?? [];
    const answered = turns.filter((turn) => turn.answer).length;
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
    if (justCompleted || reportReady) {
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

  const handleUseRoom = useCallback((code: string, token: string, host: boolean) => {
    resetMoment();
    useRoom(code, token, host);
    if (host) openDrawer("controls"); else closeDrawer();
  }, [resetMoment, useRoom, openDrawer, closeDrawer]);

  const handleLeaveRoom = useCallback(() => {
    resetMoment();
    leaveRoom();
    openDrawer("controls");
  }, [resetMoment, leaveRoom, openDrawer]);

  useEffect(() => { if (liveRoomState?.self_is_host) void refreshAccount(); }, [liveRoomState?.phase, refreshAccount]);
  useEffect(() => {
    if (actionError?.startsWith("Sign in")) { openDrawer("account"); void refreshAccount(); }
  }, [actionError, openDrawer, refreshAccount]);

  const title = drawerMode === "transcript" ? "Transcript" : drawerMode === "account" ? "Account" : "Controls";

  return (
    <div className="arena-shell">
      <div id="stage" className="arena-stage">
        <HUD roomState={roomState} roomCode={roomCode} previewMode={previewMode} onOpenDrawer={openDrawer} onPreviewMoment={previewPresenter} />
        <PanelistSeats roomState={roomState} />
        <QuestionCard roomState={roomState} />
        <DefenderSeats roomState={roomState} presenterMoment={presenterMoment} />
      </div>
      <RoomDock roomState={roomState} connected={connected} previewMode={previewMode}
        waitingForAnswerAck={waitingForAnswerAck} actionError={actionError} onSendEvent={sendEvent} />
      <Drawer open={drawerOpen} mode={drawerMode} title={title} onClose={closeDrawer}>
        {drawerMode === "controls" ? (
          <>
            <ControlsPanel roomState={previewMode ? roomState : liveRoomState} connected={connected} previewMode={previewMode}
              onUseRoom={handleUseRoom} onLeaveRoom={handleLeaveRoom} onSendEvent={sendEvent}
              onCloseDrawer={closeDrawer} showMessage={showMessage} account={account}
              onOpenAccount={() => openDrawer("account")} />
            {(message || actionError) && <div role="alert" className="drawer-error">{message || actionError}</div>}
          </>
        ) : drawerMode === "account" ? (
          <AccountPanel account={account} refresh={refreshAccount} error={actionError?.startsWith("Sign in") ? actionError : accountError} previewMode={previewMode} />
        ) : (
          <TranscriptPanel roomState={roomState} previewMode={previewMode} />
        )}
      </Drawer>
      <RotatePrompt />
    </div>
  );
}

import { useCallback, useEffect, useRef, useState } from "react";
import { AnswerComposer } from "./components/AnswerComposer";
import { ControlsPanel } from "./components/ControlsPanel";
import { Drawer } from "./components/Drawer";
import { HUD } from "./components/HUD";
import { JudgePanelOverlay } from "./components/JudgePanelOverlay";
import { PhaserScene } from "./components/PhaserScene";
import { QuestionCard } from "./components/QuestionCard";
import { RotatePrompt } from "./components/RotatePrompt";
import { TranscriptPanel } from "./components/TranscriptPanel";
import { useRoomSocket } from "./hooks/useRoomSocket";
import { previewState } from "./previewState";
import type { DrawerMode, RoomState } from "./types";

/** Duration of the post-answer "judges discussing" animation before the next
 *  question arrives.  Kept short so it does not feel like lag. */
const DISCUSSING_MS = 1800;

const previewMode =
  new URLSearchParams(window.location.search).get("preview") === "1";

export function App() {
  const {
    roomState: liveRoomState,
    connected,
    roomCode,
    waitingForAnswerAck,
    actionError,
    sendEvent,
    useRoom,
    leaveRoom,
  } = useRoomSocket(previewMode);

  const [drawerOpen, setDrawerOpen] = useState(previewMode ? false : true);
  const [drawerMode, setDrawerMode] = useState<DrawerMode>("controls");
  const [message, setMessage] = useState("");
  /** True for DISCUSSING_MS after an answer is submitted; drives the shared
   *  "thinking" animation on all judges before the next question appears. */
  const [discussing, setDiscussing] = useState(false);
  const discussingTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // In preview mode, use the static preview state; otherwise live state
  const roomState: RoomState | null = previewMode ? previewState : liveRoomState;

  // Track previous phase/feedbackStatus for auto-open drawer transitions
  const prevPhaseRef = useRef<string | undefined>(undefined);
  const prevFeedbackRef = useRef<string | undefined>(undefined);
  // -1 = baseline not yet set; set to actual count on the first snapshot so
  // a reconnect mid-session does not spuriously trigger the discussing anim.
  const prevAnsweredRef = useRef<number>(-1);

  useEffect(() => {
    const phase = roomState?.phase;
    const feedbackStatus = roomState?.feedback_status;
    const isHost = roomState?.self_is_host ?? false;
    const answered = (roomState?.turns ?? []).filter((t) => t.answer).length;

    if (phase === "retry" && prevPhaseRef.current !== "retry" && isHost) {
      openDrawer("controls");
    }
    if (phase === "complete" && prevPhaseRef.current !== "complete") {
      openDrawer("transcript");
    }
    if (
      feedbackStatus === "ready" &&
      prevFeedbackRef.current !== "ready"
    ) {
      openDrawer("transcript");
    }
    if (
      feedbackStatus === "failed" &&
      prevFeedbackRef.current !== "failed" &&
      isHost
    ) {
      openDrawer("controls");
    }

    // Trigger the discussing animation only when a genuinely new answer
    // arrives in-session — not on the first snapshot (reconnect/join).
    if (prevAnsweredRef.current === -1) {
      // First snapshot: record baseline without animating.
      prevAnsweredRef.current = answered;
    } else if (answered > prevAnsweredRef.current && phase !== "complete") {
      setDiscussing(true);
      if (discussingTimerRef.current) clearTimeout(discussingTimerRef.current);
      discussingTimerRef.current = setTimeout(() => {
        setDiscussing(false);
      }, DISCUSSING_MS);
      prevAnsweredRef.current = answered;
    } else {
      prevAnsweredRef.current = answered;
    }

    prevPhaseRef.current = phase;
    prevFeedbackRef.current = feedbackStatus;
  }, [roomState]);

  // Clean up timer on unmount
  useEffect(() => {
    return () => {
      if (discussingTimerRef.current) clearTimeout(discussingTimerRef.current);
    };
  }, []);

  const openDrawer = useCallback((mode: DrawerMode) => {
    setDrawerMode(mode);
    setDrawerOpen(true);
  }, []);

  const closeDrawer = useCallback(() => {
    setDrawerOpen(false);
  }, []);

  const showMessage = useCallback((msg: string) => {
    setMessage(msg);
    if (msg) {
      setDrawerMode("controls");
      setDrawerOpen(true);
    }
  }, []);

  const handleUseRoom = useCallback(
    (code: string, token: string, host: boolean) => {
      // Reset the baseline so the first snapshot of the new room doesn't
      // trigger the discussing animation.
      prevAnsweredRef.current = -1;
      if (discussingTimerRef.current) clearTimeout(discussingTimerRef.current);
      setDiscussing(false);
      useRoom(code, token, host);
      if (host) openDrawer("controls");
      else closeDrawer();
    },
    [useRoom, openDrawer, closeDrawer],
  );

  const handleLeaveRoom = useCallback(() => {
    prevAnsweredRef.current = -1;
    if (discussingTimerRef.current) clearTimeout(discussingTimerRef.current);
    setDiscussing(false);
    leaveRoom();
    openDrawer("controls");
  }, [leaveRoom, openDrawer],
  );

  const drawerTitle = drawerMode === "transcript" ? "Transcript" : "Controls";

  return (
    <div
      className="relative flex flex-col w-full overflow-hidden bg-[#091322]"
      style={{ height: "100dvh" }}
    >
      {/* Stage — Phaser fills this area */}
      <div
        id="stage"
        className="relative flex-1 min-h-0 overflow-hidden"
        style={{
          background:
            "radial-gradient(circle at 50% -15%, #304d6d 0, #142a43 46%, #091827 100%)",
        }}
      >
        <PhaserScene roomState={roomState} />
        <JudgePanelOverlay roomState={roomState} discussing={discussing} />
        <HUD
          roomState={roomState}
          roomCode={roomCode}
          previewMode={previewMode}
          onOpenDrawer={openDrawer}
        />
        <QuestionCard roomState={roomState} />
      </div>

      <AnswerComposer
        roomState={roomState}
        connected={connected}
        previewMode={previewMode}
        waitingForAnswerAck={waitingForAnswerAck}
        actionError={actionError}
        onSendEvent={sendEvent}
      />

      {/* Slide-in drawer */}
      <Drawer
        open={drawerOpen}
        mode={drawerMode}
        title={drawerTitle}
        onClose={closeDrawer}
      >
        {drawerMode === "controls" ? (
          <>
            <ControlsPanel
              roomState={previewMode ? roomState : liveRoomState}
              connected={connected}
              previewMode={previewMode}
              onUseRoom={handleUseRoom}
              onLeaveRoom={handleLeaveRoom}
              onSendEvent={sendEvent}
              onCloseDrawer={closeDrawer}
              showMessage={showMessage}
            />
            {message && (
              <div
                role="alert"
                className="mt-4 p-3 rounded-[9px] bg-[#512934] border border-[#a65b69] text-[#ffe0e5] text-[0.84rem] leading-[1.4]"
              >
                {message}
              </div>
            )}
          </>
        ) : (
          <TranscriptPanel roomState={roomState} />
        )}
      </Drawer>

      {/* Portrait rotation prompt */}
      <RotatePrompt />

    </div>
  );
}

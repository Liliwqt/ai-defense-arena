import { RoomExpiryNotice } from "./RoomExpiryNotice";
import type { DrawerMode, RoomState } from "../types";
import { formatCountdown, useRoomCountdown } from "../hooks/useRoomCountdown";

interface HUDProps {
  roomState: RoomState | null;
  roomCode: string | null;
  previewMode: boolean;
  onOpenDrawer: (mode: DrawerMode) => void;
  onPreviewMoment?: () => void;
}

export function HUD({ roomState, roomCode, previewMode, onOpenDrawer, onPreviewMoment }: HUDProps) {
  const phase = roomState?.phase;
  const resolved = (roomState?.turns ?? []).filter((t) => t.answer || t.timed_out).length;
  const seconds = useRoomCountdown(roomState);

  const pillCode = roomState
    ? `Room ${roomState.room_code || roomCode || "—"}`
    : "No room yet";

  const addressed = Object.values(roomState?.coverage ?? {}).filter(item => item.status === "addressed").length;
  const topicCount = roomState?.research_plan?.topics.length ?? 0;
  const pillProgress =
    phase === "complete"
      ? "COMPLETE"
      : roomState
        ? roomState.question_budget ? `Question ${roomState.turns.length} of ${roomState.question_budget} · ${roomState.active_panelist?.replace(" Reviewer", "").replace(" Judge", "") ?? "Reviewing"}` : `${resolved} RESOLVED`
        : "READY";

  const timed = phase === "voting" || phase === "question" || phase === "interpreting" || phase === "interpretation_retry";
  let status = "Ready";
  if (phase === "complete") status = "Complete";
  else if (phase === "retry") status = "Retry needed";
  else if (phase === "generating") {
    const previous = roomState?.turns.at(-1);
    status = previous?.timed_out ? "Reviewing missed turn…" : previous?.answer ? "Reviewing answer…" : "Preparing question…";
  } else if (roomState?.research_planning_status === "planning") status = "Mapping research…";
  else if (roomState?.research_planning_status === "failed") status = "Retry needed";

  return (
    <header
      id="arena-hud"
      className="arena-hud"
    >
      <div className="brand-plate">
        <span className="brand-cube" aria-hidden="true">◆</span>
        <div>
        <h1>AI Defense Arena</h1>
        <p
          className="hud-kicker"
          aria-hidden="true"
        >
          PROJECT DEFENSE SIMULATOR
        </p>
        </div>
      </div>
      <div className="hud-actions">
        <RoomExpiryNotice state={roomState} />
        {!timed && <span className="hud-mobile-status" role="status" aria-label="Room status" aria-live="polite">{status}</span>}
        <span
          id="room-pill"
          className="hud-pill hud-desktop-only"
        >
          <span aria-hidden="true">♟</span> {pillCode}
        </span>
        <span
          id="round-indicator"
          className="hud-pill hud-progress hud-desktop-only"
        >
          <span aria-hidden="true">▥</span> {pillProgress}
        </span>
        {!!roomState?.question_budget && <span className="hud-pill hud-coverage hud-desktop-only">{addressed} of {topicCount} topics addressed</span>}
        {(phase === "interpreting" || phase === "interpretation_retry") && roomState?.clock_paused !== false && <span id="room-countdown" className="hud-pill hud-timer" role="status" aria-label="Answer timer paused">PAUSED {formatCountdown(Math.ceil((roomState?.remaining_answer_ms ?? 0) / 1000))}</span>}
        {(phase === "voting" || phase === "question" || ((phase === "interpreting" || phase === "interpretation_retry") && roomState?.clock_paused === false)) && (
          <span id="room-countdown" className={`hud-pill hud-timer${seconds !== null && seconds <= (phase === "voting" ? 5 : 15) ? " is-urgent" : ""}`} role="timer" aria-label={`${phase === "voting" ? "Vote" : "Answer"} time remaining`}>
            {phase === "voting" ? "VOTE" : "ANSWER"} {formatCountdown(seconds)}
          </span>
        )}
        <button
          type="button"
          onClick={() => onOpenDrawer("controls")}
          aria-controls="drawer"
          className="hud-button hud-settings"
          aria-label="Settings — room controls"
          title="Settings — room controls"
        >
          <svg className="hud-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" aria-hidden="true"><path d="m9 3-1 3-3 1-2 3 2 2-2 2 2 3 3 1 1 3h6l1-3 3-1 2-3-2-2 2-2-2-3-3-1-1-3Z" /><circle cx="12" cy="12" r="3" /></svg>
          <span className="hud-control-label">Controls</span>
        </button>
        <button type="button" onClick={() => onOpenDrawer("account")} aria-controls="drawer" aria-label="Account" title="Account" className={`hud-button hud-account${previewMode ? " hud-preview-account" : ""}`}>
          <svg className="hud-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" aria-hidden="true"><circle cx="12" cy="8" r="4" /><path d="M4 21v-2a8 8 0 0 1 16 0v2" /></svg>
          <span className="hud-control-label">Account</span>
        </button>
        {previewMode && onPreviewMoment && (
          <button type="button" onClick={onPreviewMoment} className="hud-button hud-desktop-only">Preview presenter</button>
        )}
        {!previewMode && (
          <button
            type="button"
            onClick={() => onOpenDrawer("transcript")}
            aria-controls="drawer"
            className="hud-button hud-desktop-only"
          >
            <span aria-hidden="true">▤</span> Transcript
          </button>
        )}
      </div>
    </header>
  );
}

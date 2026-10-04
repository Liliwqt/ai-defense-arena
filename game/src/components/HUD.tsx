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
        <span
          id="room-pill"
          className="hud-pill"
        >
          <span aria-hidden="true">♟</span> {pillCode}
        </span>
        <span
          id="round-indicator"
          className="hud-pill hud-progress"
        >
          <span aria-hidden="true">▥</span> {pillProgress}
        </span>
        {!!roomState?.question_budget && <span className="hud-pill hud-coverage">{addressed} of {topicCount} topics addressed</span>}
        {(phase === "interpreting" || phase === "interpretation_retry") && <span id="room-countdown" className="hud-pill hud-timer" role="status" aria-label="Answer timer paused">PAUSED {formatCountdown(Math.ceil((roomState?.remaining_answer_ms ?? 0) / 1000))}</span>}
        {(phase === "voting" || phase === "question") && (
          <span id="room-countdown" className={`hud-pill hud-timer${seconds !== null && seconds <= (phase === "voting" ? 5 : 15) ? " is-urgent" : ""}`} role="timer" aria-label={`${phase === "voting" ? "Vote" : "Answer"} time remaining`}>
            {phase === "voting" ? "VOTE" : "ANSWER"} {formatCountdown(seconds)}
          </span>
        )}
        <button
          type="button"
          onClick={() => onOpenDrawer("controls")}
          aria-controls="drawer"
          className="hud-button"
        >
          <span aria-hidden="true">⚙</span> Controls
        </button>
        {previewMode && onPreviewMoment && (
          <button type="button" onClick={onPreviewMoment} className="hud-button">Preview presenter</button>
        )}
        {!previewMode && (
          <button
            type="button"
            onClick={() => onOpenDrawer("transcript")}
            aria-controls="drawer"
            className="hud-button"
          >
            <span aria-hidden="true">▤</span> Transcript
          </button>
        )}
      </div>
    </header>
  );
}

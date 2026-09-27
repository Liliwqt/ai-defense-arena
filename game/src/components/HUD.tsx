import type { DrawerMode, RoomState } from "../types";

interface HUDProps {
  roomState: RoomState | null;
  roomCode: string | null;
  previewMode: boolean;
  onOpenDrawer: (mode: DrawerMode) => void;
  onPreviewMoment?: () => void;
}

export function HUD({ roomState, roomCode, previewMode, onOpenDrawer, onPreviewMoment }: HUDProps) {
  const phase = roomState?.phase;
  const answered = (roomState?.turns ?? []).filter((t) => t.answer).length;

  const pillCode = roomState
    ? `Room ${roomState.room_code || roomCode || "—"}`
    : "No room yet";

  const pillProgress =
    phase === "complete"
      ? "COMPLETE"
      : roomState
        ? `${answered} ANSWERED`
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

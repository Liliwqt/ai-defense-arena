import { RoomExpiryNotice } from "./RoomExpiryNotice";
import type { DrawerMode, RoomState } from "../types";
import { formatCountdown, useRoomCountdown } from "../hooks/useRoomCountdown";

import { deriveRoomPresentation, type RoomPresentation } from "../lib/roomPresentation";

interface HUDProps {
  presentation?: RoomPresentation;
  roomState: RoomState | null;
  roomCode: string | null;
  previewMode: boolean;
  onOpenDrawer: (mode: DrawerMode) => void;
  onPreviewMoment?: () => void;
}

export function HUD({ roomState, roomCode, previewMode, onOpenDrawer, onPreviewMoment, presentation = deriveRoomPresentation(roomState) }: HUDProps) {
  const seconds = useRoomCountdown(roomState, presentation);
  const { timer, status, progress: pillProgress, coverage } = presentation;
  const timed = timer !== null;
  const pillCode = roomState ? `Room ${roomState.room_code || roomCode || "—"}` : "No room yet";

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
        {presentation.reaction && <span className="hud-pill hud-desktop-only" role="status">{status}</span>}
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
        {!!roomState?.question_budget && <span className="hud-pill hud-coverage hud-desktop-only">{coverage.addressed} of {coverage.total} topics addressed</span>}
        {timer && (
          <span id="room-countdown" className={`hud-pill hud-timer${timer.mode === "running" && seconds !== null && seconds <= timer.urgentAt ? " is-urgent" : ""}`}
            role={timer.mode === "paused" ? "status" : "timer"} aria-label={timer.accessibleLabel}>
            {timer.label} {formatCountdown(timer.mode === "paused" ? timer.savedSeconds : seconds)}
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

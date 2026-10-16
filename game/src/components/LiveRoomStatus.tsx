import { formatCountdown, useRoomCountdown } from "../hooks/useRoomCountdown";
import type { RoomPresentation } from "../lib/roomPresentation";
import type { RoomState } from "../types";

/** Uses the same authoritative deadlines as the room; navigation never owns a clock. */
export function LiveRoomStatus({ state, presentation }: { state: RoomState | null; presentation: RoomPresentation }) {
  const seconds = useRoomCountdown(state, presentation);
  const timer = presentation.timer;
  return <div className="live-room-status">
    <p role="status">{state ? `Room ${state.room_code} · ${presentation.status}` : "Waiting for room membership…"}</p>
    {timer && <p role={timer.mode === "paused" ? "status" : "timer"} aria-label={timer.accessibleLabel}>
      {timer.label} {formatCountdown(timer.mode === "paused" ? timer.savedSeconds : seconds)}
    </p>}
    <p>Room timers continue while you’re on another screen.</p>
  </div>;
}

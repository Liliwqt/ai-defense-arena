import { formatCountdown, useRoomCountdown } from "../hooks/useRoomCountdown";
import type { RoomPresentation } from "../lib/roomPresentation";
import type { RoomState } from "../types";

/** Uses the same authoritative deadlines as the room; navigation never owns a clock. */
export function LiveRoomStatus({ state, presentation }: { state: RoomState | null; presentation: RoomPresentation }) {
  const seconds = useRoomCountdown(state, presentation);
  const timer = presentation.timer;
  return <div className="live-room-status">
    <p role="status">{state ? `Room ${state.room_code} · ${timer ? presentation.guidance : presentation.status}` : "Waiting for room membership…"}</p>
    {timer && <p role={timer.mode === "paused" ? "status" : "timer"} aria-label={timer.accessibleLabel}>
      {timer.label} {formatCountdown(timer.mode === "paused" ? timer.savedSeconds : seconds)}
    </p>}
    <p>{state?.phase === "complete" && state.coaching_progress && state.coaching_progress.completion_status !== "ready" ? (["cancelled","returned","abandoned"].includes(state.coaching_progress.completion_status) ? "This run ended with incomplete coaching. Ready results remain available while the room exists." : "Discussion has ended. Coaching completion is still pending; ready results remain available while the room exists.") : state?.phase === "complete" ? "This defense is complete. Results remain available while the room exists."
      : state?.phase === "lobby" ? "No defense has started." : "Room timers continue while you’re on another screen."}</p>
  </div>;
}

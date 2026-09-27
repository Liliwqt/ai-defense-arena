import { useEffect, useState } from "react";
import type { RoomState } from "../types";

export function useRoomCountdown(roomState: RoomState | null): number | null {
  const deadline = roomState?.phase === "voting"
    ? roomState.vote_deadline_ms
    : roomState?.phase === "question" ? roomState.answer_deadline_ms : null;
  const serverNow = roomState?.server_now_ms ?? 0;
  const [remaining, setRemaining] = useState<number | null>(null);

  useEffect(() => {
    if (deadline == null) {
      setRemaining(null);
      return;
    }
    const initial = Math.max(0, deadline - serverNow);
    const started = performance.now();
    const tick = () => setRemaining(Math.max(0, Math.ceil((initial - (performance.now() - started)) / 1000)));
    tick();
    const timer = window.setInterval(tick, 250);
    return () => window.clearInterval(timer);
  }, [deadline, serverNow]);
  return remaining;
}

export function formatCountdown(seconds: number | null): string {
  if (seconds == null) return "--:--";
  return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}`;
}

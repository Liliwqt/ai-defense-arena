import type { RoomState } from "../types";

/** Discussion, closing, report availability and financial completion are separate. */
export function roomDestination(state: RoomState | null, closing: boolean): "prepare" | "room" | "results" {
  if (state?.phase === "lobby") return "prepare";
  if (state?.phase === "complete" && (state.feedback_status !== "generating" || state.coaching_progress?.overview_status === "ready") && !closing) return "results";
  return "room";
}

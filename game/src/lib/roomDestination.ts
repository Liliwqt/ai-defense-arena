import type { RoomState } from "../types";

/** A completed financial run may still be generating coaching or speaking. */
export function roomDestination(state: RoomState | null, closing: boolean): "prepare" | "room" | "results" {
  if (state?.phase === "lobby") return "prepare";
  if (state?.phase === "complete" && state.feedback_status !== "generating" && !closing) return "results";
  return "room";
}

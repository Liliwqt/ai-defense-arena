import { expect, it } from "vitest";
import { deriveRoomPresentation } from "./roomPresentation";
import { previewState } from "../previewState";
import type { RoomState } from "../types";

it("distinguishes an accepted answer awaiting a probe from resolved turns without mutating a snapshot", () => {
  const turn = { ...previewState.turns[0], answer: "We will run a pilot.", resolved: false,
    probe: { id: "p1", request: "What will the pilot measure?", status: "pending" as const,
      references: [], reply: null, clarifications: [] } };
  const state: RoomState = { ...previewState, phase: "probe", selected_seat: 0, self_seat: 0,
    turns: [turn], answer_deadline_ms: 31000, server_now_ms: 1000 };
  Object.freeze(turn);
  Object.freeze(state.turns);
  Object.freeze(state);
  const view = deriveRoomPresentation(state);
  expect(view.acceptedCount).toBe(1);
  expect(view.resolvedCount).toBe(0);
  expect(view.answerTurnIndex).toBe(0);
  expect(view.card.initialAnswer).toBe("We will run a pilot.");
  expect(view.card.probe?.request).toBe("What will the pilot measure?");
  expect(view.timer).toMatchObject({ label: "PROBE", deadline: 31000 });
  expect(state.turns[0]).toBe(turn);
});

it("honors explicit unresolved status while counting legacy answers and timeouts", () => {
  const source = previewState.turns[0];
  const view = deriveRoomPresentation({ ...previewState, phase: "complete", turns: [
    { ...source, answer: "An accepted answer", resolved: false },
    { ...source, answer: "A legacy resolved answer", resolved: undefined },
    { ...source, answer: null, timed_out: true, resolved: undefined },
  ] });
  expect(view.acceptedCount).toBe(2);
  expect(view.resolvedCount).toBe(2);
  expect(view.card.number).toBe("2 RESOLVED");
  expect(view.progress).toBe("COMPLETE");
});

it("keeps legacy interpretation clocks paused unless the snapshot explicitly runs them", () => {
  const state: RoomState = { ...previewState, phase: "interpreting", clock_paused: undefined,
    server_now_ms: 1000, answer_deadline_ms: 121000, remaining_answer_ms: 45000 };
  expect(deriveRoomPresentation(state).timer).toMatchObject({ mode: "paused", savedSeconds: 45, deadline: null });
  expect(deriveRoomPresentation({ ...state, clock_paused: false }).timer).toMatchObject({ mode: "running", deadline: 121000 });
});

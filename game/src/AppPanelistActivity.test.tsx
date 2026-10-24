import { render, screen, within } from "@testing-library/react";
import { beforeEach, afterEach, expect, it, vi } from "vitest";
import { App } from "./App";
import { useAccount } from "./hooks/useAccount";
import { useRoomSocket, type RoomSocketState } from "./hooks/useRoomSocket";
import type { RoomState } from "./types";

vi.mock("./hooks/useAccount", () => ({ useAccount: vi.fn() }));
vi.mock("./hooks/useRoomSocket", () => ({ useRoomSocket: vi.fn() }));
let socket: RoomSocketState;
function waitingRoom(extra: Partial<RoomState> = {}): RoomState {
  return {
    room_code: "NOTES1", defense_view_id: "run-one", phase: "generating", defense_type: "research",
    self_seat: 0, self_is_host: true, revision: 1, error: null,
    players: [{ seat: 0, name: "Alex", online: true, is_host: true }], files: ["paper.md"],
    active_panelist: null, feedback_status: "none", feedback: null, server_now_ms: 5000,
    turns: [{ panelist: "Methodology Reviewer", question: "Who will you invite?", filename: "paper.md",
      evidence_line: 1, evidence_text: "We plan student interviews.", answer: "We will invite volunteers.",
      resolved: true, answered_by: "Alex" }],
    operation: { id: "question:2", kind: "question", stage: "generating", started_at_ms: 1000, attempt: 1, retrying: false },
    panelist_activity: { operation_id: "question:2", view_id: "run-one", reviewer: null, context: "Participant recruitment" },
    ...extra,
  };
}
beforeEach(() => {
  sessionStorage.clear(); window.history.replaceState(null, "", "/#/room");
  vi.mocked(useAccount).mockReturnValue({ account: { authenticated: true, google_enabled: true, free_access: true }, error: "", refresh: vi.fn(async () => {}) });
  socket = { roomState: waitingRoom(), roomCode: "NOTES1", playerToken: "fixture", connected: true, knownHost: true,
    waitingForAnswerAck: false, actionError: null, actionErrorReason: null, sendEvent: vi.fn(() => true), useRoom: vi.fn(), leaveRoom: vi.fn() };
  vi.mocked(useRoomSocket).mockImplementation(() => socket);
});
afterEach(() => { vi.clearAllMocks(); vi.useRealTimers(); });

it("shows current highlighted context and removes the entire activity when the question is ready", () => {
  const app = render(<App />);
  const activity = screen.getByRole("region", { name: "Panelist activity" });
  expect(within(activity).getByText("Participant recruitment").tagName).toBe("MARK");
  expect(within(activity).getByRole("status")).toHaveTextContent("4s");
  socket.roomState = waitingRoom({ phase: "question", operation: null, panelist_activity: null,
    turns: [{ ...waitingRoom().turns[0], question: "Why this sampling frame?", answer: null, resolved: false }] });
  app.rerender(<App />);
  expect(screen.getByText("Why this sampling frame?")).toBeVisible();
  expect(screen.queryByRole("region", { name: "Panelist activity" })).toBeNull();
  expect(socket.sendEvent).not.toHaveBeenCalled();
});

it("never keeps activity for a ready question even if an obsolete operation arrives with it", () => {
  socket.roomState = waitingRoom({ phase: "question", selected_seat: 0,
    turns: [{ ...waitingRoom().turns[0], answer: null, resolved: false }] });
  render(<App />);
  expect(screen.queryByRole("region", { name: "Panelist activity" })).toBeNull();
  expect(screen.queryByText("Participant recruitment")).toBeNull();
});

it("uses a factual fallback for legacy or mismatched run context without a new command", () => {
  socket.roomState = waitingRoom({ panelist_activity: undefined });
  const app = render(<App />);
  expect(screen.getByRole("region", { name: "Panelist activity" }).querySelector("mark")).toBeNull();
  socket.roomState = waitingRoom({ defense_view_id: "new-run" });
  app.rerender(<App />);
  expect(screen.queryByText("Participant recruitment")).toBeNull();
  expect(screen.getByRole("region", { name: "Panelist activity" })).toHaveTextContent("Preparing your question");
  expect(socket.sendEvent).not.toHaveBeenCalled();
});

it("shows review context without claiming the retained submission has been accepted", () => {
  socket.roomState = waitingRoom({ phase: "interpreting", my_pending_submission: "My retained submission",
    selected_seat: 0, remaining_answer_ms: 80000,
    turns: [{ ...waitingRoom().turns[0], answer: null, resolved: false }],
    operation: { ...waitingRoom().operation!, id: "review:1", kind: "interpretation", stage: "reviewing_answer" },
    panelist_activity: { operation_id: "review:1", view_id: "run-one", reviewer: "Methodology Reviewer", context: "Participant recruitment" } });
  const app = render(<App />);
  const activity = screen.getByRole("region", { name: "Panelist activity" });
  expect(activity).toHaveTextContent("Submission saved, not yet accepted.");
  expect(activity.querySelector("mark")).toHaveTextContent("Participant recruitment");
  socket.roomState = { ...socket.roomState!, phase: "interpretation_retry", operation: null, panelist_activity: null };
  app.rerender(<App />);
  expect(screen.queryByRole("region", { name: "Panelist activity" })).toBeNull();
  expect(screen.getAllByText(/Submission saved, not accepted/).some(element => element.textContent?.includes("Submission saved"))).toBe(true);
});

it("clears highlights during retry backoff and failure while preserving recovery guidance", () => {
  const app = render(<App />);
  socket.roomState = waitingRoom({ operation: { ...waitingRoom().operation!, stage: "retry_wait", retrying: true, retry_at_ms: 9000 } });
  app.rerender(<App />);
  expect(screen.queryByRole("region", { name: "Panelist activity" })).toBeNull();
  expect(screen.getAllByText("Waiting to retry…").length).toBeGreaterThan(0);
  socket.roomState = waitingRoom({ phase: "retry", operation: null, panelist_activity: null, error: "Generation unavailable" });
  app.rerender(<App />);
  expect(screen.queryByRole("region", { name: "Panelist activity" })).toBeNull();
  expect(screen.getAllByText(/resolved turns are saved/i).length).toBeGreaterThan(0);
});

it("keeps server-anchored elapsed time and focus when current context is restored", () => {
  const app = render(<App />);
  const control = screen.getByRole("button", { name: /settings.*controls/i });
  control.focus();
  socket.roomState = waitingRoom({ server_now_ms: 31000, self_is_host: false, self_seat: 1 });
  app.rerender(<App />);
  const activity = screen.getByRole("region", { name: "Panelist activity" });
  expect(activity).toHaveTextContent("30s");
  expect(control).toHaveFocus();
  expect(activity.querySelector("mark")).toHaveTextContent("Participant recruitment");
  expect(socket.sendEvent).not.toHaveBeenCalled();
});

it("renders source phrases as text and retires highlights when a run is ended or restarted", () => {
  socket.roomState = waitingRoom({ panelist_activity: { ...waitingRoom().panelist_activity!, context: '<img src=x onerror="alert(1)">研究 scope' } });
  const app = render(<App />);
  const activity = screen.getByRole("region", { name: "Panelist activity" });
  expect(activity.querySelector("mark")).toHaveTextContent('<img src=x onerror="alert(1)">研究 scope');
  expect(activity.querySelector("img")).toBeNull();
  socket.roomState = waitingRoom({ phase: "complete", operation: null, panelist_activity: null, feedback_status: "none" });
  app.rerender(<App />);
  expect(screen.queryByRole("region", { name: "Panelist activity" })).toBeNull();
  socket.roomState = waitingRoom({ defense_view_id: "restarted-run", turns: [] });
  app.rerender(<App />);
  expect(screen.queryByText(/研究 scope/)).toBeNull();
});

it("uses the same research reviewer name in the heading and activity for a legacy role", () => {
  socket.roomState = waitingRoom({ panelist_activity: { ...waitingRoom().panelist_activity!, reviewer: "Critical Judge" } });
  render(<App />);
  expect(screen.getByRole("heading", { name: "Critical Reviewer" })).toBeVisible();
  expect(within(screen.getByRole("region", { name: "Panelist activity" })).getByText("Critical Reviewer")).toBeVisible();
  expect(screen.queryByRole("heading", { name: "Critical Judge" })).toBeNull();
});

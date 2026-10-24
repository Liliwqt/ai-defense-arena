import { act, render, screen, within } from "@testing-library/react";
import { beforeEach, afterEach, expect, it, vi } from "vitest";
import { App } from "./App";
import { useAccount } from "./hooks/useAccount";
import { useRoomSocket, type RoomSocketState } from "./hooks/useRoomSocket";
import type { RoomState } from "./types";

vi.mock("./hooks/useAccount", () => ({ useAccount: vi.fn() }));
vi.mock("./hooks/useRoomSocket", () => ({ useRoomSocket: vi.fn() }));
let socket: RoomSocketState;
function reviewRoom(extra: Partial<RoomState> = {}): RoomState {
  return {
    room_code: "SAME1", defense_view_id: "run-one", phase: "interpreting", defense_type: "research",
    self_seat: 0, self_is_host: true, revision: 1, error: null, question_budget: 4,
    players: [{ seat: 0, name: "Alex", online: true, is_host: true }], files: ["paper.md"],
    active_panelist: "Methodology Reviewer", feedback_status: "none", feedback: null, server_now_ms: 5000,
    selected_seat: 0, clock_paused: true, remaining_answer_ms: 80000, my_pending_submission: "What does recruitment mean?",
    turns: [{ panelist: "Methodology Reviewer", question: "Who will you invite?", filename: "paper.md",
      evidence_line: 1, evidence_text: "We plan student interviews.", answer: null, answered_by: null, resolved: false, clarifications: [] }],
    operation: { id: "interpretation:1", kind: "interpretation", stage: "reviewing_answer", started_at_ms: 1000, attempt: 1, retrying: false },
    panelist_activity: { operation_id: "interpretation:1", view_id: "run-one", reviewer: "Methodology Reviewer", context: "Participant recruitment" },
    ...extra,
  };
}
beforeEach(() => {
  sessionStorage.clear(); window.history.replaceState(null, "", "/#/room");
  vi.mocked(useAccount).mockReturnValue({ account: { authenticated: true, google_enabled: true, free_access: true }, error: "", refresh: vi.fn(async () => {}) });
  socket = { roomState: reviewRoom(), roomCode: "SAME1", playerToken: "fixture", connected: true, knownHost: true,
    waitingForAnswerAck: false, actionError: null, actionErrorReason: null, sendEvent: vi.fn(() => true), useRoom: vi.fn(), leaveRoom: vi.fn() };
  vi.mocked(useRoomSocket).mockImplementation(() => socket);
});
afterEach(() => { vi.clearAllMocks(); vi.useRealTimers(); });

it("truthfully includes clarification during submission review then removes activity for the explanation", () => {
  const app = render(<App />);
  const activity = screen.getByRole("region", { name: "Panelist activity" });
  expect(activity).toHaveTextContent("Reviewing your answer or clarification…");
  expect(activity).toHaveTextContent("Submission saved, not yet accepted.");
  expect(activity).toHaveTextContent("The panel may clarify the question or ask for one detail.");
  expect(activity.querySelector("mark")).toHaveTextContent("Participant recruitment");
  expect(activity).not.toHaveTextContent("What does recruitment mean?");
  socket.roomState = reviewRoom({ phase: "question", operation: null, panelist_activity: null, my_pending_submission: null,
    turns: [{ ...reviewRoom().turns[0], clarifications: [{ request: "What does recruitment mean?", reply: "Which student group will you invite and how?" }] }] });
  app.rerender(<App />);
  expect(screen.queryByRole("region", { name: "Panelist activity" })).toBeNull();
  expect(screen.getByText("Which student group will you invite and how?")).toBeVisible();
  expect(screen.getByText("What does recruitment mean?")).toBeVisible();
  expect(socket.sendEvent).not.toHaveBeenCalled();
});

function probeReview(extra: Partial<RoomState> = {}): RoomState {
  return reviewRoom({ my_pending_submission: "What list do you mean?",
    operation: { ...reviewRoom().operation!, stage: "reviewing_reply" },
    turns: [{ ...reviewRoom().turns[0], answer: "We will invite volunteers.", answered_by: "Alex",
      probe: { id: "probe-one", request: "From which complete list?", references: [], status: "pending", reply: null, clarifications: [] } }],
    ...extra });
}

it("shows probe-reply activity and removes it for a same-probe clarification with the original answer retained", () => {
  socket.roomState = probeReview();
  const app = render(<App />);
  const activity = screen.getByRole("region", { name: "Panelist activity" });
  expect(activity).toHaveTextContent("Reviewing your probe reply or clarification…");
  expect(activity).toHaveTextContent("Submission saved, not yet accepted.");
  expect(activity).toHaveTextContent("This reply stays on the current question.");
  expect(activity.querySelector("mark")).toHaveTextContent("Participant recruitment");
  expect(within(activity).getByText("Methodology Reviewer")).toBeVisible();
  const turn = socket.roomState!.turns[0];
  socket.roomState = probeReview({ phase: "probe", operation: null, panelist_activity: null, my_pending_submission: null,
    turns: [{ ...turn, probe: { ...turn.probe!, clarifications: [{ request: "What list do you mean?", reply: "Which source lists the students you could invite?" }] } }] });
  app.rerender(<App />);
  expect(screen.queryByRole("region", { name: "Panelist activity" })).toBeNull();
  const probe = screen.getByRole("region", { name: "Panelist probe" });
  expect(probe).toHaveTextContent("From which complete list?");
  expect(probe).toHaveTextContent("Which source lists the students you could invite?");
  expect(screen.getByText("We will invite volunteers.")).toBeVisible();
  expect(socket.sendEvent).not.toHaveBeenCalled();
});

it("replaces submission activity with the ready probe immediately without creating another question", () => {
  const app = render(<App />);
  socket.roomState = probeReview({ phase: "probe", operation: null, panelist_activity: null, my_pending_submission: null });
  app.rerender(<App />);
  expect(screen.queryByRole("region", { name: "Panelist activity" })).toBeNull();
  expect(screen.getByRole("region", { name: "Panelist probe" })).toHaveTextContent("From which complete list?");
  expect(screen.getByText("QUESTION 1 OF 4")).toBeVisible();
  expect(screen.getByText("We will invite volunteers.")).toBeVisible();
  expect(socket.sendEvent).not.toHaveBeenCalled();
});

it("clears probe activity during backoff and restores only the admitted attempt without changing focus or the reply timer", () => {
  socket.roomState = probeReview();
  const app = render(<App />);
  const control = screen.getByRole("button", { name: /settings.*controls/i });
  control.focus();
  socket.roomState = probeReview({ operation: { ...probeReview().operation!, stage: "retry_wait", retrying: true, retry_at_ms: 9000 } });
  app.rerender(<App />);
  expect(screen.queryByRole("region", { name: "Panelist activity" })).toBeNull();
  expect(screen.getAllByText("Waiting to retry…").length).toBeGreaterThan(0);
  socket.roomState = probeReview({ operation: { ...probeReview().operation!, attempt: 2, retrying: true }, server_now_ms: 11000 });
  app.rerender(<App />);
  expect(screen.getByRole("region", { name: "Panelist activity" })).toHaveTextContent("Trying again… Reviewing your probe reply or clarification…");
  expect(screen.getByRole("region", { name: "Panelist activity" })).toHaveTextContent("10s");
  expect(control).toHaveFocus();
  expect(screen.getByRole("status", { name: /reply timer paused/i })).toBeVisible();
  socket.roomState = probeReview({ phase: "interpretation_retry", operation: null, panelist_activity: null });
  app.rerender(<App />);
  expect(screen.queryByRole("region", { name: "Panelist activity" })).toBeNull();
  expect(screen.getAllByText(/Submission saved, not accepted/).length).toBeGreaterThan(0);
  expect(socket.sendEvent).not.toHaveBeenCalled();
});

it("preserves Free mixed guest review through navigation and rejects activity from an old run", () => {
  socket.roomState = probeReview({ practice_tier: "free", defense_type: "mixed", self_is_host: false, self_seat: 1 });
  const app = render(<App />);
  act(() => { window.history.pushState(null, "", "/#/account"); window.dispatchEvent(new PopStateEvent("popstate")); });
  expect(screen.queryByRole("region", { name: "Panelist activity" })).toBeNull();
  socket.roomState = { ...socket.roomState!, server_now_ms: 21000 };
  app.rerender(<App />);
  act(() => { window.history.pushState(null, "", "/#/room"); window.dispatchEvent(new PopStateEvent("popstate")); });
  expect(screen.getByRole("region", { name: "Panelist activity" })).toHaveTextContent("20s");
  socket.roomState = { ...socket.roomState!, defense_view_id: "new-run" };
  app.rerender(<App />);
  expect(screen.getByRole("region", { name: "Panelist activity" }).querySelector("mark")).toBeNull();
  socket.roomState = { ...socket.roomState!, phase: "complete", operation: null, panelist_activity: null };
  app.rerender(<App />);
  expect(screen.queryByRole("region", { name: "Panelist activity" })).toBeNull();
  expect(socket.sendEvent).not.toHaveBeenCalled();
});

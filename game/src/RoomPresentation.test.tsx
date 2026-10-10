import { act, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { App } from "./App";
import { useRoomSocket, type RoomSocketState } from "./hooks/useRoomSocket";
import type { RoomState } from "./types";

// External account/transport boundaries; every room view, including seats, is real.
vi.mock("./hooks/useAccount", () => ({ useAccount: () => ({ account: null, error: "", refresh: vi.fn() }) }));
vi.mock("./hooks/useRoomSocket", () => ({ useRoomSocket: vi.fn() }));

const room = (overrides: Partial<RoomState> = {}): RoomState => ({
  room_code: "ROOM1", self_seat: 0, self_is_host: true, phase: "voting",
  players: [
    { seat: 0, name: "Alex", online: true, is_host: true },
    { seat: 1, name: "Sam", online: true, is_host: false },
    { seat: 2, name: "Lee", online: false, is_host: false },
  ],
  turns: [{ panelist: "Technical Architect", question: "Why keep the queue in memory?",
    filename: "queue.py", evidence_line: 5, evidence_text: "    queue = []", answer: null, answered_by: null }],
  active_panelist: "Technical Architect", error: null, revision: 1, files: ["queue.py"],
  feedback_status: "none", feedback: null, server_now_ms: 1000, vote_deadline_ms: 16000,
  selected_seat: null, vote_counts: { "0": 1, "1": 2 }, ...overrides,
});

function snapshot(state: RoomState | null) {
  const socket: RoomSocketState = {
    roomState: state, connected: true, roomCode: state?.room_code ?? null, knownHost: true,
    waitingForAnswerAck: false, actionError: null, actionErrorReason: null, sendEvent: vi.fn(() => true),
    useRoom: vi.fn(), leaveRoom: vi.fn(), playerToken: "token",
  };
  vi.mocked(useRoomSocket).mockReturnValue(socket);
  return socket;
}

afterEach(() => { vi.useRealTimers(); vi.clearAllMocks(); });

it("keeps real seats, question, countdown and action guidance in step from vote to answer and reassignment", () => {
  vi.useFakeTimers();
  snapshot(room());
  const view = render(<App />);
  fireEvent.click(screen.getByRole("button", { name: /close panel/i }));
  expect(screen.getByText(/Choose a speaker\. You can change/)).toBeTruthy();
  expect(screen.getByLabelText("Technical Architect, asking this question")).toHaveAttribute("aria-current", "true");
  expect(screen.getByLabelText(/Defender seat 2: Sam, online, 2 votes/)).toHaveTextContent("2 votes");
  expect(screen.getByText("Why keep the queue in memory?")).toBeTruthy();
  expect(screen.getByText("queue = []")).toBeTruthy();
  expect(screen.getByRole("timer", { name: "Vote time remaining" })).toHaveTextContent("VOTE 0:15");
  act(() => vi.advanceTimersByTime(1100));
  expect(screen.getByRole("timer")).toHaveTextContent("0:14");

  snapshot(room({ phase: "question", selected_seat: 1, server_now_ms: 2100, answer_deadline_ms: 122100 }));
  view.rerender(<App />);
  expect(screen.getByText(/Sam is answering/)).toBeTruthy();
  expect(screen.getByLabelText(/Defender seat 2: Sam, online, chosen to answer/)).toHaveTextContent("Answering");
  expect(screen.queryByRole("textbox", { name: /chosen to answer/i })).toBeNull();
  expect(screen.getByRole("timer", { name: "Answer time remaining" })).toHaveTextContent("ANSWER 2:00");

  const reassigned = room({ phase: "question", selected_seat: 0, server_now_ms: 3100, answer_deadline_ms: 122100 });
  const socket = snapshot(reassigned);
  view.rerender(<App />);
  expect(screen.getByRole("textbox", { name: /Your turn.*chosen to answer/i })).toBeTruthy();
  expect(screen.getByRole("timer")).toHaveTextContent("1:59");
  expect(screen.getByLabelText(/Defender seat 2: Sam, online$/)).not.toHaveClass("is-active");
  fireEvent.change(screen.getByRole("textbox", { name: /Your turn/i }), { target: { value: "The process keeps the pilot simple." } });
  fireEvent.click(screen.getByRole("button", { name: "Submit answer" }));
  expect(socket.sendEvent).toHaveBeenCalledWith({ type: "submit_answer", turn: 0, answer: "The process keeps the pilot simple." });
  expect(within(screen.getByRole("region", { name: "Panelists" })).getAllByText("Panelist")).toHaveLength(3);
});

it("keeps a research reaction separate until a server snapshot opens voting", () => {
  vi.useFakeTimers();
  const state = room({ defense_type: "research", phase: "reacting", active_panelist: "Critical Judge",
    question_budget: 12, reaction_deadline_ms: 5000,
    turns: [{ ...room().turns[0], panelist: "Critical Judge", lead_in: "The pilot supports a narrower claim.",
      filename: "paper.md", evidence_kind: "markdown", evidence_location: "Line 5" }],
  });
  snapshot(state);
  const view = render(<App />);
  fireEvent.click(screen.getByRole("button", { name: /close panel/i }));
  expect(screen.getByLabelText("Critical Reviewer, speaking")).toHaveTextContent("Speaking");
  expect(screen.getByRole("heading", { name: "Critical Reviewer" })).toBeTruthy();
  expect(screen.getByText("The pilot supports a narrower claim.")).toBeTruthy();
  expect(screen.queryByText("Why keep the queue in memory?")).toBeNull();
  expect(screen.queryByText("queue = []")).toBeNull();
  expect(screen.queryByRole("timer")).toBeNull();
  act(() => vi.advanceTimersByTime(12000));
  // Time passing in a client cannot publish a question or open voting.
  expect(screen.getByText("The pilot supports a narrower claim.")).toBeTruthy();
  expect(screen.queryByRole("button", { name: /Vote for/ })).toBeNull();
  snapshot({ ...state, phase: "voting", server_now_ms: 13000, vote_deadline_ms: 28000 });
  view.rerender(<App />);
  expect(screen.queryByText("The pilot supports a narrower claim.")).toBeNull();
  expect(screen.getByLabelText("Critical Reviewer, asking this question")).toHaveTextContent("Asking");
  expect(screen.getByRole("timer")).toHaveTextContent("VOTE 0:15");
  expect(screen.getByText(/Question 1 of 12 · Critical/)).toBeTruthy();
  expect(screen.getByText("queue = []")).toBeTruthy();
});

it("shows factual no-defender guidance and an unknown countdown without a deadline", () => {
  snapshot(room({ phase: "question", selected_seat: null, answer_deadline_ms: null,
    players: room().players.map(player => ({ ...player, online: false })) }));
  const view = render(<App />);
  fireEvent.click(screen.getByRole("button", { name: /close panel/i }));
  expect(screen.getByText(/Waiting for a defender to reconnect/)).toBeTruthy();
  expect(screen.queryByRole("textbox", { name: /chosen to answer/i })).toBeNull();
  expect(screen.getByRole("timer")).toHaveTextContent("ANSWER --:--");
  expect(screen.queryByLabelText(/chosen to answer/)).toBeNull();
  snapshot(null);
  view.rerender(<App />);
  expect(screen.getByText("No room yet")).toBeTruthy();
  expect(screen.getByText("Your defense begins here")).toBeTruthy();
  expect(screen.queryByRole("timer")).toBeNull();
  expect(screen.getAllByText("Open seat")).toHaveLength(4);
});

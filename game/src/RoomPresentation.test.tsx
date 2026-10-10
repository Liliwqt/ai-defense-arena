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

it("keeps clarification and a pending reply on the same turn and describes paused/running review accurately", () => {
  vi.useFakeTimers();
  const source = room().turns[0];
  const state = room({ phase: "question", selected_seat: 0, answer_deadline_ms: 121000,
    turns: [{ ...source, clarifications: [{ request: "Say it simply?", reply: "Why store requests only while the app runs?" }] }] });
  snapshot(state);
  const view = render(<App />);
  fireEvent.click(screen.getByRole("button", { name: /close panel/i }));
  expect(screen.getByText("Say it simply?")).toBeTruthy();
  expect(screen.getByText("Why store requests only while the app runs?")).toBeTruthy();
  expect(screen.queryByText(source.question)).toBeNull();
  const pending = { ...source, answer: "It keeps the pilot small.", answered_by: "Alex", answered_by_seat: 0,
    resolved: false, probe: { id: "p1", request: "How will requests survive a restart?", status: "pending" as const,
      references: [], reply: null, clarifications: [] } };
  snapshot({ ...state, phase: "probe", turns: [pending], answer_deadline_ms: 31000 });
  view.rerender(<App />);
  expect(screen.getByRole("textbox", { name: /Reply to panelist/ })).toBeTruthy();
  expect(screen.getByLabelText(/Defender seat 1: Alex/)).toHaveTextContent("Replying");
  expect(screen.getByRole("timer", { name: "Reply time remaining" })).toHaveTextContent("REPLY 0:30");
  expect(screen.getByText("QUESTION 1")).toBeTruthy();
  expect(screen.getByText(/0 RESOLVED/)).toBeTruthy();
  expect(screen.getByText("It keeps the pilot small.")).toBeTruthy();
  expect(screen.getByText("queue = []")).toBeTruthy();
  snapshot({ ...state, phase: "interpreting", turns: [pending], clock_paused: true, remaining_answer_ms: 25000 });
  view.rerender(<App />);
  expect(screen.getByLabelText(/Defender seat 1: Alex/)).toHaveTextContent("Selected");
  expect(screen.getByText("Reviewing submission · Timer paused")).toBeTruthy();
  expect(screen.getByRole("status", { name: "Reply timer paused" })).toHaveTextContent("PAUSED 0:25");
  act(() => vi.advanceTimersByTime(2000));
  expect(screen.getByRole("status", { name: "Reply timer paused" })).toHaveTextContent("0:25");
  snapshot({ ...state, phase: "interpreting", turns: [pending], clock_paused: false, answer_deadline_ms: 26000 });
  view.rerender(<App />);
  expect(screen.getByText("Reviewing submission · Timer running")).toBeTruthy();
  expect(screen.getByRole("timer", { name: "Reply time remaining" })).toHaveTextContent("0:25");
  expect(screen.getByRole("button", { name: "Submit reply directly" })).toBeTruthy();
  act(() => vi.advanceTimersByTime(2100));
  expect(screen.getByRole("timer", { name: "Reply time remaining" })).toHaveTextContent("0:23");
});

it("offers recovery only to the host and selected defender, respecting exhausted attempts and acknowledgment", () => {
  const state = room({ phase: "interpretation_retry", selected_seat: 1, interpretation_attempts_left: 0,
    remaining_answer_ms: 45000, my_pending_submission: null });
  snapshot(state);
  const view = render(<App />);
  fireEvent.click(screen.getByRole("button", { name: /close panel/i }));
  expect(screen.getByRole("button", { name: "Retry panelist" })).toBeDisabled();
  expect(screen.queryByRole("button", { name: "Write a new answer" })).toBeNull();
  expect(screen.queryByRole("button", { name: "Use this as my answer" })).toBeNull();
  expect(screen.getByText(/No panelist retries remain/)).toBeTruthy();
  snapshot({ ...state, self_seat: 1, self_is_host: false, my_pending_submission: "Keep this saved answer." });
  view.rerender(<App />);
  expect(screen.getByRole("button", { name: "Use this as my answer" })).toBeEnabled();
  const pending = snapshot({ ...state, self_seat: 1, self_is_host: false, interpretation_attempts_left: 3, my_pending_submission: "Keep this saved answer." });
  pending.waitingForAnswerAck = true;
  view.rerender(<App />);
  expect(screen.getByRole("button", { name: "Retry panelist" })).toBeDisabled();
  expect(screen.getByRole("button", { name: "Use this as my answer" })).toBeDisabled();
  expect(screen.getByRole("button", { name: "Write a new answer" })).toBeDisabled();
  pending.waitingForAnswerAck = false;
  view.rerender(<App />);
  fireEvent.click(screen.getByRole("button", { name: "Write a new answer" }));
  expect(screen.getByRole("textbox")).toHaveValue("Keep this saved answer.");
  const socket = snapshot({ ...state, self_seat: 1, self_is_host: false, my_pending_submission: "Keep this saved answer." });
  socket.waitingForAnswerAck = true;
  view.rerender(<App />);
  expect(screen.getByRole("button", { name: "Sending…" })).toBeDisabled();
  expect(screen.getByRole("textbox")).toHaveValue("Keep this saved answer.");
  snapshot({ ...state, self_seat: 2, self_is_host: false });
  view.rerender(<App />);
  expect(screen.queryByRole("button", { name: "Retry panelist" })).toBeNull();
  expect(screen.queryByRole("textbox", { name: /answer/i })).toBeNull();
});

it("gives truthful shared mapping, preparation, missed-turn and exhausted recovery guidance", () => {
  const state = room({ phase: "lobby", defense_type: "research", turns: [], active_panelist: null,
    research_planning_status: "planning" });
  snapshot(state);
  const view = render(<App />);
  fireEvent.click(screen.getByRole("button", { name: /close panel/i }));
  expect(screen.getByRole("status", { name: "Room status" })).toHaveTextContent("Mapping research…");
  expect(within(screen.getByRole("region", { name: "Answer area" })).getByText(/Mapping research/)).toBeTruthy();
  expect(screen.queryByRole("timer")).toBeNull();
  snapshot({ ...state, phase: "generating", research_planning_status: "ready" });
  view.rerender(<App />);
  expect(screen.getByText("Preparing the first question…")).toBeTruthy();
  expect(screen.queryByText("QUESTION 1")).toBeNull();
  const missed = { ...room().turns[0], timed_out: true };
  snapshot({ ...state, phase: "generating", turns: [missed] });
  view.rerender(<App />);
  expect(screen.getByRole("status", { name: "Room status" })).toHaveTextContent("Reviewing missed turn…");
  expect(screen.getByText(/Time expired · question passed/)).toBeTruthy();
  snapshot({ ...state, phase: "retry", turns: [missed], question_attempts_left: 0 });
  view.rerender(<App />);
  fireEvent.click(screen.getByRole("button", { name: /settings.*controls/i }));
  expect(screen.getByRole("button", { name: "Retry question" })).toBeDisabled();
  expect(within(screen.getByRole("region", { name: "Answer area" })).getByText(/No question retries remain/)).toBeTruthy();
});

it.each(["none", "generating", "failed", "ready"] as const)("shows completion and %s coaching without an answering seat or countdown", (feedback_status) => {
  const state = room({ phase: "complete", selected_seat: 0, answer_deadline_ms: 121000,
    coaching_attempts_left: 0, feedback_status,
    turns: [{ ...room().turns[0], answer: "A saved answer", resolved: true, answered_by: "Alex" }] });
  snapshot(state);
  render(<App />);
  fireEvent.click(screen.getByRole("button", { name: /close panel/i }));
  expect(screen.queryByRole("timer")).toBeNull();
  expect(screen.getByLabelText(/Defender seat 1: Alex/)).not.toHaveClass("is-active");
  expect(screen.getByText("1 RESOLVED")).toBeTruthy();
  if (feedback_status === "failed") {
    expect(within(screen.getByRole("region", { name: "Answer area" })).getByText(/No coaching report retries remain/)).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: /settings.*controls/i }));
    expect(screen.getByRole("button", { name: "Retry coaching report" })).toBeDisabled();
    fireEvent.click(within(screen.getByRole("dialog", { name: "Controls" })).getByRole("button", { name: "Transcript" }));
    expect(within(screen.getByRole("region", { name: "Coaching report" })).getByText(/No coaching report retries remain/)).toBeTruthy();
  } else if (feedback_status === "generating") {
    expect(screen.getByRole("status", { name: "Room status" })).toHaveTextContent("Preparing coaching…");
  } else if (feedback_status === "ready") {
    expect(screen.getByRole("status", { name: "Room status" })).toHaveTextContent("Coaching ready");
  } else {
    expect(screen.getByRole("status", { name: "Room status" })).toHaveTextContent("Complete");
    expect(screen.getByText("Open Transcript to review your answers.")).toBeTruthy();
  }
});

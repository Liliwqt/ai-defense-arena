import { act, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { App } from "./App";
import { useRoomSocket } from "./hooks/useRoomSocket";
import type { RoomSocketState } from "./hooks/useRoomSocket";
import type { RoomState, Turn } from "./types";
import { researchPlanPreview } from "./researchPlanPreview";

vi.mock("./hooks/useAccount", () => ({ useAccount: () => ({account: null, error: "", refresh: vi.fn(async () => {})}) }));
vi.mock("./hooks/useRoomSocket", () => ({ useRoomSocket: vi.fn() }));
vi.mock("./components/FlatRoom", () => ({
  PanelistSeats: () => <div data-testid="panelist-row" />,
  DefenderSeats: ({ presenterMoment }: { presenterMoment: { seat: number } | null }) =>
    <div data-testid="seat-rows" data-presenter-seat={presenterMoment?.seat ?? ""} />,
}));

const turn = (answer: string | null, seat: number | null): Turn => ({
  panelist: "Technical Architect", question: "Why use SQLite?", filename: "queue.py",
  evidence_line: 5, evidence_text: "DATABASE = 'queue.db'", answer,
  answered_by: answer ? "Alex" : null, answered_by_seat: seat,
});
const room = (turns: Turn[], phase: RoomState["phase"] = "question"): RoomState => ({
  room_code: "ROOM1", self_seat: 0, self_is_host: true, phase,
  players: [
    { seat: 0, name: "Alex", online: true, is_host: true },
    { seat: 1, name: "Alex", online: true, is_host: false },
  ],
  turns, active_panelist: "Technical Architect", error: null, revision: 1,
  files: ["queue.py"], feedback_status: "none", feedback: null, selected_seat: 0,
});
const socket = (state: RoomState | null): RoomSocketState => ({
  roomState: state, connected: true, roomCode: "ROOM1", knownHost: true,
  waitingForAnswerAck: false, actionError: null, actionErrorReason: null, sendEvent: vi.fn(() => true),
  useRoom: vi.fn(), leaveRoom: vi.fn(), playerToken: "token",
});
const setSocket = (state: RoomState | null) => vi.mocked(useRoomSocket).mockReturnValue(socket(state));

afterEach(() => { vi.useRealTimers(); vi.clearAllMocks(); });

describe("flat room flow", () => {
  it("keeps research advice separate from the question and accepted answer in the room and transcript", async () => {
    const advice = "One option is to narrow the claim if recruitment access is limited.";
    const answer = "We retained the pilot and limited our conclusions to its participants.";
    const question = "How will the team define the pilot's scope?";
    const state: RoomState = { ...room([{ ...turn(answer, 0), panelist: "Methodology Reviewer",
      lead_in: advice, question, filename: "paper.md", evidence_text: "We plan a small campus pilot.",
    }], "complete"), defense_type: "research", feedback_status: "ready", feedback: {
      summary: "The team explained its scope.", strengths: [{ turn: 0, text: "Justified the scope limit." }],
      improvements: [], next_step: "Document the limits of the pilot claim.",
    } };
    setSocket({ ...state, phase: "question", turns: [{ ...state.turns[0], answer: null }] });
    const view = render(<App />);
    await userEvent.click(screen.getByRole("button", { name: /close panel/i }));
    expect(screen.getByText(advice)).toBeTruthy();
    expect(screen.getByText(question)).toBeTruthy();
    expect(screen.getByText("We plan a small campus pilot.")).toBeTruthy();
    setSocket(state);
    view.rerender(<App />);
    await userEvent.click(screen.getByRole("button", { name: /settings.*controls/i }));
    await userEvent.click(within(screen.getByRole("dialog", { name: "Controls" })).getByRole("button", { name: "Transcript" }));
    const transcript = screen.getByRole("dialog", { name: "Transcript" });
    expect(within(transcript).getByText(advice)).toBeTruthy();
    expect(within(transcript).getByText(answer)).toBeTruthy();
    expect(within(transcript).getByText("Justified the scope limit.")).toBeTruthy();
  });
  it("allows upright-phone participation without a blocking rotation instruction", async () => {
    setSocket(room([turn(null, null)]));
    render(<App />);
    expect(screen.queryByText("Rotate your phone")).toBeNull();
    await userEvent.click(screen.getByRole("button", { name: /close panel/i }));
    const answer = screen.getByRole("textbox", { name: /chosen to answer/i });
    await userEvent.type(answer, "A draft that survives orientation changes.");
    act(() => window.dispatchEvent(new Event("resize")));
    expect(answer).toHaveValue("A draft that survives orientation changes.");
    expect(screen.getByText("DATABASE = 'queue.db'")).toBeTruthy();
  });
  it("opens Transcript through Settings and restores focus without losing the answer draft", async () => {
    setSocket(room([turn(null, null)]));
    render(<App />);
    await userEvent.click(screen.getByRole("button", { name: /close panel/i }));
    const answer = screen.getByRole("textbox", { name: /chosen to answer/i });
    await userEvent.type(answer, "Keep this same-turn draft.");
    const settings = screen.getByRole("button", { name: /settings.*controls/i });
    await userEvent.click(settings);
    const controls = screen.getByRole("dialog", { name: "Controls" });
    expect(within(controls).getByText("ROOM1")).toBeTruthy();
    await userEvent.click(within(controls).getByRole("button", { name: "Transcript" }));
    expect(screen.getByRole("dialog", { name: "Transcript" })).toBeTruthy();
    expect(screen.getByRole("button", { name: /close panel/i })).toHaveFocus();
    await userEvent.keyboard("{Escape}");
    expect(settings).toHaveFocus();
    expect(answer).toHaveValue("Keep this same-turn draft.");
    await userEvent.click(screen.getByRole("button", { name: "Account" }));
    expect(screen.getByRole("dialog", { name: "Account" })).toBeTruthy();
  });

  it("distinguishes opening preparation, answer review and missed-turn review", async () => {
    setSocket(room([], "generating"));
    const view = render(<App />);
    await userEvent.click(screen.getByRole("button", { name: /close panel/i }));
    expect(screen.getByRole("status", { name: "Room status" })).toHaveTextContent("Preparing question…");
    setSocket(room([turn("We use SQLite for a single-machine prototype.", 0)], "generating"));
    view.rerender(<App />);
    expect(screen.getByRole("status", { name: "Room status" })).toHaveTextContent("Reviewing answer…");
    setSocket(room([{ ...turn(null, null), timed_out: true }], "generating"));
    view.rerender(<App />);
    expect(screen.getByRole("status", { name: "Room status" })).toHaveTextContent("Reviewing missed turn…");
  });

  it.each([
    ["no room", null, "Ready"],
    ["lobby", room([], "lobby"), "Ready"],
    ["mapping", { ...room([], "lobby"), research_planning_status: "planning" }, "Mapping research…"],
    ["map failure", { ...room([], "lobby"), research_planning_status: "failed" }, "Retry needed"],
    ["question failure", room([turn("Accepted answer", 0)], "retry"), "Retry needed"],
    ["coaching pending", { ...room([turn("Accepted answer", 0)], "complete"), feedback_status: "generating" }, "Complete"],
    ["coaching failure", { ...room([turn("Accepted answer", 0)], "complete"), feedback_status: "failed" }, "Complete"],
  ] as const)("shows a factual room status during %s", (_label, state, expected) => {
    setSocket(state);
    render(<App />);
    expect(screen.getByRole("status", { name: "Room status" })).toHaveTextContent(expected);
    expect(screen.queryByRole("timer")).toBeNull();
  });

  it.each([
    ["voting", "Vote time remaining", "VOTE 0:15"],
    ["question", "Answer time remaining", "ANSWER 2:00"],
    ["interpreting", "Answer timer paused", "PAUSED 0:45"],
    ["interpretation_retry", "Answer timer paused", "PAUSED 0:45"],
  ] as const)("keeps server-provided time during %s", (phase, label, expected) => {
    setSocket({ ...room([turn(null, null)], phase), server_now_ms: 1_000_000,
      vote_deadline_ms: phase === "voting" ? 1_015_000 : null,
      answer_deadline_ms: phase === "question" ? 1_120_000 : null,
      remaining_answer_ms: 45_000 });
    render(<App />);
    const timer = screen.getByRole(phase === "voting" || phase === "question" ? "timer" : "status", { name: label });
    expect(timer).toHaveTextContent(expected);
    expect(screen.queryByRole("status", { name: "Room status" })).toBeNull();
  });

  it("does not invent remaining time when the server deadline is absent", () => {
    setSocket(room([turn(null, null)]));
    render(<App />);
    expect(screen.getByRole("timer", { name: "Answer time remaining" })).toHaveTextContent("ANSWER --:--");
  });

  it("makes research coverage and Transcript inspectable by a guest without host controls", async () => {
    const state: RoomState = { ...room([...Array.from({ length: 10 }, () => turn("Earlier answer", 0)), turn(null, null)]),
      self_is_host: false, defense_type: "research", question_budget: 24,
      research_plan: researchPlanPreview,
      coverage: { [researchPlanPreview.topics[0].id]: { status: "addressed", turns: [0], reason: "Discussed" } } };
    setSocket(state);
    render(<App />);
    expect(screen.getByText("QUESTION 11 OF 24")).toBeTruthy();
    const controls = screen.getByRole("dialog", { name: "Controls" });
    expect(within(controls).getByText(`1 of ${researchPlanPreview.topics.length} topics addressed`)).toBeTruthy();
    expect(within(controls).queryByRole("button", { name: "End defense" })).toBeNull();
    await userEvent.click(within(controls).getByRole("button", { name: "Transcript" }));
    expect(screen.getByRole("dialog", { name: "Transcript" }).textContent).toContain("Earlier answer");
  });

  it("shows rejected host actions in Controls while keeping the room visible", () => {
    const state = room([], "lobby");
    vi.mocked(useRoomSocket).mockReturnValue({
      ...socket(state), actionError: "You need 10 available test credits to start a defense.",
    });
    render(<App />);
    const controls = screen.getByRole("dialog");
    expect(controls.textContent).toContain("You need 10 available test credits");
    expect(screen.getByTestId("seat-rows")).toBeTruthy();
  });

  it("does not replay past answers on the first snapshot, then focuses the accepted seat", () => {
    setSocket(null);
    const view = render(<App />);
    setSocket(room([turn("Earlier answer", 0)], "generating"));
    view.rerender(<App />);
    expect(screen.getByTestId("seat-rows").getAttribute("data-presenter-seat")).toBe("");
    setSocket(room([turn("Earlier answer", 0), turn("New answer", 1)], "generating"));
    view.rerender(<App />);
    expect(screen.getByTestId("seat-rows").getAttribute("data-presenter-seat")).toBe("1");
  });

  it("keeps the selected speaker's answer input in the bottom dock", async () => {
    setSocket(room([turn(null, null)]));
    render(<App />);
    await userEvent.click(screen.getByRole("button", { name: /close panel/i }));
    const textbox = screen.getByRole("textbox", { name: /chosen to answer/i });
    expect(textbox.closest("#room-dock")).toBeTruthy();
    expect(screen.getByText("DATABASE = 'queue.db'")).toBeTruthy();
    const panelists = screen.getByTestId("panelist-row");
    const question = document.querySelector("#question-card")!;
    const defenders = screen.getByTestId("seat-rows");
    expect(panelists.compareDocumentPosition(question) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(question.compareDocumentPosition(defenders) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it("waits for the final presenter moment before opening Transcript", () => {
    vi.useFakeTimers();
    setSocket(room([turn("A1", 0), turn("A2", 1), turn("A3", 0)], "question"));
    const view = render(<App />);
    setSocket(room([turn("A1", 0), turn("A2", 1), turn("A3", 0), turn("Final answer", 1)], "complete"));
    view.rerender(<App />);
    expect(screen.getByTestId("seat-rows").getAttribute("data-presenter-seat")).toBe("1");
    expect(screen.queryByRole("heading", { name: "Transcript" })).toBeNull();
    act(() => vi.advanceTimersByTime(2600));
    expect(screen.getByRole("heading", { name: "Transcript" })).toBeTruthy();
  });
});

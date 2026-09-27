import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { App } from "./App";
import { useRoomSocket } from "./hooks/useRoomSocket";
import type { RoomSocketState } from "./hooks/useRoomSocket";
import type { RoomState, Turn } from "./types";

vi.mock("./hooks/useRoomSocket", () => ({ useRoomSocket: vi.fn() }));
vi.mock("./components/ThreeDefenseScene", () => ({
  ThreeDefenseScene: ({ presenterMoment }: { presenterMoment: { seat: number } | null }) =>
    <div data-testid="scene" data-presenter-seat={presenterMoment?.seat ?? ""} />,
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
  files: ["queue.py"], feedback_status: "none", feedback: null,
});
const socket = (state: RoomState | null): RoomSocketState => ({
  roomState: state, connected: true, roomCode: "ROOM1", knownHost: true,
  waitingForAnswerAck: false, actionError: null, sendEvent: vi.fn(() => true),
  useRoom: vi.fn(), leaveRoom: vi.fn(), playerToken: "token",
});
const setSocket = (state: RoomState | null) => vi.mocked(useRoomSocket).mockReturnValue(socket(state));

afterEach(() => { vi.useRealTimers(); vi.clearAllMocks(); });

describe("illustrated room flow", () => {
  it("does not replay past answers on the first snapshot, then focuses the accepted seat", () => {
    setSocket(null);
    const view = render(<App />);
    setSocket(room([turn("Earlier answer", 0)], "generating"));
    view.rerender(<App />);
    expect(screen.getByTestId("scene").getAttribute("data-presenter-seat")).toBe("");
    setSocket(room([turn("Earlier answer", 0), turn("New answer", 1)], "generating"));
    view.rerender(<App />);
    expect(screen.getByTestId("scene").getAttribute("data-presenter-seat")).toBe("1");
  });

  it("opens a focused answer panel from the question card", async () => {
    setSocket(room([turn(null, null)]));
    render(<App />);
    await userEvent.click(screen.getByRole("button", { name: /close panel/i }));
    await userEvent.click(screen.getByRole("button", { name: /answer question/i }));
    const textbox = screen.getByRole("textbox", { name: /your answer/i });
    expect(textbox).toBe(document.activeElement);
    expect(screen.getAllByText("DATABASE = 'queue.db'")).toHaveLength(2);
  });

  it("waits for the final presenter moment before opening Transcript", () => {
    vi.useFakeTimers();
    setSocket(room([turn("A1", 0), turn("A2", 1), turn("A3", 0)], "question"));
    const view = render(<App />);
    setSocket(room([turn("A1", 0), turn("A2", 1), turn("A3", 0), turn("Final answer", 1)], "complete"));
    view.rerender(<App />);
    expect(screen.getByTestId("scene").getAttribute("data-presenter-seat")).toBe("1");
    expect(screen.queryByRole("heading", { name: "Transcript" })).toBeNull();
    act(() => vi.advanceTimersByTime(2600));
    expect(screen.getByRole("heading", { name: "Transcript" })).toBeTruthy();
  });
});

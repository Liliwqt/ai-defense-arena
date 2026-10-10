import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { RoomDock } from "./RoomDock";
import type { RoomState } from "../types";

const state: RoomState = {
  room_code: "ROOMA", self_seat: 0, self_is_host: true, phase: "voting",
  players: [
    { seat: 0, name: "Alex", online: true, is_host: true },
    { seat: 1, name: "Sam", online: true, is_host: false },
  ],
  turns: [{ panelist: "Technical Architect", question: "Why?", filename: "queue.py",
    evidence_line: 1, evidence_text: "value = 1", answer: null, answered_by: null }],
  active_panelist: "Technical Architect", error: null, revision: 1,
  files: ["queue.py"], feedback_status: "none", feedback: null,
  server_now_ms: 1_000_000, vote_deadline_ms: 1_015_000, answer_deadline_ms: null,
  selected_seat: null, vote_counts: { "0": 1, "1": 0 }, my_vote: 0, chat: [],
};
const props = { connected: true, previewMode: false, waitingForAnswerAck: false, actionError: null };

describe("RoomDock", () => {
  it("moves between dock tabs with the arrow keys", () => {
    render(<RoomDock {...props} roomState={state} onSendEvent={() => true} />);
    const actionTab = screen.getByRole("tab", { name: "Vote / Answer" });
    fireEvent.keyDown(actionTab, { key: "ArrowRight" });
    const chatTab = screen.getByRole("tab", { name: "Team chat" });
    expect(chatTab.getAttribute("aria-selected")).toBe("true");
    expect(document.activeElement).toBe(chatTab);
    fireEvent.keyDown(chatTab, { key: "ArrowLeft" });
    expect(actionTab.getAttribute("aria-selected")).toBe("true");
    expect(document.activeElement).toBe(actionTab);
  });

  it("shows live votes and lets a defender change their vote", async () => {
    const send = vi.fn(() => true);
    render(<RoomDock {...props} roomState={state} onSendEvent={send} />);
    expect(screen.getByRole("tab", { name: "Vote / Answer" })).toBeTruthy();
    expect(screen.getByRole("button", { name: /Alex.*1/ }).getAttribute("aria-pressed")).toBe("true");
    await userEvent.click(screen.getByRole("button", { name: /Sam.*0/ }));
    expect(send).toHaveBeenCalledWith({ type: "cast_vote", seat: 1 });
  });

  it("sends team chat and shows an unread indicator after switching away", async () => {
    const send = vi.fn(() => true);
    const view = render(<RoomDock {...props} roomState={state} onSendEvent={send} />);
    await userEvent.click(screen.getByRole("tab", { name: "Team chat" }));
    await userEvent.type(screen.getByRole("textbox", { name: "Team message" }), "Discuss the queue");
    await userEvent.click(screen.getByRole("button", { name: "Send" }));
    expect(send).toHaveBeenCalledWith({ type: "send_chat", text: "Discuss the queue" });
    await userEvent.click(screen.getByRole("tab", { name: "Vote / Answer" }));
    view.rerender(<RoomDock {...props} roomState={{ ...state, chat: [{ id: 1, seat: 1, name: "Sam", text: "Check the lock", sent_at_ms: 1_000_100 }] }} onSendEvent={send} />);
    expect(screen.getByRole("tab", { name: "Team chat (1)" })).toBeTruthy();
    await userEvent.click(screen.getByRole("tab", { name: "Team chat (1)" }));
    expect(screen.getByText(/Check the lock/)).toBeTruthy();
  });

  it("shows the chosen answer form only to that defender", () => {
    const question = { ...state, phase: "question" as const, selected_seat: 1, vote_deadline_ms: null, answer_deadline_ms: 1_120_000 };
    const view = render(<RoomDock {...props} roomState={question} onSendEvent={() => true} />);
    expect(screen.queryByRole("textbox", { name: /chosen to answer/i })).toBeNull();
    expect(screen.getByText(/Sam is answering/)).toBeTruthy();
    view.rerender(<RoomDock {...props} roomState={{ ...question, self_seat: 1 }} onSendEvent={() => true} />);
    expect(screen.getByRole("textbox", { name: /chosen to answer/i })).toBeTruthy();
  });
});

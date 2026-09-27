import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AnswerComposer } from "./AnswerComposer";
import type { RoomState } from "../types";

const questionState: RoomState = {
  room_code: "TEST", self_seat: 0, self_is_host: true, phase: "question",
  players: [], turns: [{ panelist: "Technical Architect", question: "Why SQLite?", filename: "queue.py", evidence_line: 5, evidence_text: "DATABASE = 'queue.db'", answer: null, answered_by: null }],
  active_panelist: "Technical Architect", error: null, revision: 1, files: [], feedback_status: "none", feedback: null, selected_seat: 0,
};

const defaults = {
  connected: true,
  previewMode: false,
  waitingForAnswerAck: false,
  actionError: null,
  onSendEvent: vi.fn(() => true),
};

describe("AnswerComposer", () => {
  it("submits the active turn from the bottom composer", async () => {
    const send = vi.fn(() => true);
    render(<AnswerComposer {...defaults} roomState={questionState} onSendEvent={send} />);
    await userEvent.type(screen.getByRole("textbox", { name: /chosen to answer/i }), "  We chose SQLite for this prototype.  ");
    await userEvent.click(screen.getByRole("button", { name: /submit answer/i }));
    expect(send).toHaveBeenCalledWith({ type: "submit_answer", turn: 0, answer: "We chose SQLite for this prototype." });
  });

  it("keeps a draft and shows an inline error if sending fails", async () => {
    render(<AnswerComposer {...defaults} roomState={questionState} onSendEvent={() => false} />);
    const field = screen.getByRole("textbox", { name: /chosen to answer/i }) as HTMLTextAreaElement;
    await userEvent.type(field, "We would measure the queue time.");
    await userEvent.click(screen.getByRole("button", { name: /submit answer/i }));
    expect(field.value).toBe("We would measure the queue time.");
    expect(screen.getByRole("alert").textContent).toMatch(/could not send/i);
  });

  it("disables repeat submission while waiting and clears the draft for a new turn", async () => {
    const { rerender } = render(<AnswerComposer {...defaults} roomState={questionState} />);
    const field = screen.getByRole("textbox", { name: /chosen to answer/i }) as HTMLTextAreaElement;
    await userEvent.type(field, "First answer");
    rerender(<AnswerComposer {...defaults} roomState={questionState} waitingForAnswerAck />);
    expect((screen.getByRole("button", { name: /sending/i }) as HTMLButtonElement).disabled).toBe(true);
    const next: RoomState = { ...questionState, revision: 2, turns: [
      { ...questionState.turns[0], answer: "First answer", answered_by: "Alex" },
      { panelist: "Security Reviewer", question: "Who may read names?", filename: "queue.py", evidence_line: 9, evidence_text: "x", answer: null, answered_by: null },
    ] };
    rerender(<AnswerComposer {...defaults} roomState={next} />);
    expect((screen.getByRole("textbox", { name: /chosen to answer/i }) as HTMLTextAreaElement).value).toBe("");
  });

  it("uses Ctrl+Enter to submit and plain Enter for a new line", async () => {
    const send = vi.fn(() => true);
    render(<AnswerComposer {...defaults} roomState={questionState} onSendEvent={send} />);
    const field = screen.getByRole("textbox", { name: /chosen to answer/i });
    await userEvent.type(field, "First line{enter}second line{Control>}{Enter}{/Control}");
    expect(send).toHaveBeenCalledWith({ type: "submit_answer", turn: 0, answer: "First line\nsecond line" });
  });

  it("shows a waiting state instead of an input while the next question generates", () => {
    render(<AnswerComposer {...defaults} roomState={{ ...questionState, phase: "generating" }} />);
    expect(screen.queryByRole("textbox")).toBeNull();
    expect(screen.getByRole("status").textContent).toMatch(/preparing/i);
  });
});

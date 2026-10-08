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
  it("sends a direct answer after two clarifications without interpretation", async () => {
    const send = vi.fn(() => true);
    const state = { ...questionState, turns: [{ ...questionState.turns[0], clarifications: [
      { request: "Simplify", reply: "Explain the choice." }, { request: "Example", reply: "Consider the queue." },
    ] }] };
    render(<AnswerComposer {...defaults} roomState={state} onSendEvent={send} />);
    await userEvent.type(screen.getByRole("textbox"), "It fits our small pilot.");
    await userEvent.click(screen.getByRole("button", { name: /submit answer/i }));
    expect(send).toHaveBeenCalledWith({ type: "submit_direct_answer", turn: 0, answer: "It fits our small pilot." });
  });

  it("disables another interpretation retry when attempts are exhausted", () => {
    render(<AnswerComposer {...defaults} roomState={{ ...questionState, phase: "interpretation_retry", interpretation_attempts_left: 0, my_pending_submission: "Our answer" }} />);
    expect(screen.getByRole("button", { name: "Retry panelist" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Use this as my answer" })).not.toBeDisabled();
  });

  it("lets the chosen defender write a different direct answer during recovery", async () => {
    const send = vi.fn(() => true);
    render(<AnswerComposer {...defaults} onSendEvent={send} roomState={{ ...questionState,
      phase: "interpretation_retry", interpretation_attempts_left: 5, my_pending_submission: "Explain?" }} />);
    await userEvent.click(screen.getByRole("button", { name: "Write a new answer" }));
    await userEvent.clear(screen.getByRole("textbox"));
    await userEvent.type(screen.getByRole("textbox"), "Our actual explanation.");
    await userEvent.click(screen.getByRole("button", { name: "Submit answer directly" }));
    expect(send).toHaveBeenCalledWith({ type: "submit_direct_answer", turn: 0, answer: "Our actual explanation." });
  });

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

  it("preserves a pending submission and offers explicit retry or answer after AI failure", async () => {
    const send = vi.fn(() => true);
    const state: RoomState = { ...questionState, phase: "interpretation_retry",
      remaining_answer_ms: 35_000, my_pending_submission: "Can you give an example?",
      error: "AI request failed." };
    render(<AnswerComposer {...defaults} roomState={state} onSendEvent={send} />);
    expect(screen.getByText("Can you give an example?")).toBeTruthy();
    await userEvent.click(screen.getByRole("button", { name: "Retry panelist" }));
    await userEvent.click(screen.getByRole("button", { name: "Use this as my answer" }));
    expect(send).toHaveBeenCalledWith({ type: "retry_interpretation" });
    expect(send).toHaveBeenCalledWith({ type: "use_pending_as_answer" });
  });

  it("clears the draft after a clarification on the same turn", async () => {
    const { rerender } = render(<AnswerComposer {...defaults} roomState={questionState} />);
    const field = screen.getByRole("textbox", { name: /chosen to answer/i }) as HTMLTextAreaElement;
    await userEvent.type(field, "Can you repeat it?");
    const clarified: RoomState = { ...questionState, revision: 2, turns: [{ ...questionState.turns[0],
      clarifications: [{ request: "Can you repeat it?", reply: "Why was SQLite chosen?" }] }] };
    rerender(<AnswerComposer {...defaults} roomState={clarified} />);
    expect(field.value).toBe("");
    expect(screen.getByText(/1 clarifications left/)).toBeTruthy();
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

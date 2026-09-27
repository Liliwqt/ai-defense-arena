import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { HUD } from "./HUD";
import type { RoomState } from "../types";

const baseState: RoomState = {
  room_code: "ABCD12",
  self_seat: 0,
  self_is_host: true,
  phase: "lobby",
  players: [],
  turns: [],
  active_panelist: null,
  error: null,
  revision: 1,
  files: [],
  feedback_status: "none",
  feedback: null,
  server_now_ms: 1_000_000,
  vote_deadline_ms: null,
  answer_deadline_ms: null,
  selected_seat: null,
  vote_counts: {},
  my_vote: null,
  chat: [],
};

describe("HUD", () => {
  it("shows No room yet when roomState is null", () => {
    render(
      <HUD roomState={null} roomCode={null} previewMode={false} onOpenDrawer={vi.fn()} />,
    );
    expect(screen.getByText("No room yet")).toBeTruthy();
  });

  it("shows room code from state", () => {
    render(
      <HUD roomState={baseState} roomCode="ABCD12" previewMode={false} onOpenDrawer={vi.fn()} />,
    );
    expect(screen.getByText("Room ABCD12")).toBeTruthy();
  });

  it("calls onOpenDrawer with controls when Controls button is clicked", async () => {
    const spy = vi.fn();
    render(
      <HUD roomState={baseState} roomCode="ABCD12" previewMode={false} onOpenDrawer={spy} />,
    );
    await userEvent.click(screen.getByRole("button", { name: /controls/i }));
    expect(spy).toHaveBeenCalledWith("controls");
  });

  it("calls onOpenDrawer with transcript when Transcript button is clicked", async () => {
    const spy = vi.fn();
    render(
      <HUD roomState={baseState} roomCode="ABCD12" previewMode={false} onOpenDrawer={spy} />,
    );
    await userEvent.click(screen.getByRole("button", { name: /transcript/i }));
    expect(spy).toHaveBeenCalledWith("transcript");
  });

  it("shows answered count without a fixed total during an adaptive defense", () => {
    const state: RoomState = {
      ...baseState,
      phase: "question",
      turns: [
        { panelist: "Technical Architect", question: "Q1", filename: "f.py", evidence_line: 1, evidence_text: "x", answer: "a", answered_by: "Alex" },
        { panelist: "Technical Architect", question: "Q2", filename: "f.py", evidence_line: 2, evidence_text: "y", answer: "b", answered_by: "Sam" },
      ],
    };
    render(<HUD roomState={state} roomCode="ABCD12" previewMode={false} onOpenDrawer={vi.fn()} />);
    expect(screen.getByText("2 RESOLVED")).toBeTruthy();
  });

  it("shows COMPLETE when phase is complete", () => {
    const state: RoomState = {
      ...baseState,
      phase: "complete",
      turns: [
        { panelist: "Technical Architect", question: "Q1", filename: "f.py", evidence_line: 1, evidence_text: "x", answer: "a", answered_by: "Alex" },
        { panelist: "Security Reviewer", question: "Q2", filename: "f.py", evidence_line: 2, evidence_text: "y", answer: "b", answered_by: "Sam" },
        { panelist: "Technical Architect", question: "Q3", filename: "f.py", evidence_line: 3, evidence_text: "z", answer: "c", answered_by: "Alex" },
        { panelist: "Security Reviewer", question: "Q4", filename: "f.py", evidence_line: 4, evidence_text: "w", answer: "d", answered_by: "Sam" },
      ],
      feedback_status: "ready",
    };
    render(
      <HUD roomState={state} roomCode="ABCD12" previewMode={false} onOpenDrawer={vi.fn()} />,
    );
    expect(screen.getByText("COMPLETE")).toBeTruthy();
  });
});

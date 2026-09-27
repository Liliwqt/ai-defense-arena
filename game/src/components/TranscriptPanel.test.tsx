import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { TranscriptPanel } from "./TranscriptPanel";
import type { RoomState } from "../types";

const emptyState: RoomState = {
  room_code: "TEST",
  self_seat: 0,
  self_is_host: false,
  phase: "lobby",
  players: [],
  turns: [],
  active_panelist: null,
  error: null,
  revision: 1,
  files: [],
  feedback_status: "none",
  feedback: null,
};

describe("TranscriptPanel", () => {
  it("shows empty state when no turns and no feedback", () => {
    render(<TranscriptPanel roomState={null} />);
    expect(screen.getByText(/will appear here/i)).toBeTruthy();
  });

  it("shows empty state when state has no turns and feedback is none", () => {
    render(<TranscriptPanel roomState={emptyState} />);
    expect(screen.getByText(/will appear here/i)).toBeTruthy();
  });

  it("shows coaching report section when feedback is generating (no turns yet)", () => {
    const state: RoomState = { ...emptyState, feedback_status: "generating" };
    render(<TranscriptPanel roomState={state} />);
    expect(screen.getByText(/preparing your coaching report/i)).toBeTruthy();
  });

  it("renders four turn cards with question text", () => {
    const turns = [
      { panelist: "Technical Architect", question: "Why SQLite?", filename: "f.py", evidence_line: 1, evidence_text: "x", answer: "Simple.", answered_by: "Alex" },
      { panelist: "Security Reviewer", question: "Input validation?", filename: "f.py", evidence_line: 2, evidence_text: "y", answer: "Sanitise.", answered_by: "Sam" },
      { panelist: "Technical Architect", question: "Concurrency?", filename: "f.py", evidence_line: 3, evidence_text: "z", answer: "Queue.", answered_by: "Alex" },
      { panelist: "Security Reviewer", question: "Access control?", filename: "f.py", evidence_line: 4, evidence_text: "w", answer: "Auth check.", answered_by: "Sam" },
    ];
    const state: RoomState = {
      ...emptyState,
      phase: "complete",
      turns,
      feedback_status: "ready",
      feedback: {
        summary: "Well done.",
        strengths: [{ turn: 0, text: "Clear." }],
        improvements: [{ turn: 1, text: "More depth." }],
        next_step: "Rehearse.",
      },
    };
    render(<TranscriptPanel roomState={state} />);
    expect(screen.getByText("Why SQLite?")).toBeTruthy();
    expect(screen.getByText("Input validation?")).toBeTruthy();
    expect(screen.getByText("4 answered")).toBeTruthy();
    expect(screen.getByText("Well done.")).toBeTruthy();
  });
});

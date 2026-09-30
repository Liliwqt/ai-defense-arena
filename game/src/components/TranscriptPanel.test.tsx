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
  server_now_ms: 1_000_000,
  vote_deadline_ms: null,
  answer_deadline_ms: null,
  selected_seat: null,
  vote_counts: {},
  my_vote: null,
  chat: [],
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
      { panelist: "Technical Architect", lead_in: "You emphasized simplicity.", question: "Why SQLite?", filename: "f.py", evidence_line: 1, evidence_text: "x", answer: "Simple.", answered_by: "Alex", clarifications: [{ request: "Can you say that simply?", reply: "What made SQLite a good fit?" }] },
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
    expect(screen.getByText("You emphasized simplicity.")).toBeTruthy();
    expect(screen.getByText("Why SQLite?")).toBeTruthy();
    expect(screen.getByText(/Can you say that simply/)).toBeTruthy();
    expect(screen.getByText(/What made SQLite a good fit/)).toBeTruthy();
    expect(screen.getByText("Input validation?")).toBeTruthy();
    expect(screen.getByText("4 answered")).toBeTruthy();
    expect(screen.getByText("Well done.")).toBeTruthy();
  });

  it("reports per-defender coverage when more than one teammate answered", () => {
    const turns = [
      { panelist: "Technical Architect", question: "Q1", filename: "f.py", evidence_line: 1, evidence_text: "x", answer: "A", answered_by: "Alex", answered_by_seat: 0 },
      { panelist: "Security Reviewer", question: "Q2", filename: "f.py", evidence_line: 2, evidence_text: "y", answer: "B", answered_by: "Alex", answered_by_seat: 0 },
      { panelist: "Product Judge", question: "Q3", filename: "f.py", evidence_line: 3, evidence_text: "z", answer: "C", answered_by: "Sam", answered_by_seat: 1 },
    ];
    render(<TranscriptPanel roomState={{ ...emptyState, phase: "complete", turns }} />);
    const coverage = screen.getByText(/Team coverage/i);
    expect(coverage.textContent).toContain("Alex answered 2");
    expect(coverage.textContent).toContain("Sam answered 1");
  });

  it("hides coverage when only one teammate answered, to avoid singling anyone out", () => {
    const turns = [
      { panelist: "Technical Architect", question: "Q1", filename: "f.py", evidence_line: 1, evidence_text: "x", answer: "A", answered_by: "Alex", answered_by_seat: 0 },
      { panelist: "Security Reviewer", question: "Q2", filename: "f.py", evidence_line: 2, evidence_text: "y", answer: "B", answered_by: "Alex", answered_by_seat: 0 },
    ];
    render(<TranscriptPanel roomState={{ ...emptyState, phase: "complete", turns }} />);
    expect(screen.queryByText(/Team coverage/i)).toBeNull();
  });

  it("does not count a timed-out turn toward anyone's coverage", () => {
    const turns = [
      { panelist: "Technical Architect", question: "Q1", filename: "f.py", evidence_line: 1, evidence_text: "x", answer: "A", answered_by: "Alex", answered_by_seat: 0 },
      { panelist: "Security Reviewer", question: "Q2", filename: "f.py", evidence_line: 2, evidence_text: "y", answer: null, timed_out: true, answered_by: null, answered_by_seat: 1 },
    ];
    render(<TranscriptPanel roomState={{ ...emptyState, phase: "complete", turns }} />);
    expect(screen.queryByText(/Team coverage/i)).toBeNull();
  });

  it("frames a timeout neutrally, without blaming the defender", () => {
    const turns = [
      { panelist: "Security Reviewer", question: "Q1", filename: "f.py", evidence_line: 1, evidence_text: "x", answer: null, timed_out: true, answered_by: null, answered_by_seat: 1 },
    ];
    render(<TranscriptPanel roomState={{ ...emptyState, phase: "complete", turns }} />);
    expect(screen.getByText(/question passed to the panel/i)).toBeTruthy();
    expect(screen.queryByText(/no answer was submitted/i)).toBeNull();
  });
});

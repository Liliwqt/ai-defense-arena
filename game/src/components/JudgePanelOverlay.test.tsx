import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { JudgePanelOverlay } from "./JudgePanelOverlay";
import type { RoomState } from "../types";

const base: RoomState = {
  room_code: "TEST",
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
};

describe("JudgePanelOverlay", () => {
  it("renders all four judge names", () => {
    render(<JudgePanelOverlay roomState={null} discussing={false} />);
    expect(screen.getByLabelText(/Product Judge/)).toBeTruthy();
    expect(screen.getByLabelText(/Technical Architect/)).toBeTruthy();
    expect(screen.getByLabelText(/Security Reviewer/)).toBeTruthy();
    expect(screen.getByLabelText(/Critical Judge/)).toBeTruthy();
  });

  it("marks active judge when phase is question", () => {
    const state: RoomState = {
      ...base,
      phase: "question",
      active_panelist: "Technical Architect",
      turns: [
        {
          panelist: "Technical Architect",
          question: "Why use SQLite?",
          filename: "queue.py",
          evidence_line: 5,
          evidence_text: "DATABASE = 'queue.db'",
          answer: null,
          answered_by: null,
        },
      ],
    };
    render(<JudgePanelOverlay roomState={state} discussing={false} />);
    const activeEl = screen.getByLabelText(/Technical Architect.*asking a question/);
    expect(activeEl).toBeTruthy();
  });

  it("does not mark asking a question when discussing is true", () => {
    const state: RoomState = {
      ...base,
      phase: "question",
      active_panelist: "Product Judge",
      turns: [
        {
          panelist: "Product Judge",
          question: "What is your USP?",
          filename: "README.md",
          evidence_line: 1,
          evidence_text: "Campus Queue",
          answer: null,
          answered_by: null,
        },
      ],
    };
    render(<JudgePanelOverlay roomState={state} discussing={true} />);
    // When discussing, no judge should be "asking a question"
    expect(screen.queryByLabelText(/asking a question/)).toBeNull();
  });

  it("renders with null roomState without throwing", () => {
    expect(() =>
      render(<JudgePanelOverlay roomState={null} discussing={false} />),
    ).not.toThrow();
  });

  it("renders with discussing=true without throwing", () => {
    expect(() =>
      render(<JudgePanelOverlay roomState={base} discussing={true} />),
    ).not.toThrow();
  });

  it("all four judges show waiting state in lobby phase", () => {
    render(<JudgePanelOverlay roomState={base} discussing={false} />);
    // In lobby, no judge should be "asking a question"
    expect(screen.queryByLabelText(/asking a question/)).toBeNull();
    // All four judges are rendered
    const slots = document.querySelectorAll(".judge-slot");
    expect(slots.length).toBe(4);
  });

  it("non-active judges show idle state while a question is active", () => {
    const state: RoomState = {
      ...base,
      phase: "question",
      active_panelist: "Security Reviewer",
      turns: [
        {
          panelist: "Security Reviewer",
          question: "Is your auth token validated server-side?",
          filename: "queue.py",
          evidence_line: 12,
          evidence_text: "token = secrets.token_hex()",
          answer: null,
          answered_by: null,
        },
      ],
    };
    render(<JudgePanelOverlay roomState={state} discussing={false} />);
    // Active judge gets the "asking a question" label
    expect(screen.getByLabelText(/Security Reviewer.*asking a question/)).toBeTruthy();
    // Other three judges do NOT get the "asking a question" label
    expect(screen.queryByLabelText(/Product Judge.*asking a question/)).toBeNull();
    expect(screen.queryByLabelText(/Technical Architect.*asking a question/)).toBeNull();
    expect(screen.queryByLabelText(/Critical Judge.*asking a question/)).toBeNull();
  });

  it("complete phase shows no active judge", () => {
    const state: RoomState = {
      ...base,
      phase: "complete",
      active_panelist: null,
      feedback_status: "ready",
    };
    render(<JudgePanelOverlay roomState={state} discussing={false} />);
    expect(screen.queryByLabelText(/asking a question/)).toBeNull();
  });

  it("retry phase shows no active judge", () => {
    const state: RoomState = {
      ...base,
      phase: "retry",
      active_panelist: "Critical Judge",
      turns: [],
    };
    render(<JudgePanelOverlay roomState={state} discussing={false} />);
    // retry phase is not "question" or "generating" so no judge is active
    expect(screen.queryByLabelText(/asking a question/)).toBeNull();
  });
});

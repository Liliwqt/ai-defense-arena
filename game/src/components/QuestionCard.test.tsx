import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { QuestionCard } from "./QuestionCard";
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

describe("QuestionCard", () => {
  it("shows default state when roomState is null", () => {
    render(
      <QuestionCard roomState={null} connected={false} previewMode={false} onOpenDrawer={vi.fn()} />,
    );
    expect(screen.getByText("Your defense begins here")).toBeTruthy();
  });

  it("shows lobby text for lobby phase", () => {
    render(
      <QuestionCard roomState={base} connected={true} previewMode={false} onOpenDrawer={vi.fn()} />,
    );
    expect(screen.getByText("Your team is gathering")).toBeTruthy();
  });

  it("shows question text and source block for question phase", () => {
    const state: RoomState = {
      ...base,
      phase: "question",
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
    render(
      <QuestionCard roomState={state} connected={true} previewMode={false} onOpenDrawer={vi.fn()} />,
    );
    expect(screen.getByText("Why use SQLite?")).toBeTruthy();
    expect(screen.getByText("QUESTION 1")).toBeTruthy();
    expect(screen.getByText(/queue\.py:5/)).toBeTruthy();
    expect(screen.getByText("DATABASE = 'queue.db'")).toBeTruthy();
  });

  it("shows a later adaptive question number without a fixed denominator", () => {
    const answered = Array.from({ length: 6 }, (_, i) => ({
      panelist: "Product Judge", question: `Q${i + 1}`,
      filename: "README.md", evidence_line: 2, evidence_text: "users", answer: `A${i + 1}`,
      answered_by: "Alex",
    }));
    const state: RoomState = {
      ...base,
      phase: "question",
      turns: [...answered, { panelist: "Critical Judge", question: "What supports that claim?",
        filename: "README.md", evidence_line: 2, evidence_text: "users", answer: null,
        answered_by: null }],
    };
    render(<QuestionCard roomState={state} connected={true} previewMode={false} onOpenDrawer={vi.fn()} />);
    expect(screen.getByText("QUESTION 7")).toBeTruthy();
    expect(screen.getByText("Critical Judge")).toBeTruthy();
  });

  it("hides source block when phase is lobby", () => {
    render(
      <QuestionCard roomState={base} connected={true} previewMode={false} onOpenDrawer={vi.fn()} />,
    );
    expect(screen.queryByLabelText("Exact cited source line")).toBeNull();
  });

  it("shows coaching preparing text when phase complete and feedback generating", () => {
    const state: RoomState = {
      ...base,
      phase: "complete",
      feedback_status: "generating",
    };
    render(
      <QuestionCard roomState={state} connected={true} previewMode={false} onOpenDrawer={vi.fn()} />,
    );
    expect(screen.getByText("Preparing coaching report")).toBeTruthy();
  });

  it("shows coaching failed text when feedback_status is failed", () => {
    const state: RoomState = {
      ...base,
      phase: "complete",
      feedback_status: "failed",
      error: "OpenAI timed out.",
    };
    render(
      <QuestionCard roomState={state} connected={true} previewMode={false} onOpenDrawer={vi.fn()} />,
    );
    expect(screen.getByText("Defense complete")).toBeTruthy();
    expect(screen.getByText("OpenAI timed out.")).toBeTruthy();
  });

  it("shows ready coaching text when feedback_status is ready", () => {
    const state: RoomState = {
      ...base,
      phase: "complete",
      feedback_status: "ready",
    };
    render(
      <QuestionCard roomState={state} connected={true} previewMode={false} onOpenDrawer={vi.fn()} />,
    );
    expect(screen.getAllByText(/coaching report/i).length).toBeGreaterThanOrEqual(1);
  });
});

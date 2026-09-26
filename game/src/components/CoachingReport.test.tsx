import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { CoachingReport } from "./CoachingReport";
import type { CoachingFeedback } from "../types";

const fullFeedback: CoachingFeedback = {
  summary: "Solid defense overall.",
  strengths: [
    { turn: 0, text: "Clear SQLite rationale." },
    { turn: 2, text: "Good concurrency awareness." },
  ],
  improvements: [{ turn: 1, text: "Elaborate on input validation." }],
  next_step: "Rehearse edge cases with the team.",
};

describe("CoachingReport", () => {
  it("renders nothing when feedbackStatus is none", () => {
    const { container } = render(
      <CoachingReport feedbackStatus="none" feedback={null} />,
    );
    expect(container.firstChild).toBeNull();
  });

  it("shows preparing text when generating", () => {
    render(<CoachingReport feedbackStatus="generating" feedback={null} />);
    expect(screen.getByText(/preparing your coaching report/i)).toBeTruthy();
  });

  it("shows error text when failed", () => {
    render(<CoachingReport feedbackStatus="failed" feedback={null} />);
    expect(screen.getByText(/could not be generated/i)).toBeTruthy();
  });

  it("shows summary, strengths, improvements, and next step when ready", () => {
    render(<CoachingReport feedbackStatus="ready" feedback={fullFeedback} />);
    expect(screen.getByText("Solid defense overall.")).toBeTruthy();
    expect(screen.getByText(/Clear SQLite rationale\./)).toBeTruthy();
    expect(screen.getByText(/Good concurrency awareness\./)).toBeTruthy();
    expect(screen.getByText(/Elaborate on input validation\./)).toBeTruthy();
    expect(screen.getByText(/Rehearse edge cases with the team\./)).toBeTruthy();
  });

  it("prefixes each item with Q{n} turn label", () => {
    render(<CoachingReport feedbackStatus="ready" feedback={fullFeedback} />);
    // Strengths: turns 0 and 2 → Q1 and Q3
    expect(screen.getAllByText(/^Q1 ·/).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(/^Q3 ·/).length).toBeGreaterThanOrEqual(1);
    // Improvement: turn 1 → Q2
    expect(screen.getAllByText(/^Q2 ·/).length).toBeGreaterThanOrEqual(1);
  });

  it("shows Strengths heading but not Improvements when improvements is empty", () => {
    const fb: CoachingFeedback = {
      ...fullFeedback,
      improvements: [],
    };
    render(<CoachingReport feedbackStatus="ready" feedback={fb} />);
    expect(screen.getByText("Strengths")).toBeTruthy();
    expect(screen.queryByText("Areas to Improve")).toBeNull();
  });
});

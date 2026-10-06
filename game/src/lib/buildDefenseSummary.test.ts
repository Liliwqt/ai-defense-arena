import { describe, it, expect } from "vitest";
import { buildDefenseSummary, defenseSummaryFileName } from "./buildDefenseSummary";
import type { RoomState } from "../types";

const baseState: RoomState = {
  room_code: "ABC123",
  self_seat: 0,
  self_is_host: true,
  phase: "complete",
  players: [
    { seat: 0, name: "You", online: true, is_host: true },
    { seat: 1, name: "Teammate A", online: true, is_host: false },
  ],
  turns: [],
  active_panelist: null,
  error: null,
  revision: 9,
  files: ["README.md", "queue.py"],
  defense_type: "code",
  feedback_status: "none",
  feedback: null,
  server_now_ms: Date.UTC(2026, 9, 1, 12, 30),
  vote_deadline_ms: null,
  answer_deadline_ms: null,
  selected_seat: null,
  vote_counts: {},
  my_vote: null,
  chat: [],
};

const turn = (over: Partial<RoomState["turns"][number]> = {}) => ({
  panelist: "Technical Architect",
  question: "Why SQLite?",
  filename: "queue.py",
  evidence_line: 12,
  evidence_text: "conn = sqlite3.connect(DB)",
  answer: "Simple and serverless.",
  answered_by: "You",
  answered_by_seat: 0,
  ...over,
});

describe("buildDefenseSummary", () => {
  it("attributes a research suggestion to the panelist rather than the team's answer", () => {
    const advice = "One option is broader recruitment if access permits.";
    const answer = "We will keep the pilot and limit its claims.";
    const text = buildDefenseSummary({ ...baseState, defense_type: "research", turns: [turn({
      panelist: "Methodology Reviewer", lead_in: advice, answer, filename: "paper.md",
    })] });
    expect(text).toContain(`Panelist: ${advice}`);
    expect(text).toContain(`Team answer (You): ${answer}`);
    expect(text).not.toContain(`Team answer (You): ${advice}`);
  });
  it("includes the defense kind, room, team, and materials", () => {
    const text = buildDefenseSummary(baseState);
    expect(text).toContain("Code project defense");
    expect(text).toContain("Room: ABC123");
    expect(text).toContain("You (host), Teammate A");
    expect(text).toContain("README.md");
    expect(text).toContain("queue.py");
  });

  it("names the defense type correctly for research and mixed rooms", () => {
    expect(buildDefenseSummary({ ...baseState, defense_type: "research" })).toContain("Research paper defense");
    expect(buildDefenseSummary({ ...baseState, defense_type: "mixed" })).toContain("Research + code defense");
  });

  it("keeps the exact cited line with each question", () => {
    const text = buildDefenseSummary({ ...baseState, turns: [turn()] });
    expect(text).toContain("Q1. Technical Architect");
    expect(text).toContain("Why SQLite?");
    expect(text).toContain("queue.py, Line 12");
    expect(text).toContain("conn = sqlite3.connect(DB)");
  });

  it("prefers the document location when the server provided one", () => {
    const text = buildDefenseSummary({
      ...baseState,
      defense_type: "research",
      turns: [turn({ evidence_location: "Page 3, line 8" })],
    });
    expect(text).toContain("Page 3, line 8");
  });

  it("states a timeout factually and never implies an answer", () => {
    const text = buildDefenseSummary({
      ...baseState,
      turns: [turn({ answer: null, timed_out: true, answered_by: null, answered_by_seat: null })],
    });
    expect(text).toContain("time expired, no answer submitted");
    expect(text).not.toContain("Team answer");
  });

  it("includes clarification exchanges", () => {
    const text = buildDefenseSummary({
      ...baseState,
      turns: [turn({ clarifications: [{ request: "Can you say that simply?", reply: "Which decision matters most?" }] })],
    });
    expect(text).toContain("Clarification requested: Can you say that simply?");
    expect(text).toContain("Technical Architect replied: Which decision matters most?");
  });

  it("includes the coaching report with turn references", () => {
    const text = buildDefenseSummary({
      ...baseState,
      feedback_status: "ready",
      turns: [turn(), turn({ panelist: "Critical Judge", question: "What evidence?" })],
      feedback: {
        summary: "The team explained the pilot.",
        strengths: [{ turn: 0, text: "Named a concrete pilot." }],
        improvements: [{ turn: 1, text: "Explain the comparison." }],
        next_step: "Write down the measures.",
      },
    });
    expect(text).toContain("COACHING REPORT");
    expect(text).toContain("The team explained the pilot.");
    expect(text).toContain("Strengths");
    expect(text).toContain("Q1: Named a concrete pilot.");
    expect(text).toContain("Q2: Explain the comparison.");
    expect(text).toContain("Next step");
    expect(text).toContain("Write down the measures.");
  });

  it("handles a room with no turns and no coaching report without throwing", () => {
    const text = buildDefenseSummary(baseState);
    expect(text).toContain("Questions: 0");
    expect(text).not.toContain("QUESTIONS AND ANSWERS");
  });

  it("labels the export as practice guidance rather than a grade", () => {
    expect(buildDefenseSummary(baseState)).toContain("not a grade");
  });

  it("never emits undefined when optional turn fields are absent", () => {
    const text = buildDefenseSummary({
      ...baseState,
      turns: [turn({ lead_in: undefined, clarifications: undefined, evidence_location: undefined })],
    });
    expect(text).not.toContain("undefined");
  });

  it("builds a filesystem-safe file name", () => {
    const name = defenseSummaryFileName(baseState);
    expect(name).toBe("defense-abc123-2026-10-01.txt");
    expect(defenseSummaryFileName({ ...baseState, room_code: "" })).toMatch(/^defense-room-\d{4}-\d{2}-\d{2}\.txt$/);
    expect(defenseSummaryFileName({ ...baseState, room_code: "a/b c" })).not.toContain("/");
  });

  it("falls back cleanly when the server clock is missing", () => {
    const text = buildDefenseSummary({ ...baseState, server_now_ms: undefined });
    expect(text).toContain("AI DEFENSE ARENA");
    expect(text).not.toContain("undefined");
    expect(defenseSummaryFileName({ ...baseState, server_now_ms: undefined })).toMatch(/\.txt$/);
  });
});

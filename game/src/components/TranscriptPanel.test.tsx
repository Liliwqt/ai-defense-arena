import { describe, it, expect, vi } from "vitest";
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

  it("offers a summary download once there is something to export", () => {
    const turns = [
      { panelist: "Technical Architect", question: "Q1", filename: "f.py", evidence_line: 1, evidence_text: "x", answer: "A", answered_by: "Alex", answered_by_seat: 0 },
    ];
    render(<TranscriptPanel roomState={{ ...emptyState, phase: "complete", turns }} />);
    expect(screen.getByRole("button", { name: /download summary/i })).toBeTruthy();
  });

  it("does not offer a download when the room has no turns or coaching yet", () => {
    render(<TranscriptPanel roomState={emptyState} />);
    expect(screen.queryByRole("button", { name: /download summary/i })).toBeNull();
  });

  it("disables the download in preview mode", () => {
    const turns = [
      { panelist: "Technical Architect", question: "Q1", filename: "f.py", evidence_line: 1, evidence_text: "x", answer: "A", answered_by: "Alex", answered_by_seat: 0 },
    ];
    render(<TranscriptPanel roomState={{ ...emptyState, phase: "complete", turns }} previewMode />);
    const button = screen.getByRole("button", { name: /download summary/i }) as HTMLButtonElement;
    expect(button.disabled).toBe(true);
  });

  it("downloads a text file whose contents match the room", async () => {
    const turns = [
      { panelist: "Technical Architect", question: "Why SQLite?", filename: "queue.py", evidence_line: 12, evidence_text: "conn = sqlite3.connect(DB)", answer: "Serverless.", answered_by: "Alex", answered_by_seat: 0 },
    ];
    const state: RoomState = {
      ...emptyState,
      phase: "complete",
      room_code: "ABC123",
      files: ["queue.py"],
      feedback_status: "ready",
      turns,
      feedback: { summary: "Solid.", strengths: [{ turn: 0, text: "Concrete." }], improvements: [{ turn: 0, text: "Cite more." }], next_step: "Rehearse." },
    };

    const createObjectURL = vi.fn((_blob: Blob) => `blob:mock`);
    const revokeObjectURL = vi.fn();
    const originalCreate = URL.createObjectURL;
    const originalRevoke = URL.revokeObjectURL;
    (URL as unknown as { createObjectURL: unknown }).createObjectURL = createObjectURL;
    // Keep the stub in place for the whole test: the component revokes the object URL
    // on a deferred timeout, after the click handler returns.
    (URL as unknown as { revokeObjectURL: unknown }).revokeObjectURL = revokeObjectURL;

    const clickSpy = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {});
    try {
      render(<TranscriptPanel roomState={state} />);
      const button = screen.getByRole("button", { name: /download summary/i }) as HTMLButtonElement;
      button.click();

      // The Blob is created synchronously by the handler; read it back to prove the
      // file the user receives actually contains this defense.
      expect(createObjectURL).toHaveBeenCalledTimes(1);
      const blob = createObjectURL.mock.calls[0][0] as Blob;
      // jsdom's Blob has no .text(); use FileReader so the assertion still reads real content.
      const text = await new Promise<string>((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(String(reader.result));
        reader.onerror = () => reject(reader.error);
        reader.readAsText(blob);
      });
      expect(blob.type).toBe("text/plain;charset=utf-8");
      expect(text).toContain("AI DEFENSE ARENA");
      expect(text).toContain("Room: ABC123");
      expect(text).toContain("Why SQLite?");
      expect(text).toContain("conn = sqlite3.connect(DB)");
      expect(text).toContain("Solid.");
      expect(text).toContain("Rehearse.");
      expect(text).toContain("not a grade");

      expect(clickSpy).toHaveBeenCalledTimes(1);
      const anchor = clickSpy.mock.instances[0] as unknown as HTMLAnchorElement;
      expect(anchor.download).toBe("defense-abc123-1970-01-01.txt");
      expect(anchor.href).toContain("blob:mock");

      // The object URL must be released, otherwise repeated exports leak blobs.
      await new Promise((resolve) => setTimeout(resolve, 0));
      expect(revokeObjectURL).toHaveBeenCalledWith("blob:mock");
    } finally {
      clickSpy.mockRestore();
      (URL as unknown as { createObjectURL: unknown }).createObjectURL = originalCreate;
      (URL as unknown as { revokeObjectURL: unknown }).revokeObjectURL = originalRevoke;
    }
  });
});

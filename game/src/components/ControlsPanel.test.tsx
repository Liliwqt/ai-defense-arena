import { describe, it, expect, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { ControlsPanel } from "./ControlsPanel";
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

const defaultProps = {
  connected: true,
  previewMode: false,
  onUseRoom: vi.fn(),
  onLeaveRoom: vi.fn(),
  onSendEvent: vi.fn(() => true),
  onCloseDrawer: vi.fn(),
  showMessage: vi.fn(),
};

describe("ControlsPanel", () => {
  it("shows create/join forms when roomState is null and not connected", () => {
    render(<ControlsPanel {...defaultProps} roomState={null} connected={false} />);
    expect(screen.getByRole("tab", { name: /create room/i })).toBeTruthy();
    expect(screen.getByRole("tab", { name: /join room/i })).toBeTruthy();
    const passcode = screen.getByLabelText("Host passcode") as HTMLInputElement;
    expect(passcode.type).toBe("password");
    expect(passcode.required).toBe(true);
  });

  it("moves between setup tabs with the arrow keys", () => {
    render(<ControlsPanel {...defaultProps} roomState={null} connected={false} />);
    const createTab = screen.getByRole("tab", { name: "Create room" });
    fireEvent.keyDown(createTab, { key: "ArrowRight" });
    const joinTab = screen.getByRole("tab", { name: "Join room" });
    expect(joinTab.getAttribute("aria-selected")).toBe("true");
    expect(document.activeElement).toBe(joinTab);
    fireEvent.keyDown(joinTab, { key: "ArrowLeft" });
    expect(createTab.getAttribute("aria-selected")).toBe("true");
    expect(document.activeElement).toBe(createTab);
  });

  it("offers separate research documents and stage for paper defenses", () => {
    render(<ControlsPanel {...defaultProps} roomState={null} connected={false} />);
    expect(screen.getByLabelText("Project source files or ZIP")).toBeTruthy();
    fireEvent.change(screen.getByLabelText("Defense type"), { target: { value: "mixed" } });
    expect(screen.getByLabelText("Research documents")).toBeTruthy();
    expect(screen.getByLabelText("Research stage")).toBeTruthy();
    fireEvent.change(screen.getByLabelText("Defense type"), { target: { value: "research" } });
    expect(screen.queryByLabelText("Project source files or ZIP")).toBeNull();
  });

  it("lists extracted documents and page counts in the lobby", () => {
    const state: RoomState = { ...baseState, defense_type: "research", accepted_files: [
      { name: "paper.pdf", kind: "research_pdf", detail: "2 pages" },
    ] };
    render(<ControlsPanel {...defaultProps} roomState={state} />);
    expect(screen.getByText(/paper.pdf · 2 pages/)).toBeTruthy();
  });

  it("host sees Start defense button in lobby phase", () => {
    render(<ControlsPanel {...defaultProps} roomState={baseState} />);
    expect(screen.getByRole("button", { name: /start defense/i })).toBeTruthy();
  });

  it("non-host does not see Start defense button", () => {
    const state: RoomState = { ...baseState, self_is_host: false };
    render(<ControlsPanel {...defaultProps} roomState={state} />);
    expect(screen.queryByRole("button", { name: /start defense/i })).toBeNull();
  });

  it("keeps answer entry out of the Controls drawer", () => {
    const state: RoomState = {
      ...baseState,
      phase: "question",
      turns: [{ panelist: "Technical Architect", question: "Why?", filename: "app.py", evidence_line: 1, evidence_text: "x", answer: null, answered_by: null }],
    };
    render(<ControlsPanel {...defaultProps} roomState={state} />);
    expect(screen.queryByRole("textbox", { name: /your answer/i })).toBeNull();
  });

  it("host sees Retry question button in retry phase", () => {
    const state: RoomState = { ...baseState, phase: "retry" };
    render(<ControlsPanel {...defaultProps} roomState={state} />);
    expect(screen.getByRole("button", { name: /retry question/i })).toBeTruthy();
  });

  it("host sees Retry coaching report when complete and feedback failed", () => {
    const state: RoomState = {
      ...baseState,
      phase: "complete",
      feedback_status: "failed",
    };
    render(<ControlsPanel {...defaultProps} roomState={state} />);
    expect(screen.getByRole("button", { name: /retry coaching report/i })).toBeTruthy();
  });

  it("host does NOT see Retry coaching report when feedback is ready", () => {
    const state: RoomState = {
      ...baseState,
      phase: "complete",
      feedback_status: "ready",
    };
    render(<ControlsPanel {...defaultProps} roomState={state} />);
    expect(screen.queryByRole("button", { name: /retry coaching report/i })).toBeNull();
  });

  it("host does NOT see Retry coaching report when not complete", () => {
    const state: RoomState = { ...baseState, phase: "lobby" };
    render(<ControlsPanel {...defaultProps} roomState={state} />);
    expect(screen.queryByRole("button", { name: /retry coaching report/i })).toBeNull();
  });
});

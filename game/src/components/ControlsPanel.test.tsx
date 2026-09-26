import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
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
};

const defaultProps = {
  connected: true,
  previewMode: false,
  waitingForAnswerAck: false,
  onUseRoom: vi.fn(),
  onLeaveRoom: vi.fn(),
  onSendEvent: vi.fn(() => true),
  onCloseDrawer: vi.fn(),
  showMessage: vi.fn(),
};

describe("ControlsPanel", () => {
  it("shows create/join forms when roomState is null and not connected", () => {
    render(<ControlsPanel {...defaultProps} roomState={null} connected={false} />);
    expect(screen.getByRole("button", { name: /create room/i })).toBeTruthy();
    expect(screen.getByRole("button", { name: /join room/i })).toBeTruthy();
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

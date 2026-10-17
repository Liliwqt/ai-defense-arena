import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { App } from "./App";
import { useAccount } from "./hooks/useAccount";
import { useRoomSocket, type RoomSocketState } from "./hooks/useRoomSocket";
import type { RoomState } from "./types";

vi.mock("./hooks/useAccount", () => ({ useAccount: vi.fn() }));
vi.mock("./hooks/useRoomSocket", () => ({ useRoomSocket: vi.fn() }));
let socket: RoomSocketState;
const room = (extra: Partial<RoomState> = {}): RoomState => ({
  room_code: "STAGE1", defense_view_id: "run-a", self_seat: 0, self_is_host: true,
  players: [{ seat: 0, name: "Alex", online: true, is_host: true }],
  phase: "question", selected_seat: 0, revision: 1, error: null, files: ["app.py"],
  active_panelist: "Technical Architect", feedback_status: "none", feedback: null,
  turns: [{ panelist: "Technical Architect", question: "Why a queue?", filename: "app.py",
    evidence_line: 1, evidence_text: "queue = []", answer: null, answered_by: null }], ...extra,
});
beforeEach(() => {
  sessionStorage.clear();
  window.history.replaceState(null, "", "/#/room");
  vi.mocked(useAccount).mockReturnValue({ account: { authenticated: true, google_enabled: true, user: { id: "host", name: "Alex", email: "host@example.com" }, free_access: true }, error: "", refresh: vi.fn(async () => {}) });
  socket = { roomState: room(), roomCode: "STAGE1", connected: true, knownHost: true, playerToken: "fixture",
    waitingForAnswerAck: false, actionError: null, actionErrorReason: null, sendEvent: vi.fn(() => true), useRoom: vi.fn(), leaveRoom: vi.fn() };
  vi.mocked(useRoomSocket).mockImplementation(() => socket);
});
afterEach(() => { vi.clearAllMocks(); vi.restoreAllMocks(); vi.useRealTimers(); });

const repeated = (): RoomState => room({
  phase: "retry", defense_type: "research", turns: [], active_panelist: null,
  opening_repeated: true, question_attempts_left: 1,
  opening_candidate: { id: "candidate-1", panelist: "Methodology Reviewer", question: "Why this campus?",
    filename: "paper.md", evidence_text: "We plan a campus pilot.", evidence_location: "Line 1" },
});

it("shows an inactive host preview and sends a bound choice once through keyboard", async () => {
  socket.roomState = repeated();
  render(<App />);
  expect(screen.getByText("Why this campus?")).toBeVisible();
  expect(screen.getByText("PREVIEW · NOT ACTIVE")).toBeVisible();
  const accept = screen.getByRole("button", { name: "Accept repeated question" });
  accept.focus();
  await userEvent.keyboard("{Enter}{Enter}");
  expect(socket.sendEvent).toHaveBeenCalledTimes(1);
  expect(socket.sendEvent).toHaveBeenCalledWith({ type: "accept_repeated_opening", candidate_id: "candidate-1" });
});

it("preserves the current preview through disconnect and enables choices on reconnect", async () => {
  socket.roomState = repeated(); socket.connected = false;
  const view = render(<App />);
  expect(screen.getByRole("button", { name: "Accept repeated question" })).toBeDisabled();
  socket.connected = true; view.rerender(<App />);
  await userEvent.click(screen.getByRole("button", { name: "Retry opening" }));
  expect(socket.sendEvent).toHaveBeenCalledWith({ type: "retry_opening", candidate_id: "candidate-1" });
  socket.roomState = { ...repeated(), question_attempts_left: 0, opening_candidate: { ...repeated().opening_candidate!, id: "candidate-2" } };
  view.rerender(<App />);
  expect(screen.getByRole("button", { name: "Retry opening" })).toBeDisabled();
  expect(screen.getByRole("button", { name: "Accept repeated question" })).toBeEnabled();
});

it("offers the same choice in full-screen Controls and retains it after action failure", async () => {
  socket.roomState = repeated(); window.history.replaceState(null, "", "/#/controls");
  const view = render(<App />);
  expect(screen.getByText("Methodology Reviewer: Why this campus?")).toBeVisible();
  await userEvent.click(screen.getByRole("button", { name: "Accept repeated question" }));
  socket.actionError = "Nothing new was charged. Try again.";
  view.rerender(<App />);
  expect(screen.getByRole("button", { name: "Accept repeated question" })).toBeEnabled();
  expect(socket.roomState.turns).toEqual([]);
});

it("gives guests waiting guidance without a candidate or host actions", () => {
  socket.roomState = { ...repeated(), self_is_host: false, self_seat: 1, opening_candidate: null };
  render(<App />);
  expect(screen.queryByText("Why this campus?")).toBeNull();
  expect(screen.queryByRole("button", { name: "Accept repeated question" })).toBeNull();
  expect(screen.queryByRole("button", { name: "Retry opening" })).toBeNull();
  expect(screen.getAllByText(/waiting for the host/i).length).toBeGreaterThan(0);
});

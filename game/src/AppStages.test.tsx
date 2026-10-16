import { act, fireEvent, render, screen } from "@testing-library/react";
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
afterEach(() => { vi.clearAllMocks(); vi.useRealTimers(); });

it("opens full-screen Controls and returns with the same answer and server deadline", async () => {
  socket.roomState = room({ server_now_ms: Date.now(), answer_deadline_ms: Date.now() + 120_000 });
  render(<App />);
  const answer = screen.getByRole("textbox", { name: /chosen to answer/i });
  await userEvent.type(answer, "We serialize the requests.");
  await userEvent.click(screen.getByRole("button", { name: /settings.*controls/i }));
  expect(window.location.hash).toBe("#/controls");
  expect(screen.getByRole("heading", { name: "Live controls" })).toBeVisible();
  expect(screen.getByRole("timer", { name: "Answer time remaining" })).toHaveTextContent("ANSWER 2:00");
  await userEvent.click(screen.getByRole("button", { name: "Return to defense" }));
  expect(answer).toBeVisible();
  expect(answer).toHaveValue("We serialize the requests.");
  expect(socket.sendEvent).not.toHaveBeenCalled();
  expect(socket.leaveRoom).not.toHaveBeenCalled();
});

it("follows shared start once, preserves manually opened Controls, and keeps Account open through completion", async () => {
  socket.roomState = room({ phase: "lobby", turns: [] });
  window.history.replaceState(null, "", "/#/prepare");
  const view = render(<App />);
  socket.roomState = room({ phase: "voting" });
  view.rerender(<App />);
  expect(window.location.hash).toBe("#/room");
  await userEvent.click(screen.getByRole("button", { name: /settings.*controls/i }));
  socket.roomState = { ...socket.roomState, revision: 3 };
  view.rerender(<App />);
  expect(screen.getByRole("heading", { name: "Live controls" })).toBeVisible();
  await userEvent.click(screen.getByRole("button", { name: /Account ↗/ }));
  socket.roomState = room({ phase: "complete", feedback_status: "ready", feedback: {
    summary: "A useful discussion.", strengths: [], improvements: [], next_step: "Practice." } });
  view.rerender(<App />);
  expect(screen.getByRole("heading", { name: "Account" })).toBeVisible();
  await userEvent.click(screen.getByRole("button", { name: "View defense results" }));
  expect(screen.getByRole("heading", { name: "Defense results" })).toBeVisible();
  expect(screen.getByText("A useful discussion.")).toBeVisible();
  expect(socket.sendEvent).not.toHaveBeenCalled();
});

it("restores a stale preparation address, finishes only the remaining closing and does not redirect on repeated snapshots", async () => {
  window.history.replaceState(null, "", "/#/prepare");
  const closing = room({ phase: "complete", feedback_status: "ready", closing_panelist: "Technical Architect",
    server_now_ms: 1000, closing_deadline_ms: 2000,
    feedback: { summary: "Saved report.", closing: "That explains the decision.", strengths: [], improvements: [], next_step: "Practice." } });
  socket.roomState = closing;
  const view = render(<App />);
  expect(window.location.hash).toBe("#/room");
  expect(screen.getByText("That explains the decision.")).toBeVisible();
  socket.roomState = { ...closing, server_now_ms: 2000, closing_deadline_ms: null };
  view.rerender(<App />);
  expect(screen.getByRole("heading", { name: "Defense results" })).toBeVisible();
  expect(screen.getByRole("button", { name: "Download summary" })).toBeEnabled();
  await userEvent.click(screen.getByRole("button", { name: "Live controls" }));
  socket.roomState = { ...socket.roomState, revision: 4 };
  view.rerender(<App />);
  expect(screen.getByRole("heading", { name: "Live controls" })).toBeVisible();
  expect(socket.sendEvent).not.toHaveBeenCalled();
});

it("keeps coaching failure and explicit host recovery available in full-screen Controls", async () => {
  socket.roomState = room({ phase: "complete", feedback_status: "failed" });
  window.history.replaceState(null, "", "/#/results");
  render(<App />);
  expect(screen.getByRole("heading", { name: "Defense results" })).toBeVisible();
  expect(screen.getByText(/Room STAGE1 · Coaching unavailable/)).toBeVisible();
  await userEvent.click(screen.getByRole("button", { name: "Live controls" }));
  await userEvent.click(screen.getByRole("button", { name: "Retry coaching report" }));
  expect(socket.sendEvent).toHaveBeenCalledExactlyOnceWith({ type: "retry_coaching" });
});

it("opening Controls after elapsed time never resets the countdown", () => {
  vi.useFakeTimers();
  socket.roomState = room({ server_now_ms: 1000, answer_deadline_ms: 121000 });
  render(<App />);
  act(() => vi.advanceTimersByTime(5000));
  fireEvent.click(screen.getByRole("button", { name: /settings.*controls/i }));
  expect(screen.getByRole("timer", { name: "Answer time remaining" })).toHaveTextContent("ANSWER 1:55");
});

it("waits in the room for coaching generation and its optional closing before automatic Results", () => {
  const view = render(<App />);
  socket.roomState = room({ phase: "complete", feedback_status: "generating" });
  view.rerender(<App />);
  expect(window.location.hash).toBe("#/room");
  expect(screen.getByRole("heading", { name: "Preparing coaching report" })).toBeVisible();
  socket.roomState = room({ phase: "complete", feedback_status: "ready", closing_panelist: "Technical Architect",
    server_now_ms: 1000, closing_deadline_ms: 2000, feedback: { summary: "Saved report.", closing: "That explains it.", strengths: [], improvements: [], next_step: "Practice." } });
  view.rerender(<App />);
  expect(window.location.hash).toBe("#/room");
  socket.roomState = { ...socket.roomState, closing_deadline_ms: null };
  view.rerender(<App />);
  expect(screen.getByRole("heading", { name: "Defense results" })).toBeVisible();
});

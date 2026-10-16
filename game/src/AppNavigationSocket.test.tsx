import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "./App";
import type { RoomState } from "./types";

// The room transport is real here, so the navigation guarantee we prove is that
// moving between app screens never reconnects the socket or replays commands.
vi.mock("./hooks/useAccount", () => ({ useAccount: () => ({ account: null, error: "", refresh: vi.fn(async () => {}) }) }));

class MockWebSocket {
  static OPEN = 1;
  readyState = MockWebSocket.OPEN;
  url: string;
  sentMessages: string[] = [];
  listeners: Record<string, ((e: unknown) => void)[]> = {};

  constructor(url: string) {
    this.url = url;
    allSockets.push(this);
  }

  send(data: string) { this.sentMessages.push(data); }

  close() { this.readyState = 3; this.emit("close", {}); }

  addEventListener(type: string, cb: (e: unknown) => void) {
    (this.listeners[type] ??= []).push(cb);
  }

  emit(type: string, event: unknown) {
    (this.listeners[type] ?? []).forEach((cb) => cb(event));
  }
}

let allSockets: MockWebSocket[] = [];
let store: Record<string, string> = {};

const answeringRoom = (): RoomState => ({
  room_code: "ABCD12", self_seat: 0, self_is_host: true, phase: "question",
  players: [{ seat: 0, name: "Alex", online: true, is_host: true }],
  turns: [{ panelist: "Technical Architect", question: "Why keep the queue in memory?",
    filename: "queue.py", evidence_line: 5, evidence_text: "    queue = []", answer: null, answered_by: null }],
  active_panelist: "Technical Architect", error: null, revision: 1, files: ["queue.py"],
  feedback_status: "none", feedback: null, server_now_ms: Date.now(), answer_deadline_ms: Date.now() + 120_000,
  vote_deadline_ms: null, selected_seat: 0, vote_counts: { "0": 1 },
});

beforeEach(() => {
  allSockets = [];
  store = { defense_room_code: "ABCD12", defense_player_token: "token" };
  vi.stubGlobal("WebSocket", MockWebSocket);
  vi.stubGlobal("localStorage", {
    getItem: (key: string) => store[key] ?? null,
    setItem: (key: string, value: string) => { store[key] = value; },
    removeItem: (key: string) => { delete store[key]; },
  });
  window.history.replaceState(null, "", "/#/room");
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.clearAllMocks();
  window.history.replaceState(null, "", "/");
});

describe("navigation over a live room", () => {
  it("keeps the room socket, sent commands and answer draft across Account and Back", async () => {
    render(<App />);
    await waitFor(() => expect(allSockets.length).toBe(1));
    act(() => allSockets[0].emit("open", {}));
    act(() => allSockets[0].emit("message", { data: JSON.stringify({ type: "snapshot", state: answeringRoom() }) }));

    const answer = await screen.findByRole("textbox", { name: /chosen to answer/i });
    await userEvent.type(answer, "Keep this same-turn draft.");
    const sendsBefore = allSockets[0].sentMessages.length;

    await userEvent.click(screen.getByRole("button", { name: "Account" }));
    expect(screen.getByRole("heading", { name: "Account" })).toBeTruthy();
    expect(allSockets.length).toBe(1);
    expect(allSockets[0].readyState).toBe(MockWebSocket.OPEN);
    expect(allSockets[0].sentMessages.length).toBe(sendsBefore);

    act(() => { window.history.back(); });
    await waitFor(() => expect(screen.getByRole("button", { name: /settings.*controls/i })).toBeTruthy());
    expect(screen.getByRole("textbox", { name: /chosen to answer/i })).toHaveValue("Keep this same-turn draft.");
    expect(allSockets.length).toBe(1);
    expect(allSockets[0].sentMessages.length).toBe(sendsBefore);
  });
});

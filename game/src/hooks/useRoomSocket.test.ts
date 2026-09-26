import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useRoomSocket } from "./useRoomSocket";

// Minimal WebSocket mock
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

  send(data: string) {
    this.sentMessages.push(data);
  }

  close() {
    this.readyState = 3; // CLOSED
    this.emit("close", {});
  }

  addEventListener(type: string, cb: (e: unknown) => void) {
    if (!this.listeners[type]) this.listeners[type] = [];
    this.listeners[type].push(cb);
  }

  emit(type: string, event: unknown) {
    (this.listeners[type] ?? []).forEach((cb) => cb(event));
  }
}

let allSockets: MockWebSocket[] = [];

beforeEach(() => {
  allSockets = [];
  vi.stubGlobal("WebSocket", MockWebSocket);
  const store: Record<string, string> = {};
  vi.stubGlobal("localStorage", {
    getItem: (k: string) => store[k] ?? null,
    setItem: (k: string, v: string) => { store[k] = v; },
    removeItem: (k: string) => { delete store[k]; },
  });
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

describe("useRoomSocket", () => {
  it("sends hello after socket opens", async () => {
    const { result } = renderHook(() => useRoomSocket(false));
    act(() => result.current.useRoom("ABCD12", "token123", true));
    await vi.waitFor(() => allSockets.length > 0);
    // Trigger open
    act(() => allSockets[0].emit("open", {}));
    expect(allSockets[0].sentMessages).toContain(
      JSON.stringify({ type: "hello", token: "token123" }),
    );
  });

  it("snapshot message updates roomState", async () => {
    const { result } = renderHook(() => useRoomSocket(false));
    act(() => result.current.useRoom("ABCD12", "tok", false));
    await vi.waitFor(() => allSockets.length > 0);
    act(() => allSockets[0].emit("open", {}));
    const mockState = {
      room_code: "ABCD12",
      phase: "lobby",
      self_seat: 1,
      self_is_host: false,
      players: [],
      turns: [],
      active_panelist: null,
      error: null,
      revision: 1,
      files: [],
      feedback_status: "none",
      feedback: null,
    };
    act(() =>
      allSockets[0].emit("message", {
        data: JSON.stringify({ type: "snapshot", state: mockState }),
      }),
    );
    expect(result.current.roomState?.room_code).toBe("ABCD12");
    expect(result.current.roomState?.phase).toBe("lobby");
  });

  it("invalid room error triggers leaveRoom", async () => {
    const { result } = renderHook(() => useRoomSocket(false));
    act(() => result.current.useRoom("ABCD12", "tok", false));
    await vi.waitFor(() => allSockets.length > 0);
    act(() => allSockets[0].emit("open", {}));
    act(() =>
      allSockets[0].emit("message", {
        data: JSON.stringify({
          type: "error",
          message: "This room link is no longer valid.",
        }),
      }),
    );
    expect(result.current.roomCode).toBeNull();
    expect(result.current.roomState).toBeNull();
  });

  it("schedules reconnect after socket closes", async () => {
    vi.useFakeTimers();
    const { result } = renderHook(() => useRoomSocket(false));
    act(() => result.current.useRoom("ABCD12", "tok", false));
    await vi.waitFor(() => allSockets.length > 0);
    act(() => allSockets[0].emit("open", {}));
    act(() => allSockets[0].emit("close", {}));
    expect(result.current.connected).toBe(false);
    // Advance past reconnect delay — a new socket should be created
    act(() => vi.advanceTimersByTime(1800));
    expect(allSockets.length).toBe(2);
  });

  it("sendEvent returns false when socket is not open", () => {
    const { result } = renderHook(() => useRoomSocket(false));
    const sent = result.current.sendEvent({ type: "start" });
    expect(sent).toBe(false);
  });
});

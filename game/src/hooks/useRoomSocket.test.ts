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
  it("retains a structured AI admission reason independent of message wording", () => {
    const { result } = renderHook(() => useRoomSocket(false));
    act(() => result.current.useRoom("ABCD12", "tok", false));
    act(() => allSockets[0].emit("open", {}));
    act(() => allSockets[0].emit("message", { data: JSON.stringify({ type: "error", reason: "ai_admission", message: "The service is busy. Retry shortly." }) }));
    expect(result.current.actionErrorReason).toBe("ai_admission");
  });
  it("keeps a healthy socket and chosen defender when the native app resumes", () => {
    const { result } = renderHook(() => useRoomSocket(false));
    act(() => result.current.useRoom("ABCD12", "same-token", false));
    act(() => allSockets[0].emit("open", {}));
    act(() => allSockets[0].emit("message", {data:JSON.stringify({type:"snapshot",state:{room_code:"ABCD12",phase:"question",selected_seat:1,turns:[]}})}));
    act(() => window.dispatchEvent(new Event("defense-native-resume")));
    expect(allSockets.length).toBe(1);
    expect(allSockets[0].readyState).toBe(MockWebSocket.OPEN);
    expect(result.current.roomState?.selected_seat).toBe(1);
  });

  it("restores an authoritative snapshot on native resume when disconnected", () => {
    const { result } = renderHook(() => useRoomSocket(false));
    act(() => result.current.useRoom("ABCD12", "same-token", false));
    act(() => allSockets[0].emit("open", {}));
    act(() => allSockets[0].close());
    act(() => window.dispatchEvent(new Event("defense-native-resume")));
    expect(allSockets.length).toBe(2);
    act(() => allSockets[1].emit("open", {}));
    expect(allSockets[1].sentMessages).toEqual([JSON.stringify({type: "hello", token: "same-token"})]);
    act(() => allSockets[1].emit("message", {data: JSON.stringify({type:"snapshot",state:{room_code:"ABCD12",phase:"question",selected_seat:1,turns:[],answer_deadline_ms:12345}})}));
    expect(result.current.roomState?.answer_deadline_ms).toBe(12345);
    expect(result.current.roomState?.selected_seat).toBe(1);
  });
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

  it("retains an expiry explanation while stopping reconnect and clearing credentials", () => {
    vi.useFakeTimers();
    const { result } = renderHook(() => useRoomSocket(false));
    act(() => result.current.useRoom("ABCD12", "tok", false));
    act(() => allSockets[0].emit("open", {}));
    const message = "Room not found. This room was closed or expired; create a fresh room.";
    act(() => allSockets[0].emit("message", { data: JSON.stringify({ type: "error", message }) }));
    expect(result.current.actionError).toBe(message);
    expect(result.current.roomCode).toBeNull();
    expect(localStorage.getItem("defense_player_token")).toBeNull();
    act(() => vi.advanceTimersByTime(6000));
    expect(allSockets).toHaveLength(1);
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

  it("keeps an answer pending until its turn changes and surfaces server errors", async () => {
    const { result } = renderHook(() => useRoomSocket(false));
    act(() => result.current.useRoom("ABCD12", "tok", false));
    await vi.waitFor(() => allSockets.length > 0);
    act(() => allSockets[0].emit("open", {}));
    act(() => { expect(result.current.sendEvent({ type: "submit_answer", turn: 0, answer: "Plan" })).toBe(true); });
    expect(result.current.waitingForAnswerAck).toBe(true);
    const question = { room_code: "ABCD12", phase: "question", turns: [{ question: "Why?", answer: null }] };
    act(() => allSockets[0].emit("message", { data: JSON.stringify({ type: "snapshot", state: question }) }));
    expect(result.current.waitingForAnswerAck).toBe(true);
    act(() => allSockets[0].emit("message", { data: JSON.stringify({ type: "error", message: "That question has already been answered." }) }));
    expect(result.current.waitingForAnswerAck).toBe(false);
    expect(result.current.actionError).toMatch(/already been answered/);
    act(() => { expect(result.current.sendEvent({ type: "submit_answer", turn: 0, answer: "Plan" })).toBe(true); });
    act(() => allSockets[0].emit("message", { data: JSON.stringify({ type: "snapshot", state: { ...question, phase: "generating", turns: [{ question: "Why?", answer: "Plan" }] } }) }));
    expect(result.current.waitingForAnswerAck).toBe(false);
    expect(result.current.actionError).toBeNull();
  });

  it("allows retry with the same draft when WebSocket send throws", async () => {
    const { result } = renderHook(() => useRoomSocket(false));
    act(() => result.current.useRoom("ABCD12", "tok", false));
    await vi.waitFor(() => allSockets.length > 0);
    act(() => allSockets[0].emit("open", {}));
    const send = vi.spyOn(allSockets[0], "send");
    send.mockImplementationOnce(() => { throw new Error("socket write failed"); });
    act(() => { expect(result.current.sendEvent({ type: "submit_answer", turn: 0, answer: "Plan" })).toBe(false); });
    expect(result.current.waitingForAnswerAck).toBe(false);
    act(() => { expect(result.current.sendEvent({ type: "submit_answer", turn: 0, answer: "Plan" })).toBe(true); });
    expect(result.current.waitingForAnswerAck).toBe(true);
  });

  it("sendEvent returns false when socket is not open", () => {
    const { result } = renderHook(() => useRoomSocket(false));
    const sent = result.current.sendEvent({ type: "start" });
    expect(sent).toBe(false);
  });
});

it("does not acknowledge a pending probe reply on an unrelated same-phase snapshot", () => {
  const { result } = renderHook(() => useRoomSocket(false));
  act(() => result.current.useRoom("ABCD12", "tok", false));
  act(() => allSockets[0].emit("open", {}));
  const snapshot = { room_code: "ABCD12", phase: "probe", turns: [{ answer: "Original answer", probe: { id: "p1", status: "pending" } }] };
  act(() => allSockets[0].emit("message", { data: JSON.stringify({ type: "snapshot", state: snapshot }) }));
  act(() => result.current.sendEvent({ type: "submit_probe_reply", turn: 0, probe_id: "p1", answer: "Reply" }));
  expect(result.current.waitingForAnswerAck).toBe(true);
  act(() => allSockets[0].emit("message", { data: JSON.stringify({ type: "snapshot", state: snapshot }) }));
  expect(result.current.waitingForAnswerAck).toBe(true);
  act(() => allSockets[0].emit("message", { data: JSON.stringify({ type: "snapshot", state: { ...snapshot, phase: "interpreting" } }) }));
  expect(result.current.waitingForAnswerAck).toBe(false);
});

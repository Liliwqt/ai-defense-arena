import { act, renderHook } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { formatCountdown, useRoomCountdown } from "./useRoomCountdown";
import type { RoomState } from "../types";

const state = (phase: RoomState["phase"], now: number, vote: number | null, answer: number | null) => ({
  phase, server_now_ms: now, vote_deadline_ms: vote, answer_deadline_ms: answer,
}) as RoomState;

afterEach(() => vi.useRealTimers());

describe("room countdown", () => {
  it("uses the server snapshot for both phase deadlines", () => {
    vi.useFakeTimers();
    const { result, rerender } = renderHook(({ room }) => useRoomCountdown(room), {
      initialProps: { room: state("voting", 1_000, 16_000, null) },
    });
    expect(result.current).toBe(15);
    act(() => vi.advanceTimersByTime(1_100));
    expect(result.current).toBe(14);
    rerender({ room: state("question", 2_100, null, 122_100) });
    expect(result.current).toBe(120);
    rerender({ room: state("complete", 2_100, null, null) });
    expect(result.current).toBeNull();
  });

  it("formats remaining time and clamps after expiry", () => {
    expect(formatCountdown(120)).toBe("2:00");
    expect(formatCountdown(9)).toBe("0:09");
    expect(formatCountdown(null)).toBe("--:--");
    vi.useFakeTimers();
    const { result } = renderHook(() => useRoomCountdown(state("voting", 1_000, 2_000, null)));
    act(() => vi.advanceTimersByTime(2_000));
    expect(result.current).toBe(0);
  });
});

it("shows the separate probe reply countdown from the server clock", () => {
  vi.useFakeTimers();
  const { result } = renderHook(() => useRoomCountdown(state("probe", 1000, null, 31000)));
  expect(result.current).toBe(30);
  act(() => vi.advanceTimersByTime(31000));
  expect(result.current).toBe(0);
});

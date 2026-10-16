import { render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";

// previewMode is read from the URL once per module load, so the entry address
// must be in place before App is imported (module registry is reset per test).
vi.mock("./hooks/useAccount", () => ({ useAccount: () => ({ account: null, error: "", refresh: vi.fn(async () => {}) }) }));
vi.mock("./hooks/useRoomSocket", () => ({
  useRoomSocket: () => ({
    roomState: null, connected: true, roomCode: null, knownHost: true, waitingForAnswerAck: false,
    actionError: null, actionErrorReason: null, sendEvent: vi.fn(() => true), useRoom: vi.fn(),
    leaveRoom: vi.fn(), playerToken: null,
  }),
}));

beforeEach(() => { vi.resetModules(); });
afterEach(() => { window.history.replaceState(null, "", "/"); vi.clearAllMocks(); });

it("keeps the ?preview=1 visual review entry on the room screen", async () => {
  window.history.replaceState(null, "", "/?preview=1");
  const { App } = await import("./App");
  render(<App />);
  expect(screen.getByRole("button", { name: "Preview presenter" })).toBeTruthy();
  expect(screen.queryByRole("heading", { name: "Home" })).toBeNull();
});

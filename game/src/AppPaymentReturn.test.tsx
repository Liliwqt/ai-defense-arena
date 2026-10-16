import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, it, vi } from "vitest";
import { App } from "./App";
import { useRoomSocket } from "./hooks/useRoomSocket";
import type { RoomState } from "./types";

vi.mock("./hooks/useRoomSocket", () => ({ useRoomSocket: vi.fn() }));
afterEach(() => { vi.unstubAllGlobals(); sessionStorage.clear(); });

it("refreshes the shell wallet on same-origin payment return before offering a paid start", async () => {
  sessionStorage.clear(); window.history.replaceState(null, "", "/#/prepare");
  let credits = 0;
  const state: RoomState = { room_code: "WALLET1", defense_view_id: "wallet-view", phase: "lobby", self_seat: 0,
    self_is_host: true, players: [], turns: [], active_panelist: null, feedback_status: "none", feedback: null,
    error: null, revision: 1, files: ["app.py"], defense_type: "code" };
  const sendEvent = vi.fn(() => true);
  vi.mocked(useRoomSocket).mockReturnValue({ roomState: state, roomCode: "WALLET1", playerToken: "fixture", connected: true,
    knownHost: true, waitingForAnswerAck: false, actionError: null, actionErrorReason: null, sendEvent, useRoom: vi.fn(), leaveRoom: vi.fn() });
  vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL) => new Response(JSON.stringify(String(input).includes("/api/auth/me") ? {
    authenticated: true, google_enabled: true, user: { id: "buyer", name: "Alex", email: "fixture@example.com" },
    csrf_token: "fixture", payment_mode: "live", topup_invited: true, live_credits: credits, ai_service_available: true, paid_starts_enabled: true,
  } : { mode: "live", enabled: false, packages: [] }), { status: 200 })));
  render(<App />);
  await waitFor(() => expect(screen.getByRole("button", { name: "Start defense · 10 credits" })).toBeDisabled());
  await userEvent.click(screen.getByRole("button", { name: "Account ↗" }));
  await screen.findByRole("link", { name: "Top up credits" });
  await userEvent.click(screen.getByRole("link", { name: "Top up credits" }));
  await screen.findByRole("heading", { name: "Credits & purchases" });
  credits = 10; // authoritative wallet changed while the payment task was open
  await userEvent.click(screen.getByRole("link", { name: /Back to your room/ }));
  await waitFor(() => expect(screen.getByText("10 available credits · 0 reserved")).toBeVisible());
  await userEvent.click(screen.getByRole("button", { name: "Return to defense" }));
  await waitFor(() => expect(screen.getByRole("button", { name: "Start defense · 10 credits" })).toBeEnabled());
  expect(sendEvent).not.toHaveBeenCalled();
});

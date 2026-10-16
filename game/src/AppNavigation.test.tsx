import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "./App";
import { useAccount, type Account } from "./hooks/useAccount";
import { useRoomSocket, type RoomSocketState } from "./hooks/useRoomSocket";
import type { RoomState } from "./types";

vi.mock("./hooks/useAccount", () => ({ useAccount: vi.fn() }));
vi.mock("./hooks/useRoomSocket", () => ({ useRoomSocket: vi.fn() }));

function setAccount(value: Account | null, error = "") {
  vi.mocked(useAccount).mockReturnValue({ account: value, error, refresh: vi.fn(async () => {}) });
}

const account = (overrides: Partial<Account> = {}): Account => ({
  authenticated: false, google_enabled: true, ...overrides,
});

function renderAt(url: string) {
  window.history.replaceState(null, "", url);
  return render(<App />);
}

const roomState = (overrides: Partial<RoomState> = {}): RoomState => ({
  room_code: "ROOM1", self_seat: 0, self_is_host: true, phase: "voting",
  players: [], turns: [], active_panelist: null, error: null, revision: 1, files: [],
  feedback_status: "none", feedback: null, ...overrides,
});

function setSocket(state: RoomState | null, overrides: Partial<RoomSocketState> = {}) {
  const socket: RoomSocketState = {
    roomState: state, connected: true, roomCode: state?.room_code ?? null, knownHost: true,
    waitingForAnswerAck: false, actionError: null, actionErrorReason: null, sendEvent: vi.fn(() => true),
    useRoom: vi.fn(), leaveRoom: vi.fn(), playerToken: "token", ...overrides,
  };
  vi.mocked(useRoomSocket).mockReturnValue(socket);
  return socket;
}

beforeEach(() => { window.history.replaceState(null, "", "/"); });
afterEach(() => { window.history.replaceState(null, "", "/"); vi.clearAllMocks(); });

describe("full-screen app navigation", () => {
  it("opens full-screen Home at the root address with separate Create and Join choices", () => {
    setAccount(account());
    setSocket(null);
    render(<App />);
    expect(screen.getByRole("heading", { name: "Home" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Create a defense" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Join a room" })).toBeTruthy();
    expect(screen.queryByRole("button", { name: /settings.*controls/i })).toBeNull();
  });

  it("opens the private Account full-screen from the legacy account link and the account address", () => {
    setAccount(account({
      authenticated: true, user: { id: "u1", name: "Host", email: "host@example.com" },
      csrf_token: "csrf", payment_mode: "test", test_credits: 7, voucher_enabled: true,
    }));
    setSocket(null);

    const legacy = renderAt("/?account=1");
    expect(screen.getByRole("heading", { name: "Account" })).toBeTruthy();
    expect(screen.getByText("host@example.com")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Sign out" })).toBeTruthy();
    expect(legacy.container.querySelector(".room-screen")?.hasAttribute("hidden")).toBe(true);
    legacy.unmount();

    renderAt("/#/account");
    expect(screen.getByRole("heading", { name: "Account" })).toBeTruthy();
    expect(screen.getByText("host@example.com")).toBeTruthy();
  });

  it("offers Google sign-in from the sign-in address and stays truthful when it is unavailable", () => {
    setSocket(null);

    setAccount(account({ authenticated: false, google_enabled: true }));
    const enabled = renderAt("/#/signin");
    expect(screen.getByRole("heading", { name: "Sign in" })).toBeTruthy();
    expect(screen.getByText(/Teammates can join using your room code/)).toBeTruthy();
    expect(screen.getByRole("link", { name: /sign in with google/i }).getAttribute("href"))
      .toBe("/api/auth/google/login?return_to=%2F%3Faccount%3D1");
    enabled.unmount();

    setAccount(account({ authenticated: false, google_enabled: false }));
    renderAt("/#/signin");
    expect(screen.getByRole("heading", { name: "Sign in" })).toBeTruthy();
    expect(screen.queryByRole("link", { name: /sign in with google/i })).toBeNull();
    expect(screen.getByText(/Google sign-in needs server configuration/)).toBeTruthy();
  });

  it("falls back to Home with guidance on an address that is not a screen and joins nothing", () => {
    setAccount(account());
    const socket = setSocket(null, { connected: false });
    renderAt("/#/results");
    expect(screen.getByRole("heading", { name: "Home" })).toBeTruthy();
    expect(screen.getByRole("status")).toHaveTextContent(/couldn’t open that screen/i);
    expect(socket.useRoom).not.toHaveBeenCalled();
  });

  it("does not grant a guest owner or account privileges through navigation", () => {
    setSocket(null, { connected: false });
    setAccount(account({ authenticated: false, google_enabled: true, manager_enabled: true }));

    const guest = renderAt("/");
    expect(screen.queryByRole("link", { name: "Owner dashboard" })).toBeNull();
    guest.unmount();

    renderAt("/#/account");
    expect(screen.getByRole("heading", { name: "Account" })).toBeTruthy();
    expect(screen.queryByRole("link", { name: "Owner dashboard" })).toBeNull();
    expect(screen.getByRole("link", { name: /sign in with google/i })).toBeTruthy();
  });

  it("moves between Home and the room with browser Back and Forward", async () => {
    setAccount(account());
    setSocket(null);
    renderAt("/");
    const roomMarker = () => screen.getByRole("button", { name: /settings.*controls/i });

    await userEvent.click(screen.getByRole("button", { name: "Join a room" }));
    expect(window.location.hash).toBe("#/room");
    expect(roomMarker()).toBeTruthy();

    await userEvent.click(screen.getByRole("button", { name: "Home" }));
    expect(window.location.hash).toBe("#/home");
    expect(screen.getByRole("heading", { name: "Home" })).toBeTruthy();

    act(() => { window.history.back(); });
    await waitFor(() => expect(roomMarker()).toBeTruthy());

    act(() => { window.history.back(); });
    await waitFor(() => expect(screen.getByRole("heading", { name: "Home" })).toBeTruthy());

    act(() => { window.history.forward(); });
    await waitFor(() => expect(roomMarker()).toBeTruthy());
  });

  it("sends a signed-out Create to sign-in and a signed-in Create to the create form", async () => {
    setSocket(null, { connected: false });
    setAccount(account({ authenticated: false, google_enabled: true }));
    const signedOut = renderAt("/");
    await userEvent.click(screen.getByRole("button", { name: "Create a defense" }));
    expect(screen.getByRole("heading", { name: "Sign in" })).toBeTruthy();
    signedOut.unmount();

    setAccount(account({ authenticated: true, csrf_token: "csrf", google_enabled: true }));
    renderAt("/");
    await userEvent.click(screen.getByRole("button", { name: "Create a defense" }));
    expect(screen.getByRole("tab", { name: "Create room" }).getAttribute("aria-selected")).toBe("true");
    expect(document.querySelector("#create-form")).not.toBeNull();
    expect(document.querySelector("#join-form")).toBeNull();
  });

  it("opens the room-code Join form from Home", async () => {
    setAccount(account());
    setSocket(null, { connected: false });
    renderAt("/");
    await userEvent.click(screen.getByRole("button", { name: "Join a room" }));
    expect(screen.getByRole("tab", { name: "Join room" }).getAttribute("aria-selected")).toBe("true");
    expect(document.querySelector("#join-form")).not.toBeNull();
    expect(document.querySelector("#create-form")).toBeNull();
  });

  it("shows the active-room return and the owner entry on Home only when they apply", async () => {
    setSocket(roomState());
    setAccount(account({ authenticated: true, google_enabled: true, manager_enabled: true }));
    const active = renderAt("/");
    expect(screen.getByRole("link", { name: "Owner dashboard" }).getAttribute("href")).toBe("/?manager=1");
    await userEvent.click(screen.getByRole("button", { name: /return to your room ROOM1/i }));
    expect(screen.getByRole("button", { name: /settings.*controls/i })).toBeTruthy();
    active.unmount();

    setSocket(null);
    setAccount(account({ authenticated: true, google_enabled: true }));
    renderAt("/");
    expect(screen.queryByRole("button", { name: /return to your room/i })).toBeNull();
    expect(screen.queryByRole("link", { name: "Owner dashboard" })).toBeNull();
  });
});

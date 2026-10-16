import { act, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "./App";
import { useAccount, type Account } from "./hooks/useAccount";
import { useRoomSocket, type RoomSocketState } from "./hooks/useRoomSocket";
import { researchPlanPreview } from "./researchPlanPreview";
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
  it("opens full-screen Home at its address with separate Create and Join choices", () => {
    setAccount(account());
    setSocket(null);
    renderAt("/#/home");
    expect(screen.getByRole("heading", { name: "Home" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Create a defense" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Join a room" })).toBeTruthy();
    expect(screen.queryByRole("button", { name: /settings.*controls/i })).toBeNull();
  });

  it.each(["/", "/#/"])("shows sign-in first at %s while the account loads and when signed out", (url) => {
    setAccount(null);
    setSocket(null, { connected: false });
    const view = renderAt(url);
    expect(screen.getByRole("heading", { name: "Sign in" })).toBeVisible();
    expect(screen.queryByRole("heading", { name: "Home" })).toBeNull();
    setAccount(account());
    view.rerender(<App />);
    expect(screen.getByRole("link", { name: /sign in with google/i })).toBeVisible();
  });

  it("shows an account-load error on the first screen with a working retry", async () => {
    setAccount(null, "Could not load your account.");
    setSocket(null, { connected: false });
    renderAt("/");
    expect(screen.getByRole("alert")).toHaveTextContent("Could not load your account.");
    await userEvent.click(screen.getByRole("button", { name: "Retry account" }));
    expect(vi.mocked(useAccount).mock.results.at(-1)?.value.refresh).toHaveBeenCalledOnce();
  });

  it("opens Home at the root for an already signed-in user", () => {
    setAccount(account({ authenticated: true }));
    setSocket(null, { connected: false });
    renderAt("/");
    expect(screen.getByRole("heading", { name: "Home" })).toBeVisible();
  });

  it("lets a signed-out teammate join directly from the first sign-in screen", async () => {
    setAccount(account());
    setSocket(null, { connected: false });
    renderAt("/");
    await userEvent.click(screen.getByRole("button", { name: "Join a room" }));
    expect(window.location.hash).toBe("#/setup");
    expect(screen.getByRole("tab", { name: "Join room" })).toHaveAttribute("aria-selected", "true");
    expect(screen.queryByRole("link", { name: /sign in with google/i })).toBeNull();
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
    setSocket(roomState());
    renderAt("/#/home");
    const roomMarker = () => screen.getByRole("button", { name: /settings.*controls/i });

    await userEvent.click(screen.getByRole("button", { name: /return to your room ROOM1/i }));
    expect(window.location.hash).toBe("#/room");
    expect(roomMarker()).toBeTruthy();

    await userEvent.click(screen.getByRole("button", { name: "Home" }));
    expect(window.location.hash).toBe("#/home");
    expect(screen.getByRole("heading", { name: "Home" })).toBeTruthy();

    act(() => { window.history.back(); });
    await waitFor(() => expect(roomMarker()).toBeTruthy());

    act(() => { window.history.back(); });
    await waitFor(() => expect(screen.getByRole("heading", { name: "Home" })).toHaveFocus());

    act(() => { window.history.forward(); });
    await waitFor(() => expect(roomMarker()).toBeTruthy());
  });

  it("sends a signed-out Create to sign-in and a signed-in Create to the create form", async () => {
    setSocket(null, { connected: false });
    setAccount(account({ authenticated: false, google_enabled: true }));
    const signedOut = renderAt("/#/home");
    await userEvent.click(screen.getByRole("button", { name: "Create a defense" }));
    expect(screen.getByRole("heading", { name: "Sign in" })).toBeTruthy();
    signedOut.unmount();

    setAccount(account({ authenticated: true, csrf_token: "csrf", google_enabled: true }));
    renderAt("/");
    await userEvent.click(screen.getByRole("button", { name: "Create a defense" }));
    expect(screen.getByRole("tab", { name: "Create room" }).getAttribute("aria-selected")).toBe("true");
    expect(document.querySelector("#create-form")).not.toBeNull();
    expect(document.querySelector("#join-form")).not.toBeVisible();
  });

  it("opens the room-code Join form from Home", async () => {
    setAccount(account());
    setSocket(null, { connected: false });
    renderAt("/");
    await userEvent.click(screen.getByRole("button", { name: "Join a room" }));
    expect(screen.getByRole("tab", { name: "Join room" }).getAttribute("aria-selected")).toBe("true");
    expect(document.querySelector("#join-form")).not.toBeNull();
    expect(document.querySelector("#create-form")).not.toBeVisible();
  });

  it("re-selects the Join form when Home asks to join again after a manual switch to Create", async () => {
    setAccount(account());
    setSocket(null, { connected: false });
    renderAt("/");

    await userEvent.click(screen.getByRole("button", { name: "Join a room" }));
    expect(screen.getByRole("tab", { name: "Join room" }).getAttribute("aria-selected")).toBe("true");

    await userEvent.click(screen.getByRole("tab", { name: "Create room" }));
    expect(screen.getByRole("tab", { name: "Create room" }).getAttribute("aria-selected")).toBe("true");

    await userEvent.click(screen.getByRole("button", { name: "Back" }));
    await userEvent.click(screen.getByRole("button", { name: "Join a room" }));

    expect(screen.getByRole("tab", { name: "Join room" }).getAttribute("aria-selected")).toBe("true");
    expect(document.querySelector("#join-form")).not.toBeNull();
    expect(document.querySelector("#create-form")).not.toBeVisible();
  });

  it("re-selects the Create form when a signed-in Home asks to create again after a manual switch to Join", async () => {
    setAccount(account({
      authenticated: true, user: { id: "u1", name: "Host", email: "host@example.com" },
      csrf_token: "csrf", payment_mode: "test", test_credits: 40,
    }));
    setSocket(null, { connected: false });
    renderAt("/");

    await userEvent.click(screen.getByRole("button", { name: "Create a defense" }));
    expect(screen.getByRole("tab", { name: "Create room" }).getAttribute("aria-selected")).toBe("true");

    await userEvent.click(screen.getByRole("tab", { name: "Join room" }));
    expect(screen.getByRole("tab", { name: "Join room" }).getAttribute("aria-selected")).toBe("true");

    await userEvent.click(screen.getByRole("button", { name: "Back" }));
    await userEvent.click(screen.getByRole("button", { name: "Create a defense" }));

    expect(screen.getByRole("tab", { name: "Create room" }).getAttribute("aria-selected")).toBe("true");
    expect(document.querySelector("#create-form")).not.toBeNull();
    expect(document.querySelector("#join-form")).not.toBeVisible();
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

  // Review fix 1: a persistent socket error must redirect once, not trap navigation.
  it("redirects to Account once for a new sign-in error and keeps Back usable while it persists", async () => {
    setAccount(account({ authenticated: false, google_enabled: true }));
    const socket = setSocket(null, { connected: false, actionError: "Sign in with Google to create a room." });
    const view = renderAt("/#/room");

    await waitFor(() => expect(screen.getByRole("heading", { name: "Account" })).toBeTruthy());
    await userEvent.click(screen.getByRole("button", { name: "Back to Home" }));
    expect(screen.getByRole("heading", { name: "Home" })).toBeTruthy();
    expect(screen.queryByRole("heading", { name: "Account" })).toBeNull();

    await userEvent.click(screen.getByRole("button", { name: "Join a room" }));
    expect(window.location.hash).toBe("#/setup");
    expect(document.querySelector("#join-form")).not.toBeNull();

    socket.actionError = "Sign in to use host controls.";
    view.rerender(<App />);
    await waitFor(() => expect(screen.getByRole("heading", { name: "Account" })).toBeTruthy());
  });

  // Review fix 2: unsent preparation drafts must survive Home/Account round trips.
  it("keeps unsent preparation drafts through Home and Account round trips", async () => {
    setAccount(account({ authenticated: true, google_enabled: true, csrf_token: "csrf", payment_mode: "test", test_credits: 40 }));
    setSocket(roomState({
      phase: "lobby", defense_type: "research", accepted_files: [{ name: "study.pdf", kind: "research_pdf", detail: "3 pages" }],
      files: ["study.pdf"], research_stage: "proposal", research_planning_status: "ready",
      research_plan: researchPlanPreview, research_plan_approved: false, research_budget_preview: 8,
      players: [{ seat: 0, name: "Alex", online: true, is_host: true }],
    }));
    renderAt("/#/room");
    await userEvent.click(screen.getByRole("button", { name: /settings.*controls/i }));
    const budget = within(screen.getByRole("dialog", { name: "Controls" })).getByLabelText(/question budget/i);
    await userEvent.clear(budget);
    await userEvent.type(budget, "12");
    await userEvent.type(within(screen.getByRole("dialog", { name: "Controls" })).getByLabelText(/research fields/i), "\nHuman-computer interaction");

    await userEvent.click(screen.getByRole("button", { name: "Account" }));
    expect(screen.getByRole("heading", { name: "Account" })).toBeTruthy();
    await userEvent.click(screen.getByRole("button", { name: "Back to Home" }));
    await userEvent.click(screen.getByRole("button", { name: /return to your room ROOM1/i }));

    await userEvent.click(screen.getByRole("button", { name: /settings.*controls/i }));
    const reopened = within(screen.getByRole("dialog", { name: "Controls" }));
    expect(reopened.getByLabelText(/question budget/i)).toHaveValue(12);
    expect(reopened.getByLabelText(/research fields/i)).toHaveValue("Education\nSoftware engineering\nHuman-computer interaction");
  });

  // Review fix 3: the legacy account query must keep its destination over a conflicting fragment.
  it("keeps the legacy account destination when a conflicting fragment is present", () => {
    setAccount(account({ authenticated: true, user: { id: "u1", name: "Host", email: "host@example.com" }, csrf_token: "csrf", payment_mode: "test" }));
    setSocket(null, { connected: false });
    renderAt("/?account=1#/home");
    expect(screen.getByRole("heading", { name: "Account" })).toBeTruthy();
    expect(screen.getByText("host@example.com")).toBeTruthy();
  });

  // Review fix 4: a screen change must move focus to the new heading.
  it("moves focus to the new screen heading after the opener is removed", async () => {
    setSocket(null, { connected: false });
    setAccount(account({ authenticated: false, google_enabled: true }));
    renderAt("/#/home");
    await userEvent.click(screen.getByRole("button", { name: "Create a defense" }));
    expect(screen.getByRole("heading", { name: "Sign in" })).toHaveFocus();
  });

  // Review fix 4: ordinary same-screen updates must not steal focus.
  it("does not steal focus when account data refreshes on the same screen", () => {
    setAccount(account({ authenticated: true, user: { id: "u1", name: "Host", email: "host@example.com" }, csrf_token: "csrf", payment_mode: "test", test_credits: 1 }));
    setSocket(null, { connected: false });
    const view = renderAt("/#/account");
    const signOut = screen.getByRole("button", { name: "Sign out" });
    signOut.focus();
    setAccount(account({ authenticated: true, user: { id: "u1", name: "Host", email: "host@example.com" }, csrf_token: "csrf", payment_mode: "test", test_credits: 5 }));
    view.rerender(<App />);
    expect(signOut).toHaveFocus();
  });

  // Review fix 5: inherited object keys must not resolve to non-screen routes.
  it.each(["constructor", "toString", "__proto__", "hasOwnProperty"])(
    "shows Home with guidance for the inherited property fragment #%s",
    (name) => {
      setAccount(account());
      setSocket(null, { connected: false });
      renderAt(`/#${name}`);
      expect(screen.getByRole("heading", { name: "Home" })).toBeTruthy();
      expect(screen.getByRole("status")).toHaveTextContent(/couldn’t open that screen/i);
    },
  );
});

import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { App } from "./App";
import { useAccount, type Account } from "./hooks/useAccount";
import { useRoomSocket, type RoomSocketState } from "./hooks/useRoomSocket";
import type { RoomState } from "./types";

vi.mock("./hooks/useAccount", async importOriginal => ({ ...await importOriginal<typeof import("./hooks/useAccount")>(), useAccount: vi.fn() }));
vi.mock("./hooks/useRoomSocket", () => ({ useRoomSocket: vi.fn() }));
let socket: RoomSocketState;
function identity(id: string | null) {
  const account: Account = { authenticated: !!id, google_enabled: true, user: id ? { id, name: "Alex", email: "fixture@example.com" } : undefined,
    payment_mode: "live", csrf_token: "fixture-csrf", topup_invited: true, free_access: true };
  vi.mocked(useAccount).mockReturnValue({ account, error: "", refresh: vi.fn(async () => {}) });
}
const room = (extra: Partial<RoomState> = {}): RoomState => ({ room_code: "TASK1", defense_view_id: "view", self_seat: 0, self_is_host: true,
  players: [{ seat: 0, name: "Alex", online: true, is_host: true }], phase: "question", selected_seat: 0,
  turns: [{ panelist: "Technical Architect", question: "Why queue?", filename: "app.py", evidence_line: 1, evidence_text: "queue=[]", answer: null, answered_by: null }],
  active_panelist: "Technical Architect", feedback_status: "none", feedback: null, revision: 1, error: null, files: [], ...extra });
beforeEach(() => {
  sessionStorage.clear(); window.history.replaceState(null, "", "/#/room"); identity("host");
  socket = { roomState: room(), roomCode: "TASK1", connected: true, playerToken: "fixture", knownHost: true,
    waitingForAnswerAck: false, actionError: null, actionErrorReason: null, sendEvent: vi.fn(() => true), useRoom: vi.fn(), leaveRoom: vi.fn() };
  vi.mocked(useRoomSocket).mockImplementation(() => socket);
  vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify({ mode: "live", enabled: false, packages: [] }), { status: 200 })));
});
afterEach(() => { vi.unstubAllGlobals(); vi.clearAllMocks(); });

it("opens legacy same-origin top-up in the shell and returns to the current results with the room still connected", async () => {
  const view = render(<App />);
  await userEvent.type(screen.getByRole("textbox", { name: /chosen to answer/i }), "Keep this draft.");
  await userEvent.click(screen.getByRole("button", { name: "Account" }));
  await userEvent.click(screen.getByRole("link", { name: "Top up credits" }));
  expect(screen.getByRole("heading", { name: "Credits & purchases" })).toBeVisible();
  socket.roomState = room({ phase: "complete", feedback_status: "ready", feedback: { summary: "Saved coaching.", strengths: [], improvements: [], next_step: "Practice." } });
  view.rerender(<App />);
  expect(screen.getByRole("heading", { name: "Credits & purchases" })).toBeVisible();
  await userEvent.click(screen.getByRole("button", { name: "View defense results" }));
  expect(screen.getByText("Saved coaching.")).toBeVisible();
  expect(socket.sendEvent).not.toHaveBeenCalled(); expect(socket.useRoom).not.toHaveBeenCalled(); expect(socket.leaveRoom).not.toHaveBeenCalled();
  expect(vi.mocked(fetch).mock.calls.every(([, init]) => !init?.method || init.method === "GET")).toBe(true);
});

it("returns a signed-out Create through the exact existing callback into setup, consuming the task without creating", async () => {
  identity(null); socket.roomState = null; socket.roomCode = null; socket.playerToken = null;
  window.history.replaceState(null, "", "/#/home");
  const first = render(<App />);
  await userEvent.click(screen.getByRole("button", { name: "Create a defense" }));
  expect(screen.getByRole("link", { name: "Sign in with Google" })).toHaveAttribute("href", "/api/auth/google/login?return_to=%2F%3Faccount%3D1");
  first.unmount(); identity("host"); window.history.replaceState(null, "", "/?account=1");
  const returned = render(<App />);
  await waitFor(() => expect(screen.getByRole("heading", { name: "Bring your work." })).toBeVisible());
  expect(socket.useRoom).not.toHaveBeenCalled(); expect(socket.sendEvent).not.toHaveBeenCalled();
  returned.unmount(); window.history.replaceState(null, "", "/?account=1"); render(<App />);
  expect(screen.getByRole("heading", { name: "Account" })).toBeVisible();
});

it("rejects a foreign-account task and never returns to a lost room", async () => {
  const first = render(<App />);
  await userEvent.click(screen.getByRole("button", { name: /settings.*controls/i }));
  await userEvent.click(screen.getByRole("button", { name: /Account ↗/ }));
  first.unmount(); identity("foreign"); window.history.replaceState(null, "", "/?account=1");
  const foreign = render(<App />);
  expect(screen.getByRole("heading", { name: "Account" })).toBeVisible();
  foreign.unmount(); identity("host"); socket.roomState = null; socket.roomCode = null;
  window.history.replaceState(null, "", "/?account=1"); render(<App />);
  expect(screen.getByRole("heading", { name: "Account" })).toBeVisible();
  expect(socket.sendEvent).not.toHaveBeenCalled();
});

it("keeps original legacy entry precedence and owner permission checks", () => {
  window.history.replaceState(null, "", "/?manager=1&payments=live&account=1#/home");
  render(<App />);
  expect(screen.getByRole("heading", { name: "Manage access and credits" })).toBeVisible();
  expect(screen.getByRole("alert")).toHaveTextContent("configured owner account");
  expect(screen.queryByRole("button", { name: "Add tester" })).toBeNull();
  expect(socket.sendEvent).not.toHaveBeenCalled();
});

it("preserves the originating WebView task through native sign-in resume without changing the callback", async () => {
  identity(null); socket.roomState = null; socket.roomCode = null;
  window.history.replaceState(null, "", "/#/home");
  const view = render(<App />);
  await userEvent.click(screen.getByRole("button", { name: "Create a defense" }));
  const signin = screen.getByRole("link", { name: "Sign in with Google" });
  expect(signin).toHaveAttribute("href", "/api/auth/google/login?return_to=%2F%3Faccount%3D1");
  act(() => window.dispatchEvent(new Event("defense-native-resume")));
  identity("host"); view.rerender(<App />);
  await waitFor(() => expect(screen.getByRole("heading", { name: "Bring your work." })).toBeVisible());
  expect(socket.useRoom).not.toHaveBeenCalled();
});

it.each(["expired", "malformed"])("discards %s task intent at the existing callback", async kind => {
  const first = render(<App />);
  await userEvent.click(screen.getByRole("button", { name: "Account" }));
  const key = Object.keys(sessionStorage).find(key => sessionStorage.getItem(key)?.includes('"target":"room"'));
  expect(key).toBeTruthy();
  first.unmount();
  if (kind === "expired") {
    const stored = JSON.parse(sessionStorage.getItem(key!)!); stored.created = 0; sessionStorage.setItem(key!, JSON.stringify(stored));
  } else sessionStorage.setItem(key!, JSON.stringify({ target: "https://attacker.invalid/" }));
  window.history.replaceState(null, "", "/?account=1"); render(<App />);
  expect(screen.getByRole("heading", { name: "Account" })).toBeVisible();
  expect(sessionStorage.getItem(key!)).toBeNull();
  expect(socket.sendEvent).not.toHaveBeenCalled();
});

it("returns unfinished new-room setup ahead of the older foreground room", async () => {
  socket.roomState = room({ phase: "lobby", turns: [] });
  window.history.replaceState(null, "", "/#/prepare");
  render(<App />);
  await userEvent.click(screen.getByRole("button", { name: "Create another room" }));
  await userEvent.click(screen.getByRole("button", { name: "Account ↗" }));
  await userEvent.click(screen.getByRole("button", { name: "Return to setup" }));
  expect(screen.getByRole("heading", { name: "Create another room" })).toBeVisible();
  expect(screen.getByRole("combobox", { name: "Defense type" })).toBeVisible();
  expect(socket.useRoom).not.toHaveBeenCalled(); expect(socket.leaveRoom).not.toHaveBeenCalled();
});

it("keeps new-room intent across an authentication reload and subsequent setup reload", async () => {
  socket.roomState = room({ phase: "lobby", turns: [] });
  window.history.replaceState(null, "", "/#/prepare");
  const first = render(<App />);
  await userEvent.click(screen.getByRole("button", { name: "Create another room" }));
  await userEvent.click(screen.getByRole("button", { name: "Account ↗" }));
  first.unmount(); window.history.replaceState(null, "", "/?account=1");
  const returned = render(<App />);
  await waitFor(() => expect(screen.getByRole("combobox", { name: "Defense type" })).toBeVisible());
  returned.unmount(); render(<App />);
  expect(screen.getByRole("combobox", { name: "Defense type" })).toBeVisible();
  expect(socket.useRoom).not.toHaveBeenCalled(); expect(socket.sendEvent).not.toHaveBeenCalled();
});

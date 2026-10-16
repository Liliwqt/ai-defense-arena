import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
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
  room_code: "ROOM1", self_seat: 0, self_is_host: true, phase: "lobby",
  players: [{ seat: 0, name: "Alex", online: true, is_host: true }], turns: [],
  active_panelist: null, error: null, revision: 1, files: [],
  feedback_status: "none", feedback: null, ...overrides,
});

// A mutable socket so a mocked useRoom can switch the foreground room and the
// next render (triggered by navigation) observes the new snapshot.
function setSocket(state: RoomState | null, overrides: Partial<RoomSocketState> = {}) {
  const socket: RoomSocketState = {
    roomState: state, connected: state !== null, roomCode: state?.room_code ?? null, knownHost: true,
    waitingForAnswerAck: false, actionError: null, actionErrorReason: null, sendEvent: vi.fn(() => true),
    useRoom: vi.fn(), leaveRoom: vi.fn(), playerToken: "token", ...overrides,
  };
  vi.mocked(socket.useRoom).mockImplementation((code: string, token: string, host: boolean) => {
    socket.roomCode = code;
    socket.roomState = roomState({ room_code: code, self_is_host: host, defense_type: "code", accepted_files: [{ name: "app.py", kind: "code", detail: "" }] });
    void token;
  });
  vi.mocked(useRoomSocket).mockImplementation(() => socket);
  return socket;
}

function mockRoomRequests() {
  const requests: Array<ReturnType<typeof makeRequest>> = [];
  function makeRequest() {
    return Object.assign(new EventTarget(), {
      upload: new EventTarget(), status: 0, responseText: "",
      open: vi.fn(), setRequestHeader: vi.fn(), send: vi.fn(),
    });
  }
  vi.stubGlobal("XMLHttpRequest", vi.fn(function () {
    const request = makeRequest();
    requests.push(request);
    return request;
  }));
  return requests;
}

const hostAccount = (overrides: Partial<Account> = {}) => account({
  authenticated: true, user: { id: "u1", name: "Host", email: "host@example.com" },
  csrf_token: "csrf", payment_mode: "test", test_credits: 40, ...overrides,
});

beforeEach(() => { sessionStorage.clear(); window.history.replaceState(null, "", "/"); });
afterEach(() => { window.history.replaceState(null, "", "/"); vi.unstubAllGlobals(); vi.clearAllMocks(); });

describe("guided setup and preparation", () => {
  it("opens a full-screen create setup from Home for a signed-in host without creating a room", async () => {
    setSocket(null);
    setAccount(hostAccount());
    renderAt("/");
    await userEvent.click(screen.getByRole("button", { name: "Create a defense" }));

    expect(window.location.hash).toBe("#/setup");
    expect(screen.getByRole("heading", { name: "Bring your work." })).toBeTruthy();
    expect(document.querySelector("#create-form")).not.toBeNull();
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(screen.getByRole("button", { name: "Back" })).toBeTruthy();
    expect(document.querySelectorAll("input[type=file]").length).toBe(1);
  });

  it("opens a full-screen Join setup from Home without joining a room", async () => {
    const socket = setSocket(null);
    setAccount(account());
    renderAt("/");
    await userEvent.click(screen.getByRole("button", { name: "Join a room" }));

    expect(window.location.hash).toBe("#/setup");
    expect(screen.getByRole("heading", { name: "Join a room" })).toBeTruthy();
    expect(document.querySelector("#join-form")).not.toBeNull();
    expect(socket.useRoom).not.toHaveBeenCalled();
  });

  it("returns to Home from the setup Back action", async () => {
    setSocket(null);
    setAccount(account());
    renderAt("/");
    await userEvent.click(screen.getByRole("button", { name: "Join a room" }));
    await userEvent.click(screen.getByRole("button", { name: "Back" }));
    expect(window.location.hash).toBe("#/home");
    expect(screen.getByRole("heading", { name: "Home" })).toBeTruthy();
  });

  it("keeps setup files, name and defense type while navigating Home and back", async () => {
    setSocket(null);
    setAccount(hostAccount());
    renderAt("/");
    await userEvent.click(screen.getByRole("button", { name: "Create a defense" }));

    const name = screen.getByRole("textbox", { name: "Your name" });
    await userEvent.clear(name);
    await userEvent.type(name, "Team Rocket");
    await userEvent.selectOptions(screen.getByLabelText("Defense type"), "research");
    const upload = screen.getByLabelText("Research documents") as HTMLInputElement;
    const paper = new File(["proposal"], "paper.md", { type: "text/markdown" });
    await userEvent.upload(upload, paper);

    await userEvent.click(screen.getByRole("button", { name: "Back" }));
    expect(screen.getByRole("heading", { name: "Home" })).toBeTruthy();
    await userEvent.click(screen.getByRole("button", { name: "Create a defense" }));

    expect(screen.getByRole("textbox", { name: "Your name" })).toHaveValue("Team Rocket");
    expect(screen.getByLabelText("Defense type")).toHaveValue("research");
    expect((screen.getByLabelText("Research documents") as HTMLInputElement).files?.[0]).toBe(paper);
  });

  it("groups setup and material in Guided cards and creates through the next-step action", async () => {
    const requests = mockRoomRequests();
    setSocket(null);
    setAccount(hostAccount());
    renderAt("/#/setup");
    expect(screen.getByRole("heading", { name: "What are you preparing?" })).toBeVisible();
    expect(screen.getByRole("heading", { name: "Your work" })).toBeVisible();
    await userEvent.upload(screen.getByLabelText("Project source files or ZIP"), new File(["print(1)"], "app.py", { type: "text/plain" }));
    const next = within(screen.getByRole("complementary", { name: "Room and next step" })).getByRole("button", { name: "Create defense room" });
    // jsdom's native file-required validation does not see userEvent's FileList.
    // Real file validation is covered separately in Chromium.
    (next as HTMLButtonElement).form!.noValidate = true;
    await userEvent.click(next);
    expect(requests).toHaveLength(1);
    expect(next).toBeDisabled();
    await userEvent.click(next);
    expect(requests).toHaveLength(1);
    await act(async () => { requests[0].dispatchEvent(new Event("error")); });
  });

  it("opens preparation with the shareable code after one explicit create", async () => {
    const requests = mockRoomRequests();
    setSocket(null);
    setAccount(hostAccount());
    renderAt("/#/setup");
    fireEvent.submit(document.querySelector("#create-form")!);
    expect(requests).toHaveLength(1);

    await act(async () => {
      requests[0].status = 201;
      requests[0].responseText = JSON.stringify({ room_code: "ROOM9", player_token: "tok" });
      requests[0].dispatchEvent(new Event("load"));
    });

    await waitFor(() => expect(screen.getByRole("heading", { name: "Prepare your defense" })).toBeTruthy());
    expect(window.location.hash).toBe("#/prepare");
    expect(within(screen.getByRole("complementary", { name: "Room and next step" })).getByText("ROOM9")).toBeTruthy();
    expect(document.querySelector("#create-form")).not.toBeVisible();
    expect(requests).toHaveLength(1);
  });

  it("clears completed uploads only when explicitly creating another room", async () => {
    const requests = mockRoomRequests();
    setSocket(null);
    setAccount(hostAccount());
    renderAt("/#/setup");
    const upload = screen.getByLabelText("Project source files or ZIP") as HTMLInputElement;
    await userEvent.upload(upload, new File(["print(1)"], "old.py", { type: "text/plain" }));
    fireEvent.submit(document.querySelector("#create-form")!);
    await act(async () => {
      requests[0].status = 201;
      requests[0].responseText = JSON.stringify({ room_code: "ROOM9", player_token: "tok" });
      requests[0].dispatchEvent(new Event("load"));
    });
    await userEvent.click(screen.getByRole("button", { name: "Create another room" }));
    expect((screen.getByLabelText("Project source files or ZIP") as HTMLInputElement).files).toHaveLength(0);
    expect(screen.queryByText("Room created successfully.")).toBeNull();
    expect(requests).toHaveLength(1);
  });

  it("shows an existing room's accepted files instead of a replacement form on setup", () => {
    setSocket(roomState({ defense_type: "research", accepted_files: [{ name: "study.pdf", kind: "research_pdf", detail: "3 pages" }] }));
    setAccount(hostAccount());
    renderAt("/#/setup");

    expect(screen.getByRole("heading", { name: "Your material" })).toBeTruthy();
    expect(within(screen.getByRole("group", { name: "Accepted files" })).getByText(/study.pdf · 3 pages/)).toBeVisible();
    expect(document.querySelector("#create-form")).not.toBeVisible();
  });

  it("opens fresh setup from preparation and retains selected files through preparation and Home", async () => {
    const socket = setSocket(roomState({ defense_type: "code" }));
    setAccount(hostAccount());
    renderAt("/#/prepare");
    await userEvent.click(screen.getByRole("button", { name: "Create another room" }));
    expect(window.location.hash).toBe("#/setup?new=1");
    const file = new File(["print(1)"], "sample.py", { type: "text/plain" });
    await userEvent.upload(screen.getByLabelText("Project source files or ZIP"), file);
    await userEvent.click(screen.getByRole("button", { name: "Back" }));
    await userEvent.click(screen.getByRole("button", { name: "Back to setup" }));
    expect((screen.getByLabelText("Project source files or ZIP") as HTMLInputElement).files?.[0]).toBe(file);
    expect(socket.leaveRoom).not.toHaveBeenCalled();
    expect(socket.sendEvent).not.toHaveBeenCalled();
  });

  it("offers Create another room from an existing room without leaving or closing it", async () => {
    const socket = setSocket(roomState({ defense_type: "research", accepted_files: [{ name: "study.pdf", kind: "research_pdf", detail: "3 pages" }] }));
    setAccount(hostAccount());
    renderAt("/#/setup");

    await userEvent.click(screen.getByRole("button", { name: "Create another room" }));
    expect(screen.getByRole("heading", { name: "Create another room" })).toBeTruthy();
    expect(document.querySelector("#create-form")).not.toBeNull();
    expect(socket.sendEvent).not.toHaveBeenCalled();
    expect(socket.leaveRoom).not.toHaveBeenCalled();
  });

  it("does not request a research map merely by opening preparation", () => {
    const socket = setSocket(roomState({ defense_type: "research", research_planning_status: "none", accepted_files: [{ name: "study.pdf", kind: "research_pdf", detail: "3 pages" }] }));
    setAccount(hostAccount());
    renderAt("/#/prepare");

    expect(socket.sendEvent).not.toHaveBeenCalled();
    expect(screen.getByRole("button", { name: /map paper/i })).toBeTruthy();
    expect(screen.queryByRole("button", { name: /start defense/i })).toBeNull();
  });

  it("shows a ready-to-start preparation for a code-only room without research mapping", () => {
    setSocket(roomState({ defense_type: "code", accepted_files: [{ name: "app.py", kind: "code", detail: "" }] }));
    setAccount(hostAccount({ free_access: true }));
    renderAt("/#/prepare");

    expect(screen.getByRole("button", { name: /start defense/i })).toBeTruthy();
    expect(screen.queryByText(/research coverage plan/i)).toBeNull();
    expect(screen.queryByRole("button", { name: /map paper/i })).toBeNull();
  });

  it("explains an uncertain creation and offers owned-room recovery before another attempt", async () => {
    const requests = mockRoomRequests();
    setSocket(null);
    setAccount(hostAccount());
    renderAt("/#/setup");
    fireEvent.submit(document.querySelector("#create-form")!);
    await act(async () => { requests[0].dispatchEvent(new Event("error")); });

    expect(screen.getByText(/confirm whether the room was created/i)).toBeTruthy();
    expect(screen.getByRole("button", { name: /manage my rooms/i })).toBeTruthy();
  });

  it.each(["home", "account"])("keeps a delayed create failure from covering %s and retains it on return", async (destination) => {
    const requests = mockRoomRequests();
    setSocket(null);
    setAccount(hostAccount());
    renderAt("/#/setup");
    fireEvent.submit(document.querySelector("#create-form")!);
    await act(async () => {
      window.history.pushState(null, "", `/#/${destination}`);
      window.dispatchEvent(new PopStateEvent("popstate"));
    });
    await act(async () => { requests[0].dispatchEvent(new Event("error")); });
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(window.location.hash).toBe(`#/${destination}`);
    await act(async () => {
      window.history.pushState(null, "", "/#/setup");
      window.dispatchEvent(new PopStateEvent("popstate"));
    });
    expect(screen.getByRole("alert")).toHaveTextContent(/could not connect/i);
  });

  it("moves between the room and preparation screens without sending Leave, End or Close", async () => {
    const socket = setSocket(roomState({ defense_type: "code" }));
    setAccount(hostAccount());
    renderAt("/#/room");

    await userEvent.click(screen.getByRole("button", { name: "Home" }));
    expect(screen.getByRole("heading", { name: "Home" })).toBeTruthy();
    await userEvent.click(screen.getByRole("button", { name: /return to your room ROOM1/i }));

    expect(window.location.hash).toBe("#/room");
    expect(socket.sendEvent).not.toHaveBeenCalled();
    expect(socket.leaveRoom).not.toHaveBeenCalled();
  });

  it("lists, resumes and closes owned retained rooms from setup", async () => {
    const socket = setSocket(null);
    setAccount(hostAccount());
    const calls: Array<{ url: string; method: string }> = [];
    const respond = (body: unknown) => ({ ok: true, status: 200, json: async () => body });
    vi.stubGlobal("fetch", vi.fn(async (url: string, init?: RequestInit) => {
      const method = init?.method ?? "GET";
      calls.push({ url: String(url), method });
      if (String(url) === "/api/rooms") return respond({ rooms: [{ room_code: "OLD111", phase: "lobby", can_close: true, expires_at_ms: null }], limit: 2 });
      if (String(url).endsWith("/OLD111/resume")) return respond({ room_code: "OLD111", player_token: "tok" });
      return respond({});
    }));

    renderAt("/#/setup");
    await userEvent.click(screen.getByRole("button", { name: /manage my rooms/i }));
    await waitFor(() => expect(screen.getByText("OLD111")).toBeTruthy());

    await userEvent.click(screen.getByRole("button", { name: /resume OLD111/i }));
    expect(socket.useRoom).toHaveBeenCalledWith("OLD111", "tok", true);

    await userEvent.click(screen.getByRole("button", { name: /close OLD111/i }));
    expect(calls).toContainEqual({ url: "/api/rooms/OLD111", method: "DELETE" });
  });

  it("keeps the legacy account screen reachable and unchanged", () => {
    setSocket(null);
    setAccount(hostAccount());
    renderAt("/?account=1#/home");
    expect(screen.getByRole("heading", { name: "Account" })).toBeTruthy();
    expect(screen.getByText("host@example.com")).toBeTruthy();
  });
});

describe("setup screen accessibility", () => {
  it("announces the preparation step and moves focus to the setup heading", async () => {
    setSocket(null);
    setAccount(hostAccount());
    renderAt("/");
    await userEvent.click(screen.getByRole("button", { name: "Create a defense" }));

    const steps = within(screen.getByRole("list", { name: "Preparation steps" })).getAllByRole("listitem");
    expect(steps[0].getAttribute("aria-current")).toBe("step");
    expect(screen.getByRole("heading", { name: "Bring your work." })).toHaveFocus();
  });
});

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { App } from "./App";
import { useAccount } from "./hooks/useAccount";
import { useRoomSocket, type RoomSocketState } from "./hooks/useRoomSocket";
import { researchPlanPreview } from "./researchPlanPreview";
import type { RoomState } from "./types";

vi.mock("./hooks/useAccount", () => ({ useAccount: vi.fn() }));
vi.mock("./hooks/useRoomSocket", () => ({ useRoomSocket: vi.fn() }));
let socket: RoomSocketState;
const room = (extra: Partial<RoomState> = {}): RoomState => ({
  room_code: "DRAFT1", defense_view_id: "view-a", self_seat: 0, self_is_host: true,
  players: [{ seat: 0, name: "Alex", online: true, is_host: true }], phase: "question", selected_seat: 0,
  turns: [{ panelist: "Technical Architect", question: "Why a queue?", filename: "app.py", evidence_line: 1,
    evidence_text: "queue = []", answer: null, answered_by: null }], active_panelist: "Technical Architect",
  feedback_status: "none", feedback: null, revision: 1, error: null, files: [], ...extra,
});
beforeEach(() => {
  sessionStorage.clear();
  window.history.replaceState(null, "", "/#/setup");
  vi.mocked(useAccount).mockReturnValue({ account: { authenticated: true, google_enabled: true,
    user: { id: "host", name: "Alex", email: "host@example.com" }, free_access: true }, error: "", refresh: vi.fn(async () => {}) });
  socket = { roomState: null, roomCode: null, connected: false, knownHost: false, playerToken: null,
    waitingForAnswerAck: false, actionError: null, actionErrorReason: null, sendEvent: vi.fn(() => true), useRoom: vi.fn(), leaveRoom: vi.fn() };
  vi.mocked(useRoomSocket).mockImplementation(() => socket);
});
afterEach(() => { vi.restoreAllMocks(); vi.unstubAllGlobals(); });

it("restores same-tab setup text after a fresh mount while requesting file reselection and replaying nothing", async () => {
  const first = render(<App />);
  const name = screen.getByRole("textbox", { name: "Your name" });
  await userEvent.clear(name); await userEvent.type(name, "Returning researcher");
  await userEvent.selectOptions(screen.getByRole("combobox", { name: "Defense type" }), "research");
  await userEvent.selectOptions(screen.getByRole("combobox", { name: "Research stage" }), "proposal");
  first.unmount();
  render(<App />);
  expect(screen.getByRole("textbox", { name: "Your name" })).toHaveValue("Returning researcher");
  expect(screen.getByRole("combobox", { name: "Defense type" })).toHaveValue("research");
  expect(screen.getByRole("combobox", { name: "Research stage" })).toHaveValue("proposal");
  expect(screen.getByText(/select your unsubmitted files again/i)).toBeVisible();
  expect(socket.sendEvent).not.toHaveBeenCalled(); expect(socket.useRoom).not.toHaveBeenCalled();
});

it("validates membership before restoring an answer and clears it for a new turn or restart", async () => {
  window.history.replaceState(null, "", "/#/room");
  socket.roomState = room(); socket.roomCode = "DRAFT1"; socket.playerToken = "private-fixture-token"; socket.connected = true;
  const first = render(<App />);
  await userEvent.type(screen.getByRole("textbox", { name: /chosen to answer/i }), "We serialize writes.");
  first.unmount();
  const current = socket.roomState;
  socket.roomState = null; socket.connected = false;
  const restored = render(<App />);
  expect(screen.queryByRole("textbox", { name: /chosen to answer/i })).toBeNull();
  socket.roomState = current; socket.connected = true;
  restored.rerender(<App />);
  await waitFor(() => expect(screen.getByRole("textbox", { name: /chosen to answer/i })).toHaveValue("We serialize writes."));
  socket.roomState = { ...current, revision: 2, turns: [{ ...current!.turns[0], clarifications: [{ request: "In Bisaya", reply: "Explain the queue." }] }] };
  restored.rerender(<App />);
  expect(screen.getByRole("textbox", { name: /chosen to answer/i })).toHaveValue("We serialize writes.");
  socket.roomState = { ...current!, defense_view_id: "view-restarted" };
  restored.rerender(<App />);
  expect(screen.getByRole("textbox", { name: /chosen to answer/i })).toHaveValue("");
  expect(socket.sendEvent).not.toHaveBeenCalled();
  expect(JSON.stringify(sessionStorage)).not.toContain("private-fixture-token");
});

it("recovers profile and budget edits without treating restored review as server approval", async () => {
  window.history.replaceState(null, "", "/#/prepare");
  socket.roomState = room({ phase: "lobby", defense_type: "research", turns: [], research_planning_status: "ready",
    research_plan: researchPlanPreview, research_budget_preview: 14, research_plan_approved: false });
  socket.roomCode = "DRAFT1"; socket.playerToken = "fixture-host"; socket.connected = true;
  const first = render(<App />);
  await userEvent.clear(screen.getByRole("spinbutton", { name: "Question budget" }));
  await userEvent.type(screen.getByRole("spinbutton", { name: "Question budget" }), "18");
  await userEvent.click(screen.getByText("Correct profile"));
  await userEvent.type(screen.getByLabelText("Research fields (one per line)"), "\nPublic health");
  // A dirty profile intentionally locks budget changes. Restore the editor first.
  first.unmount();
  const view = render(<App />);
  await userEvent.click(screen.getByText("Correct profile"));
  await waitFor(() => expect(screen.getByLabelText("Research fields (one per line)")).toHaveValue([...researchPlanPreview.profile!.fields, "Public health"].join("\n")));
  expect(screen.getByRole("spinbutton", { name: "Question budget" })).toHaveValue(18);
  expect(screen.getByRole("button", { name: /Start defense/ })).toBeDisabled();
  expect(socket.sendEvent).not.toHaveBeenCalled();
  socket.roomState = { ...socket.roomState!, research_plan: { ...researchPlanPreview, id: "new-map" } };
  view.rerender(<App />);
  expect(screen.getByLabelText("Research fields (one per line)")).toHaveValue(researchPlanPreview.profile!.fields.join("\n"));
});

it("retains chat and a pending probe draft on reload, but a different probe or account receives no old text", async () => {
  window.history.replaceState(null, "", "/#/room");
  const pending = { id: "probe-a", request: "Which writes?", references: [], reply: null, status: "pending" as const, clarifications: [] };
  socket.roomState = room({ phase: "probe", turns: [{ ...room().turns[0], answer: "We queue them.", probe: pending }] });
  socket.roomCode = "DRAFT1"; socket.playerToken = "probe-fixture"; socket.connected = true;
  const first = render(<App />);
  await userEvent.type(screen.getByRole("textbox", { name: /reply to panelist/i }), "Order writes.");
  await userEvent.click(screen.getByRole("tab", { name: /Team chat/ }));
  await userEvent.type(screen.getByRole("textbox", { name: "Team message" }), "Please review the method.");
  first.unmount();
  const view = render(<App />);
  await waitFor(() => expect(screen.getByRole("textbox", { name: /reply to panelist/i })).toHaveValue("Order writes."));
  await userEvent.click(screen.getByRole("tab", { name: /Team chat/ }));
  expect(screen.getByRole("textbox", { name: "Team message" })).toHaveValue("Please review the method.");
  socket.roomState = { ...socket.roomState!, turns: [{ ...socket.roomState!.turns[0], probe: { ...pending, id: "probe-b" } }] };
  view.rerender(<App />);
  await userEvent.click(screen.getByRole("tab", { name: "Vote / Answer" }));
  expect(screen.getByRole("textbox", { name: /reply to panelist/i })).toHaveValue("");
  vi.mocked(useAccount).mockReturnValue({ account: { authenticated: true, google_enabled: true,
    user: { id: "another", name: "Another", email: "other@example.com" } }, error: "", refresh: vi.fn(async () => {}) });
  view.rerender(<App />);
  await userEvent.click(screen.getByRole("tab", { name: /Team chat/ }));
  expect(screen.getByRole("textbox", { name: "Team message" })).toHaveValue("");
  expect(socket.sendEvent).not.toHaveBeenCalled();
});

it("keeps input usable with unavailable storage and preserves an in-memory answer across reconnect loading", async () => {
  vi.stubGlobal("sessionStorage", { getItem: () => { throw new Error("blocked"); }, setItem: () => { throw new Error("blocked"); }, removeItem: () => { throw new Error("blocked"); } });
  window.history.replaceState(null, "", "/#/room");
  const current = room(); socket.roomState = current; socket.roomCode = "DRAFT1"; socket.playerToken = "fixture";
  const view = render(<App />);
  await userEvent.type(screen.getByRole("textbox", { name: /chosen to answer/i }), "Keep in memory.");
  socket.roomState = null; socket.connected = false; view.rerender(<App />);
  socket.roomState = current; socket.connected = true; view.rerender(<App />);
  expect(screen.getByRole("textbox", { name: /chosen to answer/i })).toHaveValue("Keep in memory.");
  expect(screen.getByText(/refresh recovery.*unavailable/i)).toBeVisible();
  expect(socket.sendEvent).not.toHaveBeenCalled();
});

it("clears accepted answers and explicit Leave without resurrecting a lost report", async () => {
  window.history.replaceState(null, "", "/#/room");
  socket.roomState = room(); socket.roomCode = "DRAFT1"; socket.playerToken = "fixture"; socket.connected = true;
  const view = render(<App />);
  await userEvent.type(screen.getByRole("textbox", { name: /chosen to answer/i }), "My accepted answer.");
  socket.roomState = { ...room(), phase: "generating", turns: [{ ...room().turns[0], answer: "My accepted answer.", resolved: true }] };
  view.rerender(<App />);
  socket.roomState = room({ turns: [{ ...room().turns[0], answer: "My accepted answer." }, { ...room().turns[0], question: "Why now?" }] });
  view.rerender(<App />);
  expect(screen.getByRole("textbox", { name: /chosen to answer/i })).toHaveValue("");
  await userEvent.type(screen.getByRole("textbox", { name: /chosen to answer/i }), "Unsent next answer.");
  await userEvent.click(screen.getByRole("button", { name: /settings.*controls/i }));
  await userEvent.click(screen.getByRole("button", { name: "Leave room" }));
  expect(socket.leaveRoom).toHaveBeenCalledOnce();
  expect(JSON.stringify(sessionStorage)).not.toContain("Unsent next answer.");
  socket.roomState = null; socket.roomCode = null; socket.playerToken = null;
  window.history.replaceState(null, "", "/#/results");
  fireEvent(window, new PopStateEvent("popstate"));
  view.rerender(<App />);
  expect(screen.getByText(/Results cannot be restored from this browser/)).toBeVisible();
});

it("rejects corrupt saved input and keeps setup usable", async () => {
  const first = render(<App />);
  await userEvent.type(screen.getByRole("textbox", { name: "Your name" }), " local edit");
  const key = Object.keys(sessionStorage).find(key => sessionStorage.getItem(key)?.includes("local edit"));
  expect(key).toBeTruthy();
  first.unmount();
  sessionStorage.setItem(key!, "not valid JSON");
  render(<App />);
  expect(screen.getByRole("textbox", { name: "Your name" })).toHaveValue("Alex");
  expect(screen.getByText(/Saved drafts could not be read/)).toBeVisible();
  expect(socket.sendEvent).not.toHaveBeenCalled();
});

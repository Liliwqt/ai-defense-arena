import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
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

beforeEach(() => { window.history.replaceState(null, "", "/"); });
afterEach(() => { window.history.replaceState(null, "", "/"); vi.clearAllMocks(); vi.unstubAllGlobals(); });

function research(overrides: Partial<RoomState> = {}) {
  return roomState({ defense_type: "research", accepted_files: [{ name: "paper.pdf", kind: "research_pdf", detail: "7 pages" }],
    research_planning_status: "ready", research_plan: researchPlanPreview, research_budget_preview: 14,
    research_plan_approved: false, plan_attempts_left: 2, ...overrides });
}
function host() {
  setAccount(account({ authenticated: true, csrf_token: "fixture", free_access: true, payment_mode: "live" }));
}

describe("Guided research preparation", () => {
  it("puts profile and budget confirmation before expandable topics without mapping on entry", async () => {
    const socket = setSocket(research());
    host();
    renderAt("/#/prepare");
    const profile = screen.getByRole("region", { name: "Research profile" });
    const confirm = screen.getByRole("button", { name: "Confirm profile and budget" });
    const topics = screen.getByRole("list", { name: "Proposed research topics" });
    expect(profile.compareDocumentPosition(confirm) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(confirm.compareDocumentPosition(topics) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    const firstTopic = within(topics).getByText("Purpose and research gap").closest("details");
    expect(firstTopic).not.toHaveAttribute("open");
    await userEvent.click(within(firstTopic!).getByText("Purpose and research gap"));
    expect(within(firstTopic!).getByText(researchPlanPreview.topics[0].objective)).toBeVisible();
    expect(socket.sendEvent).not.toHaveBeenCalled();
  });
  it("maps only on the persistent action, suppresses repeats, and shows server activity and attempts", async () => {
    const snapshot = research({ research_plan: null, research_planning_status: "none" });
    const socket = setSocket(snapshot);
    host();
    const view = renderAt("/#/prepare");
    expect(socket.sendEvent).not.toHaveBeenCalled();
    const actions = within(screen.getByRole("complementary", { name: "Room and next step" }));
    const map = actions.getByRole("button", { name: "Map paper" });
    expect(screen.getByText("2 mapping attempts left")).toBeVisible();
    await userEvent.click(map);
    await userEvent.click(map);
    expect(socket.sendEvent).toHaveBeenCalledExactlyOnceWith({ type: "prepare_research_plan" });
    expect(map).toBeDisabled();
    socket.roomState = { ...snapshot, research_planning_status: "planning", plan_attempts_left: 1,
      research_plan_progress: { stage: "mapping", topics: [researchPlanPreview.topics[0]] } };
    view.rerender(<App />);
    expect(screen.getByRole("progressbar", { name: "Paper mapping progress" })).not.toHaveAttribute("aria-valuenow");
    expect(screen.getByRole("list", { name: "Draft research topics" })).toHaveTextContent("Purpose and research gap");
    expect(actions.queryByRole("button", { name: /start defense/i })).toBeNull();
    expect(socket.sendEvent).toHaveBeenCalledTimes(1);
  });

  it("waits for profile, uncertainty and server approval before one persistent Start", async () => {
    const snapshot = research({ research_plan: { ...researchPlanPreview, profile: {
      ...researchPlanPreview.profile!, needs_uncertainty_acknowledgment: true, uncertainties: ["Analysis is unclear."] } } });
    const socket = setSocket(snapshot);
    host();
    const view = renderAt("/#/prepare");
    const actions = within(screen.getByRole("complementary", { name: "Room and next step" }));
    expect(actions.getByRole("button", { name: /Start defense/ })).toBeDisabled();
    await userEvent.clear(screen.getByRole("spinbutton", { name: "Question budget" }));
    await userEvent.type(screen.getByRole("spinbutton", { name: "Question budget" }), "12");
    await userEvent.click(screen.getByLabelText("I reviewed the research profile"));
    expect(screen.getByRole("button", { name: "Confirm profile and budget" })).toBeDisabled();
    await userEvent.click(screen.getByLabelText("I understand the profile has unclear information"));
    const confirm = screen.getByRole("button", { name: "Confirm profile and budget" });
    await userEvent.click(confirm);
    await userEvent.click(confirm);
    expect(socket.sendEvent).toHaveBeenCalledExactlyOnceWith({ type: "approve_research_plan", plan_id: researchPlanPreview.id,
      question_budget: 12, confirm_profile: true, acknowledge_uncertainty: true });
    expect(actions.getByRole("button", { name: /Start defense/ })).toBeDisabled();
    expect(screen.queryByText(/Maximum confirmed:/)).toBeNull();
    socket.roomState = { ...snapshot, research_plan_approved: true, research_budget_preview: 12, revision: 2 };
    view.rerender(<App />);
    await userEvent.click(actions.getByRole("button", { name: /Start defense/ }));
    expect(socket.sendEvent).toHaveBeenLastCalledWith({ type: "start", confirm_cost: true, plan_id: researchPlanPreview.id, question_budget: 12 });
    await userEvent.click(screen.getByRole("button", { name: /settings.*controls/i }));
    expect(screen.getByRole("button", { name: /Start defense/ })).toBeDisabled();
    expect(socket.sendEvent).toHaveBeenCalledTimes(2);
  });

  it("explains exhausted mapping but still permits an already approved valid map to start", () => {
    const socket = setSocket(research({ research_plan: null, research_planning_status: "failed", plan_attempts_left: 0,
      research_plan_error: "Citation validation failed." }));
    host();
    const view = renderAt("/#/prepare");
    expect(screen.getByRole("button", { name: "Retry research map" })).toBeDisabled();
    expect(screen.getAllByText(/No mapping attempts left/).length).toBeGreaterThan(0);
    expect(screen.queryByRole("button", { name: /Start defense/ })).toBeNull();
    socket.roomState = research({ research_plan_approved: true, plan_attempts_left: 0 });
    view.rerender(<App />);
    expect(screen.getByRole("button", { name: /Start defense/ })).toBeEnabled();
  });

  it("keeps a retry pending when sending clears the previous error and unlocks on a new rejection", async () => {
    const snapshot = research({ research_plan: null, research_planning_status: "failed", research_plan_error: "Map failed." });
    const socket = setSocket(snapshot, { actionError: "Previous rejection" });
    vi.mocked(socket.sendEvent).mockImplementation(() => { socket.actionError = null; return true; });
    host();
    const view = renderAt("/#/prepare");
    await userEvent.click(screen.getByRole("button", { name: "Retry research map" }));
    view.rerender(<App />);
    expect(screen.getByRole("button", { name: "Retry research map" })).toBeDisabled();
    socket.actionError = "Please wait before another AI request.";
    view.rerender(<App />);
    expect(screen.getByRole("button", { name: "Retry research map" })).toBeEnabled();
    expect(socket.sendEvent).toHaveBeenCalledExactlyOnceWith({ type: "retry_research_plan" });
  });

  it("retains corrections across navigation and failed remapping, then requires fresh review", async () => {
    const snapshot = research({ research_plan_approved: true });
    const socket = setSocket(snapshot);
    host();
    const view = renderAt("/#/prepare");
    await userEvent.click(screen.getByText("Correct profile"));
    const fields = screen.getByLabelText("Research fields (one per line)");
    await userEvent.clear(fields);
    await userEvent.type(fields, "Public policy");
    expect(screen.getByRole("button", { name: /Start defense/ })).toBeDisabled();
    await userEvent.click(screen.getByRole("button", { name: "Account ↗" }));
    await userEvent.click(screen.getByRole("button", { name: "Back to Home" }));
    await userEvent.click(screen.getByRole("button", { name: "Create a defense" }));
    await userEvent.click(screen.getByRole("button", { name: "Back to preparation" }));
    expect(screen.getByLabelText("Research fields (one per line)")).toHaveValue("Public policy");
    await userEvent.click(screen.getByRole("button", { name: "Apply profile and remap" }));
    const correction = { fields: ["Public policy"], approaches: ["quantitative", "computational/design"] as const, setting: "University registrar" };
    expect(socket.sendEvent).toHaveBeenLastCalledWith({ type: "prepare_research_plan", profile_correction: correction });
    socket.roomState = { ...snapshot, research_plan: null, research_plan_approved: false,
      research_profile_correction: { ...correction, approaches: [...correction.approaches] }, research_planning_status: "failed", research_plan_error: "Map failed.", revision: 2 };
    view.rerender(<App />);
    expect(screen.getByRole("alert")).toHaveTextContent("Your uploads are retained");
    expect(screen.getByLabelText("Research fields (one per line)")).toHaveValue("Public policy");
    await userEvent.click(screen.getByRole("button", { name: "Retry research map" }));
    expect(socket.sendEvent).toHaveBeenLastCalledWith({ type: "retry_research_plan" });
    socket.roomState = research({ research_plan: { ...researchPlanPreview, id: "remapped", profile: {
      ...researchPlanPreview.profile!, ...correction, approaches: [...correction.approaches], host_description: { ...correction, approaches: [...correction.approaches] },
      source_description: { fields: ["Education"], approaches: ["quantitative"], setting: "Campus" } } }, revision: 3 });
    view.rerender(<App />);
    expect(screen.getByText("Host description")).toBeVisible();
    expect(screen.getByText("Paper-based suggestion")).toBeVisible();
    expect(screen.getByLabelText("I reviewed the research profile")).not.toBeChecked();
    expect(screen.getByRole("button", { name: /Start defense/ })).toBeDisabled();
    expect(socket.sendEvent).toHaveBeenCalledTimes(2);
  });

  it("creates research material, explicitly maps, confirms and starts without extra commands", async () => {
    const request = Object.assign(new EventTarget(), { upload: new EventTarget(), status: 0, responseText: "",
      open: vi.fn(), setRequestHeader: vi.fn(), send: vi.fn() });
    vi.stubGlobal("XMLHttpRequest", vi.fn(function () { return request; }));
    const socket = setSocket(null);
    vi.mocked(socket.useRoom).mockImplementation((code) => {
      socket.roomCode = code; socket.connected = true;
      socket.roomState = research({ room_code: code, research_plan: null, research_planning_status: "none" });
    });
    host();
    const view = renderAt("/#/setup");
    await userEvent.type(screen.getByRole("textbox", { name: "Your name" }), "Alex");
    await userEvent.selectOptions(screen.getByLabelText("Defense type"), "research");
    await userEvent.upload(screen.getByLabelText("Research documents"), new File(["Synthetic proposal"], "paper.md", { type: "text/markdown" }));
    fireEvent.submit(document.querySelector("#create-form")!);
    await act(async () => {
      request.status = 201; request.responseText = JSON.stringify({ room_code: "NEW1", player_token: "fixture" });
      request.dispatchEvent(new Event("load"));
    });
    await waitFor(() => expect(window.location.hash).toBe("#/prepare"));
    expect(socket.sendEvent).not.toHaveBeenCalled();
    await userEvent.click(screen.getByRole("button", { name: "Map paper" }));
    socket.roomState = research({ room_code: "NEW1" }); view.rerender(<App />);
    await userEvent.click(screen.getByLabelText("I reviewed the research profile"));
    await userEvent.click(screen.getByRole("button", { name: "Confirm profile and budget" }));
    socket.roomState = research({ room_code: "NEW1", research_plan_approved: true }); view.rerender(<App />);
    await userEvent.click(screen.getByRole("button", { name: /Start defense/ }));
    expect(vi.mocked(socket.sendEvent).mock.calls.map(([payload]) => payload.type)).toEqual(["prepare_research_plan", "approve_research_plan", "start"]);
    expect(request.send).toHaveBeenCalledTimes(1);
  });

  it("lets teammates inspect cited scope without host editing, approval or Start", async () => {
    const socket = setSocket(research({ self_is_host: false, research_plan_approved: true }));
    setAccount(account());
    renderAt("/#/prepare");
    expect(screen.getByRole("region", { name: "Research profile" })).toBeVisible();
    expect(screen.queryByRole("spinbutton")).toBeNull();
    expect(screen.queryByLabelText("Research fields (one per line)")).toBeNull();
    expect(screen.queryByRole("button", { name: /Map paper|Start defense|Confirm profile/ })).toBeNull();
    const profile = within(screen.getByRole("region", { name: "Research profile" }));
    await userEvent.click(profile.getByText(/Profile source references/));
    expect(profile.getByText(researchPlanPreview.profile!.references[0].evidence_text)).toBeVisible();
    expect(socket.sendEvent).not.toHaveBeenCalled();
  });

  it.each(["3", "101", "4.5", ""])("explains invalid budget %s without confirming or starting", async value => {
    const socket = setSocket(research()); host(); renderAt("/#/prepare");
    await userEvent.click(screen.getByLabelText("I reviewed the research profile"));
    fireEvent.change(screen.getByLabelText("Question budget"), { target: { value } });
    const confirm = screen.getByRole("button", { name: "Confirm profile and budget" });
    expect(confirm).toBeDisabled();
    expect(within(confirm.closest("form")!).getByText("Choose a whole-number question budget from 4 to 100.")).toBeVisible();
    expect(screen.getByRole("button", { name: /Start defense/ })).toBeDisabled();
    expect(socket.sendEvent).not.toHaveBeenCalled();
  });

  it.each([
    [{ authenticated: false }, true, "Sign in with the room owner’s Google account."],
    [{ authenticated: true, free_access: true, ai_service_available: false }, true, "The defense service is temporarily unavailable. Your credits are retained."],
    [{ authenticated: true, live_credits: 0, paid_starts_enabled: false }, true, "Paid starts are paused. Voucher access remains available."],
    [{ authenticated: true, live_credits: 0 }, true, "Use a free-access voucher or obtain 10 credits in Account."],
    [{ authenticated: true, free_access: true }, false, "Reconnect before starting the defense."],
  ] as const)("explains access or connection restrictions in the action area (%j)", (access, connected, message) => {
    setSocket(research({ research_plan_approved: true }), { connected });
    setAccount(account({ payment_mode: "live", ...access })); renderAt("/#/prepare");
    const actions = within(screen.getByRole("complementary", { name: "Room and next step" }));
    expect(actions.getByRole("button", { name: /Start defense/ })).toBeDisabled();
    expect(actions.getByText(message)).toBeVisible();
  });

  it("does not let a previous room's dirty profile block code-only readiness", async () => {
    const socket = setSocket(research({ research_plan_approved: true })); host();
    const view = renderAt("/#/prepare");
    await userEvent.click(screen.getByText("Correct profile"));
    await userEvent.type(screen.getByLabelText("Research fields (one per line)"), " changed");
    expect(screen.getByRole("button", { name: /Start defense/ })).toBeDisabled();
    socket.roomCode = "CODE2";
    socket.roomState = roomState({ room_code: "CODE2", defense_type: "code" });
    view.rerender(<App />);
    expect(screen.getByRole("button", { name: /Start defense/ })).toBeEnabled();
    expect(socket.sendEvent).not.toHaveBeenCalled();
  });

});

import { afterEach, describe, it, expect, vi } from "vitest";
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { ControlsPanel } from "./ControlsPanel";
import type { RoomState } from "../types";

const baseState: RoomState = {
  room_code: "ABCD12",
  self_seat: 0,
  self_is_host: true,
  phase: "lobby",
  players: [],
  turns: [],
  active_panelist: null,
  error: null,
  revision: 1,
  files: [],
  feedback_status: "none",
  feedback: null,
  server_now_ms: 1_000_000,
  vote_deadline_ms: null,
  answer_deadline_ms: null,
  selected_seat: null,
  vote_counts: {},
  my_vote: null,
  chat: [],
};

const defaultProps = {
  account: { authenticated: true, google_enabled: true, free_access: true },
  connected: true,
  previewMode: false,
  onUseRoom: vi.fn(),
  onLeaveRoom: vi.fn(),
  onSendEvent: vi.fn(() => true),
  onCloseDrawer: vi.fn(),
  showMessage: vi.fn(),
};

afterEach(() => { vi.unstubAllGlobals(); vi.useRealTimers(); });

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

describe("Room creation loading", () => {
  it("shows measured upload progress, waits for server validation and blocks duplicate submissions", async () => {
    vi.useFakeTimers();
    const requests = mockRoomRequests();
    const onUseRoom = vi.fn();
    render(<ControlsPanel {...defaultProps} roomState={null} connected={false} onUseRoom={onUseRoom} />);
    fireEvent.change(screen.getByLabelText("Your name"), { target: { value: "My team name" } });
    const form = document.querySelector("#create-form")!;
    fireEvent.submit(form);

    expect(screen.getByRole("status")).toHaveTextContent("Uploading files…");
    expect(screen.getByRole("progressbar")).toHaveAttribute("aria-valuenow", "0");
    expect(screen.getByText("0%")).toBeTruthy();
    expect(form).toHaveAttribute("aria-busy", "true");
    expect(screen.getByLabelText("Your name")).toBeDisabled();
    expect(screen.getByLabelText("Project source files or ZIP")).toBeDisabled();
    expect(screen.getByLabelText("Defense type")).toBeDisabled();
    expect(screen.getByRole("button", { name: "Creating…" })).toBeDisabled();
    const joinTab = screen.getByRole("tab", { name: "Join room" });
    expect(joinTab).toBeDisabled();
    fireEvent.keyDown(screen.getByRole("tab", { name: "Create room" }), { key: "ArrowRight" });
    expect(joinTab).toHaveAttribute("aria-selected", "false");
    fireEvent.submit(form);
    expect(requests).toHaveLength(1);
    const request = requests[0];
    expect((request.send.mock.calls[0][0] as FormData).get("host_name")).toBe("My team name");
    act(() => {
      request.upload.dispatchEvent(new ProgressEvent("progress", { loaded: 25, total: 100, lengthComputable: true }));
      vi.advanceTimersByTime(2000);
    });
    expect(screen.getByRole("progressbar")).toHaveAttribute("aria-valuenow", "25");
    expect(screen.getByText("25%")).toBeTruthy();
    expect(screen.getByText("2s elapsed")).toBeTruthy();
    act(() => request.upload.dispatchEvent(new Event("load")));
    expect(screen.getByRole("progressbar")).toHaveAttribute("aria-valuenow", "100");
    expect(screen.getByRole("status")).toHaveTextContent("Processing files and creating room…");
    expect(onUseRoom).not.toHaveBeenCalled();
    expect(screen.getByRole("button", { name: "Creating…" })).toBeDisabled();

    await act(async () => {
      request.status = 201;
      request.responseText = JSON.stringify({ room_code: "ROOM", player_token: "token" });
      request.dispatchEvent(new Event("load"));
    });
    expect(onUseRoom).toHaveBeenCalledExactlyOnceWith("ROOM", "token", true);
    expect(screen.getByRole("status")).toHaveTextContent("Room ready");
    expect(screen.getByLabelText("Your name")).toBeEnabled();
    expect(form).toHaveAttribute("aria-busy", "false");
    act(() => vi.advanceTimersByTime(1000));
    expect(screen.getByText("2s elapsed")).toBeTruthy();
  });

  it("clears loading after failure, preserves form values and allows a retry", async () => {
    const requests = mockRoomRequests();
    const onUseRoom = vi.fn();
    const showMessage = vi.fn();
    render(<ControlsPanel {...defaultProps} roomState={null} connected={false} onUseRoom={onUseRoom} showMessage={showMessage} />);
    fireEvent.change(screen.getByLabelText("Your name"), { target: { value: "Retry host" } });
    fireEvent.change(screen.getByLabelText("Defense type"), { target: { value: "research" } });
    const upload = screen.getByLabelText("Research documents") as HTMLInputElement;
    const paper = new File(["Research proposal"], "paper.md", { type: "text/markdown" });
    fireEvent.change(upload, { target: { files: [paper] } });
    fireEvent.submit(document.querySelector("#create-form")!);
    expect(screen.getByRole("progressbar")).toBeTruthy();

    await act(async () => { requests[0].dispatchEvent(new Event("error")); });
    expect(showMessage).toHaveBeenLastCalledWith("Could not connect to create the room. Check your connection and retry.");
    expect(onUseRoom).not.toHaveBeenCalled();
    expect(screen.queryByRole("progressbar")).toBeNull();
    expect(screen.getByRole("button", { name: "Create defense room" })).toBeEnabled();
    expect(screen.getByLabelText("Your name")).toHaveValue("Retry host");
    expect(screen.getByLabelText("Defense type")).toHaveValue("research");
    expect(upload.files?.[0]).toBe(paper);

    fireEvent.submit(document.querySelector("#create-form")!);
    expect(requests).toHaveLength(2);
    expect(screen.getByRole("progressbar")).toHaveAttribute("aria-valuenow", "0");
    await act(async () => {
      requests[1].status = 201;
      requests[1].responseText = JSON.stringify({ room_code: "RETRY", player_token: "token" });
      requests[1].dispatchEvent(new Event("load"));
    });
    expect(onUseRoom).toHaveBeenCalledExactlyOnceWith("RETRY", "token", true);
  });

  it("does not invent percentages when the browser cannot report upload size", () => {
    const requests = mockRoomRequests();
    render(<ControlsPanel {...defaultProps} roomState={null} connected={false} />);
    fireEvent.submit(document.querySelector("#create-form")!);
    act(() => requests[0].upload.dispatchEvent(new ProgressEvent("progress", { loaded: 20, lengthComputable: false })));
    expect(screen.getByRole("progressbar")).not.toHaveAttribute("aria-valuenow");
    expect(screen.queryByText(/\d+%/)).toBeNull();
    expect(screen.getByRole("status")).toHaveTextContent("Uploading files…");
  });

  it.each([
    [422, JSON.stringify({ detail: "This PDF has no readable text." }), "This PDF has no readable text."],
    [503, "Not JSON", "Request failed (503)."],
    [201, "null", "The server returned an incomplete room response. Please retry."],
  ])("does not treat upload completion as room success for invalid response %s", async (status, body, error) => {
    const requests = mockRoomRequests();
    const onUseRoom = vi.fn();
    const showMessage = vi.fn();
    render(<ControlsPanel {...defaultProps} roomState={null} connected={false} onUseRoom={onUseRoom} showMessage={showMessage} />);
    fireEvent.submit(document.querySelector("#create-form")!);
    act(() => requests[0].upload.dispatchEvent(new Event("load")));
    await act(async () => {
      requests[0].status = status;
      requests[0].responseText = body;
      requests[0].dispatchEvent(new Event("load"));
    });
    expect(onUseRoom).not.toHaveBeenCalled();
    expect(showMessage).toHaveBeenLastCalledWith(error);
    expect(screen.queryByRole("progressbar")).toBeNull();
    expect(screen.getByRole("button", { name: "Create defense room" })).toBeEnabled();
  });
});

describe("ControlsPanel", () => {
  it("shows create/join forms when roomState is null and not connected", () => {
    render(<ControlsPanel {...defaultProps} roomState={null} connected={false} />);
    expect(screen.getByRole("tab", { name: /create room/i })).toBeTruthy();
    expect(screen.getByRole("tab", { name: /join room/i })).toBeTruthy();
    expect(screen.queryByLabelText("Host passcode")).toBeNull();
  });

  it("moves between setup tabs with the arrow keys", () => {
    render(<ControlsPanel {...defaultProps} roomState={null} connected={false} />);
    const createTab = screen.getByRole("tab", { name: "Create room" });
    fireEvent.keyDown(createTab, { key: "ArrowRight" });
    const joinTab = screen.getByRole("tab", { name: "Join room" });
    expect(joinTab.getAttribute("aria-selected")).toBe("true");
    expect(document.activeElement).toBe(joinTab);
    fireEvent.keyDown(joinTab, { key: "ArrowLeft" });
    expect(createTab.getAttribute("aria-selected")).toBe("true");
    expect(document.activeElement).toBe(createTab);
  });

  it("offers separate research documents and stage for paper defenses", () => {
    render(<ControlsPanel {...defaultProps} roomState={null} connected={false} />);
    expect(screen.getByLabelText("Project source files or ZIP")).toBeTruthy();
    fireEvent.change(screen.getByLabelText("Defense type"), { target: { value: "mixed" } });
    expect(screen.getByLabelText("Research documents")).toBeTruthy();
    expect(screen.getByLabelText("Research stage")).toBeTruthy();
    fireEvent.change(screen.getByLabelText("Defense type"), { target: { value: "research" } });
    expect(screen.queryByLabelText("Project source files or ZIP")).toBeNull();
  });

  it("lists extracted documents and page counts in the lobby", () => {
    const state: RoomState = { ...baseState, defense_type: "research", accepted_files: [
      { name: "paper.pdf", kind: "research_pdf", detail: "2 pages" },
    ] };
    render(<ControlsPanel {...defaultProps} roomState={state} />);
    expect(screen.getByText(/paper.pdf · 2 pages/)).toBeTruthy();
  });

  it("host sees Start defense button in lobby phase", () => {
    render(<ControlsPanel {...defaultProps} roomState={baseState} />);
    expect(screen.getByRole("button", { name: /start defense/i })).toBeTruthy();
  });

  it("non-host does not see Start defense button", () => {
    const state: RoomState = { ...baseState, self_is_host: false };
    render(<ControlsPanel {...defaultProps} roomState={state} />);
    expect(screen.queryByRole("button", { name: /start defense/i })).toBeNull();
  });

  it("keeps answer entry out of the Controls drawer", () => {
    const state: RoomState = {
      ...baseState,
      phase: "question",
      turns: [{ panelist: "Technical Architect", question: "Why?", filename: "app.py", evidence_line: 1, evidence_text: "x", answer: null, answered_by: null }],
    };
    render(<ControlsPanel {...defaultProps} roomState={state} />);
    expect(screen.queryByRole("textbox", { name: /your answer/i })).toBeNull();
  });

  it("host sees Retry question button in retry phase", () => {
    const state: RoomState = { ...baseState, phase: "retry" };
    render(<ControlsPanel {...defaultProps} roomState={state} />);
    expect(screen.getByRole("button", { name: /retry question/i })).toBeTruthy();
  });

  it("host sees Retry coaching report when complete and feedback failed", () => {
    const state: RoomState = {
      ...baseState,
      phase: "complete",
      feedback_status: "failed",
    };
    render(<ControlsPanel {...defaultProps} roomState={state} />);
    expect(screen.getByRole("button", { name: /retry coaching report/i })).toBeTruthy();
  });

  it("host does NOT see Retry coaching report when feedback is ready", () => {
    const state: RoomState = {
      ...baseState,
      phase: "complete",
      feedback_status: "ready",
    };
    render(<ControlsPanel {...defaultProps} roomState={state} />);
    expect(screen.queryByRole("button", { name: /retry coaching report/i })).toBeNull();
  });

  it("host does NOT see Retry coaching report when not complete", () => {
    const state: RoomState = { ...baseState, phase: "lobby" };
    render(<ControlsPanel {...defaultProps} roomState={state} />);
    expect(screen.queryByRole("button", { name: /retry coaching report/i })).toBeNull();
  });
});

describe("Host account controls", () => {
  const signedIn = {authenticated:true,google_enabled:true,user:{id:"account-id",name:"Configured host",email:"private@example.test"},csrf_token:"csrf",free_access:false,test_credits:10};
  it("prefills an editable account name without replacing edits",()=>{
    const view=render(<ControlsPanel {...defaultProps} account={signedIn} roomState={null} connected={false}/>);
    const input=screen.getByLabelText("Your name") as HTMLInputElement;
    expect(input.value).toBe("Configured host");fireEvent.change(input,{target:{value:"My team name"}});
    view.rerender(<ControlsPanel {...defaultProps} account={{...signedIn,user:{...signedIn.user,name:"Changed account name"}}} roomState={null} connected={false}/>);
    expect(input.value).toBe("My team name");expect(screen.queryByText("private@example.test")).toBeNull();
  });
  it("keeps guest joining available when host login is unavailable",()=>{
    render(<ControlsPanel {...defaultProps} account={{authenticated:false,google_enabled:false}} roomState={null} connected={false}/>);
    expect((screen.getByRole("button",{name:"Create defense room"}) as HTMLButtonElement).disabled).toBe(true);
    fireEvent.click(screen.getByRole("tab",{name:"Join room"}));expect((screen.getByRole("button",{name:"Join team"}) as HTMLButtonElement).disabled).toBe(false);
  });
  it("includes CSRF when creating an account-owned room",async()=>{
    const requests=mockRoomRequests();
    const onUseRoom=vi.fn();render(<ControlsPanel {...defaultProps} account={signedIn} roomState={null} connected={false} onUseRoom={onUseRoom}/>);
    fireEvent.submit(document.querySelector("#create-form")!);
    await act(async()=>{
      requests[0].status=201; requests[0].responseText=JSON.stringify({room_code:"ROOM",player_token:"token"});
      requests[0].dispatchEvent(new Event("load"));
    });
    await waitFor(()=>expect(onUseRoom).toHaveBeenCalledWith("ROOM","token",true));
    expect(requests[0].open).toHaveBeenCalledWith("POST","/api/rooms");
    expect(requests[0].setRequestHeader).toHaveBeenCalledWith("X-CSRF-Token","csrf");
    expect(requests[0].send).toHaveBeenCalledWith(expect.any(FormData));
  });
  it("requires a second explicit click for a paid restart",()=>{
    const onSendEvent=vi.fn(()=>true);render(<ControlsPanel {...defaultProps} account={signedIn} roomState={{...baseState,phase:"complete"}} onSendEvent={onSendEvent}/>);
    fireEvent.click(screen.getByRole("button",{name:"Restart defense"}));expect(onSendEvent).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button",{name:"Confirm restart · 10 test credits"}));expect(onSendEvent).toHaveBeenCalledWith({type:"restart",confirm_cost:true});
  });
});

it("uses live credits for paid starts and exposes unavailable-service recovery",()=>{
 const onSendEvent=vi.fn(()=>true);
 const account={authenticated:true,google_enabled:true,payment_mode:"live" as const,live_credits:10,test_credits:999};
 const props={...defaultProps,account,onSendEvent};
 const view=render(<ControlsPanel {...props} roomState={{...baseState,phase:"lobby"}}/>);
 fireEvent.click(screen.getByRole("button",{name:"Start defense · 10 credits"}));
 expect(onSendEvent).toHaveBeenCalledWith({type:"start",confirm_cost:true});
 view.rerender(<ControlsPanel {...props} account={{...account,live_credits:0}} roomState={{...baseState,phase:"retry"}}/>);
 expect(screen.getByRole("button",{name:"End unavailable defense · return credits"})).toBeTruthy();
 expect(screen.getByRole("button",{name:"Restart defense"})).toBeDisabled();
});

it("explains a paid pause while allowing voucher starts when the service is available",()=>{
 const account={authenticated:true,google_enabled:true,payment_mode:"live" as const,live_credits:10,paid_starts_enabled:false,ai_service_available:true};
 const props={...defaultProps,account,roomState:{...baseState,phase:"lobby" as const}};
 const view=render(<ControlsPanel {...props}/>);
 expect(screen.getByRole("button",{name:"Start defense · 10 credits"})).toBeDisabled();
 expect(screen.getByText(/Paid starts are temporarily paused/)).toBeTruthy();
 view.rerender(<ControlsPanel {...props} account={{...account,free_access:true}}/>);
 expect(screen.getByRole("button",{name:"Start defense · free access"})).not.toBeDisabled();
 expect(screen.queryByText(/Paid starts are temporarily paused/)).toBeNull();
});

it("explains service unavailability and blocks new voucher or paid runs",()=>{
 const account={authenticated:true,google_enabled:true,payment_mode:"live" as const,live_credits:10,paid_starts_enabled:true,ai_service_available:false};
 const props={...defaultProps,account,roomState:{...baseState,phase:"lobby" as const}};
 const view=render(<ControlsPanel {...props}/>);
 expect(screen.getByRole("button",{name:"Start defense · 10 credits"})).toBeDisabled();
 expect(screen.getByText(/defense service is temporarily unavailable/)).toBeTruthy();
 view.rerender(<ControlsPanel {...props} account={{...account,free_access:true}}/>);
 expect(screen.getByRole("button",{name:"Start defense · free access"})).toBeDisabled();
});

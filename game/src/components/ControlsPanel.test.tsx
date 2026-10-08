import { describe, it, expect, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
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
    const fetcher=vi.fn(async()=>({ok:true,json:async()=>({room_code:"ROOM",player_token:"token"})}));vi.stubGlobal("fetch",fetcher);
    const onUseRoom=vi.fn();render(<ControlsPanel {...defaultProps} account={signedIn} roomState={null} connected={false} onUseRoom={onUseRoom}/>);
    fireEvent.submit(document.querySelector("#create-form")!);
    await waitFor(()=>expect(onUseRoom).toHaveBeenCalledWith("ROOM","token",true));
    expect(fetcher.mock.calls[0]).toEqual(["/api/rooms",expect.objectContaining({headers:{"X-CSRF-Token":"csrf"},body:expect.any(FormData)})]);vi.unstubAllGlobals();
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

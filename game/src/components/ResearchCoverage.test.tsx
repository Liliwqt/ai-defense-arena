import { describe, it, expect, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { ControlsPanel } from "./ControlsPanel";
import { HUD } from "./HUD";
import { QuestionCard } from "./QuestionCard";
import { TranscriptPanel } from "./TranscriptPanel";
import { PanelistSeats } from "./FlatRoom";
import { buildDefenseSummary } from "../lib/buildDefenseSummary";
import { researchPlanPreview } from "../researchPlanPreview";
import type { RoomState, Turn } from "../types";
const turn: Turn = {panelist:"Critical Judge", question:"Which evidence supports the planned comparison?", filename:"study.pdf", evidence_line:2,
  evidence_text:"A two-week pilot will compare waiting times.", evidence_location:"Page 2 · extracted line 2", evidence_kind:"research_pdf",
  answer:null, answered_by:null, topic_id:"topic-1"};
const state: RoomState = {room_code:"OFFLINE", self_seat:0, self_is_host:true, phase:"question",players:[],
  turns:Array.from({length:11},(_,i)=>({...turn, answer:i<10 ? "We will compare wait times.":null})), active_panelist:"Critical Judge",error:null,revision:1,
  files:["study.pdf"], defense_type:"research",research_plan:researchPlanPreview,question_budget:24,current_topic:"topic-1",
  coverage:Object.fromEntries(researchPlanPreview.topics.map((t,i)=>[t.id,{status:i<3 ? "addressed":"pending",turns:i<3?[i]:[],reason:""}])),
  feedback_status:"none",feedback:null};
const controls = { account: { authenticated: true, google_enabled: true, free_access: true },roomState:state,connected:true,previewMode:false,onUseRoom:vi.fn(),onLeaveRoom:vi.fn(),onSendEvent:vi.fn(()=>true),onCloseDrawer:vi.fn(),showMessage:vi.fn()};
describe("Research coverage room",()=>{
 it("shows question numbers beyond eight and the complete topic",()=>{
   render(<HUD roomState={state} roomCode="OFFLINE" previewMode={false} onOpenDrawer={vi.fn()}/>);
   expect(screen.getByText(/Question 11 of 24/)).toBeTruthy();
   expect(screen.getByText("3 of 7 topics addressed")).toBeTruthy();
   render(<QuestionCard roomState={state}/>);
   expect(screen.getByText("QUESTION 11 OF 24")).toBeTruthy();
   expect(screen.getByText(/Topic: Purpose and research gap/)).toBeTruthy();
   expect(screen.getByText("Critical Reviewer")).toBeTruthy();
 });
 it("highlights the actual final research reviewer despite the internal role alias",()=>{
   render(<PanelistSeats roomState={state}/>);
   expect(screen.getByLabelText("Critical Reviewer, asking this question").getAttribute("aria-current")).toBe("true");
 });
 it("lets the host end while generating and hides the action from teammates and completed rooms",()=>{
   const {rerender}=render(<ControlsPanel {...controls} roomState={{...state,phase:"generating"}}/>);
   fireEvent.click(screen.getByRole("button",{name:"End defense"}));
   expect(controls.onSendEvent).toHaveBeenCalledWith({type:"end_defense"});
   rerender(<ControlsPanel {...controls} roomState={{...state,self_is_host:false}}/>);
   expect(screen.queryByRole("button",{name:"End defense"})).toBeNull();
   rerender(<ControlsPanel {...controls} roomState={{...state,phase:"complete"}}/>);
   expect(screen.queryByRole("button",{name:"End defense"})).toBeNull();
 });
 it("blocks starting with an edited unconfirmed budget until the server acknowledges it",()=>{
   const ready={...state,phase:"lobby" as const,research_plan_approved:true,research_planning_status:"ready" as const,research_budget_preview:24};
   const {rerender}=render(<ControlsPanel {...controls} roomState={ready}/>);
   fireEvent.change(screen.getByLabelText("Question budget"),{target:{value:"20"}});
   expect((screen.getByRole("button",{name:/Start defense/}) as HTMLButtonElement).disabled).toBe(true);
   fireEvent.click(screen.getByRole("button",{name:"Confirm question budget"}));
   expect((screen.getByRole("button",{name:/Start defense/}) as HTMLButtonElement).disabled).toBe(true);
   rerender(<ControlsPanel {...controls} roomState={{...ready,research_budget_preview:20}}/>);
   expect((screen.getByRole("button",{name:/Start defense/}) as HTMLButtonElement).disabled).toBe(false);
 });
 it("exports coverage gaps, original question references, and distinct early ending",()=>{
   const ended={...state,phase:"complete" as const,completion_reason:"ended by host" as const,turns:[{...turn,ended_early:true}]};
   const summary=buildDefenseSummary(ended);
   expect(summary).toContain("Ending reason: ended by host");
   expect(summary).toContain("Q1. Critical Reviewer");
   expect(summary).not.toContain("Critical Judge");
   expect(summary).toContain("Unresolved topics:");
   expect(summary).toContain("Supporting questions: 1");
   expect(summary).toContain("ended early by host, no answer submitted");
   expect(summary).not.toContain("time expired");
   render(<TranscriptPanel roomState={ended}/>);
   expect(screen.getByText("Ending reason: ended by host")).toBeTruthy();
   expect(screen.getByText("Question 1 · Critical Reviewer")).toBeTruthy();
   expect(screen.getByText(/Ended early by host · no answer/)).toBeTruthy();
 });
});

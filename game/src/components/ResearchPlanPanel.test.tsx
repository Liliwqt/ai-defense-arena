import { describe, it, expect, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { ResearchPlanPanel } from "./ResearchPlanPanel";
import { ControlsPanel } from "./ControlsPanel";
import { researchPlanPreview } from "../researchPlanPreview";
import type { RoomState } from "../types";

const state: RoomState = {
  room_code: "OFFLINE", self_seat: 0, self_is_host: true, phase: "lobby", players: [], turns: [],
  active_panelist: null, error: null, revision: 1, files: ["paper.pdf"], defense_type: "research",
  feedback_status: "none", feedback: null, research_planning_status: "ready", research_plan: researchPlanPreview,
  research_budget_preview: 14, research_plan_approved: false,
};

function props() { return { roomState: state, connected: true, previewMode: false, onSendEvent: vi.fn(() => true) }; }

describe("ResearchPlanPanel", () => {
  it("shows ordered topics, role names, uncertainties and exact citations", () => {
    render(<ResearchPlanPanel {...props()} />);
    expect(screen.getByText("7 proposed topics")).toBeTruthy();
    expect(screen.getAllByText("Critical Reviewer")).toHaveLength(2);
    expect(screen.getByText(researchPlanPreview.uncertainties[0])).toBeTruthy();
    expect(screen.getByText(researchPlanPreview.topics[1].gaps[0])).toBeTruthy();
    fireEvent.click(screen.getAllByText("Source references (1)")[0]);
    expect(screen.getByText(researchPlanPreview.topics[0].references[0].evidence_text)).toBeTruthy();
    expect(document.querySelectorAll("[id^='plan-topic-']")).toHaveLength(7);
    expect(screen.getByText(/This budget is not a price or credit quote/)).toBeTruthy();
  });

  it("sends the editable budget with the current plan id and warns about missed topics", () => {
    const p = props();
    render(<ResearchPlanPanel {...p} />);
    fireEvent.change(screen.getByLabelText("Question budget"), { target: { value: "4" } });
    expect(screen.getByText(/smaller than the topic count/)).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Confirm question budget" }));
    expect(p.onSendEvent).toHaveBeenCalledWith({ type: "approve_research_plan", plan_id: researchPlanPreview.id, question_budget: 4 });
  });

  it("does not claim confirmation until a server snapshot acknowledges it", () => {
    const p = props();
    const { rerender } = render(<ResearchPlanPanel {...p} />);
    fireEvent.click(screen.getByRole("button", { name: "Confirm question budget" }));
    expect(screen.queryByText(/Maximum confirmed:/)).toBeNull();
    rerender(<ResearchPlanPanel {...p} roomState={{ ...state, research_plan_approved: true }} />);
    expect(screen.getByText(/Maximum confirmed: 14/)).toBeTruthy();
    fireEvent.change(screen.getByLabelText("Question budget"), { target: { value: "20" } });
    expect(screen.queryByText(/Maximum confirmed:/)).toBeNull();
  });

  it("keeps teammate access read-only", () => {
    render(<ResearchPlanPanel {...props()} roomState={{ ...state, self_is_host: false, research_plan_approved: true }} />);
    expect(screen.getByText("Purpose and research gap")).toBeTruthy();
    expect(screen.queryByRole("spinbutton")).toBeNull();
    expect(screen.queryByRole("button", { name: "Confirm question budget" })).toBeNull();
    expect(screen.getByText(/confirmed by host/)).toBeTruthy();
  });

  it("makes disconnected and visual-preview host controls read-only", () => {
    const p = props();
    const { rerender } = render(<ResearchPlanPanel {...p} connected={false} />);
    expect((screen.getByRole("button", { name: "Confirm question budget" }) as HTMLButtonElement).disabled).toBe(true);
    expect(screen.queryByRole("button", { name: "Prepare map again" })).toBeNull();
    rerender(<ResearchPlanPanel {...p} previewMode />);
    expect((screen.getByRole("spinbutton") as HTMLInputElement).disabled).toBe(true);
  });

  it("resets a draft when the host receives a different map", () => {
    const p = props();
    const { rerender } = render(<ResearchPlanPanel {...p} />);
    fireEvent.change(screen.getByLabelText("Question budget"), { target: { value: "22" } });
    rerender(<ResearchPlanPanel {...p} roomState={{ ...state, research_plan: { ...researchPlanPreview, id: "new-map", suggested_budget: 18 }, research_budget_preview: 18 }} />);
    expect((screen.getByRole("spinbutton") as HTMLInputElement).value).toBe("18");
  });

  it("prepares and retries independently of starting the defense", () => {
    const p = props();
    const { rerender } = render(<ResearchPlanPanel {...p} roomState={{ ...state, research_plan: null, research_planning_status: "none" }} />);
    fireEvent.click(screen.getByRole("button", { name: "Prepare defense" }));
    expect(p.onSendEvent).toHaveBeenCalledWith({ type: "prepare_research_plan" });
    rerender(<ResearchPlanPanel {...p} roomState={{ ...state, research_plan: null, research_planning_status: "failed", research_plan_error: "Invalid citation." }} />);
    expect(screen.getByRole("alert").textContent).toContain("Your uploads are retained");
    fireEvent.click(screen.getByRole("button", { name: "Retry research map" }));
    expect(p.onSendEvent).toHaveBeenCalledWith({ type: "retry_research_plan" });
    expect(p.onSendEvent).not.toHaveBeenCalledWith({ type: "start" });
  });

  it("requires confirmation before sending the research start budget", () => {
    const p = props();
    const controls = { ...p, onUseRoom: vi.fn(), onLeaveRoom: vi.fn(), onCloseDrawer: vi.fn(), showMessage: vi.fn() };
    const { rerender } = render(<ControlsPanel {...controls} roomState={{ ...state, research_plan: null, research_planning_status: "planning" }} />);
    expect((screen.getByRole("button", { name: "Start defense" }) as HTMLButtonElement).disabled).toBe(true);
    expect(screen.getByRole("status").textContent).toContain("Mapping");
    rerender(<ControlsPanel {...controls} roomState={{...state, research_plan_approved: true}} />);
    fireEvent.click(screen.getByRole("button", { name: "Start defense" }));
    expect(p.onSendEvent).toHaveBeenCalledWith({ type: "start", plan_id: researchPlanPreview.id, question_budget: 14 });
  });

  it("preserves indentation and scrollable code references in mixed topics", () => {
    const citation = { filename: "queue.py", evidence_line: 5, evidence_text: "    save_reservation(student_id)", evidence_location: "Line 5", evidence_kind: "source" };
    const plan = { ...researchPlanPreview, topics: [{ ...researchPlanPreview.topics[0], references: [citation] }] };
    render(<ResearchPlanPanel {...props()} roomState={{ ...state, defense_type: "mixed", research_plan: plan }} />);
    expect(screen.getByRole("group", { name: "Exact cited source at queue.py, Line 5" }).querySelector("code")?.textContent).toBe(citation.evidence_text);
    expect(document.querySelector(".plan-source pre")?.getAttribute("tabindex")).toBe("0");
  });
});

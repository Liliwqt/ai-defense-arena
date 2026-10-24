import { act, render, screen, within } from "@testing-library/react";
import { beforeEach, afterEach, expect, it, vi } from "vitest";
import { App } from "./App";
import { useAccount } from "./hooks/useAccount";
import { useRoomSocket, type RoomSocketState } from "./hooks/useRoomSocket";
import { researchPlanPreview } from "./researchPlanPreview";
import type { RoomState } from "./types";

vi.mock("./hooks/useAccount", () => ({ useAccount: vi.fn() }));
vi.mock("./hooks/useRoomSocket", () => ({ useRoomSocket: vi.fn() }));
let socket: RoomSocketState;
function mappingRoom(extra: Partial<RoomState> = {}): RoomState {
  return {
    room_code: "MAP1", defense_view_id: "preparation-one", phase: "lobby", defense_type: "research",
    self_seat: 0, self_is_host: true, revision: 1, error: null, server_now_ms: 5000,
    players: [{ seat: 0, name: "Alex", online: true, is_host: true }], turns: [], active_panelist: null,
    files: ["paper.pdf"], accepted_files: [{ name: "paper.pdf", kind: "research_pdf", detail: "7 pages" }],
    feedback_status: "none", feedback: null, research_planning_status: "planning", research_plan: null,
    research_plan_progress: { stage: "mapping", topics: [researchPlanPreview.topics[0]] }, plan_attempts_left: 2,
    operation: { id: "mapping:1", kind: "mapping", stage: "mapping", started_at_ms: 1000, attempt: 1, retrying: false },
    panelist_activity: { operation_id: "mapping:1", view_id: "preparation-one", reviewer: null, context: "paper.pdf" },
    ...extra,
  };
}
beforeEach(() => {
  sessionStorage.clear(); window.history.replaceState(null, "", "/#/prepare");
  vi.mocked(useAccount).mockReturnValue({ account: { authenticated: true, google_enabled: true, free_access: true }, error: "", refresh: vi.fn(async () => {}) });
  socket = { roomState: mappingRoom(), roomCode: "MAP1", playerToken: "fixture", connected: true, knownHost: true,
    waitingForAnswerAck: false, actionError: null, actionErrorReason: null, sendEvent: vi.fn(() => true), useRoom: vi.fn(), leaveRoom: vi.fn() };
  vi.mocked(useRoomSocket).mockImplementation(() => socket);
});
afterEach(() => { vi.clearAllMocks(); vi.useRealTimers(); });

it("shows accepted-upload activity beside provisional progress and removes it when the map is ready", () => {
  const app = render(<App />);
  const activity = screen.getByRole("region", { name: "Panelist activity" });
  expect(activity.querySelector("mark")).toHaveTextContent("paper.pdf");
  expect(activity).toHaveTextContent("Mapping your paper…");
  expect(activity).toHaveTextContent("4s");
  expect(activity).not.toHaveTextContent(researchPlanPreview.topics[0].title);
  expect(screen.getByRole("list", { name: "Draft research topics" })).toHaveTextContent(researchPlanPreview.topics[0].title);
  expect(screen.queryByText("Checking source references…")).toBeNull();
  socket.roomState = mappingRoom({ operation: { ...mappingRoom().operation!, stage: "validating" },
    research_plan_progress: { stage: "validating", topics: [researchPlanPreview.topics[0]] } });
  app.rerender(<App />);
  expect(within(screen.getByRole("region", { name: "Panelist activity" })).getByText("Checking source references…")).toBeVisible();
  socket.roomState = mappingRoom({ research_planning_status: "ready", research_plan: researchPlanPreview, research_plan_progress: null,
    research_budget_preview: 14, research_plan_approved: false, operation: null, panelist_activity: null });
  app.rerender(<App />);
  expect(screen.queryByRole("region", { name: "Panelist activity" })).toBeNull();
  expect(screen.queryByRole("progressbar", { name: "Paper mapping progress" })).toBeNull();
  expect(screen.getByRole("region", { name: "Research profile" })).toBeVisible();
  expect(screen.getByRole("button", { name: "Confirm profile and budget" })).toBeDisabled();
  expect(socket.sendEvent).not.toHaveBeenCalled();
});

it("restores Free mixed guest activity through navigation without remapping or resetting elapsed time", () => {
  socket.roomState = mappingRoom({ practice_tier: "free", defense_type: "mixed", self_is_host: false, self_seat: 1 });
  const app = render(<App />);
  expect(screen.getByRole("region", { name: "Panelist activity" })).toHaveTextContent("paper.pdf");
  act(() => {
    window.history.pushState(null, "", "/#/account");
    window.dispatchEvent(new PopStateEvent("popstate"));
  });
  expect(screen.queryByRole("region", { name: "Panelist activity" })).toBeNull();
  socket.roomState = { ...socket.roomState!, server_now_ms: 31000 };
  app.rerender(<App />);
  act(() => {
    window.history.pushState(null, "", "/#/prepare");
    window.dispatchEvent(new PopStateEvent("popstate"));
  });
  expect(screen.getByRole("region", { name: "Panelist activity" })).toHaveTextContent("30s");
  expect(screen.queryByRole("button", { name: "Map paper" })).toBeNull();
  expect(socket.sendEvent).not.toHaveBeenCalled();
});

it("clears activity on failed remapping and uses only the new admitted operation context", () => {
  socket.roomState = mappingRoom({ research_plan: researchPlanPreview });
  const app = render(<App />);
  socket.roomState = mappingRoom({ research_planning_status: "failed", research_plan: researchPlanPreview,
    research_plan_progress: null, operation: null, panelist_activity: null, research_plan_error: "Mapping unavailable" });
  app.rerender(<App />);
  expect(screen.queryByRole("region", { name: "Panelist activity" })).toBeNull();
  expect(screen.getByRole("alert")).toHaveTextContent("Your uploads are retained");
  expect(screen.getByRole("region", { name: "Research profile" })).toBeVisible();
  socket.roomState = mappingRoom({ operation: { ...mappingRoom().operation!, id: "mapping:2" } });
  app.rerender(<App />);
  const activity = screen.getByRole("region", { name: "Panelist activity" });
  expect(activity.querySelector("mark")).toBeNull();
  expect(activity).toHaveTextContent("Mapping your paper…");
  socket.roomState = mappingRoom({ research_planning_status: "none", operation: null, panelist_activity: null });
  app.rerender(<App />);
  expect(screen.queryByRole("region", { name: "Panelist activity" })).toBeNull();
  expect(socket.sendEvent).not.toHaveBeenCalled();
});

it("handles legacy snapshots and treats unusual accepted names as text without a leftover after fast completion", () => {
  socket.roomState = mappingRoom({ panelist_activity: undefined });
  const app = render(<App />);
  expect(screen.getByRole("region", { name: "Panelist activity" }).querySelector("mark")).toBeNull();
  const filename = '<img src=x onerror="alert(1)">研究.md';
  socket.roomState = mappingRoom({ panelist_activity: { ...mappingRoom().panelist_activity!, context: filename } });
  app.rerender(<App />);
  const activity = screen.getByRole("region", { name: "Panelist activity" });
  expect(activity.querySelector("mark")).toHaveTextContent(filename);
  expect(activity.querySelector("img")).toBeNull();
  socket.roomState = mappingRoom({ research_planning_status: "ready", research_plan: researchPlanPreview });
  app.rerender(<App />);
  expect(screen.queryByRole("region", { name: "Panelist activity" })).toBeNull();
  expect(screen.queryByText(filename)).toBeNull();
  expect(socket.sendEvent).not.toHaveBeenCalled();
});

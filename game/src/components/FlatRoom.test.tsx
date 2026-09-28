import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { DefenderSeats, PanelistSeats, type PresenterMoment } from "./FlatRoom";
import type { RoomState } from "../types";

const state: RoomState = {
  room_code: "ROOM", self_seat: 0, self_is_host: true, phase: "question",
  players: [
    { seat: 0, name: "Alex", online: true, is_host: true },
    { seat: 1, name: "Sam", online: true, is_host: false },
    { seat: 2, name: "Lee", online: false, is_host: false },
  ],
  turns: [{ panelist: "Technical Architect", question: "Why?", filename: "code.py",
    evidence_line: 1, evidence_text: "x = 1", answer: null, answered_by: null }],
  active_panelist: "Technical Architect", error: null, revision: 1,
  files: ["code.py"], feedback_status: "none", feedback: null, selected_seat: 1,
};

function RoomSeats({ roomState, presenterMoment }: { roomState: RoomState | null; presenterMoment: PresenterMoment | null }) {
  return <><PanelistSeats roomState={roomState} /><DefenderSeats roomState={roomState} presenterMoment={presenterMoment} /></>;
}

describe("FlatRoom", () => {
  it("shows four ordered panelists and four defender seats with text states", () => {
    const { container } = render(<RoomSeats roomState={state} presenterMoment={null} />);
    const panelists = Array.from(container.querySelectorAll(".panelist-seat strong"), element => element.textContent);
    expect(panelists).toEqual(["Technical Architect", "Security Reviewer", "Product Judge", "Critical Judge"]);
    expect(container.querySelectorAll(".defender-seat")).toHaveLength(4);
    expect(screen.getByLabelText(/Defender seat 2: Sam, online, chosen to answer/i)).toBeTruthy();
    expect(screen.getByText("Offline")).toBeTruthy();
    expect(screen.getByText("Available")).toBeTruthy();
  });

  it("uses research roles and never labels open seats as the current user", () => {
    const { container } = render(<RoomSeats roomState={{ ...state, defense_type: "research", players: [], self_seat: null,
      active_panelist: "Methodology Reviewer", selected_seat: null }} presenterMoment={null} />);
    const panelists = Array.from(container.querySelectorAll(".panelist-seat strong"), element => element.textContent);
    expect(panelists).toEqual(["Methodology Reviewer", "Ethics Reviewer", "Impact Reviewer", "Critical Reviewer"]);
    expect(container.textContent).not.toContain("(you)");
  });

  it("shows votes during selection and the accepted presenter's seat afterward", () => {
    const voting: RoomState = { ...state, phase: "voting", selected_seat: null, vote_counts: { "0": 1, "1": 2 } };
    const view = render(<RoomSeats roomState={voting} presenterMoment={null} />);
    expect(screen.getByLabelText(/Defender seat 2: Sam, online, 2 votes/i)).toBeTruthy();
    view.rerender(<RoomSeats roomState={{ ...state, phase: "generating", selected_seat: null }}
      presenterMoment={{ seat: 1, sequence: 1, reducedMotion: true }} />);
    expect(screen.getByText("Answered")).toBeTruthy();
  });
});

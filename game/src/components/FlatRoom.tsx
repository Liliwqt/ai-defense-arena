import type { RoomState } from "../types";

import { deriveRoomPresentation, type RoomPresentation } from "../lib/roomPresentation";

export interface PresenterMoment {
  seat: number;
  sequence: number;
  reducedMotion: boolean;
}

export function PanelistSeats({ roomState, presentation = deriveRoomPresentation(roomState) }: { roomState: RoomState | null; presentation?: RoomPresentation }) {
  return (
    <section className="seat-section panelist-section" aria-label="Panelists">
      <div className="seat-section-heading"><span>THE PANEL</span><span>Four perspectives</span></div>
      <div className="seat-row panelist-row">
        {presentation.panelists.map(({ name, active, label, accessibleLabel }, index) => (
          <div key={name} className={`seat-card panelist-seat${active ? " is-active" : ""}`}
            aria-label={accessibleLabel} aria-current={active ? "true" : undefined}>
            <span className="seat-index" aria-hidden="true">0{index + 1}</span>
            <strong title={name}>{name}</strong>
            <span className="seat-state">{label}</span>
          </div>
        ))}
      </div>
    </section>
  );
}

export function DefenderSeats({ roomState, presenterMoment, presentation = deriveRoomPresentation(roomState) }: {
  presentation?: RoomPresentation;
  roomState: RoomState | null;
  presenterMoment: PresenterMoment | null;
}) {
  const choosing = presentation.voting;
  return (
    <section className="seat-section defender-section" aria-label="Defenders">
      <div className="seat-section-heading"><span>YOUR TEAM</span><span>{choosing ? "Choose a speaker below" : "Four defender seats"}</span></div>
      <div className="seat-row defender-row">
        {presentation.defenders.map(({ seat, name, self, online, selected, label, accessibleLabel }) => {
          const presenting = presenterMoment?.seat === seat;
          return <div key={seat} className={`seat-card defender-seat${selected || presenting ? " is-active" : ""}${!online ? " is-muted" : ""}`}
            aria-label={accessibleLabel}>
            <span className="seat-index" aria-hidden="true">0{seat + 1}</span>
            <strong title={name}>{name}{self ? " (you)" : ""}</strong>
            <span className="seat-state">{!selected && presenting ? "Answered" : label}</span>
          </div>;
        })}
      </div>
    </section>
  );
}

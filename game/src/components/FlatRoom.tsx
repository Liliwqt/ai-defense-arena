import type { RoomState } from "../types";

export interface PresenterMoment {
  seat: number;
  sequence: number;
  reducedMotion: boolean;
}

const CODE_PANELISTS = ["Technical Architect", "Security Reviewer", "Product Judge", "Critical Judge"];
const RESEARCH_PANELISTS = ["Methodology Reviewer", "Ethics Reviewer", "Impact Reviewer", "Critical Reviewer"];

export function PanelistSeats({ roomState }: { roomState: RoomState | null }) {
  const panelists = roomState?.defense_type && roomState.defense_type !== "code"
    ? RESEARCH_PANELISTS : CODE_PANELISTS;
  const speaker = panelists === RESEARCH_PANELISTS && roomState?.active_panelist === "Critical Judge" ? "Critical Reviewer" : roomState?.active_panelist;
  const speaking = roomState?.phase === "voting" || roomState?.phase === "probe" || roomState?.phase === "question"
    || roomState?.phase === "interpreting" || roomState?.phase === "interpretation_retry";
  return (
    <section className="seat-section panelist-section" aria-label="Panelists">
      <div className="seat-section-heading"><span>THE PANEL</span><span>Four perspectives</span></div>
      <div className="seat-row panelist-row">
        {panelists.map((name, index) => {
          const active = speaking && speaker === name;
          return <div key={name} className={`seat-card panelist-seat${active ? " is-active" : ""}`}
            aria-label={`${name}${active ? ", asking this question" : ""}`} aria-current={active ? "true" : undefined}>
            <span className="seat-index" aria-hidden="true">0{index + 1}</span>
            <strong title={name}>{name}</strong>
            <span className="seat-state">{active ? "Asking" : "Panelist"}</span>
          </div>;
        })}
      </div>
    </section>
  );
}

export function DefenderSeats({ roomState, presenterMoment }: {
  roomState: RoomState | null;
  presenterMoment: PresenterMoment | null;
}) {
  const choosing = roomState?.phase === "voting";
  const selected = roomState?.selected_seat;
  return (
    <section className="seat-section defender-section" aria-label="Defenders">
      <div className="seat-section-heading"><span>YOUR TEAM</span><span>{choosing ? "Choose a speaker below" : "Four defender seats"}</span></div>
      <div className="seat-row defender-row">
        {Array.from({ length: 4 }, (_, seat) => {
          const player = roomState?.players.find((candidate) => candidate.seat === seat);
          const isSelected = selected === seat && ["question", "probe", "interpreting", "interpretation_retry"].includes(roomState?.phase ?? "");
          const presenting = presenterMoment?.seat === seat;
          const votes = roomState?.vote_counts?.[String(seat)] ?? 0;
          const label = player ? `${player.name}${player.is_host ? ", host" : ""}, ${player.online ? "online" : "offline"}` : "Open seat";
          const state = isSelected ? "Answering" : presenting ? "Answered" : choosing && player?.online ? `${votes} ${votes === 1 ? "vote" : "votes"}` : player?.online ? "Online" : player ? "Offline" : "Available";
          return <div key={seat} className={`seat-card defender-seat${isSelected || presenting ? " is-active" : ""}${!player?.online ? " is-muted" : ""}`}
            aria-label={`Defender seat ${seat + 1}: ${label}${isSelected ? ", chosen to answer" : ""}${choosing && player?.online ? `, ${votes} votes` : ""}`}>
            <span className="seat-index" aria-hidden="true">0{seat + 1}</span>
            <strong title={player?.name ?? "Open seat"}>{player?.name ?? "Open seat"}{player && player.seat === roomState?.self_seat ? " (you)" : ""}</strong>
            <span className="seat-state">{state}</span>
          </div>;
        })}
      </div>
    </section>
  );
}

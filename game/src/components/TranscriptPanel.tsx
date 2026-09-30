import { CoachingReport } from "./CoachingReport";
import { TurnCard } from "./TurnCard";
import type { RoomState } from "../types";

interface TranscriptPanelProps {
  roomState: RoomState | null;
}

export function TranscriptPanel({ roomState }: TranscriptPanelProps) {
  const turns = roomState?.turns ?? [];
  const answered = turns.filter((t) => t.answer).length;
  const timedOut = turns.filter((t) => t.timed_out).length;
  const feedbackStatus = roomState?.feedback_status ?? "none";
  const hasSomething = turns.length > 0 || feedbackStatus !== "none";

  // Per-defender contribution, built from data already in the snapshot. This is
  // deliberately not a score: it reports coverage (who spoke, how often) rather
  // than judging answer quality, matching the coaching report's no-grade rule.
  const contributions = new Map<number, { name: string; count: number }>();
  for (const turn of turns) {
    const seat = turn.answered_by_seat;
    if (typeof seat !== "number" || !turn.answer) continue;
    const name = turn.answered_by?.trim() || `Seat ${seat + 1}`;
    const entry = contributions.get(seat);
    if (entry) entry.count += 1;
    else contributions.set(seat, { name, count: 1 });
  }
  const roster = contributions.size > 1 ? [...contributions.entries()] : [];

  return (
    <div>
      <div className="transcript-heading">
        <div>
          <p className="transcript-kicker">
            SESSION HISTORY
          </p>
          <h3 className="transcript-title">
            Defense transcript
          </h3>
        </div>
        <span
          id="transcript-count"
          className="transcript-count"
        >
          {answered} answered{timedOut ? ` · ${timedOut} timed out` : ""}
        </span>
      </div>

      {roster.length > 0 && (
        <p className="transcript-coverage">
          Team coverage:{" "}
          {roster
            .sort((a, b) => b[1].count - a[1].count)
            .map(([, entry]) => `${entry.name} answered ${entry.count}`)
            .join(" · ")}
        </p>
      )}

      {!hasSomething && (
        <p className="transcript-empty">
          Questions and team answers will appear here.
        </p>
      )}

      {hasSomething && (
        <div className="transcript-list">
          <CoachingReport
            feedbackStatus={feedbackStatus}
            feedback={roomState?.feedback ?? null}
          />
          {turns.map((turn, index) => (
            <TurnCard key={index} turn={turn} index={index} />
          ))}
        </div>
      )}
    </div>
  );
}

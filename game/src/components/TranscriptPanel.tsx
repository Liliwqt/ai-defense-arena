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

import { CoachingReport } from "./CoachingReport";
import { TurnCard } from "./TurnCard";
import type { RoomState } from "../types";

interface TranscriptPanelProps {
  roomState: RoomState | null;
}

export function TranscriptPanel({ roomState }: TranscriptPanelProps) {
  const turns = roomState?.turns ?? [];
  const answered = turns.filter((t) => t.answer).length;
  const feedbackStatus = roomState?.feedback_status ?? "none";
  const hasSomething = turns.length > 0 || feedbackStatus !== "none";

  return (
    <div>
      <div className="flex items-end justify-between gap-4 mb-4">
        <div>
          <p className="text-[#85acd4] text-[0.68rem] font-black tracking-[0.16em] m-0 mb-1">
            SESSION HISTORY
          </p>
          <h3 className="text-[1.17rem] m-0 text-[#eaf2ff]">
            Defense transcript
          </h3>
        </div>
        <span
          id="transcript-count"
          className="text-[#96bad8] text-[0.78rem] font-[750] whitespace-nowrap"
        >
          {answered} / 4 answered
        </span>
      </div>

      {!hasSomething && (
        <p className="text-[#91a9c2] text-[0.88rem]">
          Questions and team answers will appear here.
        </p>
      )}

      {hasSomething && (
        <div className="grid gap-3">
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

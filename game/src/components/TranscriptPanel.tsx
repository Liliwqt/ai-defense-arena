import { CoachingReport } from "./CoachingReport";
import { deriveRoomPresentation, type RoomPresentation } from "../lib/roomPresentation";
import { TurnCard } from "./TurnCard";
import { buildDefenseSummary, defenseSummaryFileName } from "../lib/buildDefenseSummary";
import { saveDefenseSummary } from "../lib/saveDefenseSummary";
import type { RoomState } from "../types";

interface TranscriptPanelProps {
  presentation?: RoomPresentation;
  roomState: RoomState | null;
  previewMode?: boolean;
}

export function TranscriptPanel({ roomState, previewMode = false, presentation = deriveRoomPresentation(roomState) }: TranscriptPanelProps) {
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

      {roomState?.research_plan && roomState.coverage && <section className="transcript-coverage" aria-label="Research coverage">
        <h4>Research coverage</h4>
        {roomState.completion_reason && <p>Ending reason: {roomState.completion_reason}</p>}
        <p>Addressed means discussion coverage, not proof that the research is correct.</p>
        <ul>{roomState.research_plan.topics.map(topic => <li key={topic.id}>
          <strong>{topic.title}</strong>: {roomState.coverage?.[topic.id]?.status ?? "pending"}
          {roomState.coverage?.[topic.id]?.turns.length ? ` · questions ${roomState.coverage[topic.id].turns.map(i => i + 1).join(", ")}` : ""}
        </li>)}</ul>
      </section>}
      {roster.length > 0 && (
        <p className="transcript-coverage">
          Team coverage:{" "}
          {roster
            .sort((a, b) => b[1].count - a[1].count)
            .map(([, entry]) => `${entry.name} answered ${entry.count}`)
            .join(" · ")}
        </p>
      )}

      {hasSomething && roomState && (
        <div className="transcript-actions">
          <button
            type="button"
            className="export-button"
            disabled={previewMode}
            title={previewMode ? "Preview mode cannot download" : "Save this defense as a text file"}
            onClick={() => {
              saveDefenseSummary(defenseSummaryFileName(roomState), buildDefenseSummary(roomState));
            }}
          >
            Download summary
          </button>
          <p className="export-note">
            Rooms are not saved on the server, so this file is your copy of this defense.
          </p>
        </div>
      )}

      {!hasSomething && (
        <p className="transcript-empty">
          Questions and team answers will appear here.
        </p>
      )}

      {hasSomething && (
        <div className="transcript-list">
          <CoachingReport
            failureGuidance={presentation.guidance}
            feedbackStatus={feedbackStatus}
            feedback={roomState?.feedback ?? null}
          />
          {turns.map((turn, index) => (
            <TurnCard key={index} turn={turn} index={index} research={!!roomState?.defense_type && roomState.defense_type !== "code"} />
          ))}
        </div>
      )}
    </div>
  );
}

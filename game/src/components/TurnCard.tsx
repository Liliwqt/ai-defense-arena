import type { Turn } from "../types";

interface TurnCardProps {
  turn: Turn;
  index: number;
}

export function TurnCard({ turn, index }: TurnCardProps) {
  return (
    <article className="transcript-turn">
      <h3>Question {index + 1} · {turn.panelist || "Panelist"}</h3>
      {turn.lead_in && <p className="transcript-lead-in">{turn.lead_in}</p>}
      <p className="transcript-question">{turn.question || "Question being prepared…"}</p>
      {turn.filename && Number.isInteger(turn.evidence_line) && <p className="transcript-source">
        {turn.filename}, {turn.evidence_location ?? `Line ${turn.evidence_line}`} — {turn.evidence_text ?? ""}
      </p>}
      {turn.clarifications?.map((exchange, exchangeIndex) => <div key={exchangeIndex} className="turn-clarification">
        <p><strong>Clarification request:</strong> {exchange.request}</p>
        <p><strong>{turn.panelist}:</strong> {exchange.reply}</p>
      </div>)}
      {turn.timed_out && <p className="turn-timeout">Time expired · question passed to the panel.</p>}
      {turn.answer && <p className="transcript-answer">
        <strong>Team answer{turn.answered_by ? ` · ${turn.answered_by}` : ""}:</strong> {turn.answer}
      </p>}
    </article>
  );
}

import type { RoomState } from "../types";

interface QuestionCardProps {
  roomState: RoomState | null;
  onAnswer?: () => void;
  canAnswer?: boolean;
}

function deriveContent(state: RoomState | null) {
  const phase = state?.phase ?? "none";
  const answered = (state?.turns ?? []).filter((turn) => turn.answer).length;
  const turns = state?.turns ?? [];
  let current = null as (typeof turns)[number] | null;
  let currentIndex = -1;
  for (let index = turns.length - 1; index >= 0; index--) {
    if (turns[index].question && !turns[index].answer) {
      current = turns[index];
      currentIndex = index;
      break;
    }
  }

  if (phase === "question" && current) {
    return {
      name: current.panelist,
      question: current.question,
      number: `QUESTION ${currentIndex + 1}`,
      filename: current.filename,
      line: current.evidence_line,
      evidence: current.evidence_text,
    };
  }
  if (phase === "generating") {
    return { name: state?.active_panelist ?? "The panel", question: "Preparing the next question…", number: `QUESTION ${answered + 1}` };
  }
  if (phase === "retry") {
    return { name: "Question paused", question: `${state?.error ?? "The next question could not be generated."} The host can retry from Controls.`, number: `QUESTION ${answered + 1}` };
  }
  if (phase === "complete") {
    const feedback = state?.feedback_status;
    return {
      name: feedback === "generating" ? "Preparing coaching report" : "Defense complete",
      question: feedback === "generating"
        ? "The team has answered the panel. Your coaching report is being prepared."
        : feedback === "failed"
          ? `${state?.error ?? "The coaching report could not be generated."} The host can retry from Controls.`
          : "Open Transcript to review your answers and coaching report.",
      number: `${answered} ANSWERED`,
    };
  }
  if (phase === "lobby") {
    return { name: "Your team is gathering", question: "The host starts the defense when everyone is ready.", number: "READY" };
  }
  return { name: "Your defense begins here", question: "Create or join a room to begin your defense.", number: "READY" };
}

export function QuestionCard({ roomState, onAnswer, canAnswer = false }: QuestionCardProps) {
  const content = deriveContent(roomState);
  return (
    <section id="question-card" aria-labelledby="panelist-name" tabIndex={0}>
      <div className="question-heading">
        <div>
          <p className="question-kicker">THE PANEL ASKS</p>
          <h2 id="panelist-name">{content.name}</h2>
        </div>
        <span className="question-number">{content.number}</span>
      </div>
      <p id="question-text" aria-live="polite">{content.question}</p>
      {content.filename !== undefined && (
        <div id="source-block" role="group" aria-label="Exact cited source line">
          <div className="source-heading">
            <span className="source-filename" title={content.filename}>{content.filename}</span>
            <span className="source-line-label">Line {content.line}</span>
          </div>
          <div className="source-code-scroll" tabIndex={0} aria-label={`Source code at ${content.filename}, line ${content.line}`}>
            <span className="source-line-number" aria-hidden="true">{content.line}</span>
            <pre><code>{content.evidence}</code></pre>
          </div>
        </div>
      )}
      {roomState?.phase === "question" && onAnswer && (
        <div className="question-footer">
          <p>Any teammate can answer; the first valid submission counts.</p>
          <button type="button" onClick={onAnswer} disabled={!canAnswer}>
            Answer question <span aria-hidden="true">›</span>
          </button>
        </div>
      )}
    </section>
  );
}

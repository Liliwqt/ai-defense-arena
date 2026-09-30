import { PageCitation } from "./PageCitation";
import { isResearchCitation } from "../lib/citation";
import type { RoomState, Turn } from "../types";

interface QuestionCardProps {
  roomState: RoomState | null;
}

interface CardContent {
  name: string;
  question: string;
  number: string;
  leadIn?: string;
  filename?: string;
  line?: number;
  evidence?: string;
  location?: string;
  kind?: string;
  reviewStatus?: string;
  previousAnswer?: string;
  clarifications?: Turn["clarifications"];
}

function sourceContent(turn: Turn) {
  return {
    leadIn: turn.lead_in,
    filename: turn.filename,
    line: turn.evidence_line,
    evidence: turn.evidence_text,
    location: turn.evidence_location,
    kind: turn.evidence_kind,
  };
}

function deriveContent(state: RoomState | null): CardContent {
  const phase = state?.phase ?? "none";
  const turns = state?.turns ?? [];
  const resolved = turns.filter((turn) => turn.answer || turn.timed_out).length;
  let current: Turn | null = null;
  let currentIndex = -1;
  for (let index = turns.length - 1; index >= 0; index--) {
    if (turns[index].question && !turns[index].answer && !turns[index].timed_out) {
      current = turns[index];
      currentIndex = index;
      break;
    }
  }

  if ((phase === "voting" || phase === "question" || phase === "interpreting" || phase === "interpretation_retry") && current) {
    return {
      name: current.panelist,
      question: current.question,
      number: `QUESTION ${currentIndex + 1}`,
      ...sourceContent(current),
      clarifications: current.clarifications,
      reviewStatus: phase === "interpreting" ? "Reading your submission… Answer clock paused." : phase === "interpretation_retry" ? "Could not interpret the submission. Answer clock paused." : undefined,
    };
  }
  if (phase === "generating") {
    const previous = [...turns].reverse().find((turn) => turn.answer || turn.timed_out);
    if (previous) {
      return {
        name: previous.panelist,
        question: previous.question,
        number: "REVIEWING",
        reviewStatus: previous.timed_out ? "Reviewing the missed turn…" : "Reviewing your answer…",
        previousAnswer: previous.timed_out
          ? "Time expired · question passed to the panel."
          : `Team answer${previous.answered_by ? ` · ${previous.answered_by}` : ""}: ${previous.answer}`,
        ...sourceContent(previous),
        clarifications: previous.clarifications,
      };
    }
    return { name: state?.active_panelist ?? "The panel", question: "Reviewing the project…", number: `QUESTION ${resolved + 1}` };
  }
  if (phase === "retry") {
    return { name: "Question paused", question: `${state?.error ?? "The next question could not be generated."} The host can retry from Controls.`, number: `QUESTION ${resolved + 1}` };
  }
  if (phase === "complete") {
    const feedback = state?.feedback_status;
    return {
      name: feedback === "generating" ? "Preparing coaching report" : "Defense complete",
      question: feedback === "generating"
        ? "The panel has finished. Your coaching report is being prepared."
        : feedback === "failed"
          ? `${state?.error ?? "The coaching report could not be generated."} The host can retry from Controls.`
          : "Open Transcript to review your answers and coaching report.",
      number: `${resolved} RESOLVED`,
    };
  }
  if (phase === "lobby") {
    return { name: "Your team is gathering", question: "The host starts the defense when everyone is ready.", number: "READY" };
  }
  return { name: "Your defense begins here", question: "Create or join a room to begin your defense.", number: "READY" };
}

export function QuestionCard({ roomState }: QuestionCardProps) {
  const content = deriveContent(roomState);
  return (
    <section id="question-card" aria-labelledby="panelist-name">
      <div className="question-heading">
        <div>
          <p className="question-kicker">THE PANEL ASKS</p>
          <h2 id="panelist-name">{content.name}</h2>
        </div>
        <span className="question-number">{content.number}</span>
      </div>
      {content.reviewStatus && <p className="question-review-status" aria-live="polite">{content.reviewStatus}</p>}
      <div className="question-scroll" tabIndex={0} aria-label="Question and cited source">
      {content.leadIn && <p id="panelist-lead-in">{content.leadIn}</p>}
      <p id="question-text">{content.question}</p>
      {content.clarifications?.map((exchange, index) => <div className="question-clarification" key={index}>
        <p><strong>Defender asks:</strong> {exchange.request}</p>
        <p><strong>{content.name} explains:</strong> {exchange.reply}</p>
      </div>)}
      {content.previousAnswer && <p className="question-previous-answer">{content.previousAnswer}</p>}
      {content.filename !== undefined && (
        isResearchCitation(content.kind) ? (
          <PageCitation
            filename={content.filename}
            evidence={content.evidence}
            location={content.location}
          />
        ) : (
        <div id="source-block" role="group" aria-label={content.kind?.startsWith("research") ? "Exact extracted document text" : "Exact cited source line"}>
          <div className="source-heading">
            <span className="source-filename" title={content.filename}>{content.filename}</span>
            <span className="source-line-label">{content.location ?? `Line ${content.line}`}</span>
          </div>
          <div className="source-code-scroll" tabIndex={0} aria-label={`${content.kind?.startsWith("research") ? "Extracted document text" : "Source code"} at ${content.filename}, ${content.location ?? `line ${content.line}`}`}>
            <span className="source-line-number" aria-hidden="true">{content.location?.match(/extracted line (\d+)/)?.[1] ?? content.line}</span>
            <pre><code>{content.evidence}</code></pre>
          </div>
        </div>
        )
      )}
      </div>
    </section>
  );
}

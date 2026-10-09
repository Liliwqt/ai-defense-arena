import { ProbeExchange } from "./ProbeExchange";
import { PageCitation } from "./PageCitation";
import { useEffect, useRef } from "react";
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
  before?: string;
  after?: string;
  reviewStatus?: string;
  previousAnswer?: string;
  clarifications?: Turn["clarifications"];
  probe?: Turn["probe"];
  initialAnswer?: string | null;
}

function sourceContent(turn: Turn) {
  return {
    probe: turn.probe,
    leadIn: turn.lead_in,
    filename: turn.filename,
    line: turn.evidence_line,
    evidence: turn.evidence_text,
    location: turn.evidence_location,
    kind: turn.evidence_kind,
    before: turn.evidence_before,
    after: turn.evidence_after,
  };
}

function deriveContent(state: RoomState | null): CardContent {
  const phase = state?.phase ?? "none";
  const turns = state?.turns ?? [];
  const resolved = turns.filter((turn) => turn.resolved ?? (!!turn.answer || !!turn.timed_out)).length;
  let current: Turn | null = null;
  let currentIndex = -1;
  for (let index = turns.length - 1; index >= 0; index--) {
    if (turns[index].question && (!turns[index].answer || turns[index].probe?.status === "pending") && !turns[index].timed_out) {
      current = turns[index];
      currentIndex = index;
      break;
    }
  }

  if ((phase === "voting" || phase === "probe" || phase === "question" || phase === "interpreting" || phase === "interpretation_retry") && current) {
    return {
      name: current.panelist,
      question: current.question,
      number: `QUESTION ${currentIndex + 1}${state?.question_budget ? ` OF ${state.question_budget}` : ""}`,
      ...sourceContent(current),
      clarifications: current.clarifications,
      initialAnswer: current.answer,
      reviewStatus: phase === "interpreting" ? state?.clock_paused === false ? "Reading your submission… Answer clock running." : "Reading your submission… Answer clock paused." : phase === "interpretation_retry" ? state?.clock_paused === false ? "Could not interpret the submission. Answer clock running." : "Could not interpret the submission. Answer clock paused." : undefined,
    };
  }
  if (phase === "generating") {
    const previous = [...turns].reverse().find((turn) => turn.resolved ?? (!!turn.answer || !!turn.timed_out));
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
          : `Open Transcript to review your answers and coaching report.${state?.completion_reason ? ` Ending reason: ${state.completion_reason}.` : ""}`,
      number: `${resolved} RESOLVED`,
    };
  }
  if (phase === "lobby") {
    if (state?.research_planning_status === "planning") {
      return { name: "Preparing research coverage", question: "Mapping the uploaded research. The scope preview will appear in Controls for your team to inspect.", number: "MAPPING" };
    }
    if (state?.research_plan) {
      return { name: "Research scope ready", question: `${state.research_plan.topics.length} proposed topics are ready in Controls. Review the map and confirm the question budget before starting.`, number: "PLAN READY" };
    }
    return { name: "Your team is gathering", question: "The host starts the defense when everyone is ready.", number: "READY" };
  }
  return { name: "Your defense begins here", question: "Create or join a room to begin your defense.", number: "READY" };
}

export function QuestionCard({ roomState }: QuestionCardProps) {
  const content = deriveContent(roomState);
  const scrollRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = 0;
  }, [roomState?.room_code, roomState?.turns.length]);
  useEffect(() => {
    const scroll = scrollRef.current;
    const probe = scroll?.querySelector<HTMLElement>(".panelist-probe");
    if (scroll && probe) scroll.scrollTop += probe.getBoundingClientRect().top - scroll.getBoundingClientRect().top;
  }, [content.probe?.id, content.probe?.clarifications.length]);
  if (roomState?.defense_type && roomState.defense_type !== "code" && content.name === "Critical Judge") content.name = "Critical Reviewer";
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
      <div className="question-scroll" ref={scrollRef} tabIndex={0} aria-label="Question and cited source">
      {roomState?.current_topic && <p className="question-topic">Topic: {roomState.research_plan?.topics.find(t => t.id === roomState.current_topic)?.title}</p>}
      {content.leadIn && <p id="panelist-lead-in">{content.leadIn}</p>}
      <p id="question-text">{content.question}</p>
      {content.clarifications?.map((exchange, index) => <div className="question-clarification" key={index}>
        <p><strong>Defender asks:</strong> {exchange.request}</p>
        <p><strong>{content.name} explains:</strong> {exchange.reply}</p>
      </div>)}
      {content.initialAnswer && <p className="question-previous-answer"><strong>Original answer:</strong> <span>{content.initialAnswer}</span></p>}
      <ProbeExchange probe={content.probe} panelist={content.name} />
      {content.previousAnswer && <p className="question-previous-answer">{content.previousAnswer}</p>}
      {content.filename !== undefined && (
        isResearchCitation(content.kind) ? (
          <PageCitation
            filename={content.filename}
            evidence={content.evidence}
            location={content.location}
            before={content.before}
            after={content.after}
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

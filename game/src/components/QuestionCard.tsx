import { ProbeExchange } from "./ProbeExchange";
import { PageCitation } from "./PageCitation";
import { useEffect, useRef } from "react";
import { isResearchCitation } from "../lib/citation";
import type { RoomState } from "../types";

import { deriveRoomPresentation, type RoomPresentation } from "../lib/roomPresentation";

interface QuestionCardProps {
  presentation?: RoomPresentation;
  roomState: RoomState | null;
}

export function QuestionCard({ roomState, presentation = deriveRoomPresentation(roomState) }: QuestionCardProps) {
  const content = presentation.card;
  const clarification = content.probe ? undefined : content.clarifications?.at(-1);
  const scrollRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = 0;
  }, [roomState?.room_code, roomState?.turns.length, content.clarifications?.length]);
  useEffect(() => {
    const scroll = scrollRef.current;
    const probe = scroll?.querySelector<HTMLElement>(".panelist-probe");
    if (scroll && probe) scroll.scrollTop += probe.getBoundingClientRect().top - scroll.getBoundingClientRect().top;
  }, [content.probe?.id, content.probe?.clarifications.length]);
  if (presentation.reaction) {
    const { name, text } = presentation.reaction;
    return (
      <section id="question-card" className="panelist-reaction-card" aria-labelledby="panelist-reaction-name">
        <div className="question-heading">
          <div><p className="question-kicker">THE PANEL RESPONDS</p><h2 id="panelist-reaction-name">{name}</h2></div>
          <span className="question-number">SPEAKING</span>
        </div>
        <div className="question-scroll panelist-reaction-scroll" tabIndex={0} aria-label="Panelist response">
          <p className="panelist-reaction-text" role="status" aria-live="polite" aria-atomic="true">{text}</p>
          <p className="panelist-reaction-next">The next question and speaker vote will follow.</p>
        </div>
      </section>
    );
  }
  return (
    <section id="question-card" aria-labelledby="panelist-name">
      <div className="question-heading">
        <div>
          <p className="question-kicker">{clarification ? "THE PANEL CLARIFIES" : "THE PANEL ASKS"}</p>
          <h2 id="panelist-name">{content.name}</h2>
        </div>
        <span className="question-number">{content.number}</span>
      </div>
      {content.reviewStatus && <p className="question-review-status" aria-live="polite">{content.reviewStatus}</p>}
      <div className="question-scroll" ref={scrollRef} tabIndex={0} aria-label="Question and cited source">
      {roomState?.current_topic && <p className="question-topic">Topic: {roomState.research_plan?.topics.find(t => t.id === roomState.current_topic)?.title}</p>}
      {clarification && <p className="clarification-request"><strong>Defender asks:</strong> {clarification.request}</p>}
      <p id="question-text" aria-live={clarification ? "polite" : undefined}>{clarification?.reply ?? content.question}</p>
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

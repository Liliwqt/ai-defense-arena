import { ProbeExchange } from "./ProbeExchange";
import { PageCitation } from "./PageCitation";
import { useEffect, useRef, useState } from "react";
import { PDFViewer } from "./PDFViewer";
import { PaperMappingProgress } from "./PaperMappingProgress";
import { WaitingIndicator } from "./WaitingIndicator";
import { isResearchCitation } from "../lib/citation";
import type { RoomState } from "../types";

import { deriveRoomPresentation, type RoomPresentation } from "../lib/roomPresentation";

interface QuestionCardProps {
  playerToken?: string | null;
  presentation?: RoomPresentation;
  roomState: RoomState | null;
}

export function QuestionCard({ roomState, playerToken, presentation = deriveRoomPresentation(roomState) }: QuestionCardProps) {
  const hasPaper = Boolean(roomState?.documents?.length);
  const [paperTab, setPaperTab] = useState("question");
  const [expanded, setExpanded] = useState(false);
  const content = presentation.card;
  const { clarification } = presentation;
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
    const { name, text, closing } = presentation.reaction;
    return (
      <section id="question-card" className="panelist-reaction-card" aria-labelledby="panelist-reaction-name">
        <div className="question-heading">
          <div><p className="question-kicker">THE PANEL RESPONDS</p><h2 id="panelist-reaction-name">{name}</h2></div>
          <span className="question-number">SPEAKING</span>
        </div>
        <div className="question-scroll panelist-reaction-scroll" tabIndex={0} aria-label="Panelist response">
          <p className="panelist-reaction-text" role="status" aria-live="polite" aria-atomic="true">{text}</p>
          <p className="panelist-reaction-next">{closing ? "Your coaching report will follow. The defense is complete." : "The next question and speaker vote will follow."}</p>
        </div>
      </section>
    );
  }
  return (
    <section id="question-card" className={hasPaper ? "has-paper" : undefined} data-paper-tab={paperTab} data-paper-expanded={expanded} aria-labelledby="panelist-name">
      <div className="question-card-header">
      <div className="question-heading">
        <div>
          <p className="question-kicker">{clarification ? "THE PANEL CLARIFIES" : "THE PANEL ASKS"}</p>
          <h2 id="panelist-name">{content.name}</h2>
        </div>
        <span className="question-number">{content.number}</span>
      </div>
      {roomState?.voice?.enabled && <button type="button" className="speaker-desk-shortcut" onClick={() => {
        document.getElementById("answer-composer")?.scrollIntoView({block:"start",behavior:"smooth"});
        document.querySelector<HTMLElement>('#answer-composer textarea, #answer-composer button')?.focus({preventScroll:true});
      }}>Go to answer</button>}
      {hasPaper && <div className="paper-tabs" role="tablist" aria-label="Question or paper">
        {(["question", "paper"] as const).map(tab => <button key={tab} id={`paper-tab-${tab}`} type="button" role="tab" aria-controls={tab === "paper" ? "paper-reading-panel" : "paper-question-panel"} aria-selected={paperTab === tab} tabIndex={paperTab === tab ? 0 : -1}
          onKeyDown={event => { if (["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) { event.preventDefault(); const next = event.key === "Home" ? "question" : event.key === "End" ? "paper" : tab === "paper" ? "question" : "paper"; setPaperTab(next); if (next === "question") setExpanded(false); document.getElementById(`paper-tab-${next}`)?.focus(); } }}
          onClick={() => { setPaperTab(tab); if (tab === "question") setExpanded(false); }}>{tab === "paper" ? "Paper" : "Question"}</button>)}
      </div>}
      </div>
      {presentation.waiting && !content.mapping
        ? <div className="question-review-status">
          <WaitingIndicator label={presentation.waiting.label} detail={presentation.waiting.detail}
            active={presentation.waiting.active} startedAtMs={presentation.waiting.startedAtMs}
            serverNowMs={roomState?.server_now_ms} />
          {content.reviewStatus?.includes("Timer") && <p>{content.reviewStatus}</p>}
        </div>
        : content.reviewStatus && <p className="question-review-status" aria-live="polite">{content.reviewStatus}</p>}
      <div className="question-scroll" ref={scrollRef} tabIndex={0} aria-label="Question and cited source">
      <div className="question-copy" id="paper-question-panel" role={hasPaper ? "tabpanel" : undefined} aria-labelledby={hasPaper ? "paper-tab-question" : undefined}>
      {roomState?.current_topic && <p className="question-topic">Topic: {roomState.research_plan?.topics.find(t => t.id === roomState.current_topic)?.title}</p>}
      {clarification && <p className="clarification-request"><strong>Defender asks:</strong> {clarification.request}</p>}
      <p id="question-text" className={content.mapping ? "mapping-intro" : undefined} aria-live={clarification ? "polite" : undefined}>{clarification?.reply ?? content.question}</p>
      {content.mapping && <PaperMappingProgress progress={roomState?.research_plan_progress}
        startedAtMs={presentation.waiting?.startedAtMs} serverNowMs={roomState?.server_now_ms} />}
      {content.initialAnswer && <p className="question-previous-answer"><strong>Original answer:</strong> <span>{content.initialAnswer}</span></p>}
      <ProbeExchange probe={content.probe} panelist={content.name} />
      {content.previousAnswer && <p className="question-previous-answer">{content.previousAnswer}</p>}
      {content.filename !== undefined && !(hasPaper && roomState?.turns.at(-1)?.evidence_document_id) && (
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
      {hasPaper && roomState && <PDFViewer roomState={roomState} playerToken={playerToken} expanded={expanded} onExpandedChange={value => { setExpanded(value); if (value) setPaperTab("paper"); }} />}
      </div>
    </section>
  );
}

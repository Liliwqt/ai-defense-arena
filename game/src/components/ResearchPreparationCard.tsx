import { useState } from "react";
import type { RoomState } from "../types";
import { PaperMappingProgress } from "./PaperMappingProgress";
import { PDFViewer } from "./PDFViewer";
import "./researchPreparation.css";

/** The accepted paper stays readable while the shared research map is prepared. */
export function ResearchPreparationCard({ roomState, playerToken }: {
  roomState: RoomState; playerToken?: string | null;
}) {
  const [tab, setTab] = useState<"question" | "paper">("question");
  const [expanded, setExpanded] = useState(false);
  const hasPaper = !!roomState.documents?.length;
  const uploads = roomState.accepted_files?.filter(file => file.kind.startsWith("research")) ?? [];
  return <section id="question-card" className={`research-preparation-card${hasPaper ? " has-paper" : ""}`}
    data-paper-tab={tab} data-paper-expanded={expanded} aria-labelledby="research-preparation-title">
    <div className="question-heading">
      <div><p className="question-kicker">RESEARCH PREPARATION</p><h2 id="research-preparation-title">Research preparation</h2></div>
      <span className="question-number">{roomState.practice_tier === "free" ? "FREE" : "STANDARD"} · MAPPING</span>
    </div>
    {hasPaper && <div className="paper-tabs" role="tablist" aria-label="Mapping or paper">
      {(["question", "paper"] as const).map(value => <button key={value} type="button" role="tab"
        id={`paper-tab-${value}`} aria-controls={value === "paper" ? "paper-reading-panel" : "paper-question-panel"}
        aria-selected={tab === value} tabIndex={tab === value ? 0 : -1}
        onClick={() => { setTab(value); if (value === "question") setExpanded(false); }}
        onKeyDown={event => {
          if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
          event.preventDefault();
          const next = event.key === "Home" ? "question" : event.key === "End" ? "paper" : value === "paper" ? "question" : "paper";
          setTab(next); if (next === "question") setExpanded(false);
          document.getElementById(`paper-tab-${next}`)?.focus();
        }}>{value === "paper" ? "Paper" : "Mapping"}</button>)}
    </div>}
    <div className="mapping-desk">
      <div className="mapping-desk-notes question-copy" id="paper-question-panel" role={hasPaper ? "tabpanel" : undefined}
        aria-labelledby={hasPaper ? "paper-tab-question" : undefined}>
        <PaperMappingProgress roomState={roomState} compact />
        <section className="mapping-accepted-upload" aria-label="Accepted research upload">
          <p className="question-kicker">ACCEPTED UPLOAD{uploads.length > 1 ? "S" : ""}</p>
          {uploads.length ? uploads.map(file => <div key={file.name}><strong>{file.name}</strong><p>{file.detail} · Research paper</p></div>)
            : <strong>{roomState.files.join(", ") || "Your accepted research material"}</strong>}
          <p>No defense question has started. Your team can keep reading while the map is prepared.</p>
        </section>
      </div>
      {hasPaper ? <PDFViewer roomState={roomState} playerToken={playerToken} expanded={expanded}
        onExpandedChange={value => { setExpanded(value); if (value) setTab("paper"); }} />
        : <section className="mapping-paper-unavailable" aria-label="Paper preview">
          <p className="question-kicker">YOUR PAPER</p><h3>Accepted and ready for mapping</h3>
          <p>Original page viewing is available for PDF uploads. Your finished map will include references to the accepted text.</p>
        </section>}
    </div>
  </section>;
}

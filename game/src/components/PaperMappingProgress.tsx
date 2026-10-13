import type { RoomState } from "../types";

const stages = [
  { id: "preparing", label: "Preparing accepted documents" },
  { id: "mapping", label: "Drafting research topics" },
  { id: "validating", label: "Checking the complete map" },
] as const;

export function PaperMappingProgress({ progress }: { progress?: RoomState["research_plan_progress"] }) {
  const stage = progress?.stage ?? "mapping";
  const topics = progress?.topics ?? [];
  const step = stages.findIndex(item => item.id === stage);
  const status = stage === "preparing" ? "Preparing uploaded research…" : stage === "validating"
    ? "Checking the complete map and source references…" : "Mapping the uploaded research…";
  return <div className="room-create-progress paper-mapping-progress" aria-busy="true">
    <p role="status" aria-live="polite" aria-atomic="true">{status} {topics.length > 0 ? `${topics.length} draft ${topics.length === 1 ? "topic" : "topics"} received.` : "No defense question has started."}</p>
    <div className="room-create-progress-track" role="progressbar" aria-label="Paper mapping progress" aria-valuetext={stage === "mapping" ? "Mapping in progress" : status}>
      <span className="room-create-progress-fill is-indeterminate" aria-hidden="true" />
    </div>
    <ol className="mapping-stages" aria-label="Mapping stages">{stages.map((item, index) => <li key={item.id} aria-current={index === step ? "step" : undefined}>
      <span aria-hidden="true">{index < step ? "✓" : index + 1}</span> {item.label}<span className="mapping-step-status">{index < step ? "Done" : index === step ? "In progress" : "Waiting"}</span>
    </li>)}</ol>
    {topics.length > 0 && <>
      <p className="control-help">Draft topics · provisional until the complete map passes validation.</p>
      <ol className="mapping-topics" aria-label="Draft research topics">{topics.map(topic => <li key={topic.id}>
        <div className="mapping-topic-heading"><strong>{topic.title}</strong><span>Draft</span></div>
        <p className="mapping-reviewer">{topic.panelist === "Critical Judge" ? "Critical Reviewer" : topic.panelist}</p>
        <p>{topic.objective}</p>
        <details><summary>Source references ({topic.references.length})</summary>{topic.references.map((ref, index) => <div className="mapping-reference" key={index}>
          <strong>{ref.filename} · {ref.evidence_location}</strong>
          <pre tabIndex={0}><code>{ref.evidence_text}</code></pre>
        </div>)}</details>
      </li>)}</ol>
    </>}
    <p className="control-help">Your uploads are retained. Review the finished map before starting.</p>
  </div>;
}

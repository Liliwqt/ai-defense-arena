import { useEffect, useState } from "react";
import type { RoomState } from "../types";
import { isResearchCitation } from "../lib/citation";
import { PageCitation } from "./PageCitation";

interface Props {
  roomState: RoomState;
  connected: boolean;
  previewMode: boolean;
  onSendEvent: (payload: Record<string, unknown>) => boolean;
  onBudgetDraftChange?: (dirty: boolean) => void;
}

export function ResearchPlanPanel({ roomState: state, connected, previewMode, onSendEvent, onBudgetDraftChange }: Props) {
  const plan = state.research_plan;
  const addressed = Object.values(state.coverage ?? {}).filter(topic => topic.status === "addressed").length;
  const status = state.research_planning_status ?? "none";
  const [budget, setBudget] = useState<string>("");
  const [dirty, setDirty] = useState(false);
  const [error, setError] = useState("");
  const [pendingBudget, setPendingBudget] = useState<number | null>(null);
  const editable = state.self_is_host && state.phase === "lobby" && connected && !previewMode;

  useEffect(() => {
    setBudget(String(state.research_budget_preview ?? plan?.suggested_budget ?? ""));
    setDirty(false); setError("");
    onBudgetDraftChange?.(false);
  }, [plan?.id, state.research_budget_preview, state.research_plan_approved, onBudgetDraftChange]);

  useEffect(() => {
    if (pendingBudget !== null && state.research_plan_approved && state.research_budget_preview === pendingBudget) {
      setDirty(false); setPendingBudget(null); onBudgetDraftChange?.(false);
    }
  }, [pendingBudget, state.research_plan_approved, state.research_budget_preview, onBudgetDraftChange]);

  function approve(event: React.FormEvent) {
    event.preventDefault();
    const value = Number(budget);
    if (!Number.isInteger(value) || value < 4 || value > 100) {
      setError("Choose a whole-number question budget from 4 to 100."); return;
    }
    if (onSendEvent({ type: "approve_research_plan", plan_id: plan?.id, question_budget: value })) {
      setError(""); setPendingBudget(value);
    }
  }

  return <section className="research-plan-panel" aria-labelledby="research-plan-heading">
    <div className="research-plan-heading">
      <span className="plan-preview-badge">RESEARCH SCOPE</span>
      <h3 id="research-plan-heading">Research coverage plan</h3>
    </div>
    <p className="control-help">Review the topics and confirm a maximum before starting. Addressed means discussion coverage, not proof that the research is correct. This budget is not a price or credit quote.</p>
    {status === "none" && <p className="control-help">{state.self_is_host ? "Prepare an AI map of the accepted papers and any accompanying code." : "The host can prepare the research map. It will appear here for the whole team."}</p>}
    {status === "planning" && <p role="status" aria-live="polite">Mapping the uploaded research… No defense question has started.</p>}
    {status === "failed" && <p role="alert" className="drawer-error">{state.research_plan_error ?? "The research map could not be prepared."} Your uploads are retained. {state.self_is_host ? "Retry when ready." : "The host can retry."}</p>}
    {editable && status !== "planning" && <button type="button" disabled={state.plan_attempts_left === 0} className="button-secondary"
      onClick={() => onSendEvent({ type: status === "failed" ? "retry_research_plan" : "prepare_research_plan" })}>
      {status === "failed" ? "Retry research map" : plan ? "Prepare map again" : "Prepare defense"}
    </button>}
    {plan && <>
      {state.completion_reason && <p role="status">Ending reason: {state.completion_reason}</p>}
      {state.coverage && <p className="plan-summary">{addressed} of {plan.topics.length} topics addressed</p>}
      <p className="plan-summary"><strong>{plan.topics.length} proposed topics</strong> · suggested maximum {plan.suggested_budget} questions</p>
      {plan.uncertainties.length > 0 && <div className="plan-uncertainties"><strong>Unclear or missing information</strong>
        <ul>{plan.uncertainties.map((item, i) => <li key={i}>{item}</li>)}</ul>
      </div>}
      <ol className="plan-topics" aria-label="Proposed research topics">{plan.topics.map((topic, index) => <li key={topic.id}>
        <div className="plan-topic-heading"><span>TOPIC {index + 1}</span><span>{topic.panelist === "Critical Judge" ? "Critical Reviewer" : topic.panelist}</span></div>
        <h4>{topic.title}</h4><p>{topic.objective}</p>
        {state.coverage?.[topic.id] && <div className="topic-coverage">
          <strong>{state.coverage[topic.id].status}</strong>
          <span> · supporting questions: {state.coverage[topic.id].turns.map(i => i + 1).join(", ") || "none"}</span>
          {state.coverage[topic.id].reason && <p>{state.coverage[topic.id].reason}</p>}
        </div>}
        {topic.gaps.length > 0 && <div className="plan-topic-gaps"><strong>Needs clarification</strong><ul>{topic.gaps.map((gap, i) => <li key={i}>{gap}</li>)}</ul></div>}
        <details><summary>Source references ({topic.references.length})</summary>
          {topic.references.map((ref, i) => isResearchCitation(ref.evidence_kind)
            ? <PageCitation key={i} id={`plan-${topic.id}-ref-${i}`} filename={ref.filename}
                evidence={ref.evidence_text} location={ref.evidence_location} before={ref.evidence_before} after={ref.evidence_after} />
            : <div key={i} className="plan-source" role="group" aria-label={`Exact cited source at ${ref.filename}, ${ref.evidence_location}`}>
                <strong>{ref.filename} · {ref.evidence_location}</strong><pre tabIndex={0}><code>{ref.evidence_text}</code></pre>
              </div>)}
        </details>
      </li>)}</ol>
      {state.self_is_host && state.phase === "lobby" ? <form onSubmit={approve} className="plan-budget-form">
        <label className="setup-label">Question budget
          <input className="setup-input" type="number" min={4} max={100} step={1} value={budget}
            disabled={!editable} onChange={event => { setBudget(event.target.value); setDirty(true); onBudgetDraftChange?.(true); setError(""); }} />
        </label>
        <p className="control-help">4–100 questions. The defense stops at this maximum or when all topics are addressed after every reviewer has spoken.</p>
        {Number(budget) > 0 && Number(budget) < plan.topics.length && <p className="plan-warning" role="status">This limit is smaller than the topic count. Some topics may remain unexplored.</p>}
        <button type="submit" className="button-primary" disabled={!editable}>Confirm question budget</button>
        {state.research_plan_approved && !dirty && <p role="status">Maximum confirmed: {state.research_budget_preview} questions.</p>}
        {error && <p role="alert" className="drawer-error">{error}</p>}
      </form> : <p className="control-help">Maximum questions: {state.research_budget_preview ?? plan.suggested_budget} questions · {state.research_plan_approved ? "confirmed by host" : "awaiting host confirmation"}.</p>}
      <p className="control-help">Source locations are validated. The proposed map and its interpretation still need your review.</p>
    </>}
  </section>;
}

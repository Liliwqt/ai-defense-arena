import { useEffect, useRef, useState } from "react";
import { useTabDraft } from "../hooks/useTabDraft";
import { createPortal } from "react-dom";
import type { ProfileDescription, RoomState } from "../types";
import { isResearchCitation } from "../lib/citation";
import { PageCitation } from "./PageCitation";
import { PaperMappingProgress } from "./PaperMappingProgress";
import { ResearchProfileEditor } from "./ResearchProfileEditor";
import { ResearchProfileReview } from "./ResearchProfileReview";

interface Props {
  roomState: RoomState;
  connected: boolean;
  previewMode: boolean;
  onSendEvent: (payload: Record<string, unknown>) => boolean;
  onScopeDraftChange?: (dirty: boolean) => void;
  actionContainer?: HTMLElement | null;
  actionError?: string | null;
  accessReason?: string;
  startControl?: { label: string; reason: string; accessLabel: string; onStart: () => void; onAccount?: () => void };
}

export function ResearchPlanPanel({ roomState: state, connected, previewMode, onSendEvent, onScopeDraftChange, actionContainer, actionError, accessReason, startControl }: Props) {
  const plan = state.research_plan;
  const mappingPending = useRef(false);
  const reviewFormRef = useRef<HTMLFormElement>(null);
  const correctionRef = useRef<HTMLDetailsElement>(null);
  const [waitingForMap, setWaitingForMap] = useState(false);
  const addressed = Object.values(state.coverage ?? {}).filter(topic => topic.status === "addressed").length;
  const status = state.research_planning_status ?? "none";
  const questionLimit = state.question_limit ?? (state.practice_tier === "free" ? 8 : 100);
  const initialBudget = String(state.research_budget_preview ?? (plan ? Math.min(plan.suggested_budget, questionLimit) : ""));
  const [budget, setBudget] = useTabDraft("budget", initialBudget, { room: true, marker: plan?.id });
  const dirty = budget !== initialBudget;
  const [profileDirty, setProfileDirty] = useState(false);
  const [error, setError] = useState("");
  const [pendingBudget, setPendingBudget] = useState<number | null>(null);
  const approvalPending = useRef(false);
  const [reviewedText, setReviewedText] = useTabDraft("profile-reviewed", state.research_plan_approved ? "yes" : "no", { room: true, marker: plan?.id, valid: value => ["yes", "no"].includes(value) });
  const [uncertaintyText, setUncertaintyText] = useTabDraft("profile-uncertainty", state.research_plan_approved ? "yes" : "no", { room: true, marker: plan?.id, valid: value => ["yes", "no"].includes(value) });
  const reviewedProfile = reviewedText === "yes";
  const acknowledgedUncertainty = uncertaintyText === "yes";
  const previousApproval = useRef(state.research_plan_approved);
  const editable = state.self_is_host && state.phase === "lobby" && connected && !previewMode && status !== "planning" && !waitingForMap && pendingBudget === null && !accessReason;

  useEffect(() => {
    mappingPending.current = false;
    setWaitingForMap(false);
  }, [status, plan?.id, state.room_code, connected]);

  useEffect(() => {
    approvalPending.current = false;
    setPendingBudget(null);
  }, [plan?.id, state.room_code, connected]);

  useEffect(() => {
    if (!actionError) return;
    mappingPending.current = false;
    approvalPending.current = false;
    setWaitingForMap(false);
    setPendingBudget(null);
  }, [actionError]);

  function prepare(profile_correction?: ProfileDescription) {
    if (!editable || mappingPending.current || state.plan_attempts_left === 0) return false;
    const payload = profile_correction ? { type: "prepare_research_plan", profile_correction }
      : { type: status === "failed" ? "retry_research_plan" : "prepare_research_plan" };
    if (!onSendEvent(payload)) return false;
    mappingPending.current = true;
    setWaitingForMap(true);
    return true;
  }

  useEffect(() => {
    if (!previousApproval.current && state.research_plan_approved && plan?.profile) { setReviewedText("yes"); setUncertaintyText("yes"); }
    previousApproval.current = state.research_plan_approved;
  }, [plan?.id, state.research_plan_approved]);

  useEffect(() => {
    setError("");
  }, [plan?.id, state.research_budget_preview, state.research_plan_approved, onScopeDraftChange]);

  useEffect(() => {
    if (pendingBudget !== null && state.research_plan_approved && state.research_budget_preview === pendingBudget) {
      setPendingBudget(null); approvalPending.current = false;
    }
  }, [pendingBudget, state.research_plan_approved, state.research_budget_preview, onScopeDraftChange]);

  useEffect(() => { onScopeDraftChange?.(dirty || profileDirty || waitingForMap || pendingBudget !== null); }, [dirty, profileDirty, waitingForMap, pendingBudget, onScopeDraftChange]);

  const description = state.research_profile_correction ?? plan?.profile;

  function approve(event: React.FormEvent) {
    event.preventDefault();
    if (!editable || approvalPending.current || status !== "ready") return;
    const value = Number(budget);
    if (!Number.isInteger(value) || value < 4 || value > questionLimit) {
      setError(`Choose a whole-number question budget from 4 to ${questionLimit}.`); return;
    }
    if (profileDirty || !plan?.profile || !reviewedProfile || (plan.profile.needs_uncertainty_acknowledgment && !acknowledgedUncertainty)) {
      setError("Review the research profile and acknowledge any unclear information before confirming."); return;
    }
    approvalPending.current = true;
    if (onSendEvent({ type: "approve_research_plan", plan_id: plan.id, question_budget: value,
                      confirm_profile: true, acknowledge_uncertainty: acknowledgedUncertainty })) {
      setError(""); setPendingBudget(value);
    } else approvalPending.current = false;
  }

  const reviewReason = previewMode ? "Visual preview · preparation controls are read-only."
    : !state.self_is_host ? "The host prepares and confirms the research map."
    : state.phase !== "lobby" ? "The research profile is fixed during this defense."
    : !connected ? "Reconnect to prepare or confirm the research map."
    : accessReason || "";
  const mapReason = reviewReason || (state.plan_attempts_left === 0 ? "No mapping attempts left. Your accepted uploads are retained."
      : profileDirty ? "Apply your profile changes and remap before continuing."
      : waitingForMap ? "Waiting for the server to begin mapping…" : "");
  const readyMap = status === "ready" && !!plan?.profile;
  const mappingButton = state.self_is_host && state.phase === "lobby" && status !== "planning" && <button type="button"
    disabled={!editable || state.plan_attempts_left === 0 || profileDirty} className={readyMap ? "button-secondary" : "button-primary"} onClick={() => prepare()}>
    {status === "failed" ? "Retry research map" : plan ? "Prepare map again" : "Map paper"}
  </button>;

  const validBudget = Number.isInteger(Number(budget)) && Number(budget) >= 4 && Number(budget) <= questionLimit;
  const confirmationReason = profileDirty ? "Apply your profile changes and remap before confirming or starting."
    : pendingBudget !== null ? "Waiting for the server to confirm this profile and budget…"
    : !validBudget ? `Choose a whole-number question budget from 4 to ${questionLimit}.`
    : !reviewedProfile ? "Review and explicitly confirm the research profile before starting."
    : plan?.profile?.needs_uncertainty_acknowledgment && !acknowledgedUncertainty ? "Acknowledge the unclear profile information before confirming."
    : dirty || !state.research_plan_approved ? "Confirm the current profile and question budget before starting." : "";
  const alreadyConfirmed = !!state.research_plan_approved && !confirmationReason;
  const startReason = startControl?.reason || reviewReason || (waitingForMap ? "Waiting for the server to begin mapping…" : confirmationReason);
  const nextTitle = !state.self_is_host ? "Waiting for the host"
    : state.phase !== "lobby" ? "Defense overview"
    : status === "planning" || waitingForMap ? "Mapping your paper"
    : pendingBudget !== null ? "Confirming your review"
    : profileDirty ? "Apply your profile changes"
    : !readyMap ? status === "failed" ? "Retry paper mapping" : "Map your paper"
    : alreadyConfirmed ? "Start your defense" : "Review and confirm";

  function showRequiredReview() {
    if (profileDirty && correctionRef.current) {
      correctionRef.current.open = true;
      const button = correctionRef.current.querySelector<HTMLButtonElement>('button[type="submit"]');
      button?.scrollIntoView?.({ block: "center" });
      button?.focus({ preventScroll: true });
      return;
    }
    const form = reviewFormRef.current;
    const target = !validBudget ? form?.querySelector<HTMLInputElement>('input[type="number"]')
      : form?.querySelector<HTMLInputElement>('input[type="checkbox"]:not(:checked):not(:disabled)')
        ?? form?.querySelector<HTMLButtonElement>('button[type="submit"]');
    target?.scrollIntoView?.({ block: "center" });
    target?.focus({ preventScroll: true });
  }

  const actions = <>
    <div className="next-step-heading" aria-live="polite" aria-atomic="true">
      <span>Next step</span><h3>{nextTitle}</h3>
    </div>
    <p className="control-help">{status === "planning" ? "Mapping your paper… Start appears when the validated map is ready."
      : waitingForMap ? "Waiting for the server to begin mapping…"
      : readyMap ? startReason || "Your team can start when you’re ready." : mapReason || "Prepare the map first. Start appears when it is ready."}</p>
    {!readyMap && mappingButton}
    {(readyMap || profileDirty) && state.self_is_host && state.phase === "lobby" && !alreadyConfirmed && <button type="button"
      className="button-primary" disabled={!editable} onClick={showRequiredReview}>
      {profileDirty ? "Review profile changes" : "Review profile and budget"}
    </button>}
    {readyMap && state.self_is_host && state.phase === "lobby" && !previewMode && startControl && <button type="button"
      className={alreadyConfirmed ? "button-primary" : "button-secondary"} disabled={!!startReason} onClick={startControl.onStart}>{startControl.label}</button>}
    {state.self_is_host && startControl && <p className="preparation-access">{startControl.accessLabel}</p>}
    {state.self_is_host && startControl?.onAccount && <button type="button" className="button-secondary" onClick={startControl.onAccount}>Open Account</button>}
  </>;

  return <section className="research-plan-panel" aria-labelledby="research-plan-heading">
    <div className="research-plan-heading">
      <span className="plan-preview-badge">RESEARCH SCOPE</span>
      <h3 id="research-plan-heading">Research coverage plan</h3>
    </div>
    {status === "none" && <p className="control-help">{state.self_is_host ? "Prepare an AI map of the accepted papers and any accompanying code." : "The host can prepare the research map. It will appear here for the whole team."}</p>}
    {status === "planning" && <PaperMappingProgress progress={state.research_plan_progress}
      startedAtMs={state.operation?.started_at_ms ?? null} serverNowMs={state.server_now_ms} />}
    {status === "failed" && <p role="alert" className="drawer-error">{state.research_plan_error ?? "The research map could not be prepared."} Your uploads are retained. {state.self_is_host ? "Retry when ready." : "The host can retry."}</p>}
    {actionContainer ? createPortal(actions, actionContainer) : startControl ? <div className="research-next-action">{actions}</div> : null}
    {plan?.profile && <ResearchProfileReview profile={plan.profile} confirmed={Boolean(state.research_plan_approved && !profileDirty)} />}
    {plan && !plan.profile && <p role="alert" className="drawer-error">Prepare a new research map to review and confirm its research profile.</p>}
    {state.self_is_host && state.phase === "lobby" && description && <details ref={correctionRef} className="profile-correction">
      <summary>Correct profile</summary>
      <ResearchProfileEditor
      description={{ fields: description.fields, approaches: description.approaches, setting: description.setting }}
      planId={plan?.id} editable={editable && state.plan_attempts_left !== 0} onDirtyChange={setProfileDirty}
      onPrepare={prepare} />
    </details>}
    {!plan && state.research_profile_correction && !state.self_is_host && <p className="control-help">
      Saved host description: {state.research_profile_correction.fields.join(", ")} · {state.research_profile_correction.approaches.join(", ")}
      {state.research_profile_correction.setting && ` · ${state.research_profile_correction.setting}`}. Awaiting a validated map.
    </p>}
    {!plan && <>
    {readyMap || (!actionContainer && !startControl) ? mappingButton : null}
    {typeof state.plan_attempts_left === "number" && <p className="control-help">{state.plan_attempts_left} mapping attempts left</p>}
    {mapReason && <p className="control-help">{mapReason}</p>}
    </>}
    {plan && <>
      {status === "failed" && <p role="status">Previous map retained for reference. Complete mapping again before confirming or starting.</p>}
      {state.self_is_host && state.phase === "lobby" ? <form ref={reviewFormRef} onSubmit={approve} className="plan-budget-form">
        <h3>Confirm and prepare to start</h3>
        <label className="setup-label">Question budget
          <input className="setup-input" type="number" min={4} max={questionLimit} step={1} value={budget}
            disabled={!editable || profileDirty || status !== "ready"} onChange={event => { setBudget(event.target.value); setError(""); }} />
        </label>
        <p className="control-help">4–{questionLimit} questions. The defense stops at this maximum or when all topics are addressed after every reviewer has spoken.</p>
        {Number(budget) > 0 && Number(budget) < plan.topics.length && <p className="plan-warning" role="status">This limit is smaller than the topic count. Some topics may remain unexplored.</p>}
        {plan.profile && <>
          <label className="profile-confirmation"><input type="checkbox" checked={reviewedProfile} disabled={!editable || status !== "ready"}
            onChange={event => setReviewedText(event.target.checked ? "yes" : "no")} />I reviewed the research profile</label>
          {plan.profile.needs_uncertainty_acknowledgment && <label className="profile-confirmation">
            <input type="checkbox" checked={acknowledgedUncertainty} disabled={!editable || status !== "ready"}
              onChange={event => setUncertaintyText(event.target.checked ? "yes" : "no")} />I understand the profile has unclear information
          </label>}
        </>}
        <button type="submit" className="button-primary" disabled={!editable || status !== "ready" || profileDirty || !validBudget || alreadyConfirmed || !plan.profile || !reviewedProfile ||
          (plan.profile.needs_uncertainty_acknowledgment && !acknowledgedUncertainty)}>Confirm profile and budget</button>
        {confirmationReason && <p className="control-help">{confirmationReason}</p>}
        {state.research_plan_approved && !dirty && !profileDirty && pendingBudget === null && <p role="status">Maximum confirmed: {state.research_budget_preview} questions.</p>}
        {error && <p role="alert" className="drawer-error">{error}</p>}
      </form> : <p className="control-help">Maximum questions: {state.research_budget_preview ?? plan.suggested_budget} questions · {state.research_plan_approved ? "confirmed by host" : "awaiting host confirmation"}.</p>}
    {readyMap || (!actionContainer && !startControl) ? mappingButton : null}
    {typeof state.plan_attempts_left === "number" && <p className="control-help">{state.plan_attempts_left} mapping attempts left</p>}
    {mapReason && <p className="control-help">{mapReason}</p>}
      <section className="discussion-topics">
      <h3>Discussion topics</h3>
    <p className="control-help">Review the topics and confirm a maximum before starting. Addressed means discussion coverage, not proof that the research is correct. This budget is not a price or credit quote.</p>
      {state.completion_reason && <p role="status">Ending reason: {state.completion_reason}</p>}
      {state.coverage && <p className="plan-summary">{addressed} of {plan.topics.length} topics addressed</p>}
      <p className="plan-summary"><strong>{plan.topics.length} proposed topics</strong> · suggested maximum {plan.suggested_budget} questions</p>
      {plan.uncertainties.length > 0 && <div className="plan-uncertainties"><strong>Unclear or missing information</strong>
        <ul>{plan.uncertainties.map((item, i) => <li key={i}>{item}</li>)}</ul>
      </div>}

      <ol className="plan-topics" aria-label="Proposed research topics">{plan.topics.map((topic, index) => <li key={topic.id}>
        <details className="plan-topic-details"><summary>
          <span className="plan-topic-number">{String(index + 1).padStart(2, "0")}</span> {topic.title}
          <span className="plan-topic-reviewer">{topic.panelist === "Critical Judge" ? "Critical Reviewer" : topic.panelist}</span>
        </summary><p>{topic.objective}</p>
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
        </details>
      </li>)}</ol>
      </section>
      <p className="control-help">Source locations are validated. The proposed map and its interpretation still need your review.</p>
    </>}
  </section>;
}

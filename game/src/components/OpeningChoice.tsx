import { createPortal } from "react-dom";
import { useEffect, useState } from "react";
import type { RoomState } from "../types";

interface Props {
  state: RoomState;
  connected: boolean;
  previewMode: boolean;
  actionError?: string | null;
  showPreview?: boolean;
  actionContainer?: HTMLElement | null;
  onSendEvent: (payload: Record<string, unknown>) => boolean;
}

/** Both room and Controls use the same candidate-bound actions. */
export function OpeningChoice({ state, connected, previewMode, actionError, showPreview, actionContainer, onSendEvent }: Props) {
  const candidate = state.opening_candidate;
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => { setPending(false); setError(""); }, [candidate?.id, connected]);
  useEffect(() => { if (actionError) setPending(false); }, [actionError]);
  function choose(type: string) {
    if (!candidate || pending || !connected || previewMode) return;
    setError("");
    if (onSendEvent({ type, candidate_id: candidate.id })) setPending(true);
    else setError("Could not send your choice. Reconnect and try again.");
  }
  if (!state.self_is_host || !candidate) return <p role="status">Waiting for the host to choose an opening. No question timer has started.</p>;
  const actions = <>
    <div className="submission-retry-actions">
      <button type="button" disabled={!connected || previewMode || pending || state.question_attempts_left === 0} onClick={() => choose("retry_opening")}>Retry opening</button>
      <button type="button" disabled={!connected || previewMode || pending} onClick={() => choose("accept_repeated_opening")}>Accept repeated question</button>
    </div>
    {state.question_attempts_left === 0 && <p>No opening attempts remain. Accept this question or restart from Controls.</p>}
    {pending && <p role="status">Saving your choice…</p>}
    {!connected && <p role="status">Reconnecting… Your opening choice is retained.</p>}
    {(error || actionError) && <p role="alert">{error || actionError}</p>}
  </>;
  return <section className="submission-retry" aria-label="Repeated opening choice">
    <p>The opening repeats a recent question. Choose another attempt or explicitly accept this one. No new defense has been charged.</p>
    {showPreview && <><strong>Preview · not active</strong><p>{candidate.panelist}: {candidate.question}</p>
      <blockquote>{candidate.evidence_text}</blockquote><p>{candidate.filename} · {candidate.evidence_location}</p></>}
    {actionContainer ? createPortal(<><div className="next-step-heading"><span>Next step</span><h3>Choose an opening</h3></div>{actions}</>, actionContainer) : actions}
  </section>;
}

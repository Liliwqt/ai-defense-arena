import { useEffect, useState } from "react";
import type { RoomState } from "../types";

import { deriveRoomPresentation, type RoomPresentation } from "../lib/roomPresentation";

interface AnswerComposerProps {
  presentation?: RoomPresentation;
  roomState: RoomState | null;
  connected: boolean;
  previewMode: boolean;
  waitingForAnswerAck: boolean;
  actionError: string | null;
  actionErrorReason?: string | null;
  onSendEvent: (payload: Record<string, unknown>) => boolean;
}

export function AnswerComposer({ roomState, connected, previewMode, waitingForAnswerAck, actionError, actionErrorReason, onSendEvent, presentation = deriveRoomPresentation(roomState) }: AnswerComposerProps) {
  const [draft, setDraft] = useState("");
  const [localError, setLocalError] = useState("");
  const [writeRecovery, setWriteRecovery] = useState(false);
  const [interpretationLimited, setInterpretationLimited] = useState(false);
  const turnIndex = presentation.answerTurnIndex;
  const { submission } = presentation;
  const { probe, probing, turnKey, clarificationCount: allClarifications } = submission;
  const chosen = presentation.chosenSelf;
  const canWrite = chosen && (submission.entry === "open" || (submission.entry === "recovery" && writeRecovery));
  const recoveryAvailable = interpretationLimited || submission.recoveryAvailable;
  const direct = interpretationLimited || submission.direct;
  const recoveryDisabled = !connected || previewMode || waitingForAnswerAck;
  const reviewGuidance = previewMode ? "Mock preview · recovery actions are disabled."
    : !connected ? "Reconnecting… Your submission and remaining time are saved."
    : waitingForAnswerAck ? "Waiting for submission acknowledgment…"
    : submission.recoveryGuidance;

  useEffect(() => { setDraft(""); setLocalError(""); setWriteRecovery(false); setInterpretationLimited(false); }, [turnKey]);
  useEffect(() => {
    if (actionErrorReason === "ai_admission") setInterpretationLimited(true);
  }, [actionErrorReason]);
  useEffect(() => { if (allClarifications > 0) { setDraft(""); setLocalError(""); } }, [allClarifications, turnKey]);
  useEffect(() => { if (roomState?.my_pending_submission) setDraft(roomState.my_pending_submission); }, [roomState?.my_pending_submission]);

  function submitAnswer(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (previewMode || !canWrite || waitingForAnswerAck) return;
    const answer = draft.trim();
    if (!answer) { setLocalError("Write an answer before submitting."); return; }
    setLocalError("");
    if (!onSendEvent(probing ? { type: "submit_probe_reply", turn: turnIndex, probe_id: probe?.id, answer, direct } : { type: direct ? "submit_direct_answer" : "submit_answer", turn: turnIndex, answer })) {
      setLocalError("Could not send your answer. Check the connection and try again.");
    }
  }

  return (
    <section id="answer-composer" aria-label="Answer area">
      {submission.showRecovery && !canWrite && roomState ? (
        <div className="submission-retry" role="status">
          <p>{reviewGuidance}</p>
          {roomState.my_pending_submission && <p className="pending-text">{roomState.my_pending_submission}</p>}
          <div className="submission-retry-actions">
            <button type="button" disabled={recoveryDisabled || !submission.retryAvailable} onClick={() => onSendEvent({ type: "retry_interpretation" })}>Retry panelist</button>
            {chosen && <button type="button" disabled={recoveryDisabled} onClick={() => setWriteRecovery(true)}>Write a new answer</button>}
            {chosen && <button type="button" disabled={recoveryDisabled || !submission.savedAvailable} onClick={() => onSendEvent({ type: "use_pending_as_answer" })}>{probing ? "Use this as my reply" : "Use this as my answer"}</button>}
            {chosen && probing && <button type="button" disabled={recoveryDisabled} onClick={() => onSendEvent({ type: "finish_probe", turn: turnIndex, probe_id: probe?.id })}>Continue with original answer</button>}
          </div>
          {actionError && <p role="alert">{actionError}</p>}
        </div>
      ) : canWrite ? (
        <form id="answer-form" onSubmit={submitAnswer}>
          <label htmlFor="answer-textarea">{presentation.answerPrompt}{direct ? "" : " or clarify"} question {turnIndex + 1} · {Math.max(0, 2 - allClarifications)} clarifications left</label>
          <div className="answer-controls">
            <textarea id="answer-textarea" name="answer" rows={3} maxLength={4000} value={draft}
              onChange={(event) => { setDraft(event.target.value); setLocalError(""); }}
              onKeyDown={(event) => {
                if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) {
                  event.preventDefault(); event.currentTarget.form?.requestSubmit();
                }
              }}
              placeholder={direct ? "Write your defense answer. This submission will not request clarification." : "Answer, or ask this panelist to repeat, simplify, or give an example…"} aria-describedby="answer-status" />
            <button type="submit" disabled={previewMode || !connected || waitingForAnswerAck}>
              {previewMode ? "Preview only" : waitingForAnswerAck ? "Sending…" : probing ? direct ? "Submit reply directly" : "Submit reply" : direct ? "Submit answer directly" : "Submit answer"}
            </button>
          </div>
          <p id="answer-status" role={localError || actionError || roomState?.error ? "alert" : "status"}>
            {localError || actionError || roomState?.error || (previewMode ? "Mock preview · answers are disabled."
              : connected ? direct ? "Submitted text will be recorded as your answer without AI interpretation. Ctrl/⌘ + Enter to submit." : "A clarification keeps this question open. Ctrl/⌘ + Enter to submit."
              : "Reconnecting before you can submit…")}
          </p>
          {probing && recoveryAvailable && <button type="button" disabled={!connected || previewMode || waitingForAnswerAck} onClick={() => onSendEvent({ type: "finish_probe", turn: turnIndex, probe_id: probe?.id })}>Continue with original answer</button>}
        </form>
      ) : (
        <p id="answer-status" role={actionError ? "alert" : "status"}>
          {actionError || (submission.reviewing || submission.retrying
            ? submission.retrying ? reviewGuidance : submission.reviewGuidance
            : turnIndex >= 0
            ? presentation.teammateInstruction
            : presentation.guidance)}
        </p>
      )}
    </section>
  );
}

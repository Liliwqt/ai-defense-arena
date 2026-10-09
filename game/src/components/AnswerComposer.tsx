import { useEffect, useState } from "react";
import type { RoomState } from "../types";

interface AnswerComposerProps {
  roomState: RoomState | null;
  connected: boolean;
  previewMode: boolean;
  waitingForAnswerAck: boolean;
  actionError: string | null;
  actionErrorReason?: string | null;
  onSendEvent: (payload: Record<string, unknown>) => boolean;
}

function currentQuestionIndex(state: RoomState | null): number {
  if (!state || !["question", "probe", "interpreting", "interpretation_retry"].includes(state.phase)) return -1;
  for (let index = state.turns.length - 1; index >= 0; index--) {
    const turn = state.turns[index];
    if (turn.question && (!turn.answer || turn.probe?.status === "pending") && !turn.timed_out) return index;
  }
  return -1;
}

function waitingText(state: RoomState | null): string {
  if (!state) return "Create or join a room to begin your defense.";
  if (state.phase === "lobby") return state.self_is_host
    ? "Start the defense from Controls when your team is ready."
    : "Waiting for the host to start the defense.";
  if (state.phase === "interpreting") return state.clock_paused === false ? "The panelist is reading the submission. The answer clock is running." : "The panelist is reading the submission. The answer clock is paused.";
  if (state.phase === "interpretation_retry") return state.clock_paused === false ? "Interpretation failed. The answer clock is running; use the saved submission as an answer." : "Interpretation failed. Retry or explicitly use the saved submission as an answer.";
  if (state.phase === "generating") return "The panel is preparing the next question…";
  if (state.phase === "retry") return state.self_is_host
    ? "Question generation failed. The previous turn is saved; retry from Controls."
    : "Question generation failed. The previous turn is saved; the host can retry.";
  if (state.phase === "complete") {
    if (state.feedback_status === "generating") return "Preparing the team's coaching report…";
    if (state.feedback_status === "failed") return state.self_is_host
      ? "Coaching failed. Retry from Controls."
      : "Coaching failed. The host can retry.";
    return "Defense complete. Open Transcript to review answers, timeouts, and coaching.";
  }
  return "Waiting for the next question…";
}

export function AnswerComposer({ roomState, connected, previewMode, waitingForAnswerAck, actionError, actionErrorReason, onSendEvent }: AnswerComposerProps) {
  const [draft, setDraft] = useState("");
  const [localError, setLocalError] = useState("");
  const [writeRecovery, setWriteRecovery] = useState(false);
  const [interpretationLimited, setInterpretationLimited] = useState(false);
  const turnIndex = currentQuestionIndex(roomState);
  const probe = turnIndex >= 0 ? roomState?.turns[turnIndex]?.probe : null;
  const probing = probe?.status === "pending";
  const turnKey = `${roomState?.room_code ?? ""}:${turnIndex}:${turnIndex >= 0 ? roomState?.turns[turnIndex]?.question ?? "" : ""}:${probe?.id ?? ""}`;
  const chosen = turnIndex >= 0 && roomState?.selected_seat != null && roomState.selected_seat === roomState.self_seat;
  const canWrite = chosen && (roomState?.phase === "probe" || roomState?.phase === "question" || (roomState?.phase === "interpretation_retry" && writeRecovery) || (roomState?.phase === "interpreting" && roomState.clock_paused === false));
  const clarifications = turnIndex >= 0 ? roomState?.turns[turnIndex]?.clarifications?.length ?? 0 : 0;
  const allClarifications = clarifications + (probe?.clarifications.length ?? 0);
  const direct = interpretationLimited || allClarifications >= 2 || roomState?.interpretation_attempts_left === 0 || roomState?.phase === "interpretation_retry" || roomState?.phase === "interpreting";
  const chosenName = roomState?.players.find((player) => player.seat === roomState.selected_seat)?.name;

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
      {roomState?.phase === "interpretation_retry" && !canWrite && (chosen || roomState.self_is_host) ? (
        <div className="submission-retry" role="status">
          <p>{roomState.error || "Could not interpret the submission."} The submission and remaining answer time are saved.</p>
          {roomState.my_pending_submission && <p className="pending-text">{roomState.my_pending_submission}</p>}
          <div className="submission-retry-actions">
            <button type="button" disabled={!connected || previewMode || roomState.interpretation_attempts_left === 0} onClick={() => onSendEvent({ type: "retry_interpretation" })}>Retry panelist</button>
            {chosen && <button type="button" disabled={!connected || previewMode} onClick={() => setWriteRecovery(true)}>Write a new answer</button>}
            {chosen && <button type="button" disabled={!connected || previewMode || !roomState.my_pending_submission} onClick={() => onSendEvent({ type: "use_pending_as_answer" })}>{probing ? "Use this as my reply" : "Use this as my answer"}</button>}
            {chosen && probing && <button type="button" disabled={!connected || previewMode} onClick={() => onSendEvent({ type: "finish_probe", turn: turnIndex, probe_id: probe.id })}>Continue with original answer</button>}
          </div>
          {actionError && <p role="alert">{actionError}</p>}
        </div>
      ) : canWrite ? (
        <form id="answer-form" onSubmit={submitAnswer}>
          <label htmlFor="answer-textarea">{probing ? "Reply to the panelist probe" : "You were chosen to answer"}{direct ? "" : " or clarify"} question {turnIndex + 1} · {Math.max(0, 2 - allClarifications)} clarifications left</label>
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
          {probing && (interpretationLimited || roomState?.interpretation_attempts_left === 0 || roomState?.phase === "interpretation_retry") && <button type="button" disabled={!connected || previewMode || waitingForAnswerAck} onClick={() => onSendEvent({ type: "finish_probe", turn: turnIndex, probe_id: probe.id })}>Continue with original answer</button>}
        </form>
      ) : (
        <p id="answer-status" role={actionError ? "alert" : "status"}>
          {actionError || (roomState?.phase === "interpreting" || roomState?.phase === "interpretation_retry"
            ? waitingText(roomState)
            : turnIndex >= 0
            ? chosenName ? `${chosenName} was chosen to answer. Use Team Chat to help them.` : "Waiting for a defender to reconnect. The answer clock keeps running."
            : waitingText(roomState))}
        </p>
      )}
    </section>
  );
}

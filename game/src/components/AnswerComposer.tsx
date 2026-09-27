import { useEffect, useState } from "react";
import type { RoomState } from "../types";

interface AnswerComposerProps {
  roomState: RoomState | null;
  connected: boolean;
  previewMode: boolean;
  waitingForAnswerAck: boolean;
  actionError: string | null;
  onSendEvent: (payload: Record<string, unknown>) => boolean;
}

function currentQuestionIndex(state: RoomState | null): number {
  if (state?.phase !== "question") return -1;
  for (let index = state.turns.length - 1; index >= 0; index--) {
    const turn = state.turns[index];
    if (turn.question && !turn.answer && !turn.timed_out) return index;
  }
  return -1;
}

function waitingText(state: RoomState | null): string {
  if (!state) return "Create or join a room to begin your defense.";
  if (state.phase === "lobby") return state.self_is_host
    ? "Start the defense from Controls when your team is ready."
    : "Waiting for the host to start the defense.";
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

export function AnswerComposer({ roomState, connected, previewMode, waitingForAnswerAck, actionError, onSendEvent }: AnswerComposerProps) {
  const [draft, setDraft] = useState("");
  const [localError, setLocalError] = useState("");
  const turnIndex = currentQuestionIndex(roomState);
  const turnKey = `${roomState?.room_code ?? ""}:${turnIndex}:${turnIndex >= 0 ? roomState?.turns[turnIndex]?.question ?? "" : ""}`;
  const chosen = turnIndex >= 0 && roomState?.selected_seat != null && roomState.selected_seat === roomState.self_seat;
  const chosenName = roomState?.players.find((player) => player.seat === roomState.selected_seat)?.name;

  useEffect(() => { setDraft(""); setLocalError(""); }, [turnKey]);

  function submitAnswer(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (previewMode || !chosen || waitingForAnswerAck) return;
    const answer = draft.trim();
    if (!answer) { setLocalError("Write an answer before submitting."); return; }
    setLocalError("");
    if (!onSendEvent({ type: "submit_answer", turn: turnIndex, answer })) {
      setLocalError("Could not send your answer. Check the connection and try again.");
    }
  }

  return (
    <section id="answer-composer" aria-label="Answer area">
      {chosen ? (
        <form id="answer-form" onSubmit={submitAnswer}>
          <label htmlFor="answer-textarea">You were chosen to answer question {turnIndex + 1}</label>
          <div className="answer-controls">
            <textarea id="answer-textarea" name="answer" rows={3} maxLength={4000} value={draft}
              onChange={(event) => { setDraft(event.target.value); setLocalError(""); }}
              onKeyDown={(event) => {
                if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) {
                  event.preventDefault(); event.currentTarget.form?.requestSubmit();
                }
              }}
              placeholder="Explain your team's decision…" aria-describedby="answer-status" />
            <button type="submit" disabled={previewMode || !connected || waitingForAnswerAck}>
              {previewMode ? "Preview only" : waitingForAnswerAck ? "Sending…" : "Submit answer"}
            </button>
          </div>
          <p id="answer-status" role={localError || actionError ? "alert" : "status"}>
            {localError || actionError || (previewMode ? "Mock preview · answers are disabled."
              : connected ? "Your answer must arrive before time runs out. Ctrl/⌘ + Enter to submit."
              : "Reconnecting before you can submit…")}
          </p>
        </form>
      ) : (
        <p id="answer-status" role={actionError ? "alert" : "status"}>
          {actionError || (turnIndex >= 0
            ? chosenName ? `${chosenName} was chosen to answer. Use Team Chat to help them.` : "Waiting for a defender to reconnect. The answer clock keeps running."
            : waitingText(roomState))}
        </p>
      )}
    </section>
  );
}

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
    if (state.turns[index].question && !state.turns[index].answer) return index;
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
    ? "Question generation failed. Your answer is saved; retry from Controls."
    : "Question generation failed. Your answer is saved; the host can retry.";
  if (state.phase === "complete") {
    if (state.feedback_status === "generating") return "Preparing the team's coaching report…";
    if (state.feedback_status === "failed") return state.self_is_host
      ? "Coaching failed. Retry from Controls."
      : "Coaching failed. The host can retry.";
    return "Defense complete. Open Transcript to review the answers and coaching report.";
  }
  return "Waiting for the next question…";
}

export function AnswerComposer({ roomState, connected, previewMode, waitingForAnswerAck, actionError, onSendEvent }: AnswerComposerProps) {
  const [draft, setDraft] = useState("");
  const [localError, setLocalError] = useState("");
  const turnIndex = currentQuestionIndex(roomState);
  const currentTurn = turnIndex >= 0 ? roomState?.turns[turnIndex] : null;
  const turnKey = `${roomState?.room_code ?? ""}:${turnIndex}:${turnIndex >= 0 ? roomState?.turns[turnIndex]?.question ?? "" : ""}`;

  useEffect(() => {
    setDraft("");
    setLocalError("");
  }, [turnKey]);

  function submitAnswer(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (previewMode) return;
    if (waitingForAnswerAck) return;
    const answer = draft.trim();
    if (!answer) {
      setLocalError("Write an answer before submitting.");
      return;
    }
    setLocalError("");
    if (!onSendEvent({ type: "submit_answer", turn: turnIndex, answer })) {
      setLocalError("Could not send your answer. Check the connection and try again.");
    }
  }

  return (
    <section id="answer-composer" aria-label="Answer area">
      {turnIndex >= 0 ? (
        <>
        {currentTurn && <div className="answer-context">
          <p className="answer-context-kicker">{currentTurn.panelist} · Question {turnIndex + 1}</p>
          <p className="answer-context-question">{currentTurn.question}</p>
          <p className="answer-context-source">{currentTurn.filename}:{currentTurn.evidence_line} · <code>{currentTurn.evidence_text}</code></p>
        </div>}
        <form id="answer-form" onSubmit={submitAnswer}>
          <label htmlFor="answer-textarea">Your answer</label>
          <div className="answer-controls">
            <textarea
              id="answer-textarea"
              name="answer"
              rows={8}
              maxLength={4000}
              value={draft}
              onChange={(event) => { setDraft(event.target.value); setLocalError(""); }}
              onKeyDown={(event) => {
                if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) {
                  event.preventDefault();
                  event.currentTarget.form?.requestSubmit();
                }
              }}
              placeholder="Explain your team's decision…"
              aria-describedby="answer-status"
            />
            <button type="submit" disabled={previewMode || !connected || waitingForAnswerAck}>
              {previewMode ? "Preview only" : waitingForAnswerAck ? "Sending…" : "Submit answer"}
            </button>
          </div>
          <p id="answer-status" role={localError || actionError ? "alert" : "status"}>
            {localError || actionError || (previewMode
              ? "Mock preview · answers are disabled."
              : connected
              ? "Any teammate may answer. First valid submission wins. Ctrl/⌘ + Enter to submit."
              : "Reconnecting before you can submit…")}
          </p>
        </form>
        </>
      ) : (
        <p id="answer-status" role="status">
          {previewMode && turnIndex >= 0 ? "Mock preview · answers are disabled." : waitingText(roomState)}
        </p>
      )}
    </section>
  );
}

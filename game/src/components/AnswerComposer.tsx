import {useVoiceCaptureSupported} from "../audio/nativeCapture";
import { VoiceAnswer } from "./VoiceAnswer";
import { WaitingIndicator } from "./WaitingIndicator";
import { OpeningChoice } from "./OpeningChoice";
import { useEffect, useState } from "react";
import type { RoomState } from "../types";
import { useTabDraft } from "../hooks/useTabDraft";

import { deriveRoomPresentation, questionRecoveryAction, type RoomPresentation } from "../lib/roomPresentation";

interface AnswerComposerProps {
  active?: boolean;
  playerToken?: string | null;
  presentation?: RoomPresentation;
  roomState: RoomState | null;
  connected: boolean;
  previewMode: boolean;
  waitingForAnswerAck: boolean;
  actionError: string | null;
  actionErrorReason?: string | null;
  onSendEvent: (payload: Record<string, unknown>) => boolean;
}

export function AnswerComposer({ active = true, playerToken, roomState, connected, previewMode, waitingForAnswerAck, actionError, actionErrorReason, onSendEvent, presentation = deriveRoomPresentation(roomState) }: AnswerComposerProps) {
  const voiceAvailable = useVoiceCaptureSupported();
  const current = roomState?.turns.at(-1);
  const inputScope = JSON.stringify([roomState?.room_code, roomState?.defense_view_id, roomState?.turns.length, current?.probe?.id ?? "answer",
    current?.probe ? current.probe.status : current?.answer || current?.timed_out || current?.resolved ? "resolved" : "open", roomState?.selected_seat, !!roomState?.my_pending_submission]);
  const [draft, setDraft] = useTabDraft("answer", roomState?.my_pending_submission ?? "", { room: true, marker: inputScope });
  const [localError, setLocalError] = useState("");
  const [voiceMode, setVoiceMode] = useState(false);
  const [confirmVoice, setConfirmVoice] = useState(false);
  useEffect(()=>{if(!voiceAvailable){setVoiceMode(false);setConfirmVoice(false);}},[voiceAvailable]);
  const [writeRecovery, setWriteRecovery] = useState(false);
  const [interpretationLimited, setInterpretationLimited] = useState(false);
  const [questionRetryPending, setQuestionRetryPending] = useState(false);
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

  useEffect(() => { setLocalError(""); setWriteRecovery(false); setInterpretationLimited(false); }, [turnKey, roomState?.defense_view_id]);
  useEffect(() => {
    if (actionErrorReason === "ai_admission") setInterpretationLimited(true);
  }, [actionErrorReason]);
  useEffect(() => {
    setLocalError("");
    const acceptedRequest = current?.probe?.status === "pending" ? current.probe.clarifications.at(-1)?.request : current?.clarifications?.at(-1)?.request;
    // An acknowledged clarification clears only the text actually submitted;
    // a newer unsent answer on the same question must survive it.
    if (acceptedRequest && draft.trim() === acceptedRequest.trim()) setDraft("");
  }, [allClarifications, turnKey]);
  useEffect(() => { setQuestionRetryPending(false); }, [roomState?.phase, roomState?.room_code]);
  useEffect(() => { if (actionError) setQuestionRetryPending(false); }, [actionError]);

  useEffect(() => { setVoiceMode(false); setConfirmVoice(false); }, [inputScope]);

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

  const waiting = presentation.waiting;
  return (
    <section id="answer-composer" aria-label="Answer area">
      {roomState?.opening_repeated ? <OpeningChoice state={roomState} connected={connected} previewMode={previewMode} actionError={actionError} onSendEvent={onSendEvent} /> : presentation.controls.questionRetry && roomState ? (
        <div className="submission-retry">
          {localError || actionError || !connected
            ? <p role="status">{localError || actionError || "Reconnecting… Your saved turns are retained."}</p>
            : <WaitingIndicator label={waiting?.label ?? "Waiting to retry…"} active={false}
                detail={[waiting?.detail, presentation.guidance].filter(Boolean).join(" ")} />}
          {roomState.self_is_host && <button type="button"
            disabled={recoveryDisabled || questionRetryPending || !presentation.controls.questionRetryAvailable}
            onClick={() => {
              setLocalError("");
              if (onSendEvent({ type: "retry" })) setQuestionRetryPending(true);
              else setLocalError("Could not send the retry. Reconnect and try again; your saved turns are retained.");
            }}>
            {questionRecoveryAction(roomState) ?? (roomState.turns.some(turn => turn.answer || turn.timed_out) ? "Retry next question" : "Retry first question")}
          </button>}
        </div>
      ) : submission.showRecovery && !canWrite && roomState ? (
        <div className="submission-retry">
          {waiting
            ? <WaitingIndicator label={waiting.label} active={false}
                detail={[waiting.detail, reviewGuidance].filter(Boolean).join(" ")} />
            : <p role="status">{reviewGuidance}</p>}
          {roomState.my_pending_submission && <p className="pending-text">{roomState.my_pending_submission}</p>}
          <div className="submission-retry-actions">
            <button type="button" disabled={recoveryDisabled || !submission.retryAvailable} onClick={() => onSendEvent({ type: "retry_interpretation" })}>Retry panelist</button>
            {chosen && <button type="button" disabled={recoveryDisabled} onClick={() => setWriteRecovery(true)}>Write a new answer</button>}
            {chosen && <button type="button" disabled={recoveryDisabled || !submission.savedAvailable} onClick={() => onSendEvent({ type: "use_pending_as_answer" })}>{probing ? "Use this as my reply" : "Use this as my answer"}</button>}
            {chosen && probing && <button type="button" disabled={recoveryDisabled} onClick={() => onSendEvent({ type: "finish_probe", turn: turnIndex, probe_id: probe?.id })}>Continue with original answer</button>}
          </div>
          {actionError && <p role="alert">{actionError}</p>}
        </div>
      ) : canWrite && voiceMode && voiceAvailable && roomState ? <VoiceAnswer state={roomState} token={playerToken}
        active={active && connected && !previewMode} onSend={onSendEvent} direct={direct}
        actionError={actionError} onTyping={() => {setDraft("");setVoiceMode(false);}} /> : canWrite ? (
        <form id="answer-form" onSubmit={submitAnswer}>
          {roomState?.defense_type !== "code" && roomState?.voice?.enabled && voiceAvailable && <div className="voice-mode-choice">
            {confirmVoice ? <><p>Your unsent typed answer will be discarded when you switch.</p><button type="button" onClick={() => {setDraft("");setConfirmVoice(false);setVoiceMode(true);}}>Discard typed draft and use voice</button><button type="button" onClick={() => setConfirmVoice(false)}>Keep typing</button></>
              : <button type="button" disabled={!connected || previewMode || waitingForAnswerAck} onClick={() => {if(draft.trim())setConfirmVoice(true);else setVoiceMode(true);}}>{roomState?.my_voice_draft ? "Review unsent voice draft" : "Use voice"}</button>}
          </div>}
          {roomState?.defense_type !== "code" && roomState?.voice?.enabled && !voiceAvailable && <p className="control-help">Voice is unavailable in this app/browser. Typing still works.</p>}
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
        actionError ? <p id="answer-status" role="alert">{actionError}</p>
          : waiting && (waiting.active || submission.retrying)
            ? <WaitingIndicator label={waiting.label} active={waiting.active}
                detail={[waiting.detail, submission.reviewing ? submission.reviewGuidance : ""].filter(Boolean).join(" ")}
                startedAtMs={waiting.startedAtMs} serverNowMs={roomState?.server_now_ms} />
            : <p id="answer-status" role="status">
              {turnIndex >= 0 ? presentation.teammateInstruction : presentation.guidance}
            </p>
      )}
    </section>
  );
}

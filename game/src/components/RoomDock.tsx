import { useEffect, useRef, useState } from "react";
import { AnswerComposer } from "./AnswerComposer";
import type { RoomState } from "../types";

interface RoomDockProps {
  roomState: RoomState | null;
  connected: boolean;
  previewMode: boolean;
  waitingForAnswerAck: boolean;
  actionError: string | null;
  actionErrorReason?: string | null;
  onSendEvent: (payload: Record<string, unknown>) => boolean;
}

function VotePanel({ state, connected, previewMode, actionError, onSendEvent }: {
  state: RoomState;
  connected: boolean;
  previewMode: boolean;
  actionError: string | null;
  onSendEvent: RoomDockProps["onSendEvent"];
}) {
  const [localError, setLocalError] = useState("");
  return (
    <div className="vote-panel" aria-label="Choose a defender">
      <p className="vote-instruction">Choose who will answer. You can change your vote until the clock reaches zero.</p>
      <div className="vote-choices">
        {state.players.filter((player) => player.online).map((player) => (
          <button key={player.seat} type="button" className={state.my_vote === player.seat ? "selected" : ""}
            aria-pressed={state.my_vote === player.seat} disabled={!connected || previewMode}
            onClick={() => {
              setLocalError("");
              if (!onSendEvent({ type: "cast_vote", seat: player.seat })) setLocalError("Could not send your vote. Reconnect and try again.");
            }}>
            <span>{player.name}{player.seat === state.self_seat ? " (you)" : ""}</span>
            <strong>{state.vote_counts?.[String(player.seat)] ?? 0}</strong>
          </button>
        ))}
      </div>
      {(localError || actionError) && <p className="dock-error" role="alert">{localError || actionError}</p>}
    </div>
  );
}

function TeamChat({ state, connected, previewMode, actionError, onSendEvent, visible }: {
  state: RoomState | null;
  connected: boolean;
  previewMode: boolean;
  actionError: string | null;
  onSendEvent: RoomDockProps["onSendEvent"];
  visible: boolean;
}) {
  const [draft, setDraft] = useState("");
  const [localError, setLocalError] = useState("");
  const listRef = useRef<HTMLDivElement>(null);
  const newestId = state?.chat?.at(-1)?.id ?? 0;
  useEffect(() => { if (visible && listRef.current) listRef.current.scrollTop = listRef.current.scrollHeight; }, [visible, newestId]);
  useEffect(() => { setDraft(""); setLocalError(""); }, [state?.room_code]);

  function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const text = draft.trim();
    if (!text) { setLocalError("Write a team message first."); return; }
    if (text.length > 500) { setLocalError("Keep team messages under 500 characters."); return; }
    setLocalError("");
    if (onSendEvent({ type: "send_chat", text })) setDraft("");
    else setLocalError("Could not send your message. Reconnect and try again.");
  }

  return (
    <section className="team-chat" aria-label="Private team chat">
      <div className="chat-messages" ref={listRef} role="log" aria-live="polite" aria-relevant="additions text">
        {!state?.chat?.length && <p className="chat-empty">Only your team sees this chat. It is not sent to the AI panel.</p>}
        {state?.chat?.map((item) => <p key={item.id} className="chat-message">
          <strong>{item.name}{item.seat === state.self_seat ? " (you)" : ""}:</strong> {item.text}
        </p>)}
      </div>
      <form onSubmit={submit} className="chat-form">
        <label htmlFor="chat-input" className="sr-only">Team message</label>
        <input id="chat-input" value={draft} maxLength={500} disabled={!state || !connected || previewMode}
          onChange={(event) => { setDraft(event.target.value); setLocalError(""); }} placeholder="Message your team…" />
        <button type="submit" disabled={!state || !connected || previewMode}>Send</button>
      </form>
      {(localError || actionError) && <p className="dock-error" role="alert">{localError || actionError}</p>}
    </section>
  );
}

export function RoomDock({ roomState, connected, previewMode, waitingForAnswerAck, actionError, actionErrorReason, onSendEvent }: RoomDockProps) {
  const [tab, setTab] = useState<"action" | "chat">("action");
  const [seenChatId, setSeenChatId] = useState(0);
  const latestChatId = roomState?.chat?.at(-1)?.id ?? 0;
  const turnCount = roomState?.turns.length ?? 0;
  useEffect(() => { setTab("action"); }, [roomState?.room_code, roomState?.phase, turnCount]);
  useEffect(() => { setSeenChatId(latestChatId); }, [roomState?.room_code]);
  useEffect(() => { if (tab === "chat") setSeenChatId(latestChatId); }, [tab, latestChatId]);
  const unread = (roomState?.chat ?? []).filter((message) => message.id > seenChatId).length;
  function handleDockTabKey(event: React.KeyboardEvent<HTMLButtonElement>) {
    if ((event.key !== "ArrowLeft" && event.key !== "ArrowRight") || !roomState) return;
    event.preventDefault();
    const next = tab === "action" ? "chat" : "action";
    setTab(next);
    const tabs = event.currentTarget.parentElement?.querySelectorAll<HTMLButtonElement>("[role=tab]");
    tabs?.[next === "action" ? 0 : 1]?.focus();
  }
  return (
    <div id="room-dock" className="room-dock">
      <div className="dock-tabs" role="tablist" aria-label="Room conversation and answer">
        <button type="button" role="tab" aria-selected={tab === "action"} aria-controls="dock-action" tabIndex={tab === "action" ? 0 : -1} onKeyDown={handleDockTabKey}
          onClick={() => setTab("action")}>Vote / Answer</button>
        <button type="button" role="tab" aria-selected={tab === "chat"} aria-controls="dock-chat" tabIndex={tab === "chat" ? 0 : -1} onKeyDown={handleDockTabKey}
          disabled={!roomState} onClick={() => setTab("chat")}>Team chat{unread > 0 ? ` (${unread})` : ""}</button>
      </div>
      <div id="dock-action" role="tabpanel" hidden={tab !== "action"} className="dock-content">
        {roomState?.phase === "voting" ? <VotePanel state={roomState} connected={connected} previewMode={previewMode}
          actionError={actionError} onSendEvent={onSendEvent} /> :
          <AnswerComposer roomState={roomState} connected={connected} previewMode={previewMode}
            waitingForAnswerAck={waitingForAnswerAck} actionError={actionError} actionErrorReason={actionErrorReason} onSendEvent={onSendEvent} />}
      </div>
      <div id="dock-chat" role="tabpanel" hidden={tab !== "chat"} className="dock-content">
        <TeamChat state={roomState} connected={connected} previewMode={previewMode} actionError={actionError}
          onSendEvent={onSendEvent} visible={tab === "chat"} />
      </div>
    </div>
  );
}

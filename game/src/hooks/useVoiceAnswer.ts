import { useEffect, useRef, useState } from 'react';
import { startCapture } from '../audio/capture';
import type { RoomState } from '../types';

type Status = 'idle' | 'starting' | 'listening' | 'finalizing' | 'ready' | 'sending' | 'failed';
export function useVoiceAnswer(state: RoomState, token: string | null | undefined, active: boolean,
    onSend: (payload: Record<string, unknown>) => boolean, direct: boolean, actionError: string | null) {
  const [status, setStatus] = useState<Status>('idle');
  const [text, setText] = useState('');
  const [finalized, setFinalized] = useState('');
  const [error, setError] = useState('');
  const [remaining, setRemaining] = useState(state.voice?.remaining_ms ?? 0);
  const version = useRef(0);
  const socket = useRef<WebSocket | null>(null);
  const capture = useRef<Awaited<ReturnType<typeof startCapture>> | null>(null);
  const currentStatus = useRef<Status>('idle');
  const attempt = useRef('');
  const requestedSend = useRef(false);
  const readyText = useRef('');
  const flushing = useRef(false);
  const startupTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const scope = `${state.room_code}:${state.defense_view_id}:${state.turns.length}:${state.selected_seat}`;
  const latest = useRef({ state, onSend, direct }); latest.current = { state, onSend, direct };
  function change(value: Status) { currentStatus.current = value; setStatus(value); }
  function stopMedia() { capture.current?.stop(); capture.current = null; }
  function cancel() {
    version.current++; requestedSend.current = false; flushing.current = false; readyText.current = "";
    if (startupTimer.current) clearTimeout(startupTimer.current);
    stopMedia();
    const previous = socket.current; socket.current = null;
    try { if (previous?.readyState === WebSocket.OPEN) previous.send(JSON.stringify({type:'cancel'})); } catch { /* Already disconnected. */ }
    previous?.close(); attempt.current = ''; change('idle'); setText(''); setFinalized('');
  }
  function fail(message: string) {
    cancel(); setError(message); change('failed');
  }
  useEffect(() => {
    if (!active) cancel();
    return () => { version.current++; requestedSend.current = false; if(startupTimer.current)clearTimeout(startupTimer.current); stopMedia(); socket.current?.close(); socket.current = null; };
  }, [scope, active]);
  useEffect(() => {
    const stop = () => { if (currentStatus.current !== 'idle') fail('Capture stopped while away. Nothing was submitted automatically; record again or type.'); };
    const visibility = () => { if (document.visibilityState === 'hidden') stop(); };
    document.addEventListener('visibilitychange', visibility); window.addEventListener('pagehide', stop); window.addEventListener('defense-native-background', stop);
    return () => { document.removeEventListener('visibilitychange', visibility); window.removeEventListener('pagehide', stop); window.removeEventListener('defense-native-background', stop); };
  }, []);
  useEffect(() => {
    if (actionError && currentStatus.current === 'sending') { requestedSend.current = false; setError(actionError); change('ready'); }
  }, [actionError]);
  function submit(finalText: string) {
    if (!requestedSend.current || currentStatus.current === 'sending') return;
    requestedSend.current = false;
    const {state: room, onSend: send, direct: submitDirect} = latest.current;
    if (!finalText.trim() || finalText.length > 4000) { fail('The transcript is empty or exceeds 4000 characters. Nothing was submitted; record again or type.'); return; }
    change('sending');
    if (!send({type:submitDirect?'submit_direct_answer':'submit_answer',turn:room.turns.length-1,answer:finalText,voice_attempt:attempt.current})) {
      setError('Could not send. Reconnect and record again or type.'); change('ready');
    }
  }
  async function start() {
    if (!active || !token || !['idle','failed'].includes(currentStatus.current)) return;
    cancel(); setError(''); change('starting');
    const id = version.current;
    const isCurrent = () => id === version.current;
    try {
      capture.current = await startCapture(frame => {
        const ws = socket.current;
        if (!isCurrent() || !['listening','finalizing'].includes(currentStatus.current) || ws?.readyState !== WebSocket.OPEN) return;
        if (ws.bufferedAmount > 19200) { fail('Audio connection is too slow. Nothing was submitted; use typing.'); return; }
        try { ws.send(frame); } catch { fail("Audio connection failed. Nothing was submitted; use typing."); }
      }, () => { if (isCurrent()) fail('Microphone stopped unexpectedly. Nothing was submitted; use typing.'); }, isCurrent);
      if (!isCurrent()) { stopMedia(); return; }
      const ws = new WebSocket(`${location.protocol==='https:'?'wss:':'ws:'}//${location.host}/ws/${encodeURIComponent(state.room_code)}/speech`);
      socket.current = ws;
      startupTimer.current = setTimeout(() => { if(isCurrent())fail("Voice connection timed out. Nothing was submitted; use typing."); },8000);
      ws.addEventListener('open', () => { if (isCurrent()) ws.send(JSON.stringify({type:'start',token,turn:state.turns.length-1,view_id:state.defense_view_id})); });
      ws.addEventListener('message', event => {
        if (!isCurrent()) return;
        try {
          const message = JSON.parse(String(event.data));
          if (message.type === 'started') { if(startupTimer.current)clearTimeout(startupTimer.current); attempt.current = message.attempt_id; setRemaining(message.remaining_ms); change('listening'); }
          if (message.type === 'transcript' && currentStatus.current !== 'ready' && currentStatus.current !== 'sending') { setText(message.text); setFinalized(message.finalized_text); }
          if (message.type === 'allowance') {
            setRemaining(message.remaining_ms);
            if (message.capped) { stopMedia(); change('finalizing'); }
          }
          if (message.type === 'ready' && message.attempt_id === attempt.current && currentStatus.current !== 'sending') {
            readyText.current = message.text; setText(message.text); setFinalized(message.text);
            if(!flushing.current) { stopMedia(); change('ready'); submit(message.text); }
          }
          if (message.type === 'error' || message.type === 'stopped') fail(message.message || 'Voice stopped. Nothing was submitted; use typing.');
        } catch { fail('Invalid speech response. Nothing was submitted; use typing.'); }
      });
      ws.addEventListener('close', () => { if (isCurrent() && currentStatus.current !== 'sending') fail('Voice disconnected. Nothing was submitted; record again or type.'); });
      ws.addEventListener('error', () => { if (isCurrent()) fail('Voice connection failed. Nothing was submitted; use typing.'); });
    } catch (failure) {
      if (isCurrent()) fail(failure instanceof Error ? failure.message : 'Microphone permission denied. Use typing.');
    }
  }
  async function send() {
    if (!active || !['listening','ready'].includes(currentStatus.current) || requestedSend.current) return;
    requestedSend.current = true; setError('');
    if (currentStatus.current === 'ready') { submit(text); return; }
    change('finalizing'); flushing.current = true;
    const id = version.current;
    try {
      await capture.current?.finish(); capture.current = null;
      if (id !== version.current) return;
      flushing.current = false;
      if(readyText.current) { change('ready'); submit(readyText.current); return; }
      if (socket.current?.readyState !== WebSocket.OPEN) throw new Error('Voice disconnected before finalization. Nothing was submitted.');
      socket.current.send(JSON.stringify({type:'finalize'}));
    } catch (failure) { if (id === version.current) fail((failure as Error).message); }
  }
  return {status,text,finalized,error,remaining,start,send,cancel};
}

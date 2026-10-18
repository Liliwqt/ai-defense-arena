import { formatCountdown, useRoomCountdown } from '../hooks/useRoomCountdown';
import type { RoomState } from '../types';
import { useVoiceAnswer } from '../hooks/useVoiceAnswer';
export function VoiceAnswer({state,token,active,onSend,direct,actionError,onTyping}: {
  state:RoomState;token?:string|null;active:boolean;onSend:(payload:Record<string,unknown>)=>boolean;
  direct:boolean;actionError:string|null;onTyping:()=>void;
}) {
  const voice=useVoiceAnswer(state,token,active,onSend,direct,actionError);
  const seconds=useRoomCountdown(state);
  const busy=['starting','finalizing','sending'].includes(voice.status);
  return <section className="voice-answer" aria-label="Speaker desk">
    <div className="speaker-desk-heading"><span className="voice-answer-timer" aria-label="Answer deadline">Answer time {formatCountdown(seconds)}</span><strong>Speaker desk</strong><span>{formatCountdown(Math.ceil(voice.remaining/1000))} voice time left · shared by the team</span></div>
    <details className="voice-disclosure" open={voice.status==='idle'||voice.status==='failed'}><summary>Microphone and privacy</summary>
      <p>For spoken defense practice, use voice. Typing is always available. English pilot; Tagalog and Bisaya recognition are not yet verified.</p>
      <p>Audio streams to OpenAI only after Start mic. This app keeps no audio archive. OpenAI’s default abuse-monitoring retention is up to 30 days, with separate account controls and exceptions. Your submitted transcript stays with this room’s results.</p>
    </details>
    <label htmlFor="spoken-answer">Spoken answer</label>
    <textarea id="spoken-answer" readOnly value={voice.text} aria-describedby="voice-status" rows={6}
      onKeyDown={event=>{if(event.key==='Enter'&&(event.ctrlKey||event.metaKey)){event.preventDefault();void voice.send();}}}
      placeholder="Your recognized words appear here. They cannot be edited."/>
    <p id="voice-status" role="status" aria-live="polite">{voice.status==='starting'?'Starting microphone…':voice.status==='listening'?voice.text===voice.finalized?'Listening · words finalized so far, not submitted':'Listening · provisional words may change':voice.status==='finalizing'?'Finishing transcript…':voice.status==='ready'?'Final transcript · not submitted':voice.status==='sending'?'Waiting for answer acknowledgment…':'Start the mic when you are ready. Your answer timer keeps running.'}</p>
    <div className="voice-actions">
      {['idle','failed'].includes(voice.status)&&<button type="button" disabled={!active||!token||voice.remaining<=0} onClick={()=>void voice.start()}>Start mic</button>}
      {['listening','ready','finalizing','sending'].includes(voice.status)&&<button type="button" disabled={!active||busy} onClick={()=>void voice.send()}>Send voice answer</button>}
      {voice.status!=='idle'&&<button type="button" disabled={voice.status==='sending'} onClick={voice.cancel}>Discard and record again</button>}
      <button type="button" disabled={voice.status==='sending'} onClick={()=>{voice.cancel();onTyping();}}>Switch to typing</button>
    </div>
    {(voice.error||actionError)&&<p role="alert">{voice.error||actionError}</p>}
  </section>;
}

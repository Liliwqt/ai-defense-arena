import { act, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { App } from './App';
import { useAccount } from './hooks/useAccount';
import { useRoomSocket, type RoomSocketState } from './hooks/useRoomSocket';
import type { RoomState } from './types';
vi.mock('./hooks/useAccount', () => ({ useAccount: vi.fn() }));
vi.mock('./hooks/useRoomSocket', () => ({ useRoomSocket: vi.fn() }));
let roomSocket: RoomSocketState;
class SpeechSocket extends EventTarget {
  static OPEN = 1;
  static sockets: SpeechSocket[] = [];
  readyState = 1; bufferedAmount = 0; sent: unknown[] = [];
  constructor(public url: string) { super(); SpeechSocket.sockets.push(this); queueMicrotask(() => this.dispatchEvent(new Event('open'))); }
  send(message: string | ArrayBuffer) { this.sent.push(typeof message === 'string' ? JSON.parse(message) : message); }
  close() { this.readyState = 3; }
  event(value: unknown) { this.dispatchEvent(new MessageEvent('message', { data: JSON.stringify(value) })); }
}
const stopTrack = vi.fn();
let mediaTrack: EventTarget & {stop: typeof stopTrack};
const getUserMedia = vi.fn(async () => ({ getTracks: () => [mediaTrack] }));
class Context {
  sampleRate = 24000; destination = {};
  audioWorklet = { addModule: vi.fn(async () => {}) };
  createMediaStreamSource() { return { connect: vi.fn(), disconnect: vi.fn() }; }
  resume = vi.fn(async () => {}); close = vi.fn(async () => {});
}
class Worklet {
  static instance: Worklet;
  port = { onmessage: null as null | ((e: { data: unknown }) => void), postMessage: () => queueMicrotask(() => this.port.onmessage?.({ data: { type: 'flushed' } })) };
  connect = vi.fn(); disconnect = vi.fn(); addEventListener = vi.fn();
  constructor() { Worklet.instance = this; }
}
beforeEach(() => {
  mediaTrack=Object.assign(new EventTarget(),{stop:stopTrack});
  sessionStorage.clear(); window.history.replaceState(null, '', '/#/room'); SpeechSocket.sockets = [];
  vi.mocked(useAccount).mockReturnValue({ account: { authenticated: true, google_enabled: true, free_access: true }, error: '', refresh: vi.fn(async () => {}) });
  const state: RoomState = { room_code:'VOICE1', defense_view_id:'run-one', self_is_host:true,self_seat:0,
    players:[{seat:0,name:'Alex',online:true,is_host:true}],phase:'question',selected_seat:0,revision:1,error:null,
    files:['paper.md'],defense_type:'research',active_panelist:'Methodology Reviewer',feedback_status:'none',feedback:null,
    voice:{enabled:true,remaining_ms:600000,provider:'OpenAI',model:'gpt-live-transcribe',language:'en'},
    turns:[{panelist:'Methodology Reviewer',question:'Why this campus?',filename:'paper.md',evidence_line:1,evidence_text:'Campus pilot.',answer:null,answered_by:null}] };
  roomSocket={roomState:state,roomCode:'VOICE1',connected:true,knownHost:true,playerToken:'token',waitingForAnswerAck:false,
    actionError:null,actionErrorReason:null,sendEvent:vi.fn(()=>true),useRoom:vi.fn(),leaveRoom:vi.fn()};
  vi.mocked(useRoomSocket).mockImplementation(()=>roomSocket);
  Object.defineProperty(navigator,'mediaDevices',{configurable:true,value:{getUserMedia}});
  vi.stubGlobal('AudioContext',Context);vi.stubGlobal('AudioWorkletNode',Worklet);vi.stubGlobal('WebSocket',SpeechSocket);
});
afterEach(()=>{act(()=>window.dispatchEvent(new Event('pagehide')));vi.unstubAllGlobals();vi.restoreAllMocks();vi.clearAllMocks();});
it('captures explicitly, shows read-only words and finalizes once only after manual Send',async()=>{
  const view=render(<App/>);
  expect(getUserMedia).not.toHaveBeenCalled();
  await userEvent.click(screen.getByRole('button',{name:'Use voice'}));
  expect(screen.getByText(/30 days/)).toBeVisible();
  await userEvent.click(screen.getByRole('button',{name:'Start mic'}));
  expect(getUserMedia).toHaveBeenCalledTimes(1);
  const speech=SpeechSocket.sockets[0];
  await act(async()=>speech.event({type:'started',attempt_id:'attempt-1',remaining_ms:600000}));
  await act(async()=>speech.event({type:'transcript',text:'We plan a pilot',finalized_text:''}));
  const words=screen.getByRole('textbox',{name:'Spoken answer'});
  expect(words).toHaveAttribute('readonly');expect(words).not.toBeDisabled();expect(words).toHaveValue('We plan a pilot');
  expect(roomSocket.sendEvent).not.toHaveBeenCalled();
  await userEvent.click(screen.getByRole('button',{name:'Send voice answer'}));
  expect(screen.getByText('Finishing transcript…')).toBeVisible();
  expect(stopTrack).toHaveBeenCalled();
  await act(async()=>speech.event({type:'ready',attempt_id:'attempt-1',text:'We plan a campus pilot.'}));
  await act(async()=>speech.event({type:'ready',attempt_id:'attempt-1',text:'We plan a campus pilot.'}));
  expect(roomSocket.sendEvent).toHaveBeenCalledTimes(1);
  expect(roomSocket.sendEvent).toHaveBeenCalledWith({type:'submit_answer',turn:0,answer:'We plan a campus pilot.',voice_attempt:'attempt-1'});
  roomSocket.waitingForAnswerAck=true;view.rerender(<App/>);
  expect(speech.readyState).toBe(1);
  expect(screen.getByRole('textbox',{name:'Spoken answer'})).toHaveValue('We plan a campus pilot.');
});

it('requires explicit draft replacement and permits a fresh typed answer after mic denial',async()=>{
  getUserMedia.mockRejectedValueOnce(new DOMException('Microphone permission denied'));
  render(<App/>);
  await userEvent.type(screen.getByRole('textbox',{name:/Your turn/}),'Keep this typed answer.');
  await userEvent.click(screen.getByRole('button',{name:'Use voice'}));
  expect(screen.getByRole('textbox',{name:/Your turn/})).toHaveValue('Keep this typed answer.');
  expect(getUserMedia).not.toHaveBeenCalled();
  await userEvent.click(screen.getByRole('button',{name:'Keep typing'}));
  await userEvent.click(screen.getByRole('button',{name:'Use voice'}));
  await userEvent.click(screen.getByRole('button',{name:'Discard typed draft and use voice'}));
  await userEvent.click(screen.getByRole('button',{name:'Start mic'}));
  expect(await screen.findByRole('alert')).toHaveTextContent('permission denied');
  await userEvent.click(screen.getByRole('button',{name:'Switch to typing'}));
  expect(screen.getByRole('textbox',{name:/Your turn/})).toHaveValue('');
  expect(roomSocket.sendEvent).not.toHaveBeenCalled();
});

it('quota finalization never sends automatically and keyboard sends the ready text once',async()=>{
  render(<App/>);await userEvent.click(screen.getByRole('button',{name:'Use voice'}));
  await userEvent.click(screen.getByRole('button',{name:'Start mic'}));
  const speech=SpeechSocket.sockets[0];
  await act(async()=>speech.event({type:'started',attempt_id:'cap',remaining_ms:100}));
  await act(async()=>speech.event({type:'allowance',remaining_ms:0,capped:true}));
  expect(stopTrack).toHaveBeenCalled();
  await act(async()=>speech.event({type:'ready',attempt_id:'cap',text:'My final words.'}));
  expect(roomSocket.sendEvent).not.toHaveBeenCalled();
  screen.getByRole('textbox',{name:'Spoken answer'}).focus();
  await userEvent.keyboard('{Control>}{Enter}{/Control}');
  expect(roomSocket.sendEvent).toHaveBeenCalledTimes(1);
});

it('navigation stops capture, ignores old callbacks and never resumes the microphone',async()=>{
  render(<App/>);await userEvent.click(screen.getByRole('button',{name:'Use voice'}));
  await userEvent.click(screen.getByRole('button',{name:'Start mic'}));
  const speech=SpeechSocket.sockets[0];
  await act(async()=>speech.event({type:'started',attempt_id:'old',remaining_ms:600000}));
  await userEvent.click(screen.getByRole('button',{name:/Settings.*Controls/i}));
  expect(stopTrack).toHaveBeenCalled();expect(speech.readyState).toBe(3);
  await act(async()=>speech.event({type:'ready',attempt_id:'old',text:'Late text'}));
  await userEvent.click(screen.getByRole('button',{name:'Return to defense'}));
  expect(getUserMedia).toHaveBeenCalledTimes(1);
  expect(screen.getByRole('textbox',{name:'Spoken answer'})).toHaveValue('');
  expect(roomSocket.sendEvent).not.toHaveBeenCalled();
});

it('stops acquired tracks when audio context construction fails',async()=>{
  vi.stubGlobal('AudioContext',class { constructor(){throw new Error('Audio context unavailable');} });
  render(<App/>);await userEvent.click(screen.getByRole('button',{name:'Use voice'}));
  await userEvent.click(screen.getByRole('button',{name:'Start mic'}));
  expect(await screen.findByRole('alert')).toHaveTextContent('Audio context unavailable');
  expect(stopTrack).toHaveBeenCalled();expect(SpeechSocket.sockets).toHaveLength(0);
});

it('records a same-question probe reply with a separate identity and reply labels',async()=>{
  roomSocket.roomState={...roomSocket.roomState!,phase:'probe',turns:[{...roomSocket.roomState!.turns[0],answer:'Our original explanation.',answered_by:'Alex',
    input_provenance:{method:'voice',provider:'OpenAI',model:'gpt-live-transcribe',audio_ms:100},
    probe:{id:'probe-current',request:'Which comparison?',references:[],status:'pending',reply:null,clarifications:[]}}]};
  render(<App/>);
  await userEvent.click(screen.getByRole('button',{name:'Use voice'}));
  expect(screen.getByRole('textbox',{name:'Spoken reply'})).toHaveAttribute('readonly');
  await userEvent.click(screen.getByRole('button',{name:'Start mic'}));
  const speech=SpeechSocket.sockets[0];
  expect(speech.sent).toContainEqual({type:'start',token:'token',turn:0,view_id:'run-one',probe_id:'probe-current'});
  await act(async()=>speech.event({type:'started',attempt_id:'reply-attempt',remaining_ms:599900}));
  await userEvent.click(screen.getByRole('button',{name:'Send voice reply'}));
  await act(async()=>speech.event({type:'ready',attempt_id:'reply-attempt',text:'We will compare the measured waiting times.'}));
  expect(roomSocket.sendEvent).toHaveBeenCalledWith({type:'submit_probe_reply',turn:0,probe_id:'probe-current',answer:'We will compare the measured waiting times.',voice_attempt:'reply-attempt',direct:false});
});

it('retains only finalized unsent words across navigation and requires a fresh manual Send',async()=>{
  render(<App/>);await userEvent.click(screen.getByRole('button',{name:'Use voice'}));
  await userEvent.click(screen.getByRole('button',{name:'Start mic'}));
  const speech=SpeechSocket.sockets[0];
  await act(async()=>speech.event({type:'started',attempt_id:'saved',remaining_ms:100}));
  await act(async()=>speech.event({type:'allowance',remaining_ms:0,capped:true}));
  await act(async()=>speech.event({type:'ready',attempt_id:'saved',text:'A finalized unsent explanation.'}));
  await userEvent.click(screen.getByRole('button',{name:/Settings.*Controls/i}));
  expect(speech.readyState).toBe(3);
  await act(async()=>speech.event({type:'ready',attempt_id:'saved',text:'Obsolete injected replacement'}));
  await userEvent.click(screen.getByRole('button',{name:'Return to defense'}));
  expect(screen.getByRole('textbox',{name:'Spoken answer'})).toHaveValue('A finalized unsent explanation.');
  expect(roomSocket.sendEvent).not.toHaveBeenCalled();
  expect(getUserMedia).toHaveBeenCalledTimes(1);
  await userEvent.click(screen.getByRole('button',{name:'Send voice answer'}));
  expect(roomSocket.sendEvent).toHaveBeenCalledTimes(1);
  expect(roomSocket.sendEvent).toHaveBeenCalledWith({type:'submit_answer',turn:0,answer:'A finalized unsent explanation.',voice_attempt:'saved'});
});

it('restores a server-validated draft read-only after reconnect without replacing typed work',async()=>{
  const view=render(<App/>);
  await userEvent.type(screen.getByRole('textbox',{name:/Your turn/}),'My unrelated typed draft.');
  roomSocket={...roomSocket,connected:false};view.rerender(<App/>);
  roomSocket={...roomSocket,connected:true,roomState:{...roomSocket.roomState!,voice:{...roomSocket.roomState!.voice!,remaining_ms:599900},
    my_voice_draft:{attempt_id:'restored',text:'Verified final words.',turn:0,probe_id:null,view_id:'run-one'}}};
  view.rerender(<App/>);
  expect(screen.getByRole('textbox',{name:/Your turn/})).toHaveValue('My unrelated typed draft.');
  await userEvent.click(screen.getByRole('button',{name:'Review unsent voice draft'}));
  await userEvent.click(screen.getByRole('button',{name:'Discard typed draft and use voice'}));
  expect(screen.getByRole('textbox',{name:'Spoken answer'})).toHaveValue('Verified final words.');
  expect(getUserMedia).not.toHaveBeenCalled();expect(roomSocket.sendEvent).not.toHaveBeenCalled();
  await userEvent.click(screen.getByRole('button',{name:'Switch to typing'}));
  expect(screen.getByRole('textbox',{name:/Your turn/})).toHaveValue('');
  expect(roomSocket.sendEvent).toHaveBeenCalledWith({type:'discard_voice_draft',attempt_id:'restored'});
});

it('keeps typing available in older Android WebViews without the audio capability',()=>{
 vi.spyOn(navigator,'userAgent','get').mockReturnValue('Mozilla/5.0 (Linux; Android 13; Pixel; wv) AppleWebKit/537.36 Version/4.0 Chrome/120.0 Mobile Safari/537.36');
 render(<App/>);
 expect(screen.getByRole('textbox',{name:/Your turn/})).toBeVisible();
 expect(screen.queryByRole('button',{name:'Use voice'})).toBeNull();
 expect(getUserMedia).not.toHaveBeenCalled();
});

// Native media and speech remain fake; these exercise the rendered App boundary.
class NativeAudioPort {
  onmessage: ((event: {data:string})=>void)|null=null;
  messages: {type:string;id:string}[]=[];
  start() {} close() {}
  postMessage(raw:string) { this.messages.push(JSON.parse(raw)); }
  reply(type:'prepared'|'denied',id=this.messages.at(-1)!.id) {
    this.onmessage?.({data:JSON.stringify({type,id})});
  }
}
function nativeShell() {
  vi.spyOn(navigator,'userAgent','get').mockReturnValue('Mozilla/5.0 (Linux; Android 13; Pixel; wv) AppleWebKit/537.36 DefenseArenaAndroid/2');
}
function transferAudio(port:NativeAudioPort,source:MessageEventSource|null=null,origin='') {
  window.dispatchEvent(new MessageEvent('message',{data:'defense-audio-port-v1',ports:[port as unknown as MessagePort],source,origin}));
}
it('waits for a trusted top-page capability and explicit native preparation before capture',async()=>{
  nativeShell();render(<App/>);const port=new NativeAudioPort();
  await act(async()=>transferAudio(port,window,'https://external.example'));
  expect(screen.queryByRole('button',{name:'Use voice'})).toBeNull();
  await act(async()=>transferAudio(port));
  expect(getUserMedia).not.toHaveBeenCalled();expect(port.messages).toEqual([]);
  await userEvent.click(screen.getByRole('button',{name:'Use voice'}));
  await userEvent.click(screen.getByRole('button',{name:'Start mic'}));
  expect(port.messages).toEqual([{type:'prepare',id:expect.any(String)}]);
  expect(getUserMedia).not.toHaveBeenCalled();
  await act(async()=>port.reply('prepared'));
  expect(getUserMedia).toHaveBeenCalledTimes(1);
  const speech=SpeechSocket.sockets[0];
  await act(async()=>speech.event({type:'started',attempt_id:'native',remaining_ms:600000}));
  await act(async()=>speech.event({type:'transcript',text:'Our pilot',finalized_text:''}));
  expect(screen.getByRole('textbox',{name:'Spoken answer'})).toHaveAttribute('readonly');
  expect(roomSocket.sendEvent).not.toHaveBeenCalled();
  await userEvent.click(screen.getByRole('button',{name:'Send voice answer'}));
  expect(stopTrack).toHaveBeenCalled();expect(port.messages.at(-1)?.type).toBe('cancel');
  await act(async()=>speech.event({type:'ready',attempt_id:'native',text:'Our pilot uses measured waiting times.'}));
  expect(roomSocket.sendEvent).toHaveBeenCalledWith({type:'submit_answer',turn:0,answer:'Our pilot uses measured waiting times.',voice_attempt:'native'});
});
it('offers typing after native permission denial without capturing or connecting speech',async()=>{
  nativeShell();render(<App/>);const port=new NativeAudioPort();await act(async()=>transferAudio(port));
  await userEvent.click(screen.getByRole('button',{name:'Use voice'}));
  await userEvent.click(screen.getByRole('button',{name:'Start mic'}));
  await act(async()=>port.reply('denied'));
  expect(await screen.findByRole('alert')).toHaveTextContent('Microphone access was denied');
  expect(getUserMedia).not.toHaveBeenCalled();expect(SpeechSocket.sockets).toHaveLength(0);
  await userEvent.click(screen.getByRole('button',{name:'Switch to typing'}));
  expect(screen.getByRole('textbox',{name:/Your turn/})).toHaveValue('');
});
it('ignores a late native permission approval after backgrounding and requires a new start',async()=>{
  nativeShell();render(<App/>);const port=new NativeAudioPort();await act(async()=>transferAudio(port));
  await userEvent.click(screen.getByRole('button',{name:'Use voice'}));
  await userEvent.click(screen.getByRole('button',{name:'Start mic'}));
  const pendingId=port.messages[0].id;
  await act(async()=>window.dispatchEvent(new Event('defense-native-background')));
  await act(async()=>port.reply('prepared',pendingId));
  await act(async()=>window.dispatchEvent(new Event('defense-native-resume')));
  expect(getUserMedia).not.toHaveBeenCalled();expect(SpeechSocket.sockets).toHaveLength(0);
  expect(screen.getByRole('button',{name:'Start mic'})).toBeEnabled();
  expect(roomSocket.sendEvent).not.toHaveBeenCalled();
});
it('backgrounding stops native tracks and upstream forwarding without sending provisional words',async()=>{
  nativeShell();render(<App/>);const port=new NativeAudioPort();await act(async()=>transferAudio(port));
  await userEvent.click(screen.getByRole('button',{name:'Use voice'}));
  await userEvent.click(screen.getByRole('button',{name:'Start mic'}));
  await act(async()=>port.reply('prepared'));
  const speech=SpeechSocket.sockets[0];
  await act(async()=>speech.event({type:'started',attempt_id:'background',remaining_ms:600000}));
  await act(async()=>speech.event({type:'transcript',text:'Unfinished',finalized_text:''}));
  await act(async()=>window.dispatchEvent(new Event('defense-native-background')));
  expect(stopTrack).toHaveBeenCalled();expect(speech.readyState).toBe(3);
  await act(async()=>speech.event({type:'ready',attempt_id:'background',text:'Late final words.'}));
  await act(async()=>window.dispatchEvent(new Event('defense-native-resume')));
  expect(getUserMedia).toHaveBeenCalledTimes(1);
  expect(screen.getByRole('textbox',{name:'Spoken answer'})).toHaveValue('');
  expect(roomSocket.sendEvent).not.toHaveBeenCalled();
});

it('stops forwarding and offers recovery when the operating system mutes capture',async()=>{
  render(<App/>);await userEvent.click(screen.getByRole('button',{name:'Use voice'}));
  await userEvent.click(screen.getByRole('button',{name:'Start mic'}));
  const speech=SpeechSocket.sockets[0];
  await act(async()=>speech.event({type:'started',attempt_id:'muted',remaining_ms:600000}));
  await act(async()=>mediaTrack.dispatchEvent(new Event('mute')));
  expect(stopTrack).toHaveBeenCalled();expect(speech.readyState).toBe(3);
  expect(screen.getByRole('alert')).toHaveTextContent('Microphone stopped unexpectedly');
  expect(roomSocket.sendEvent).toHaveBeenCalledWith({type:'discard_voice_draft',attempt_id:'muted'});
  expect(roomSocket.sendEvent).not.toHaveBeenCalledWith(expect.objectContaining({type:'submit_answer'}));
});

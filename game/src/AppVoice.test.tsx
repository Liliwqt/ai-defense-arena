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
const getUserMedia = vi.fn(async () => ({ getTracks: () => [{ stop: stopTrack, addEventListener: vi.fn() }] }));
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
afterEach(()=>{vi.unstubAllGlobals();vi.clearAllMocks();});
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

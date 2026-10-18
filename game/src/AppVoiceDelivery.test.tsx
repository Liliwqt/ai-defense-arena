import {render,screen,within} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {beforeEach,afterEach,expect,it,vi} from 'vitest';
import {App} from './App';
import {useAccount} from './hooks/useAccount';
import {useRoomSocket} from './hooks/useRoomSocket';
import {coachedRoom} from './test/coachingFixture';
vi.mock('./hooks/useAccount',()=>({useAccount:vi.fn()}));
vi.mock('./hooks/useRoomSocket',()=>({useRoomSocket:vi.fn()}));
export function deliveryRoom(){
 const state=coachedRoom();const card=state.feedback!.answer_cards![0];
 const evidence={input_method:'voice' as const,recording:{version:1 as const,source:'server_pcm_samples' as const,capture_ms:12000,recognition_confidence:'not_provided' as const,configured_language:'en' as const},observations:{filler_examples:['Uhm'],repetition_examples:[]},speaking_rate:null,pauses:null,measurement_reason:'word_timing_and_confidence_unavailable' as const};
 card.delivery=evidence;card.input_provenance={method:'voice',provider:'OpenAI',model:'gpt-live-transcribe',audio_ms:12000,delivery_evidence:evidence.recording};
 card.probe!.delivery={...evidence,recording:{...evidence.recording,capture_ms:100},observations:{filler_examples:[],repetition_examples:[]},measurement_reason:'recording_too_short'};
 card.probe!.input_provenance={method:'voice',provider:'OpenAI',model:'gpt-live-transcribe',audio_ms:100,delivery_evidence:card.probe!.delivery.recording!};
 const typed=state.feedback!.answer_cards![1];typed.original_answer='We will request consent.';typed.speaker_name='Sam';typed.timed_out=false;
 typed.delivery={input_method:'typed',recording:null,observations:{filler_examples:[],repetition_examples:[]},speaking_rate:null,pauses:null,measurement_reason:'typed_input'};
 return state;
}
beforeEach(()=>{
 sessionStorage.clear();window.history.replaceState(null,'','/#/results');
 vi.mocked(useAccount).mockReturnValue({account:{authenticated:true,google_enabled:true,free_access:true},error:'',refresh:vi.fn(async()=>{})});
 vi.mocked(useRoomSocket).mockReturnValue({roomState:deliveryRoom(),roomCode:'COACH1',playerToken:'token',connected:true,knownHost:true,waitingForAnswerAck:false,actionError:null,actionErrorReason:null,sendEvent:vi.fn(()=>true),useRoom:vi.fn(),leaveRoom:vi.fn()});
});
afterEach(()=>vi.clearAllMocks());
it('distinguishes capture facts, recognized examples and suggestions for each speaker, without invented speaking measures',async()=>{
 render(<App/>);
 const answer=screen.getByRole('region',{name:'Alex · Answer delivery evidence'});
 expect(within(answer).getByText(/Measured recording: 12.0 seconds/)).toBeVisible();
 expect(within(answer).getByText(/possible hesitation wording: “Uhm”/)).toBeVisible();
 expect(within(answer).getByText(/no word timing or transcription confidence/)).toBeVisible();
 const reply=screen.getByRole('region',{name:'Sam · Reply delivery evidence'});
 expect(within(reply).getByText(/recording is too short/)).toBeVisible();
 expect(within(reply).queryByText(/“Uhm”/)).toBeNull();
 expect(screen.getByText('We will limit our claim to the campus pilot.')).toBeVisible();
 await userEvent.selectOptions(screen.getByRole('combobox',{name:'Review a question'}),'1');
 const typed=screen.getByRole('region',{name:'Sam · Answer delivery evidence'});
 expect(within(typed).getByText(/Typed answer · Audio measurements unavailable/)).toBeVisible();
 expect(within(typed).queryByText(/Measured recording/)).toBeNull();
});
it('exports distinct speaker evidence and transcript observations without speech-rate placeholders',async()=>{
 const {buildDefenseSummary}=await import('./lib/buildDefenseSummary');
 const text=buildDefenseSummary(deliveryRoom());
 expect(text).toContain('Measured recording: 12.0 seconds');
 expect(text).toContain('Reply delivery evidence · Sam');
 expect(text).toContain('possible hesitation wording: “Uhm”');
 expect(text).toContain('recording is too short');
 expect(text).toContain('AI practice suggestions · check the paper and intended meaning.');
 expect(text).not.toMatch(/0 wpm|0 pauses|filler-free:/);
});
it('never labels an unanswered turn as typed delivery in the summary',async()=>{
 const {buildDefenseSummary}=await import('./lib/buildDefenseSummary');
 const text=buildDefenseSummary(coachedRoom()).split('Q2 · DETAILED COACHING')[1];
 expect(text).toContain('No answer recorded.');
 expect(text).not.toContain('Typed answer');
});

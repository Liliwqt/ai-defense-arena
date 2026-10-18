import { render,screen,within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach,afterEach,expect,it,vi } from 'vitest';
import { App } from './App';
import { useAccount } from './hooks/useAccount';
import { useRoomSocket,type RoomSocketState } from './hooks/useRoomSocket';
import { coachedRoom } from './test/coachingFixture';
vi.mock('./hooks/useAccount',()=>({useAccount:vi.fn()}));
vi.mock('./hooks/useRoomSocket',()=>({useRoomSocket:vi.fn()}));
let socket:RoomSocketState;
beforeEach(()=>{
 sessionStorage.clear();window.history.replaceState(null,'','/#/room');
 vi.mocked(useAccount).mockReturnValue({account:{authenticated:true,google_enabled:true,free_access:true},error:'',refresh:vi.fn(async()=>{})});
 const state=coachedRoom();state.feedback!.answer_cards=state.feedback!.answer_cards!.slice(0,1);
 state.feedback_status='generating';state.coaching_progress={job_id:'job-one',overview_status:'ready',cards_ready:1,cards_required:2,
  completion_status:'pending',completion_error:null,can_retry:false,sections:[{id:'overview',turns:null,status:'ready',attempts_left:2,error:null},
   {id:'answers-0',turns:[0],status:'ready',attempts_left:2,error:null},{id:'answers-1',turns:[1],status:'generating',attempts_left:2,error:null}]};
 socket={roomState:state,roomCode:'COACH1',playerToken:'token',connected:true,knownHost:true,waitingForAnswerAck:false,actionError:null,actionErrorReason:null,sendEvent:vi.fn(()=>true),useRoom:vi.fn(),leaveRoom:vi.fn()};
 vi.mocked(useRoomSocket).mockImplementation(()=>socket);
});
afterEach(()=>vi.clearAllMocks());
it('opens partial Results after the overview and retains ready cards while another is pending',async()=>{
 render(<App/>);
 expect(screen.getByRole('heading',{name:'Defense results'})).toBeVisible();
 expect(within(screen.getByRole('region',{name:'Coaching progress'})).getByText('1 of 2 answers coached')).toBeVisible();
 const selector=screen.getByRole('combobox',{name:'Review a question'});
 expect(within(screen.getByRole('region',{name:'Question coaching'})).getByText('We will limit our claim to the campus pilot.')).toBeVisible();
 await userEvent.selectOptions(selector,'1');
 expect(screen.getByText('Coaching for this question is still being prepared.')).toBeVisible();
 expect(screen.queryByText('This defense is complete. Results remain available while the room exists.')).toBeNull();
 expect(socket.sendEvent).not.toHaveBeenCalled();
});
it('preserves partial cards and offers host-only failed-section retry without replaying the closing',async()=>{
 socket.roomState!.feedback_status='failed';socket.roomState!.coaching_progress!.can_retry=true;
 socket.roomState!.coaching_progress!.sections[2].status='failed';
 render(<App/>);await userEvent.click(screen.getByRole('button',{name:'Retry failed coaching sections'}));
 expect(socket.sendEvent).toHaveBeenCalledExactlyOnceWith({type:'retry_coaching'});
 expect(screen.getByRole('region',{name:'Question coaching'})).toBeVisible();
});
it('keeps Account tasks open while partial coaching becomes complete',()=>{
 window.history.replaceState(null,'','/#/account');
 const app=render(<App/>);
 expect(screen.queryByRole('heading',{name:'Defense results'})).toBeNull();
 socket.roomState={...socket.roomState!,feedback_status:'ready',coaching_progress:{...socket.roomState!.coaching_progress!,completion_status:'ready',cards_ready:2}};
 app.rerender(<App/>);
 expect(screen.queryByRole('heading',{name:'Defense results'})).toBeNull();
 expect(window.location.hash).toBe('#/account');
 expect(socket.sendEvent).not.toHaveBeenCalled();
});
it('retains progress and original words in a partial summary export',async()=>{
 const {buildDefenseSummary}=await import('./lib/buildDefenseSummary');
 const text=buildDefenseSummary(socket.roomState!);
 expect(text).toContain('Coaching status: generating');
 expect(text).toContain('Coaching progress: 1/2 answers coached · completion pending');
 expect(text).toContain('Questions 2: generating');
 expect(text).toContain('Uhm, we will limit the claim.');
 expect(text).toContain('Reply coaching · Sam');
});

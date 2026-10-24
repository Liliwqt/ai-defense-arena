import { act,render,screen,within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach,afterEach,expect,it,vi } from 'vitest';
import { App } from './App';
import { useAccount } from './hooks/useAccount';
import { useRoomSocket,type RoomSocketState } from './hooks/useRoomSocket';
import { coachedRoom } from './test/coachingFixture';
import type { RoomState } from './types';
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

function activeReport():RoomState {
 return {...socket.roomState!,server_now_ms:5000,
  operation:{id:'coaching:1',kind:'coaching',stage:'answers',started_at_ms:1000,attempt:1,retrying:false},
  panelist_activity:{operation_id:'coaching:1',view_id:'run-coach',reviewer:null,context:'Question 2',job_id:'job-one',section_id:'answers-1'}};
}
it('shows activity for only the running section while ready coaching stays readable and clears it on completion',()=>{
 socket.roomState=activeReport();
 const app=render(<App/>);
 const report=screen.getByRole('region',{name:'Coaching report'});
 const activity=within(report).getByRole('region',{name:'Panelist activity'});
 expect(activity.querySelector('mark')).toHaveTextContent('Question 2');
 expect(activity).toHaveTextContent('Preparing your answer coaching…');
 expect(activity).toHaveTextContent('4s');
 expect(within(screen.getByRole('region',{name:'Question coaching'})).getByText('We will limit our claim to the campus pilot.')).toBeVisible();
 expect(activity).not.toHaveTextContent('Lead with the boundary');
 socket.roomState={...socket.roomState!,feedback_status:'ready',feedback:coachedRoom().feedback,
  coaching_progress:{...socket.roomState!.coaching_progress!,cards_ready:2,completion_status:'ready',sections:socket.roomState!.coaching_progress!.sections.map(section=>({...section,status:'ready'}))}};
 app.rerender(<App/>);
 expect(screen.queryByRole('region',{name:'Panelist activity'})).toBeNull();
 expect(screen.getByRole('region',{name:'Question coaching'})).toBeVisible();
 expect(socket.sendEvent).not.toHaveBeenCalled();
});

it('clears finished overview activity while the next section is queued without hiding the overview',()=>{
 socket.roomState=activeReport();
 socket.roomState.operation={...socket.roomState.operation!,stage:'overview'};
 socket.roomState.panelist_activity={...socket.roomState.panelist_activity!,section_id:'overview',context:'Team overview'};
 socket.roomState.feedback=null;
 socket.roomState.coaching_progress={...socket.roomState.coaching_progress!,overview_status:'generating',cards_ready:0,
  sections:socket.roomState.coaching_progress!.sections.map(section=>({...section,status:section.id==='overview'?'generating':'pending'}))};
 const app=render(<App/>);
 expect(screen.getByRole('region',{name:'Panelist activity'})).toHaveTextContent('Preparing your coaching overview…');
 socket.roomState={...socket.roomState,feedback:coachedRoom().feedback,coaching_progress:{...socket.roomState.coaching_progress!,overview_status:'ready',
  sections:socket.roomState.coaching_progress!.sections.map(section=>({...section,status:section.id==='overview'?'ready':'pending'}))}};
 app.rerender(<App/>);
 expect(screen.queryByRole('region',{name:'Panelist activity'})).toBeNull();
 expect(screen.getByText('Waiting for the next coaching section…')).toBeVisible();
 expect(screen.getByText('The discussion established a limited scope; consent remains unanswered.')).toBeVisible();
 expect(socket.sendEvent).not.toHaveBeenCalled();
});

it('keeps ready cards through failure and rejects a completed-section or old-job highlight during retry',async()=>{
 socket.roomState=activeReport();
 const app=render(<App/>);
 socket.roomState={...socket.roomState!,feedback_status:'failed',operation:null,panelist_activity:null,
  coaching_progress:{...socket.roomState!.coaching_progress!,can_retry:true,sections:socket.roomState!.coaching_progress!.sections.map(section=>section.id==='answers-1'?{...section,status:'failed'}:section)}};
 app.rerender(<App/>);
 expect(screen.queryByRole('region',{name:'Panelist activity'})).toBeNull();
 expect(screen.getByRole('region',{name:'Question coaching'})).toHaveTextContent('We will limit our claim to the campus pilot.');
 await userEvent.click(screen.getByRole('button',{name:'Retry failed coaching sections'}));
 expect(socket.sendEvent).toHaveBeenCalledExactlyOnceWith({type:'retry_coaching'});
 socket.roomState={...activeReport(),feedback_status:'generating',
  operation:{...activeReport().operation!,id:'coaching:2',retrying:true},
  panelist_activity:{...activeReport().panelist_activity!,operation_id:'coaching:2',section_id:'answers-0',context:'Question 1'},
  coaching_progress:{...socket.roomState.coaching_progress!,sections:socket.roomState.coaching_progress!.sections.map(section=>section.id==='answers-1'?{...section,status:'generating'}:section)}};
 app.rerender(<App/>);
 expect(screen.getByRole('region',{name:'Panelist activity'}).querySelector('mark')).toBeNull();
 expect(screen.getByRole('region',{name:'Panelist activity'})).toHaveTextContent('Trying again…');
 socket.roomState={...socket.roomState,coaching_progress:{...socket.roomState.coaching_progress!,job_id:'new-job'}};
 app.rerender(<App/>);
 expect(screen.getByRole('region',{name:'Panelist activity'}).querySelector('mark')).toBeNull();
});

it('restores only current coaching through navigation, names saving work and clears cancelled activity',()=>{
 socket.roomState={...activeReport(),practice_tier:'free',defense_type:'mixed',self_is_host:false,self_seat:1};
 const app=render(<App/>);
 act(()=>{window.history.pushState(null,'','/#/account');window.dispatchEvent(new PopStateEvent('popstate'));});
 expect(screen.queryByRole('region',{name:'Panelist activity'})).toBeNull();
 socket.roomState={...socket.roomState!,server_now_ms:31000};app.rerender(<App/>);
 act(()=>{window.history.pushState(null,'','/#/results');window.dispatchEvent(new PopStateEvent('popstate'));});
 expect(screen.getByRole('region',{name:'Panelist activity'})).toHaveTextContent('30s');
 socket.roomState={...socket.roomState,operation:{...socket.roomState.operation!,stage:'saving_completion'},
  panelist_activity:{...socket.roomState.panelist_activity!,section_id:'saving_completion',context:'Completed coaching sections'},
  coaching_progress:{...socket.roomState.coaching_progress!,cards_ready:2,sections:socket.roomState.coaching_progress!.sections.map(section=>({...section,status:'ready'}))}};
 app.rerender(<App/>);
 expect(screen.getByRole('region',{name:'Panelist activity'})).toHaveTextContent('Saving your coaching…');
 socket.roomState={...socket.roomState,feedback_status:'none',operation:null,panelist_activity:null,
  coaching_progress:{...socket.roomState.coaching_progress!,completion_status:'cancelled'}};
 app.rerender(<App/>);
 expect(screen.queryByRole('region',{name:'Panelist activity'})).toBeNull();
 expect(screen.getByRole('region',{name:'Question coaching'})).toBeVisible();
 expect(socket.sendEvent).not.toHaveBeenCalled();
});

it('uses a factual fallback when a legacy coaching snapshot cannot validate the section context',()=>{
 socket.roomState={...activeReport(),coaching_progress:undefined};
 render(<App/>);
 const activity=screen.getByRole('region',{name:'Panelist activity'});
 expect(activity.querySelector('mark')).toBeNull();
 expect(activity).toHaveTextContent('Preparing your answer coaching…');
 expect(socket.sendEvent).not.toHaveBeenCalled();
});

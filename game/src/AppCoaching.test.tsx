import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, afterEach, expect, it, vi } from 'vitest';
import { App } from './App';
import { useAccount } from './hooks/useAccount';
import { useRoomSocket } from './hooks/useRoomSocket';
import { coachedRoom } from './test/coachingFixture';
vi.mock('./hooks/useAccount',()=>({useAccount:vi.fn()}));
vi.mock('./hooks/useRoomSocket',()=>({useRoomSocket:vi.fn()}));
beforeEach(()=>{
  sessionStorage.clear();window.history.replaceState(null,'','/#/results');
  vi.mocked(useAccount).mockReturnValue({account:{authenticated:true,google_enabled:true,free_access:true},error:'',refresh:vi.fn(async()=>{})});
  vi.mocked(useRoomSocket).mockReturnValue({roomState:coachedRoom(),roomCode:'COACH1',playerToken:'token',connected:true,knownHost:true,
    waitingForAnswerAck:false,actionError:null,actionErrorReason:null,sendEvent:vi.fn(()=>true),useRoom:vi.fn(),leaveRoom:vi.fn()});
});
afterEach(()=>vi.clearAllMocks());
it('selects focused coaching with preserved original/probe speakers and unanswered guidance',async()=>{
  render(<App/>);
  const selector=screen.getByRole('combobox',{name:'Review a question'});
  let detail=screen.getByRole('region',{name:'Question coaching'});
  expect(within(detail).getByText('Uhm, we will limit the claim.')).toBeVisible();
  expect(within(detail).getByText('Alex · Original answer')).toBeVisible();expect(within(detail).getAllByText(/Sam/).length).toBeGreaterThan(0);
  expect(within(detail).getByText('We will limit our claim to the campus pilot.')).toBeVisible();
  expect(within(detail).getByText(/Conditional scaffold/)).toBeVisible();
  expect(within(detail).getAllByText(/Audio measurements unavailable/)[0]).toBeVisible();
  await userEvent.selectOptions(selector,'1');
  detail=screen.getByRole('region',{name:'Question coaching'});
  expect(within(detail).getByText('No answer was recorded.')).toBeVisible();
  expect(within(detail).queryByText('We will limit our claim to the campus pilot.')).toBeNull();
  expect(within(detail).getByText('Locate the consent plan and practice explaining it.')).toBeVisible();
  expect(within(detail).queryByText('Suggested wording')).toBeNull();
  selector.focus();expect(selector).toHaveFocus();
});

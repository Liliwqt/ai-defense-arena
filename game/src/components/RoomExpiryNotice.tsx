import type { RoomState } from '../types';
import { formatCountdown, useRoomCountdown } from '../hooks/useRoomCountdown';

export function RoomExpiryNotice({ state }: { state: RoomState | null }) {
  const seconds = useRoomCountdown(state?.expires_at_ms ? { ...state, phase: 'question', answer_deadline_ms: state.expires_at_ms } : null);
  if (seconds === null || seconds > 120) return null;
  return <span className="hud-pill hud-timer is-urgent" role="status">Room expires in {formatCountdown(seconds)} · save transcript</span>;
}

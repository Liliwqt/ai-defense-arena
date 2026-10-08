import { useState } from 'react';

interface OwnedRoom { room_code: string; phase: string; can_close: boolean; expires_at_ms: number | null }
interface Props { csrf: string; onResume: (code: string, token: string) => void; onClosed: (code: string) => void }

export function OwnedRooms({ csrf, onResume, onClosed }: Props) {
  const [rooms, setRooms] = useState<OwnedRoom[]>([]);
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const [allowance, setAllowance] = useState(2);
  async function request(path: string, method = 'GET') {
    const response = await fetch(path, { method, headers: { 'X-CSRF-Token': csrf } });
    const body = await response.json();
    if (!response.ok) throw new Error(typeof body.detail === 'string' ? body.detail : 'Could not update your rooms.');
    return body;
  }
  async function refresh() {
    if (busy) return;
    setBusy(true); setMessage('');
    try { const body = await request('/api/rooms'); setRooms(body.rooms ?? []); setAllowance(body.limit ?? 2); setLoaded(true); }
    catch (error) { setMessage(error instanceof Error ? error.message : 'Could not load rooms.'); }
    finally { setBusy(false); }
  }
  async function act(room: OwnedRoom, close: boolean) {
    if (busy) return;
    setBusy(true); setMessage('');
    try {
      const body = await request(`/api/rooms/${encodeURIComponent(room.room_code)}${close ? '' : '/resume'}`, close ? 'DELETE' : 'POST');
      if (close) { setRooms(previous => previous.filter(item => item.room_code !== room.room_code)); onClosed(room.room_code); }
      else onResume(body.room_code, body.player_token);
    } catch (error) { setMessage(error instanceof Error ? error.message : 'Could not update the room.'); }
    finally { setBusy(false); }
  }
  return <section className="account-access-card" aria-label="Your rooms">
    <p>You may keep {allowance} rooms. Close an unused room to make space.</p>
    <button type="button" className="button-secondary" disabled={busy} onClick={refresh}>{busy ? 'Updating rooms…' : 'Manage my rooms'}</button>
    {loaded && <ul>{rooms.map(room => <li key={room.room_code}>
      <strong>{room.room_code}</strong> · {room.phase}{room.expires_at_ms && <> · expires {new Date(room.expires_at_ms).toLocaleTimeString()}</>}
      <div className="submission-retry-actions"><button type="button" className="button-secondary" disabled={busy} onClick={() => act(room, false)}>Resume {room.room_code}</button>
      <button type="button" className="button-secondary" disabled={busy || !room.can_close} onClick={() => act(room, true)}>Close {room.room_code}</button></div>
    </li>)}</ul>}
    {loaded && !rooms.length && <p>No retained rooms.</p>}
    {message && <p role="alert">{message}</p>}
  </section>;
}

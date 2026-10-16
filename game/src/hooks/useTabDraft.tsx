import { createContext, useContext, useEffect, useRef, useState, type ReactNode } from "react";
import type { Account } from "./useAccount";
import type { RoomState } from "../types";

const STORAGE = "arena-navigation-drafts-v1";
const CLEAR = "defense-clear-private-drafts";
type Entry = { scope: string; text: string };
type Vault = { version: 1; entries: Record<string, Entry> };
function readVault(): Vault {
  const raw = sessionStorage.getItem(STORAGE);
  if (!raw) return { version: 1, entries: {} };
  if (raw.length > 200_000) throw new Error("Invalid drafts");
  const value = JSON.parse(raw) as Vault;
  if (value?.version !== 1 || !value.entries || typeof value.entries !== "object" || Array.isArray(value.entries)) throw new Error("Invalid drafts");
  if (Object.keys(value.entries).length > 50 || Object.values(value.entries).some(entry => !entry || typeof entry.scope !== "string" || typeof entry.text !== "string" || entry.text.length > 8000)) throw new Error("Invalid drafts");
  return value;
}
export function clearPrivateDrafts() {
  try { sessionStorage.removeItem(STORAGE); } catch { /* in-memory participation still works */ }
  window.dispatchEvent(new Event(CLEAR));
}
export function clearRoomDrafts(room: string) {
  try {
    const vault = readVault();
    for (const family of Object.keys(vault.entries)) {
      if (JSON.parse(family)[2] === room) delete vault.entries[family];
    }
    sessionStorage.setItem(STORAGE, JSON.stringify(vault));
  } catch { /* room state is never restored from drafts */ }
  window.dispatchEvent(new Event(CLEAR));
}
interface Session {
  actor: string | null;
  member: string | null;
  state: RoomState | null;
  generation: number;
  unavailable: () => void;
}
const Context = createContext<Session>({ actor: null, member: null, state: null, generation: 0, unavailable: () => {} });

/** Store unsent input only. Membership secrets are hashed, never copied to this vault. */
export function DraftSession({ account, token, state, preview, children }: {
  account: Account | null; token: string | null; state: RoomState | null; preview: boolean; children: ReactNode;
}) {
  const actor = preview || !account ? null : account.authenticated ? account.user?.id ? `account:${account.user.id}` : null : "guest";
  const [fingerprint, setFingerprint] = useState<{ token: string; digest: string } | null>(null);
  const [generation, setGeneration] = useState(0);
  const [warning, setWarning] = useState("");
  const previousActor = useRef<string | null>(null);
  useEffect(() => {
    const clear = () => setGeneration(value => value + 1);
    window.addEventListener(CLEAR, clear);
    try { readVault(); } catch {
      try { sessionStorage.removeItem(STORAGE); } catch { /* unavailable storage */ }
      setWarning("Saved drafts could not be read. You can continue; refresh recovery may be unavailable.");
    }
    return () => window.removeEventListener(CLEAR, clear);
  }, []);
  useEffect(() => {
    if (!actor) return;
    if (previousActor.current && previousActor.current !== actor) clearPrivateDrafts();
    previousActor.current = actor;
  }, [actor]);
  useEffect(() => {
    let active = true;
    if (token && !preview) {
      void (async () => crypto.subtle.digest("SHA-256", new TextEncoder().encode(token)))().then(buffer => {
        if (active) setFingerprint({ token, digest: Array.from(new Uint8Array(buffer), byte => byte.toString(16).padStart(2, "0")).join("") });
      }).catch(() => { if (active) setWarning("Refresh recovery is unavailable. Keep this tab open to retain drafts."); });
    }
    return () => { active = false; };
  }, [token, preview]);
  return <Context.Provider value={{ actor, member: fingerprint?.token === token ? fingerprint.digest : null,
    state, generation, unavailable: () => setWarning("Refresh recovery is unavailable. Keep this tab open to retain drafts.") }}>
    {warning && <p className="navigation-notice" role="status">{warning}</p>}{children}
  </Context.Provider>;
}

/** A family has one current scope: new turns/maps/runs evict the obsolete value. */
export function useTabDraft(kind: string, initial: string, options: { room?: boolean; marker?: string; valid?: (text: string) => boolean } = {}) {
  const session = useContext(Context);
  const state = session.state;
  const family = session.actor && (!options.room || (session.member && state?.defense_view_id && state.self_seat !== null))
    ? JSON.stringify([session.actor, options.room ? session.member : "setup", options.room ? state?.room_code : "", kind]) : null;
  const scope = JSON.stringify([options.room ? state?.defense_view_id : "setup", options.marker ?? ""]);
  const identity = JSON.stringify([family, scope, session.generation]);
  const owner = JSON.stringify([session.actor, options.room ? state?.room_code : "setup", scope, session.generation]);
  const memory = useRef(new Map<string, string>());
  function restored(): string {
    if (memory.current.has(identity)) return memory.current.get(identity)!;
    if (!family) return initial;
    try {
      const entry = readVault().entries[family];
      return entry?.scope === scope && (!options.valid || options.valid(entry.text)) ? entry.text : initial;
    } catch { return initial; }
  }
  const [draft, setDraft] = useState(() => ({ identity, owner, text: restored(), touched: false }));
  if (draft.identity !== identity) setDraft({ identity, owner,
    text: draft.owner === owner && draft.touched ? draft.text : restored(), touched: draft.owner === owner && draft.touched });
  useEffect(() => {
    if (!family) return;
    try {
      const vault = readVault();
      if (vault.entries[family]?.scope !== scope) {
        delete vault.entries[family]; sessionStorage.setItem(STORAGE, JSON.stringify(vault));
      }
    } catch { session.unavailable(); }
  }, [family, scope]);
  const setText = (text: string) => {
    setDraft({ identity, owner, text, touched: true });
    memory.current.set(identity, text);
    if (!family) return;
    try {
      const vault = readVault();
      if (text) vault.entries[family] = { scope, text: text.slice(0, 8000) };
      else delete vault.entries[family];
      // Bound browser storage; old inactive families are dispensable input.
      while (Object.keys(vault.entries).length > 40) delete vault.entries[Object.keys(vault.entries)[0]];
      sessionStorage.setItem(STORAGE, JSON.stringify(vault));
    } catch { session.unavailable(); }
  };
  // Fingerprinting can finish while someone is already typing. Carry that input
  // only within the same validated actor/room/scope, then save it under membership.
  useEffect(() => { if (draft.identity === identity && draft.touched && family) setText(draft.text); }, [identity]);
  return [draft.identity === identity ? draft.text : initial, setText] as const;
}

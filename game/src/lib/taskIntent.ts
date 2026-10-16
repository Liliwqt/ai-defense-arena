import type { Account } from "../hooks/useAccount";
import type { RoomState } from "../types";
import type { AppScreen } from "./appRoute";
import { roomDestination } from "./roomDestination";

const KEY = "arena-navigation-task-v1";
const MAX_AGE = 2 * 60 * 60 * 1000;
const targets = ["home", "setup", "prepare", "room", "controls", "results", "account", "payments-live", "payments-test", "manager"];
interface TaskIntent { version: 1; target: AppScreen; room: string | null; owner: string | null; created: number; authTarget?: AppScreen }
export function clearTaskIntent() { try { sessionStorage.removeItem(KEY); } catch { /* safe default navigation */ } }
function read(): TaskIntent | null {
  try {
    const value = JSON.parse(sessionStorage.getItem(KEY) ?? "null") as TaskIntent;
    if (!value) return null;
    if (value.version !== 1 || !targets.includes(value.target) ||
      (value.authTarget !== undefined && !["account", "payments-live", "payments-test", "manager"].includes(value.authTarget)) ||
      (value.room !== null && (typeof value.room !== "string" || !/^[A-Z0-9]{1,12}$/.test(value.room))) ||
      (value.owner !== null && (typeof value.owner !== "string" || value.owner.length > 200)) ||
      !Number.isFinite(value.created) || Date.now() - value.created > MAX_AGE || value.created > Date.now() + 1000) throw new Error("Invalid task");
    return value;
  } catch { clearTaskIntent(); return null; }
}
function save(intent: TaskIntent) { try { sessionStorage.setItem(KEY, JSON.stringify(intent)); } catch { /* no arbitrary URL fallback */ } }
export function rememberTask(target: AppScreen, account: Account | null, room: string | null) {
  if (!targets.includes(target)) return;
  save({ version: 1, target, owner: account?.authenticated ? account.user?.id ?? null : null, room, created: Date.now() });
}
export function isFreshSetupReturn() { const intent = read(); return intent?.target === "setup" && intent.room === null; }
export function rememberAuthTask(screen: AppScreen, account: Account | null) {
  const intent = read();
  if (["payments-live", "payments-test", "manager"].includes(screen)) {
    save({ ...(intent ?? { version: 1, target: screen, owner: account?.user?.id ?? null, room: null, created: Date.now() }), authTarget: screen });
  }
}
export function resolveTaskReturn(account: Account, state: RoomState | null, closing: boolean, auth = false): AppScreen | null {
  const intent = read();
  if (!intent || !account.authenticated || !account.user?.id) return null;
  if (intent.owner && intent.owner !== account.user.id) { clearTaskIntent(); return null; }
  const target = auth && intent.authTarget ? intent.authTarget : intent.target;
  if (intent.room && (!state || state.room_code !== intent.room || state.self_seat === null)) { clearTaskIntent(); return null; }
  if (["room", "controls", "prepare", "results"].includes(target) || (target === "setup" && intent.room)) {
    if (!state || !intent.room) { clearTaskIntent(); return null; }
    const stage = roomDestination(state, closing);
    if (stage === "results") return "results";
    if (stage === "prepare") return target === "setup" ? "setup" : "prepare";
    return target === "controls" ? "controls" : "room";
  }
  return target;
}
export function consumeTaskReturn(account: Account, auth = false) {
  const intent = read();
  if (auth && intent?.authTarget && intent.authTarget !== intent.target) {
    delete intent.authTarget; intent.owner = account.user?.id ?? null; save(intent);
  } else clearTaskIntent();
}

import { useCallback, useEffect, useRef, useState } from "react";
import type { DefenseRunReceipt, TestPurchase } from "../lib/paymentHistory";

export interface Account {
  authenticated: boolean;
  google_enabled: boolean;
  user?: { id: string; name: string; email: string };
  csrf_token?: string;
  free_access?: boolean;
  voucher_enabled?: boolean;
  test_credits?: number;
  reserved_credits?: number;
  spent_credits?: number;
  run_cost?: number;
  payment_mode?: "test" | "live";
  live_credits?: number;
  live_reserved_credits?: number;
  live_held_credits?: number;
  topup_invited?: boolean;
  manager_enabled?: boolean;
  active_run?: string | null;
  paid_starts_enabled?: boolean;
  ai_service_available?: boolean;
  live_orders?: {id:string;status:string;amount:number;credits:number;refund_status?:string|null;refund_eligibility?:string}[];
  live_runs?: {id:string;status:string;outcome:string;cost:number}[];
  credit_returns?: {id:string;credits:number;reason:string}[];
  orders?: TestPurchase[];
  runs?: DefenseRunReceipt[];
}

export async function accountResponse(response: Response) {
  const body = await response.json();
  if (!response.ok) throw new Error(typeof body.detail === "string" ? body.detail : "The account request failed. Try again.");
  return body;
}

export function useAccount(preview: boolean) {
  const [account, setAccount] = useState<Account | null>(null);
  const [error, setError] = useState("");
  const version = useRef(0);
  const refresh = useCallback(async () => {
    if (preview) return;
    const current = ++version.current;
    try {
      const value = await accountResponse(await fetch("/api/auth/me", { cache: "no-store" }));
      if (current === version.current) { setAccount(value); setError(""); }
    } catch (failure) {
      if (current === version.current) setError(failure instanceof Error ? failure.message : "Could not load your account.");
    }
  }, [preview]);
  useEffect(() => { void refresh(); return () => { version.current++; }; }, [refresh]);
  useEffect(() => {
    const update = () => { void refresh(); };
    window.addEventListener("focus", update);
    return () => window.removeEventListener("focus", update);
  }, [refresh]);
  return { account, refresh, error };
}

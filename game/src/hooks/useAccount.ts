import { useCallback, useEffect, useRef, useState } from "react";

export interface Account {
  authenticated: boolean;
  google_enabled: boolean;
  user?: { id: string; name: string; email: string };
  csrf_token?: string;
  free_access?: boolean;
  voucher_enabled?: boolean;
  test_credits?: number;
  reserved_credits?: number;
  run_cost?: number;
  orders?: { id: string; status: string; credits: number; amount: number; currency: string }[];
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

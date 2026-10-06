import { useCallback, useEffect, useRef, useState } from "react";
import "./payments.css";
import { purchaseLabel, type TestPurchase } from "../lib/paymentHistory";
import { isNativeShell } from "../lib/saveDefenseSummary";

export const RECEIPT_KEY = "arena-test-payment";
export const ATTEMPT_KEY = "arena-test-checkout-attempt";
type Order = {
  id: string; mode: "test"; status: "pending" | "paid";
  amount: number; currency: "PHP"; checkout_url: string; credits?: number;
};
type Receipt = { id: string; token?: string };
type Account = { authenticated: boolean; google_enabled: boolean;
  user?: { id: string; name: string; email: string }; csrf_token?: string;
  test_credits?: number; orders?: TestPurchase[] };

async function readResponse(response: Response) {
  const body = await response.json();
  if (!response.ok) throw new Error(typeof body.detail === "string" ? body.detail : "The test-payment request failed.");
  return body;
}

function validateOrder(value: Order): Order {
  const url = new URL(value.checkout_url);
  if (value.mode !== "test" || !["pending", "paid"].includes(value.status) || value.currency !== "PHP" || value.amount !== 10000 || url.origin !== "https://checkout.paymongo.com" || url.username || url.password) {
    throw new Error("The server did not return a valid test checkout.");
  }
  return value;
}

function savedReceipt(): Receipt | null {
  try {
    const value = JSON.parse(sessionStorage.getItem(RECEIPT_KEY) ?? "null");
    return value && typeof value.id === "string" ? { id: value.id, ...(typeof value.token === "string" ? { token: value.token } : {}) } : null;
  } catch { return null; }
}

export function PaymentTestPage() {
  const [enabled, setEnabled] = useState<boolean | null>(null);
  const [account, setAccount] = useState<Account | null>(null);
  const [receipt, setReceipt] = useState<Receipt | null>(savedReceipt);
  const [order, setOrder] = useState<Order | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [attempt, setAttempt] = useState<string | null>(() => sessionStorage.getItem(ATTEMPT_KEY));
  const checking = useRef(false);
  const accountVersion = useRef(0);
  const returnState = new URLSearchParams(location.search).get("payment_return");
  const signinError = new URLSearchParams(location.search).get("signin_error");

  const refreshAccount = useCallback(async () => {
    const version = ++accountVersion.current;
    const body = await readResponse(await fetch("/api/auth/me", { cache: "no-store" }));
    if (accountVersion.current === version) setAccount(body);
  }, []);

  useEffect(() => {
    const refresh = () => { void refreshAccount().catch(() => setError("Could not refresh your account. Try Refresh balance.")); };
    window.addEventListener("defense-native-resume", refresh);
    return () => window.removeEventListener("defense-native-resume", refresh);
  }, [refreshAccount]);

  useEffect(() => {
    let active = true;
    fetch("/api/payments/test/config")
      .then(readResponse)
      .then(body => { if (active) setEnabled(body.mode === "test" && body.enabled === true); })
      .catch(() => { if (active) { setEnabled(false); setError("Could not load payment configuration. Check the local server and reload."); } });
    const version = ++accountVersion.current;
    fetch("/api/auth/me", { cache: "no-store" }).then(readResponse)
      .then(body => { if (active && accountVersion.current === version) setAccount(body); })
      .catch(() => { if (active) setError("Could not load your account. Reload before purchasing."); });
    return () => { active = false; };
  }, []);

  useEffect(() => {
    if (!receipt || order?.status === "paid" || !account || (!account.authenticated && !receipt.token)) return;
    let active = true;
    async function refresh() {
      if (checking.current) return;
      checking.current = true;
      try {
        const body = await readResponse(await fetch(`/api/payments/test/orders/${encodeURIComponent(receipt!.id)}`, {
          ...(receipt!.token ? { headers: { Authorization: `Bearer ${receipt!.token}` } } : {}), cache: "no-store",
        }));
        if (active) {
          const verified = validateOrder(body.order);
          setOrder(verified); setError("");
          if (verified.status === "paid") await refreshAccount();
        }
      } catch (err) {
        if (active) setError(err instanceof Error ? err.message : "Could not verify payment. Your test order is retained.");
      } finally { checking.current = false; }
    }
    void refresh();
    window.addEventListener("defense-native-resume", refresh);
    const interval = window.setInterval(() => { void refresh(); }, 5000);
    return () => { active = false; window.clearInterval(interval); window.removeEventListener("defense-native-resume", refresh); };
  }, [receipt, order?.status, account?.authenticated, account?.user?.id, refreshAccount]);

  async function create(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy || !account?.authenticated || !account.csrf_token) return;
    const form = event.currentTarget;
    setBusy(true); setError("");
    try {
      const requestId = attempt ?? crypto.randomUUID();
      // Preserve the ID before requesting: a lost response retries the same
      // provider checkout, rather than creating another payable session.
      sessionStorage.setItem(ATTEMPT_KEY, requestId); setAttempt(requestId);
      const body = await readResponse(await fetch("/api/payments/test/checkout", {
        method: "POST", headers: { "Content-Type": "application/json", "X-CSRF-Token": account.csrf_token, "Idempotency-Key": requestId,
          ...(isNativeShell() ? { "X-Arena-Native": "1" } : {}) },
        body: JSON.stringify({}),
      }));
      const result = validateOrder(body.order);
      const next = { id: result.id };
      // New receipts use the HttpOnly account session; store only the order ID.
      sessionStorage.setItem(RECEIPT_KEY, JSON.stringify(next));
      setOrder(result); setReceipt(next); form.reset();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create a test checkout.");
    } finally { setBusy(false); }
  }

  function reset() {
    sessionStorage.removeItem(RECEIPT_KEY); setReceipt(null); setOrder(null); setError("");
    sessionStorage.removeItem(ATTEMPT_KEY); setAttempt(null);
  }

  async function logout() {
    if (!account?.csrf_token || busy) return;
    setBusy(true); setError("");
    ++accountVersion.current;
    try {
      await readResponse(await fetch("/api/auth/logout", { method: "POST", headers: { "X-CSRF-Token": account.csrf_token } }));
      reset(); setAccount({ authenticated: false, google_enabled: true });
    } catch { setError("Could not sign out. Please try again."); }
    finally { setBusy(false); }
  }

  return <main className="payment-page">
    <div className="payment-container">
      <a href="/" className="payment-back">← Back to AI Defense Arena</a>
      <header><span className="payment-badge">TEST MODE · SANDBOX CHECKOUT</span>
        <h1>Try a test payment</h1>
        <p>Sign in, try a simulated purchase, and check your test-credit balance. A defense run uses 10 test credits; voucher accounts have free access. These are sandbox fixtures.</p>
      </header>
      <section className="payment-account" aria-label="Your account">
        {!account ? <p role="status">Loading your account…</p> : account.authenticated ? <>
          <strong>{account.user?.name}</strong><p>{account.user?.email}</p>
          <p className="payment-balance"><b>{account.test_credits ?? 0}</b> test credits</p>
          <button className="button-secondary" onClick={logout} disabled={busy}>Sign out</button>
        </> : <>
          <h2>Sign in to own your test credits</h2>
          {account.google_enabled ? <a className="button-primary payment-checkout" href="/api/auth/google/login?return_to=%2F%3Fpayments%3Dtest">Sign in with Google</a>
            : <p>Google sign-in needs server configuration. Follow the README’s Google account setup.</p>}
        </>}
        {signinError && <p role="alert">Google sign-in did not finish. Please try again; your test credits are saved.</p>}
      </section>
      <ol className="payment-steps">
        <li><strong>1. Check server setup</strong>
          <p role="status">{enabled === null ? "Checking setup…" : enabled ? "Test checkout is configured." : "Test checkout is not configured yet."}</p>
          {enabled === false && <p>Follow the README payment setup: configure the PayMongo test key, webhook secret, public base URL in the server terminal, then restart it.</p>}
        </li>
        <li><strong>2. Open PayMongo checkout</strong>
          <p>Simulated pack: <b>100 test credits for ₱100.00</b>. This is a test fixture, not the app’s final price.</p>
          <p><strong>QRPh testing:</strong> use PayMongo’s test simulator. Do not scan or pay the QR code with a real bank or wallet app; PayMongo warns this can process a real payment.</p>
          {!receipt && <form onSubmit={create}>
            <button className="button-primary" disabled={!enabled || !account?.authenticated || busy} type="submit">{busy ? "Creating test checkout…" : "Create test checkout"}</button>
          </form>}
          {order?.status === "pending" && <a href={order.checkout_url} className="button-primary payment-checkout">Open test checkout</a>}
          {receipt && !order && <p>{account?.authenticated || receipt.token ? "Loading your saved test order…" : "Sign in to check your saved purchase."}</p>}
          {!receipt && attempt && <><p>Retry keeps the same checkout request. Check purchase history before starting a new attempt.</p><button className="button-secondary" onClick={reset} disabled={busy}>Start a new checkout attempt</button></>}
        </li>
        <li><strong>3. Confirm the test receipt</strong>
          <div role="status" aria-live="polite">
            {order?.status === "paid" ? <p><b>Test payment confirmed.</b> The server verified PayMongo’s signed notification. {order.credits ? `${order.credits} test credits were added to the purchasing account.` : "This earlier anonymous test receipt has no account credits."}</p>
              : receipt ? <p>Awaiting a verified payment notification. Status refreshes every five seconds.</p>
              : <p>Your test receipt will appear here after checkout.</p>}
          </div>
          {returnState === "success" && order?.status !== "paid" && <p>Checkout returned successfully; payment still needs server verification.</p>}
          {returnState === "cancel" && <p>You returned from checkout without completing it. A return alone does not change payment status.</p>}
          {returnState && !receipt && <p>Open the browser tab that created the checkout to view its receipt.</p>}
          {order && <p className="payment-order">Test order: {order.id}</p>}
          {receipt && <button className="button-secondary" onClick={reset}>{order?.status === "paid" ? "Start another test" : "Forget this test receipt"}</button>}
        </li>
      </ol>
      {account?.authenticated && <section className="payment-account" aria-label="Your test purchases">
        <h2>Your test purchases</h2>
        {account.orders?.length ? <ul className="payment-history">{account.orders.map(purchase => <li key={purchase.id}>
          <span className="payment-order">{purchase.id}</span><span>{purchaseLabel(purchase)}</span>
        </li>)}</ul> : <p>No account purchases yet.</p>}
        <button className="button-secondary" onClick={() => { void refreshAccount().catch(() => setError("Could not refresh your account. Try again.")); }}>Refresh balance</button>
      </section>}
      {error && <p className="payment-error" role="alert">{error}</p>}
    </div>
  </main>;
}

import { useCallback, useEffect, useRef, useState } from "react";
import "./payments.css";
import { purchaseLabel, type TestPurchase } from "../lib/paymentHistory";

// Legacy checkout receipts remain separate and available in purchase history.
export const RECEIPT_KEY = "arena-test-topup";
export const ATTEMPT_KEY = "arena-test-topup-attempt";
const OWNER_KEY = "arena-test-topup-owner";
type Package = { id: string; amount: number; currency: "PHP"; credits: number };
type TopupStatus = "creating" | "creation_failed" | "pending" | "paid" | "failed" | "expired";
type Topup = { id: string; mode: "test"; status: TopupStatus; amount: number; currency: "PHP"; credits: number;
  qr_image_url: string | null; expires_at: number | null; simulated: boolean };
type Receipt = { id: string; account_id: string; hidden?: boolean };
type Account = { authenticated: boolean; google_enabled: boolean;
  user?: { id: string; name: string; email: string }; csrf_token?: string;
  test_credits?: number; orders?: TestPurchase[] };
async function readResponse(response: Response) {
  const body = await response.json();
  if (!response.ok) throw new Error(typeof body.detail === "string" ? body.detail : "The test top-up request failed. Try again.");
  return body;
}
function savedReceipt(): Receipt | null {
  try {
    const value = JSON.parse(sessionStorage.getItem(RECEIPT_KEY) ?? "null");
    return value && typeof value.id === "string" && typeof value.account_id === "string" ? value : null;
  } catch { return null; }
}
function validateTopup(value: Topup, packages: Package[], expectedId?: string): Topup {
  if (!value || value.mode !== "test" || typeof value.id !== "string" || !value.id || (expectedId && value.id !== expectedId)
      || !["creating", "creation_failed", "pending", "paid", "failed", "expired"].includes(value.status)
      || !packages.some(pack => pack.amount === value.amount && pack.credits === value.credits && pack.currency === value.currency)
      || typeof value.simulated !== "boolean"
      || (value.qr_image_url !== null && (typeof value.qr_image_url !== "string" || !/^data:image\/png;base64,[A-Za-z0-9+/]+={0,2}$/.test(value.qr_image_url)))
      || (value.expires_at !== null && (!Number.isSafeInteger(value.expires_at) || value.expires_at <= 0))
      || (value.status === "pending" && (!value.qr_image_url || !value.expires_at))) {
    throw new Error("The server did not return a valid sandbox top-up. Your request is retained.");
  }
  return value;
}
const price = (amount: number) => `₱${(amount / 100).toFixed(2)}`;

export function PaymentTestPage() {
  const [enabled, setEnabled] = useState<boolean | null>(null);
  const [packages, setPackages] = useState<Package[]>([]);
  const [packageId, setPackageId] = useState("");
  const [account, setAccount] = useState<Account | null>(null);
  const [receipt, setReceipt] = useState<Receipt | null>(savedReceipt);
  const [topup, setTopup] = useState<Topup | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [attempt, setAttempt] = useState<string | null>(() => sessionStorage.getItem(ATTEMPT_KEY));
  const [now, setNow] = useState(Date.now());
  const version = useRef(0);
  const accountVersion = useRef(0);
  const checking = useRef(false);
  const mutating = useRef(false);
  const currentOwner = useRef<string>();
  const signinError = new URLSearchParams(location.search).get("signin_error");
  const returnState = new URLSearchParams(location.search).get("payment_return");

  const refreshAccount = useCallback(async () => {
    const request = ++accountVersion.current;
    const value: Account = await readResponse(await fetch("/api/auth/me", { cache: "no-store" }));
    if (request !== accountVersion.current) return;
    if (currentOwner.current !== value.user?.id) { version.current++; currentOwner.current = value.user?.id; }
    setAccount(value);
  }, []);
  const refreshAfterPayment = useCallback(async (request: number) => {
    try { await refreshAccount(); }
    catch { if (request === version.current) setError("Payment is recorded, but the balance could not refresh. Try Refresh balance."); }
  }, [refreshAccount]);
  useEffect(() => {
    let active = true;
    void fetch("/api/payments/test/config").then(readResponse).then(body => {
      if (!active) return;
      const accepted: Package[] = Array.isArray(body.packages) ? body.packages.filter((pack: Package) => pack
        && typeof pack.id === "string" && pack.id && pack.currency === "PHP"
        && Number.isSafeInteger(pack.amount) && pack.amount > 0 && Number.isSafeInteger(pack.credits) && pack.credits > 0) : [];
      setEnabled(body.mode === "test" && body.enabled === true && accepted.length > 0);
      setPackages(accepted);
    }).catch(() => { if (active) { setEnabled(false); setError("Could not load top-up configuration. Reload to try again."); } });
    void refreshAccount().catch(() => { if (active) setError("Could not load your account. Reload before topping up."); });
    const tick = window.setInterval(() => setNow(Date.now()), 1000);
    const resume = () => { setNow(Date.now()); void refreshAccount().catch(() => setError("Could not refresh your account. Try Refresh balance.")); };
    window.addEventListener("defense-native-resume", resume); window.addEventListener("focus", resume);
    return () => { active = false; version.current++; accountVersion.current++; window.clearInterval(tick);
      window.removeEventListener("defense-native-resume", resume); window.removeEventListener("focus", resume); };
  }, [refreshAccount]);

  const owned = !!account?.authenticated && receipt?.account_id === account.user?.id;
  useEffect(() => {
    if (!owned || !receipt || !packages.length || (topup?.status === "paid" && !topup.simulated)) return;
    let active = true;
    async function refresh() {
      if (checking.current || mutating.current) return;
      checking.current = true; const request = version.current;
      try {
        const body = await readResponse(await fetch(`/api/payments/test/topups/${encodeURIComponent(receipt!.id)}`, { cache: "no-store" }));
        if (active && request === version.current) {
          const verified = validateTopup(body.topup, packages, receipt!.id);
          setTopup(verified); setError("");
          if (verified.status === "paid") await refreshAfterPayment(request);
        }
      } catch (failure) { if (active && request === version.current) setError(failure instanceof Error ? failure.message : "Could not check your saved top-up."); }
      finally { checking.current = false; }
    }
    void refresh(); const interval = window.setInterval(() => { void refresh(); }, 5000);
    window.addEventListener("defense-native-resume", refresh); window.addEventListener("focus", refresh);
    return () => { active = false; window.clearInterval(interval); window.removeEventListener("defense-native-resume", refresh); window.removeEventListener("focus", refresh); };
  }, [owned, receipt?.id, packages, topup?.status, topup?.simulated, refreshAfterPayment]);

  function reset() {
    version.current++; sessionStorage.removeItem(RECEIPT_KEY); sessionStorage.removeItem(ATTEMPT_KEY); sessionStorage.removeItem(OWNER_KEY);
    setReceipt(null); setTopup(null); setAttempt(null); setError("");
  }
  async function create(event?: React.FormEvent<HTMLFormElement>, newAttempt = false, chosenPackage = packageId || packages[0]?.id) {
    event?.preventDefault();
    if (mutating.current || !enabled || !account?.authenticated || !account.csrf_token || !account.user || !packages.some(pack => pack.id === chosenPackage)) return;
    if (newAttempt) reset();
    mutating.current = true; setBusy(true); setError(""); const request = ++version.current;
    try {
      const requestId = !newAttempt && attempt && sessionStorage.getItem(OWNER_KEY) === account.user.id ? attempt : crypto.randomUUID();
      sessionStorage.setItem(ATTEMPT_KEY, requestId); sessionStorage.setItem(OWNER_KEY, account.user.id); setAttempt(requestId);
      const body = await readResponse(await fetch("/api/payments/test/topups", { method: "POST",
        headers: { "Content-Type": "application/json", "X-CSRF-Token": account.csrf_token, "Idempotency-Key": requestId },
        body: JSON.stringify({ package_id: chosenPackage }) }));
      if (request !== version.current) return;
      const verified = validateTopup(body.topup, packages); const next = { id: verified.id, account_id: account.user.id };
      sessionStorage.setItem(RECEIPT_KEY, JSON.stringify(next)); setReceipt(next); setTopup(verified);
      if (verified.status === "paid") await refreshAfterPayment(request);
    } catch (failure) { if (request === version.current) setError(failure instanceof Error ? failure.message : "Could not generate a test QR."); }
    finally { mutating.current = false; setBusy(false); }
  }
  async function simulate() {
    if (mutating.current || !enabled || !owned || !account?.csrf_token || !topup || topup.status !== "pending" || !topup.expires_at || topup.expires_at * 1000 <= Date.now() || receipt?.hidden) return;
    mutating.current = true; setBusy(true); setError(""); const request = ++version.current;
    try {
      const body = await readResponse(await fetch(`/api/payments/test/topups/${encodeURIComponent(topup.id)}/simulate`, {
        method: "POST", headers: { "Content-Type": "application/json", "X-CSRF-Token": account.csrf_token }, body: "{}" }));
      if (request !== version.current) return;
      setTopup(validateTopup(body.topup, packages, topup.id)); await refreshAfterPayment(request);
    } catch (failure) { if (request === version.current) setError(failure instanceof Error ? failure.message : "Could not simulate this top-up."); }
    finally { mutating.current = false; setBusy(false); }
  }
  function cancel() {
    if (!receipt || busy) return;
    const hidden = { ...receipt, hidden: true }; sessionStorage.setItem(RECEIPT_KEY, JSON.stringify(hidden)); setReceipt(hidden);
  }
  async function logout() {
    if (!account?.csrf_token || mutating.current) return;
    mutating.current = true; setBusy(true); setError(""); ++version.current; ++accountVersion.current;
    try {
      await readResponse(await fetch("/api/auth/logout", { method: "POST", headers: { "X-CSRF-Token": account.csrf_token } }));
      ++accountVersion.current; reset(); currentOwner.current = undefined; setAccount({ authenticated: false, google_enabled: account.google_enabled });
    } catch { setError("Could not sign out. Please try again."); }
    finally { mutating.current = false; setBusy(false); }
  }

  const visibleTopup = owned ? topup : null;
  const remaining = visibleTopup?.expires_at ? Math.max(0, Math.ceil((visibleTopup.expires_at * 1000 - now) / 1000)) : 0;
  const status = visibleTopup?.status === "paid" ? "paid" : receipt?.hidden && owned ? "cancelled"
    : visibleTopup?.status === "pending" && remaining === 0 ? "expired" : visibleTopup?.status;
  const selectable = !receipt || !owned;
  return <main className="payment-page"><div className="payment-container">
    <a href="/" className="payment-back">← Back to AI Defense Arena</a>
    <header><span className="payment-badge">TEST MODE · SANDBOX TOP-UP</span><h1>Top up test credits</h1>
      <p>A defense run uses 10 test credits. These packages are sandbox fixtures, not final pricing.</p></header>
    <section className="payment-account" aria-label="Your account">
      {!account ? <p role="status">Loading your account…</p> : account.authenticated ? <>
        <strong>{account.user?.name}</strong><p>{account.user?.email}</p>
        <p className="payment-balance"><b>{account.test_credits ?? 0}</b> available test credits</p>
        <button className="button-secondary" onClick={logout} disabled={busy}>Sign out</button>
      </> : <><h2>Sign in to own your test credits</h2>{account.google_enabled
        ? <a className="button-primary payment-login" href="/api/auth/google/login?return_to=%2F%3Fpayments%3Dtest">Sign in with Google</a>
        : <p>Google sign-in needs server configuration. Follow the README’s Google account setup.</p>}</>}
      {signinError && <p role="alert">Google sign-in did not finish. Please try again; your test credits are saved.</p>}
    </section>
    <section className="payment-account" aria-label="Sandbox top-up"><h2>Choose a test-credit package</h2>
      <p role="status">{enabled === null ? "Checking setup…" : enabled ? "Test top-up is configured." : "Test top-up is not configured yet."}</p>
      {enabled === false && <p>Configure the PayMongo test key, webhook secret and public base URL on the server. Live keys are not accepted.</p>}
      <p className="payment-warning"><strong>Sandbox only:</strong> Do not scan or pay the QR code with a real bank or wallet app. Use sandbox simulation below or PayMongo’s test tools.</p>
      {selectable && <form className="payment-package" onSubmit={create}>
        <label htmlFor="test-package">Test-credit package</label><select id="test-package" value={packageId} onChange={event => { const selected = event.target.value; setPackageId(selected); void create(undefined, false, selected); }} disabled={busy || !!attempt || !enabled || !account?.authenticated}>
          <option value="" disabled>Choose a package</option>
          {packages.map(pack => <option key={pack.id} value={pack.id}>{pack.credits} test credits · {price(pack.amount)}</option>)}
        </select><button className="button-primary" type="submit" disabled={!enabled || !account?.authenticated || busy}>{busy ? "Generating test QR…" : "Generate test QR"}</button>
      </form>}
      {receipt && !owned && <p>Sign in to the account that created this top-up to restore it, or create a top-up for your current account.</p>}
      {owned && !visibleTopup && <p>Loading your saved test top-up…</p>}
      {!receipt && attempt && <><p>Retry uses the same request. Check history before explicitly starting a new attempt.</p>
        <button className="button-secondary" onClick={reset} disabled={busy}>Start a new top-up attempt</button></>}
      {visibleTopup && <div className="payment-receipt"><p><strong>{price(visibleTopup.amount)} · {visibleTopup.credits} test credits</strong></p>
        {status === "pending" && <><img className="payment-qr" src={visibleTopup.qr_image_url!} alt="Sandbox QR Ph code" />
          <p>QR display validity: <time>{String(Math.floor(remaining / 60)).padStart(2, "0")}:{String(remaining % 60).padStart(2, "0")}</time></p>
          <p role="status">Awaiting server confirmation. No test credits added yet. Status refreshes every five seconds.</p>
          <div className="payment-actions"><button className="button-primary" onClick={simulate} disabled={!enabled || busy}>Simulate paid top-up</button>
            <button className="button-secondary" onClick={cancel} disabled={busy}>Cancel top-up</button></div>
          <p>Simulation grants test credits only; it does not process a provider payment.</p></>}
        {status === "paid" && <><h3 role="status">{visibleTopup.simulated ? "Sandbox simulation applied." : "Test payment confirmed."}</h3>
          <p>{visibleTopup.credits} test credits applied. {visibleTopup.simulated ? "No provider payment was processed." : "The server verified the payment notification."}</p>
          <button className="button-secondary" onClick={reset} disabled={busy}>Start another top-up</button></>}
        {status === "failed" && <><h3>Test payment failed.</h3><p>No credits were added for this failed payment. A later verified payment can still update this receipt.</p></>}
        {status === "expired" && <><h3>Test QR expired.</h3><p>No credits are added by expiry. The QR is hidden; server confirmation is still monitored.</p></>}
        {status === "cancelled" && <><h3>Top-up cancelled on this device.</h3><p>The QR is hidden, not cancelled at PayMongo. No credits are added by cancelling; a later verified payment can still apply.</p></>}
        {["creating", "creation_failed"].includes(status ?? "") && <><h3>Top-up creation could not be verified.</h3><p>No credits were added. Check history before starting another attempt.</p></>}
        {["failed", "expired", "cancelled", "creation_failed"].includes(status ?? "") && <><p>A new attempt creates a separate QR. The old receipt stays in your history.</p>
          <button className="button-secondary" onClick={() => { void create(undefined, true); }} disabled={!enabled || busy}>Regenerate test QR</button></>}
        <p className="payment-order">Test top-up: {visibleTopup.id}</p></div>}
      {returnState && <p>Your earlier receipt is available in purchase history. Returning here does not verify payment.</p>}
    </section>
    {account?.authenticated && <section className="payment-account" aria-label="Your test purchases"><h2>Your test top-ups and purchases</h2>
      {account.orders?.length ? <ul className="payment-history">{account.orders.map(purchase => <li key={purchase.id}>
        <span className="payment-order">{purchase.id}</span><span>{purchaseLabel(purchase)}</span>
        {purchase.provider === "payment_intent" && <button className="button-secondary" disabled={busy} onClick={() => {
          version.current++; const next = { id: purchase.id, account_id: account.user!.id };
          sessionStorage.setItem(RECEIPT_KEY, JSON.stringify(next)); setReceipt(next); setTopup(null); setError("");
        }}>View top-up {purchase.id}</button>}</li>)}</ul> : <p>No account purchases yet.</p>}
      <button className="button-secondary" onClick={() => { void refreshAccount().catch(() => setError("Could not refresh your account. Try again.")); }}>Refresh balance</button>
    </section>}
    {error && <p className="payment-error" role="alert">{error}</p>}
  </div></main>;
}

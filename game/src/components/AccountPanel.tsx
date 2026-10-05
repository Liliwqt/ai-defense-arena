import { useState } from "react";
import { accountResponse, type Account } from "../hooks/useAccount";

export function AccountPanel({ account, refresh, error, previewMode = false }: {
  account: Account | null; refresh: () => Promise<void>; error: string; previewMode?: boolean;
}) {
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  async function redeem(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy || !account?.csrf_token) return;
    const form = event.currentTarget;
    const voucher = new FormData(form).get("voucher");
    setBusy(true); setMessage("");
    try {
      await accountResponse(await fetch("/api/auth/voucher", {
        method: "POST", headers: { "Content-Type": "application/json", "X-CSRF-Token": account.csrf_token },
        body: JSON.stringify({ voucher }),
      }));
      await refresh(); setMessage("Free access is active for your account.");
    } catch (failure) { setMessage(failure instanceof Error ? failure.message : "Could not redeem the voucher."); }
    finally { form.reset(); setBusy(false); }
  }
  async function logout() {
    if (busy || !account?.csrf_token) return;
    setBusy(true); setMessage("");
    try {
      await accountResponse(await fetch("/api/auth/logout", { method: "POST", headers: { "X-CSRF-Token": account.csrf_token } }));
      // Close the host socket and recheck its session; room credentials stay saved.
      window.location.reload();
    } catch { setMessage("Could not sign out. Please try again."); setBusy(false); }
  }
  return <section className="account-panel" aria-label="Account access">
    <p className="account-kicker">HOST ACCOUNT · SANDBOX ACCESS</p>
    {previewMode ? <p>Account actions are disabled in this visual preview.</p> : !account ? <p role="status">Loading your account…</p> : !account.authenticated ? <>
      <h2>Sign in to host a defense</h2>
      <p>Teammates can join using your room code without signing in.</p>
      {account.google_enabled ? <a className="button-primary account-login" href="/api/auth/google/login?return_to=%2F%3Faccount%3D1">Sign in with Google</a>
        : <p role="status">Google sign-in needs server configuration. Follow the README’s local account setup.</p>}
    </> : <>
      <div className="account-profile"><h2>{account.user?.name}</h2><p>{account.user?.email}</p></div>
      <div className="account-access-card">
        <strong>{account.free_access ? "Free access active" : "10 test credits per defense run"}</strong>
        <p><b>{account.test_credits ?? 0}</b> available test credits · <b>{account.reserved_credits ?? 0}</b> reserved</p>
        <p>{account.free_access ? "Your voucher covers defense runs without spending credits." : "Credits are reserved at Start and charged when the first question appears. An opening failure releases the reservation."}</p>
        <p>Sandbox fixtures only. Question count does not change the 10-credit test charge.</p>
      </div>
      {!account.free_access && account.voucher_enabled && <form onSubmit={redeem} className="account-voucher">
        <label className="setup-label">Free-access voucher<input name="voucher" type="password" required maxLength={200} autoComplete="off" className="setup-input" /></label>
        <button type="submit" className="button-primary" disabled={busy}>Redeem voucher</button>
      </form>}
      {!account.free_access && !account.voucher_enabled && <p>Voucher access is not configured on this server.</p>}
      <a className="button-secondary account-login" href="/?payments=test">Get sandbox test credits</a>
      <div><h3>Your test purchases</h3>{account.orders?.length ? <ul className="account-orders">{account.orders.map(order => <li key={order.id}><span>{order.status} · {order.credits} test credits</span><small>{order.id}</small></li>)}</ul> : <p>No test purchases yet.</p>}</div>
      <div className="account-buttons"><button className="button-secondary" disabled={busy} onClick={() => { void refresh(); }}>Refresh account</button><button className="button-secondary" disabled={busy} onClick={logout}>Sign out</button></div>
    </>}
    {new URLSearchParams(location.search).get("signin_error") && <p role="alert">Google sign-in did not finish. Please try again.</p>}
    {(message || error) && <p role="status" className="account-message">{message || error}</p>}
  </section>;
}

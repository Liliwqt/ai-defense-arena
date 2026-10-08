import { useEffect, useRef, useState } from "react";
import { accountResponse, useAccount } from "../hooks/useAccount";
import "./manager.css";

type User = { id: string; name: string; email: string; live_credits: number; live_reserved_credits: number; live_held_credits: number; test_credits: number; free_access: boolean; topup_invited: boolean };
type Tester = { email: string; enabled: boolean };
type Entry = { id: string; action: string; email: string | null; account_email: string | null; delta: number | null; reason: string; balance_after: number | null; created_at: number };
type CreditDraft = { target: User; delta: string; reason: string; direction: "add" | "remove" };
const PAGE_SIZE = 25;

export function ManagerPage() {
  const { account, error: accountError, refresh } = useAccount(false);
  const [users, setUsers] = useState<User[]>([]), [testers, setTesters] = useState<Tester[]>([]), [entries, setEntries] = useState<Entry[]>([]);
  const [query, setQuery] = useState(""), [search, setSearch] = useState(""), [offset, setOffset] = useState(0), [total, setTotal] = useState(0);
  const [email, setEmail] = useState(""), [draft, setDraft] = useState<CreditDraft | null>(null);
  const [error, setError] = useState(""), [message, setMessage] = useState(""), [busy, setBusy] = useState(false), [loading, setLoading] = useState(false), [reload, setReload] = useState(0);
  const pending = useRef(false), attempt = useRef<{ payload: string; key: string } | null>(null);
  const creditForm = useRef<HTMLFormElement>(null), creditInput = useRef<HTMLInputElement>(null);
  const owner = account?.manager_enabled === true && account.authenticated;
  const identity = account?.user?.id;
  const revision = useRef(0);

  useEffect(() => {
    if (draft) { creditForm.current?.scrollIntoView?.({ block: "start" }); creditInput.current?.focus({ preventScroll: true }); }
  }, [draft?.target.id]);

  useEffect(() => {
    const version = ++revision.current;
    setUsers([]); setTesters([]); setEntries([]); setDraft(null); attempt.current = null;
    if (!owner) return;
    let active = true;
    setLoading(true);
    void Promise.all([
      fetch(`/api/manager/users?q=${encodeURIComponent(search)}&limit=${PAGE_SIZE}&offset=${offset}`, { cache: "no-store" }).then(accountResponse),
      fetch("/api/manager/testers", { cache: "no-store" }).then(accountResponse),
      fetch("/api/manager/audit", { cache: "no-store" }).then(accountResponse),
    ]).then(([people, invitations, audit]) => {
      if (!active || revision.current !== version) return;
      setUsers(people.users); setTotal(people.total); setTesters(invitations.testers); setEntries(audit.entries); setError("");
    }).catch(failure => { if (active && revision.current === version) setError(failure instanceof Error ? failure.message : "Could not load the dashboard."); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [owner, identity, search, offset, reload]);

  async function mutate(path: string, method: string, body: object, success: string, key?: string) {
    if (pending.current || !owner || !account?.csrf_token) return;
    const version = revision.current;
    pending.current = true; setBusy(true); setError(""); setMessage("");
    try {
      await accountResponse(await fetch(path, { method, headers: { "Content-Type": "application/json", "X-CSRF-Token": account.csrf_token, ...(key ? { "Idempotency-Key": key } : {}) }, body: JSON.stringify(body) }));
      if (revision.current !== version) return;
      setMessage(success); setEmail(""); setDraft(null); attempt.current = null;
      setReload(value => value + 1); await refresh();
    } catch (failure) {
      if (revision.current === version) setError(failure instanceof Error ? failure.message : "Could not save. Your request is retained for retry.");
    } finally { pending.current = false; setBusy(false); }
  }

  function adjust(event: React.FormEvent) {
    event.preventDefault();
    if (!draft || pending.current) return;
    const amount = Number(draft.delta);
    if (!Number.isSafeInteger(amount) || amount < 1 || amount > 100000 || draft.reason.trim().length < 5) {
      setError("Enter 1–100,000 credits and a reason of at least five characters."); return;
    }
    const payload = { delta: draft.direction === "add" ? amount : -amount, reason: draft.reason.trim() };
    const signature = JSON.stringify([draft.target.id, payload]);
    if (attempt.current && attempt.current.payload !== signature) { setError("Retry the retained request before changing its details. Refresh to inspect the current balance."); return; }
    attempt.current ??= { payload: signature, key: crypto.randomUUID() };
    void mutate(`/api/manager/users/${encodeURIComponent(draft.target.id)}/credits`, "POST", payload, "Credit adjustment recorded.", attempt.current.key);
  }

  return <main className="manager-page">
    <header className="manager-header"><div><p className="account-kicker">OWNER ONLY</p><h1>Manage access and credits</h1></div><a className="button-secondary" href="/?account=1">Back to room</a></header>
    {!account ? <p role="status">Loading your account…</p> : !account.authenticated ? <section className="manager-card"><h2>Sign in to manage</h2>{account.google_enabled ? <a className="button-primary" href="/api/auth/google/login?return_to=%2F%3Fmanager%3D1">Sign in with Google</a> : <p>Google sign-in needs server configuration.</p>}</section> : !owner ? <p role="alert">This dashboard is available only to the configured owner account.</p> : <>
      <p>Signed in as {account.user?.email}. Invitations enable new top-ups; voucher access remains available to all signed-in users.</p>
      <section className="manager-card"><h2>Top-up testers</h2>
        <form onSubmit={event => { event.preventDefault(); void mutate("/api/manager/testers", "PUT", { email, enabled: true }, "Tester invitation enabled."); }}>
          <label>Google email<input type="email" required maxLength={254} value={email} onChange={event => setEmail(event.target.value)} disabled={busy}/></label>
          <button className="button-primary" disabled={busy || loading}>Add tester</button>
        </form>
        <ul className="manager-list">{testers.map(tester => <li key={tester.email}><div><strong>{tester.email}</strong><p>{tester.enabled ? "Top-ups enabled" : "Top-ups disabled"}</p></div><button className="button-secondary" disabled={busy || loading} onClick={() => void mutate("/api/manager/testers", "PUT", { email: tester.email, enabled: !tester.enabled }, "Tester access updated.")}>{tester.enabled ? "Disable" : "Enable"}<span className="sr-only"> top-ups for {tester.email}</span></button></li>)}</ul>
        {!loading && !testers.length && <p>No tester invitations yet. You can invite an email before its first sign-in.</p>}
      </section>
      <section className="manager-card"><h2>Registered users</h2>
        <form onSubmit={event => { event.preventDefault(); setSearch(query.trim()); setOffset(0); }}><label>Search users<input type="search" value={query} onChange={event => setQuery(event.target.value)} disabled={busy}/></label><button className="button-secondary" disabled={busy}>Search</button></form>
        <p>{total} registered users{search ? " matching this search" : ""}. Credits below are live credits; test history stays separate.</p>
        <ul className="manager-list">{users.map(user => <li key={user.id}><div><strong>{user.name}</strong><p>{user.email}</p><p>{user.live_credits} available · {user.live_reserved_credits} reserved · {user.live_held_credits} held</p><p>{user.free_access ? "Voucher active" : "No active voucher"} · {user.topup_invited ? "Top-ups enabled" : "Top-ups disabled"} · {user.test_credits} test credits</p></div><button className="button-secondary" disabled={busy || loading} onClick={() => { if (attempt.current) { setError("Retry the retained credit request or refresh the dashboard first."); return; } setDraft({ target: user, direction: "add", delta: "10", reason: "" }); }}>Edit credits<span className="sr-only"> for {user.email}</span></button></li>)}</ul>
        <div className="manager-actions"><button className="button-secondary" disabled={busy || loading || offset === 0} onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}>Previous users</button><button className="button-secondary" disabled={busy || loading || offset + PAGE_SIZE >= total} onClick={() => setOffset(offset + PAGE_SIZE)}>Next users</button></div>
        {draft && <form ref={creditForm} className="manager-adjustment" onSubmit={adjust}><h3>Edit live credits for {draft.target.email}</h3><p>Current available balance: {draft.target.live_credits}. Changes are recorded with your account and reason. Reserved and held credits cannot be removed.</p>
          <label>Adjustment<select value={draft.direction} disabled={busy || !!attempt.current} onChange={event => setDraft({ ...draft, direction: event.target.value as "add" | "remove" })}><option value="add">Add credits</option><option value="remove">Remove credits</option></select></label>
          <label>Credits<input ref={creditInput} type="number" min="1" max="100000" step="1" required value={draft.delta} disabled={busy || !!attempt.current} onChange={event => setDraft({ ...draft, delta: event.target.value })}/></label>
          <label>Reason<textarea minLength={5} maxLength={255} required value={draft.reason} disabled={busy || !!attempt.current} onChange={event => setDraft({ ...draft, reason: event.target.value })}/></label>
          <button className="button-primary" disabled={busy}>{attempt.current ? "Retry credit adjustment" : "Confirm credit adjustment"}</button><button type="button" className="button-secondary" disabled={busy} onClick={() => { setDraft(null); attempt.current = null; }}>Close</button>
        </form>}
      </section>
      <section className="manager-card"><h2>Recent changes</h2><ul className="manager-list">{entries.map(entry => <li key={entry.id}><div><strong>{entry.account_email ?? entry.email}</strong><p>{entry.reason}{entry.delta !== null ? ` · ${entry.delta > 0 ? "+" : ""}${entry.delta} credits · ${entry.balance_after} available after change` : ""}</p><time dateTime={new Date(entry.created_at * 1000).toISOString()}>{new Date(entry.created_at * 1000).toLocaleString()}</time></div></li>)}</ul>{!loading && !entries.length && <p>No changes recorded yet.</p>}</section>
      <button className="button-secondary" disabled={busy} onClick={() => { setReload(value => value + 1); void refresh(); }}>Refresh dashboard</button>
      {loading && <p role="status">Loading dashboard…</p>}{busy && <p role="status">Saving…</p>}
    </>}
    {(error || accountError || message) && <div className="manager-feedback">{(error || accountError) && <p role="alert">{error || accountError}</p>}{message && <p role="status">{message}</p>}</div>}
  </main>;
}

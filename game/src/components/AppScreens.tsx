import type { ReactNode } from "react";
import { AccountPanel } from "./AccountPanel";
import type { Account } from "../hooks/useAccount";

interface AppPageProps {
  kicker: string;
  title: string;
  notice?: string | null;
  actions?: ReactNode;
  children: ReactNode;
}

/** One full-screen app page. Hidden room content stays mounted behind it. */
export function AppPage({ kicker, title, notice, actions, children }: AppPageProps) {
  return (
    <section className="app-page" aria-labelledby="app-screen-title">
      <div className="app-page-inner">
        <header className="app-page-header">
          <div className="app-page-brand">
            <img className="brand-icon" src="/ai-defense-arena-icon.png" width="35" height="35" alt="" />
            <span>AI Defense Arena</span>
          </div>
          <div className="app-page-actions">{actions}</div>
        </header>
        <div className="app-page-intro">
          <p className="app-page-kicker">{kicker}</p>
          <h1 id="app-screen-title" tabIndex={-1}>{title}</h1>
          {notice && <p className="app-page-notice" role="status">{notice}</p>}
        </div>
        {children}
      </div>
    </section>
  );
}

export function AccountScreen({ account, error, refresh, previewMode, onBack }: {
  account: Account | null;
  error: string;
  refresh: () => Promise<void>;
  previewMode: boolean;
  onBack: () => void;
}) {
  return (
    <AppPage kicker="HOST ACCOUNT · PRIVATE TO YOU" title="Account"
      actions={<button type="button" className="button-secondary" onClick={onBack}>Back to Home</button>}>
      <AccountPanel account={account} refresh={refresh} error={error} previewMode={previewMode} />
    </AppPage>
  );
}

export function SignInScreen({ account, onBack, onAccount }: {
  account: Account | null;
  onBack: () => void;
  onAccount: () => void;
}) {
  return (
    <AppPage kicker="HOST ACCOUNT · SIGN IN" title="Sign in"
      actions={<button type="button" className="button-secondary" onClick={onBack}>Back to Home</button>}>
      <section className="app-card" aria-labelledby="signin-card-title">
        <h2 id="signin-card-title">Host a defense</h2>
        {!account ? <p className="app-status" role="status">Loading your account…</p>
          : account.authenticated ? <>
            <p className="app-status" role="status">You’re signed in{account.user?.name ? ` as ${account.user.name}` : ""}.</p>
            <button type="button" className="button-secondary" onClick={onAccount}>Go to Account</button>
          </> : <>
            <p>Teammates can join using your room code without signing in.</p>
            {account.google_enabled
              ? <a className="button-primary account-login" href="/api/auth/google/login?return_to=%2F%3Faccount%3D1">Sign in with Google</a>
              : <p className="app-status" role="status">Google sign-in needs server configuration. Follow the README’s local account setup.</p>}
          </>}
      </section>
    </AppPage>
  );
}

export function HomeScreen({ onCreate, onJoin, roomCode, onReturnToRoom, ownerHref, notice }: {
  onCreate: () => void;
  onJoin: () => void;
  roomCode?: string | null;
  onReturnToRoom?: () => void;
  ownerHref?: string | null;
  notice?: string | null;
}) {
  return (
    <AppPage kicker="AI DEFENSE ARENA" title="Home" notice={notice}
      actions={ownerHref ? <a className="button-secondary" href={ownerHref}>Owner dashboard</a> : null}>
      <div className="app-choice-grid">
        <section className="app-card" aria-labelledby="home-create-title">
          <span className="app-number" aria-hidden="true">01</span>
          <h2 id="home-create-title">Create a defense</h2>
          <p>Upload your code or paper, prepare the panel and invite your team.</p>
          <button type="button" className="button-primary" onClick={onCreate}>Create a defense</button>
        </section>
        <section className="app-card" aria-labelledby="home-join-title">
          <span className="app-number" aria-hidden="true">02</span>
          <h2 id="home-join-title">Join a room</h2>
          <p>Have a room code? Join your team without a Google account.</p>
          <button type="button" className="button-secondary" onClick={onJoin}>Join a room</button>
        </section>
        {roomCode && onReturnToRoom && (
          <section className="app-card" aria-labelledby="home-return-title">
            <span className="app-number" aria-hidden="true">03</span>
            <h2 id="home-return-title">Your room is still open</h2>
            <p>Return to room {roomCode} with your seat, question and drafts kept.</p>
            <button type="button" className="button-secondary" onClick={onReturnToRoom}>Return to your room {roomCode}</button>
          </section>
        )}
      </div>
    </AppPage>
  );
}

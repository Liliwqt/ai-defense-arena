import type { ReactNode } from "react";
import { AccountPanel, GoogleSignIn } from "./AccountPanel";
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

/** Guided preparation progress: a description of the flow, not room authority. */
export function PreparationSteps({ current, onSelect, hasRoom = false }: { current: 1 | 2 | 3; onSelect?: (step: 1 | 2 | 3) => void; hasRoom?: boolean }) {
  const steps = ["Upload", "Review", "Defend"];
  return (
    <ol className="prepare-steps" aria-label="Preparation steps">
      {steps.map((label, index) => {
        const number = index + 1;
        return (
          <li key={label} className="prepare-step" aria-current={number === current ? "step" : undefined}>
            <button type="button" aria-current={number === current ? "step" : undefined}
              disabled={number > 1 && !hasRoom} onClick={() => onSelect?.(number as 1 | 2 | 3)}>
              {number} · {label}
            </button>
          </li>
        );
      })}
    </ol>
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

export function SignInScreen({ account, error, onRetry, onBack, onAccount, onJoin }: {
  account: Account | null;
  onBack: () => void;
  onAccount: () => void;
  onJoin: () => void;
  error?: string;
  onRetry: () => void;
}) {
  return (
    <AppPage kicker="HOST ACCOUNT · SIGN IN" title="Sign in"
      actions={<button type="button" className="button-secondary" onClick={onBack}>Back to Home</button>}>
      <section className="app-card" aria-labelledby="signin-card-title">
        <h2 id="signin-card-title">Host a defense</h2>
        {!account ? error ? <>
          <p className="app-status" role="alert">{error}</p>
          <button type="button" className="button-secondary" onClick={onRetry}>Retry account</button>
        </> : <p className="app-status" role="status">Loading your account…</p>
          : account.authenticated ? <>
            <p className="app-status" role="status">You’re signed in{account.user?.name ? ` as ${account.user.name}` : ""}.</p>
            <button type="button" className="button-secondary" onClick={onAccount}>Go to Account</button>
          </> : <>
            <p>Teammates can join using your room code without signing in.</p>
            <GoogleSignIn googleEnabled={!!account.google_enabled} />
          </>}
        <button type="button" className="button-secondary" onClick={onJoin}>Join a room</button>
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

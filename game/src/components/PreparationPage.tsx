import type { ReactNode } from "react";

interface Props {
  open: boolean;
  title: string;
  onClose: () => void;
  kicker?: string;
  steps?: ReactNode;
  onHome?: () => void;
  onAccount?: () => void;
  description?: string;
  introContent?: ReactNode;
  children: ReactNode;
}

/** Persistent page content retains in-memory forms while another screen is open. */
export function PreparationPage({ open, title, onClose, kicker, steps, onHome, onAccount, description, introContent, children }: Props) {
  return (
    <div
        id="preparation-page"
        aria-labelledby="app-screen-title"
        className="app-surface"
        hidden={!open}
      >
        <div className="app-surface-header">
          <div className="app-page-brand">
            <img className="brand-icon" src="/ai-defense-arena-icon.png" width="35" height="35" alt="" />
            <span>AI Defense Arena<small>PREPARE WITH PURPOSE</small></span>
          </div>
          <div className="app-page-actions">
          {onAccount && <button type="button" className="button-secondary" onClick={onAccount}>Account ↗</button>}
          <button
            type="button"
            id="preparation-back"
            aria-label="Back"
            onClick={onClose}
            className="button-secondary app-surface-back"
          >
            Back
          </button>
          </div>
        </div>
        <div className="guided-navigation">{onHome && <button type="button" className="button-secondary" onClick={onHome}>Home</button>}{steps}</div>
        <div className="app-surface-inner-split">
          {/* Stable slot: children remain mounted during ordinary page navigation. */}
          <div className="app-surface-main">
            <div className="guided-intro">
              {kicker && <p className="app-page-kicker">{kicker}</p>}
              <h1 id={open ? "app-screen-title" : undefined} className="app-surface-title" tabIndex={-1}>{title}</h1>
              {description && <p className="guided-lede">{description}</p>}
              {introContent}
            </div>
            {children}
          </div>
        </div>
    </div>
  );
}

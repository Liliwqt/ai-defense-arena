import { useEffect, useRef } from "react";
import type { DrawerMode } from "../types";

interface DrawerProps {
  open: boolean;
  mode: DrawerMode;
  title: string;
  onClose: () => void;
  /** "overlay" is the in-room side drawer; "page" is a full-screen preparation surface. */
  variant?: "overlay" | "page";
  kicker?: string;
  steps?: React.ReactNode;
  onHome?: () => void;
  onAccount?: () => void;
  description?: string;
  children: React.ReactNode;
}

export function Drawer({ open, mode, title, onClose, variant = "overlay", kicker, steps, onHome, onAccount, description, children }: DrawerProps) {
  const isPage = variant === "page";
  const closeButtonRef = useRef<HTMLButtonElement>(null);
  const drawerRef = useRef<HTMLDivElement>(null);
  const returnFocusRef = useRef<HTMLElement | null>(null);
  const wasOpenRef = useRef(false);

  // Place focus inside the dialog and restore it to its opener when dismissed.
  // Full-screen pages announce their own heading instead of grabbing the Back control.
  useEffect(() => {
    if (isPage) return;
    if (open) {
      if (!wasOpenRef.current) {
        returnFocusRef.current = document.activeElement as HTMLElement | null;
        wasOpenRef.current = true;
      }
      closeButtonRef.current?.focus();
    } else if (wasOpenRef.current) {
      wasOpenRef.current = false;
      const opener = returnFocusRef.current;
      // Never restore focus into hidden content (the room stays mounted off-screen).
      if (opener?.isConnected && !opener.closest("[hidden]")) opener.focus();
      returnFocusRef.current = null;
    }
  }, [open, mode, isPage]);

  // Escape key + Tab trap are overlay behaviour; a page is left with its Back action.
  useEffect(() => {
    if (!open || isPage) return;

    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") {
        e.preventDefault();
        onClose();
        return;
      }
      if (e.key !== "Tab") return;
      const drawer = drawerRef.current;
      if (!drawer) return;
      const focusable = Array.from(
        drawer.querySelectorAll<HTMLElement>(
          "a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), summary, [tabindex='0']",
        ),
      ).filter(
        (el) =>
          !el.closest("[hidden]") &&
          !el.closest("[aria-hidden='true']") &&
          el.getClientRects().length > 0,
      );
      if (!focusable.length) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    }

    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [open, isPage, onClose]);

  // The panel and its children keep the same element slots whether the variant is
  // overlay or page, so preparation drafts and file selections never remount.
  return (
    <>
      {!isPage && (
        <div id="drawer-scrim" className="drawer-scrim" hidden={!open} onClick={onClose} aria-hidden="true" />
      )}
      <div
        id="drawer"
        ref={drawerRef}
        role={isPage ? undefined : "dialog"}
        aria-modal={isPage ? undefined : true}
        aria-labelledby={isPage ? "app-screen-title" : "drawer-title"}
        className={isPage ? "app-surface" : "drawer-panel"}
        hidden={!open}
        style={isPage ? undefined : { width: "min(460px, 100vw)", height: "100dvh" }}
      >
        <div className={isPage ? "app-surface-header" : "drawer-header"}>
          {isPage ? (
            <div className="app-page-brand">
              <img className="brand-icon" src="/ai-defense-arena-icon.png" width="35" height="35" alt="" />
              <span>AI Defense Arena<small>PREPARE WITH PURPOSE</small></span>
            </div>
          ) : (
            <div>
              <p className="drawer-kicker">DEFENSE ROOM</p>
              <h2 id="drawer-title" className="drawer-title">{title}</h2>
            </div>
          )}
          <div className="app-page-actions">
          {isPage && onAccount && <button type="button" className="button-secondary" onClick={onAccount}>Account ↗</button>}
          <button
            ref={closeButtonRef}
            type="button"
            id="drawer-close"
            aria-label={isPage ? "Back" : "Close panel"}
            onClick={onClose}
            className={isPage ? "button-secondary app-surface-back" : "drawer-close"}
          >
            {isPage ? "Back" : <>Close <span aria-hidden="true" className="text-[1.15rem] align-[-1px] ml-1">×</span></>}
          </button>
          </div>
        </div>
        {isPage ? <div className="guided-navigation">{onHome && <button type="button" className="button-secondary" onClick={onHome}>Home</button>}{steps}</div> : null}
        <div className={isPage ? "app-surface-inner-split" : "drawer-body"} style={isPage ? undefined : { overscrollBehavior: "contain" }}>
          {/* Stable slot: children never remount when the variant changes. */}
          <div className={isPage ? "app-surface-main" : "drawer-main"}>
            {isPage && <div className="guided-intro">
              {kicker && <p className="app-page-kicker">{kicker}</p>}
              <h1 id={open ? "app-screen-title" : undefined} className="app-surface-title" tabIndex={-1}>{title}</h1>
              {description && <p className="guided-lede">{description}</p>}
            </div>}
            {children}
          </div>
        </div>
      </div>
    </>
  );
}

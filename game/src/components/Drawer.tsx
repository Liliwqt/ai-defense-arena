import { useEffect, useRef } from "react";
import type { DrawerMode } from "../types";

interface DrawerProps {
  open: boolean;
  mode: DrawerMode;
  title: string;
  onClose: () => void;
  children: React.ReactNode;
}

export function Drawer({ open, mode, title, onClose, children }: DrawerProps) {
  const closeButtonRef = useRef<HTMLButtonElement>(null);
  const drawerRef = useRef<HTMLElement>(null);
  const returnFocusRef = useRef<HTMLElement | null>(null);
  const wasOpenRef = useRef(false);

  // Place focus inside the dialog and restore it to its opener when dismissed.
  useEffect(() => {
    if (open) {
      if (!wasOpenRef.current) {
        returnFocusRef.current = document.activeElement as HTMLElement | null;
        wasOpenRef.current = true;
      }
      closeButtonRef.current?.focus();
    } else if (wasOpenRef.current) {
      wasOpenRef.current = false;
      if (returnFocusRef.current?.isConnected) returnFocusRef.current.focus();
      returnFocusRef.current = null;
    }
  }, [open, mode]);

  // Escape key + Tab trap
  useEffect(() => {
    if (!open) return;

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
  }, [open, onClose]);

  if (!open) return null;

  return (
    <>
      {/* Scrim */}
      <div
        id="drawer-scrim"
        className="drawer-scrim"
        onClick={onClose}
        aria-hidden="true"
      />
      {/* Panel */}
      <aside
        id="drawer"
        ref={drawerRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="drawer-title"
        className="drawer-panel"
        style={{ width: "min(460px, 100vw)", height: "100dvh" }}
      >
        {/* Header */}
        <div className="drawer-header">
          <div>
            <p className="drawer-kicker">
              DEFENSE ROOM
            </p>
            <h2 id="drawer-title" className="drawer-title">
              {title}
            </h2>
          </div>
          <button
            ref={closeButtonRef}
            type="button"
            id="drawer-close"
            aria-label="Close panel"
            onClick={onClose}
            className="drawer-close"
          >
            Close <span aria-hidden="true" className="text-[1.15rem] align-[-1px] ml-1">×</span>
          </button>
        </div>
        {/* Body */}
        <div
          className="drawer-body"
          style={{ overscrollBehavior: "contain" }}
        >
          {children}
        </div>
      </aside>
    </>
  );
}

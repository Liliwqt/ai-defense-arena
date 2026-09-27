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
          "button:not([disabled]), input:not([disabled]), textarea:not([disabled])",
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
        className="fixed inset-0 z-[9] bg-[#020913a8]"
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
        className="fixed inset-y-0 right-0 z-10 flex flex-col drawer-panel"
        style={{ width: "min(460px, 100vw)", height: "100dvh" }}
      >
        {/* Header */}
        <div className="flex-none flex items-center justify-between gap-3 p-[19px_20px] border-b border-[#304e6b] bg-[#122943]">
          <div>
            <p className="text-[#85acd4] text-[0.68rem] font-black tracking-[0.16em] m-0 mb-1">
              DEFENSE ROOM
            </p>
            <h2 id="drawer-title" className="text-[1.35rem] m-0 text-[#eaf2ff]">
              {title}
            </h2>
          </div>
          <button
            ref={closeButtonRef}
            type="button"
            id="drawer-close"
            aria-label="Close panel"
            onClick={onClose}
            className="border border-[#56799b] rounded-[9px] bg-[#294b69] text-[#f1f8ff] p-[8px_10px] text-[0.81rem] font-black"
          >
            Close <span aria-hidden="true" className="text-[1.15rem] align-[-1px] ml-1">×</span>
          </button>
        </div>
        {/* Body */}
        <div
          className="flex-1 min-h-0 overflow-auto p-5"
          style={{ overscrollBehavior: "contain" }}
        >
          {children}
        </div>
      </aside>
    </>
  );
}

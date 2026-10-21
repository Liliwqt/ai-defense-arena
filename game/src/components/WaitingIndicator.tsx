import { useEffect, useRef, useState } from "react";

interface WaitingIndicatorProps {
  label: string;
  detail?: string;
  active?: boolean;
  startedAtMs?: number | null;
  serverNowMs?: number;
  className?: string;
}

function elapsedText(milliseconds: number): string {
  const seconds = Math.floor(milliseconds / 1000);
  return seconds < 60 ? `${seconds}s` : `${Math.floor(seconds / 60)}m ${String(seconds % 60).padStart(2, "0")}s`;
}

export function WaitingIndicator({ label, detail, active = true, startedAtMs = null,
                                    serverNowMs, className }: WaitingIndicatorProps) {
  const anchor = useRef({ wall: Date.now(), server: serverNowMs ?? 0 });
  const [, tick] = useState(0);
  useEffect(() => {
    anchor.current = { wall: Date.now(), server: serverNowMs ?? 0 };
  }, [serverNowMs, startedAtMs]);
  useEffect(() => {
    if (!active || startedAtMs === null || serverNowMs === undefined) return;
    const interval = window.setInterval(() => tick(value => value + 1), 1000);
    return () => window.clearInterval(interval);
  }, [active, startedAtMs, serverNowMs]);
  const elapsed = startedAtMs !== null && serverNowMs !== undefined
    ? Math.max(0, anchor.current.server - startedAtMs + Math.max(0, Date.now() - anchor.current.wall))
    : null;
  return (
    <span className={`waiting-status ${active ? "is-active" : "is-static"}${className ? ` ${className}` : ""}`}
      role="status" aria-live="polite" aria-busy={active || undefined}>
      <span className="waiting-dots" aria-hidden="true"><i /><i /><i /></span>
      <span className="waiting-label">{label}</span>
      {elapsed !== null && <span className="waiting-elapsed" aria-hidden="true">{elapsedText(elapsed)}</span>}
      {detail && <span className="waiting-detail">{detail}</span>}
    </span>
  );
}

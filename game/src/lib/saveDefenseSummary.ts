type NativeExport = { filename: string; text: string };
let androidPort: MessagePort | null = null;

// Android transfers a port only to the configured top-level website origin.
// Reject cross-origin windows; native delivery has a null source.
window.addEventListener("message", (event: MessageEvent) => {
  if (window !== window.top || event.data !== "defense-export-port" || event.ports.length !== 1) return;
  if (event.source !== null && (event.source !== window || event.origin !== window.location.origin)) return;
  androidPort?.close();
  androidPort = event.ports[0];
});

export function isNativeShell(): boolean {
  const native = window as unknown as { webkit?: { messageHandlers?: { defenseExport?: unknown } } };
  return window === window.top && Boolean(androidPort || native.webkit?.messageHandlers?.defenseExport);
}

export function saveDefenseSummary(filename: string, text: string): void {
  const payload: NativeExport = { filename, text };
  const native = window as unknown as { webkit?: { messageHandlers?: { defenseExport?: { postMessage: (value: NativeExport) => void } } } };
  if (native.webkit?.messageHandlers?.defenseExport && window === window.top) {
    native.webkit.messageHandlers.defenseExport.postMessage(payload);
    return;
  }
  if (androidPort) { androidPort.postMessage(JSON.stringify(payload)); return; }
  const url = URL.createObjectURL(new Blob([text], { type: "text/plain;charset=utf-8" }));
  const link = document.createElement("a");
  link.href = url; link.download = filename;
  document.body.appendChild(link); link.click(); link.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 0);
}

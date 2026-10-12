import { useEffect, useRef, useState } from "react";
import type { PDFDocumentProxy, PDFDocumentLoadingTask, RenderTask, TextLayer } from "pdfjs-dist";
import workerUrl from "pdfjs-dist/legacy/build/pdf.worker.min.mjs?url";
import type { RoomState } from "../types";
import "./pdfViewer.css";
import { usePaperNavigation } from "../hooks/usePaperNavigation";
import { highlightCitation } from "../lib/pdfHighlight";

interface Props { roomState: RoomState; playerToken?: string | null; expanded?: boolean; onExpandedChange?: (value: boolean) => void; }

export function PDFViewer({roomState, playerToken, expanded = false, onExpandedChange}: Props) {
  const turn = roomState.turns.at(-1);
  const {document, page, zoom, selectDocument, selectPage, setZoom, returnToCitation} = usePaperNavigation(roomState);
  const expandRef = useRef<HTMLButtonElement>(null);
  const readingRef = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(600);
  const [pdf, setPdf] = useState<{id: string; source: PDFDocumentProxy} | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [retry, setRetry] = useState(0);
  const [highlighted, setHighlighted] = useState<boolean | null>(null);
  const pageRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const reading = readingRef.current;
    if (!reading || typeof ResizeObserver === "undefined") return;
    const observer = new ResizeObserver(entries => {
      const measured = entries[0]?.contentRect.width;
      if (measured > 0) setWidth(measured);
    });
    observer.observe(reading);
    return () => observer.disconnect();
  }, []);
  useEffect(() => {
    let current = true;
    let task: PDFDocumentLoadingTask | undefined;
    setPdf(null); setError(null); setLoading(true); setHighlighted(null);
    if (!document || !playerToken) { setLoading(false); setError("Reconnect to view this room’s paper."); return; }
    void import("pdfjs-dist/legacy/build/pdf.mjs").then(api => {
      if (!current) return;
      api.GlobalWorkerOptions.workerSrc = workerUrl;
      task = api.getDocument({url: `/api/rooms/${encodeURIComponent(roomState.room_code)}/documents/${encodeURIComponent(document.id)}`,
        httpHeaders: {"X-Player-Token": playerToken}, disableRange: true,
        cMapUrl: "/pdf-assets/cmaps/", cMapPacked: true, standardFontDataUrl: "/pdf-assets/standard_fonts/", wasmUrl: "/pdf-assets/wasm/"});
      return task.promise.then(result => { if (current) setPdf({id: document.id, source: result}); });
    }).catch(() => { if (current) { setError("Could not load this paper. Check your room access and retry."); setLoading(false); } });
    return () => { current = false; void task?.destroy()?.catch(() => {}); };
  }, [roomState.room_code, document?.id, playerToken, retry]);

  useEffect(() => {
    setHighlighted(null);
    if (!pdf || pdf.id !== document?.id || !pageRef.current) return;
    let current = true;
    let render: RenderTask | undefined;
    let text: TextLayer | undefined;
    const host = pageRef.current;
    setLoading(true);
    setError(null);
    const canvas = window.document.createElement("canvas");
    const layer = window.document.createElement("div"); layer.className = "textLayer";
    host.replaceChildren(canvas, layer);
    void Promise.all([pdf.source.getPage(page), import("pdfjs-dist/legacy/build/pdf.mjs")]).then(async ([source, api]) => {
      if (!current) return;
      const natural = source.getViewport({scale: 1});
      const scale = width / natural.width * zoom;
      const viewport = source.getViewport({scale});
      host.style.width = `${viewport.width}px`; host.style.height = `${viewport.height}px`;
      host.style.setProperty("--total-scale-factor", String(scale));
      // Bound the canvas allocation even for unusually tall pages or high zoom.
      const ratio = Math.min(window.devicePixelRatio || 1, 2,
        8192 / Math.max(viewport.width, viewport.height), Math.sqrt(16_000_000 / (viewport.width * viewport.height)));
      canvas.width = Math.ceil(viewport.width * ratio); canvas.height = Math.ceil(viewport.height * ratio);
      canvas.style.width = `${viewport.width}px`; canvas.style.height = `${viewport.height}px`;
      const context = canvas.getContext("2d");
      if (!context) throw Error("Canvas unavailable");
      render = source.render({canvas, canvasContext: context, viewport, transform: [ratio, 0, 0, ratio, 0, 0]});
      await render.promise;
      const content = await source.getTextContent();
      if (!current) return;
      text = new api.TextLayer({container: layer, textContentSource: content, viewport});
      await text.render();
      if (current) {
        const cited = Boolean(turn && turn.evidence_document_id === document?.id && turn.evidence_page === page);
        setHighlighted(cited && turn ? highlightCitation(layer, host, turn.evidence_text) : false);
        setLoading(false);
      }
    }).catch(() => { if (current) { setError("Could not render this page. Retry paper loading."); setLoading(false); } });
    return () => { current = false; render?.cancel(); text?.cancel(); host.replaceChildren(); };
  }, [pdf, page, width, zoom, document?.id, turn?.evidence_document_id, turn?.evidence_page, turn?.evidence_text]);

  const exitReading = () => { onExpandedChange?.(false); expandRef.current?.focus(); };
  return <section className="pdf-viewer" aria-label="Original PDF" onKeyDown={event => {
    if (expanded && event.key === "Escape") { event.preventDefault(); event.stopPropagation(); exitReading(); }
  }}>
    {turn?.evidence_document_id && <div className="pdf-exact-quote">
      <p className="pdf-quote-filename">{turn.filename}</p>
      <p>Exact extracted quotation · {turn.evidence_location}</p>
      <pre tabIndex={0} aria-label="Exact extracted quotation">{turn.evidence_text}</pre>
      {highlighted !== null && <p role="status">{highlighted ? "Cited text highlighted" : "Precise highlight unavailable"}</p>}
    </div>}
    <div className="pdf-reading" role="tabpanel" id="paper-reading-panel" aria-labelledby="paper-tab-paper">
    <div className="pdf-toolbar" role="group" aria-label="Paper reading controls">
      <label>Document <select aria-label="PDF document" value={document?.id ?? ""} onChange={event => selectDocument(event.target.value)}>
        {roomState.documents?.map(item => <option key={item.id} value={item.id}>{item.filename}</option>)}
      </select></label>
      <button type="button" aria-label="Previous page" disabled={page <= 1} onClick={() => selectPage(page - 1)}>←</button>
      <button type="button" aria-label="Next page" disabled={page >= (document?.page_count ?? 1)} onClick={() => selectPage(page + 1)}>→</button>
      <button type="button" aria-label="Zoom out" disabled={zoom <= .5} onClick={() => setZoom(Math.max(.5, zoom - .25))}>−</button>
      <span aria-label="Zoom level">{Math.round(zoom * 100)}%</span>
      <button type="button" aria-label="Zoom in" disabled={zoom >= 3} onClick={() => setZoom(Math.min(3, zoom + .25))}>+</button>
      <button type="button" onClick={() => setZoom(1)}>Fit width</button>
      <button type="button" disabled={!turn?.evidence_document_id} onClick={returnToCitation}>Return to citation</button>
      <button ref={expandRef} type="button" aria-expanded={expanded} onClick={() => expanded ? exitReading() : onExpandedChange?.(true)}>{expanded ? "Exit expanded reading" : "Expand paper"}</button>
    </div>
    <p className="pdf-document-title">{document?.filename} · Physical page {page} of {document?.page_count}</p>
    {loading && <p role="status">Loading paper…</p>}
    {error && <div role="alert"><p>{error}</p><button type="button" onClick={() => setRetry(value => value + 1)}>Retry paper</button></div>}
    <div ref={readingRef} className="pdf-page-scroll" tabIndex={0} aria-label="PDF page"><div ref={pageRef} className="pdf-page" /></div>
    </div>
  </section>;
}

import { citationLocationLabel, parseCitationLocation } from "../lib/citation";

interface PageCitationProps {
  filename: string;
  evidence?: string;
  location?: string;
}

/**
 * Present a citation from an uploaded research document as a document page rather
 * than as source code.
 *
 * The server extracts PDF text with pypdf and discards the original file, so this
 * is the extracted text laid out like a page, not a faithful render of the PDF. The
 * fidelity note below says so plainly rather than letting the page framing imply
 * otherwise. Code citations never reach this component; they keep the monospace
 * source block in QuestionCard.
 */
export function PageCitation({ filename, evidence, location }: PageCitationProps) {
  const parsed = parseCitationLocation(location);
  const label = citationLocationLabel(location);
  const where = label || "Cited excerpt";

  return (
    <div
      id="page-citation"
      role="group"
      aria-label={`Cited document text from ${filename}, ${where}`}
      tabIndex={0}
    >
      <div className="page-citation-header">
        <span className="page-citation-file" title={filename}>{filename}</span>
        <span className="page-citation-where">
          {parsed.page ? `Page ${parsed.page}` : label}
          {parsed.line ? <span className="page-citation-line"> · line {parsed.line}</span> : null}
        </span>
      </div>
      <div className="page-citation-body">
        <p className="page-citation-text">{evidence ?? ""}</p>
      </div>
      <p className="page-fidelity-note">
        Text extracted from the uploaded document. Figures, tables, and equations are not shown.
      </p>
    </div>
  );
}

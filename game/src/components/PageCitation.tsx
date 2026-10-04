import { citationLocationLabel, parseCitationLocation } from "../lib/citation";

interface PageCitationProps {
  id?: string;
  filename: string;
  evidence?: string;
  location?: string;
  before?: string;
  after?: string;
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
 *
 * A PDF has no sentences, only visual lines, so the cited line alone often opens
 * without its subject or ends after a conjunction. When the server supplies
 * neighbouring lines they are shown as dimmed context above and below, with the
 * cited line itself emphasized, so the passage reads as prose while "the exact
 * cited line" stays visually distinct and remains exactly the text the server
 * validated.
 */
export function PageCitation({ id = "page-citation", filename, evidence, location, before, after }: PageCitationProps) {
  const parsed = parseCitationLocation(location);
  const label = citationLocationLabel(location);
  const where = label || "Cited excerpt";
  const hasContext = Boolean(before || after);

  return (
    <div
      id={id}
      className="page-citation"
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
        {hasContext ? (
          <div className="page-citation-passage">
            {before ? <p className="page-citation-context">{before}</p> : null}
            <p className="page-citation-text is-cited">{evidence ?? ""}</p>
            {after ? <p className="page-citation-context">{after}</p> : null}
          </div>
        ) : (
          <p className="page-citation-text">{evidence ?? ""}</p>
        )}
      </div>
      <p className="page-fidelity-note">
        {hasContext
          ? "The cited line is highlighted. Neighbouring lines are shown for context. Text extracted from the uploaded document; figures, tables, and equations are not shown."
          : "Text extracted from the uploaded document. Figures, tables, and equations are not shown."}
      </p>
    </div>
  );
}

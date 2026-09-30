/**
 * Helpers for reading a server-supplied citation location.
 *
 * `evidence_location` is built in `research_files.py` and reaches the client as a
 * plain string. PDF citations look like "Page 4 · extracted line 12"; DOCX, TXT and
 * Markdown citations carry a bare label with no page. Everything here is defensive:
 * the value is optional and server-controlled, so an unrecognised string must
 * degrade to the raw text rather than break the question card.
 */

export interface CitationLocation {
  /** 1-based page number for PDF citations. */
  page?: number;
  /** 1-based extracted line number within the page, when the server reported one. */
  line?: number;
  /** Non-page label, e.g. a DOCX paragraph reference. */
  label?: string;
  /** The original string, always preserved for display. */
  raw: string;
}

const PAGE_LINE = /^Page\s+(\d+)\s*(?:·|·)\s*extracted line\s+(\d+)$/i;
const PAGE_ONLY = /^Page\s+(\d+)$/i;
const LEADING_PAGE = /^Page\s+(\d+)\s*(?:·|·)\s*(.+)$/i;

/** Parse a citation location into structured parts. Never throws. */
export function parseCitationLocation(location?: string | null): CitationLocation {
  const raw = typeof location === "string" ? location.trim() : "";
  if (!raw) return { raw: "" };

  const pageAndLine = raw.match(PAGE_LINE);
  if (pageAndLine) {
    return { page: Number(pageAndLine[1]), line: Number(pageAndLine[2]), raw };
  }

  const pageOnly = raw.match(PAGE_ONLY);
  if (pageOnly) return { page: Number(pageOnly[1]), raw };

  const pageWithLabel = raw.match(LEADING_PAGE);
  if (pageWithLabel) return { page: Number(pageWithLabel[1]), label: pageWithLabel[2].trim(), raw };

  const trailingLine = raw.match(/extracted line\s+(\d+)$/i);
  if (trailingLine) return { line: Number(trailingLine[1]), raw };

  return { label: raw, raw };
}

/** True when the citation came from an uploaded research document rather than code. */
export function isResearchCitation(kind?: string | null): boolean {
  return typeof kind === "string" && kind.startsWith("research");
}

/** A short, human label for the citation location, e.g. "Page 4" or "Paragraph 7". */
export function citationLocationLabel(location?: string | null): string {
  const parsed = parseCitationLocation(location);
  if (parsed.page && parsed.label) return `Page ${parsed.page} · ${parsed.label}`;
  if (parsed.page) return `Page ${parsed.page}`;
  return parsed.raw;
}

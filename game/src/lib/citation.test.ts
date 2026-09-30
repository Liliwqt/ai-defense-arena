import { describe, it, expect } from "vitest";
import { parseCitationLocation, isResearchCitation, citationLocationLabel } from "./citation";

describe("parseCitationLocation", () => {
  it("parses a PDF page and extracted line", () => {
    expect(parseCitationLocation("Page 4 · extracted line 12")).toEqual({
      page: 4, line: 12, raw: "Page 4 · extracted line 12",
    });
  });

  it("parses a page with no line", () => {
    expect(parseCitationLocation("Page 2")).toEqual({ page: 2, raw: "Page 2" });
  });

  it("parses a page with a trailing label", () => {
    const parsed = parseCitationLocation("Page 7 · Paragraph 3");
    expect(parsed.page).toBe(7);
    expect(parsed.label).toBe("Paragraph 3");
  });

  it("keeps a DOCX-style label intact", () => {
    const parsed = parseCitationLocation("Paragraph 7");
    expect(parsed.page).toBeUndefined();
    expect(parsed.label).toBe("Paragraph 7");
  });

  it("recovers a line number from an unrecognised prefix", () => {
    const parsed = parseCitationLocation("Some layout · extracted line 9");
    expect(parsed.line).toBe(9);
  });

  it("returns only the raw value for an unknown format", () => {
    expect(parseCitationLocation("Table 2, row 4")).toEqual({ label: "Table 2, row 4", raw: "Table 2, row 4" });
  });

  it("handles missing, empty, and non-string input without throwing", () => {
    expect(parseCitationLocation(undefined)).toEqual({ raw: "" });
    expect(parseCitationLocation(null)).toEqual({ raw: "" });
    expect(parseCitationLocation("")).toEqual({ raw: "" });
    expect(parseCitationLocation("   ")).toEqual({ raw: "" });
    expect(parseCitationLocation(42 as unknown as string)).toEqual({ raw: "" });
  });

  it("tolerates odd separators and casing", () => {
    const parsed = parseCitationLocation("page  3 ·  extracted line  5");
    expect(parsed.page).toBe(3);
    expect(parsed.line).toBe(5);
  });
});

describe("isResearchCitation", () => {
  it("recognises the research kinds the server emits", () => {
    expect(isResearchCitation("research_pdf")).toBe(true);
    expect(isResearchCitation("research_docx")).toBe(true);
  });

  it("rejects code and missing kinds", () => {
    expect(isResearchCitation("source")).toBe(false);
    expect(isResearchCitation(undefined)).toBe(false);
    expect(isResearchCitation(null)).toBe(false);
    expect(isResearchCitation("")).toBe(false);
  });
});

describe("citationLocationLabel", () => {
  it("prefers a page number when present", () => {
    expect(citationLocationLabel("Page 4 · extracted line 12")).toBe("Page 4");
    expect(citationLocationLabel("Page 9")).toBe("Page 9");
  });

  it("falls back to the raw label when there is no page", () => {
    expect(citationLocationLabel("Paragraph 7")).toBe("Paragraph 7");
    expect(citationLocationLabel(undefined)).toBe("");
  });
});

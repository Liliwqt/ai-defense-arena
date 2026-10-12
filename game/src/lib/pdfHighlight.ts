/** Conservative visual matching; the server quote is never rewritten. */
function normalized(text: string): {text: string; offsets: number[]} {
  let result = "";
  const offsets: number[] = [];
  for (let index = 0; index < text.length; index++) {
    const char = /\s/.test(text[index]) ? " " : text[index];
    if (char === " " && (!result || result.endsWith(" "))) continue;
    result += char; offsets.push(index);
  }
  if (result.endsWith(" ")) { result = result.slice(0, -1); offsets.pop(); }
  return {text: result, offsets};
}

function occurrences(text: string, quote: string): number {
  let count = 0;
  let start = 0;
  while ((start = text.indexOf(quote, start)) !== -1) {
    if (++count > 1) return count;
    start++;
  }
  return count;
}

export function highlightCitation(layer: HTMLElement, page: HTMLElement, quote: string): boolean {
  const target = normalized(quote).text;
  if (!target) return false;
  const spans = Array.from(layer.querySelectorAll("span")).filter(span =>
    span.childNodes.length === 1 && span.firstChild?.nodeType === Node.TEXT_NODE);
  // Count both joins to reject duplicate text split into different PDF runs.
  // Geometry is accepted only inside one run; uncertain cross-run/column or
  // wrapped matches deliberately use the exact-quote fallback.
  if (["", " "].some(separator => occurrences(normalized(spans.map(span => span.textContent).join(separator)).text, target) > 1)) return false;
  const matches = spans.flatMap(span => {
    const content = normalized(span.textContent ?? "");
    const index = content.text.indexOf(target);
    return index < 0 ? [] : [{span, content, index}];
  });
  if (matches.length !== 1) return false;
  const {span, content, index} = matches[0];
  const rotation = span.style.getPropertyValue("--rotate");
  if (rotation && rotation !== "0deg") return false;
  const range = document.createRange();
  range.setStart(span.firstChild!, content.offsets[index]);
  range.setEnd(span.firstChild!, content.offsets[index + target.length - 1] + 1);
  const rectangles = Array.from(range.getClientRects()).filter(rect => rect.width > 0 && rect.height > 0);
  if (!rectangles.length) return false;
  const origin = page.getBoundingClientRect();
  for (const rect of rectangles) {
    const marker = document.createElement("div");
    marker.className = "pdf-citation-mark";
    marker.setAttribute("aria-hidden", "true");
    Object.assign(marker.style, {left: `${rect.left - origin.left}px`, top: `${rect.top - origin.top}px`, width: `${rect.width}px`, height: `${rect.height}px`});
    page.append(marker);
  }
  return true;
}

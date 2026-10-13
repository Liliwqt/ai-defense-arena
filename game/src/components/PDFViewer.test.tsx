import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { QuestionCard } from "./QuestionCard";
import type { RoomState } from "../types";
import userEvent from "@testing-library/user-event";

const provider = vi.hoisted(() => ({getDocument: vi.fn(), getPage: vi.fn(), text: ["Planned interviews"]}));
vi.mock("pdfjs-dist/legacy/build/pdf.mjs", () => ({
  GlobalWorkerOptions: {}, getDocument: provider.getDocument,
  TextLayer: class {
    constructor(private options: {container: HTMLElement}) {}
    render() { for (const value of provider.text) { const span = document.createElement("span"); span.textContent = value; this.options.container.append(span); } return Promise.resolve(); }
    cancel() {}
  },
}));

const state: RoomState = {
  room_code: "PAPER", self_seat: 0, self_is_host: true, phase: "question", players: [],
  active_panelist: "Methodology Reviewer", error: null, revision: 1, files: ["paper.pdf"],
  feedback_status: "none", feedback: null, defense_view_id: "run-view",
  documents: [{id: "doc-one", filename: "paper.pdf", page_count: 3}],
  turns: [{panelist: "Methodology Reviewer", question: "How will you recruit?", filename: "paper.pdf",
    evidence_text: "Planned interviews", evidence_line: 2, evidence_location: "Page 2 · extracted line 1",
    evidence_kind: "research_pdf", evidence_document_id: "doc-one", evidence_page: 2,
    answer: null, answered_by: null}],
};

beforeEach(() => {
  vi.clearAllMocks(); sessionStorage.clear();
  provider.text = ["Planned interviews"];
  Object.defineProperty(Range.prototype, "getClientRects", {configurable: true, value: () => [{left: 20, top: 30, width: 100, height: 14}]});
  vi.spyOn(HTMLCanvasElement.prototype, "getContext").mockReturnValue({} as CanvasRenderingContext2D);
  provider.getPage.mockResolvedValue({
    getViewport: ({scale}: {scale: number}) => ({width: 300 * scale, height: 400 * scale, scale}),
    render: () => ({promise: Promise.resolve(), cancel: vi.fn()}),
    getTextContent: () => Promise.resolve({items: [], styles: {}}),
  });
  provider.getDocument.mockReturnValue({promise: Promise.resolve({getPage: provider.getPage}), destroy: vi.fn()});
});

describe("Original paper in the question card", () => {
  it("keeps reading position and zoom when opening and closing view options", async () => {
    const user = userEvent.setup();
    render(<QuestionCard roomState={state} playerToken="private-player" />);
    await screen.findByText("Cited text highlighted");
    const options = screen.getByRole("button", {name: "Paper view options"});
    expect(options.getAttribute("aria-expanded")).toBe("false");
    await user.click(options);
    expect(options.getAttribute("aria-expanded")).toBe("true");
    await user.click(screen.getByRole("button", {name: "Zoom in"}));
    await user.click(screen.getByRole("button", {name: "Next page"}));
    await waitFor(() => expect(provider.getPage).toHaveBeenLastCalledWith(3));
    await user.click(options);
    await user.click(options);
    expect(screen.getByLabelText("Zoom level").textContent).toBe("125%");
    expect(screen.getByLabelText("Page 3 of 3")).toBeTruthy();
    await user.click(screen.getByRole("button", {name: "Fit width"}));
    expect(screen.getByLabelText("Zoom level").textContent).toBe("100%");
  });

  it("opens the server-cited physical page while keeping the question and exact quote", async () => {
    render(<QuestionCard roomState={state} playerToken="private-player" />);
    expect(screen.getByRole("tab", {name: "Paper"})).toBeTruthy();
    await waitFor(() => expect(provider.getPage).toHaveBeenCalledWith(2));
    expect(screen.getByText("How will you recruit?")).toBeTruthy();
    expect(screen.getByRole("region", {name: "Original PDF"})).toBeTruthy();
    expect(screen.getByLabelText("Exact extracted quotation").textContent).toBe("Planned interviews");
    const request = provider.getDocument.mock.calls[0][0];
    expect(request.url).not.toContain("private-player");
    expect(request.httpHeaders).toEqual({"X-Player-Token": "private-player"});
  });

  it("keeps personal reading through clarification and reconnect, then follows a new turn", async () => {
    const user = userEvent.setup();
    const view = render(<QuestionCard roomState={state} playerToken="private-player" />);
    await waitFor(() => expect(provider.getPage).toHaveBeenLastCalledWith(2));
    await user.click(screen.getByRole("button", {name: "Next page"}));
    await waitFor(() => expect(provider.getPage).toHaveBeenLastCalledWith(3));
    await user.click(screen.getByRole("button", {name: "Zoom in"}));
    const clarified = {...state, revision: 2, turns: [{...state.turns[0], clarifications: [{request: "Simplify", reply: "Who will you invite?"}]}]};
    view.rerender(<QuestionCard roomState={clarified} playerToken="private-player" />);
    expect(screen.getByText(/Physical page 3 of 3/)).toBeTruthy();
    expect(screen.getByText("125%")).toBeTruthy();
    view.unmount();
    const reconnect = render(<QuestionCard roomState={clarified} playerToken="private-player" />);
    await waitFor(() => expect(provider.getPage).toHaveBeenLastCalledWith(3));
    expect(screen.getByText("125%")).toBeTruthy();
    reconnect.rerender(<QuestionCard roomState={{...clarified, turns: [...clarified.turns, {...state.turns[0], question: "How will consent work?", evidence_page: 1}]}} playerToken="private-player" />);
    await waitFor(() => expect(provider.getPage).toHaveBeenLastCalledWith(1));
  });

  it.each([
    [["Planned interviews"], "Cited text highlighted"],
    [["Planned interviews", "Planned interviews"], "Precise highlight unavailable"],
    [["Other content"], "Precise highlight unavailable"],
  ])("shows truthful citation precision for %j", async (text, expected) => {
    provider.text = text as string[];
    render(<QuestionCard roomState={state} playerToken="private-player" />);
    await waitFor(() => expect(screen.getByText(expected as string)).toBeTruthy());
    expect(screen.getByLabelText("Exact extracted quotation").textContent).toBe("Planned interviews");
  });

  it("ignores an obsolete document load and lets each reader return to the citation", async () => {
    const user = userEvent.setup();
    let resolveOld!: (value: {getPage: typeof provider.getPage}) => void;
    const destroyOld = vi.fn().mockResolvedValue(undefined);
    provider.getDocument.mockReturnValueOnce({promise: new Promise(resolve => {resolveOld = resolve;}), destroy: destroyOld});
    const multiple = {...state, documents: [...state.documents!, {id:'doc-two',filename:'second.pdf',page_count:2}]};
    render(<QuestionCard roomState={multiple} playerToken="private-player" />);
    await waitFor(() => expect(provider.getDocument).toHaveBeenCalledTimes(1));
    await user.selectOptions(screen.getByRole('combobox',{name:'PDF document'}), 'doc-two');
    await waitFor(() => expect(screen.getByText(/second.pdf · Physical page 1 of 2/)).toBeTruthy());
    await waitFor(() => expect(provider.getPage).toHaveBeenCalledWith(1));
    const oldPage = vi.fn();
    resolveOld({getPage:oldPage});
    await waitFor(() => expect(destroyOld).toHaveBeenCalled());
    expect(oldPage).not.toHaveBeenCalled();
    await user.click(screen.getByRole('button',{name:'Return to citation'}));
    await waitFor(() => expect(screen.getByText(/paper.pdf · Physical page 2 of 3/)).toBeTruthy());
    expect(provider.getDocument.mock.calls.at(-1)?.[0].url).toContain('doc-one');
  });

  it("retries only the paper and supports keyboard tabs and expanded reading exit", async () => {
    const user = userEvent.setup();
    provider.getDocument.mockReturnValueOnce({promise:Promise.reject(Error('synthetic network error')),destroy:vi.fn()});
    render(<QuestionCard roomState={state} playerToken="private-player" />);
    await screen.findByRole('alert');
    expect(screen.getByText('How will you recruit?')).toBeTruthy();
    expect(screen.getByLabelText('Exact extracted quotation').textContent).toBe('Planned interviews');
    await user.click(screen.getByRole('button',{name:'Retry paper'}));
    await screen.findByText('Cited text highlighted');
    screen.getByRole('tab',{name:'Question'}).focus();
    await user.keyboard('{ArrowRight}');
    expect(document.activeElement).toBe(screen.getByRole('tab',{name:'Paper'}));
    await user.click(screen.getByRole('button',{name:'Expand paper'}));
    const exit = screen.getByRole('button',{name:'Exit expanded reading'});
    expect(exit.getAttribute('aria-expanded')).toBe('true');
    await user.keyboard('{Escape}');
    expect(document.activeElement).toBe(screen.getByRole('button',{name:'Expand paper'}));
    expect(provider.getDocument).toHaveBeenCalledTimes(2);
  });
});

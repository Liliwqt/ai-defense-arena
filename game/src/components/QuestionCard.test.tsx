import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { QuestionCard } from "./QuestionCard";
import type { RoomState } from "../types";

const base: RoomState = {
  room_code: "TEST",
  self_seat: 0,
  self_is_host: true,
  phase: "lobby",
  players: [],
  turns: [],
  active_panelist: null,
  error: null,
  revision: 1,
  files: [],
  feedback_status: "none",
  feedback: null,
  server_now_ms: 1_000_000,
  vote_deadline_ms: null,
  answer_deadline_ms: null,
  selected_seat: null,
  vote_counts: {},
  my_vote: null,
  chat: [],
};

describe("QuestionCard", () => {
  it("shows default state when roomState is null", () => {
    render(
      <QuestionCard roomState={null} />,
    );
    expect(screen.getByText("Your defense begins here")).toBeTruthy();
  });

  it("shows lobby text for lobby phase", () => {
    render(
      <QuestionCard roomState={base} />,
    );
    expect(screen.getByText("Your team is gathering")).toBeTruthy();
  });

  it("keeps the original question and citation while showing a clarification", () => {
    const state: RoomState = { ...base, phase: "interpreting", remaining_answer_ms: 42_000,
      turns: [{ panelist: "Methodology Reviewer", question: "How will you recruit?",
        filename: "paper.pdf", evidence_line: 2, evidence_location: "Page 1 · extracted line 2",
        evidence_kind: "research_pdf", evidence_text: "Planned interviews", answer: null, answered_by: null,
        clarifications: [{ request: "Can you explain?", reply: "How will you invite participants?" }] }] };
    render(<QuestionCard roomState={state} />);
    expect(screen.getByText("How will you recruit?")).toBeTruthy();
    expect(screen.getByText(/How will you invite participants/)).toBeTruthy();
    expect(screen.getByText("Planned interviews")).toBeTruthy();
    expect(screen.getByText(/clock paused/i)).toBeTruthy();
  });

  it("shows question text and source block for question phase", () => {
    const state: RoomState = {
      ...base,
      phase: "question",
      turns: [
        {
          panelist: "Technical Architect",
          lead_in: "You chose SQLite for a small prototype. Let's examine that tradeoff.",
          question: "Why use SQLite?",
          filename: "queue.py",
          evidence_line: 5,
          evidence_text: "DATABASE = 'queue.db'",
          answer: null,
          timed_out: false,
          assigned_seat: null,
          answered_by: null,
        },
      ],
    };
    render(
      <QuestionCard roomState={state} />,
    );
    expect(screen.getByText("You chose SQLite for a small prototype. Let's examine that tradeoff.")).toBeTruthy();
    expect(screen.getByText("Why use SQLite?")).toBeTruthy();
    expect(screen.getByText("QUESTION 1")).toBeTruthy();
    expect(screen.getByText("queue.py")).toBeTruthy();
    expect(screen.getByText("Line 5")).toBeTruthy();
    expect(screen.getByText("DATABASE = 'queue.db'")).toBeTruthy();
  });

  it("keeps the resolved exchange visible while reviewing the answer", () => {
    const state: RoomState = {
      ...base,
      phase: "generating",
      turns: [{
        panelist: "Technical Architect", lead_in: "You chose a local database.",
        question: "Why SQLite?", filename: "queue.py", evidence_line: 5,
        evidence_text: "DATABASE = 'queue.db'", answer: "It keeps setup simple.",
        answered_by: "Alex",
      }],
    };
    render(<QuestionCard roomState={state} />);
    expect(screen.getByText("Reviewing your answer…")).toBeTruthy();
    expect(screen.getByText("Why SQLite?")).toBeTruthy();
    expect(screen.getByText("Team answer · Alex: It keeps setup simple.")).toBeTruthy();
    expect(screen.getByText("DATABASE = 'queue.db'")).toBeTruthy();
  });

  it("describes a timeout truthfully while preparing the next turn", () => {
    const state: RoomState = {
      ...base, phase: "generating",
      turns: [{ panelist: "Security Reviewer", question: "Who may read this?",
        filename: "queue.py", evidence_line: 8, evidence_text: "name = input()",
        answer: null, timed_out: true, answered_by: null }],
    };
    render(<QuestionCard roomState={state} />);
    expect(screen.getByText("Reviewing the missed turn…")).toBeTruthy();
expect(screen.getByText("Time expired · question passed to the panel.")).toBeTruthy();
  });

  it("shows the cited question during speaker voting", () => {
    const state: RoomState = { ...base, phase: "voting", turns: [{ panelist: "Technical Architect", question: "Why SQLite?", filename: "queue.py", evidence_line: 5, evidence_text: "DATABASE = 'queue.db'", answer: null, answered_by: null }] };
    render(<QuestionCard roomState={state} />);
    expect(screen.getByText("Why SQLite?")).toBeTruthy();
    expect(screen.getByText("queue.py")).toBeTruthy();
  });

  it("shows a later adaptive question number without a fixed denominator", () => {
    const answered = Array.from({ length: 6 }, (_, i) => ({
      panelist: "Product Judge", question: `Q${i + 1}`,
      filename: "README.md", evidence_line: 2, evidence_text: "users", answer: `A${i + 1}`,
      answered_by: "Alex",
    }));
    const state: RoomState = {
      ...base,
      phase: "question",
      turns: [...answered, { panelist: "Critical Judge", question: "What supports that claim?",
        filename: "README.md", evidence_line: 2, evidence_text: "users", answer: null,
        answered_by: null }],
    };
    render(<QuestionCard roomState={state} />);
    expect(screen.getByText("QUESTION 7")).toBeTruthy();
    expect(screen.getByText("Critical Judge")).toBeTruthy();
  });

  it("preserves the exact cited line in a code element", () => {
    const line = "    rooms: dict[str, Room] = {}  ";
    const state: RoomState = { ...base, phase: "question", turns: [{ panelist: "Technical Architect", question: "What is the tradeoff?", filename: "game_server.py", evidence_line: 127, evidence_text: line, answer: null, answered_by: null }] };
    const { container } = render(<QuestionCard roomState={state} />);
    expect(screen.getByText("game_server.py")).toBeTruthy();
    expect(screen.getByText("Line 127")).toBeTruthy();
    expect(container.querySelector("#source-block pre code")?.textContent).toBe(line);
  });

it("presents extracted PDF text as a document page, not as code", () => {
    const state: RoomState = { ...base, defense_type: "research", phase: "voting", turns: [{
      panelist: "Methodology Reviewer", question: "How will you recruit students?",
      filename: "paper.pdf", evidence_line: 2, evidence_location: "Page 2 · extracted line 1",
      evidence_kind: "research_pdf", evidence_text: "  Planned student interviews  ",
      answer: null, answered_by: null,
    }] };
    const { container } = render(<QuestionCard roomState={state} />);
    // The page view replaces the code block entirely for research citations.
    expect(container.querySelector("#page-citation")).toBeTruthy();
    expect(container.querySelector("#source-block")).toBeNull();
    expect(screen.getByText("paper.pdf")).toBeTruthy();
    expect(screen.getByText("Page 2")).toBeTruthy();
    expect(container.querySelector(".page-citation-line")?.textContent).toContain("line 1");
    // The exact excerpt is preserved, including its original leading and trailing
    // whitespace, so the citation still matches the uploaded document exactly.
    expect(container.querySelector(".page-citation-text")?.textContent).toBe("  Planned student interviews  ");
    expect(screen.getByLabelText(/Cited document text from paper\.pdf, Page 2/)).toBeTruthy();
  });

  it("states that the page view is extracted text, not a true PDF render", () => {
    const state: RoomState = { ...base, defense_type: "research", phase: "voting", turns: [{
      panelist: "Methodology Reviewer", question: "Q?",
      filename: "paper.pdf", evidence_line: 1, evidence_location: "Page 1",
      evidence_kind: "research_pdf", evidence_text: "Some text.",
      answer: null, answered_by: null,
    }] };
    render(<QuestionCard roomState={state} />);
    expect(screen.getByText(/Text extracted from the uploaded document/i)).toBeTruthy();
  });

  it("labels a DOCX citation without inventing a page number", () => {
    const state: RoomState = { ...base, defense_type: "research", phase: "voting", turns: [{
      panelist: "Ethics Reviewer", question: "How is consent handled?",
      filename: "study.docx", evidence_line: 4, evidence_location: "Paragraph 4",
      evidence_kind: "research_docx", evidence_text: "Participants sign a consent form.",
      answer: null, answered_by: null,
    }] };
    const { container } = render(<QuestionCard roomState={state} />);
    expect(container.querySelector("#page-citation")).toBeTruthy();
    expect(screen.getByText("Paragraph 4")).toBeTruthy();
    expect(screen.queryByText(/^Page \d/)).toBeNull();
  });

  it("keeps the exact monospace source block for code citations", () => {
    const state: RoomState = { ...base, phase: "voting", turns: [{
      panelist: "Technical Architect", question: "Why SQLite?",
      filename: "queue.py", evidence_line: 5, evidence_location: "Line 5",
      evidence_kind: "source", evidence_text: "DATABASE = 'queue.db'",
      answer: null, answered_by: null,
    }] };
    const { container } = render(<QuestionCard roomState={state} />);
    expect(container.querySelector("#source-block")).toBeTruthy();
    expect(container.querySelector("#page-citation")).toBeNull();
    expect(container.querySelector("#source-block pre code")?.textContent).toBe("DATABASE = 'queue.db'");
    expect(container.querySelector(".page-fidelity-note")).toBeNull();
  });

  it("still renders the page view when the location string is malformed", () => {
    const state: RoomState = { ...base, defense_type: "research", phase: "voting", turns: [{
      panelist: "Impact Reviewer", question: "Who benefits?",
      filename: "paper.pdf", evidence_line: 1, evidence_location: "somewhere unknown",
      evidence_kind: "research_pdf", evidence_text: "Students benefit first.",
      answer: null, answered_by: null,
    }] };
    const { container } = render(<QuestionCard roomState={state} />);
    expect(container.querySelector("#page-citation")).toBeTruthy();
    expect(screen.getByText("somewhere unknown")).toBeTruthy();
  });

  it("shows the cited line with its neighbouring lines as dimmed context", () => {
    // A PDF line can end on "Similarly," and mean nothing alone. The server sends
    // the neighbours; the cited line must stay emphasized and byte-exact.
    const state: RoomState = { ...base, defense_type: "research", phase: "voting", turns: [{
      panelist: "Methodology Reviewer", question: "Which hardware?",
      filename: "paper.pdf", evidence_line: 2, evidence_location: "Page 4 · extracted line 2",
      evidence_kind: "research_pdf", evidence_text: "Wi-Fi 6 module (2.4 GHz). Similarly,",
      evidence_before: "The study uses a Wi-Fi 6 module.", evidence_after: "The office runs the same hardware.",
      answer: null, answered_by: null,
    }] };
    const { container } = render(<QuestionCard roomState={state} />);
    const cited = container.querySelector(".page-citation-text.is-cited");
    const before = container.querySelector(".page-citation-passage .page-citation-context");
    const after = container.querySelectorAll(".page-citation-passage .page-citation-context")[1];
    expect(cited?.textContent).toBe("Wi-Fi 6 module (2.4 GHz). Similarly,");
    expect(cited?.classList.contains("is-cited")).toBe(true);
    expect(before?.textContent).toBe("The study uses a Wi-Fi 6 module.");
    expect(after?.textContent).toBe("The office runs the same hardware.");
    // The note must say which line was cited, so context is never mistaken for it.
    expect(screen.getByText(/Neighbouring lines are shown for context/i)).toBeTruthy();
  });

  it("shows the cited line alone when the server sent no context", () => {
    const state: RoomState = { ...base, defense_type: "research", phase: "voting", turns: [{
      panelist: "Ethics Reviewer", question: "How is consent handled?",
      filename: "paper.pdf", evidence_line: 1, evidence_location: "Page 1",
      evidence_kind: "research_pdf", evidence_text: "Participants sign a consent form.",
      answer: null, answered_by: null,
    }] };
    const { container } = render(<QuestionCard roomState={state} />);
    expect(container.querySelector(".page-citation-passage")).toBeNull();
    expect(container.querySelector(".page-citation-text")?.textContent).toBe("Participants sign a consent form.");
    expect(screen.queryByText(/Neighbouring lines/i)).toBeNull();
  });

  it("keeps source block when phase is lobby", () => {
    render(
      <QuestionCard roomState={base} />,
    );
    expect(screen.queryByLabelText("Exact cited source line")).toBeNull();
  });

  // jsdom performs no layout, so pinning is asserted structurally: the heading must
  // sit outside the scroll region, and the region that actually overflows must be
  // the focusable one. The visual proof is a scroll-position measurement in a browser.
  it("keeps the asker heading pinned outside the scrolling body", () => {
    const { container } = render(<QuestionCard roomState={base} />);
    const scroll = container.querySelector(".question-scroll");
    const heading = container.querySelector(".question-heading");
    expect(scroll).toBeTruthy();
    expect(heading).toBeTruthy();
    expect(scroll?.contains(heading)).toBe(false);
    expect(container.querySelector("#question-card")?.contains(heading)).toBe(true);
    expect(scroll?.querySelector("#question-text")).toBeTruthy();
  });

  it("scrolls the citation inside the pinned card for both citation kinds", () => {
    const code: RoomState = { ...base, phase: "voting", turns: [{
      panelist: "Technical Architect", question: "Why SQLite?", filename: "queue.py",
      evidence_line: 5, evidence_location: "Line 5", evidence_kind: "source",
      evidence_text: "DATABASE = 'queue.db'", answer: null, answered_by: null,
    }] };
    const codeView = render(<QuestionCard roomState={code} />);
    expect(codeView.container.querySelector(".question-scroll #source-block")).toBeTruthy();
    codeView.unmount();

    const research: RoomState = { ...base, defense_type: "research", phase: "voting", turns: [{
      panelist: "Methodology Reviewer", question: "How will you recruit students?",
      filename: "paper.pdf", evidence_line: 2, evidence_location: "Page 2 · extracted line 1",
      evidence_kind: "research_pdf", evidence_text: "Planned student interviews.",
      answer: null, answered_by: null,
    }] };
    const researchView = render(<QuestionCard roomState={research} />);
    expect(researchView.container.querySelector(".question-scroll #page-citation")).toBeTruthy();
  });

  it("moves the keyboard scroll tab stop onto the scrolling body", () => {
    const { container } = render(<QuestionCard roomState={base} />);
    const card = container.querySelector("#question-card");
    const scroll = container.querySelector(".question-scroll");
    // The card itself no longer scrolls, so it must not be the tab stop.
    expect(card?.getAttribute("tabindex")).toBeNull();
    expect(scroll?.getAttribute("tabindex")).toBe("0");
    expect(scroll?.getAttribute("aria-label")).toBeTruthy();
  });

  it("shows coaching preparing text when phase complete and feedback generating", () => {
    const state: RoomState = {
      ...base,
      phase: "complete",
      feedback_status: "generating",
    };
    render(
      <QuestionCard roomState={state} />,
    );
    expect(screen.getByText("Preparing coaching report")).toBeTruthy();
  });

  it("shows coaching failed text when feedback_status is failed", () => {
    const state: RoomState = {
      ...base,
      phase: "complete",
      feedback_status: "failed",
      error: "OpenAI timed out.",
    };
    render(
      <QuestionCard roomState={state} />,
    );
    expect(screen.getByText("Defense complete")).toBeTruthy();
    expect(screen.getByText(/OpenAI timed out/)).toBeTruthy();
  });

  it("shows ready coaching text when feedback_status is ready", () => {
    const state: RoomState = {
      ...base,
      phase: "complete",
      feedback_status: "ready",
    };
    render(
      <QuestionCard roomState={state} />,
    );
    expect(screen.getAllByText(/coaching report/i).length).toBeGreaterThanOrEqual(1);
  });
});

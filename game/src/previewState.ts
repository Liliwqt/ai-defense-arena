import type { RoomState } from "./types";

const previewParams = new URLSearchParams(window.location.search);
const votePreview = previewParams.get("vote") === "1";
const reviewPreview = previewParams.get("review") === "1";
const longPreview = previewParams.get("long") === "1";
const researchPreview = previewParams.get("research") === "1";
const clarifyPreview = previewParams.get("clarify") === "1";
const completePreview = previewParams.get("complete") === "1";

export const previewState: RoomState = {
  room_code: "PREVIEW",
  phase: reviewPreview ? "generating" : votePreview ? "voting" : "question",
  self_seat: 0,
  self_is_host: true,
  players: [
    { seat: 0, name: "You", online: true, is_host: true },
    { seat: 1, name: "Teammate A", online: true, is_host: false },
    { seat: 2, name: "Teammate B", online: true, is_host: false },
    { seat: 3, name: "Teammate C", online: false, is_host: false },
  ],
  turns: [
    {
      panelist: researchPreview ? "Methodology Reviewer" : "Product Judge",
      lead_in: researchPreview ? "You described planned interviews. I want to understand how those interviews will answer the study question." : "You connected the prototype to a real registrar workflow. I want to understand how you will verify that it helps students.",
      question: researchPreview ? "How will you recruit participants and test whether the planned interviews answer your research question?" : longPreview
        ? "The question card is absolutely positioned over the room illustration and limited to part of the viewport height. How would you ensure that the full question and cited source line stay readable when a defender uses a short landscape phone, a browser with enlarged text, or a narrow split-screen window? Which parts should scroll, which parts must remain visible, and what would you test before choosing these limits? Describe the tradeoff between keeping all eight seats in view and giving the cited project evidence enough space to inspect without losing the active speaker."
        : "How will you learn whether reserving before walking to the counter saves students time?",
      filename: researchPreview ? "study.pdf" : longPreview ? "game/src/index.css" : "sample_project/README.md",
      evidence_line: researchPreview ? 8 : longPreview ? 457 : 3,
      evidence_location: researchPreview ? "Page 2 · extracted line 3" : undefined,
      evidence_kind: researchPreview ? "research_pdf" : "source",
      evidence_text: researchPreview ? "We plan to interview students who use the registrar office and compare common themes in their experiences." : longPreview
        ? "#question-card { z-index: 7; top: auto; bottom: clamp(14px, 3.2vh, 38px); left: max(18px, calc((100% - 1360px) / 2)); right: max(18px, calc((100% - 1360px) / 2)); min-height: 0; max-height: min(35dvh, 340px); padding: clamp(15px, 2.1vw, 28px) clamp(18px, 2.7vw, 40px); border: 1px solid #ffffff; border-radius: 20px; background: #f9fbfff2; box-shadow: 0 18px 55px #27415d60, inset 0 1px #fff; color: #17233e; scrollbar-color: #a3bcd8 #edf4fb; }"
        : "Campus Queue lets students reserve a place in a registrar office queue before",
      clarifications: clarifyPreview ? [{ request: "Can you repeat it in simple English and give an example?", reply: researchPreview ? "I mean how you would invite participants and check whether the interviews address your research question. For example, you might explain who you will interview and how you will analyze their answers." : "I mean how you would check whether the reservation actually saves students time. For example, you could compare how long a student waits with and without a reservation." }] : [],
      answer: reviewPreview ? "We will compare the reservation time with walk-in wait times during a pilot." : null,
      timed_out: false,
      assigned_seat: 0,
      answered_by: reviewPreview ? "You" : null,
      answered_by_seat: reviewPreview ? 0 : null,
    },
  ],
  active_panelist: researchPreview ? "Methodology Reviewer" : "Product Judge",
  error: null,
  revision: 1,
  defense_type: researchPreview ? "research" : "code",
  research_stage: researchPreview ? "proposal" : "infer",
  accepted_files: researchPreview ? [{ name: "study.pdf", kind: "research_pdf", detail: "3 pages" }] : undefined,
  files: researchPreview ? ["study.pdf"] : longPreview ? ["game/src/index.css"] : ["sample_project/README.md", "sample_project/queue.py"],
  feedback_status: "none",
  feedback: null,
  server_now_ms: Date.now(),
  vote_deadline_ms: votePreview ? Date.now() + 15_000 : null,
  answer_deadline_ms: votePreview || reviewPreview ? null : Date.now() + 120_000,
  selected_seat: votePreview || reviewPreview ? null : 0,
  vote_counts: votePreview ? { "0": 1, "1": 1, "2": 0 } : {},
  my_vote: votePreview ? 0 : null,
  chat: [],
};

if (completePreview) {
  const roles = researchPreview
    ? ["Methodology Reviewer", "Ethics Reviewer", "Impact Reviewer", "Critical Reviewer"]
    : ["Technical Architect", "Security Reviewer", "Product Judge", "Critical Judge"];
  previewState.phase = "complete";
  previewState.active_panelist = null;
  previewState.answer_deadline_ms = null;
  previewState.selected_seat = null;
  previewState.turns = roles.map((panelist, index) => ({
    panelist,
    lead_in: index ? "You described a practical first step. Let's examine the next decision." : "",
    question: ["What choice matters most in this approach?", "How will you protect the people involved?",
      "Who benefits first, and how will you know?", "What evidence would change your conclusion?"][index],
    filename: researchPreview ? "study.pdf" : "README.md",
    evidence_line: 1,
    evidence_location: researchPreview ? "Page 1 · extracted line 1" : "Line 1",
    evidence_kind: researchPreview ? "research_pdf" : "source",
    evidence_text: researchPreview ? "We plan to interview students during a small pilot." : "The prototype helps students reserve a place in a queue.",
    answer: ["We chose a small pilot to test the workflow.", "We ask for consent and avoid publishing names.",
      "Students benefit first; we will compare wait times.", "If wait times do not improve, we would revise the design."][index],
    timed_out: false,
    assigned_seat: index % 2,
    answered_by: index % 2 ? "Teammate A" : "You",
    answered_by_seat: index % 2,
    clarifications: index === 0 ? [{ request: "Can you say that more simply?", reply: "I mean which decision has the biggest effect on the pilot." }] : [],
  }));
  previewState.feedback_status = "ready";
  previewState.feedback = {
    summary: "The team explained the pilot and tied several answers to the stated workflow.",
    strengths: [{ turn: 0, text: "The first answer named a concrete pilot." }],
    improvements: [{ turn: 2, text: "Explain how wait times will be compared." }],
    next_step: "Write down the pilot measures before rehearsing again.",
  };
}

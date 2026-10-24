import type { RoomState } from "./types";
import { researchPlanPreview } from "./researchPlanPreview";

const previewParams = new URLSearchParams(window.location.search);
const votePreview = previewParams.get("vote") === "1";
const reviewPreview = previewParams.get("review") === "1";
const reactionPreview = previewParams.get("reaction") === "1";
const longPreview = previewParams.get("long") === "1";
const planPreview = previewParams.get("plan") === "1";
const researchPreview = planPreview || previewParams.get("research") === "1";
const clarifyPreview = previewParams.get("clarify") === "1";
const completePreview = previewParams.get("complete") === "1";

export const previewState: RoomState = {
  room_code: "PREVIEW",
  phase: reactionPreview ? "reacting" : reviewPreview ? "generating" : votePreview ? "voting" : "question",
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
      // A PDF line can end on a conjunction and mean nothing alone, so the mock
      // research citation reproduces that real case with its neighbours supplied.
      evidence_before: researchPreview ? "The registrar office runs on a single shared queue for walk-in students." : undefined,
      evidence_after: researchPreview ? "We will compare both groups across the same two-week window." : undefined,
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
  reaction_deadline_ms: reactionPreview ? Date.now() + 8_000 : null,
  answer_deadline_ms: reactionPreview || votePreview || reviewPreview ? null : Date.now() + 120_000,
  selected_seat: reactionPreview || votePreview || reviewPreview ? null : 0,
  vote_counts: votePreview ? { "0": 1, "1": 1, "2": 0 } : {},
  my_vote: votePreview ? 0 : null,
  chat: [],
};

// AI-free research review fixture: the topic describes the displayed discussion,
// never a prospective question. Used by the existing local preview route only.
if (researchPreview && reviewPreview) {
  previewState.defense_view_id = "preview-research-review";
  previewState.operation = { id: "preview-question", kind: "question", stage: "generating",
    started_at_ms: previewState.server_now_ms! - 4000, attempt: 1, retrying: false };
  previewState.panelist_activity = { operation_id: "preview-question", view_id: "preview-research-review",
    reviewer: null, context: "Participant recruitment" };
}

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

if (planPreview) {
  const budget = Number(previewParams.get("budget") ?? researchPlanPreview.suggested_budget);
  const requestedStatus = previewParams.get("planstatus");
  previewState.phase = "lobby";
  previewState.turns = [];
  previewState.active_panelist = null;
  previewState.vote_deadline_ms = null;
  previewState.answer_deadline_ms = null;
  previewState.selected_seat = null;
  previewState.feedback = null;
  previewState.feedback_status = "none";
  previewState.research_planning_status = requestedStatus === "planning" || requestedStatus === "failed" ? requestedStatus : "ready";
  previewState.research_plan = previewState.research_planning_status === "ready" ? researchPlanPreview : null;
  previewState.research_plan_progress = previewState.research_planning_status === "planning"
    ? { stage: "mapping", topics: researchPlanPreview.topics.slice(0, 3) } : null;
  previewState.research_budget_preview = Number.isInteger(budget) && budget >= 4 && budget <= 100 ? budget : researchPlanPreview.suggested_budget;
  previewState.research_plan_approved = false;
  previewState.research_plan_error = requestedStatus === "failed" ? "The AI cited an invalid source line. Retry preparing the defense." : null;
  previewState.files = ["campus-queue-proposal.pdf"];
  previewState.accepted_files = [{ name: "campus-queue-proposal.pdf", kind: "research_pdf", detail: "7 pages · synthetic visual fixture" }];
  if (previewState.research_planning_status === "planning") {
    previewState.defense_view_id = "preview-preparation";
    previewState.server_now_ms = Date.now();
    previewState.operation = { id: "mapping:1", kind: "mapping", stage: "mapping",
      started_at_ms: previewState.server_now_ms - 4000, attempt: 1, retrying: false };
    previewState.panelist_activity = { operation_id: "mapping:1", view_id: "preview-preparation",
      reviewer: null, context: "campus-queue-proposal.pdf" };
  }
}

// Synthetic visual fixture for the longer policy; never used by live rooms.
if (researchPreview && !planPreview) {
  previewState.research_plan = researchPlanPreview;
  previewState.research_planning_status = "ready";
  previewState.research_plan_approved = true;
  previewState.research_budget_preview = 24;
  previewState.question_budget = 24;
  previewState.current_topic = researchPlanPreview.topics[0].id;
  previewState.coverage = Object.fromEntries(researchPlanPreview.topics.map((topic, i) =>
    [topic.id, {status: i < 3 ? "addressed" : i === 3 ? "needs clarification" : "pending", turns: i < 4 ? [i] : [], reason: i === 3 ? "The pilot comparison needs a clearer explanation." : ""}]));
  previewState.turns = previewState.turns.map(turn => ({...turn, topic_id: researchPlanPreview.topics[0].id}));
  if (previewParams.get("coverage") === "1" && !completePreview) {
    const current = previewState.turns[0];
    previewState.turns = [...Array.from({length: 10}, (_, i) => ({...current,
      panelist: ["Methodology Reviewer", "Ethics Reviewer", "Impact Reviewer", "Critical Judge"][i % 4],
      question: `Synthetic discussion ${i + 1}: explain the pilot decision.`,
      answer: i === 3 ? null : "We would measure waiting time in the pilot.",
      timed_out: i === 3, answered_by: i === 3 ? null : "Teammate A",
      topic_id: researchPlanPreview.topics[i % 7].id})), current];
  }
  if (completePreview) previewState.completion_reason = "budget exhausted";
}

// Illustrative synthetic dialogue for layout review only; never used for live AI.
if (previewParams.get("probe") === "1" && !completePreview && !planPreview) {
  previewState.phase = "probe";
  previewState.answer_deadline_ms = Date.now() + 30_000;
  previewState.probe_deadline_ms = previewState.answer_deadline_ms;
  previewState.turns[0].answer = "We will choose students randomly.";
  previewState.turns[0].answered_by = "You";
  previewState.turns[0].resolved = false;
  previewState.turns[0].probe = {
    id: "synthetic-probe-preview",
    request: "Will you draw names from a complete student list, or approach whoever is available?",
    references: [], status: "pending", reply: null, clarifications: [],
  };
}

// Display-only submission/coaching states; no AI request or payment is made.
const submissionPreview = previewParams.get("submission");
if (submissionPreview && !completePreview && !planPreview) {
  previewState.phase = submissionPreview === "retry" ? "interpretation_retry" : "interpreting";
  previewState.clock_paused = submissionPreview !== "running";
  previewState.remaining_answer_ms = 25_000;
  previewState.answer_deadline_ms = previewState.clock_paused ? null : Date.now() + 25_000;
  previewState.selected_seat = 0;
  previewState.my_pending_submission = "We would compare the pilot with the existing workflow.";
  previewState.interpretation_attempts_left = submissionPreview === "retry" ? 0 : 5;
  if (researchPreview && previewState.phase === "interpreting") {
    previewState.defense_view_id = "preview-same-question";
    previewState.operation = { id: "interpretation:1", kind: "interpretation",
      stage: previewState.turns[0].probe ? "reviewing_reply" : "reviewing_answer",
      started_at_ms: Date.now() - 4000, attempt: 1, retrying: false };
    previewState.panelist_activity = { operation_id: "interpretation:1", view_id: "preview-same-question",
      reviewer: previewState.turns[0].panelist, context: researchPlanPreview.topics[0].title };
  }
}
const coachingPreview = previewParams.get("coaching");
if (completePreview && researchPreview && coachingPreview === "partial" && previewState.feedback) {
  previewState.defense_view_id = "preview-coaching";
  previewState.feedback_status = "generating";
  previewState.feedback.answer_cards = previewState.turns.slice(0, 3).map((turn, index) => ({
    turn: index, question: turn.question, panelist: turn.panelist, original_answer: turn.answer,
    speaker_name: turn.answered_by, timed_out: false, ended_early: false, probe: null, probe_feedback: null,
    citation: { filename: turn.filename, evidence_line: turn.evidence_line, evidence_text: turn.evidence_text },
    feedback: { strengths: ["You stated a concrete pilot decision."], improvements: ["Connect that decision to its source before adding detail."],
      stronger_answer: "If supported, explain [the decision], [why it fits] and [the paper evidence].", wording_basis: "conditional",
      practice_task: "Practice a direct answer, reason and source.", wording_examples: [] },
  }));
  previewState.coaching_progress = { job_id: "preview-job", overview_status: "ready", cards_ready: 3, cards_required: 4,
    completion_status: "pending", completion_error: null, can_retry: false, sections: [
      { id: "overview", turns: null, status: "ready", attempts_left: 2, error: null },
      { id: "answers-0", turns: [0, 1, 2], status: "ready", attempts_left: 2, error: null },
      { id: "answers-3", turns: [3], status: "generating", attempts_left: 2, error: null },
    ] };
  previewState.operation = { id: "coaching:1", kind: "coaching", stage: "answers", started_at_ms: Date.now() - 4000, attempt: 1, retrying: false };
  previewState.panelist_activity = { operation_id: "coaching:1", view_id: "preview-coaching", reviewer: null, context: "Question 4",
    job_id: "preview-job", section_id: "answers-3" };
}
if (completePreview && ["none", "generating", "failed"].includes(coachingPreview ?? "")) {
  previewState.feedback_status = coachingPreview as "none" | "generating" | "failed";
  previewState.feedback = null;
  previewState.coaching_attempts_left = coachingPreview === "failed" ? 0 : 3;
}

// Match the rendered snapshot to deadlines created while assembling the fixture.
if (completePreview && previewParams.get("closing") === "1" && previewState.feedback) {
  previewState.feedback.closing = "That explains the limits of your pilot. Review the remaining topics in coaching.";
  previewState.closing_panelist = previewState.turns.at(-1)?.panelist;
  previewState.closing_deadline_ms = Date.now() + 8_000;
}
previewState.server_now_ms = Date.now();

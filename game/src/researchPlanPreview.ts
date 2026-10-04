import type { ResearchPlan } from "./types";

/** Synthetic scope data for visual review only; never used in a live room. */
export const researchPlanPreview: ResearchPlan = {
  id: "synthetic-plan-preview",
  suggested_budget: 14,
  uncertainties: ["The proposal does not specify the pilot sample size. No completed-study results are reported."],
  topics: [
    ["Purpose and research gap", "Discuss the registrar workflow and the evidence needed to establish the waiting-time problem.", "Impact Reviewer", "Students report long waits when requesting registrar services."],
    ["Study design and recruitment", "Discuss participant recruitment and whether the pilot can answer the stated research objective.", "Methodology Reviewer", "We plan to recruit volunteer students for a two-week queue pilot."],
    ["Measurement and comparison", "Discuss how reservation users and walk-in students will be compared fairly.", "Methodology Reviewer", "We will compare wait times for reservation users and walk-in students."],
    ["Consent and participant privacy", "Discuss consent, access to participant data, and the planned retention period.", "Ethics Reviewer", "Participants may withdraw, and their responses will be anonymized."],
    ["Feasibility and implementation", "Discuss how the prototype's storage choice supports the planned pilot and where it may need revision.", "Critical Judge", "The pilot prototype stores reservations in a local SQLite database."],
    ["Expected impact", "Discuss who should benefit and how the study will assess that benefit without assuming success.", "Impact Reviewer", "The pilot aims to reduce waiting time for students at the registrar."],
    ["Limitations and assumptions", "Discuss the limits of a single-campus pilot and the assumptions that need evidence.", "Critical Judge", "A single-campus pilot may not represent other institutions."],
  ].map(([title, objective, panelist, evidence], i) => ({
    id: `topic-${i + 1}`, title, objective, panelist,
    gaps: i === 1 ? ["Participant count and sample-size justification are not stated."] : [],
    references: [{ filename: "campus-queue-proposal.pdf", evidence_line: i + 1,
      evidence_text: evidence, evidence_location: `Page ${i + 1} · extracted line 1`, evidence_kind: "research_pdf" }],
  })),
};

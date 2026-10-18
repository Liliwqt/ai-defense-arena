/** Mirror of game_server.py Room.snapshot() return value. */

export type Phase =
  | "lobby"
  | "generating"
  | "reacting"
  | "voting"
  | "question"
  | "probe"
  | "interpreting"
  | "interpretation_retry"
  | "retry"
  | "complete";

export type FeedbackStatus = "none" | "generating" | "ready" | "failed";

export interface Player {
  seat: number;
  name: string;
  online: boolean;
  is_host: boolean;
}

export interface ClarificationExchange {
  request: string;
  reply: string;
}

export interface Turn {
  evidence_document_id?: string;
  evidence_page?: number;
  probe?: PanelistProbe | null;
  resolved?: boolean;
  panelist: string;
  lead_in?: string;
  question: string;
  filename: string;
  evidence_line: number;
  evidence_text: string;
  evidence_location?: string;
  evidence_kind?: string;
  /** Research citations only: neighbouring lines so a fragment reads as prose. */
  evidence_before?: string;
  evidence_after?: string;
  answer: string | null;
  clarifications?: ClarificationExchange[];
  timed_out?: boolean;
  ended_early?: boolean;
  topic_id?: string | null;
  is_follow_up?: boolean;
  assigned_seat?: number | null;
  answered_by: string | null;
  input_provenance?: {method: "voice"; provider: string; model: string; audio_ms: number; padding_ms?: number} | null;
  answered_by_seat?: number | null;
}

export interface PanelistProbe {
  id: string;
  request: string;
  references: SourceReference[];
  status: "pending" | "answered" | "expired" | "ended_early";
  reply: string | null;
  speaker_name?: string | null;
  speaker_seat?: number | null;
  clarifications: ClarificationExchange[];
  input_provenance?: Turn["input_provenance"];
}

export interface CoachingPoint {
  turn: number;
  text: string;
}

export interface AnswerFeedback {
  strengths: string[];
  improvements: string[];
  stronger_answer: string | null;
  wording_basis: "supported" | "conditional" | "unanswered";
  practice_task: string;
  wording_examples: string[];
}

export interface AnswerCoachingCard {
  turn: number;
  question: string;
  panelist: string;
  original_answer: string | null;
  speaker_name: string | null;
  timed_out: boolean;
  ended_early?: boolean;
  probe: PanelistProbe | null;
  input_provenance?: Turn["input_provenance"];
  citation?: {filename: string; evidence_line: number; evidence_text: string; evidence_location?: string} | null;
  feedback: AnswerFeedback;
  probe_feedback: AnswerFeedback | null;
}

export type CoachingSectionStatus = "pending" | "generating" | "ready" | "failed" | "cancelled";
export interface CoachingProgress {
  job_id: string;
  overview_status: CoachingSectionStatus;
  cards_ready: number;
  cards_required: number;
  completion_status: "pending" | "ready" | "failed" | "cancelled" | "returned" | "abandoned";
  completion_error: string | null;
  can_retry: boolean;
  sections: {id:string; turns:number[] | null; status:CoachingSectionStatus; attempts_left:number; error:string | null}[];
}

export interface CoachingFeedback {
  answer_cards?: AnswerCoachingCard[] | null;
  summary: string;
  strengths: CoachingPoint[];
  improvements: CoachingPoint[];
  next_step: string;
  closing?: string;
}

export interface ChatMessage {
  id: number;
  seat: number;
  name: string;
  text: string;
  sent_at_ms: number;
}

export interface SourceReference {
  filename: string;
  evidence_line: number;
  evidence_text: string;
  evidence_location: string;
  evidence_kind: string;
  evidence_before?: string;
  evidence_after?: string;
}

export interface ProfileDescription {
  fields: string[];
  approaches: ("quantitative" | "qualitative" | "mixed-methods" | "theoretical" | "computational/design" | "other" | "unclear")[];
  setting: string | null;
}

export interface ResearchProfile extends ProfileDescription {
  host_description?: ProfileDescription | null;
  source_description?: ProfileDescription | null;
  explanation: string;
  references: SourceReference[];
  uncertainties: string[];
  needs_uncertainty_acknowledgment: boolean;
}

export interface ResearchPlan {
  id: string;
  suggested_budget: number;
  uncertainties: string[];
  profile?: ResearchProfile | null;
  topics: { id: string; title: string; objective: string; panelist: string;
    references: SourceReference[]; gaps: string[] }[];
}

export interface RoomState {
  coaching_progress?: CoachingProgress | null;
  my_voice_draft?: {attempt_id: string; text: string; turn: number; probe_id: string | null; view_id: string} | null;
  voice?: { enabled: boolean; remaining_ms: number; provider: string; model: string; language: string } | null;
  defense_view_id?: string;
  documents?: {id: string; filename: string; page_count: number}[];
  probe_recovery_available?: boolean;
  room_code: string;
  self_seat: number | null;
  self_is_host: boolean;
  phase: Phase;
  players: Player[];
  turns: Turn[];
  active_panelist: string | null;
  error: string | null;
  revision: number;
  files: string[];
  accepted_files?: { name: string; kind: string; detail: string }[];
  defense_type?: "code" | "research" | "mixed";
  research_stage?: "infer" | "proposal" | "completed";
  research_planning_status?: "none" | "planning" | "ready" | "failed";
  research_plan_progress?: { stage: "preparing" | "mapping" | "validating"; topics: ResearchPlan["topics"] } | null;
  research_plan?: ResearchPlan | null;
  research_plan_error?: string | null;
  research_profile_correction?: ProfileDescription | null;
  research_budget_preview?: number | null;
  research_plan_approved?: boolean;
  question_budget?: number | null;
  coverage?: Record<string, {status: "pending" | "discussed" | "needs clarification" | "addressed"; turns: number[]; reason: string}>;
  current_topic?: string | null;
  completion_reason?: "coverage addressed" | "budget exhausted" | "ended by host" | null;
  feedback_status: FeedbackStatus;
  feedback: CoachingFeedback | null;
  closing_panelist?: string | null;
  closing_deadline_ms?: number | null;
  server_now_ms?: number;
  vote_deadline_ms?: number | null;
  reaction_deadline_ms?: number | null;
  answer_deadline_ms?: number | null;
  probe_deadline_ms?: number | null;
  remaining_answer_ms?: number | null;
  expires_at_ms?: number | null;
  clock_paused?: boolean;
  pause_deadline_ms?: number | null;
  interpretation_attempts_left?: number;
  question_attempts_left?: number;
  question_retrying?: boolean;
  opening_repeated?: boolean;
  opening_candidate?: { id: string; panelist: string; question: string; filename: string;
    evidence_text: string; evidence_location: string } | null;
  coaching_attempts_left?: number;
  plan_attempts_left?: number;
  my_pending_submission?: string | null;
  selected_seat?: number | null;
  vote_counts?: Record<string, number>;
  my_vote?: number | null;
  chat?: ChatMessage[];
}

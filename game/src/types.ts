/** Mirror of game_server.py Room.snapshot() return value. */

export type Phase =
  | "lobby"
  | "generating"
  | "voting"
  | "question"
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
  answered_by_seat?: number | null;
}

export interface CoachingPoint {
  turn: number;
  text: string;
}

export interface CoachingFeedback {
  summary: string;
  strengths: CoachingPoint[];
  improvements: CoachingPoint[];
  next_step: string;
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

export interface ResearchPlan {
  id: string;
  suggested_budget: number;
  uncertainties: string[];
  topics: { id: string; title: string; objective: string; panelist: string;
    references: SourceReference[]; gaps: string[] }[];
}

export interface RoomState {
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
  research_plan?: ResearchPlan | null;
  research_plan_error?: string | null;
  research_budget_preview?: number | null;
  research_plan_approved?: boolean;
  question_budget?: number | null;
  coverage?: Record<string, {status: "pending" | "discussed" | "needs clarification" | "addressed"; turns: number[]; reason: string}>;
  current_topic?: string | null;
  completion_reason?: "coverage addressed" | "budget exhausted" | "ended by host" | null;
  feedback_status: FeedbackStatus;
  feedback: CoachingFeedback | null;
  server_now_ms?: number;
  vote_deadline_ms?: number | null;
  answer_deadline_ms?: number | null;
  remaining_answer_ms?: number | null;
  my_pending_submission?: string | null;
  selected_seat?: number | null;
  vote_counts?: Record<string, number>;
  my_vote?: number | null;
  chat?: ChatMessage[];
}

export type DrawerMode = "controls" | "transcript";

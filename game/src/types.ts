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

/** Mirror of game_server.py Room.snapshot() return value. */

export type Phase =
  | "lobby"
  | "generating"
  | "voting"
  | "question"
  | "retry"
  | "complete";

export type FeedbackStatus = "none" | "generating" | "ready" | "failed";

export interface Player {
  seat: number;
  name: string;
  online: boolean;
  is_host: boolean;
}

export interface Turn {
  panelist: string;
  question: string;
  filename: string;
  evidence_line: number;
  evidence_text: string;
  answer: string | null;
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
  feedback_status: FeedbackStatus;
  feedback: CoachingFeedback | null;
  server_now_ms?: number;
  vote_deadline_ms?: number | null;
  answer_deadline_ms?: number | null;
  selected_seat?: number | null;
  vote_counts?: Record<string, number>;
  my_vote?: number | null;
  chat?: ChatMessage[];
}

export type DrawerMode = "controls" | "transcript";

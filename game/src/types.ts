/** Mirror of game_server.py Room.snapshot() return value. */

export type Phase =
  | "lobby"
  | "generating"
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
}

export type DrawerMode = "controls" | "transcript" | "answer";

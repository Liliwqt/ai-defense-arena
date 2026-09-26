import type { RoomState } from "./types";

export const previewState: RoomState = {
  room_code: "PREVIEW",
  phase: "question",
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
      panelist: "Technical Architect",
      question:
        "Why does reserve() open a new SQLite connection for every reservation, and how will that choice behave when several students reserve at once?",
      filename: "sample_project/queue.py",
      evidence_line: 9,
      evidence_text: "    with sqlite3.connect(DATABASE) as connection:",
      answer: null,
      answered_by: null,
    },
  ],
  active_panelist: "Technical Architect",
  error: null,
  revision: 1,
  files: ["sample_project/README.md", "sample_project/queue.py"],
  feedback_status: "none",
  feedback: null,
};

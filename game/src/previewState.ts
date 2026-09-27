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
      panelist: "Product Judge",
      question:
        "How will you learn whether reserving before walking to the counter saves students time?",
      filename: "sample_project/README.md",
      evidence_line: 2,
      evidence_text: "Campus Queue lets students reserve a place in a registrar office queue before",
      answer: null,
      answered_by: null,
    },
  ],
  active_panelist: "Product Judge",
  error: null,
  revision: 1,
  files: ["sample_project/README.md", "sample_project/queue.py"],
  feedback_status: "none",
  feedback: null,
};

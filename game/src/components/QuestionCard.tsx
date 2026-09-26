import type { DrawerMode, RoomState } from "../types";

interface QuestionCardProps {
  roomState: RoomState | null;
  connected: boolean;
  previewMode: boolean;
  onOpenDrawer: (mode: DrawerMode, focusAnswer?: boolean) => void;
}

function deriveContent(state: RoomState | null, isHost: boolean) {
  const phase = state?.phase ?? "none";
  const feedbackStatus = state?.feedback_status ?? "none";
  const answered = (state?.turns ?? []).filter((t) => t.answer).length;

  // Find current unanswered turn
  const turns = state?.turns ?? [];
  let current: { turn: (typeof turns)[number]; index: number } | null = null;
  for (let i = turns.length - 1; i >= 0; i--) {
    if (turns[i].question && !turns[i].answer) {
      current = { turn: turns[i], index: i };
      break;
    }
  }

  let name = "Your defense begins here";
  let question = "Create or join a room to begin your defense.";
  let number = "READY";
  let status = "Create or join a room to begin.";
  let source: string | null = null;
  let evidence: string | null = null;
  let showAnswerBtn = false;

  if (phase === "lobby") {
    name = "Your team is gathering";
    question = "The host starts the defense when everyone is ready.";
    status = isHost
      ? "Open Controls to start the defense."
      : "Waiting for the host to start.";
  } else if (phase === "generating") {
    name = state?.active_panelist ?? "The panel";
    question = "Preparing the next question…";
    number = `QUESTION ${Math.min(answered + 1, 4)} OF 4`;
    status = "Your team will see the same question when it is ready.";
  } else if (phase === "question" && current) {
    name = current.turn.panelist;
    question = current.turn.question;
    number = `QUESTION ${current.index + 1} OF 4`;
    source = `${current.turn.filename}:${current.turn.evidence_line}`;
    evidence = current.turn.evidence_text;
    status = "Any teammate can answer; the first valid submission counts.";
    showAnswerBtn = true;
  } else if (phase === "retry") {
    name = state?.active_panelist ?? "The panel";
    question = "The next question could not be generated.";
    number = `QUESTION ${Math.min(answered + 1, 4)} OF 4`;
    status =
      state?.error ??
      (isHost ? "Open Controls to retry." : "The host can retry.");
  } else if (phase === "complete") {
    if (feedbackStatus === "generating") {
      name = "Preparing coaching report";
      question =
        "Your team's coaching report is being prepared. It will appear in the Transcript.";
      number = "4 OF 4";
      status = "This may take a few seconds.";
    } else if (feedbackStatus === "failed") {
      name = "Defense complete";
      question =
        "All four questions have been answered. The coaching report could not be generated.";
      number = "4 OF 4";
      status =
        state?.error ??
        (isHost
          ? "Open Controls to retry the coaching report."
          : "The host can retry the coaching report.");
    } else {
      name = "Defense complete";
      question =
        "All four questions have been answered. Open Transcript to review your coaching report.";
      number = "4 OF 4";
      status =
        "The complete transcript and coaching report remain in this room until the server restarts.";
    }
  }

  return { name, question, number, status, source, evidence, showAnswerBtn };
}

export function QuestionCard({
  roomState,
  connected,
  previewMode,
  onOpenDrawer,
}: QuestionCardProps) {
  const isHost = roomState?.self_is_host ?? false;
  const { name, question, number, status, source, evidence, showAnswerBtn } =
    deriveContent(roomState, isHost);

  return (
    <section
      id="question-card"
      aria-labelledby="panelist-name"
      className="relative z-10 flex flex-col gap-[7px] border-t-2 border-[#81bce3] text-[#12243b]"
      style={{
        height: "var(--dock-height)",
        padding: "clamp(13px,2vh,20px) clamp(18px,3vw,42px)",
        background:
          "linear-gradient(115deg, #e6f3ff 0, #f4f9ff 60%, #d7ecff 100%)",
        boxShadow: "0 -15px 55px #030b1d90",
      }}
    >
      {/* Heading row */}
      <div className="flex items-center justify-between gap-4 min-w-0">
        <div className="min-w-0">
          <p className="text-[#8a3e4e] text-[0.68rem] font-black tracking-[0.16em] m-0 mb-1">
            THE PANEL ASKS
          </p>
          <h2
            id="panelist-name"
            className="text-[clamp(1rem,1.8vw,1.35rem)] m-0 leading-tight text-[#182d48]"
          >
            {name}
          </h2>
        </div>
        <span className="flex-none px-[10px] py-[5px] rounded-full bg-[#fbdfe2] text-[#8a3446] text-[0.72rem] font-black tracking-[0.08em]">
          {number}
        </span>
      </div>

      {/* Scrollable question text */}
      <div
        id="question-content"
        className="flex-auto min-h-0 overflow-auto pr-2"
        style={{ scrollbarColor: "#75a9c8 transparent", overscrollBehavior: "contain" }}
        tabIndex={0}
        aria-live="polite"
      >
        <p
          id="question-text"
          className="text-[clamp(0.98rem,1.9vw,1.3rem)] font-[750] leading-[1.36] my-[2px] mb-[11px] break-words whitespace-pre-wrap"
        >
          {question}
        </p>
      </div>

      {/* Source citation */}
      {source !== null && (
        <div
          id="source-block"
          className="flex-none grid gap-[5px] max-h-[72px] overflow-auto p-[9px_11px] border-l-4 border-[#4c92c3] rounded bg-[#ccdfef]"
          aria-label="Exact cited source line"
          tabIndex={0}
          style={{ overscrollBehavior: "contain" }}
        >
          <span className="text-[0.79rem] font-black text-[#234d70] break-words">
            {source}
          </span>
          <pre className="font-[600] text-[0.78rem] leading-[1.4] text-[#17334c] m-0 whitespace-pre-wrap break-words font-mono">
            {evidence ?? ""}
          </pre>
        </div>
      )}

      {/* Footer */}
      <div className="mt-auto border-t border-[#bdd6e9] pt-2 flex items-center justify-between gap-4 min-h-[36px]">
        <p
          id="arena-status"
          role="status"
          className="text-[#46627b] text-[0.76rem] m-0 leading-tight break-words"
        >
          {status}
        </p>
        {!previewMode && showAnswerBtn && (
          <button
            type="button"
            onClick={() => onOpenDrawer("controls", true)}
            disabled={!connected}
            className="flex-none w-auto min-w-[155px] px-[14px] py-2 rounded-[9px] bg-[#50b6ee] text-[#092039] font-[850] border-0 disabled:opacity-55 hover:not-disabled:bg-[#83d2f8]"
          >
            Answer question
          </button>
        )}
      </div>
    </section>
  );
}

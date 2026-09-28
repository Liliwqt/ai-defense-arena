import type { Turn } from "../types";

interface TurnCardProps {
  turn: Turn;
  index: number;
}

export function TurnCard({ turn, index }: TurnCardProps) {
  return (
    <article className="border border-[#324d68] bg-[#0b1c2d] rounded-[10px] p-[14px_15px]">
      <h3 className="text-[#ff9b9b] text-[0.82rem] m-0 mb-2 font-black">
        QUESTION {index + 1} · {turn.panelist || "Panelist"}
      </h3>
      {turn.lead_in && (
        <p className="leading-[1.45] my-[6px] text-[#9fc4e4] italic whitespace-pre-wrap break-words text-[0.8rem]">
          {turn.lead_in}
        </p>
      )}
      <p className="leading-[1.45] my-[6px] text-[#e4effb] whitespace-pre-wrap break-words text-[0.84rem]">
        {turn.question || "Question being prepared…"}
      </p>
      {turn.filename && Number.isInteger(turn.evidence_line) && (
        <p className="text-[0.75rem] text-[#9bcbe8] whitespace-pre-wrap break-words">
          {turn.filename}, {turn.evidence_location ?? `Line ${turn.evidence_line}`} — {turn.evidence_text ?? ""}
        </p>
      )}
      {turn.timed_out && <p className="turn-timeout">Time expired · no answer was submitted.</p>}
      {turn.answer && (
        <p className="border-t border-[#304c65] pt-[10px] mt-3 text-[#bcdcf6] leading-[1.45] text-[0.84rem] whitespace-pre-wrap break-words">
          Team answer{turn.answered_by ? ` · ${turn.answered_by}` : ""}: {turn.answer}
        </p>
      )}
    </article>
  );
}

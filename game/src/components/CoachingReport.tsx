import type { CoachingFeedback, FeedbackStatus } from "../types";

interface CoachingReportProps {
  feedbackStatus: FeedbackStatus;
  feedback: CoachingFeedback | null;
}

export function CoachingReport({ feedbackStatus, feedback }: CoachingReportProps) {
  if (feedbackStatus === "none") return null;

  return (
    <section className="border border-[#435e76] bg-[#0e2035] rounded-[12px] p-[15px_17px] mb-[14px]">
      <h3 className="text-[#ffd97d] text-[0.85rem] m-0 mb-[10px] tracking-[0.05em] font-black">
        Coaching Report
      </h3>

      {feedbackStatus === "generating" && (
        <p className="text-[0.85rem] text-[#8abdd8] m-0 italic">
          Preparing your coaching report…
        </p>
      )}

      {feedbackStatus === "failed" && (
        <p className="text-[0.85rem] text-[#f7a8b4] m-0">
          The coaching report could not be generated. The host can retry from Controls.
        </p>
      )}

      {feedbackStatus === "ready" && feedback && (
        <>
          <p className="text-[0.87rem] leading-[1.5] text-[#ddeeff] m-0 mb-3 whitespace-pre-wrap break-words">
            {feedback.summary}
          </p>

          {feedback.strengths.length > 0 && (
            <div className="mt-[11px]">
              <h4 className="text-[0.76rem] font-black tracking-[0.09em] m-0 mb-[6px] text-[#7adba6]">
                Strengths
              </h4>
              {feedback.strengths.map((item, i) => (
                <p
                  key={i}
                  className="text-[0.84rem] leading-[1.45] my-[4px] text-[#cce8f8] whitespace-pre-wrap break-words pl-[14px] border-l-[3px] border-[#3fba82]"
                >
                  <span className="text-[0.72rem] font-black opacity-70 mr-1">
                    Q{item.turn + 1} ·{" "}
                  </span>
                  {item.text}
                </p>
              ))}
            </div>
          )}

          {feedback.improvements.length > 0 && (
            <div className="mt-[11px]">
              <h4 className="text-[0.76rem] font-black tracking-[0.09em] m-0 mb-[6px] text-[#f4a96a]">
                Areas to Improve
              </h4>
              {feedback.improvements.map((item, i) => (
                <p
                  key={i}
                  className="text-[0.84rem] leading-[1.45] my-[4px] text-[#cce8f8] whitespace-pre-wrap break-words pl-[14px] border-l-[3px] border-[#d97f3a]"
                >
                  <span className="text-[0.72rem] font-black opacity-70 mr-1">
                    Q{item.turn + 1} ·{" "}
                  </span>
                  {item.text}
                </p>
              ))}
            </div>
          )}

          {feedback.next_step && (
            <div className="mt-[11px]">
              <h4 className="text-[0.76rem] font-black tracking-[0.09em] m-0 mb-[6px] text-[#eaf2ff]">
                Next Step
              </h4>
              <p className="text-[0.84rem] leading-[1.45] my-[4px] text-[#cce8f8] whitespace-pre-wrap break-words pl-[14px] border-l-[3px] border-[#314e68]">
                {feedback.next_step}
              </p>
            </div>
          )}
        </>
      )}
    </section>
  );
}

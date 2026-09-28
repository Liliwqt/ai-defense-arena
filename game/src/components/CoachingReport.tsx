import type { CoachingFeedback, FeedbackStatus } from "../types";

interface CoachingReportProps {
  feedbackStatus: FeedbackStatus;
  feedback: CoachingFeedback | null;
}

export function CoachingReport({ feedbackStatus, feedback }: CoachingReportProps) {
  if (feedbackStatus === "none") return null;

  return (
    <section className="coaching-report" aria-label="Coaching report">
      <h3>Coaching Report</h3>
      {feedbackStatus === "generating" && <p className="report-status">Preparing your coaching report…</p>}
      {feedbackStatus === "failed" && <p className="report-error" role="alert">The coaching report could not be generated. The host can retry from Controls.</p>}
      {feedbackStatus === "ready" && feedback && <>
        <p className="report-summary">{feedback.summary}</p>
        {feedback.strengths.length > 0 && <div className="report-group">
          <h4>Strengths</h4>
          {feedback.strengths.map((item, index) => <p className="report-point" key={index}>
            <span>Q{item.turn + 1} · </span>{item.text}
          </p>)}
        </div>}
        {feedback.improvements.length > 0 && <div className="report-group">
          <h4>Areas to Improve</h4>
          {feedback.improvements.map((item, index) => <p className="report-point" key={index}>
            <span>Q{item.turn + 1} · </span>{item.text}
          </p>)}
        </div>}
        {feedback.next_step && <div className="report-group">
          <h4>Next Step</h4>
          <p className="report-point">{feedback.next_step}</p>
        </div>}
      </>}
    </section>
  );
}

import { AnswerCoaching } from "./AnswerCoaching";
import type { CoachingFeedback, CoachingProgress, FeedbackStatus } from "../types";

interface CoachingReportProps {
  failureGuidance?: string;
  feedbackStatus: FeedbackStatus;
  feedback: CoachingFeedback | null;
  closingPanelist?: string | null;
  progress?: CoachingProgress | null;
  onRetry?: () => boolean;
  retryDisabled?: boolean;
}

export function CoachingReport({ feedbackStatus, feedback, closingPanelist, progress, onRetry, retryDisabled, failureGuidance = "Review Controls for recovery options." }: CoachingReportProps) {
  if (feedbackStatus === "none" && !progress) return null;

  return (
    <section className="coaching-report" aria-label="Coaching report">
      <h3>Coaching Report</h3>
      {feedbackStatus === "generating" && <p className="report-status">Preparing your coaching report…</p>}
      {feedbackStatus === "failed" && <p className="report-error" role="alert">The coaching report could not be generated. {failureGuidance}</p>}
      {progress && <section className="coaching-progress" aria-label="Coaching progress">
        <p role="status">{progress.cards_ready} of {progress.cards_required} answers coached</p>
        {progress.completion_status !== "ready" && <p>{progress.completion_status === "failed" ? "Ready coaching is retained. Completion could not be saved." : ["cancelled","returned","abandoned"].includes(progress.completion_status) ? "This run ended with incomplete coaching. Ready sections are retained." : "Coaching is incomplete. Finished sections remain available while the rest are prepared."}</p>}
        <progress aria-label="Answer coaching progress" value={progress.cards_ready} max={Math.max(1,progress.cards_required)} />
        <details><summary>Section status and recovery</summary><ul>{progress.sections.map(section=><li key={section.id}>{section.turns ? `Questions ${section.turns.map(i=>i+1).join(', ')}` : 'Team overview'} · {section.status}{section.error ? ` · ${section.error}` : ''}{section.status==='failed' ? ` · ${section.attempts_left} attempts left` : ''}</li>)}</ul></details>
        {feedbackStatus==='failed' && onRetry && progress.can_retry && <button type="button" className="button-primary" disabled={retryDisabled} onClick={()=>onRetry()}>{progress.completion_status==='failed'?'Retry saving completion':'Retry failed coaching sections'}</button>}
        {feedbackStatus==='failed' && !progress.can_retry && <p>Coaching retry allowance used. Review Controls for available recovery actions.</p>}
      </section>}
      {(feedbackStatus === "ready" || progress?.overview_status === "ready") && feedback && <>
        {feedback.closing && <div className="report-group" aria-label="Panelist closing">
          <h4>{closingPanelist ?? "Panelist"} · Closing remarks</h4>
          <p>{feedback.closing}</p>
        </div>}
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
        {(progress || !!feedback.answer_cards?.length) && <AnswerCoaching cards={feedback.answer_cards ?? []} progress={progress} />}
        {feedback.next_step && <div className="report-group">
          <h4>Next Step</h4>
          <p className="report-point">{feedback.next_step}</p>
        </div>}
      </>}
    </section>
  );
}

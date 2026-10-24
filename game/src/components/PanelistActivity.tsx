import type { RoomPresentation } from "../lib/roomPresentation";
import { WaitingIndicator } from "./WaitingIndicator";

export function PanelistActivity({ presentation, serverNowMs }: {
  presentation: RoomPresentation; serverNowMs?: number;
}) {
  const { activity, waiting } = presentation;
  if (!activity || !waiting) return null;
  return <section className="panelist-activity" aria-label="Panelist activity">
    <span className="activity-gutter" aria-hidden="true"><span>◇</span><i /></span>
    <div className="activity-content">
      {activity.reviewer && <p className="activity-reviewer">{activity.reviewer === "Critical Judge" ? "Critical Reviewer" : activity.reviewer}</p>}
      <WaitingIndicator label={waiting.label} detail={waiting.detail} context={activity.context}
        active={waiting.active} startedAtMs={waiting.startedAtMs} serverNowMs={serverNowMs} />
    </div>
  </section>;
}

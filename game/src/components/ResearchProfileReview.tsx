import type { ResearchProfile } from "../types";
import { PageCitation } from "./PageCitation";

export function ResearchProfileReview({ profile, confirmed }: { profile: ResearchProfile; confirmed: boolean }) {
  return <section className="research-profile-review" aria-label="Research profile">
    <h4>Research profile</h4>
    <p className="control-help">{confirmed ? "Profile confirmed by host" : "Suggested profile · awaiting host review"}</p>
    {profile.host_description && <p className="control-help"><strong>Host description</strong> · requested practice lens, not paper evidence.</p>}
    <dl className="research-profile-facts">
      <div><dt>Fields</dt><dd>{profile.fields.join(", ")}</dd></div>
      <div><dt>Study approaches</dt><dd>{profile.approaches.join(", ")}</dd></div>
      {profile.setting && <div><dt>Setting</dt><dd>{profile.setting}</dd></div>}
    </dl>
    {profile.source_description && <div className="profile-source-description">
      <strong>Paper-based suggestion</strong>
      <p>{profile.source_description.fields.join(", ")} · {profile.source_description.approaches.join(", ")}
        {profile.source_description.setting && ` · ${profile.source_description.setting}`}</p>
    </div>}
    {profile.host_description && <strong>Paper-grounded explanation</strong>}
    <p>{profile.explanation}</p>
    {profile.uncertainties.length > 0 && <div className="plan-uncertainties">
      <strong>Profile uncertainties</strong>
      <ul>{profile.uncertainties.map((item, index) => <li key={index}>{item}</li>)}</ul>
    </div>}
    <details><summary>Profile source references ({profile.references.length})</summary>
      {profile.references.map((ref, index) => <PageCitation key={index} id={`profile-reference-${index}`}
        filename={ref.filename} evidence={ref.evidence_text} location={ref.evidence_location}
        before={ref.evidence_before} after={ref.evidence_after} />)}
    </details>
    <p className="control-help">This profile guides practice. It does not certify the study or the panel's expertise.</p>
  </section>;
}

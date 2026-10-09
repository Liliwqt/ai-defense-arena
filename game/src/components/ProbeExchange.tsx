import "./ProbeExchange.css";
import type { PanelistProbe } from "../types";

export function ProbeExchange({ probe, panelist }: { probe?: PanelistProbe | null; panelist: string }) {
  if (!probe) return null;
  return <section className="panelist-probe" aria-label="Panelist probe" aria-live="polite">
    <p className="probe-label">Panelist asks for a detail · {panelist}</p>
    <p className="probe-request">{probe.request}</p>
    {probe.references.map((ref, index) => <figure className="probe-source" key={index}>
      <figcaption>{ref.filename} · {ref.evidence_location}{ref.evidence_kind.startsWith("research") ? " · extracted text" : ""}</figcaption>
      <pre tabIndex={0} aria-label="Probe cited source">{ref.evidence_text}</pre>
    </figure>)}
    {probe.clarifications.map((exchange, index) => <div className="question-clarification" key={index}>
      <p><strong>Defender asks:</strong> {exchange.request}</p>
      <p><strong>{panelist} explains:</strong> {exchange.reply}</p>
    </div>)}
    {probe.reply != null && <p><strong>Probe reply{probe.speaker_name ? ` · ${probe.speaker_name}` : ""}:</strong> {probe.reply}</p>}
    {probe.status === "expired" && <p>Probe reply time expired. The original answer is retained.</p>}
    {probe.status === "ended_early" && <p>Probe ended early. The original answer is retained.</p>}
  </section>;
}

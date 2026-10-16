import { useEffect, useState } from "react";
import { useTabDraft } from "../hooks/useTabDraft";
import type { ProfileDescription } from "../types";

const approaches: { value: ProfileDescription["approaches"][number]; label: string }[] = [
  { value: "quantitative", label: "Quantitative" }, { value: "qualitative", label: "Qualitative" },
  { value: "mixed-methods", label: "Mixed methods" }, { value: "theoretical", label: "Theoretical" },
  { value: "computational/design", label: "Computational / design" },
  { value: "other", label: "Other" }, { value: "unclear", label: "Unclear" },
];

interface Props {
  description: ProfileDescription;
  planId?: string;
  editable: boolean;
  onDirtyChange: (dirty: boolean) => void;
  onPrepare: (description: ProfileDescription) => boolean;
}

export function ResearchProfileEditor({ description, planId, editable, onDirtyChange, onPrepare }: Props) {
  const savedKey = JSON.stringify(description);
  const marker = JSON.stringify([planId, savedKey]);
  const [fields, setFields] = useTabDraft("profile-fields", description.fields.join("\n"), { room: true, marker });
  const [selectedText, setSelectedText] = useTabDraft("profile-approaches", JSON.stringify(description.approaches), {
    room: true, marker, valid: value => { try { const parsed = JSON.parse(value); return Array.isArray(parsed) && parsed.every(item => approaches.some(option => option.value === item)); } catch { return false; } },
  });
  const selected = JSON.parse(selectedText) as ProfileDescription["approaches"];
  const [setting, setSetting] = useTabDraft("profile-setting", description.setting ?? "", { room: true, marker });
  const [error, setError] = useState("");

  useEffect(() => {
    setError("");
  }, [savedKey, planId]);

  const draft: ProfileDescription = {
    fields: fields.split("\n").map(value => value.trim()).filter(Boolean),
    approaches: approaches.filter(option => selected.includes(option.value)).map(option => option.value),
    setting: setting.trim() || null,
  };
  const dirty = fields !== description.fields.join("\n") || setting !== (description.setting ?? "") ||
    selected.length !== description.approaches.length || selected.some(value => !description.approaches.includes(value));

  useEffect(() => { onDirtyChange(dirty); }, [dirty, onDirtyChange]);

  function submit(event: React.FormEvent) {
    event.preventDefault();
    if (!editable || !dirty) return;
    if (draft.fields.length < 1 || draft.fields.length > 8 || draft.fields.some(value => value.length > 120) ||
      new Set(draft.fields.map(value => value.toLocaleLowerCase())).size !== draft.fields.length || !selected.length) {
      setError("Choose 1–8 distinct fields, up to 120 characters each, and at least one study approach."); return;
    }
    if (onPrepare(draft)) setError("");
  }

  return <form className="research-profile-editor" onSubmit={submit} aria-label="Correct research profile">
    <h4>Correct the practice profile</h4>
    <p className="control-help">Your descriptions guide practice; the uploaded paper remains the evidence. Applying changes prepares a new map and requires fresh profile and budget confirmation.</p>
    <label className="setup-label">Research fields (one per line)
      <textarea className="setup-input" rows={2} maxLength={1024} value={fields} disabled={!editable}
        onChange={event => { setFields(event.target.value); setError(""); }} />
    </label>
    <fieldset disabled={!editable}>
      <legend>Study approaches</legend>
      <div className="profile-approach-options">{approaches.map(option => <label key={option.value} className="profile-confirmation">
        <input type="checkbox" checked={selected.includes(option.value)} onChange={event => {
          setSelectedText(JSON.stringify(event.target.checked ? [...selected, option.value] : selected.filter(value => value !== option.value)));
          setError("");
        }} />{option.label}
      </label>)}</div>
    </fieldset>
    <label className="setup-label">Research setting (optional)
      <input className="setup-input" maxLength={300} value={setting} disabled={!editable}
        onChange={event => { setSetting(event.target.value); setError(""); }} />
    </label>
    {dirty && <p role="status" className="plan-warning">Unsaved profile changes. Apply them and remap before confirming or starting.</p>}
    <button type="submit" className={dirty ? "button-primary" : "button-secondary"} disabled={!editable || !dirty}>Apply profile and remap</button>
    {error && <p role="alert" className="drawer-error">{error}</p>}
  </form>;
}

import type { RoomState, Turn } from "../types";

/**
 * Build a plain-text export of one completed defense.
 *
 * Rooms live in server memory and are never persisted, so this is the only way a
 * team can keep a record to compare against a later rehearsal. Everything here is
 * derived from data already in the room snapshot; no new server data is requested.
 *
 * Timeouts are reported as "no answer submitted" without editorializing, matching
 * the server's rule that a timeout is never treated as an answer.
 */

function safeFileName(value: string): string {
  return value.replace(/[^a-z0-9]+/gi, "-").replace(/^-+|-+$/g, "").toLowerCase() || "defense";
}

function defenseKind(state: RoomState): string {
  if (state.defense_type === "research") return "Research paper defense";
  if (state.defense_type === "mixed") return "Research + code defense";
  return "Code project defense";
}

function timestampLine(state: RoomState): string {
  // The server sends its own clock; prefer it over the device clock so the export
  // matches the room rather than a skewed local time.
  const ms = typeof state.server_now_ms === "number" ? state.server_now_ms : Date.now();
  const date = new Date(ms);
  if (Number.isNaN(date.getTime())) return "";
  return date.toISOString().replace("T", " ").slice(0, 16) + " UTC";
}

function turnLines(turn: Turn, index: number, research = false): string[] {
  const lines: string[] = [];
  const panelist = research && turn.panelist === "Critical Judge" ? "Critical Reviewer" : turn.panelist || "Panelist";
  lines.push(`Q${index + 1}. ${panelist}`);
  if (turn.topic_id) lines.push(`   Topic: ${turn.topic_id}${turn.is_follow_up ? " (follow-up)" : ""}`);
  if (turn.lead_in) lines.push(`   Panelist: ${turn.lead_in}`);
  lines.push(`   Question: ${turn.question}`);
  if (turn.filename && Number.isInteger(turn.evidence_line)) {
    const location = turn.evidence_location ?? `Line ${turn.evidence_line}`;
    lines.push(`   Citation: ${turn.filename}, ${location}`);
    // The cited line is the validated text. Surrounding lines, when the server sent
    // them, are labeled as context so the export cannot be misread as one blob.
    if (turn.evidence_before) lines.push(`   Context before: ${turn.evidence_before}`);
    lines.push(`   Cited text: ${turn.evidence_text ?? ""}`);
    if (turn.evidence_after) lines.push(`   Context after: ${turn.evidence_after}`);
  }
  for (const exchange of turn.clarifications ?? []) {
    lines.push(`   Clarification requested: ${exchange.request}`);
    lines.push(`   ${panelist} replied: ${exchange.reply}`);
  }
  if (turn.ended_early) {
    lines.push("   Result: ended early by host, no answer submitted.");
  } else if (turn.timed_out) {
    lines.push("   Result: time expired, no answer submitted.");
  } else if (turn.answer) {
    const who = turn.answered_by ? ` (${turn.answered_by})` : "";
    lines.push(`   Team answer${who}: ${turn.answer}`);
  }
  if (turn.probe) {
    lines.push(`   Panelist probe: ${turn.probe.request}`);
    for (const ref of turn.probe.references) lines.push(`   Probe citation: ${ref.filename}, ${ref.evidence_location} — ${ref.evidence_text}`);
    for (const c of turn.probe.clarifications) {
      lines.push(`   Probe clarification requested: ${c.request}`);
      lines.push(`   ${panelist} explains: ${c.reply}`);
    }
    lines.push(`   Probe status: ${turn.probe.status}`);
    if (turn.probe.reply != null) lines.push(`   Probe reply (${turn.probe.speaker_name ?? "Defender"}): ${turn.probe.reply}`);
  }
  lines.push("");
  return lines;
}

export function buildDefenseSummary(state: RoomState): string {
  const lines: string[] = [];
  const stamp = timestampLine(state);
  const kind = defenseKind(state);

  lines.push("AI DEFENSE ARENA");
  lines.push(kind);
  if (stamp) lines.push(stamp);
  if (state.room_code) lines.push(`Room: ${state.room_code}`);
  lines.push("");

  const team = state.players
    .map((player) => `${player.name}${player.is_host ? " (host)" : ""}`)
    .filter(Boolean);
  if (team.length > 0) {
    lines.push(`Team: ${team.join(", ")}`);
    lines.push("");
  }

  if (state.files.length > 0) {
    lines.push("Materials reviewed");
    for (const file of state.files) lines.push(`  - ${file}`);
    lines.push("");
  }

  const answered = state.turns.filter((turn) => turn.answer).length;
  const expired = state.turns.filter((turn) => turn.timed_out).length;
  lines.push(`Questions: ${state.turns.length} · answered ${answered}${expired ? ` · ${expired} timed out` : ""}`);
  lines.push("");

  if (state.research_plan && state.coverage) {
    lines.push(`Maximum questions: ${state.question_budget ?? state.research_budget_preview}`);
    if (state.completion_reason) lines.push(`Ending reason: ${state.completion_reason}`);
    lines.push("RESEARCH COVERAGE");
    lines.push("Addressed means discussion coverage, not proof that the research is correct.");
    for (const topic of state.research_plan.topics) {
      const coverage = state.coverage[topic.id];
      lines.push(`  - ${topic.title}: ${coverage?.status ?? "pending"} · ${topic.panelist === "Critical Judge" ? "Critical Reviewer" : topic.panelist}`);
      if (coverage?.reason) lines.push(`    ${coverage.reason}`);
      if (coverage?.turns.length) lines.push(`    Supporting questions: ${coverage.turns.map(i => i + 1).join(", ")}`);
    }
    const gaps = state.research_plan.topics.filter(t => state.coverage?.[t.id]?.status !== "addressed");
    lines.push(`Unresolved topics: ${gaps.map(t => t.title).join("; ") || "none"}`, "");
  }
  if (state.turns.length > 0) {
    lines.push("QUESTIONS AND ANSWERS");
    lines.push("");
    state.turns.forEach((turn, index) => lines.push(...turnLines(turn, index, !!state.defense_type && state.defense_type !== "code")));
  }

  if (state.feedback) {
    lines.push("COACHING REPORT");
    lines.push("");
    lines.push(state.feedback.summary);
    lines.push("");
    if (state.feedback.strengths.length > 0) {
      lines.push("Strengths");
      for (const item of state.feedback.strengths) lines.push(`  - Q${item.turn + 1}: ${item.text}`);
      lines.push("");
    }
    if (state.feedback.improvements.length > 0) {
      lines.push("Areas to improve");
      for (const item of state.feedback.improvements) lines.push(`  - Q${item.turn + 1}: ${item.text}`);
      lines.push("");
    }
    if (state.feedback.next_step) {
      lines.push("Next step");
      lines.push(`  ${state.feedback.next_step}`);
      lines.push("");
    }
  }

  lines.push("Practice guidance only. This is not a grade, and it is not part of any");
  lines.push("formal assessment of the work.");

  return lines.join("\n");
}

export function defenseSummaryFileName(state: RoomState): string {
  const ms = typeof state.server_now_ms === "number" ? state.server_now_ms : Date.now();
  const date = new Date(ms);
  const stamp = Number.isNaN(date.getTime())
    ? "export"
    : date.toISOString().slice(0, 10);
  return `defense-${safeFileName(state.room_code || "room")}-${stamp}.txt`;
}

import type { RoomState, Turn } from "../types";

export interface CardContent {
  name: string;
  question: string;
  number: string;
  filename?: string;
  line?: number;
  evidence?: string;
  location?: string;
  kind?: string;
  before?: string;
  after?: string;
  reviewStatus?: string;
  previousAnswer?: string;
  clarifications?: Turn["clarifications"];
  probe?: Turn["probe"];
  initialAnswer?: string | null;
}

function sourceContent(turn: Turn) {
  return {
    probe: turn.probe,
    filename: turn.filename,
    line: turn.evidence_line,
    evidence: turn.evidence_text,
    location: turn.evidence_location,
    kind: turn.evidence_kind,
    before: turn.evidence_before,
    after: turn.evidence_after,
  };
}

function isResolved(turn: Turn): boolean {
  return turn.resolved ?? (!!turn.answer || !!turn.timed_out);
}

function deriveContent(state: Readonly<RoomState> | null, currentIndex: number, resolved: number): CardContent {
  const phase = state?.phase ?? "none";
  const turns = state?.turns ?? [];
  const current = turns[currentIndex];

  if ((phase === "voting" || phase === "probe" || phase === "question" || phase === "interpreting" || phase === "interpretation_retry") && current) {
    return {
      name: current.panelist,
      question: current.question,
      number: `QUESTION ${currentIndex + 1}${state?.question_budget ? ` OF ${state.question_budget}` : ""}`,
      ...sourceContent(current),
      clarifications: current.clarifications,
      initialAnswer: current.answer,
      reviewStatus: phase === "interpreting" ? state?.clock_paused === false ? "Reading your submission… Answer clock running." : "Reading your submission… Answer clock paused." : phase === "interpretation_retry" ? state?.clock_paused === false ? "Could not interpret the submission. Answer clock running." : "Could not interpret the submission. Answer clock paused." : undefined,
    };
  }
  if (phase === "generating") {
    const previous = [...turns].reverse().find(isResolved);
    if (previous) {
      return {
        name: previous.panelist,
        question: previous.question,
        number: "REVIEWING",
        reviewStatus: previous.timed_out ? "Reviewing the missed turn…" : "Reviewing your answer…",
        previousAnswer: previous.timed_out
          ? "Time expired · question passed to the panel."
          : `Team answer${previous.answered_by ? ` · ${previous.answered_by}` : ""}: ${previous.answer}`,
        ...sourceContent(previous),
        clarifications: previous.clarifications,
      };
    }
    return { name: state?.active_panelist ?? "The panel", question: "Reviewing the project…", number: `QUESTION ${resolved + 1}` };
  }
  if (phase === "retry") {
    return { name: "Question paused", question: `${state?.error ?? "The next question could not be generated."} The host can retry from Controls.`, number: `QUESTION ${resolved + 1}` };
  }
  if (phase === "complete") {
    const feedback = state?.feedback_status;
    return {
      name: feedback === "generating" ? "Preparing coaching report" : "Defense complete",
      question: feedback === "generating"
        ? "The panel has finished. Your coaching report is being prepared."
        : feedback === "failed"
          ? `${state?.error ?? "The coaching report could not be generated."} The host can retry from Controls.`
          : `Open Transcript to review your answers and coaching report.${state?.completion_reason ? ` Ending reason: ${state.completion_reason}.` : ""}`,
      number: `${resolved} RESOLVED`,
    };
  }
  if (phase === "lobby") {
    if (state?.research_planning_status === "planning") {
      return { name: "Preparing research coverage", question: "Mapping the uploaded research. The scope preview will appear in Controls for your team to inspect.", number: "MAPPING" };
    }
    if (state?.research_plan) {
      return { name: "Research scope ready", question: `${state.research_plan.topics.length} proposed topics are ready in Controls. Review the map and confirm the question budget before starting.`, number: "PLAN READY" };
    }
    return { name: "Your team is gathering", question: "The host starts the defense when everyone is ready.", number: "READY" };
  }
  return { name: "Your defense begins here", question: "Create or join a room to begin your defense.", number: "READY" };
}

const CODE_PANELISTS = ["Technical Architect", "Security Reviewer", "Product Judge", "Critical Judge"];
const RESEARCH_PANELISTS = ["Methodology Reviewer", "Ethics Reviewer", "Impact Reviewer", "Critical Reviewer"];

export interface RoomTimer {
  readonly mode: "running" | "paused";
  readonly deadline: number | null;
  readonly serverNow: number;
  readonly savedSeconds: number | null;
  readonly label: string;
  readonly accessibleLabel: string;
  readonly urgentAt: number;
}

function deriveTimer(state: Readonly<RoomState> | null): RoomTimer | null {
  if (!state) return null;
  const reviewing = state.phase === "interpreting" || state.phase === "interpretation_retry";
  if (reviewing && state.clock_paused !== false) {
    return { mode: "paused", deadline: null, serverNow: state.server_now_ms ?? 0,
      savedSeconds: Math.ceil((state.remaining_answer_ms ?? 0) / 1000), label: "PAUSED",
      accessibleLabel: "Answer timer paused", urgentAt: 15 };
  }
  const voting = state.phase === "voting";
  if (!voting && state.phase !== "question" && state.phase !== "probe" && !reviewing) return null;
  const probing = state.turns?.at(-1)?.probe?.status === "pending";
  return { mode: "running", deadline: (voting ? state.vote_deadline_ms : state.answer_deadline_ms) ?? null,
    serverNow: state.server_now_ms ?? 0, savedSeconds: null,
    label: voting ? "VOTE" : probing ? "PROBE" : "ANSWER",
    accessibleLabel: `${voting ? "Vote" : probing ? "Probe reply" : "Answer"} time remaining`,
    urgentAt: voting ? 5 : 15 };
}

function roomStatus(state: Readonly<RoomState> | null): string {
  if (state?.phase === "complete") return "Complete";
  if (state?.phase === "retry") return "Retry needed";
  if (state?.phase === "reacting") return "Panelist speaking…";
  if (state?.phase === "generating") {
    const previous = state.turns?.at(-1);
    return previous?.timed_out ? "Reviewing missed turn…" : previous?.answer ? "Reviewing answer…" : "Preparing question…";
  }
  if (state?.research_planning_status === "planning") return "Mapping research…";
  if (state?.research_planning_status === "failed") return "Retry needed";
  return "Ready";
}

/** Read-only display decisions. Permissions, clocks, drafts and effects belong to their existing owners. */
export function deriveRoomPresentation(state: Readonly<RoomState> | null) {
  const turns = state?.turns ?? [];
  const resolvedCount = turns.filter(isResolved).length;
  const acceptedCount = turns.filter(turn => !!turn.answer).length;
  let currentIndex = -1;
  for (let index = turns.length - 1; index >= 0; index--) {
    const turn = turns[index];
    if (turn.question && (!turn.answer || turn.probe?.status === "pending") && !turn.timed_out) {
      currentIndex = index;
      break;
    }
  }
  const research = !!state?.defense_type && state.defense_type !== "code";
  const displayRole = (role: string) => research && role === "Critical Judge" ? "Critical Reviewer" : role;
  const phase = state?.phase;
  const voting = phase === "voting";
  const reacting = phase === "reacting";
  const answering = ["question", "probe", "interpreting", "interpretation_retry"].includes(phase ?? "");
  const answerTurnIndex = answering ? currentIndex : -1;
  const selectedSeat = answering ? state?.selected_seat ?? null : null;
  const chosenName = state?.players?.find(player => player.seat === selectedSeat)?.name;
  const chosenSelf = answerTurnIndex >= 0 && selectedSeat !== null && selectedSeat === state?.self_seat;
  const rawCard = deriveContent(state, currentIndex, resolvedCount);
  const card = { ...rawCard, name: displayRole(rawCard.name) };
  const reactionTurn = reacting ? turns.at(-1) : undefined;
  const reaction = reacting ? { name: displayRole(reactionTurn?.panelist ?? ""), text: reactionTurn?.lead_in } : null;
  const speaker = reaction?.name ?? displayRole(state?.active_panelist ?? "");
  const panelists = (research ? RESEARCH_PANELISTS : CODE_PANELISTS).map(name => {
    const active = (reacting || voting || answering) && name === speaker;
    return { name, active, label: active ? reacting ? "Speaking" : "Asking" : "Panelist",
      accessibleLabel: `${name}${active ? reacting ? ", speaking" : ", asking this question" : ""}` };
  });
  const defenders = Array.from({ length: 4 }, (_, seat) => {
    const player = state?.players?.find(candidate => candidate.seat === seat);
    const selected = selectedSeat === seat;
    const votes = state?.vote_counts?.[String(seat)] ?? 0;
    const name = player?.name ?? "Open seat";
    const label = selected ? "Answering" : voting && player?.online ? `${votes} ${votes === 1 ? "vote" : "votes"}` : player?.online ? "Online" : player ? "Offline" : "Available";
    const description = player ? `${name}${player.is_host ? ", host" : ""}, ${player.online ? "online" : "offline"}` : "Open seat";
    return { seat, name, self: !!player && seat === state?.self_seat, online: !!player?.online, selected, label,
      accessibleLabel: `Defender seat ${seat + 1}: ${description}${selected ? ", chosen to answer" : ""}${voting && player?.online ? `, ${votes} votes` : ""}` };
  });
  const progress = phase === "complete" ? "COMPLETE" : state
    ? state.question_budget ? `Question ${turns.length} of ${state.question_budget} · ${displayRole(state.active_panelist ?? "Reviewing").replace(" Reviewer", "").replace(" Judge", "")}` : `${resolvedCount} RESOLVED`
    : "READY";
  return {
    currentIndex, answerTurnIndex, acceptedCount, resolvedCount, card, reaction, panelists, defenders,
    voting, chosenSelf, chosenName, timer: deriveTimer(state), status: roomStatus(state), progress,
    coverage: { addressed: Object.values(state?.coverage ?? {}).filter(item => item.status === "addressed").length,
      total: state?.research_plan?.topics.length ?? 0 },
    voteInstruction: "Choose a speaker. You can change your vote until the clock reaches zero.",
    answerPrompt: phase === "question" ? "Your turn · You were chosen to answer" : "You were chosen to answer",
    teammateInstruction: chosenName ? phase === "question" ? `${chosenName} is answering. Use Team Chat to help them.` : `${chosenName} was chosen to answer. Use Team Chat to help them.` : "Waiting for a defender to reconnect. The answer clock keeps running.",
  };
}

export type RoomPresentation = Readonly<ReturnType<typeof deriveRoomPresentation>>;

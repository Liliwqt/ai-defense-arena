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

function interpretationStatus(state: Readonly<RoomState> | null): string | undefined {
  if (state?.phase !== "interpreting" && state?.phase !== "interpretation_retry") return undefined;
  return `${state.phase === "interpreting" ? "Reviewing submission" : "Submission review failed"} · Timer ${state.clock_paused === false ? "running" : "paused"}`;
}

function submissionRecoveryGuidance(state: Readonly<RoomState> | null, chosen: boolean, probing: boolean): string {
  const retryAvailable = state?.interpretation_attempts_left !== 0;
  const prefix = retryAvailable ? "" : "No panelist retries remain. ";
  if (!chosen) return `${prefix}${retryAvailable
    ? state?.self_is_host ? "You can retry the panelist; the selected defender controls their answer." : "The host or selected defender can retry the panelist. The selected defender controls their answer."
    : "The selected defender can submit directly."}`;
  const actions = ["write a new answer"];
  if (retryAvailable) actions.unshift("retry the panelist");
  if (state?.my_pending_submission) actions.push("use the saved submission");
  if (probing) actions.push("continue with the original answer");
  return `${prefix}You can ${actions.join(", or ")}.`;
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
      reviewStatus: interpretationStatus(state),
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
    return { name: "Preparing defense", question: "Preparing the first question…", number: "PREPARING" };
  }
  if (phase === "retry") {
    return { name: "Question paused", question: `${state?.error ?? "The next question could not be generated."} ${lifecycleGuidance(state)}`, number: "RETRY" };
  }
  if (phase === "complete") {
    const feedback = state?.feedback_status;
    return {
      name: feedback === "generating" ? "Preparing coaching report" : "Defense complete",
      question: feedback === "generating"
        ? "The panel has finished. Your coaching report is being prepared."
        : feedback === "failed"
          ? `${state?.error ?? "The coaching report could not be generated."} ${lifecycleGuidance(state)}`
          : `Open Transcript to review your answers${feedback === "ready" ? " and coaching report" : ""}.${state?.completion_reason ? ` Ending reason: ${state.completion_reason}.` : ""}`,
      number: `${resolved} RESOLVED`,
    };
  }
  if (phase === "lobby") {
    if (state?.research_planning_status === "planning") {
      return { name: "Preparing research coverage", question: "Mapping the uploaded research. The scope preview will appear in Controls for your team to inspect.", number: "MAPPING" };
    }
    if (state?.research_planning_status === "failed") {
      return { name: "Research mapping failed", question: `${state.research_plan_error ?? "The paper map could not be prepared."} ${lifecycleGuidance(state)}`, number: "RETRY PLAN" };
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
  const probing = state.turns?.at(-1)?.probe?.status === "pending";
  if (reviewing && state.clock_paused !== false) {
    return { mode: "paused", deadline: null, serverNow: state.server_now_ms ?? 0,
      savedSeconds: Math.ceil((state.remaining_answer_ms ?? 0) / 1000), label: "PAUSED",
      accessibleLabel: `${probing ? "Reply" : "Answer"} timer paused`, urgentAt: 15 };
  }
  const voting = state.phase === "voting";
  if (!voting && state.phase !== "question" && state.phase !== "probe" && !reviewing) return null;
  return { mode: "running", deadline: (voting ? state.vote_deadline_ms : state.answer_deadline_ms) ?? null,
    serverNow: state.server_now_ms ?? 0, savedSeconds: null,
    label: voting ? "VOTE" : probing ? "REPLY" : "ANSWER",
    accessibleLabel: `${voting ? "Vote" : probing ? "Reply" : "Answer"} time remaining`,
    urgentAt: voting ? 5 : 15 };
}

function roomStatus(state: Readonly<RoomState> | null): string {
  if (state?.phase === "complete") return state.feedback_status === "generating" ? "Preparing coaching…" : state.feedback_status === "failed" ? "Coaching unavailable" : state.feedback_status === "ready" ? "Coaching ready" : "Complete";
  if (state?.phase === "retry") return "Retry needed";
  if (state?.phase === "reacting") return "Panelist speaking…";
  if (state?.phase === "generating") {
    const previous = state.turns?.at(-1);
    return previous?.timed_out ? "Reviewing missed turn…" : previous?.answer ? "Reviewing answer…" : "Preparing question…";
  }
  if (state?.research_planning_status === "planning") return "Mapping research…";
  if (state?.research_planning_status === "failed") return "Retry needed";
  if (state?.phase === "lobby" && state.research_plan) return "Research scope ready";
  return "Ready";
}

function recoveryGuidance(state: Readonly<RoomState>, name: string, remaining: number | undefined): string {
  if (remaining === 0) return `No ${name} retries remain. ${state.self_is_host ? "Open Controls to review recovery options." : "The host can review recovery options in Controls."}`;
  return state.self_is_host ? `Retry ${name} from Controls. The saved turns are retained.` : `The host can retry ${name} from Controls. The saved turns are retained.`;
}

function lifecycleGuidance(state: Readonly<RoomState> | null): string {
  if (!state) return "Create or join a room to begin your defense.";
  if (state.phase === "lobby") {
    if (state.research_planning_status === "planning") return "Mapping research… Your uploads are retained; wait for the scope preview.";
    if (state.research_planning_status === "failed") return recoveryGuidance(state, "research plan", state.plan_attempts_left);
    if (state.research_plan) return state.self_is_host
      ? state.research_plan_approved ? "Research scope ready. Start from Controls when the team is ready." : "Research scope ready. Review and confirm the budget in Controls."
      : "Research scope ready. Inspect it in Controls while the host confirms the budget and starts.";
    return state.self_is_host ? "Start the defense from Controls when your team is ready." : "Waiting for the host to start the defense.";
  }
  if (state.phase === "generating") {
    const previous = state.turns?.at(-1);
    return previous?.timed_out ? "Reviewing missed turn… No answer was given; wait for the next question."
      : previous?.answer ? "Reviewing answer… The accepted answer is saved; wait for the panel."
      : "Preparing the first question… Wait for the panel.";
  }
  if (state.phase === "reacting") return "Listen to the panelist. Your full voting and answer time starts afterward.";
  if (state.phase === "retry") return recoveryGuidance(state, "question", state.question_attempts_left);
  if (state.phase === "complete") {
    if (state.feedback_status === "generating") return "Preparing the team's coaching report… Your answers are saved.";
    if (state.feedback_status === "failed") return recoveryGuidance(state, "coaching report", state.coaching_attempts_left);
    return state.feedback_status === "ready" ? "Defense complete. Open Transcript to review answers, timeouts, and coaching." : "Defense complete. Open Transcript to review the saved turns.";
  }
  return "Waiting for the next question…";
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
  const reviewing = phase === "interpreting";
  const retryingSubmission = phase === "interpretation_retry";
  const voting = phase === "voting";
  const reacting = phase === "reacting";
  const answering = ["question", "probe", "interpreting", "interpretation_retry"].includes(phase ?? "");
  const answerTurnIndex = answering ? currentIndex : -1;
  const selectedSeat = answering ? state?.selected_seat ?? null : null;
  const chosenName = state?.players?.find(player => player.seat === selectedSeat)?.name;
  const chosenSelf = answerTurnIndex >= 0 && selectedSeat !== null && selectedSeat === state?.self_seat;
  const current = turns[answerTurnIndex];
  const probe = current?.probe;
  const probing = probe?.status === "pending";
  const clarificationCount = (current?.clarifications?.length ?? 0) + (probe?.clarifications.length ?? 0);
  const reviewStatus = interpretationStatus(state);
  const submission = {
    probe, probing, reviewing, retrying: retryingSubmission,
    turnKey: `${state?.room_code ?? ""}:${answerTurnIndex}:${current?.question ?? ""}:${probe?.id ?? ""}`,
    clarificationCount,
    entry: phase === "question" || phase === "probe" || (reviewing && state?.clock_paused === false)
      ? "open" as const : retryingSubmission ? "recovery" as const : "closed" as const,
    direct: !!state?.probe_recovery_available || clarificationCount >= 2 || state?.interpretation_attempts_left === 0 || retryingSubmission || reviewing,
    recoveryAvailable: !!state?.probe_recovery_available || state?.interpretation_attempts_left === 0 || retryingSubmission,
    showRecovery: retryingSubmission && (chosenSelf || !!state?.self_is_host),
    retryAvailable: state?.interpretation_attempts_left !== 0,
    savedAvailable: !!state?.my_pending_submission,
    guidance: reviewStatus,
    recoveryGuidance: reviewStatus ? `${reviewStatus}. ${submissionRecoveryGuidance(state, chosenSelf, probing)}` : "",
    reviewGuidance: reviewStatus ? `${reviewStatus}. ${chosenName ? `Selected defender: ${chosenName}.` : "Waiting for a selected defender."}` : "",
  };
  const rawCard = deriveContent(state, currentIndex, resolvedCount);
  const card = { ...rawCard, name: displayRole(rawCard.name) };
  const clarification = card.probe ? undefined : card.clarifications?.at(-1);
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
    const label = selected ? reviewing || retryingSubmission ? "Selected" : probing ? "Replying" : "Answering" : voting && player?.online ? `${votes} ${votes === 1 ? "vote" : "votes"}` : player?.online ? "Online" : player ? "Offline" : "Available";
    const description = player ? `${name}${player.is_host ? ", host" : ""}, ${player.online ? "online" : "offline"}` : "Open seat";
    return { seat, name, self: !!player && seat === state?.self_seat, online: !!player?.online, selected, label,
      accessibleLabel: `Defender seat ${seat + 1}: ${description}${selected ? ", chosen to answer" : ""}${voting && player?.online ? `, ${votes} votes` : ""}` };
  });
  const progress = phase === "complete" ? "COMPLETE" : state
    ? state.question_budget ? turns.length === 0 ? `0 of ${state.question_budget} questions generated` : `Question ${turns.length} of ${state.question_budget} · ${displayRole(state.active_panelist ?? "Reviewing").replace(" Reviewer", "").replace(" Judge", "")}` : `${resolvedCount} RESOLVED`
    : "READY";
  const voteInstruction = "Choose a speaker. You can change your vote until the clock reaches zero.";
  const answerPrompt = probing ? "Reply to panelist" : phase === "question" ? "Your turn · You were chosen to answer" : "Submit an answer directly";
  const teammateInstruction = chosenName ? `${chosenName} is ${probing ? "replying" : "answering"}. Use Team Chat to help them.` : "Waiting for a defender to reconnect. The answer clock keeps running.";
  const guidance = voting ? voteInstruction
    : retryingSubmission ? submission.recoveryGuidance
    : reviewing ? submission.reviewGuidance
    : phase === "question" || phase === "probe" ? chosenSelf ? `${answerPrompt} in the bottom dock.` : teammateInstruction
    : lifecycleGuidance(state);
  return {
    currentIndex, answerTurnIndex, acceptedCount, resolvedCount, card, clarification, reaction, panelists, defenders,
    guidance,
    controls: { questionRetry: phase === "retry", questionRetryAvailable: state?.question_attempts_left !== 0,
      coachingRetry: phase === "complete" && state?.feedback_status === "failed", coachingRetryAvailable: state?.coaching_attempts_left !== 0 },
    voting, chosenSelf, chosenName, submission, timer: deriveTimer(state), status: interpretationStatus(state) ?? roomStatus(state), progress,
    coverage: { addressed: Object.values(state?.coverage ?? {}).filter(item => item.status === "addressed").length,
      total: state?.research_plan?.topics.length ?? 0 },
    voteInstruction, answerPrompt, teammateInstruction,
  };
}

export type RoomPresentation = Readonly<ReturnType<typeof deriveRoomPresentation>>;

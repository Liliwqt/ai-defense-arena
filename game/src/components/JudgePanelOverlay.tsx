/**
 * JudgePanelOverlay
 *
 * A pure-React/CSS overlay that renders four animated judge avatars aligned
 * to the top (panelist) row of the Phaser stage.  It reads the current
 * session phase, active panelist, and a local "discussing" flag to drive
 * four possible animation states per judge:
 *
 *   idle        — subtle personality-specific idle behaviour while user composes
 *   active      — prominent glow + speaking motion for the judge asking a question
 *   discussing  — shared "thinking together" animation after an answer is submitted
 *   waiting     — calm attentive pose (lobby, generating, complete)
 *
 * No Phaser or animation library dependency — all animations are CSS keyframes
 * defined in index.css.
 */

import type { RoomState } from "../types";
import { JUDGES, type JudgeConfig, type JudgeState } from "./judgeConfig";

interface JudgePanelOverlayProps {
  roomState: RoomState | null;
  /** Transient flag set briefly after answer submission, before next question. */
  discussing: boolean;
}

/**
 * Determine the animation state for a single judge given the current room state.
 */
function resolveJudgeState(
  judge: JudgeConfig,
  roomState: RoomState | null,
  discussing: boolean,
): JudgeState {
  const phase = roomState?.phase ?? "none";

  // Post-answer discussion sequence takes priority over everything
  if (discussing) return "discussing";

  // Active speaker
  if (
    (phase === "question" || phase === "generating") &&
    roomState?.active_panelist === judge.name
  ) {
    return "active";
  }

  // If there's an unanswered turn for this judge and we're in question phase
  if (phase === "question") {
    const unanswered = (roomState?.turns ?? []).some(
      (t) => t.panelist === judge.name && t.question && !t.answer,
    );
    if (unanswered) return "active";
  }

  // User is actively composing — all non-active judges do idle personality anim
  if (phase === "question") return "idle";

  // In lobby or generating, everyone waits attentively
  if (phase === "lobby" || phase === "generating") return "waiting";

  // Complete — relaxed waiting
  if (phase === "complete") return "waiting";

  // Default
  return "waiting";
}

/** Build the CSS class string for a judge avatar given its state + variant. */
function avatarClasses(judge: JudgeConfig, state: JudgeState): string {
  const base = "judge-avatar";
  const stateClass = `judge-${state}`;
  const variantClass = state === "idle" ? `judge-idle-${judge.idleVariant}` : "";
  return [base, stateClass, variantClass].filter(Boolean).join(" ");
}

/**
 * Render a single judge avatar tile.
 * Each tile is absolutely positioned in the parent overlay grid.
 */
function JudgeAvatar({
  judge,
  state,
  index,
}: {
  judge: JudgeConfig;
  state: JudgeState;
  index: number;
}) {
  const isActive = state === "active";
  const isDiscussing = state === "discussing";

  return (
    <div
      className="judge-slot"
      style={{ "--judge-index": index } as React.CSSProperties}
      aria-label={`${judge.name}: ${judge.description}${isActive ? " — asking a question" : ""}`}
      role="img"
    >
      {/* Glow ring — only visible when active */}
      <div
        className="judge-glow-ring"
        style={{
          opacity: isActive ? 1 : isDiscussing ? 0.35 : 0,
          boxShadow: isActive
            ? `0 0 0 3px ${judge.accentColor}, 0 0 22px 6px ${judge.glowColor}`
            : isDiscussing
            ? `0 0 0 2px ${judge.accentColor}88, 0 0 14px 3px ${judge.glowColor}`
            : "none",
          transition: "opacity 0.4s ease, box-shadow 0.4s ease",
        }}
      />

      {/* Avatar body */}
      <div
        className={avatarClasses(judge, state)}
        style={
          {
            "--accent": judge.accentColor,
            "--glow": judge.glowColor,
          } as React.CSSProperties
        }
      >
        {/* Head */}
        <div className="judge-head">
          {/* Eyes */}
          <div className="judge-eyes">
            <div className="judge-eye judge-eye-left" />
            <div className="judge-eye judge-eye-right" />
          </div>
          {/* Mouth / expression */}
          <div className={`judge-mouth judge-mouth-${judge.idleVariant}`} />
        </div>

        {/* Jacket body */}
        <div className="judge-body">
          <div
            className="judge-lapel"
            style={{ borderColor: judge.accentColor }}
          />
        </div>

        {/* Speaking / thinking indicator */}
        {isActive && (
          <div className="judge-speaking-cue" aria-hidden="true">
            <span className="judge-dot" />
            <span className="judge-dot" />
            <span className="judge-dot" />
          </div>
        )}
        {isDiscussing && (
          <div className="judge-thinking-cue" aria-hidden="true">
            <span className="judge-dot" />
            <span className="judge-dot" />
            <span className="judge-dot" />
          </div>
        )}
      </div>

      {/* Name label */}
      <span
        className="judge-label"
        style={{ color: isActive ? judge.accentColor : undefined }}
      >
        {judge.shortLabel}
      </span>
    </div>
  );
}

export function JudgePanelOverlay({
  roomState,
  discussing,
}: JudgePanelOverlayProps) {
  const judges = roomState?.defense_type && roomState.defense_type !== "code"
    ? JUDGES.map((judge, index) => ({ ...judge,
        name: ["Impact Reviewer", "Methodology Reviewer", "Ethics Reviewer", "Critical Reviewer"][index],
        shortLabel: ["Impact", "Methodology", "Ethics", "Critical"][index],
      }))
    : JUDGES;
  return (
    <div
      className="judge-panel-overlay"
      aria-label="Judge panel"
      role="group"
    >
      {judges.map((judge, index) => {
        const state = resolveJudgeState(judge, roomState, discussing);
        return (
          <JudgeAvatar
            key={judge.name}
            judge={judge}
            state={state}
            index={index}
          />
        );
      })}
    </div>
  );
}

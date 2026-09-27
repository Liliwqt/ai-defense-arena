/**
 * Judge personality configuration.
 * Defines per-judge CSS classes, idle animation variant, and colors for the
 * JudgePanelOverlay.  No business logic here — purely presentation config.
 */

export type JudgeState = "idle" | "active" | "discussing" | "waiting";

export interface JudgeConfig {
  /** Full display name (must match server panelist strings). */
  name: string;
  /** Short label shown under the avatar. */
  shortLabel: string;
  /** Tailwind/CSS ring accent colour (raw hex, used inline). */
  accentColor: string;
  /** Glow colour when active. */
  glowColor: string;
  /** Which idle animation variant to use. */
  idleVariant: "composed" | "analytical" | "watchful" | "skeptical";
  /** ARIA description of the personality. */
  description: string;
}

export const JUDGES: readonly JudgeConfig[] = [
  {
    name: "Product Judge",
    shortLabel: "Product",
    accentColor: "#e9747c",
    glowColor: "rgba(233,116,124,0.55)",
    idleVariant: "composed",
    description: "Professional and attentive",
  },
  {
    name: "Technical Architect",
    shortLabel: "Technical",
    accentColor: "#5ba3e8",
    glowColor: "rgba(91,163,232,0.55)",
    idleVariant: "analytical",
    description: "Analytical and thoughtful",
  },
  {
    name: "Security Reviewer",
    shortLabel: "Security",
    accentColor: "#59c98e",
    glowColor: "rgba(89,201,142,0.55)",
    idleVariant: "watchful",
    description: "Cautious, observant, slightly suspicious",
  },
  {
    name: "Critical Judge",
    shortLabel: "Critical",
    accentColor: "#b97cff",
    glowColor: "rgba(185,124,255,0.55)",
    idleVariant: "skeptical",
    description: "Skeptical, stern, and challenging",
  },
] as const;

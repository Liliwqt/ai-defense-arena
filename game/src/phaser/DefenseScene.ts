import Phaser from "phaser";
import type { RoomState } from "../types";

const PANEL_NAMES = ["Product Judge", "Technical Architect", "Security Reviewer", "Critical Judge"] as const;

interface Seat {
  ring: Phaser.GameObjects.Arc;
  glow: Phaser.GameObjects.Arc;
  sprite: Phaser.GameObjects.Sprite | null;
  label: Phaser.GameObjects.Text;
}

interface DefenderSeat {
  ring: Phaser.GameObjects.Arc;
  sprite: Phaser.GameObjects.Sprite;
  label: Phaser.GameObjects.Text;
}

function findCurrentTurn(state: RoomState | null) {
  const turns = state?.turns ?? [];
  for (let i = turns.length - 1; i >= 0; i--) {
    if (turns[i].question && !turns[i].answer)
      return { turn: turns[i], index: i };
  }
  return null;
}

export class DefenseScene extends Phaser.Scene {
  private background!: Phaser.GameObjects.Graphics;
  private panelSeats!: Seat[];
  private defenderSeats!: DefenderSeat[];
  private cue!: Phaser.GameObjects.Graphics;
  private cueText!: Phaser.GameObjects.Text;
  private currentState: RoomState | null = null;

  constructor() {
    super("DefenseScene");
  }

  create() {
    this.makeTextures();
    this.background = this.add.graphics();
    this.panelSeats = Array.from({ length: 4 }, (_, index) => ({
      ring: this.add
        .circle(0, 0, 40, 0x5c2737, 0.62)
        .setStrokeStyle(2, 0xe9747c, 0.8),
      glow: this.add
        .circle(0, 0, 46)
        .setStrokeStyle(4, 0xffd26d, 1)
        .setVisible(false),
      sprite: this.add.sprite(0, 0, "panelist"),
      label: this.add
        .text(
          0,
          0,
          PANEL_NAMES[index],
          {
            fontFamily: "Arial, sans-serif",
            color: "#ffe0e0",
            fontStyle: "bold",
            align: "center",
          },
        )
        .setOrigin(0.5),
    }));
    this.defenderSeats = Array.from({ length: 4 }, (_, index) => ({
      ring: this.add
        .circle(0, 0, 40, 0x1e527b, 0.55)
        .setStrokeStyle(2, 0x55a9e6, 0.8),
      sprite: this.add.sprite(0, 0, "defender").setAlpha(0.22),
      label: this.add
        .text(0, 0, `Open seat ${index + 1}`, {
          fontFamily: "Arial, sans-serif",
          color: "#9cb7d3",
          fontStyle: "bold",
          align: "center",
        })
        .setOrigin(0.5),
    }));
    this.cue = this.add.graphics();
    this.cueText = this.add
      .text(0, 0, "", {
        fontFamily: "Arial, sans-serif",
        color: "#16324b",
        fontStyle: "bold",
        align: "center",
      })
      .setOrigin(0.5);
    this.scale.on("resize", this.layout, this);
    this.layout();
    this.renderState(this.currentState);
  }

  private makeTextures() {
    for (const [name, jacket, trim] of [
      ["panelist", 0xe66572, 0xffced0],
      ["defender", 0x4baef2, 0xc3ebff],
    ] as [string, number, number][]) {
      const g = this.make.graphics({ x: 0, y: 0 }, false);
      g.fillStyle(0x071526, 0.25);
      g.fillEllipse(43, 78, 60, 10);
      g.fillStyle(jacket);
      g.fillRoundedRect(13, 37, 60, 42, 12);
      g.fillStyle(trim);
      g.fillTriangle(36, 38, 50, 38, 43, 57);
      g.fillStyle(0xe9ad82);
      g.fillCircle(43, 25, 21);
      g.fillStyle(0x19273d);
      g.fillEllipse(43, 13, 44, 19);
      g.fillCircle(37, 26, 2);
      g.fillCircle(49, 26, 2);
      g.lineStyle(2, 0x855545);
      g.lineBetween(37, 34, 49, 34);
      g.generateTexture(name, 86, 84);
      g.destroy();
    }
  }

  layout() {
    if (!this.panelSeats) return;
    const width = this.scale.width;
    const height = this.scale.height;
    const compact = height < 320;
    const radius = compact
      ? Phaser.Math.Clamp(height * 0.085, 17, 28)
      : Phaser.Math.Clamp(height * 0.095, 24, 63);
    const panelY = compact
      ? Math.max(66, height * 0.31)
      : Math.max(130, height * 0.24);
    const defenderY = compact ? height - 53 : height * 0.73;
    const labelSize = compact ? "10px" : "15px";
    const labelWidth = width * 0.22;
    this.background.clear();
    this.background.fillStyle(0x0d2238, 1).fillRect(0, 0, width, height);
    this.background.fillStyle(0x183651, 1).fillRoundedRect(
      12,
      compact ? 39 : 72,
      width - 24,
      height - (compact ? 45 : 82),
      15,
    );
    this.background
      .lineStyle(2, 0x42688a, 0.75)
      .strokeRoundedRect(
        12,
        compact ? 39 : 72,
        width - 24,
        height - (compact ? 45 : 82),
        15,
      );
    this.background
      .lineStyle(2, 0x3b6382, 0.8)
      .lineBetween(
        30,
        (panelY + defenderY) / 2,
        width - 30,
        (panelY + defenderY) / 2,
      );
    for (let index = 0; index < 4; index++) {
      const x = width * (0.14 + index * 0.24);
      const panel = this.panelSeats[index];
      panel.ring.setPosition(x, panelY).setRadius(radius);
      panel.glow.setPosition(x, panelY).setRadius(radius + 6);
      if (panel.sprite)
        panel.sprite
          .setPosition(x, panelY + 3)
          .setScale((radius * 1.55) / 86);
      panel.label
        .setPosition(x, panelY + radius + (compact ? 9 : 13))
        .setFontSize(labelSize)
        .setWordWrapWidth(labelWidth);
      const defender = this.defenderSeats[index];
      defender.ring.setPosition(x, defenderY).setRadius(radius);
      defender.sprite
        .setPosition(x, defenderY + 3)
        .setScale((radius * 1.55) / 86);
      defender.label
        .setPosition(x, defenderY + radius + (compact ? 9 : 13))
        .setFontSize(labelSize)
        .setWordWrapWidth(labelWidth);
    }
    this.cueText.setFontSize(compact ? "12px" : "20px");
    this.renderCue(this.currentState);
  }

  private renderCue(state: RoomState | null) {
    const height = this.scale.height;
    const width = this.scale.width;
    const compact = height < 320;
    const panelY = compact
      ? Math.max(66, height * 0.31)
      : Math.max(130, height * 0.24);
    const defenderY = compact ? height - 53 : height * 0.73;
    const cueY = compact ? panelY : (panelY + defenderY) / 2;
    const cueWidth = compact ? Math.min(width * 0.18, 160) : Math.min(width * 0.48, 530);
    const cueHeight = compact ? 28 : 68;
    const activeName =
      state?.active_panelist ?? findCurrentTurn(state)?.turn.panelist;
    const activeIndex = PANEL_NAMES.findIndex((name) => name === activeName);
    let cue = "Create or join a room";
    if (state?.phase === "lobby") cue = "Your team is gathering";
    else if (state?.phase === "generating")
      cue = `${activeName ?? "The panel"} is preparing a question`;
    else if (state?.phase === "question")
      cue = `${activeName ?? "The panel"} is asking`;
    else if (state?.phase === "retry") cue = "Question paused · host can retry";
    else if (state?.phase === "complete") {
      const fs = state.feedback_status;
      if (fs === "generating") cue = "Preparing coaching report";
      else if (fs === "failed") cue = "Coaching report failed";
      else cue = "Defense complete";
    }
    this.cue.clear();
    this.cue
      .fillStyle(0xe7f4ff, 1)
      .fillRoundedRect(
        width / 2 - cueWidth / 2,
        cueY - cueHeight / 2,
        cueWidth,
        cueHeight,
        compact ? 9 : 15,
      );
    this.cue
      .lineStyle(2, 0x8fc8e9, 1)
      .strokeRoundedRect(
        width / 2 - cueWidth / 2,
        cueY - cueHeight / 2,
        cueWidth,
        cueHeight,
        compact ? 9 : 15,
      );
    if (activeIndex >= 0 && !compact && state?.phase !== "complete") {
      const x = width * (0.14 + activeIndex * 0.24);
      this.cue
        .fillStyle(0xe7f4ff, 1)
        .fillTriangle(
          x - 11,
          cueY - cueHeight / 2 + 1,
          x + 11,
          cueY - cueHeight / 2 + 1,
          x,
          cueY - cueHeight / 2 - 12,
        );
    }
    const compactCue = state?.phase === "question" ? "Asking" :
      state?.phase === "generating" ? "Preparing" :
      state?.phase === "retry" ? "Retry" :
      state?.phase === "complete" ? "Complete" :
      state?.phase === "lobby" ? "Waiting" : "Join a room";
    this.cueText
      .setPosition(width / 2, cueY)
      .setWordWrapWidth(cueWidth - 20)
      .setText(compact ? compactCue : cue);
    this.panelSeats.forEach((seat, index) =>
      seat.glow.setVisible(
        index === activeIndex && state?.phase !== "complete",
      ),
    );
  }

  renderState(state: RoomState | null) {
    this.currentState = state;
    if (!this.panelSeats) return;
    const players = state?.players ?? [];
    for (let index = 0; index < 4; index++) {
      const seat = this.defenderSeats[index];
      const player = players.find((p) => p.seat === index);
      seat.sprite.setAlpha(player ? (player.online ? 1 : 0.45) : 0.22);
      seat.label.setText(
        player
          ? `${player.name || "Defender"}${player.is_host ? " ★" : ""}${player.online ? "" : " (offline)"}`
          : `Open seat ${index + 1}`,
      );
      seat.label.setColor(player ? "#cdeeff" : "#91a6bd");
    }
    this.renderCue(state);
  }
}

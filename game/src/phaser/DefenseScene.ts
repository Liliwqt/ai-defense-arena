import Phaser from "phaser";
import type { RoomState } from "../types";

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

export class DefenseScene extends Phaser.Scene {
  private background!: Phaser.GameObjects.Graphics;
  private panelSeats!: Seat[];
  private defenderSeats!: DefenderSeat[];
  private speakerDot!: Phaser.GameObjects.Arc;
  private currentState: RoomState | null = null;

  constructor() {
    super("DefenseScene");
  }

  create() {
    this.makeTextures();
    this.background = this.add.graphics();
    this.panelSeats = Array.from({ length: 4 }, (_u, _i) => ({
      ring: this.add
        .circle(0, 0, 40, 0x0d1f35, 0.0)   // hidden — React overlay covers panel row
        .setStrokeStyle(0, 0xe9747c, 0),
      glow: this.add
        .circle(0, 0, 46)
        .setStrokeStyle(0, 0xffd26d, 0)
        .setVisible(false),
      sprite: null as unknown as Phaser.GameObjects.Sprite, // not created; overlay renders avatars
      label: this.add
        .text(
          0,
          0,
          "",  // hidden — React JudgePanelOverlay renders panelist labels
          {
            fontFamily: "Arial, sans-serif",
            color: "#ffe0e0",
            fontStyle: "bold",
            align: "center",
          },
        )
        .setOrigin(0.5)
        .setVisible(false),
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
    this.speakerDot = this.add.circle(0, 0, 6, 0xffd26d).setVisible(false);
    this.scale.on("resize", this.layout, this);
    this.layout();
    this.renderState(this.currentState);
  }

  private makeTextures() {
    // Only the "defender" texture is used; panelist avatars are rendered by
    // the React JudgePanelOverlay, so their Phaser sprite is null.
    for (const [name, jacket, trim] of [
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
    const compact = height < 480;
    const radius = compact
      ? Phaser.Math.Clamp(height * 0.08, 17, 26)
      : Phaser.Math.Clamp(height * 0.075, 24, 58);
    const panelY = compact
      ? Math.max(62, height * 0.25)
      : Math.max(105, height * 0.18);
    const defenderY = compact ? height - 52 : Math.min(height - 78, height * 0.84);
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
    this.renderSpeaker(this.currentState);
  }

  private renderSpeaker(state: RoomState | null) {
    // The React JudgePanelOverlay now handles the active-judge glow and
    // speaking cue.  Hide the Phaser glow rings and speaker dot to avoid
    // double-rendering on top of the React overlay.
    this.panelSeats.forEach((seat) => seat.glow.setVisible(false));
    this.speakerDot.setVisible(false);
    void state; // consumed by JudgePanelOverlay
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
    this.renderSpeaker(state);
  }
}

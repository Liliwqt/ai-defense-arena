import { useEffect, useRef } from "react";
import Phaser from "phaser";
import { DefenseScene } from "../phaser/DefenseScene";
import type { RoomState } from "../types";

interface PhaserSceneProps {
  roomState: RoomState | null;
}

export function PhaserScene({ roomState }: PhaserSceneProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const gameRef = useRef<Phaser.Game | null>(null);

  // Mount Phaser once
  useEffect(() => {
    if (!containerRef.current) return;
    const game = new Phaser.Game({
      type: Phaser.AUTO,
      parent: containerRef.current,
      width: 960,
      height: 540,
      backgroundColor: "#0d2238",
      scale: { mode: Phaser.Scale.RESIZE },
      scene: DefenseScene,
    });
    gameRef.current = game;
    return () => {
      game.destroy(true);
      gameRef.current = null;
    };
  }, []);

  // Forward roomState updates to the scene without re-mounting
  useEffect(() => {
    const game = gameRef.current;
    if (!game) return;
    const scene = game.scene.getScene("DefenseScene") as DefenseScene | null;
    scene?.renderState(roomState);
  }, [roomState]);

  return (
    <div
      id="phaser-container"
      ref={containerRef}
      className="absolute inset-0 w-full h-full"
      aria-label="Four panelist seats face four defender seats"
    />
  );
}

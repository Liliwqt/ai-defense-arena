import { useEffect, useRef } from "react";
import Phaser from "phaser";
import { DefenseScene } from "../phaser/DefenseScene";
import type { RoomState } from "../types";

interface PhaserSceneProps {
  roomState: RoomState | null;
}

export function PhaserScene({ roomState }: PhaserSceneProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const sceneRef = useRef<DefenseScene | null>(null);
  const latestStateRef = useRef(roomState);
  latestStateRef.current = roomState;

  // Mount Phaser once
  useEffect(() => {
    if (!containerRef.current) return;
    const scene = new DefenseScene();
    scene.renderState(latestStateRef.current);
    const game = new Phaser.Game({
      type: Phaser.AUTO,
      parent: containerRef.current,
      width: 960,
      height: 540,
      backgroundColor: "#0d2238",
      scale: { mode: Phaser.Scale.RESIZE },
      scene,
    });
    sceneRef.current = scene;
    return () => {
      game.destroy(true);
      sceneRef.current = null;
    };
  }, []);

  // Forward roomState updates to the scene without re-mounting
  useEffect(() => {
    sceneRef.current?.renderState(roomState);
  }, [roomState]);

  return (
    <div
      id="phaser-container"
      ref={containerRef}
      className="absolute inset-0 w-full h-full"
      aria-label="Four active panelists face four defender seats"
    />
  );
}

import { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import type { RoomState } from "../types";

export interface PresenterMoment { seat: number; sequence: number; reducedMotion: boolean }

interface ThreeDefenseSceneProps {
  roomState: RoomState | null;
  presenterMoment: PresenterMoment | null;
}

const judgeNames = ["Technical Architect", "Security Reviewer", "Product Judge", "Critical Judge"];
const judgeColors = [0x346eae, 0xdda33f, 0x8167af, 0xb66378];
const defenderColors = [0x4a8ac5, 0x6896a2, 0x727db7, 0x9a78a3];
const judgeXs = [-5.25, -1.75, 1.75, 5.25];
const defenderXs = [-5.6, -3.15, -0.7, 1.75];
const podium = new THREE.Vector3(4.35, 0, 1.45);
const softWhite = new THREE.MeshStandardMaterial({ color: 0xf7fbff, roughness: 0.74 });
const paleBlue = new THREE.MeshStandardMaterial({ color: 0xdceaf8, roughness: 0.78 });
const deepBlue = new THREE.MeshStandardMaterial({ color: 0x263a5b, roughness: 0.78 });
const warmWood = new THREE.MeshStandardMaterial({ color: 0xd9b794, roughness: 0.83 });

function box(parent: THREE.Object3D, size: [number, number, number], position: [number, number, number], material: THREE.Material, cast = true) {
  const mesh = new THREE.Mesh(new THREE.BoxGeometry(...size), material);
  mesh.position.set(...position);
  mesh.castShadow = cast;
  mesh.receiveShadow = true;
  parent.add(mesh);
  return mesh;
}

function cylinder(parent: THREE.Object3D, radiusTop: number, radiusBottom: number, height: number, position: [number, number, number], material: THREE.Material, sides = 16) {
  const mesh = new THREE.Mesh(new THREE.CylinderGeometry(radiusTop, radiusBottom, height, sides), material);
  mesh.position.set(...position);
  mesh.castShadow = true;
  mesh.receiveShadow = true;
  parent.add(mesh);
  return mesh;
}

function sphere(parent: THREE.Object3D, radius: number, position: [number, number, number], material: THREE.Material, width = 16) {
  const mesh = new THREE.Mesh(new THREE.SphereGeometry(radius, width, 12), material);
  mesh.position.set(...position);
  mesh.castShadow = true;
  parent.add(mesh);
  return mesh;
}

function labelTexture(text: string, accent: string, width = 640, dark = false) {
  const canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = 120;
  const ctx = canvas.getContext("2d")!;
  ctx.fillStyle = dark ? "#253b5d" : "rgba(255,255,255,.96)";
  ctx.beginPath();
  ctx.roundRect(5, 5, width - 10, 110, 22);
  ctx.fill();
  ctx.strokeStyle = dark ? "rgba(255,255,255,.35)" : "rgba(50,76,119,.16)";
  ctx.lineWidth = 4;
  ctx.stroke();
  ctx.fillStyle = accent;
  ctx.fillRect(20, 22, 9, 76);
  ctx.fillStyle = dark ? "#ffffff" : "#192947";
  ctx.font = "bold 43px Arial, sans-serif";
  ctx.textBaseline = "middle";
  const truncated = text.length > 22 ? `${text.slice(0, 20)}…` : text;
  ctx.fillText(truncated, 49, 61, width - 68);
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  return texture;
}

function label(text: string, accent: string, scale: [number, number], dark = false) {
  const sprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: labelTexture(text, accent, 640, dark), transparent: true, depthTest: false }));
  sprite.scale.set(scale[0], scale[1], 1);
  sprite.renderOrder = 30;
  return sprite;
}

function deskRolePlaque(text: string, accent: string) {
  const canvas = document.createElement("canvas");
  canvas.width = 512;
  canvas.height = 160;
  const ctx = canvas.getContext("2d")!;
  ctx.fillStyle = "#253b5d";
  ctx.beginPath();
  ctx.roundRect(3, 3, 506, 154, 18);
  ctx.fill();
  ctx.fillStyle = accent;
  ctx.fillRect(21, 21, 12, 118);
  ctx.fillStyle = "#ffffff";
  ctx.font = "bold 57px Arial, sans-serif";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  const [first, second] = text.split(" ");
  ctx.fillText(first, 274, 51, 450);
  ctx.fillText(second, 274, 111, 450);
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  const plaque = new THREE.Mesh(
    new THREE.PlaneGeometry(2.72, 0.62),
    new THREE.MeshBasicMaterial({ map: texture, transparent: true, side: THREE.DoubleSide }),
  );
  plaque.receiveShadow = false;
  return plaque;
}

function setLabelText(sprite: THREE.Sprite, text: string, accent: string, dark = false) {
  const material = sprite.material as THREE.SpriteMaterial;
  material.map?.dispose();
  material.map = labelTexture(text, accent, 640, dark);
  material.needsUpdate = true;
}

function chair(parent: THREE.Object3D, x: number, z: number, facingFront: boolean) {
  const group = new THREE.Group();
  group.position.set(x, 0, z);
  group.rotation.y = facingFront ? 0 : Math.PI;
  parent.add(group);
  box(group, [1.05, 0.17, 0.94], [0, 0.72, 0], deepBlue);
  box(group, [1.1, 1.15, 0.16], [0, 1.33, -0.46], paleBlue);
  for (const dx of [-0.43, 0.43]) for (const dz of [-0.34, 0.34]) {
    cylinder(group, 0.045, 0.045, 0.65, [dx, 0.34, dz], deepBlue, 8);
  }
  return group;
}

function plant(parent: THREE.Object3D, x: number, z: number, scale = 1) {
  const group = new THREE.Group();
  group.position.set(x, 0, z);
  group.scale.setScalar(scale);
  parent.add(group);
  cylinder(group, 0.37, 0.29, 0.72, [0, 0.36, 0], softWhite);
  const leafMaterials = [0x477d5e, 0x68a77c, 0x83b785].map((color) => new THREE.MeshStandardMaterial({ color, side: THREE.DoubleSide, roughness: 0.85 }));
  for (let i = 0; i < 8; i++) {
    const angle = i * Math.PI / 4;
    const leaf = new THREE.Mesh(new THREE.ConeGeometry(0.31, 1.25, 5), leafMaterials[i % 3]);
    leaf.position.set(Math.cos(angle) * 0.22, 1.27 + (i % 3) * 0.11, Math.sin(angle) * 0.22);
    leaf.rotation.z = Math.cos(angle) * 0.37;
    leaf.rotation.x = -Math.sin(angle) * 0.37;
    leaf.castShadow = true;
    group.add(leaf);
  }
}

interface Person {
  group: THREE.Group;
  torso: THREE.Group;
  leftArm: THREE.Group;
  rightArm: THREE.Group;
  halo: THREE.Mesh;
  jacket: THREE.MeshStandardMaterial;
}

function person(color: number, hairColor: number, seated: boolean, skinColor = 0xe7ae83): Person {
  const group = new THREE.Group();
  const jacket = new THREE.MeshStandardMaterial({ color, roughness: 0.78 });
  const hair = new THREE.MeshStandardMaterial({ color: hairColor, roughness: 0.92 });
  const skin = new THREE.MeshStandardMaterial({ color: skinColor, roughness: 0.88 });
  const dark = new THREE.MeshStandardMaterial({ color: 0x1b293b, roughness: 0.85 });
  const torso = new THREE.Group();
  group.add(torso);
  torso.position.y = seated ? 0.95 : 1.13;
  const chest = cylinder(torso, 0.42, 0.52, 0.88, [0, 0.17, 0], jacket);
  chest.scale.z = 0.72;
  cylinder(torso, 0.12, 0.12, 0.17, [0, 0.68, 0], skin);
  sphere(torso, 0.37, [0, 1.02, 0], skin, 20);
  const cap = sphere(torso, 0.385, [0, 1.2, -0.01], hair, 20);
  cap.scale.y = 0.59;
  box(torso, [0.48, 0.09, 0.13], [0, 1.29, 0.27], hair);
  for (const eyeX of [-0.13, 0.13]) sphere(torso, 0.026, [eyeX, 1.03, 0.353], dark, 10);
  const leftArm = new THREE.Group();
  const rightArm = new THREE.Group();
  leftArm.position.set(-0.49, 0.52, 0);
  rightArm.position.set(0.49, 0.52, 0);
  torso.add(leftArm, rightArm);
  cylinder(leftArm, 0.13, 0.11, 0.54, [-0.02, -0.27, 0.07], jacket, 12).rotation.z = -0.23;
  cylinder(rightArm, 0.13, 0.11, 0.54, [0.02, -0.27, 0.07], jacket, 12).rotation.z = 0.23;
  sphere(leftArm, 0.12, [-0.09, -0.52, 0.13], skin);
  sphere(rightArm, 0.12, [0.09, -0.52, 0.13], skin);
  if (!seated) {
    for (const dx of [-0.19, 0.19]) {
      cylinder(group, 0.16, 0.15, 0.9, [dx, 0.47, 0], dark, 12);
      box(group, [0.34, 0.13, 0.5], [dx, 0.07, 0.15], dark);
    }
  }
  const halo = new THREE.Mesh(new THREE.RingGeometry(0.56, 0.7, 32), new THREE.MeshBasicMaterial({ color: 0x5ba8eb, transparent: true, opacity: 0.72, side: THREE.DoubleSide, depthWrite: false }));
  halo.rotation.x = -Math.PI / 2;
  halo.position.y = 0.04;
  halo.visible = false;
  group.add(halo);
  return { group, torso, leftArm, rightArm, halo, jacket };
}

class DefenseWorld {
  readonly renderer: THREE.WebGLRenderer;
  readonly scene = new THREE.Scene();
  readonly camera = new THREE.OrthographicCamera(-10, 10, 6, -6, 0.1, 100);
  private readonly content = new THREE.Group();
  private readonly judges: Person[] = [];
  private readonly defenders: Person[] = [];
  private readonly defenderLabels: THREE.Sprite[] = [];
  private readonly speakerBubble: THREE.Sprite;
  private readonly presenterLabel: THREE.Sprite;
  private readonly standing: Person;
  private readonly baseCamera = new THREE.Vector3(13, 11, 18.8);
  private readonly baseTarget = new THREE.Vector3(0, 0, 1.8);
  private readonly clock = new THREE.Clock();
  private readonly reducedMotion = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches ?? false;
  private moment: { seat: number; started: number; reduced: boolean } | null = null;
  private frame = 0;
  private state: RoomState | null = null;
  private width = 1;
  private height = 1;

  constructor(private host: HTMLElement) {
    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.7));
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.55;
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    host.appendChild(this.renderer.domElement);
    this.scene.background = new THREE.Color(0xdbe8f5);
    this.scene.add(this.content);
    this.scene.add(new THREE.AmbientLight(0xffffff, 2.15));
    const sun = new THREE.DirectionalLight(0xfff2dd, 3.2);
    sun.position.set(-7, 14, 9);
    sun.castShadow = true;
    sun.shadow.mapSize.set(2048, 2048);
    sun.shadow.camera.left = -13; sun.shadow.camera.right = 13;
    sun.shadow.camera.top = 13; sun.shadow.camera.bottom = -13;
    sun.shadow.bias = -0.0003;
    this.scene.add(sun);
    this.camera.position.copy(this.baseCamera);
    this.camera.lookAt(this.baseTarget);
    this.buildRoom();
    this.speakerBubble = label("is asking…", "#e4a83c", [2.8, 0.52]);
    this.speakerBubble.visible = false;
    this.content.add(this.speakerBubble);
    this.standing = person(defenderColors[0], 0x273148, false);
    this.standing.group.position.set(podium.x, 0, podium.z - 0.7);
    this.standing.group.rotation.y = -0.25;
    this.standing.group.visible = false;
    this.content.add(this.standing.group);
    this.presenterLabel = label("Teammate answered", "#347ac2", [2.6, 0.46]);
    this.presenterLabel.position.set(podium.x, 2.65, podium.z - 0.7);
    this.presenterLabel.visible = false;
    this.content.add(this.presenterLabel);
    this.resize();
    this.loop();
  }

  private buildRoom() {
    const room = this.content;
    const wall = new THREE.MeshStandardMaterial({ color: 0xecf3fb, roughness: 0.86 });
    const floor = new THREE.MeshStandardMaterial({ color: 0xf1f5f9, roughness: 0.68 });
    const glass = new THREE.MeshStandardMaterial({ color: 0xa9d8f5, emissive: 0x438fd0, emissiveIntensity: 0.18, roughness: 0.2 });
    box(room, [19, 0.22, 12.4], [0, -0.14, 0], floor, false);
    box(room, [19, 6.2, 0.23], [0, 3, -6.05], wall, false);
    box(room, [0.22, 6.2, 12.4], [-9.45, 3, 0], wall, false);
    const grid = new THREE.GridHelper(19, 19, 0xcbd6e4, 0xdce5ef);
    grid.position.y = -0.025;
    room.add(grid);
    // Glazed left wall and slatted daylight.
    box(room, [0.045, 3.7, 5.1], [-9.27, 2.68, 0.25], glass, false);
    for (let z = -2.25; z <= 2.7; z += 0.74) box(room, [0.08, 3.9, 0.08], [-9.21, 2.68, z], softWhite, false);
    box(room, [0.12, 0.13, 5.55], [-9.2, 4.72, 0.22], warmWood, false);
    // Projection screen with code-built abstract graphics.
    box(room, [7.6, 3.25, 0.12], [2.8, 3.65, -5.79], deepBlue, false);
    box(room, [7.33, 2.98, 0.045], [2.8, 3.65, -5.7], glass, false);
    box(room, [2.35, 1.6, 0.04], [1.25, 3.62, -5.66], new THREE.MeshBasicMaterial({ color: 0x4e8fcc }), false);
    for (let i = 0; i < 5; i++) box(room, [0.25, 0.4 + i * 0.15, 0.05], [4.3 + i * 0.36, 2.78 + i * 0.075, -5.64], new THREE.MeshBasicMaterial({ color: 0x397bbe }), false);
    // Whiteboard and trim.
    box(room, [4.55, 2.65, 0.1], [-5.85, 3.65, -5.78], warmWood, false);
    box(room, [4.36, 2.47, 0.06], [-5.85, 3.65, -5.7], softWhite, false);
    for (let i = 0; i < 3; i++) box(room, [0.8, 0.045, 0.03], [-7 + i * 1.18, 4.15 - i * 0.55, -5.65], paleBlue, false);
    // Panel platform, desk, chairs and people.
    box(room, [15.6, 0.22, 3.65], [0, 0.03, -3.7], paleBlue, false);
    for (let i = 0; i < 4; i++) {
      const x = judgeXs[i];
      chair(room, x, -4.02, true);
      const judge = person(judgeColors[i], [0x263149, 0x432c28, 0x20243e, 0x414049][i], true, [0xe3ad86, 0xd7a078, 0xe8b495, 0xc98e71][i]);
      judge.group.position.set(x, 0.49, -3.72);
      judge.group.rotation.y = 0.12;
      room.add(judge.group);
      this.judges.push(judge);
    }
    box(room, [15.2, 0.32, 1.28], [0, 1.28, -2.15], warmWood);
    box(room, [15.1, 1.16, 0.42], [0, 0.64, -1.65], softWhite);
    judgeXs.forEach((x, i) => {
      box(room, [2.9, 0.7, 0.04], [x, 0.68, -1.42], paleBlue, false);
      const plaque = deskRolePlaque(judgeNames[i], `#${judgeColors[i].toString(16).padStart(6, "0")}`);
      plaque.position.set(x, 0.68, -1.39);
      room.add(plaque);
    });
    // Teammates stand in front of the panel.
    for (let i = 0; i < 4; i++) {
      const x = defenderXs[i];
      const defender = person(defenderColors[i], [0x273148, 0x49302d, 0x282638, 0x513f37][i], false, [0xdca077, 0xe4b18c, 0xc98f72, 0xf0c19d][i]);
      defender.group.position.set(x, 0, 2.34);
      defender.group.rotation.y = Math.PI;
      defender.group.visible = false;
      room.add(defender.group);
      this.defenders.push(defender);
      const badge = label(`Open seat ${i + 1}`, "#5c789b", [2.15, 0.42], true);
      badge.position.set(x, 0.34, 2.95);
      room.add(badge);
      this.defenderLabels.push(badge);
    }
    // Speaker podium.
    box(room, [1.25, 1.2, 0.82], [podium.x, 0.6, podium.z], softWhite);
    box(room, [1.52, 0.16, 1.08], [podium.x, 1.27, podium.z], warmWood);
    cylinder(room, 0.035, 0.035, 0.42, [podium.x, 1.55, podium.z - 0.17], deepBlue, 8);
    sphere(room, 0.1, [podium.x, 1.82, podium.z - 0.17], deepBlue);
    // Room details add depth without baked UI text.
    plant(room, -8.05, -4.68, 0.88);
    plant(room, 8.15, -4.73, 1.08);
    plant(room, 8.38, 3.6, 0.8);
    box(room, [1.45, 2.0, 0.95], [8.35, 1, -1.08], softWhite);
    cylinder(room, 0.37, 0.37, 0.74, [8.35, 2.32, -1.08], glass);
    box(room, [1.7, 0.8, 0.95], [-8.18, 0.4, -4.8], softWhite);
  }

  resize = () => {
    this.width = Math.max(1, this.host.clientWidth);
    this.height = Math.max(1, this.host.clientHeight);
    const aspect = this.width / this.height;
    const viewHeight = aspect > 2.8 ? 15 : 13;
    const viewWidth = viewHeight * aspect;
    this.camera.left = -viewWidth / 2;
    this.camera.right = viewWidth / 2;
    this.camera.top = viewHeight / 2;
    this.camera.bottom = -viewHeight / 2;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(this.width, this.height, false);
  };

  renderState(state: RoomState | null) {
    this.state = state;
    const active = state?.phase === "question" || state?.phase === "voting" || state?.phase === "generating" ? state.active_panelist : null;
    this.judges.forEach((judge, index) => { judge.halo.visible = judgeNames[index] === active; });
    const activeIndex = judgeNames.indexOf(active ?? "");
    this.speakerBubble.visible = activeIndex >= 0 && (state?.phase === "question" || state?.phase === "voting");
    if (activeIndex >= 0) {
      this.speakerBubble.position.set(judgeXs[activeIndex], 3.38, -3.55);
      setLabelText(this.speakerBubble, `${judgeNames[activeIndex]} is asking…`, "#e9aa39");
      this.speakerBubble.scale.set(4.25, 0.55, 1);
    }
    this.defenders.forEach((defender, index) => {
      const player = state?.players.find((item) => item.seat === index);
      defender.group.visible = Boolean(player) && this.moment?.seat !== index;
      const chosen = state?.phase === "question" && state.selected_seat === index;
      defender.halo.visible = Boolean(chosen) && this.moment?.seat !== index;
      if (defender.halo.material instanceof THREE.MeshBasicMaterial) defender.halo.material.color.setHex(chosen ? 0xf5b942 : 0x5ba8eb);
      setLabelText(this.defenderLabels[index], player ? `${player.name}${player.is_host ? " ★" : ""}${chosen ? " • Speaker" : ""}${player.online ? "" : " (offline)"}` : `Open seat ${index + 1}`, chosen ? "#b97812" : player?.online ? "#347ac2" : "#8194ad", true);
    });
  }

  playMoment(moment: PresenterMoment) {
    if (moment.seat < 0 || moment.seat > 3) return;
    this.moment = { seat: moment.seat, started: performance.now(), reduced: moment.reducedMotion };
    const player = this.state?.players.find((item) => item.seat === moment.seat);
    if (!moment.reducedMotion) {
      this.defenders[moment.seat].group.visible = false;
      this.standing.group.visible = true;
      this.standing.group.position.set(podium.x, 0, podium.z - 0.7);
      this.standing.jacket.color.setHex(defenderColors[moment.seat]);
      this.standing.halo.visible = true;
      this.presenterLabel.visible = true;
      setLabelText(this.presenterLabel, `${player?.name ?? "Teammate"} answered`, "#347ac2");
    } else {
      this.defenders[moment.seat].halo.visible = true;
    }
    if (player) setLabelText(this.defenderLabels[moment.seat], `${player.name} answered`, "#347ac2", true);
  }

  private loop = () => {
    this.frame = requestAnimationFrame(this.loop);
    const t = this.clock.getElapsedTime();
    this.judges.forEach((judge, i) => {
      const active = judgeNames[i] === this.state?.active_panelist && (this.state?.phase === "question" || this.state?.phase === "voting");
      judge.torso.position.y = this.reducedMotion ? 0.95 : 0.95 + Math.sin(t * (active ? 3.8 : 1.5) + i) * (active ? 0.035 : 0.012);
      judge.torso.rotation.z = this.reducedMotion ? 0 : Math.sin(t * 1.1 + i) * (active ? 0.025 : 0.009);
      judge.rightArm.rotation.x = !this.reducedMotion && active ? Math.sin(t * 4 + i) * 0.17 : 0;
      if (judge.halo.material instanceof THREE.MeshBasicMaterial) judge.halo.material.opacity = this.reducedMotion ? 0.74 : 0.54 + Math.sin(t * 3.5) * 0.2;
    });
    this.defenders.forEach((defender, i) => { defender.torso.position.y = this.reducedMotion ? 0.95 : 0.95 + Math.sin(t * 1.4 + i * 0.7) * 0.012; });
    if (this.moment) {
      const elapsed = performance.now() - this.moment.started;
      const { seat, reduced } = this.moment;
      if (elapsed >= 2600) {
        this.defenders[seat].halo.visible = false;
        this.standing.group.visible = false;
        this.presenterLabel.visible = false;
        this.defenders[seat].group.visible = Boolean(this.state?.players.find((item) => item.seat === seat));
        this.moment = null;
        this.renderState(this.state);
      } else if (!reduced) {
        const inAmount = Math.min(1, elapsed / 450);
        const outAmount = Math.min(1, Math.max(0, (2600 - elapsed) / 620));
        const strength = Math.min(inAmount, outAmount);
        const eased = strength * strength * (3 - 2 * strength);
        this.camera.zoom = 1 + 0.32 * eased;
        const shift = podium.clone().multiplyScalar(0.48 * eased);
        this.camera.position.copy(this.baseCamera).add(shift);
        this.camera.lookAt(this.baseTarget.clone().add(shift));
        this.camera.updateProjectionMatrix();
        this.standing.torso.position.y = 1.13 + Math.sin(t * 3.8) * 0.027;
        this.standing.group.position.y = -0.3 * (1 - Math.min(1, elapsed / 450));
        this.standing.leftArm.rotation.x = Math.sin(t * 6) * 0.24;
        this.standing.rightArm.rotation.x = -Math.sin(t * 6 + 0.7) * 0.3;
      } else if (this.defenders[seat].halo.material instanceof THREE.MeshBasicMaterial) {
        this.defenders[seat].halo.material.opacity = 0.8;
      }
    } else if (this.camera.zoom !== 1) {
      this.camera.zoom = 1;
      this.camera.position.copy(this.baseCamera);
      this.camera.lookAt(this.baseTarget);
      this.camera.updateProjectionMatrix();
    }
    this.renderer.render(this.scene, this.camera);
  };

  dispose() {
    cancelAnimationFrame(this.frame);
    this.scene.traverse((object) => {
      if (object instanceof THREE.Mesh || object instanceof THREE.Sprite) {
        object.geometry?.dispose();
        const materials = Array.isArray(object.material) ? object.material : [object.material];
        for (const material of materials) {
          if (material instanceof THREE.SpriteMaterial || material instanceof THREE.MeshBasicMaterial) material.map?.dispose();
          material.dispose();
        }
      }
    });
    this.renderer.dispose();
    this.renderer.domElement.remove();
  }
}

export function ThreeDefenseScene({ roomState, presenterMoment }: ThreeDefenseSceneProps) {
  const hostRef = useRef<HTMLDivElement>(null);
  const worldRef = useRef<DefenseWorld | null>(null);
  const latestState = useRef(roomState);
  const latestMoment = useRef(presenterMoment);
  const [unavailable, setUnavailable] = useState(false);
  latestState.current = roomState;
  latestMoment.current = presenterMoment;

  useEffect(() => {
    if (!hostRef.current) return;
    try {
      const world = new DefenseWorld(hostRef.current);
      worldRef.current = world;
      world.renderState(latestState.current);
      if (latestMoment.current) world.playMoment(latestMoment.current);
      const observer = new ResizeObserver(world.resize);
      observer.observe(hostRef.current);
      return () => { observer.disconnect(); world.dispose(); worldRef.current = null; };
    } catch {
      setUnavailable(true);
    }
  }, []);

  useEffect(() => { worldRef.current?.renderState(roomState); }, [roomState]);
  useEffect(() => { if (presenterMoment) worldRef.current?.playMoment(presenterMoment); }, [presenterMoment]);

  const presenterName = presenterMoment ? roomState?.players.find((player) => player.seat === presenterMoment.seat)?.name : null;
  const sceneDescription = presenterMoment
    ? presenterName === "You" ? "You are presenting your accepted answer in the defense room" : `${presenterName ?? "A teammate"} is presenting their accepted answer in the defense room`
    : "Code-built isometric defense room with four panelists and four standing teammates";
  return <div id="defense-world" ref={hostRef} className="absolute inset-0" role="img" aria-label={sceneDescription}>{unavailable && <div className="scene-unavailable">Room illustration unavailable. The defense controls remain usable.</div>}</div>;
}

import React from "react";
import { Img, useCurrentFrame } from "reelkit/frame";

// Same rule as Staircase's stepPoint: the tread of step n, a little left of its centre.
const stepPoint = (n: number, stepW: number, stepH: number) => ({ x: (n + 0.45) * stepW, y: -n * stepH });

// stride: in the segment that ends at this key, each one-step hop takes this many frames and the
// character stands for the rest of that step's share of the time: a walk, one step per beat when
// the keys are timed to beats. Leave it out for an even, continuous run.
export type ClimbKey = { at: number; step: number; stride?: number };
export type ClimbPose = { from: number; src: string; aspect: number };

export type ClimberProps = {
  // Which step the character is on over time; holds before the first key and after the last.
  path: ClimbKey[];
  // Its picture over time: the last pose whose from has passed (each with width / height).
  poses: ClimbPose[];
  stepW: number;
  stepH: number;
  // Its height in world pixels, and how high each hop arcs (a fraction of stepH).
  height: number;
  hop?: number;
  // Little jumps on the spot (a celebration), each starting at one of these frames.
  jumps?: number[];
  jumpFrames?: number;
};

/** The step the character is on at a frame (fractional while it moves). */
export const climbStep = (path: ClimbKey[], frame: number) => {
  const keys = [...path].sort((a, b) => a.at - b.at);
  if (frame <= keys[0].at) return keys[0].step;
  for (let i = 1; i < keys.length; i++) {
    const a = keys[i - 1];
    const b = keys[i];
    if (frame > b.at) continue;
    const n = b.step - a.step;
    const span = Math.max(1, b.at - a.at);
    if (!b.stride || n <= 0) return a.step + (n * (frame - a.at)) / span;
    const slot = span / n;
    const local = frame - a.at;
    const k = Math.min(n - 1, Math.floor(local / slot));
    return a.step + k + Math.min(1, (local - k * slot) / Math.min(b.stride, slot));
  }
  return keys[keys.length - 1].step;
};

/** The world point under the character's feet at a frame, hop arc included. */
export const climbPoint = (path: ClimbKey[], frame: number, stepW: number, stepH: number, hop = 0.45) => {
  const s = climbStep(path, frame);
  const k = Math.floor(s);
  const frac = s - k;
  const base = stepPoint(k, stepW, stepH);
  const rise = 1 - (1 - frac) * (1 - frac);
  return { x: base.x + frac * stepW, y: base.y - rise * stepH - Math.sin(frac * Math.PI) * hop * stepH };
};

/** A smooth point for a camera to follow: the climb averaged over a short window, without hops,
 * so the camera glides up the stairs instead of bobbing with every step. */
export const climbTrack = (path: ClimbKey[], frame: number, stepW: number, stepH: number, window = 8) => {
  let s = 0;
  for (let d = -window; d <= window; d++) s += climbStep(path, frame + d);
  s /= window * 2 + 1;
  return { x: (s + 0.45) * stepW, y: -s * stepH };
};

// A character sticker that climbs a Staircase: it hops up step by step along a timed path (a run,
// or a walk with one hop per beat), stretches as it takes off and squashes as it lands, switches
// pictures (running, celebrating, thinking) as the path says, can jump on the spot to celebrate,
// and bobs gently while it stands. Its feet are on the tread. Place it inside the same WorldCamera
// as the Staircase.
export const Climber: React.FC<ClimberProps> = ({ path, poses, stepW, stepH, height, hop = 0.45, jumps = [], jumpFrames = 12 }) => {
  const frame = useCurrentFrame();
  const p = climbPoint(path, frame, stepW, stepH, hop);
  const pose = [...poses].sort((a, b) => a.from - b.from).filter((q) => q.from <= frame).pop() ?? poses[0];
  const moved = (f: number) => climbStep(path, f) - climbStep(path, f - 1) > 0.001;
  const moving = moved(frame);

  // A jump on the spot: up and down over jumpFrames, then a squash.
  let jumpY = 0;
  let sinceJump = Infinity;
  for (const j of jumps) {
    const t = (frame - j) / jumpFrames;
    if (t >= 0 && t <= 1) jumpY = Math.sin(t * Math.PI) * height * 0.22;
    if (frame - j - jumpFrames >= 0) sinceJump = Math.min(sinceJump, frame - j - jumpFrames);
  }
  const airborne = moving || jumpY > 0;

  // Frames since the last landing (from a hop or a jump), for the squash.
  let sinceLand = sinceJump;
  if (!moving) {
    for (let d = 1; d <= 6; d++) {
      if (moved(frame - d)) {
        sinceLand = Math.min(sinceLand, d - 1);
        break;
      }
    }
  }
  const squash = !airborne && sinceLand < 6 ? 0.12 * (1 - sinceLand / 6) : 0;
  const sy = airborne ? 1.05 : 1 - squash;
  const sx = airborne ? 0.96 : 1 + squash * 0.7;
  const bob = !airborne && squash === 0 ? Math.sin(frame / 8) * height * 0.012 : 0;
  const w = height * pose.aspect;
  return (
    <div
      style={{
        position: "absolute",
        left: p.x - w / 2,
        top: p.y - height + bob - jumpY,
        width: w,
        height,
        transformOrigin: "50% 100%",
        transform: `scale(${sx}, ${sy})`,
      }}
    >
      <Img src={pose.src} style={{ width: "100%", height: "100%", objectFit: "contain" }} />
    </div>
  );
};

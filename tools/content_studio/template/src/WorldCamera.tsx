import React from "react";
import { interpolate, useCurrentFrame, useVideoConfig } from "reelkit/frame";
import { ease } from "reelkit/kit";

export type WorldPoint = { x: number; y: number };

export type WorldCameraKey = {
  // The frame the camera has arrived (in the clock where the component stands), and how many
  // frames the move into this key takes.
  at: number;
  dur?: number;
  zoom: number;
  // A fixed point of the world to look at, or follow: true to look at the follow() point
  // (plus offset) as it moves.
  x?: number;
  y?: number;
  follow?: boolean;
  offset?: [number, number];
  // After arriving, keep pushing in slowly by this fraction of the zoom per second, so a held
  // shot is never perfectly still; the next move starts from wherever the push has got to.
  drift?: number;
};

export type WorldCameraPunch = { at: number; amount?: number; frames?: number; hold?: number };

export type WorldCameraProps = {
  keys: WorldCameraKey[];
  // The moving point a "follow" key tracks (e.g. a character), given the frame.
  follow?: (frame: number) => WorldPoint;
  punches?: WorldCameraPunch[];
  // Where on screen the looked-at point sits, as fractions of the frame.
  focus?: [number, number];
  children: React.ReactNode;
};

const resolve = (k: WorldCameraKey, frame: number, follow?: (f: number) => WorldPoint): WorldPoint & { zoom: number } => {
  if (k.follow && follow) {
    const p = follow(frame);
    return { x: p.x + (k.offset?.[0] ?? 0), y: p.y + (k.offset?.[1] ?? 0), zoom: k.zoom };
  }
  return { x: k.x ?? 0, y: k.y ?? 0, zoom: k.zoom };
};

/** Where the camera looks and how far it is zoomed at a frame (same rules as the component). */
export const cameraAt = (keys: WorldCameraKey[], frame: number, follow?: (f: number) => WorldPoint, fps = 30) => {
  const sorted = [...keys].sort((a, b) => a.at - b.at);
  const drifted = (k: WorldCameraKey, p: WorldPoint & { zoom: number }) =>
    k.drift && frame > k.at ? { ...p, zoom: p.zoom * (1 + (k.drift * (frame - k.at)) / fps) } : p;
  let cur = drifted(sorted[0], resolve(sorted[0], frame, follow));
  for (let i = 1; i < sorted.length; i++) {
    const k = sorted[i];
    const dur = k.dur ?? 16;
    if (frame < k.at - dur) break;
    const t = interpolate(frame, [k.at - dur, k.at], [0, 1], { easing: ease.inOut, extrapolateLeft: "clamp", extrapolateRight: "clamp" });
    const to = drifted(k, resolve(k, frame, follow));
    // Zoom moves in log space so a big pull-back feels even all the way.
    const z = Math.exp(Math.log(cur.zoom) + (Math.log(to.zoom) - Math.log(cur.zoom)) * t);
    cur = { x: cur.x + (to.x - cur.x) * t, y: cur.y + (to.y - cur.y) * t, zoom: z };
  }
  return cur;
};

// A camera over a large world drawn in world pixels: its children are laid out at world
// coordinates (absolute left/top), and the camera looks at a fixed point or follows a moving
// one, gliding and zooming between keys (zoom eases in log space, so a pull-back from a close-up
// to a whole map stays smooth). Punches are short emphasis zooms. For a long continuous shot over
// a map, a timeline, a staircase or a route, instead of cutting between slides.
export const WorldCamera: React.FC<WorldCameraProps> = ({ keys, follow, punches = [], focus = [0.5, 0.55], children }) => {
  const frame = useCurrentFrame();
  const { width, height, fps } = useVideoConfig();
  const cam = cameraAt(keys, frame, follow, fps);
  let punch = 1;
  for (const p of punches) {
    const frames = p.frames ?? 6;
    const hold = p.hold ?? 8;
    const up = interpolate(frame, [p.at, p.at + frames], [0, 1], { easing: ease.out, extrapolateLeft: "clamp", extrapolateRight: "clamp" });
    const down = interpolate(frame, [p.at + frames + hold, p.at + frames + hold + 12], [0, 1], { easing: ease.inOut, extrapolateLeft: "clamp", extrapolateRight: "clamp" });
    punch *= 1 + (p.amount ?? 0.1) * (up - down);
  }
  const z = cam.zoom * punch;
  return (
    <div style={{ position: "absolute", inset: 0, overflow: "hidden" }}>
      <div
        style={{
          position: "absolute",
          left: 0,
          top: 0,
          width: 1,
          height: 1,
          overflow: "visible",
          transformOrigin: "0 0",
          transform: `translate(${width * focus[0]}px, ${height * focus[1]}px) scale(${z}) translate(${-cam.x}px, ${-cam.y}px)`,
        }}
      >
        {children}
      </div>
    </div>
  );
};

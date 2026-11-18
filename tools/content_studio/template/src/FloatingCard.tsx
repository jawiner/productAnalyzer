import React from "react";
import { Img, interpolate, spring, useCurrentFrame, useVideoConfig } from "reelkit/frame";
import { springs } from "reelkit/kit";

export type FloatingCardProps = {
  // A real screen cut out on transparent (urls[...]); its own aspect is kept.
  src: string;
  // Width as a fraction of the frame width, and the picture's height over its width.
  width?: number;
  aspect: number;
  // It rises in from below with a small turn and settles at delay; it then floats gently.
  delay?: number;
  shadow?: string;
  // A small tag pinned to its top-left corner (e.g. "Example"), drawn by the caller.
  tag?: React.ReactNode;
};

/** The frame (in its own clock) the card has settled. */
export const floatingCardSettle = (delay = 0) => delay + 22;

// A real product screen, cut out, lifted off the page: it rises in, turns flat and settles with a
// soft shadow, then floats a pixel or two so the shot never freezes. For the one moment a film
// shows the actual product (a card, a dialog, a receipt) with its own pixels, never redrawn.
export const FloatingCard: React.FC<FloatingCardProps> = ({ src, width = 0.56, aspect, delay = 0, shadow = "rgba(30, 20, 10, 0.28)", tag }) => {
  const frame = useCurrentFrame();
  const { width: W, fps } = useVideoConfig();
  const s = spring({ frame: frame - delay, fps, config: springs.smooth });
  const w = W * width;
  const float = Math.sin((frame - delay) / 22) * W * 0.003;
  const o = interpolate(frame - delay, [0, 6], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <div
      style={{
        position: "relative",
        width: w,
        height: w * aspect,
        opacity: o,
        transform: `translateY(${(1 - s) * W * 0.28 + float}px) rotate(${(1 - s) * 7}deg) scale(${0.9 + 0.1 * s})`,
        filter: `drop-shadow(0 ${W * 0.025}px ${W * 0.035}px ${shadow})`,
      }}
    >
      <Img src={src} style={{ width: "100%", height: "100%", objectFit: "contain" }} />
      {tag ? <div style={{ position: "absolute", left: -W * 0.02, top: w * aspect * 0.2 }}>{tag}</div> : null}
    </div>
  );
};

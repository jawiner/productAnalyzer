import React from "react";
import { spring, useCurrentFrame, useVideoConfig } from "reelkit/frame";

export type TextDropProps = {
  text: string;
  color: string;
  font: string;
  // Font size as a fraction of the frame width.
  size: number;
  // It pops in at `at`. At dropAt it wobbles loose, hops up a little and falls out of the
  // frame, turning as it goes (leave dropAt out for words that stay).
  at: number;
  dropAt?: number;
  // Which way it tips as it falls: 1 clockwise, -1 counter-clockwise.
  dir?: 1 | -1;
  // A halo in this colour round the letters (the ground colour), so something passing behind
  // the words never muddles them.
  halo?: string;
};

// A line of heavy display words that pops onto the frame and can later come loose and fall off
// the bottom, like a sticker peeling off: for words that get dropped, cut or forgotten (a
// condition the quote lost, a feature removed, a promise broken).
export const TextDrop: React.FC<TextDropProps> = ({ text, color, font, size, at, dropAt, dir = 1, halo }) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  if (frame < at) return null;
  const fs = width * size;
  const pop = spring({ frame: frame - at, fps, config: { stiffness: 260, damping: 14 } });
  let x = 0;
  let y = 0;
  let r = 0;
  if (dropAt !== undefined) {
    const before = dropAt - frame;
    if (before > 0 && before <= 6) r = Math.sin(before * 2.4) * 3 * dir;
    const t = frame - dropAt;
    if (t > 0) {
      y = -16 * t + 2.4 * t * t;
      x = dir * 4 * t;
      r = dir * (2.5 * t + 0.09 * t * t);
    }
    if (y > height * 1.2) return null;
  }
  const hr = fs * 0.07;
  const shadow = halo
    ? Array.from({ length: 12 }, (_, i) => `${(Math.cos((i / 12) * Math.PI * 2) * hr).toFixed(1)}px ${(Math.sin((i / 12) * Math.PI * 2) * hr).toFixed(1)}px 0 ${halo}`).join(", ")
    : undefined;
  return (
    <div
      style={{
        textShadow: shadow,
        fontFamily: font,
        fontSize: fs,
        lineHeight: 1,
        color,
        whiteSpace: "nowrap",
        letterSpacing: fs * 0.01,
        transform: `translate(${x}px, ${y}px) rotate(${r}deg) scale(${0.5 + 0.5 * pop})`,
        opacity: Math.min(1, pop * 2),
      }}
    >
      {text}
    </div>
  );
};

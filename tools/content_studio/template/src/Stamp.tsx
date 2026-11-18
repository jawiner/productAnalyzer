import React from "react";
import { interpolate, useCurrentFrame, useVideoConfig } from "reelkit/frame";
import { ease } from "reelkit/kit";

export type StampProps = {
  text: string;
  color: string;
  font: string;
  // Font size as a fraction of the frame width, and the stamp's tilt in degrees.
  size?: number;
  rotate?: number;
  // It slams down at `at`: big and transparent, then hard onto the page with a small shake.
  at?: number;
};

/** The frame (in its own clock) the stamp hits the page. */
export const stampHit = (at = 0) => at + 5;

// A rubber stamp that slams onto the frame: outlined capitals in a rough double border, coming
// down from large and settling with a short shake. For a verdict on a claim: WRONG, MYTH,
// APPROVED, SOLD OUT.
export const Stamp: React.FC<StampProps> = ({ text, color, font, size = 0.14, rotate = -8, at = 0 }) => {
  const frame = useCurrentFrame();
  const { width } = useVideoConfig();
  const fs = width * size;
  const t = interpolate(frame, [at, at + 5], [0, 1], { easing: ease.in, extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const shake = frame >= at + 5 && frame < at + 11 ? Math.sin((frame - at) * 2.6) * fs * 0.03 * (1 - (frame - at - 5) / 6) : 0;
  if (frame < at) return null;
  return (
    <div
      style={{
        display: "inline-block",
        padding: `${fs * 0.08}px ${fs * 0.28}px`,
        border: `${fs * 0.08}px solid ${color}`,
        outline: `${fs * 0.03}px solid ${color}`,
        outlineOffset: fs * 0.05,
        borderRadius: fs * 0.12,
        color,
        fontFamily: font,
        fontSize: fs,
        lineHeight: 1,
        letterSpacing: fs * 0.04,
        opacity: 0.35 + 0.65 * t,
        transform: `translate(${shake}px, 0) rotate(${rotate}deg) scale(${1.3 - 0.3 * t})`,
        whiteSpace: "nowrap",
        background: "rgba(255,253,249,0.9)",
      }}
    >
      {text}
    </div>
  );
};

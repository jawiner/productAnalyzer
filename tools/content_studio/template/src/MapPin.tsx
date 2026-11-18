import React from "react";
import { spring, useCurrentFrame, useVideoConfig } from "reelkit/frame";
import { springs } from "reelkit/kit";

export type MapPinProps = {
  // The world point the pin's tip touches.
  x: number;
  y: number;
  label: string;
  // Label size in world pixels: size it for how far the camera is when the pin is seen.
  size: number;
  bg: string;
  ink: string;
  font: string;
  // It drops in at `at` (leave out to be there from the start) and shrinks away at outAt.
  at?: number;
  outAt?: number;
};

// A pin that drops onto a point of a drawn world with a short label in a rounded tag: a place,
// a day, a record. Sized in world pixels, so a pin meant to be read from far away is drawn huge.
export const MapPin: React.FC<MapPinProps> = ({ x, y, label, size, bg, ink, font, at, outAt }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const inS = at === undefined ? 1 : spring({ frame: frame - at, fps, config: springs.snappy });
  const outS = outAt === undefined ? 0 : Math.min(1, Math.max(0, (frame - outAt) / 8));
  const s = inS * (1 - outS);
  if ((at !== undefined && frame < at) || (outAt !== undefined && frame >= outAt + 8)) return null;
  return (
    <div style={{ position: "absolute", left: x, top: y, width: 0, height: 0 }}>
      <div style={{ position: "absolute", left: 0, top: 0, transform: `translate(-50%, -100%) translateY(${(1 - s) * -size * 1.2}px) scale(${0.6 + 0.4 * s})`, transformOrigin: "50% 100%", opacity: Math.min(1, s * 1.5), display: "flex", flexDirection: "column", alignItems: "center" }}>
        <div style={{ background: bg, color: ink, fontFamily: font, fontSize: size, lineHeight: 1, padding: `${size * 0.28}px ${size * 0.5}px`, borderRadius: size * 0.4, whiteSpace: "nowrap" }}>{label}</div>
        <div style={{ width: 0, height: 0, borderLeft: `${size * 0.3}px solid transparent`, borderRight: `${size * 0.3}px solid transparent`, borderTop: `${size * 0.5}px solid ${bg}` }} />
      </div>
    </div>
  );
};

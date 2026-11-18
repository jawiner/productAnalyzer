import React from "react";
import { useVideoConfig } from "reelkit/frame";

export type LabelChipProps = {
  text: string;
  bg: string;
  ink: string;
  font: string;
  // Font size as a fraction of the frame width.
  size?: number;
  // An outline instead of a filled pill.
  outline?: boolean;
};

// A small spaced-capitals label on a pill: a source, a date, a category, an "Example" tag on a
// real screen. Static; bring it in with the kit's Entrance.
export const LabelChip: React.FC<LabelChipProps> = ({ text, bg, ink, font, size = 0.034, outline = false }) => {
  const { width } = useVideoConfig();
  const fs = width * size;
  return (
    <div
      style={{
        display: "inline-flex",
        alignItems: "center",
        padding: `${fs * 0.5}px ${fs * 0.95}px`,
        borderRadius: fs * 2,
        background: outline ? "transparent" : bg,
        border: outline ? `${Math.max(2, fs * 0.09)}px solid ${bg}` : "none",
        color: ink,
        fontFamily: font,
        fontSize: fs,
        fontWeight: 800,
        letterSpacing: fs * 0.14,
        textTransform: "uppercase",
        whiteSpace: "nowrap",
      }}
    >
      {text}
    </div>
  );
};

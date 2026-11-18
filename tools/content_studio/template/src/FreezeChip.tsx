import React from "react";
import { useVideoConfig } from "reelkit/frame";

export type FreezeChipProps = {
  label: string;
  bg: string;
  ink: string;
  font: string;
  // Font size as a fraction of the frame width.
  size?: number;
};

// A rounded chip with a drawn snowflake glyph and a short label: a streak freeze, a pause, a
// "frozen" state. Static; bring it in with the kit's Entrance.
export const FreezeChip: React.FC<FreezeChipProps> = ({ label, bg, ink, font, size = 0.042 }) => {
  const { width } = useVideoConfig();
  const fs = width * size;
  const arm = (deg: number) => (
    <g key={deg} transform={`rotate(${deg} 12 12)`}>
      <line x1="12" y1="2.5" x2="12" y2="21.5" />
      <polyline points="9,5 12,8 15,5" />
      <polyline points="9,19 12,16 15,19" />
    </g>
  );
  return (
    <div style={{ display: "inline-flex", alignItems: "center", gap: fs * 0.45, padding: `${fs * 0.5}px ${fs * 0.85}px ${fs * 0.5}px ${fs * 0.6}px`, borderRadius: fs * 2, background: bg, color: ink, fontFamily: font, fontSize: fs, whiteSpace: "nowrap" }}>
      <svg viewBox="0 0 24 24" width={fs * 1.25} height={fs * 1.25} fill="none" stroke={ink} strokeWidth={2.2} strokeLinecap="round" strokeLinejoin="round">
        {[0, 60, 120].map(arm)}
      </svg>
      {label}
    </div>
  );
};

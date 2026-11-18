import React from "react";
import { useVideoConfig } from "reelkit/frame";

export type PlaceProps = {
  // Where the centre of the content sits, as fractions of the frame.
  x?: number;
  y: number;
  // Width of the box the content is laid out in, as a fraction of the frame width.
  width?: number;
  style?: React.CSSProperties;
  children: React.ReactNode;
};

// Puts one piece of a layout at a point of the frame, centred on it, so a scene can be laid out
// in fractions of the frame (and so stays right at any aspect). Use for every element a scene
// positions by hand: a label, a chart, a card, a character.
export const Place: React.FC<PlaceProps> = ({ x = 0.5, y, width = 1, style, children }) => {
  const { width: W, height: H } = useVideoConfig();
  return (
    <div
      style={{
        position: "absolute",
        left: W * x,
        top: H * y,
        width: W * width,
        transform: "translate(-50%, -50%)",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        ...style,
      }}
    >
      {children}
    </div>
  );
};

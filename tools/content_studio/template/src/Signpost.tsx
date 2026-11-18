import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "reelkit/frame";
import { ease, springs } from "reelkit/kit";

export type SignpostProps = {
  // The world point the post stands on (its foot).
  x: number;
  y: number;
  // The board's text, set heavy.
  text: string;
  // A smaller second line under it (optional).
  sub?: string;
  font: string;
  subFont?: string;
  ink: string;
  board: string;
  edge: string;
  hero: string;
  // Sizes in world pixels.
  fontSize: number;
  postHeight?: number;
  // The board springs up at appearAt (leave out to be there from the start).
  appearAt?: number;
  // Words written in above the text with an editor's caret at insertAt (a correction the
  // original left out), a hand-drawn circle round them at circleAt, and a strike through the
  // board's text at strikeAt.
  insert?: string;
  insertAt?: number;
  circleAt?: number;
  strikeAt?: number;
  // Overall opacity, for stepping the sign out of a shot that needs the space.
  opacity?: number;
};

// A signpost standing in a drawn world: a post and a board with a short claim on it. It can pop
// up, have the words the claim left out written in with a caret, get those words circled, and
// finally be struck through. For a milestone, a myth on the way, a "you are here".
export const Signpost: React.FC<SignpostProps> = ({
  x, y, text, sub, font, subFont, ink, board, edge, hero, fontSize, postHeight, appearAt, insert, insertAt, circleAt, strikeAt, opacity = 1,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
  const up = appearAt === undefined ? 1 : spring({ frame: frame - appearAt, fps, config: springs.snappy });
  const ins = insertAt === undefined ? 0 : interpolate(frame, [insertAt, insertAt + 8], [0, 1], { easing: ease.out, ...clamp });
  const circ = circleAt === undefined ? 0 : interpolate(frame, [circleAt, circleAt + 12], [0, 1], { easing: ease.inOut, ...clamp });
  const strike = strikeAt === undefined ? 0 : interpolate(frame, [strikeAt, strikeAt + 8], [0, 1], { easing: ease.out, ...clamp });
  const post = postHeight ?? fontSize * 2.6;
  const pad = fontSize * 0.42;
  return (
    <div style={{ position: "absolute", left: x, top: y, width: 0, height: 0, opacity: appearAt === undefined || frame >= appearAt ? opacity : 0 }}>
      <div style={{ position: "absolute", left: -fontSize * 0.07, top: -post, width: fontSize * 0.14, height: post, background: edge, borderRadius: fontSize * 0.05, transformOrigin: "50% 100%", transform: `scaleY(${up})` }} />
      <div
        style={{
          position: "absolute",
          left: 0,
          top: -post,
          transform: `translate(-50%, -100%) scale(${up})`,
          transformOrigin: "50% 100%",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
        }}
      >
        {insert ? (
          <div style={{ position: "relative", marginBottom: fontSize * 0.05, opacity: ins, transform: `translateY(${(1 - ins) * fontSize * 0.3}px)` }}>
            <div style={{ fontFamily: font, fontSize: fontSize * 0.62, color: hero, whiteSpace: "nowrap", transform: "rotate(-4deg)", padding: `0 ${fontSize * 0.1}px` }}>{insert}</div>
            <svg viewBox="0 0 200 80" preserveAspectRatio="none" style={{ position: "absolute", left: "-14%", top: "-30%", width: "128%", height: "160%", overflow: "visible" }}>
              <path d="M120 6 C 60 2, 8 14, 6 40 C 4 66, 70 78, 120 74 C 176 70, 198 52, 194 34 C 190 14, 150 4, 96 8" fill="none" stroke={hero} strokeWidth={5} strokeLinecap="round" pathLength={100} strokeDasharray={100} strokeDashoffset={100 * (1 - circ)} opacity={circ > 0 ? 1 : 0} />
            </svg>
          </div>
        ) : null}
        <div style={{ position: "relative", background: board, border: `${fontSize * 0.09}px solid ${edge}`, borderRadius: fontSize * 0.22, padding: `${pad * 0.7}px ${pad * 1.4}px ${pad * 0.6}px`, display: "flex", flexDirection: "column", alignItems: "center" }}>
          {insert ? (
            <div style={{ position: "absolute", left: fontSize * 0.55, top: -fontSize * 0.2, width: 0, height: 0, borderLeft: `${fontSize * 0.16}px solid transparent`, borderRight: `${fontSize * 0.16}px solid transparent`, borderBottom: `${fontSize * 0.3}px solid ${hero}`, opacity: ins }} />
          ) : null}
          <div style={{ position: "relative", fontFamily: font, fontSize, color: ink, lineHeight: 1, whiteSpace: "nowrap" }}>
            {text}
            <div style={{ position: "absolute", left: "-6%", top: "46%", width: "112%", height: fontSize * 0.13, borderRadius: fontSize, background: hero, transformOrigin: "0 50%", transform: `rotate(-8deg) scaleX(${strike})`, opacity: strike > 0 ? 1 : 0 }} />
          </div>
          {sub ? <div style={{ marginTop: fontSize * 0.12, fontFamily: subFont ?? font, fontSize: fontSize * 0.34, letterSpacing: fontSize * 0.04, color: ink, opacity: 0.7, whiteSpace: "nowrap", textTransform: "uppercase" }}>{sub}</div> : null}
        </div>
      </div>
    </div>
  );
};

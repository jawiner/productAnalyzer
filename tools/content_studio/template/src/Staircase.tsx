import React from "react";

export type StaircaseProps = {
  // Steps 1..count rise up and to the right: step n's tread runs from x = n * stepW to
  // (n + 1) * stepW at height y = -n * stepH (world pixels; y grows downward).
  count: number;
  stepW: number;
  stepH: number;
  color: string;
  // Steps above paleFrom fade toward pale by paleAmount (0 to 1): how much of the way is done.
  pale?: string;
  paleFrom?: number;
  paleAmount?: number;
  // Steps drawn as a missing tread: a dashed outline instead of a solid block (a missed day).
  hollow?: number[];
  hollowColor?: string;
  // The step's number on its face: every step up to numberUpTo, then every numberEvery.
  numberColor?: string;
  font?: string;
  numberUpTo?: number;
  numberEvery?: number;
  // A light edge along each tread.
  tread?: string;
  // How far below the floor (y = 0) the solid mass goes.
  depth?: number;
};

/** The world point a step's tread centre sits at (its top surface, a little left of centre). */
export const stepPoint = (n: number, stepW: number, stepH: number) => ({ x: (n + 0.45) * stepW, y: -n * stepH });

const mix = (a: string, b: string, t: number) => {
  const p = (h: string) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16));
  const [x, y] = [p(a), p(b)];
  return `rgb(${x.map((v, i) => Math.round(v + (y[i] - v) * t)).join(",")})`;
};

// A side-view staircase drawn in world pixels, one solid column per step with its number on
// its face, for a "day by day" or "level by level" journey a character climbs. Steps can fade
// pale above a point (progress) and single steps can be drawn hollow (a gap, a missed day).
// Place it inside a WorldCamera; it draws thousands of pixels wide and is meant to be flown over.
export const Staircase: React.FC<StaircaseProps> = ({
  count, stepW, stepH, color, pale = "#C9D4FA", paleFrom = Infinity, paleAmount = 0, hollow = [], hollowColor = "#FF5A1F",
  numberColor = "#FFFDF9", font, numberUpTo = 80, numberEvery = 10, tread = "rgba(255,255,255,0.32)", depth = 900,
}) => {
  const cols = [];
  for (let n = 1; n <= count; n++) {
    const x = n * stepW;
    const top = -n * stepH;
    const fill = n > paleFrom && paleAmount > 0 && color.startsWith("#") ? mix(color, pale, paleAmount) : color;
    const isHollow = hollow.includes(n);
    const showNumber = n <= numberUpTo || n % numberEvery === 0;
    cols.push(
      <g key={n}>
        <rect x={x} y={isHollow ? top + stepH : top} width={stepW + 0.5} height={(isHollow ? depth - stepH : depth) + n * stepH} fill={fill} />
        {isHollow ? (
          <rect x={x + stepW * 0.04} y={top + stepH * 0.04} width={stepW * 0.92} height={stepH * 0.92} fill="none" stroke={hollowColor} strokeWidth={stepH * 0.07} strokeDasharray={`${stepH * 0.22} ${stepH * 0.14}`} rx={stepH * 0.08} />
        ) : (
          <rect x={x} y={top} width={stepW} height={Math.max(4, stepH * 0.07)} fill={tread} />
        )}
        {showNumber && !isHollow ? (
          <text x={x + stepW * 0.5} y={top + stepH * 0.68} textAnchor="middle" fontFamily={font} fontSize={n > numberUpTo ? stepH * 0.9 : stepH * 0.42} fill={numberColor} opacity={0.92}>
            {n}
          </text>
        ) : null}
      </g>,
    );
  }
  return (
    <svg width={1} height={1} style={{ position: "absolute", left: 0, top: 0, overflow: "visible" }}>
      {cols}
    </svg>
  );
};

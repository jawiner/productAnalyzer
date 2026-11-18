import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "reelkit/frame";
import { ease } from "reelkit/kit";

export type MirrorFaceProps = {
  // Height as a fraction of the frame height (the width follows, 2:3).
  height: number;
  // It pops in at `at`; at revealAt the bandage peels off and flies away and the face smiles.
  at: number;
  revealAt: number;
  ink: string;
  hero: string;
  accent: string;
  paper: string;
  glass?: string;
  skin?: string;
};

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

// A hand mirror held up in the frame with a face in it: bandaged over the nose at first (just
// after surgery), then the bandage peels off and flies out, the eyes close happily, the mouth
// turns to a smile and it sparkles. For "getting used to a new face", a makeover, a before and
// after. Flat sticker style: thick ink outlines, brand colours for frame and shirt.
export const MirrorFace: React.FC<MirrorFaceProps> = ({
  height, at, revealAt, ink, hero, accent, paper, glass = "#DCE5FF", skin = "#F4BE98",
}) => {
  const frame = useCurrentFrame();
  const { fps, height: H } = useVideoConfig();
  if (frame < at) return null;
  const h = H * height;
  const w = (h * 200) / 300;
  const pop = spring({ frame: frame - at, fps, config: { stiffness: 260, damping: 14 } });
  const sway = Math.sin((frame - at) / 18) * 2.5;
  const peel = interpolate(frame, [revealAt, revealAt + 12], [0, 1], { easing: ease.in, ...clamp });
  const smile = interpolate(frame, [revealAt + 3, revealAt + 11], [0, 1], { easing: ease.out, ...clamp });
  const spark = (delay: number) => {
    const t = interpolate(frame, [revealAt + 6 + delay, revealAt + 22 + delay], [0, 1], clamp);
    return t <= 0 || t >= 1 ? 0 : Math.sin(t * Math.PI);
  };
  const star = (x: number, y: number, r: number, s: number, color: string) =>
    s > 0 ? (
      <path
        d={`M${x} ${y - r} Q${x} ${y} ${x + r} ${y} Q${x} ${y} ${x} ${y + r} Q${x} ${y} ${x - r} ${y} Q${x} ${y} ${x} ${y - r} Z`}
        fill={color}
        stroke={ink}
        strokeWidth={2.5}
        strokeLinejoin="round"
        transform={`translate(${x} ${y}) scale(${s}) translate(${-x} ${-y})`}
      />
    ) : null;
  // The mouth: a flat, unsure line that bends into a smile.
  const my = 147 - 4 * smile;
  const mc = 145 + 18 * smile;
  return (
    <div
      style={{
        width: w,
        height: h,
        transformOrigin: "50% 85%",
        transform: `scale(${0.4 + 0.6 * pop}) rotate(${(1 - pop) * -14 + sway}deg)`,
        opacity: Math.min(1, pop * 2),
        filter: "drop-shadow(0 18px 24px rgba(23,19,15,0.16))",
      }}
    >
      <svg viewBox="0 0 200 300" width={w} height={h} style={{ overflow: "visible" }}>
        <defs>
          <clipPath id="mirror-glass">
            <ellipse cx={100} cy={104} rx={78} ry={84} />
          </clipPath>
        </defs>
        <rect x={88} y={192} width={24} height={100} rx={12} fill={ink} />
        <rect x={84} y={204} width={32} height={14} rx={6} fill={hero} stroke={ink} strokeWidth={3} />
        <ellipse cx={100} cy={104} rx={94} ry={100} fill={hero} stroke={ink} strokeWidth={6} />
        <ellipse cx={100} cy={104} rx={78} ry={84} fill={glass} stroke={ink} strokeWidth={4} />
        <g clipPath="url(#mirror-glass)">
          <ellipse cx={100} cy={206} rx={62} ry={34} fill={accent} stroke={ink} strokeWidth={4} />
          <rect x={86} y={150} width={28} height={44} fill={skin} stroke={ink} strokeWidth={4} />
          <circle cx={57} cy={116} r={10} fill={skin} stroke={ink} strokeWidth={4} />
          <circle cx={143} cy={116} r={10} fill={skin} stroke={ink} strokeWidth={4} />
          <ellipse cx={100} cy={114} rx={44} ry={50} fill={skin} stroke={ink} strokeWidth={4} />
          <path d="M55 106 C 54 58, 146 58, 145 106 C 136 84, 118 78, 100 84 C 82 78, 64 84, 55 106 Z" fill={ink} />
          {smile < 0.5 ? (
            <>
              <ellipse cx={83} cy={112} rx={4.5} ry={5.5} fill={ink} />
              <ellipse cx={117} cy={112} rx={4.5} ry={5.5} fill={ink} />
            </>
          ) : (
            <>
              <path d="M76 114 Q83 105 90 114" fill="none" stroke={ink} strokeWidth={4} strokeLinecap="round" />
              <path d="M110 114 Q117 105 124 114" fill="none" stroke={ink} strokeWidth={4} strokeLinecap="round" />
            </>
          )}
          <path d="M100 116 Q106 127 98 131" fill="none" stroke={ink} strokeWidth={3.5} strokeLinecap="round" />
          <circle cx={73} cy={134} r={8} fill={hero} opacity={0.35 * smile} />
          <circle cx={127} cy={134} r={8} fill={hero} opacity={0.35 * smile} />
          <path d={`M84 ${my} Q100 ${mc} 116 ${my}`} fill="none" stroke={ink} strokeWidth={4} strokeLinecap="round" />
          <path d="M46 70 Q54 44 80 32" fill="none" stroke="#FFFFFF" strokeWidth={8} strokeLinecap="round" opacity={0.75} />
        </g>
        {peel < 1 ? (
          <g
            transform={`translate(${100 + peel * 70} ${124 - peel * 120}) rotate(${peel * 70})`}
            opacity={1 - peel * peel}
          >
            {[-32, 32].map((r) => (
              <g key={r} transform={`rotate(${r})`}>
                <rect x={-30} y={-8} width={60} height={16} rx={7} fill={paper} stroke={ink} strokeWidth={3} />
                <rect x={-8} y={-6} width={16} height={12} rx={3} fill="#F2E4CF" />
              </g>
            ))}
          </g>
        ) : null}
        {star(28, 40, 16, spark(0), hero)}
        {star(176, 70, 12, spark(4), accent)}
        {star(166, 176, 14, spark(8), hero)}
      </svg>
    </div>
  );
};

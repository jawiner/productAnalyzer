import React from "react";
import { Img, interpolate, spring, useCurrentFrame, useVideoConfig } from "reelkit/frame";
import { springs } from "reelkit/kit";

export type StickerCharacterProps = {
  // The character's picture, cut out on transparent (urls[...]).
  src: string;
  // Height as a fraction of the frame height; the picture's width over its height.
  height?: number;
  aspect?: number;
  // It pops up from below the frame edge at delay and then bobs gently.
  delay?: number;
  // Turn the picture to face the other way.
  flip?: boolean;
  // Leaves (drops back down) at exitAt, if given.
  exitAt?: number;
};

// A mascot or character sticker that hops up into the shot with a squash-and-settle and then
// bobs, so a faceless film has someone in it. For an app mascot greeting, pointing or reacting.
export const StickerCharacter: React.FC<StickerCharacterProps> = ({ src, height = 0.2, aspect = 1, delay = 0, flip = false, exitAt }) => {
  const frame = useCurrentFrame();
  const { height: H, fps } = useVideoConfig();
  const h = H * height;
  const up = spring({ frame: frame - delay, fps, config: springs.snappy });
  const out = exitAt === undefined ? 0 : interpolate(frame, [exitAt, exitAt + 9], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const bob = Math.sin((frame - delay) / 9) * h * 0.012;
  const squash = 1 + Math.max(0, Math.sin(Math.min(1, (frame - delay) / 10) * Math.PI)) * 0.06;
  return (
    <div
      style={{
        width: h * aspect,
        height: h,
        transformOrigin: "50% 100%",
        transform: `translateY(${(1 - up) * h * 0.9 + out * h + bob}px) scale(${flip ? -1 : 1}, ${1 / squash}) scaleX(${squash})`,
        opacity: frame < delay ? 0 : 1 - out,
      }}
    >
      <Img src={src} style={{ width: "100%", height: "100%", objectFit: "contain" }} />
    </div>
  );
};

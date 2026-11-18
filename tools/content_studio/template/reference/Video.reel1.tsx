import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "reelkit/frame";
import {
  Captions, Entrance, font, fonts, Grain, Headline, Music, onWord, SceneFrame, sceneById, Sfx, Voiceover, wordFrame,
} from "reelkit/kit";
import type { VideoProps } from "reelkit/kit";
import { Climber, climbStep, climbTrack } from "./Climber";
import type { ClimbKey } from "./Climber";
import { FloatingCard } from "./FloatingCard";
import { FreezeChip } from "./FreezeChip";
import { LabelChip } from "./LabelChip";
import { MapPin } from "./MapPin";
import { MirrorFace } from "./MirrorFace";
import { Place } from "./Place";
import { Signpost } from "./Signpost";
import { Staircase, stepPoint } from "./Staircase";
import { Stamp } from "./Stamp";
import { StickerCharacter } from "./StickerCharacter";
import { TextDrop } from "./TextDrop";
import { WorldCamera } from "./WorldCamera";

// LifeMaxer's Daylight look: warm paper, near-black ink, tangerine hero, cobalt staircase
// (the blue of Steppy's sneakers and of the steps in the app's own Day 66 card).
const palette = { bg: "#F6F0E6", paper: "#FFFDF9", ink: "#17130F", hero: "#FF5A1F", accent: "#1F4FE6", pale: "#C9D4FA", track: "#E6DDCF" };
const display = font("archivoBlack");
const body = fonts.body;

// The world: one step is one day. Step n's tread sits at x = n * W, y = -n * H (world pixels).
const W = 150;
const H = 110;
const STEPS = 260;
const MISSED = 52;
const STEPPY_H = 240;
// One hop per beat of the music while Steppy walks (110 bpm at 30 fps), each hop this many frames.
const BEAT = (30 * 60) / 110;
const STRIDE = 9;

const POSE = {
  run: { src: "assets/user/a-d616071c-steppy-run.webp", aspect: 560 / 546 },
  celebrate: { src: "assets/user/a-3da24598-steppy-celebrate.webp", aspect: 476 / 560 },
  think: { src: "assets/user/a-1909f07b-steppy-think.webp", aspect: 371 / 560 },
  trophy: { src: "assets/user/a-e8f10eaf-steppy-trophy.webp", aspect: 303 / 560 },
};
const STEPPY_POINT = "assets/user/a-714645f9-steppy-point.webp";
const CARD_66 = "assets/user/a-d9bf09ef-milestone-66-card.png";
const MUSIC = "assets/lib/music-tutorial-pulse/track.mp3";
const POP = "assets/lib/sfx-ui-bubble-pop/clip.mp3";
const IMPACT = "assets/lib/sfx-ui-soft-impact/clip.mp3";
const TICKS = "assets/lib/sfx-ui-count-ticks/clip.mp3";
const WHOOSH = "assets/lib/sfx-ui-soft-whoosh/clip.mp3";
const CHIME = "assets/lib/sfx-ui-success-chime/clip.mp3";

export const Video: React.FC<VideoProps> = ({ manifest, urls }) => {
  const frame = useCurrentFrame();
  const hook = sceneById(manifest, "hook");
  const origin = sceneById(manifest, "origin");
  const study = sceneById(manifest, "study");
  const miss = sceneById(manifest, "miss");
  const turn = sceneById(manifest, "turn");
  const app = sceneById(manifest, "app");
  const cta = sceneById(manifest, "cta");
  type Scene = typeof hook;
  // Absolute frames of spoken words, for everything that lives in the world across scenes.
  const at = (s: Scene, word: string, nth?: number) => wordFrame(s, word, { absolute: true, nth });

  // Steppy never waits long: running on frame 1, on step 21 as "21" is said, a beat to think
  // after "wrong", then he keeps climbing one step per beat (landing on the beat) through the
  // whole origin story, and breaks into a run in the study, landing on 66 as "66" is said. On the
  // summit he jumps for joy every other beat.
  const beats = manifest.music?.beatFrames ?? [];
  const arrive21 = at(hook, "21");
  const firstBeat = beats.find((b) => b >= at(hook, "wrong") + 16) ?? at(hook, "wrong") + 24;
  const walkStart = firstBeat - STRIDE;
  const climbStart = at(study, "researchers");
  const arrive66 = at(study, "66");
  const walkSteps = Math.floor((climbStart - walkStart) / BEAT);
  const path: ClimbKey[] = [
    { at: 0, step: 2 },
    { at: arrive21, step: 21 },
    { at: walkStart, step: 21 },
    { at: walkStart + walkSteps * BEAT, step: 21 + walkSteps, stride: STRIDE },
    { at: arrive66, step: 66 },
  ];
  const poses = [
    { from: 0, ...POSE.run },
    { from: arrive21, ...POSE.celebrate },
    { from: at(hook, "wrong"), ...POSE.think },
    { from: walkStart, ...POSE.run },
    { from: arrive66, ...POSE.trophy },
  ];
  const jumps = beats.filter((b) => b > arrive66 + 30).filter((_, i) => i % 2 === 0).map((b) => b - 6);
  // The camera follows a smoothed track (no bob with each hop).
  const steppy = (f: number) => climbTrack(path, f, W, H);
  const dayNow = Math.max(1, Math.round(climbStep(path, frame)));

  // Camera: follow the run, pull up on "wrong", close on the sign, follow the climb, land on 66,
  // pull back for 18 and all the way out for 254, then the missed day, day 22, a third, the
  // summit, and back to the 21 sign to strike it.
  const fit = (steps: number) => (1080 * 0.88) / ((steps + 2) * W);
  const sign21 = { x: (21 + 0.78) * W, y: -21 * H };
  const cameraKeys = [
    { at: 0, zoom: 1.25, follow: true, offset: [W * 1.0, -H * 1.7] as [number, number] },
    { at: at(hook, "wrong") + 18, dur: 22, zoom: 0.42, x: 26 * W, y: -26 * H - 300 },
    // Follow the walk with Steppy low on the left, leaving the sky above him for the story.
    { at: origin.startFrame + 44, dur: 26, zoom: 0.85, follow: true, offset: [254, -294] as [number, number], drift: 0.008 },
    { at: climbStart + 10, dur: 16, zoom: 0.72, follow: true, offset: [W * 1.4, -H * 1.5] as [number, number] },
    { at: arrive66 + 4, dur: 12, zoom: 0.8, x: 66.6 * W, y: -66 * H - 260, drift: 0.02 },
    { at: at(study, "18") + 2, dur: 14, zoom: fit(66), x: 34 * W, y: -34 * H },
    // Room for the 254 pin's label, which reaches far right of the top step.
    { at: at(study, "254") + 4, dur: 18, zoom: fit(298), x: 140 * W, y: -128 * H, drift: 0.015 },
    { at: miss.startFrame + 12, dur: 18, zoom: 0.28, x: 58 * W, y: -58 * H - 120, drift: 0.02 },
    { at: turn.startFrame + 10, dur: 16, zoom: 0.85, x: 22.6 * W, y: -22 * H - 160, drift: 0.02 },
    { at: at(turn, "third") + 2, dur: 18, zoom: fit(66), x: 34 * W, y: -34 * H, drift: 0.012 },
    { at: app.startFrame + 12, dur: 16, zoom: 0.55, x: 66.6 * W, y: -66 * H - 300, drift: 0.012 },
    { at: cta.startFrame + 8, dur: 14, zoom: 1.0, x: sign21.x - W * 0.3, y: sign21.y - 160, drift: 0.03 },
  ];
  // The 21 sign steps out while the camera is on day 22 (its pin needs the space).
  const sign21Opacity =
    1 - interpolate(frame, [turn.startFrame, turn.startFrame + 8], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) +
    interpolate(frame, [app.startFrame, app.startFrame + 8], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  // "A third of the way": steps after 22 fade pale on "third", back to full on the summit.
  const third = at(turn, "third");
  const paleAmount =
    interpolate(frame, [third - 6, third + 8], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) -
    interpolate(frame, [app.startFrame, app.startFrame + 10], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  const voice = (s: Scene) => (
    <>
      <Captions words={s.words} group={manifest.captions} mode="highlight" highlight={palette.hero} bottom={0.26} />
      {s.voiceoverKey ? <Voiceover src={urls[s.voiceoverKey]} /> : null}
    </>
  );
  const scene = (s: Scene, children: React.ReactNode) => (
    <SceneFrame key={s.id} from={s.startFrame} durationInFrames={s.durationFrames} enter={s.startFrame === 0 ? "cut" : "fade"} exit="fade" transitionFrames={6}>
      {children}
      {voice(s)}
    </SceneFrame>
  );
  const pt = (n: number) => stepPoint(n, W, H);

  return (
    <AbsoluteFill style={{ background: palette.bg }}>
      {/* The world: one continuous shot under every scene. */}
      <WorldCamera keys={cameraKeys} follow={steppy} punches={[{ at: at(origin, "surgery"), amount: 0.07, frames: 6, hold: 10 }]}>
        <Staircase count={STEPS} stepW={W} stepH={H} color={palette.accent} pale={palette.pale} paleFrom={22} paleAmount={Math.max(0, paleAmount)} hollow={[MISSED]} hollowColor={palette.hero} numberColor={palette.paper} font={display} />
        <Signpost
          x={sign21.x} y={sign21.y} text="21 DAYS" font={display} ink={palette.ink} board={palette.paper} edge={palette.ink} hero={palette.hero}
          fontSize={92} postHeight={330} appearAt={at(hook, "21") - 3} opacity={Math.min(1, sign21Opacity)} strikeAt={onWord(cta, "21", { absolute: true })}
        />
        <Signpost
          x={(66 + 0.8) * W} y={-66 * H} text="66 DAYS" sub="median" font={display} subFont={body} ink={palette.ink} board={palette.paper} edge={palette.ink} hero={palette.hero}
          fontSize={110} postHeight={260} appearAt={onWord(study, "66", { absolute: true })} opacity={1 - interpolate(frame, [app.startFrame, app.startFrame + 6], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })}
        />
        <MapPin x={pt(18).x} y={pt(18).y - 10} label="18 DAYS" size={560} bg={palette.ink} ink={palette.paper} font={display} at={onWord(study, "18", { absolute: true })} outAt={miss.startFrame} />
        <MapPin x={pt(254).x} y={pt(254).y - 10} label="254 DAYS" size={2000} bg={palette.hero} ink={palette.paper} font={display} at={onWord(study, "254", { absolute: true })} outAt={miss.startFrame} />
        <MapPin x={pt(MISSED).x + W * 0.05} y={pt(MISSED).y - 20} label="MISSED" size={160} bg={palette.hero} ink={palette.paper} font={display} at={miss.startFrame + 6} outAt={turn.startFrame} />
        <MapPin x={pt(22).x} y={pt(22).y - 10} label="DAY 22" size={96} bg={palette.ink} ink={palette.paper} font={display} at={onWord(turn, "22", { absolute: true })} outAt={app.startFrame} />
        <Climber path={path} poses={poses.map((p) => ({ ...p, src: urls[p.src] }))} stepW={W} stepH={H} height={STEPPY_H} jumps={jumps} />
      </WorldCamera>

      {scene(hook, (
        <>
          {/* Readable from frame 1: muted scrollers decide on the first frame. */}
          <Headline text="A HABIT TAKES 21 DAYS?" keyword="21" emphasis="color" hero={palette.hero} ink={palette.ink} font={display} maxSize={0.105} delay={-6} per={2} y={0.21} />
          <Place y={0.22}>
            <Stamp text="WRONG" color={palette.hero} font={display} size={0.15} rotate={-9} at={wordFrame(hook, "wrong")} />
          </Place>
          <Sfx src={urls[TICKS]} at={0} volume={0.14} />
          <Sfx src={urls[IMPACT]} at={wordFrame(hook, "21")} volume={0.18} />
          <Sfx src={urls[IMPACT]} at={wordFrame(hook, "wrong") + 4} volume={0.26} />
          <Sfx src={urls[WHOOSH]} at={wordFrame(hook, "wrong") + 6} volume={0.16} />
        </>
      ))}

      {scene(origin, (
        <>
          {/* The twist first: 21 was never about habits. Out before the mirror comes in. */}
          <div style={{ position: "absolute", inset: 0, opacity: 1 - interpolate(frame, [at(origin, "plastic") - 8, at(origin, "plastic")], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) }}>
            <Headline text="NEVER ABOUT HABITS" keyword="never" emphasis="color" hero={palette.hero} ink={palette.ink} font={display} maxSize={0.11} delay={onWord(origin, "never")} per={2} y={0.19} />
          </div>
          <Place y={0.14}>
            <Entrance delay={onWord(origin, "plastic")}>
              <LabelChip text="1960 · a plastic surgeon" bg={palette.ink} ink={palette.paper} font={body} size={0.036} />
            </Entrance>
          </Place>
          <Place x={0.28} y={0.305}>
            <MirrorFace height={0.27} at={onWord(origin, "plastic")} revealAt={wordFrame(origin, "face")} ink={palette.ink} hero={palette.hero} accent={palette.accent} paper={palette.paper} />
          </Place>
          <Place x={0.705} y={0.255}>
            <TextDrop text="AT LEAST" color={palette.hero} font={display} size={0.075} at={onWord(origin, "at")} dropAt={wordFrame(origin, "dropped")} />
          </Place>
          <Place x={0.705} y={0.33}>
            <TextDrop text="21 DAYS" color={palette.ink} font={display} size={0.09} halo={palette.bg} at={onWord(origin, "21", { nth: 2 })} />
          </Place>
          <Sfx src={urls[WHOOSH]} at={onWord(origin, "never")} volume={0.14} />
          <Sfx src={urls[POP]} at={wordFrame(origin, "plastic")} volume={0.2} />
          <Sfx src={urls[POP]} at={wordFrame(origin, "at")} volume={0.16} />
          <Sfx src={urls[IMPACT]} at={wordFrame(origin, "21", { nth: 2 })} volume={0.16} />
          <Sfx src={urls[CHIME]} at={wordFrame(origin, "face") + 4} volume={0.14} />
          <Sfx src={urls[WHOOSH]} at={wordFrame(origin, "dropped")} volume={0.22} />
        </>
      ))}

      {scene(study, (
        <>
          <Place y={0.14}>
            <LabelChip text="UCL · 2010 · 96 people" bg={palette.ink} ink={palette.paper} font={body} size={0.04} />
          </Place>
          {frame >= climbStart - 4 && frame < at(study, "18") ? (
            <Place y={0.205}>
              <LabelChip text={`Day ${dayNow}`} bg={dayNow >= 66 ? palette.hero : palette.accent} ink={palette.paper} font={display} size={0.05} />
            </Place>
          ) : null}
          <Sfx src={urls[TICKS]} at={wordFrame(study, "researchers")} volume={0.12} />
          <Sfx src={urls[TICKS]} at={wordFrame(study, "researchers") + 36} volume={0.12} />
          <Sfx src={urls[TICKS]} at={wordFrame(study, "researchers") + 72} volume={0.12} />
          <Sfx src={urls[TICKS]} at={wordFrame(study, "researchers") + 108} volume={0.12} />
          <Sfx src={urls[CHIME]} at={wordFrame(study, "66")} volume={0.2} />
          <Sfx src={urls[WHOOSH]} at={wordFrame(study, "18")} volume={0.18} />
          <Sfx src={urls[WHOOSH]} at={wordFrame(study, "254")} volume={0.2} />
        </>
      ))}

      {scene(miss, (
        <>
          <Place y={0.14}>
            <LabelChip text="One missed day" bg={palette.ink} ink={palette.paper} font={body} size={0.04} />
          </Place>
          <Headline text="NO DIFFERENCE" keyword="no" emphasis="color" hero={palette.hero} ink={palette.ink} font={display} maxSize={0.12} delay={onWord(miss, "result")} per={3} y={0.215} />
          <Sfx src={urls[POP]} at={6} volume={0.16} />
          <Sfx src={urls[IMPACT]} at={wordFrame(miss, "result")} volume={0.18} />
        </>
      ))}

      {scene(turn, (
        <>
          <Headline text="A THIRD OF THE WAY" keyword="third" emphasis="color" hero={palette.hero} ink={palette.ink} font={display} maxSize={0.11} delay={onWord(turn, "third")} per={3} y={0.19} />
          <Sfx src={urls[POP]} at={wordFrame(turn, "22")} volume={0.18} />
          <Sfx src={urls[WHOOSH]} at={wordFrame(turn, "third")} volume={0.16} />
        </>
      ))}

      {scene(app, (
        <>
          <Headline text="66, NOT 21" keyword="66" emphasis="color" hero={palette.hero} ink={palette.ink} font={display} maxSize={0.11} delay={onWord(app, "day")} per={3} y={0.16} />
          <Place y={0.44}>
            <FloatingCard src={urls[CARD_66]} width={0.44} aspect={1830 / 1090} delay={0} tag={<LabelChip text="Example" bg={palette.ink} ink={palette.paper} font={body} size={0.026} />} />
          </Place>
          <Place y={0.665} style={{ flexDirection: "row", gap: 24 }}>
            <Entrance delay={onWord(app, "two")}>
              <FreezeChip label="Freeze" bg={palette.accent} ink={palette.paper} font={display} size={0.04} />
            </Entrance>
            <Entrance delay={onWord(app, "freezes")}>
              <FreezeChip label="Freeze" bg={palette.accent} ink={palette.paper} font={display} size={0.04} />
            </Entrance>
          </Place>
          <Sfx src={urls[WHOOSH]} at={0} volume={0.18} />
          <Sfx src={urls[POP]} at={wordFrame(app, "two")} volume={0.2} />
          <Sfx src={urls[POP]} at={wordFrame(app, "freezes")} volume={0.18} />
        </>
      ))}

      {scene(cta, (
        <>
          <Headline text="SAVE THIS" keyword="save" emphasis="color" hero={palette.hero} ink={palette.ink} font={display} maxSize={0.13} delay={onWord(cta, "save")} per={3} y={0.16} />
          <Place x={0.68} y={0.585} width={0.36}>
            <StickerCharacter src={urls[STEPPY_POINT]} height={0.17} aspect={462 / 560} delay={2} />
          </Place>
          <Sfx src={urls[POP]} at={wordFrame(cta, "save")} volume={0.16} />
          <Sfx src={urls[WHOOSH]} at={onWord(cta, "21")} volume={0.2} />
        </>
      ))}

      {/* Under the voice the bed stays audible, and the pauses barely lift it (no pumping). */}
      {manifest.music ? <Music src={urls[MUSIC]} duckTo={0.34} volume={0.4} /> : null}
      <Grain blend="multiply" opacity={0.035} />
    </AbsoluteFill>
  );
};

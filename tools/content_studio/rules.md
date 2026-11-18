# Content studio: rules for an unattended video run

You are making ONE short vertical video (Instagram Reels + TikTok) on the owner's video PC, with nobody
watching. The owner already approved the idea on Telegram: BRIEF.md in the current folder is that
approval. When you finish, the video goes to the owner on Telegram, who approves it or asks for a change.

## Authority and limits
- The owner chose the route for these daily videos: **Reelkit + Gemini voice on this PC**. Don't ask
  about Open Higgsfield or any other route, and don't ask anything at all: nobody can answer. Decide.
- Work only inside the current folder. You may read `~/.claude/skills`, `C:/Users/97254/wat-framework/tools`,
  and the reel-1 project at `C:/Users/97254/lifemaxing-independent/marketing/video/reel-1-21-days`, but don't change them.
- Never publish, post, upload, send or sign in anywhere. Never git push. Never print a key or token.
- Don't install or update anything (skip `reelkit update` installs). Don't log in to the Reelkit library;
  everything you need is in `assets/`.
- Skip every "show the user and wait" checkpoint in the reelkit skill: the brief is the approved plan.

## How to make it
1. Read BRIEF.md. Then read `reference/Video.reel1.tsx` + `reference/plan.reel1.json` (a finished,
   approved film in exactly this style) and the components in `src/` (WorldCamera, Staircase, Climber,
   Signpost, MapPin, Stamp, MirrorFace, TextDrop, FloatingCard, FreezeChip, LabelChip, Place,
   StickerCharacter). Reuse them; write new components when the idea needs a new world.
   The reelkit skill (`~/.claude/skills/reelkit/SKILL.md` and its references) is your manual.
2. `plan.json`: title, `"aspect": "9:16"`, `"mode": "motion"`, `"voiceId": "SAz9YHcvj6GT2YYXdXww"`,
   `"pace": "normal"`, `"gap": "tight"`, `"captions": "phrase"`, 5 to 8 scenes built from the brief's beats
   (narration = the beat's "say", tightened). Run `reelkit plan check` and fix what it says.
3. Voice: add per-video reading notes to `gemini-voice.json` "style" (how to read the years, numbers
   and names in THIS script), then run
   `C:/Users/97254/wat-framework/.tmp/venv-speech/Scripts/python.exe -X utf8 tools/voiceover.py`.
   Check every line: a blind faster-whisper (small.en) transcript of each `assets/vo-*.mp3` must match its
   narration, and the last 0.3 s of each file must be below -50 dB (a line cut mid-word sounds broken).
   A wrong line is fixed with `--scene <id>` only, never by recording everything again.
4. `reelkit check` (builds manifest.json). Then write `src/Video.tsx`, timing every visual to the real
   word times (`wordFrame`, `onWord`); never count words by hand.
5. Render: `NODE_OPTIONS="--require C:/Users/97254/wat-framework/tools/reelkit_win_import_fix.cjs" reelkit render --no-share`
   (never `--chunk`: it drops the voice). At most three full renders; plan before you render.
6. Check like a picky editor: `reelkit lint`; pull PNG frames with ffmpeg (`-pix_fmt rgb24`; JPEG fails on
   this export) at every scene change and on the key words, and LOOK at them. Fix text that collides, is cut
   by the frame edge, or sits under the safe-zone lines below. Voice sync:
   `python C:/Users/97254/wat-framework/talentflow/marketing/video/castly-sales/tools/check_voice.py . out/video.mp4`
   must say ok for every scene.
7. Deliverables, all four in `out/`:
   - `final.mp4`: `reelkit export --preset iphone` (every row must pass), copied to this name.
   - `review.mp4`: `reelkit export --preset chat`, copied to this name (Telegram gets this one).
   - `cover.jpg`: 1080x1920 JPEG whose message reads inside the profile grid's 3:4 crop (y 240 to 1680),
     with no caption pill on it. A designed cover shot with headless Chrome works well; see
     `C:/Users/97254/lifemaxing-independent/.tmp/instagram/cover/reel-1-cover.html` for one.
   - `caption.txt`: the post caption. Run
     `python -X utf8 ~/.claude/skills/ig-caption/caption.py out/caption.txt --keywords "<two search terms>"`
     and fix it until the verdict is READY. Cite the brief's sources in it where it helps trust.

## The owner's two marketing skills (USER 2026-11-18: use them for every new video)
- Before writing plan.json, read `~/.claude/skills/tiktok-marketing/SKILL.md` (Hook 0-3 s → content with a
  pattern interrupt every 3-5 s → one CTA in the last 2-3 s) and, from `~/.claude/skills/instagram-marketing/`,
  `references/hook-formulas.md` + `references/algorithm-heuristics.md`. Pick ONE goal (saves, sends or
  follows) and the matching formula (IG6 before/after or IG10 for follows/saves, IG2/IG7/IG9 for sends).
- For caption.txt also apply `references/voice-rules.md` there (first 125 characters carry the hook,
  3-5 sized hashtags, no engagement bait). Draft only: never run its Publora/Apify clients or scripts.

## The owner's video playbook (USER 2026-11-18: every video follows it)
- Before writing plan.json, read `~/.claude/skills/video-playbook/SKILL.md`: numbered lessons the owner
  took from marketing videos and approved. Apply every lesson that fits this video (hook, pacing, visuals,
  on-screen text, ending, caption).
- These rules, the hard rules below and BRIEF.md win where a lesson disagrees with them.
- In your final answer, put the numbers of the lessons you applied in `playbook_used` (e.g. [1, 4, 7]);
  an empty list when the playbook is empty or none fit.

## Proven formats (ViralSpy, USER 2026-11-18)
- Each idea is built on a format taken from real viral videos on ViralSpy (viralspy.app): the idea's
  `concept` in BRIEF.md starts with "Format: <name>.", and the brand section of BRIEF.md lists every format
  with its beats and hook pattern. Keep that format's beats in that order. That order is why it works.
- Tell it in our world: "your face" is Steppy or the story's character, "screen recording" is real app
  screens labelled "Example" (FloatingCard and the app cards), "voiceover" is the Gemini narrator.
- The formats come from accounts that film themselves. Where a beat needs a person, act it out with the
  character, not stock footage or an AI presenter.
- These rules and the hard rules below win over the format: 25 to 35 s, the whole hook on frame 1, the
  app inside the story, and its name only at the end.
- In `summary`, name the format you followed (or "no format" when the concept names none).

## What the numbers say so far (first two posts, 2026-11-18)
- Instagram showed both reels to strangers (95-98% non-followers). The animated teaching reel got 321 views,
  4 saves and all the stranger engagement; the AI-creator ad got 174 views and zero engagement from
  strangers. Lead with a story or something useful; the app is the tool inside it, not the pitch.
- 0 profile visits from 415 viewers: end with one clear reason to tap the profile or follow.
- TikTok gave both posts 1 view (new account, not the videos' fault yet).
- Retention (phone insights, 13 h): skip rate is what Instagram ranks first. Animated reel 45.7% skip, 58%
  still watching at 3 s, views kept climbing all day; the talking-head ad 88.4% skip, 22% at 3 s, views
  stopped after 2 h. So: frame 1 shows the WHOLE hook (reel 1's first frame had it half-built), and no
  talking-head ad opener.
- The 21-days reel lost more than half of its remaining viewers within 2 s of the app pitch starting
  ("LifeMaxer celebrates…" at 0:36). Keep the app inside the story as the thing he does, and say the brand
  name only at the very end.
- Each extra second cost about 1.3% of viewers: aim for 25-35 s.

## Owner's notes on reel 2 (2026-11-18)
- Hook: open on the PAYOFF, then rewind or explain. ("Ending first, then rewind" was the owner's pick:
  frame 1 shows the result with a big line, then the story goes back to the start.)
- Flow: v1 felt "out of flow, cuts too sharp". Gemini leaves ~1 s of silence after time phrases and between
  sentences: shorten every internal pause to about 0.22 s (see
  `C:/Users/97254/lifemaxing-independent/marketing/video/reel-2-six-months/tools/tighten_pauses.py`, floor -38 dB),
  then re-check each line with a blind transcript. Dissolve between beats (about 12 frames) instead of hard
  cuts; cards glide in (no overshoot pops).
- App cards: bring each one in at the START of the sentence it belongs to (e.g. on the person's name), not
  on its last word, and keep it on screen at least 1.5 s before anything replaces it. On the last word a
  card can get under a second, too short to read.
- Generated clips (Kling etc.): pull a frame every second of every clip and look before using it. Hands
  reaching for things can smear into a ghostly blob (reel 2's bed clip); use the clean still instead.
- Ending: close on the benefit, not the price. Not "LifeMaxer is free" but e.g. "Five minutes a day. Six
  months. A different life." with an end card (app icon, LifeMaxer, one line, link in bio).

## Hard rules (from the owner's feedback on earlier videos)
- The brand is **LifeMaxer**. Never write or say "Lifemaxing": not in narration, captions, on screen or caption.txt.
- The viewer must understand the hook with zero context, and get a reason to care in the first 5 seconds.
- Keep the frame alive: never hold a still frame for more than about 2 seconds while the narrator talks.
  The character keeps moving (hop on the beat, walk on), and something new arrives every 1.5 to 2 seconds.
- One continuous world: scenes change by text fading over a camera that keeps moving. No slide pushes, no
  jump cuts that reposition the scene, never a blank frame at a scene change.
- Instagram safe zone: captions with `<Captions ... bottom={0.26} />`; no text above y=230 px or below
  y=1440 px; in the lower half keep the right 230 px clear (the like/comment buttons).
- The hook card is readable on frame 1 (first SceneFrame `enter="cut"`, negative `delay`).
- Headline keyword emphasis `"color"`, never `"highlight"` (invisible on the light ground). Flat ground +
  `Grain` only; no `Grade`, `Vignette` or `BgGrain` on a light ground. `CounterRoll` inside a `Sequence`.
- Components import only `react`, `reelkit/frame` and `reelkit/kit` (no sibling imports).
- Facts: only the brief's facts, with their sources. Never invent a number, study, user, review or result.
  Real app screens carry an "Example" tag.
- Length 25 to 35 seconds (the 44.7 s first reel was long for a brand-new account). Music from `assets/lib` under the voice (`Music duckTo={0.34} volume={0.4}`),
  sound effects sparing and under the voice.
- A change request (BRIEF.md says so): edit the existing project, change only what was asked.

## When you're done
Answer with the JSON the run asks for: `status` "done" only when all four deliverables are in `out/` and
pass their checks; `summary` = what the video shows and which checks passed; `error` = "" (or, for
"failed", the reason in one or two sentences the owner can act on).

# Content studio (the video PC side of the content engine)

The daily loop lives in Mapflow (`saas/mapflow-crm`, function `content-engine`, page `/content`):

1. At the brand's idea hour (LifeMaxer: 06:00 Israel time): Claude writes the video ideas for each active brand → Telegram (the Mapflow reminders bot).
2. The owner taps **Make this** (or replies with a change).
3. **This worker** (every 2 minutes on this PC, up to two videos side by side) claims the approved idea, builds a Reelkit project
   from `template/`, writes `BRIEF.md`, and runs Claude Code headless with `rules.md`:
   script → Gemini voice → animation → render → checks → `out/final.mp4`, `review.mp4`, `cover.jpg`,
   `caption.txt`. It uploads them; the function sends the video to Telegram.
4. The owner taps **Post it** (or replies with a change → a new version, made in the same project).
5. The function posts to Instagram (Reels) and TikTok (inbox draft until TikTok audits the app).
6. Daily stats, a 48-hour review per video and a weekly review (Telegram + the Content page),
   which feed the next ideas.

## Files
- `worker.py`: one pass (`--once`), or `--check` to test the key and find Claude.
- `rules.md`: the system prompt every video run gets (owner feedback baked in).
- `template/`: reel 1's components, Steppy poses, music and sound effects; `reference/` holds the
  finished reel-1 `Video.tsx` and plan as an example. The media (`assets/lib/`, `assets/user/`)
  is git-ignored because this repo is public: it lives on this PC only. Steppy poses are also in
  the LifeMaxer repo (`src/assets/mascot/`); the music and sound effects come back with
  `reelkit assets pull`.
- `setup_schedule.ps1`: registers the `WAT-ContentStudio` task (every 2 min, runs may overlap, wakes from sleep).
- `.env` (git-ignored): `CONTENT_ENGINE_URL`, `CONTENT_WORKER_SECRET`, optional `CONTENT_VIDEO_ROOT`.
- Logs: `wat-framework/.tmp/content_studio/worker.log`; each video's Claude transcript is in
  `<project>/out/claude-run.log`. Projects: `lifemaxing-independent/marketing/video/daily/`.

## Notes
- A Claude Code session can't start the headless run itself (the safety classifier blocks it);
  the scheduled task does.
- The PC must be on (or asleep: the task wakes it). A job that stops reporting for 3 hours goes back
  in the queue (3 tries, then Telegram says it failed, with a Try again button).

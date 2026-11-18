# Workflow: Content Engine (daily LifeMaxer videos)

## Objective
Every morning, propose short-video ideas for a brand, make the one the owner picks, post it to
Instagram and TikTok after the owner approves it, and learn from the results. The owner only taps
buttons in Telegram; everything else runs on its own.

Brand today: **LifeMaxer** (never write or say "Lifemaxing" in content).

## Where it lives
| Part | Place |
|---|---|
| Brain (ideas, Telegram, posting, stats, reviews) | Mapflow `saas/mapflow-crm`: function `supabase/functions/content-engine`, shared code `_shared/contentCopy.js` + `_shared/social.ts`, migration `20261118100000_content_engine.sql` |
| Telegram | the Mapflow reminders bot; `lead-reminders` forwards `ct:` buttons and replies to the content engine |
| Page | Mapflow → **Content** (`/content`, home workspace only): Today, Results, Accounts & settings |
| Video PC | `tools/content_studio/` on this PC: `worker.py`, `rules.md`, `template/` |
| Video projects | `lifemaxing-independent/marketing/video/daily/<date>-<slug>/` |

## The daily loop
1. **Ideas (idea hour, default 09:00 Israel).** The hourly job (`content-engine-hourly`, minute 4)
   writes 3 ideas per active brand from the brand voice, themes, past videos and their results.
   Each idea goes to Telegram with hook, script beats and sources, and buttons **Make this /
   Change / Skip**. Change = reply to the message with what to change; a new version comes back.
2. **Make.** `WAT-ContentStudio` (Task Scheduler, every 10 min, wakes the PC) runs
   `worker.py --once`: it claims the approved idea, copies `template/` (or the previous version's
   project for a change request), writes `BRIEF.md`, and runs Claude Code headless
   (Opus 5.5, high effort, 150 min limit) with `rules.md` as the system prompt. Deliverables:
   `out/final.mp4`, `out/review.mp4`, `out/cover.jpg`, `out/caption.txt`. The worker checks them
   with ffprobe and uploads them to the private `content-media` bucket.
3. **Approve.** The function sends the video to Telegram with **Post it / Change / Drop**.
   Change makes a new version in the same project.
4. **Post.** `content-engine-posts` (every 2 min, only while a post is queued) posts the Reel to
   Instagram (container → status → publish) and sends the video to the TikTok inbox (drafts:
   the owner taps Post in the TikTok app until TikTok audits the app).
5. **Learn.** Daily stats per post, a review 48 hours after posting, a weekly review on Sunday.
   All go to Telegram and the Results tab, and feed the next ideas.

## The video playbook (learn from marketing videos)
The owner sends marketing advice; approved lessons steer every video after that.
1. **Send:** to @MashtechCrmBot: a TikTok / Instagram / YouTube / Facebook / X / LinkedIn /
   Threads link, a video file (20 MB at most, a Telegram bot limit), or `/learn` + any text or
   article link. `/learn` alone explains it; `/playbook` says how big it is. Or paste on
   Content → **Playbook**. A message with only a business website link (no `/learn`) stays a lead
   note: lead-reminders forwards only `C.playbookIntent` messages from content-engine owners.
2. **Study** (video PC, `tools/content_studio/playbook.py`, when no video job is waiting):
   `study_prep.py` in the speech venv downloads with yt-dlp (+ curl_cffi, which TikTok needs),
   writes the transcript (faster-whisper: `small` tells the language, `small.en` for English,
   ivrit-ai turbo for Hebrew), the cut times and up to 36 frames (every 0.5 s of the hook);
   then headless Claude reads `STUDY.md` + frames with only Read/Glob (`study_rules.md`) and
   proposes 0-4 lessons, marked new / supports #n / conflicts #n against the playbook.
   Work folders: `.tmp/content_studio/studies/` (kept 21 days).
3. **Decide:** Telegram shows the lessons with **Add all / ➕ n / Skip**; a reply rewrites them
   (Claude in the function). Same on the Playbook tab. Adding a "conflicts" lesson replaces the
   old one; numbers (#n) are never reused (`content_lesson_decide`).
4. **Use:** every worker pass writes the added lessons to `~/.claude/skills/video-playbook/`
   (`SKILL.md` + `references/sources.md`), the skill every video job reads; `rules.md` makes the
   daily videos apply it and report `playbook_used` (the tab counts "used in N videos"). The
   morning ideas get the lessons in their prompt.

## Setup (once)
1. Video PC: `python tools/content_studio/connect_worker.py` from the wat-framework folder.
   It writes `tools/content_studio/.env` (git-ignored) without printing the key, checks the
   connection and registers the task. **A Claude session can't run it** (the safety check blocks
   moving the key and starting headless Claude); the owner runs it with `!` in the chat.
2. Instagram: `saas/mapflow-crm/.tmp/content-setup/1-instagram.md` (Meta app, Instagram Login,
   long-lived token pasted in Content → Accounts & settings). Tokens refresh themselves.
3. TikTok: `saas/mapflow-crm/.tmp/content-setup/2-tiktok.md` (developer app, keys into
   `tiktok-keys.env`), then set them as function secrets with a script that reads the file
   (never echo them), then **Connect TikTok** on the page.

## Checking on it
- Worker log: `.tmp/content_studio/worker.log`. `python tools/content_studio/worker.py --check`
  tests the key and finds Claude.
- A video run's whole Claude transcript: `<project>/out/claude-run.log`.
- Database: `content_ideas`, `content_videos`, `content_posts`, `content_metrics`,
  `content_reviews` (read with `npx supabase db query --remote=ginzdkemoribpqpwspix --read-only`).
- Function logs: Supabase dashboard → Edge Functions → content-engine.

## Edge cases
- **PC off:** nothing gets made; the idea waits. A job that stops reporting for 3 hours goes back
  in the queue; after 3 tries Telegram says it failed, with a **Try again** button.
- **Instagram refuses a post:** the post row keeps the error; **Retry** on the Content page.
  Check the file against the Reels rules in Meta's content publishing docs (the Reelkit iPhone
  export, 9:16 H.264/AAC, is the format the worker delivers).
- **TikTok unaudited:** only inbox drafts or private posts. Keep drafts mode unless TikTok
  approves the app.
- **Ideas repeat a past video:** add a history row (status `dropped`) for videos made by hand,
  so the idea writer sees them.
- **Playbook download fails:** Instagram often wants a login (code `login`): the bot asks the
  owner to send the video file instead. Don't add browser cookies without asking (it's their
  account). Other download errors update yt-dlp once a day and retry (3 tries per source).
  Over 60 minutes or 400 MB is refused. A study stuck for an hour goes back in the queue.
- **Template media:** `template/assets/lib/` (Reelkit library music and sound effects) and
  `template/assets/user/` (Steppy poses, app cards) stay on this PC only; the root repo is public.
  To restore: Steppy poses from the LifeMaxer repo `src/assets/mascot/`, the rest from the reel-1
  project or `reelkit assets pull`.

## Lessons
- `supabase db query` / `functions deploy` in agent mode need `--yes` for changes; deploy from
  `git archive <sha> supabase/functions` with `--use-api --no-verify-jwt`.
- The test database image lacks `storage.buckets.file_size_limit`; the migration guards it.
- Voice: the kit's `reach_sound_end` keeps the last word before a pause whole (a long number lost
  its end before the fix).
- Playbook prep: the ivrit-ai Hebrew model hears Hebrew in everything (detected an English video as
  `he` at 1.0) and is ~3x slower, so the multilingual `small` model picks the language first.
  The first prep run took 5 min (the hub checks); the worker runs prep with `HF_HUB_OFFLINE=1`
  (about 1.5 min for a 1-minute TikTok). yt-dlp `-S res:720` keeps vertical videos 720 wide so
  on-screen text stays readable in the frames.
- Release (2026-11-18): the safety check blocked `functions deploy` from the session; the owner
  approves or runs it (see the session's handoff file).

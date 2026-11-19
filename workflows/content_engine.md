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
| Telegram | its own **video bot** (USER 2026-11-18: separate from the lead bot): secret `CONTENT_BOT_TOKEN`, webhook straight to content-engine (header secret = sha256(token + ":content-webhook"), set by `ensureContentBot()` hourly or by `worker.py --check`). A person gets content there after pressing **Start** (`alert_devices.content_bot_started_at`); before that, and for older messages, the lead bot is used and `lead-reminders` forwards its `ct:` buttons, replies and playbook links |
| Page | Mapflow → **Content** (`/content`, home workspace only): Today, Playbook, Results, Accounts & settings (shows the video bot) |
| Video PC | `tools/content_studio/` on this PC: `worker.py`, `rules.md`, `template/` |
| Video projects | `lifemaxing-independent/marketing/video/daily/<date>-<slug>/` |

## The daily loop
1. **Ideas (idea hour, default 09:00 Israel; LifeMaxer 06:00 since 2026-11-19, USER).** The hourly job (`content-engine-hourly`, minute 4)
   writes 3 ideas per active brand from the brand voice, themes, past videos and their results.
   Each idea goes to Telegram with hook, script beats and sources, and buttons **Make this /
   Change / Skip**. Change = reply to the message with what to change; a new version comes back.
   **The owner's own ideas (2026-11-19):** "Add your idea" on the Content page, or `/idea <text>` on
   the video bot. The row is saved at once (`origin = 'owner'`, `owner_text` = their words, status
   `revising`), Claude writes it up in the background (`C.ownIdeaPrompt`: their lines word for word,
   brand rules and no made-up facts still win), then it's offered on Telegram like any idea, or with
   "Write it up and make it" goes straight to the PC. It counts toward `videos_per_day`. A write-up
   that never comes back is offered as written after 15 min (hourly job). `BRIEF.md` quotes
   `owner_text` under the write-up, and the owner's words win where they differ.
2. **Make.** `WAT-ContentStudio` (Task Scheduler, every 2 min, wakes the PC, runs may overlap)
   runs `worker.py --once`: it takes one of two video slots (`worker.lock`, `worker-2.lock`; two
   videos are made side by side, USER 2026-11-19) and claims the approved idea, copies `template/` (or the previous version's
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
1. **Send:** to the video bot: any link, a video file (20 MB at most, a Telegram bot limit), or
   `/learn` + text (a long text works without it). `/playbook` says how big it is; `/help` and
   `/start` explain the bot. Or paste on Content → **Playbook**. Sent to the lead bot by habit, a
   social video link or `/learn` still works (with a pointer to the video bot); a business website
   link alone stays a lead note there (`C.playbookIntent`, `ownBot` only on the video bot).
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
5. **Screenshots** (USER 2026-11-18, after the Insights photos they sent were dropped: before this
   the bots had no photo handling, and a bot can't fetch old messages, so they were lost): a photo
   or an image file sent to either bot is a `photos` source (on the lead bot with the pointer). An
   album arrives as one message per photo: `content_add_photo()` puts them in one source (one
   reply, each photo once, at most 10, a failed one sent again is read again), and `claim_source`
   waits until none came for 60 s. The PC downloads each one (`source_file` with `n`), Claude reads
   them (the Screenshots section of `study_rules.md`, with the owner's post log in STUDY.md to tell
   which video it is) and answers with `stats` (one entry per video, every value as shown) plus
   lessons from them. The numbers go on the Telegram card, in `content_sources.stats` (Playbook tab:
   on the card, and **Show the numbers** under "Sent and studied") and at the end of
   `~/.claude/instagram/log.md`. The owner's reels aren't in `content_posts` (made by hand), so they
   aren't linked to `content_metrics` yet.

## Remakes (our own ad in the format of one the owner likes)
USER 2026-11-18: share an ad, get a similar one for LifeMaxer ("decide per ad" between routes).
1. **Ask:** `/remake` + a video link (or a video file with `/remake` as its caption) on the video bot,
   **🎬 Make one like this** under a studied video, or the tick box in Content → Playbook.
   Only videos (not text or web pages). The source is studied first if it's new (lessons too).
2. **Write it** (video PC, `playbook.remake_next()`, before studies when no video job is waiting):
   reuses the study folder (frames, transcript, cuts) or prepares it again, writes `REMAKE.md`
   (measurements + brand voice + playbook + recent titles), headless Claude with Read/Glob only
   and `remake_rules.md` returns the blueprint (their beats with times, the format, the hook),
   our idea (beats with `mirrors`), and the route (`motion` or `ai_footage` with a reason).
   Rule: borrow the format, never their words (no run of 4+ words), footage, music, logo or people.
3. **Decide:** a remake card on Telegram / Today → **Remakes**: **🎨 Make it (motion graphics)**,
   **🎥 With AI footage**, Change, Skip (the recommended route first). Remakes are extra videos:
   they don't count toward `videos_per_day` or park the morning ideas.
4. **Motion graphics:** the normal video job; `BRIEF.md` gets a "THIS IS A REMAKE" section and the
   reference frames in `reference/remake/`.
5. **AI footage** (status `ai_waiting`; credits are never spent unattended): in a session, the owner
   says "make the AI remake". Then:
   `python tools/content_studio/deliver_video.py --list` → `--show <idea id>` (beats, format, brand);
   ask the Open Higgsfield question (global CLAUDE.md), quote the cost (`estimate_video_cost`; a 15 s
   Seedance 2.5 presenter with speech, 9:16: 480p 45 credits, 720p 105, 1080p 240) and get the owner's
   OK. Only the AI shots get generated (by the owner in Open Higgsfield, http://127.0.0.1:3000, or with
   the Higgsfield connector after the OK). Billing differs: the connector spends the higgsfield.ai plan
   credits; Open Higgsfield is free software but spends the separate Higgsfield API dollar balance
   (pay-as-you-go, top-ups from $5; Seedance 2.5 listed at $0.1177/s, about $1.77 for 15 s). Then, the usual way:
   `python tools/content_studio/deliver_video.py --footage <idea id> <clip.mp4> ...`: the clips go to
   `.tmp/content_studio/ai_footage/<idea id>/`, the remake is queued (`queue_ai_remake`), and the PC
   assembles it (kept clips, AI presenter with its own voice, app screens, end card) like any video.
   `--footage` refuses before copying anything when a clip isn't a vertical (about 9:16) mp4, 2 to 30 s,
   with a sound track (`--silent-ok` for b-roll without speech), or when the idea isn't in `ai_waiting`.
   It clears the clips from an earlier try first, because the PC uses every mp4 in that folder.
   `--check-clips <clip.mp4> ...` runs only the clip check, offline. Pass full paths, and run it
   from the wat-framework folder. A relative `wat-framework/.tmp/...` path from inside that folder
   doesn't exist. Look at frames and run a blind transcript of the speech too: the script can't see
   a garbled face or wrong words. A made-up presenter never speaks as a user (that would be a fake
   testimonial) and doesn't say the brand name, which the end card shows.
   A video finished entirely in the session instead: `deliver_video.py --idea <id> --project <folder>`
   (checks `out/`, `adopt_idea`, uploads). Once adopted, a row stuck in `making` returns to the PC's
   queue after 3 h, so check the files first.
   Keep stretches (`blueprint.keep`, only when the owner's /remake note asks, e.g. the clip a reaction
   video reacts to): cut to `reference/remake/keep-N.mp4` with their sound; credit the creator.
   First test 2026-11-18: realtor reel (water-balloon clip + pitch in a car) → "Parked-car pitch".

## Proven formats from ViralSpy
ViralSpy (https://viralspy.app/dashboard, signed in as the LifeMaxer Google account in Claude in Chrome
"Browser 1"; viralspy.ai is a different product) ranks real videos by how far they beat their creator's
usual views and breaks each into beats. It has no API or export, so nothing pulls from it automatically.
- **Formats → ideas:** 11 faceless formats (beats + hook pattern each) are appended to LifeMaxer's brand
  voice in `content_brands.voice` under "## Proven formats". Every morning idea names one at the start of
  `concept` ("Format: <name>."), and `rules.md` tells the video PC to keep that format's beats.
  The pre-change voice is in `.tmp/viralspy/voice-before.md`. To change the list, edit that section in
  CRM → Content → Accounts & settings → brand voice, not in code.
- **Videos to copy:** a viral link from ViralSpy (Viral now, or the examples under a format) goes to
  @MashtechVideoBot as `/remake <link>` (see Remakes above), or as a plain link to become a playbook source.
- **Account setup done 2026-11-18:** topic, About you, business details, brand facts (products, audience,
  rules, style, banned words; 300 characters max per fact) and 4 competitors (@jamesclear, @aliabdaal,
  @mattdavella on Instagram, @finchcare on TikTok). Its AI writer's scripts run long and pitch early (a
  54 s test named the app at about 12 s), so take its formats and hooks, not its scripts.
- Limits a month: 200 AI writes, 30 video checks, 100 breakdowns, 20 competitors. No Hebrew.

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
- Release (2026-11-18): the safety check blocks `functions deploy` to production until the owner
  says yes in the chat; ask once with the exact functions, then deploy. First live study: a 61 s
  TikTok took 9 min end to end (prep ~1.5 min, Claude the rest) and gave 4 concrete lessons.
- Long renders (2026-11-19, first 2-a-day batch): a 34 s video's `reelkit render` took ~14 min. Bash's
  default 10-min cap moved it to the background, the headless run ended its turn to wait, and with
  `--json-schema` ending the turn means reporting: it said "failed" with a finished `out/video.mp4`
  and no exports. The worker then started over in a new `-2` folder. Fixes: `child_env()` sets
  `BASH_MAX_TIMEOUT_MS` (then 60 min, now 120: see below) and `rules.md` says to run render/export in
  the foreground with a matching `timeout`; a run that stops with the render made but not exported is resumed once in
  the same session (`--resume`); a retry (claim attempts > 1) goes back to the failed run's
  `project_dir` and resumes its session (id from `out/claude-run.log`) instead of starting over.
- Two videos side by side (2026-11-19): the task runs every 2 min with `MultipleInstances Parallel`;
  the worker holds `worker.lock` or `worker-2.lock` per video and `playbook.lock` for studies and remakes,
  so a pass that finds both video slots busy exits in a second. Re-running `setup_schedule.ps1`
  (`Register-ScheduledTask -Force`) does NOT stop a pass that is already running (tested with a
  throwaway task), so the schedule can be changed mid-video.
- **The slow day (2026-11-19): two videos took ~6 hours instead of ~2.** What went wrong, in order:
  1. A ~14 min render passed Bash's 10-min cap, went to the background and the run reported
     "failed" (fixed: `BASH_MAX_TIMEOUT_MS`, foreground rule).
  2. The retry started from zero instead of finishing the rendered video (fixed: retries resume).
  3. Side by side was switched on after checking CPU only, not memory. On this 16 GB laptop the
     memory was already taken: Docker Desktop's VM with a local Supabase (~12 GB, up for days), VS
     Code + several Claude sessions (~4 GB), a playbook study (`study_prep.py`, ~5 GB). Two renders on
     top made Windows swap to disk (42 GB committed): renders went from 0.8 to 3-7 s a frame, one
     render was killed out of memory (exit 137), and runs hit the 150-min limit.
  4. Telegram cut a ~17,000-character change reply into parts; only the first ~4,000 characters
     reached the PC (fixed: parts are appended, the claim waits 60 s).
  5. Stopping a run with `taskkill /T` on claude.exe does NOT stop its `reelkit render` (Git Bash
     breaks the parent chain), so a "stopped" render kept eating memory. Find it by start time
     (`node ... reelkit.mjs render`) and stop it too. The worker's timeout kill has the same gap.
  6. A Vite dev server left running from an earlier session (port 5197, since 2026-11-17) used ~2
     CPU threads all day and was first mistaken for the render.
  **Before blaming the render, check memory first:** free RAM (`Win32_OperatingSystem`) and the top
  holders by private bytes (vmmem/vmmemWSL = Docker/WSL). Below ~3 GB free, don't start a second
  render or a study.
- **Renders take turns (USER 2026-11-19, built the same day):** `tools/content_studio/media_turn.py` is one
  turn (`.tmp/content_studio/media.lock`: pid, label, project) for every heavy media job. `rules.md` runs
  `reelkit render` and `reelkit export` through it (`python .../media_turn.py reelkit render --no-share`);
  a second one prints "media_turn: waiting ..." and waits (max 60 min, then goes anyway). A study's prep
  takes the same turn, and a study isn't even claimed while a render holds it (so the source keeps its
  tries). On a run's timeout the worker also stops the media job of that project through the turn's pid
  (the render runs under the wrapper, so its tree is whole). Two videos still build side by side.
- **Steering a retry:** put the owner's instruction in `out/RESUME_NOTE.md` of the project and re-queue the
  video with `attempts` > 1 counted from 1 (SQL: status 'queued', attempts 1, project_dir set); the retry adds
  the note to its prompt and renames it `RESUME_NOTE.used.md`. Used 2026-11-19 to ship Start Monday's
  finished 12:12 render instead of a third slow render.
- **Why a video took 40-60 min, and the three fixes (USER approved 2026-11-19, built that evening):**
  a full render is ~15 min with free memory, and runs re-rendered whole films (up to 3) to fix layout a
  still would have shown. (1) `rules.md` step 5: `reelkit preview` stills first (two frames per scene +
  both sides of every cut + `out/preview/sheet.jpg`, a minute or two, no turn needed), fix until every
  still is right, then ONE full render; a second only for something the stills can't show (voice sync,
  sound, a scene that plays wrong), never a third. The turn is mandatory, also in a resumed run (the gym
  redesign's resumed session rendered directly at 17:57 because its earlier turns had). (2) A render that
  takes its turn with < 3 GB free (`LOW_MEMORY_GB`; `media.lock` records `free_gb`) makes the worker send
  the owner one Telegram note per run (`low_memory` action: the video, the GB free, "close Docker / extra
  Claude windows / VS Code"). (3) One Bash command may run 120 min (`BASH_CAP_MS`, rules say
  `timeout: 7200000`): a slow render plus its wait passed the old 60-min cap at ~18:30 and the harness
  killed it (a command over the cap goes to the background and is stopped 10 min later). The whole run
  is still `CLAUDE_TIMEOUT_S` 150 min inside the engine's 3 h making window.
- **Two bots, one chat (2026-11-19):** the lead bot and the content bot number their messages
  separately in the owner's chat. Once the content bot reached the lead bot's old numbers (53-66), the
  key `(chat_id, message_id)` refused Start Monday v2's message row (no error surfaced: the insert's
  error wasn't read), and a reply could have matched the other bot's idea or video. Fixed in fb44efc:
  key `(chat_id, bot, message_id)`, replies looked up in the bot they came in, a failed insert is logged.
  A "ready" video without a `content_messages` row of kind `video` means its message wasn't recorded.
- **Posting hours (USER 2026-11-19, "upload it at a good time"):** the 5-h gap between a brand's
  posts had put the day's second video at 01:24. Posts now go up only between 09:00 and 21:00 on the
  brand's clock (`C.POST_HOURS`, `content_brands.timezone`); a time outside waits for 09:00. With a
  9:00 post, the next two land at 14:00 and 19:00. Mapflow 28311fd. To move a waiting post by hand,
  set `content_posts.next_check_at` while its status is 'queued'.

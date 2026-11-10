# Notion Missions

**Objective:** I write missions on a Notion board. Every hour my PC picks up the
ones marked Ready, Claude Code does each one unattended on its own branch, and the
report lands back in the mission's Notion page. Nothing is pushed, deployed, sent
or paid for without me: those steps happen only after I review, in a normal session.

## The board

A Notion page called "Claude Missions" holding a database **Missions** with:

| Property | Use |
|---|---|
| Mission (title) | Short name of the job |
| Status | (empty) or **Ready** → Running → Needs review / Needs info / Failed → Done. **Draft** = leave it alone. |
| Project | Folder to work in. Synced from `websites/`, `saas/`, `internal/`, root-level repos and `extra_projects` in `board.json` (outside projects such as lifemaxing, and overrides such as barukh-law → its `site/` repo). Also "No project (research / writing)" and "New project". |
| Priority | High / Normal / Low (empty counts as Normal) |
| Result | One line from Claude (or why it didn't run) |
| Branch | `mission/<date>-<id>-<slug>` in the project's repo |
| Last run | When it last started |

The page body is the brief. Images and files in it are downloaded and handed to
Claude. Each run appends a "🤖 Claude's report" section (what changed, how it was
verified, what's left, questions, run details).

## Live view (I asked to see live what's running, waiting and finished, 2026-10-19)

- **Board view** grouped by Status, created through the API (`board.create_board_view`,
  Notion-Version `2026-03-11`, `POST /v1/views`; everything else stays on `2022-06-28`).
- **Live status box** (📡 callout right above the board, id `status_block_id` in board.json,
  recreated if deleted): what's being worked on, minutes, current step; how many are
  waiting, drafts, finished to check, done, failed, waiting for my answer; update time.
- **Running card's Result**: `Working · 14 min · Step 2/4: Fixing the day editor · Run the
  calendar tests`. Read from Claude Code's own session transcript
  (`~/.claude/projects/*-<short id>*/<session>.jsonl`: last TodoWrite step + last tool use).
  Commands without a description show only the program name, since arguments can carry tokens.
- **Waiting cards' Result**: `Waiting · #n in line`, keeping any "Paused …" note.
- `live.refresh()` runs at run start, every 45 s while a mission runs (`live.Ticker`), after
  each mission and at the end. `run_missions.py --status` does one refresh by hand.
- It never writes to a card someone else edited last: that write would make the
  integration the last editor and hide their edit from the safety check. Such cards also
  don't get a place in line.

## Trigger

Windows Task Scheduler task `WAT-NotionMissions`, every 60 minutes while I'm logged
on (`pythonw`, no window, never two at once):

```
pythonw tools\notion_missions\run_missions.py      # --max 3 --timeout-min 60 --dry-run
```

## Tools

- `tools/notion_missions/notion_api.py`: Notion REST client (API version 2022-06-28)
  and Markdown → Notion blocks.
- `tools/notion_missions/board.py`: property names, statuses, project list, reading a
  page as text.
- `tools/notion_missions/setup_board.py <page link>`: one-time; builds the how-to,
  the database and a Draft example inside a page shared with the integration and
  writes `tools/notion_missions/board.json` (gitignored: database id, my Notion user
  id as owner, the integration's bot id, `extra_projects`).
- `tools/notion_missions/run_missions.py`: the runner (below).
- `tools/notion_missions/add_missions.py <missions.json> [--draft]`: adds missions I
  dictate in a session (list of {title, project, body, priority?}). Created Ready, so the
  next run takes them; `--draft` parks them.
- `tools/notion_missions/setup_schedule.ps1 [-EveryMinutes 60]`: registers the task.

## What one run does

1. Takes the run lock (`.tmp/notion_missions/run.lock`). Any mission still "Running"
   is from a dead run, so it becomes Failed. Adds new project folders to the dropdown.
   Removes clean worktrees of missions I set to Done (the branches stay).
2. Picks missions hands-off (I asked for no manual step, 2026-10-19): everything set to
   Ready, plus new rows with **no Status** once nobody has edited them for 10 minutes
   (so a half-typed mission isn't grabbed). High first, then oldest. At most `--max` per run.
   Rows with no name and no text are ignored (accidental empty rows). Picked rows
   without a Status get Status Ready so the board shows them waiting.
3. Checks, before anything runs: **the last editor must be me or the integration**
   (only my own tools hold its token), else Needs info ("someone other than you edited
   this"). **No Project chosen** → a quick Haiku call with no tools (`classify`) picks one
   from the mission text, the projects on the board and MEMORY.md, and writes it on the card.
   "Unclear" → Needs info. The project folder must exist.
4. Workspace:
   - git repo → its own worktree at `.tmp/notion_missions/wt/<id8>` on the mission
     branch, from the repo's `main`/`master`. The normal checkout (my work in
     progress, other sessions) is never touched. A follow-up run reuses the worktree.
   - No project → scratch folder `.tmp/notion_missions/scratch/<id8>`.
   - New project → workspace root; Claude creates the folder with its own repo.
   - Folder tracked inside a bigger repo (e.g. `internal/work-showcase` in wat-framework)
     → worktree of that repo, working in the subfolder. It must exist on `main`, not
     only in the staging area.
   - Non-git folder → in place (Claude lists every file it changed). Avoid this: on
     2026-10-19 plumb, zakai, ashcroft-vale, studio-north and intake-studio got their
     own local repos (first commit = snapshot) so missions there get branches too. Do
     the same for any new project.
5. Runs the Claude CLI headless (`claude -p`, found on PATH or in the VS Code
   extension at `~/.vscode/extensions/anthropic.claude-code-*/resources/native-binary/`):
   `--model claude-opus-5-5 --effort high` (my choice, 2026-10-19: `MODEL`/`EFFORT` in
   run_missions.py; the project guess uses them too),
   `--permission-mode auto --permission-prompts none --strict-mcp-config`, deny rules
   for push/gh/vercel/supabase deploy, `--json-schema` for {status, summary, report,
   questions}, and rules (appended system prompt) about where to work and the hard limits.
6. Writes the report into the page and sets Needs review (done), Needs info
   (questions) or Failed. Raw output goes to `.tmp/notion_missions/logs/`.

## Safety model (why it's allowed to run unattended)

- **Only my edits trigger work** (mine or the integration's, i.e. my own tools). Anyone
  else editing a mission blocks it until I set Ready again myself. Keep the page private anyway.
- **git push is disabled** for the run through `GIT_CONFIG_*` env (`pushInsteadOf`
  rewrites every https/ssh/git@ remote to a dead scheme), on top of the deny rules.
- **No MCP connectors** (`--strict-mcp-config`), so no Supabase, Vercel, Higgsfield
  or other paid or live services.
- **Auto mode's classifier** still checks every action; nothing can prompt, so
  anything it would ask about is denied.
- **Pro plan, not the API.** The runner reads `.env` with `dotenv_values()` (never into
  `os.environ`) and strips `ANTHROPIC_API_KEY`/`ANTHROPIC_AUTH_TOKEN` from the child
  env, so missions use my claude.ai login.

## Reviewing and shipping

- Needs review → look at the report, the branch, or the worktree folder. To ship,
  ask Claude in a normal session: "review and release mission branch `mission/…` in
  <project>". It merges and releases with the usual approvals. Then set Done.
- Needs info → answer under the questions in the page and set Ready. The next run
  sees the whole page, including its earlier report, and keeps working on the same branch.
- To continue a mission interactively: the report's Run details give
  `claude --resume <session id>`, run from the worktree folder.

## One-time setup

1. https://www.notion.so/profile/integrations → New integration (Internal) → copy the
   secret into `.env` as `NOTION_TOKEN=...` (I paste it myself, it never goes in chat).
2. Create an empty Notion page, then ••• → Connections → add the integration.
3. `python tools/notion_missions/setup_board.py <page link>`
4. `python tools/notion_missions/run_missions.py --dry-run` → lists what would run.
5. First real run by hand: `python tools/notion_missions/run_missions.py --max 1`.
6. `powershell -ExecutionPolicy Bypass -File tools\notion_missions\setup_schedule.ps1`

## Known limitations

- Runs only while the PC is on and I'm logged on.
- **Cut-off runs carry on by themselves.** Lost connection or a Claude server error puts
  the mission back to Ready ("Paused: …") and stops that run. Hitting the time limit
  (75 min) puts it back to Ready, and the run moves on to the next mission. A card still
  "Running" at the start of a run (PC off, crash) goes back to Ready too. The next attempt
  continues from the worktree, including uncommitted changes. 3 cut-offs in a row → Failed.
  Counter: `.tmp/notion_missions/attempts.json`.
- **If Notion can't be reached** when a result is ready, it's kept in
  `.tmp/notion_missions/pending/` and sent first thing on the next run. A half-sent result
  doesn't post the report twice.
- Lesson (2026-10-19, first real run): the internet dropped 36 min into a mission (Claude
  returned "Can't reach the API server … ENOTFOUND"). Writing the failure to Notion then
  raised a raw `requests` ConnectionError, and under pythonw the runner died silently with
  the card stuck on Running. Fixed: the Notion client retries and wraps network errors,
  everything above is retried, and any crash is written to runner.log.
- Missions use my Pro plan's usage. When the limit hits, the mission goes back to Ready
  ("Waiting: Claude usage limit…") and the runner stops until the next hour.
- A fresh worktree has no `node_modules` or `.env.local`: Claude installs dependencies
  in the worktree and may read env files from the normal checkout.
- A Claude Code session can't start the runner itself: the auto-mode classifier blocks
  launching unattended agents from inside a session ("Create Unsafe Agents"). Run it
  from a terminal, or let the scheduled task do it.
- Board view: the API creates a table. Switch it to Board grouped by Status by hand.
- Notion page ids in one workspace share a long prefix (ours all start `3febc2789f1d81…`).
  Short ids for folders, branches and logs must come from the END of the id
  (`board.short_id`). The first version used the start, so every mission would have
  shared one worktree; caught by the dry run on 2026-10-19. The offline test uses
  shared-prefix ids so this can't come back.
- Two Pythons on this PC: the Store Python on PATH has `requests`/`python-dotenv`, but
  `Programs\Python312` (used by the daily summary task) doesn't. `setup_schedule.ps1`
  picks the first one that has both.
- After changing the runner, run the offline test: `python tools/notion_missions/test_offline.py`
  (fake Notion, scratch repo, stub Claude; 45 checks; touches nothing real, starts no agent).

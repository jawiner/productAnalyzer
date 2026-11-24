# Expiry Watch (renewal alerts)

**Objective:** I get a Telegram message before anything with an end date runs out:
subscriptions, domains, site certificates, API keys and tokens, licences, memberships.
One daily check on my PC, one list in Notion that I can edit from the phone.

## The list

Notion page **Renewals** (link in `tools/expiry_watch/board.json`, gitignored), table columns:

| Column | Use |
|---|---|
| Name | What it is. For Type = Domain: the address (`example.co.il`). |
| Expires | The end date, or the next charge date for something that pays by itself. |
| Days left | Counted live by Notion. |
| Type | Subscription, Domain, SSL certificate, API key / token, Licence, Membership, Other |
| Status | Written by the check: 🟢 OK, 🟡 soon, 🔴 very soon / expired / key rejected, ⚪ no date |
| Repeats + Renews by itself | Monthly or Yearly and ticked = it charges by itself. Short heads-up before each charge, then the date moves on by itself. |
| Warn days before | Optional, e.g. `60, 30, 7`. Empty = the defaults below. |
| Cost, Where to renew, Notes | Shown in the alert. |
| Paused | Ticked = never mentioned. |
| Last alert, Auto key | The check's own bookkeeping. Don't edit. |

**Default warning days:** 30, 14, 7, 3, 1 and on the day. Monthly: 3, 1, on the day.
Pays by itself: monthly 3 and 1 days before, yearly 14, 3 and 1. Certificates: from 14 days
(hosts renew them by themselves about 30 days ahead, so earlier would be noise).
After the date with nothing changed: the next 3 days, then once a week.

## What is checked automatically

- **Domain rows:** the real registration date from the registry (RDAP, then WHOIS; `.co.il`
  comes from ISOC's WHOIS `validity:` line). The registry's date overwrites what's in Expires.
  Addresses on a shared host (`x.vercel.app`) have no registration, only a certificate.
- **Certificates:** each Domain row gets its own "… certificate" row with the date read
  from the live site. A certificate browsers reject is reported as a problem right away.
- **Keys in `.env`:** tested with a free "who am I / list" call, never a paid one:
  Anthropic, Gemini, OpenAI, Notion, Supabase access token, Firecrawl (also shows credits
  left), Telegram bot, WhatsApp token (Meta also gives its end date), Gmail app password
  (log-in only, nothing sent), and `token.json` (Google sign-in) when it exists. Any key
  shaped like a JWT gets its built-in end date read.
  A rejected key alerts once, then weekly while it stays broken. No internet is never an alert.
- **Not tested:** `GOOGLE_PLACES_API_KEY` (no free test call). `--dry-run` lists every secret
  that has no test.
- More env files: add `{"label": "castly", "path": "talentflow/.env.deploy"}` to
  `extra_env_files` in `board.json`. Only add files I've agreed to (mapflow's `.env.local`
  is off limits).

## Alerts

One Telegram message per day with everything that reached a new warning day or broke.
Each warning day alerts once: if the PC was off for a week, one message with the real
number of days, not a backlog. If sending fails, nothing is marked as sent and the next
run tries again. Once a week (first run from Sunday) a short "still running" note with
what's next, so silence never means the check died. If no run succeeded for 2 days, it
says so.

## Trigger

Task Scheduler task `WAT-ExpiryWatch`: daily 09:00, plus at log-on and every 3 hours.
The script skips when today's run already succeeded, so the extra triggers only matter
when the PC was off or offline at 09:00.

```
pythonw tools\expiry_watch\watch.py --if-due
```

## Tools

- `tools/expiry_watch/watch.py`: the daily run. `--dry-run` (change and send nothing),
  `--test-message`, `--heartbeat`, `--if-due`.
- `tools/expiry_watch/rules.py`: when to warn and the message text (pure logic).
- `tools/expiry_watch/checks.py`: domain, certificate and key checks.
- `tools/expiry_watch/renewals.py`: the Notion table (columns, reading rows).
  Uses the Notion client in `tools/notion_missions/notion_api.py`.
- `tools/expiry_watch/telegram_send.py`: sending.
- `tools/expiry_watch/setup_board.py [page link]`: one-time; builds the page and table.
- `tools/expiry_watch/setup_telegram.py`: one-time; finds my chat with the bot, sends a test.
- `tools/expiry_watch/setup_schedule.ps1`: registers the task.
- `tools/expiry_watch/test_offline.py`: fake Notion, lookups and Telegram; run after any change.

## One-time setup

1. `NOTION_TOKEN` in `.env` (already there for the missions board).
2. `python tools/expiry_watch/setup_board.py`: creates Renewals inside the page the
   integration can already write to. If I move the page elsewhere in Notion, add the
   integration again: ••• → Connections.
3. Telegram: @BotFather → `/newbot` → put the token in `.env` as `TELEGRAM_BOT_TOKEN=...`
   (I paste it myself, never in chat) → open the new bot, press Start →
   `python tools/expiry_watch/setup_telegram.py`. Use a bot of its own: the CRM's bot
   (the CRM's lead bot) has a webhook, so its messages can't be read to find the chat.
4. `powershell -ExecutionPolicy Bypass -File tools\expiry_watch\setup_schedule.ps1`

## Adding things from a session

When I say "remind me about X on <date>", add a row to the table (Name, Expires, Type;
Repeats + Renews by itself for things that charge by themselves) through the Notion client,
then run `watch.py --dry-run` to confirm the row reads correctly.

## Known limits and lessons

- Runs only while the PC is on. A missed day is caught up at the next log-on.
- Without Telegram set up, the run still keeps the Notion list current and holds the
  alerts back; they go out on the first run after setup.
- State outside Notion (`.tmp/expiry_watch/state.json`: last good run, weekly note) is
  disposable. Losing it costs one extra weekly note. What was already alerted lives in
  the row's "Last alert".
- Notion's `now()` in a date formula carries the time of day and made "Days left" one
  short; the column uses `today()`.
- A row the check added itself (Auto key filled) comes back if deleted while the thing
  still exists. Tick Paused instead. If the thing is gone (key removed from `.env`, domain
  row deleted), the row is marked "No longer found" and left for me to delete.
- Errors never include a secret: request errors are reduced to a status code or an error
  name, because their text can carry the URL or headers.
- First run (2026-11-10) found both Anthropic keys and the Supabase access token in the
  root `.env` rejected by their services.

---
name: deploy-tracker
description: Deploy or update the accountability bot + dashboard on this machine with docker compose. Use when asked to deploy, run, restart, or update the tracker.
---

# Deploy the tracker

Target: an **always-on** machine (reminders die when the machine sleeps —
warn the user if this looks like a laptop).

## Fresh deploy

1. Verify `docker compose version` works.
2. Clone `calmmage/calmmage-task-tracker` (or `git pull` if present) and check
   out the current main / feature branch the user names.
3. `cp .env.example .env` and fill it in — ask the user for anything missing:
   - `TELEGRAM_BOT_TOKEN` — from @BotFather (`/newbot` if none exists)
   - `TELEGRAM_USER_ID` — user's numeric ID (@userinfobot)
   - `OBSIDIAN_VAULT` — absolute host path to the vault
   - `OBSIDIAN_INBOX_GLOBS` — where inbox items live; check the actual vault
     structure (`ls` it) and adjust: a folder (`Inbox/**/*.md`), daily notes
     (`Daily/*.md`), or several globs comma-separated. Items are unchecked
     `- [ ]` tasks plus titles of task-less notes.
   - `ANTHROPIC_API_KEY` — optional; without it triage falls back to
     `plan/on-deck.md`
4. `docker compose up -d --build`

## Verify (do not skip)

1. `docker compose ps` — both services up; `docker compose logs bot --tail 20`
   shows "Bot starting".
2. Have the user send `/start`, then `/inbox` — confirm 3 focus buttons appear
   and reflect real vault items.
3. `curl -s localhost:8000 | head -5` returns the dashboard HTML.
4. Timezone check: `TZ` in .env matches where the user actually is (reminders
   fire 08:00 / 21:30 / Sun 18:00 local).

## Update

`git pull && docker compose up -d --build`. SQLite migrations run
automatically on connect.

## Backup

Add a daily cron: `cp <repo>/data/tracker.db <backup-dir>/tracker-$(date +%F).db`
(keep ~30). The DB file is the entire state.

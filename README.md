# calmmage-task-tracker

Personal accountability system for the life improvement plan. Deliberately
small: a Telegram bot, a SQLite file, and a one-page dashboard.

## The plan it enforces

- `plan/life-improvement-plan.md` — the system: Daily 3, floors not goals,
  never miss twice, seasonal challenges with stakes.
- `plan/health-roadmap.md` — health targets, 12-week mission, trophy goals.
- `plan/systems.md` — what infrastructure gets built, deferred, and cut
  (read this before adding anything).

## The daily loop

1. **08:00** — bot pings: score yesterday if unscored, shows the morning
   routine checklist (one ✅ button), then reads the **Obsidian inbox from
   disk**, has Claude triage it, and offers **3 focus buttons** — one tap sets
   the day's Focus. No manual dumping.
2. **21:30** — bot asks for the day's score (0–3 buttons) unless already scored.
3. **Sunday 18:00** — weekly review checklist.

Bot commands: `/inbox` (re-triage anytime), `/focus <task>`, `/drill`,
`/score 0-3`, `/weight 91.2 [waist_cm]`, `/today`, `/stats`, `/cancel`.

Without `ANTHROPIC_API_KEY` the focus buttons come from `plan/on-deck.md`
instead of LLM triage — the bot never blocks on an API. See "Where the AI is"
in `plan/systems.md`.

Dashboard (`:8000`): 12-week mission progress bar, 8-week Daily 3 score grid,
90-day weight chart.

## Run it

```bash
cp .env.example .env   # bot token, user id, OBSIDIAN_VAULT path, optional API key
docker compose up -d --build
```

Or let a local Claude Code session do it: the `deploy-tracker` skill in
`.claude/skills/` walks through setup, vault glob configuration, and
verification. Deploy target must be **always-on** — reminders die when the
machine sleeps.

Data lives in `./data/tracker.db` — back it up by copying the file.

Without Docker:

```bash
pip install -e ".[dev]"
python -m tracker.bot                                   # bot + reminders
uvicorn tracker.dashboard:app --port 8000               # dashboard
pytest                                                  # tests
```

## Claude integration

`.claude/skills/drill-me/SKILL.md` gives any Claude session in this repo a
`/drill-me` command for deeper check-ins and weekly reviews. The bot handles
the 60-second daily loop; Claude handles the thinking.

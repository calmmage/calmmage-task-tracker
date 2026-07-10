# Systems: what gets built, deferred, and cut

The request was: Google Calendar, reminders, Telegram bot, DB/Docker, Apple
Health sync, mobile app, web dashboard — EVERYTHING to ensure the plan happens.

Hard truth first: **the plan fails from too many systems, not too few.** The
person this is for (see `life-improvement-plan.md`) drowns in projects. Every
piece of infrastructure here is itself a project that can catch fire. So each
requested item gets a verdict, and the default verdict is NO.

## Verdicts

| Requested | Verdict | Why |
|---|---|---|
| Telegram bot | **BUILD** | The single interaction point. Already on your phone, zero UI work, push by default. This *is* the mobile app. |
| Reminders | **BUILD** (inside the bot) | Morning drill, evening score, weekly review — three scheduled jobs. Not a separate system. |
| DB | **BUILD** — SQLite | One file, zero ops, trivially backed up by copying. Postgres is a server to babysit for a dataset that will be ~365 rows/year. |
| Docker | **BUILD** — one compose file | Two services, one volume. Nothing more. |
| Web dashboard | **BUILD** — read-only, one page | Server-rendered HTML, inline SVG. No React, no build step, no auth system (optional token). You look at it weekly; it doesn't need to be a product. |
| Apple Health sync | **DEFER** to Phase 1 | The cheap path is the "Health Auto Export" app POSTing JSON to one endpoint — a day of work, no Apple developer account. But until there are 14 days of real bot usage, a sync pipeline is procrastination with extra steps. `/weight 91.2` takes 4 seconds. |
| Google Calendar API | **CUT** | The value is *booking the session*, which takes 30 seconds by hand. OAuth consent screens, token refresh, and API quotas take days and rot. The weekly review reminder says "book it" — that's the integration. |
| Mobile app | **CUT permanently** | Months of work to rebuild what Telegram already does. This is the single most dangerous item on the list — a novelty-generating mega-project disguised as self-improvement. |

## Self-critique checkpoints (read these before adding anything)

1. **The system is not the goal.** Every hour building the tracker is an hour
   not walking, not sleeping, not with your daughter. The tracker earns
   expansion only by being *used*: no new infrastructure until the bot has
   14 days of real check-ins logged.
2. **Kill criterion:** if the bot goes unused for 7 consecutive days, the fix
   is to *remove* features until the daily interaction is under 60 seconds —
   never to add a new system to remind you about the old one.
3. **The "make the system the project" clause** (from the main plan) is a
   *wildcard slot* privilege, not a standing license. Tracker work competes
   with other wildcards at the weekly review like everything else.

## Where the AI is (and deliberately isn't)

The skeleton is deterministic: schedules, storage, buttons, canned reminder
text. Zero cost, zero latency, never hallucinates a reminder. The LLM sits
only at the judgment points where actual thinking is needed:

1. **Morning inbox triage** — reads the Obsidian vault from disk (no manual
   dumping), Claude picks 3 focus candidates against the season goal and
   on-deck list; one button tap sets the day's Focus. Falls back to
   `plan/on-deck.md` without an API key — the morning never blocks on an API.
2. **Weekly review** — deeper thinking happens in a Claude session via
   `/drill-me` against the same SQLite + repo (Phase 1 candidate: an in-bot
   LLM weekly summary, only if the weekly Claude session proves too heavy).
3. **Not for reminder phrasing.** LLM-flavored nagging is novelty that decays
   in a week; canned lines are free and reliable.

## Phases

- **Phase 0 (now):** bot + SQLite + 3 reminders + dashboard + compose. Done in
  this repo, deployable on any box with Docker.
- **Phase 1 (after 14 logged days):** Apple Health via Health Auto Export →
  `POST /api/health` (weight, sleep, steps land in the same SQLite file).
- **Phase 2 (only if a real need appears in weekly reviews):** .ics generation
  for booked sessions; Claude-generated weekly review summaries from the DB.
- **Never:** custom mobile app, Postgres/microservices/k8s, OAuth calendar
  sync, a second tracking system of any kind.

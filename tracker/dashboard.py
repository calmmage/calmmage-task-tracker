"""Read-only web dashboard. One page, server-rendered, no JS build step.

Run with: uvicorn tracker.dashboard:app --host 0.0.0.0 --port 8000
"""

from datetime import date, datetime, timedelta

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse

from tracker import config, db

app = FastAPI(title="calmmage tracker")

SCORE_COLORS = {None: "#2a2a2a", 0: "#7f1d1d", 1: "#a16207", 2: "#4d7c0f", 3: "#15803d"}


def today() -> date:
    return datetime.now(config.TZ).date()


def mission_bar(s: dict) -> str:
    if s["weight"] is None:
        return "<p class='muted'>No weights yet — log with <code>/weight 91.2</code> in the bot.</p>"
    start, target = config.MISSION_START_KG, config.MISSION_TARGET_KG
    pct = max(0.0, min(1.0, (start - s["weight"]) / (start - target)))
    trend = f" · {s['delta21']:+} kg / 3 weeks" if s["delta21"] is not None else ""
    waist = f" · waist {s['waist']} cm" if s["waist"] else ""
    return (
        f"<p>{s['weight']} kg (logged {s['weight_date']}){trend}{waist}</p>"
        f"<div class='track'><div class='fill' style='width:{pct * 100:.0f}%'></div></div>"
        f"<p class='muted'>{start} kg → {target} kg · {pct * 100:.0f}% of the 12-week mission</p>"
    )


def score_grid(conn, end: date, weeks: int = 8) -> str:
    start = end - timedelta(days=end.weekday())  # Monday of current week
    start -= timedelta(weeks=weeks - 1)
    rows = {r["date"]: r["score"] for r in db.days_since(conn, start)}
    html = ["<table class='grid'>"]
    for w in range(weeks):
        cells = []
        for d in range(7):
            day = start + timedelta(weeks=w, days=d)
            if day > end:
                cells.append("<td></td>")
                continue
            score = rows.get(day.isoformat())
            label = "·" if score is None else str(score)
            cells.append(
                f"<td style='background:{SCORE_COLORS[score]}' title='{day}'>{label}</td>"
            )
        html.append(f"<tr><th>{(start + timedelta(weeks=w)):%d %b}</th>{''.join(cells)}</tr>")
    html.append("</table>")
    return "".join(html)


def weight_svg(conn, end: date) -> str:
    points = db.weights_since(conn, end - timedelta(days=90))
    if len(points) < 2:
        return "<p class='muted'>Weight chart appears after 2+ entries.</p>"
    kgs = [p["kg"] for p in points]
    lo = min(min(kgs), config.MISSION_TARGET_KG) - 0.5
    hi = max(max(kgs), config.MISSION_START_KG) + 0.5
    w, h = 640, 160

    def x(i):
        return round(i * w / (len(points) - 1), 1)

    def y(kg):
        return round(h - (kg - lo) / (hi - lo) * h, 1)

    line = " ".join(f"{x(i)},{y(p['kg'])}" for i, p in enumerate(points))
    ty = y(config.MISSION_TARGET_KG)
    return (
        f"<svg viewBox='0 0 {w} {h}' width='100%' height='{h}'>"
        f"<line x1='0' y1='{ty}' x2='{w}' y2='{ty}' stroke='#4d7c0f' stroke-dasharray='6 4'/>"
        f"<text x='4' y='{ty - 6}' fill='#4d7c0f' font-size='12'>{config.MISSION_TARGET_KG} kg target</text>"
        f"<polyline points='{line}' fill='none' stroke='#60a5fa' stroke-width='2'/>"
        f"<text x='4' y='14' fill='#888' font-size='12'>{kgs[-1]} kg · last 90 days</text>"
        "</svg>"
    )


@app.get("/", response_class=HTMLResponse)
def index(token: str = Query(default="")):
    if config.DASHBOARD_TOKEN and token != config.DASHBOARD_TOKEN:
        raise HTTPException(status_code=403, detail="bad token")
    end = today()
    with db.connect() as conn:
        s = db.stats(conn, end)
        grid = score_grid(conn, end)
        svg = weight_svg(conn, end)

    warning = ""
    if s["miss_gap"] is not None and s["miss_gap"] >= 2:
        warning = (
            f"<p class='warn'>⚠️ {s['miss_gap']} days without a scored win. "
            "Missed twice is a decision. Come back today.</p>"
        )
    avg = f"{s['avg7']}/3 avg last 7 days" if s["avg7"] is not None else "no scores yet"

    return f"""<!doctype html>
<meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>One day at a time</title>
<style>
  body {{ font-family: system-ui, sans-serif; background: #141414; color: #eee;
         max-width: 720px; margin: 2rem auto; padding: 0 1rem; }}
  h1 {{ font-size: 1.4rem; }} h2 {{ font-size: 1.05rem; margin-top: 2rem; color: #bbb; }}
  .muted {{ color: #888; font-size: .9rem; }}
  .warn {{ color: #fca5a5; }}
  .track {{ background: #2a2a2a; border-radius: 6px; height: 14px; }}
  .fill {{ background: #15803d; border-radius: 6px; height: 14px; }}
  table.grid {{ border-collapse: separate; border-spacing: 3px; }}
  table.grid td {{ width: 2rem; height: 2rem; text-align: center; border-radius: 4px;
                   font-size: .8rem; color: #ddd; }}
  table.grid th {{ font-size: .75rem; color: #777; font-weight: normal;
                   text-align: right; padding-right: .5rem; }}
  code {{ background: #2a2a2a; padding: 0 .3em; border-radius: 3px; }}
</style>
<h1>One day at a time</h1>
{warning}
<h2>12-week mission</h2>
{mission_bar(s)}
<h2>Daily 3 — {avg}</h2>
{grid}
<h2>Weight</h2>
{svg}
<p class='muted'>Data lives in the bot: /drill · /score · /weight. This page just shows it.</p>
"""

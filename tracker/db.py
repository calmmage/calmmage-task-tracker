"""SQLite storage. One file, two tables — that is the whole database layer."""

import sqlite3
from contextlib import contextmanager
from datetime import date, timedelta
from pathlib import Path

from tracker import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS days (
    date TEXT PRIMARY KEY,
    focus TEXT,
    body TEXT,
    people TEXT,
    score INTEGER,
    routine INTEGER
);
CREATE TABLE IF NOT EXISTS weights (
    date TEXT PRIMARY KEY,
    kg REAL NOT NULL,
    waist_cm REAL
);
"""


@contextmanager
def connect(path=None):
    path = Path(path or config.DB_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    try:  # migrate DBs created before the routine column existed
        conn.execute("ALTER TABLE days ADD COLUMN routine INTEGER")
    except sqlite3.OperationalError:
        pass
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def set_daily3(conn, day: date, focus: str, body: str, people: str) -> None:
    conn.execute(
        """INSERT INTO days (date, focus, body, people) VALUES (?, ?, ?, ?)
           ON CONFLICT(date) DO UPDATE SET
             focus=excluded.focus, body=excluded.body, people=excluded.people""",
        (day.isoformat(), focus, body, people),
    )


def set_focus(conn, day: date, focus: str) -> None:
    conn.execute(
        """INSERT INTO days (date, focus) VALUES (?, ?)
           ON CONFLICT(date) DO UPDATE SET focus=excluded.focus""",
        (day.isoformat(), focus),
    )


def set_routine(conn, day: date, done: bool = True) -> None:
    conn.execute(
        """INSERT INTO days (date, routine) VALUES (?, ?)
           ON CONFLICT(date) DO UPDATE SET routine=excluded.routine""",
        (day.isoformat(), int(done)),
    )


def set_score(conn, day: date, score: int) -> None:
    conn.execute(
        """INSERT INTO days (date, score) VALUES (?, ?)
           ON CONFLICT(date) DO UPDATE SET score=excluded.score""",
        (day.isoformat(), score),
    )


def add_weight(conn, day: date, kg: float, waist_cm: float | None = None) -> None:
    conn.execute(
        """INSERT INTO weights (date, kg, waist_cm) VALUES (?, ?, ?)
           ON CONFLICT(date) DO UPDATE SET kg=excluded.kg, waist_cm=excluded.waist_cm""",
        (day.isoformat(), kg, waist_cm),
    )


def get_day(conn, day: date):
    return conn.execute(
        "SELECT * FROM days WHERE date=?", (day.isoformat(),)
    ).fetchone()


def days_since(conn, since: date):
    return conn.execute(
        "SELECT * FROM days WHERE date>=? ORDER BY date", (since.isoformat(),)
    ).fetchall()


def weights_since(conn, since: date):
    return conn.execute(
        "SELECT * FROM weights WHERE date>=? ORDER BY date", (since.isoformat(),)
    ).fetchall()


def latest_weight(conn):
    return conn.execute("SELECT * FROM weights ORDER BY date DESC LIMIT 1").fetchone()


def stats(conn, today: date) -> dict:
    """Everything the bot and the dashboard show, computed in one place."""
    scores7 = []
    routine7 = 0
    for i in range(6, -1, -1):
        row = get_day(conn, today - timedelta(days=i))
        scores7.append(None if row is None else row["score"])
        if row is not None and row["routine"]:
            routine7 += 1
    scored = [s for s in scores7 if s is not None]
    avg7 = round(sum(scored) / len(scored), 2) if scored else None

    # Miss gap: consecutive days ending yesterday with no score or score 0.
    # >= 2 means "missed twice" — the plan's one red flag.
    any_scored = conn.execute(
        "SELECT COUNT(*) AS c FROM days WHERE score IS NOT NULL"
    ).fetchone()["c"]
    miss_gap = None
    if any_scored:
        miss_gap = 0
        d = today - timedelta(days=1)
        for _ in range(60):
            row = get_day(conn, d)
            if row is not None and (row["score"] or 0) > 0:
                break
            miss_gap += 1
            d -= timedelta(days=1)

    latest = latest_weight(conn)
    window = weights_since(conn, today - timedelta(days=21))
    delta21 = (
        round(latest["kg"] - window[0]["kg"], 1) if latest and window else None
    )
    return {
        "scores7": scores7,
        "routine7": routine7,
        "avg7": avg7,
        "miss_gap": miss_gap,
        "weight": latest["kg"] if latest else None,
        "weight_date": latest["date"] if latest else None,
        "waist": latest["waist_cm"] if latest else None,
        "delta21": delta21,
    }

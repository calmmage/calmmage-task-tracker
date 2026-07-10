from datetime import date, timedelta

from tracker import db

D = date(2026, 7, 10)


def test_daily3_then_score_upserts_same_row(tmp_path):
    p = tmp_path / "t.db"
    with db.connect(p) as conn:
        db.set_daily3(conn, D, "ship X by 15:00", "walk 30 min", "15 min with daughter")
        db.set_score(conn, D, 3)
    with db.connect(p) as conn:
        row = db.get_day(conn, D)
        assert row["focus"] == "ship X by 15:00"
        assert row["score"] == 3


def test_score_without_daily3(tmp_path):
    p = tmp_path / "t.db"
    with db.connect(p) as conn:
        db.set_score(conn, D, 2)
    with db.connect(p) as conn:
        row = db.get_day(conn, D)
        assert row["score"] == 2
        assert row["focus"] is None


def test_stats_avg_and_miss_gap(tmp_path):
    p = tmp_path / "t.db"
    with db.connect(p) as conn:
        db.set_score(conn, D - timedelta(days=4), 3)
        db.set_score(conn, D - timedelta(days=3), 2)
        # days -2 and -1 unscored -> miss gap of 2 ending yesterday
        s = db.stats(conn, D)
        assert s["avg7"] == 2.5
        assert s["miss_gap"] == 2


def test_stats_empty_db(tmp_path):
    with db.connect(tmp_path / "t.db") as conn:
        s = db.stats(conn, D)
        assert s["avg7"] is None
        assert s["miss_gap"] is None
        assert s["weight"] is None


def test_weight_trend(tmp_path):
    with db.connect(tmp_path / "t.db") as conn:
        db.add_weight(conn, D - timedelta(days=20), 92.7, 98.0)
        db.add_weight(conn, D, 91.5)
        s = db.stats(conn, D)
        assert s["weight"] == 91.5
        assert s["delta21"] == -1.2

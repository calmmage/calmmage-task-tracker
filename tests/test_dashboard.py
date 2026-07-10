from datetime import timedelta

from fastapi.testclient import TestClient

from tracker import config, db
from tracker.dashboard import app, today


def test_dashboard_renders(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "t.db")
    end = today()
    with db.connect() as conn:
        db.set_daily3(conn, end, "focus", "body", "people")
        db.set_score(conn, end, 3)
        db.add_weight(conn, end - timedelta(days=7), 92.7)
        db.add_weight(conn, end, 91.9)
    r = TestClient(app).get("/")
    assert r.status_code == 200
    assert "12-week mission" in r.text
    assert "91.9" in r.text


def test_dashboard_token(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "t.db")
    monkeypatch.setattr(config, "DASHBOARD_TOKEN", "s3cret")
    client = TestClient(app)
    assert client.get("/").status_code == 403
    assert client.get("/?token=s3cret").status_code == 200

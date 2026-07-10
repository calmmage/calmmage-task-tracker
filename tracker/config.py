import os
from pathlib import Path
from zoneinfo import ZoneInfo

DATA_DIR = Path(os.environ.get("DATA_DIR", "data"))
DB_PATH = DATA_DIR / "tracker.db"
TZ = ZoneInfo(os.environ.get("TZ", "Europe/Zurich"))

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
OWNER_ID = int(os.environ.get("TELEGRAM_USER_ID", "0"))
# If set, the dashboard requires ?token=... — enough for a single-user page
# that should anyway sit behind a VPN / tailscale.
DASHBOARD_TOKEN = os.environ.get("DASHBOARD_TOKEN", "")

# 12-week mission anchors, see plan/health-roadmap.md
MISSION_START_KG = 92.7
MISSION_TARGET_KG = 87.0

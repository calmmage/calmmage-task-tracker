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

# Morning routine, in his order
ROUTINE = [
    "Make the bed",
    "Go outside for a walk",
    "Drink water",
    "Cold / warm shower",
    "Meditation (3 breaths is the floor)",
    "Get dressed",
]

# Obsidian inbox triage. OBSIDIAN_VAULT_MOUNT is set inside the container;
# OBSIDIAN_VAULT is the host path used directly when running without Docker.
OBSIDIAN_VAULT = os.environ.get("OBSIDIAN_VAULT_MOUNT") or os.environ.get("OBSIDIAN_VAULT", "")
OBSIDIAN_INBOX_GLOBS = [
    g.strip()
    for g in os.environ.get("OBSIDIAN_INBOX_GLOBS", "Inbox/**/*.md").split(",")
    if g.strip()
]
ON_DECK_PATH = Path(os.environ.get("ON_DECK_PATH", "plan/on-deck.md"))

# LLM layer — optional. Without a key the bot falls back to the on-deck list.
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
TRIAGE_MODEL = os.environ.get("TRIAGE_MODEL", "claude-sonnet-5")

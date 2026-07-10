"""Morning inbox triage.

Reads inbox items straight from the Obsidian vault on disk (no manual
dumping), asks Claude for 3 focus candidates, falls back to the on-deck list
on any failure. The morning must never block on an API error.
"""

import json
import logging
import re
from pathlib import Path

from tracker import config

log = logging.getLogger(__name__)

MAX_ITEMS = 80
TASK_RE = re.compile(r"^\s*[-*] \[ \] (.+)$")
ON_DECK_RE = re.compile(r"^\d+\.\s+(.+)$", re.M)

TRIAGE_PROMPT = """You triage a morning inbox for a man whose head swarms with tasks on waking.
Pick the 3 best candidates for today's ONE focus task.

Selection rules:
- concrete and finishable in one 90-minute block beats big and vague
- already-started work beats new shiny ideas
- deadlines and other people waiting beat solo someday-tasks

Context (season goal, on-deck shortlist, recent log):
{context}

Inbox items (newest first):
{items}

Reply with ONLY a JSON array of exactly 3 strings, each a task of at most
7 words, based on the items above (rephrase for brevity). No other text."""


def gather_inbox(vault: str | Path | None = None, globs: list[str] | None = None) -> list[str]:
    """Unchecked tasks (and titles of task-less notes) from the vault, newest first."""
    raw = vault or config.OBSIDIAN_VAULT
    if not raw:  # Path("") is ".", which would silently scan the CWD
        return []
    vault = Path(raw)
    if not vault.is_dir():
        return []
    files: set[Path] = set()
    for g in globs or config.OBSIDIAN_INBOX_GLOBS:
        files.update(f for f in vault.glob(g) if f.is_file())
    items: list[str] = []
    for f in sorted(files, key=lambda f: f.stat().st_mtime, reverse=True):
        try:
            text = f.read_text(errors="ignore")
        except OSError:
            continue
        tasks = [m.group(1).strip() for line in text.splitlines() if (m := TASK_RE.match(line))]
        items.extend(tasks or [f.stem])
        if len(items) >= MAX_ITEMS:
            break
    return items[:MAX_ITEMS]


def on_deck() -> list[str]:
    """Top candidates from plan/on-deck.md — the no-LLM fallback."""
    try:
        text = config.ON_DECK_PATH.read_text()
    except OSError:
        return []
    return ON_DECK_RE.findall(text)[:3]


def propose_focus(items: list[str], context_note: str = "") -> list[str]:
    """Up to 3 focus candidates. Any failure degrades to the first items."""
    if not items:
        return []
    if not config.ANTHROPIC_API_KEY:
        return items[:3]
    try:
        import anthropic

        client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        msg = client.messages.create(
            model=config.TRIAGE_MODEL,
            max_tokens=300,
            messages=[{
                "role": "user",
                "content": TRIAGE_PROMPT.format(
                    context=context_note or "(none)",
                    items="\n".join(f"- {i}" for i in items),
                ),
            }],
        )
        text = msg.content[0].text.strip()
        text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.M).strip()
        candidates = [str(c)[:80] for c in json.loads(text) if str(c).strip()]
        return candidates[:3] or items[:3]
    except Exception:
        log.warning("triage LLM call failed, falling back to raw items", exc_info=True)
        return items[:3]

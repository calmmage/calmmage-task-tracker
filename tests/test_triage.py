import os
import time

from tracker import config, triage


def make_vault(tmp_path):
    inbox = tmp_path / "Inbox"
    inbox.mkdir()
    older = inbox / "older.md"
    older.write_text("- [ ] task one\n- [x] done task\n- [ ] task two\n")
    newer = inbox / "newer note.md"
    newer.write_text("just prose, no tasks\n")
    (tmp_path / "outside.md").write_text("- [ ] not in glob\n")
    now = time.time()
    os.utime(older, (now - 100, now - 100))
    os.utime(newer, (now, now))
    return tmp_path


def test_gather_inbox_tasks_titles_and_order(tmp_path):
    items = triage.gather_inbox(make_vault(tmp_path), ["Inbox/**/*.md"])
    # newest file first; task-less note contributes its title; [x] excluded
    assert items == ["newer note", "task one", "task two"]


def test_gather_inbox_missing_vault(tmp_path):
    assert triage.gather_inbox(tmp_path / "nope", ["*.md"]) == []
    assert triage.gather_inbox("", ["*.md"]) == []


def test_propose_focus_fallback_without_key(monkeypatch):
    monkeypatch.setattr(config, "ANTHROPIC_API_KEY", "")
    items = ["a", "b", "c", "d"]
    assert triage.propose_focus(items) == ["a", "b", "c"]
    assert triage.propose_focus([]) == []


def test_on_deck_parsing(tmp_path, monkeypatch):
    f = tmp_path / "on-deck.md"
    f.write_text("# On deck\n\n1. First thing.\n2. Second thing.\n3. Third.\n")
    monkeypatch.setattr(config, "ON_DECK_PATH", f)
    assert triage.on_deck() == ["First thing.", "Second thing.", "Third."]
    monkeypatch.setattr(config, "ON_DECK_PATH", tmp_path / "missing.md")
    assert triage.on_deck() == []
